from subprocess import call, check_output, PIPE, Popen
import os, sys, json, smtplib
import click
if float(sys.version[:3]) < 3.3:
    from pipes import quote
else:
    from shlex import quote

base_path = os.path.dirname(os.path.abspath(__file__))

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
        ], shell=True)
    return result

def handbrake(source,title):
    opts = {
        'src': quote(os.path.join(source,'%s.mkv' % title)),
        'dest': quote(os.path.join(source, '%s.mp4' % title)),
        }
    result = shell(
        ['HandBrakeCLI -i %(src)s -o %(dest)s --preset="AppleTV 3"' % opts],
        shell=True)
    return result

def makemkv(source,output,title):
    print('Running makemkv')
    shell('makemkvcon mkv --decrypt --cache=16 -r disc:%d all %s' % (source,
        output), stream=True)

    # Find which files to keep
    fl = os.listdir(output)
    keep = -1
    destroy = [os.path.join(output, f) for f in fl]
    sizes = [os.path.getsize(f) for f in destroy]
    biggest = sizes.index(max(sizes))
    del destroy[biggest]

    print('Cleaning up')
    [os.remove(os.path.join(output, f)) for f in destroy]
    save_path = os.path.join(output, '%s.mkv' % title)
    os.rename(os.path.join(output, fl[biggest]), save_path)

@click.command()
@click.option('--source', '-s', default=0,
    help='Device Source Integer, ie /dev/sr0 [default: 0]')
@click.option('--output', '-o', default=os.path.join(base_path, 'output'),
    help='Absolute path of Output Directory [default: ./output]')
@click.option('--notify', '-n', default=False, multiple=True,
    help='Email address to notify')
@click.option('--email-sender', '-f', default='encode@optical.disc',
    help='Email sender address')
@click.option('--email-host', '-h', default='localhost', help='Email provider')
@click.option('--email-port', '-l', default=25, help='Email port')
@click.option('--starttls', '-t', is_flag=True, help='Email starttls')
@click.option('--email-user', '-u', default=False, help='Email user')
@click.option('--email-pass', '-p', default=False, help='Email password')
def main(source, output,notify,email_sender,email_host,email_port,starttls,email_user,email_pass):
    # get the movie title
    # title = get_dvd_name(source)
    title = 'Something'
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
        send_email(message='Encoding started.', **email_temp)

    # make necessary directories
    # groupP = os.path.join(output, title)
    # os.makedirs(output, exist_ok=True)
    # os.makedirs(groupP, exist_ok=True)

    # rip to mkv
    # makemkv(source, groupP, title)

    # Convert and insert subtitles
    # convert_subtitles(groupP, title)

    # Encode mp4
    # ffmpeg(groupP, title)

    shell(['eject', 'sr%d' % source])
    if notify:
        send_email(message='Encoding finished.', **email_temp)


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
        return output.decode('utf-8')
    else:
        return check_output(cmd)

if __name__ == "__main__":
    main()
