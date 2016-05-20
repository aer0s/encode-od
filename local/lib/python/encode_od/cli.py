from subprocess import call, check_output, PIPE, Popen
import os, sys, json, smtplib, datetime, shlex
import click
if float(sys.version[:3]) < 3.3:
    from pipes import quote
else:
    from shlex import quote
    unicode = str

base_path = os.path.dirname(os.path.abspath(__file__))

# This is decieving as by default shell commands are logged. See global_logging
# assignment in main()
global_logging = '/tmp'

def eject(drive):
    if type(drive) is int:
        drive = 'sr%d' % drive
    shell(['eject', drive], shell=True)

def get_dvd_name(source):
    cmd = [' '.join([
        "vobcopy", "-i", "/dev/sr%d" % source, "-I", "2>&1", ">", "/dev/stdout",
        "|", "grep","DVD-name","|",
        "sed","-e","'s/.*DVD-name: //'",
        ])]
    r = Popen(cmd, shell=True, stdout=PIPE)
    (output, err) = r.communicate()
    result = output.decode('utf-8').strip()
    return result.replace('_', ' ').title()

def ffmpeg(source,title):
    opts = {
        'src': quote(os.path.join(source,'%s.mkv' % title)),
        'dest': quote(os.path.join(source, '%s.m4v' % title)),
        'srt': quote(os.path.join(source, '%s.srt' % title)),
        }
    result = shell([' '.join([
            'ffmpeg','-i', opts['src'], '-i', opts['srt'],
            '-map', '0:v', '-map', '0:a', '-map', '1:s',
            '-c:v', 'copy', '-vcodec', 'libx264',
            '-c:a', 'copy', '-acodec', 'aac',
            '-c:s', 'mov_text', opts['dest']])
        ], shell=True, logdir=source)
    return result

def handbrake(source,output):
    opts = {
        'src': quote(source),
        'dest': quote(output),
        }
    result = shell(
        ['HandBrakeCLI -i %(src)s -o %(dest)s --preset="AppleTV 3"' % opts],
        shell=True)
    return result

def log(message, email_temp=False):
    logfile = os.path.join(global_logging,'rip.log')
    if type(message) not in [str,unicode]:
        message = str(message)
    if os.path.isdir(global_logging):
        log_file = open(logfile, 'a')
        log_file.write('[ %s ] - ' % str(datetime.datetime.now()))
        log_file.write(message)
        log_file.write('\n')
        log_file.close()
    if email_temp:
        send_email(message=message, **email_temp)


def makemkv(source,output,title):
    log('Running makemkv')
    cmd = 'makemkvcon mkv --decrypt --cache=16 -r disc:%d all %s'
    shell([cmd % (source, output)], shell=True)

    # Find which files to keep
    fl = os.listdir(output)
    destroy = [os.path.join(output, f) for f in fl if f.endswith('.mkv')]
    sizes = [os.path.getsize(f) for f in destroy]
    if sizes:
        biggest = sizes.index(max(sizes))
        # remove the largest mkv from the list
        del destroy[biggest]

        log('Cleaning up')
        [os.remove(os.path.join(output, f)) for f in destroy]
        save_path = os.path.join(output, '%s.mkv' % title)
        os.rename(os.path.join(output, fl[biggest]), save_path)
    else:
        log(cmd % (source, output))

@click.command()
@click.option('--source', '-s', default=0,
    help='Device Source Integer, ie /dev/sr0 [default: 0]')
@click.option('--output', '-o', default=os.path.join(base_path, 'output'),
    help='Absolute path of Output Directory [default: ./output]')
@click.option('--force', is_flag=True, help='Force overwrite')
@click.option('--no-logging', is_flag=True, help='Disable logging')
@click.option('--notify', '-n', default=False, multiple=True,
    help='Email address to notify')
@click.option('--email-sender', '-f', default='encode@optical.disc',
    help='Email sender address')
@click.option('--email-host', '-h', default='localhost', help='Email provider')
@click.option('--email-port', '-l', default=25, help='Email port')
@click.option('--starttls', '-t', is_flag=True, help='Email starttls')
@click.option('--email-user', '-u', default=False, help='Email user')
@click.option('--email-pass', '-p', default=False, help='Email password')
def main(source, output,force,no_logging,notify,email_sender,email_host,email_port,starttls,email_user,email_pass):
    # get the movie title
    title = get_dvd_name(source)
    email_temp = False
    if notify:
        email_temp = {
        'sender': email_sender,
        'receivers': notify,
        'subject': 'Encoding %s' %title,
        'host': email_host,
        'port': email_port,
        'starttls': starttls,
        'user': email_user,
        'password': email_pass,
        }
    log('Encoding started.', email_temp)

    # make necessary directories
    groupP = os.path.join(output, title.replace(' ', '_'))
    global global_logging
    global_logging = groupP if not no_logging else False
    os.makedirs(output, exist_ok=True)
    # If this has already been done then kill this attempt unless forced
    if not os.path.isdir(groupP) or force:
        os.makedirs(groupP, exist_ok=True)

        # rip to mkv
        log('Rip to mkv')
        try:
            makemkv(source, groupP, title)
        except Exception as Err:
            log('MakeMKV encode Failure!:\n%s' % str(Err), email_temp)
            try:
                log('Attempting to encode with HandBrake', email_temp)
                handbrake('/dev/sr%d' % source, os.path.join(groupP, '%s.mkv' % title))
            except Exception as Err:
                log('HandBrake MKV encode Failure!:\n%s' % str(Err), email_temp)
                exit()
        # Convert and insert subtitles
        log('Convert and insert subtitles')
        try:
            convert_subtitles(groupP, title)
        except Exception as Err:
            log('Subtitle Failure!:\n%s' % str(Err), email_temp)

        # Encode mp4
        log('Encode mp4')
        try:
            ffmpeg(groupP, title)
        except Exception as Err:
            log('FFmpeg Failure!:\n%s' % str(Err), email_temp)
            exit()

        shell(['touch %s' % os.path.join(groupP, 'complete.done')])
        log('Encoding finished.', email_temp)
        eject(source)
    else:
        log('This od has been encoded already. If you woul like to do it again plese use --force option.', email_temp)


def send_email(**kwargs):
    sender = kwargs.get('sender',False)
    receivers = kwargs.get('receivers',False)
    subject = kwargs.get('subject',False)
    message = kwargs.get('message',False)
    host = kwargs.get('host', 'localhost')
    port = kwargs.get('port', 25)
    starttls = kwargs.get('starttls', False)
    user = kwargs.get('user',False)
    password = kwargs.get('password',False)
    if type(receivers) is str:
        recievers = [recievers]
    body = '\r\n'.join([
        'From: %s' % sender,
        'To: %s' % ','.join(receivers),
        'Subject: %s' % subject,
        '',
        message
        ])

    try:
       smtpObj = smtplib.SMTP(host, port)
       smtpObj.ehlo()
       if starttls:
           smtpObj.starttls()
       smtpObj.ehlo()
       if user and password:
           smtpObj.login(user,password)
       smtpObj.sendmail(sender, receivers, body)
       smtpObj.quit()
       print("Successfully sent email")
    except Exception as err:
       print("Error: unable to send email")
       print(err)

def convert_subtitles(output, title):
    sfiles = {
        'mkv': quote(os.path.join(output, '%s.mkv' % title)),
        'mkvCopy': quote(os.path.join(output, '%s-working.mkv' % title)),
        'idx': quote(os.path.join(output, '%s.idx' % title)),
        'srt': quote(os.path.join(output, '%s.srt' % title)),
        'sub': quote(os.path.join(output, '%s' % title)),
    }
    # get and index of mkv tracks
    r = shell(['mkvmerge -i -F json %(mkv)s' % sfiles], shell=True)
    subs = []
    for track in json.loads(r).get('tracks',[]):
        # ident english subtitle files and extract
        if track.get('type', '') in 'subtitles':
            subs.append(track.get('id'))
            if track.get('properties',{}).get('language','') in 'eng':
                sfiles['id'] = track.get('id',False)

    if sfiles['id']:
        print('Extracting subtitles... be patient this is not fast')
        shell([
            'mkvextract tracks %(mkv)s %(id)d:%(idx)s' % sfiles,
        ],shell=True)
        print('Converting optical subtitles to text (OCR)...')
        shell(['vobsub2srt %(sub)s' % sfiles,], shell=True)
        print('Subtitles converted, begining merge...')
        shell([
            "mkvmerge -o %(mkvCopy)s --subtitle-tracks %(id)d %(mkv)s %(srt)s" % sfiles,
            ], shell=True)
        print('Cleaning up ...')
        os.remove(os.path.join(output, '%s.idx' % title))
        os.remove(os.path.join(output, '%s.sub' % title))
        os.remove(os.path.join(output, '%s.srt' % title))
        os.remove(os.path.join(output, '%s.mkv' % title))
        os.rename(os.path.join(output, '%s-working.mkv' % title), os.path.join(output, '%s.mkv' % title))
        print('done.')
    else:
        print('Well damn it!')


def shell(cmd, **kwargs):
    if type(cmd) == str:
        cmd = cmd.split(' ')

    if kwargs.get('stream',False):
        call(cmd)
    elif kwargs.get('shell', False):
        r = Popen(cmd, stdout=PIPE, shell=True)
        (output, err) = r.communicate()
        if global_logging:
            if output:
                log(output.decode('utf-8'))
            if err:
                log(err.decode('utf-8'))
        else:
            return output.decode('utf-8')
    else:
        return check_output(cmd)

if __name__ == "__main__":
    main()
