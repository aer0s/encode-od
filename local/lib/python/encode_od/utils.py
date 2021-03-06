from subprocess import call, check_output, PIPE, Popen
import os
import sys
import json
import smtplib
import datetime
import shlex
import click
from shlex import quote
import hashlib


class odTools(object):

    def __init__(self, **kwargs):
        # This is decieving as by default shell commands are logged.
        # See logging assignment in main()
        self.logging = kwargs.get('logging', False)
        self.log_name = kwargs.get('log_name', 'rip.log')
        self.email_temp = kwargs.get('email', False)
        self.output = os.path.abspath(kwargs.get('output', os.getcwd()))
        self.lock_name = kwargs.get('lock_name', 'encodeODsource.lock')
        self.title = kwargs.get('title', False)
        # this needs to be done afert title and output assignment
        if self.title:
            self.paths = self.get_filenames()

    def convert_subtitles(self):
        sfiles = dict(self.paths['quoted'])
        # get and index of mkv tracks
        r = self.shell(['mkvmerge -i -F json %(mkv)s' % sfiles], shell=True)
        subs = []
        for track in json.loads(r).get('tracks', []):
            # ident english subtitle files and extract
            if track.get('type', '') in 'subtitles':
                subs.append(track.get('id'))
                if track.get('properties', {}).get('language', '') in 'eng':
                    sfiles['id'] = track.get('id', False)

        if sfiles['id']:
            self.log('Extracting subtitles... be patient this is not fast')
            self.shell([
                'mkvextract tracks %(mkv)s %(id)d:%(idx)s' % sfiles,
            ], shell=True)
            self.log('Converting optical subtitles to text (OCR)...')
            self.shell(['vobsub2srt %(subPath)s' % sfiles], shell=True)
            self.log('Subtitles converted, begining merge...')
            cmd = ' '.join([
                "mkvmerge -o %(mkvCopy)s --subtitle-tracks",
                "%(id)d %(mkv)s %(srt)s"
            ])
            self.shell([cmd % sfiles], shell=True)
            self.log('Cleaning up ...')
            for ftype in ['idx', 'sub', 'mkv']:
                if os.path.isfile(self.paths['actual']['mkvCopy']):
                    self.log('Deleting [%s]' % self.paths['actual'][ftype])
                    os.remove(self.paths['actual'][ftype])
            if os.path.isfile(self.paths['actual']['mkvCopy']):
                os.rename(self.paths['actual']['mkvCopy'],
                          self.paths['actual']['mkv'])
                self.log('Subtitle creation done.')
            else:
                self.log('Something went wrong in merging the subtitles')
        else:
            self.log('No subtitles found for the language: %s' % self.sub_lang)

    def eject(self, drive):
        if type(drive) is int:
            drive = 'sr%d' % drive
        self.shell(['eject', drive], shell=True)

    def get_dvd_name(self, source):
        # Turnning off logging to do this check. Because there is a possibility
        # that the project dir hasn't been made yet
        original_logging = self.logging
        self.logging = False
        cmd = ' '.join([
            "vobcopy -i /dev/sr%d -I 2>&1 > /dev/stdout" % source,
            "| grep DVD-name | sed -e 's/.*DVD-name: //'",
        ])

        result = self.shell(cmd, shell=True, as_string=True).strip()
        self.title = result.replace('_', ' ').title()
        if self.email_temp:
            title_obj = {'title': self.title}
            self.email_temp['subject'] = self.email_temp['subject'] % title_obj
        # create a uid
        mnt = ''.join(self.shell("mount | grep /dev/sr%d | awk '{print $3}'" %
                                 source, shell=True,
                                 as_string=True).split('\n'))
        size = self.shell("du -s %s | awk '{print $1}'" % mnt,
                          shell=True, as_string=True) if mnt else ''
        self.uid = hashlib.sha1(
            (str(self.title) + str(size)).encode('utf-8')).hexdigest()
        self.paths = self.get_filenames()
        self.logging = original_logging
        return self.title

    def get_filenames(self):
        if hasattr(self, 'uid'):
            self.group = os.path.join(self.output, self.uid)
        else:
            self.group = os.path.join(
                self.output, self.title.replace(' ', '_'))
        os.makedirs(self.output, exist_ok=True)
        os.makedirs(self.group, exist_ok=True)

        extless = os.path.join(self.group, self.title)
        paths = {
            'actual': {
                'mkv': '%s.mkv' % extless,
                'm4v': '%s.m4v' % extless,
                'gif': '%s Preview.gif' % extless,
                'mkvCopy': '%s-working.mkv' % extless,
                'idx': '%s.idx' % extless,
                'srt': '%s.srt' % extless,
                'sub': '%s.sub' % extless,
                'subPath': '%s' % extless,
                'log': os.path.join(self.group, self.log_name),
                'done': os.path.join(self.group, 'complete.done'),
                'moved': os.path.join(self.group, 'complete.moved'),
                'lock': os.path.join(self.output, self.lock_name)
            },
        }
        paths['quoted'] = {t: quote(v) for t, v in paths['actual'].items()}
        return paths

    def lock(self, lock=True):
        if lock:
            with open(self.paths['actual']['lock'], 'w') as lk:
                pass
        else:
            os.remove(self.paths['actual']['lock'])

    def isdone(self):
        return any([
            os.path.isfile(self.paths['actual']['done']),
            os.path.isfile(self.paths['actual']['moved'])
        ])

    def islocked(self):
        return os.path.isfile(self.paths['actual']['lock'])

    def ffmpeg(self):
        opts = {
            'src': self.paths['quoted']['mkv'],
            'dest': self.paths['quoted']['m4v'],
            'srt': self.paths['actual']['srt'],
        }
        # make sure srt file actually exists
        if os.path.isfile(opts['srt']):
            opts['srt'] = '-i %s -map 1:s -c:s mov_text' % quote(opts['srt'])
        else:
            opts['srt'] = ''

        result = self.shell([' '.join([
            'ffmpeg', '-i', opts['src'], opts['srt'],
            '-map', '0:v', '-map', '0:a',
            '-c:v', 'copy', '-vcodec', 'libx264',
            '-c:a', 'copy', '-acodec', 'aac', opts['dest']])
        ], shell=True)
        self.log(result)

    def handbrake(self, source, format='mkv'):
        opts = {
            'src': quote(source),
            'dest': self.paths['quoted'][format],
        }
        cmd = 'HandBrakeCLI -i %(src)s -o %(dest)s --preset="AppleTV 3"' % opts
        return self.shell(cmd, shell=True)

    def log(self, message, **kwargs):
        if type(message) is not str:
            message = str(message)
        with open(self.paths['actual']['log'], 'a') as log_file:
            log_file.write('[ %s ] - ' % str(datetime.datetime.now()))
            log_file.write(message)
            log_file.write('\n')
        print(message)
        if kwargs.get('notify', False):
            self.send_email(message=message, **self.email_temp)

    def makemkv(self, source_disc):
        # TODO locate source disc mapping using makemkvcon info -r list command
        dvs, source = [], '"/dev/sr%d"' % source_disc
        cmd = ['makemkvcon info -r list']
        for s in self.shell(cmd, shell=True, log=False).split('\n'):
            if s.startswith('DRV'):
                dvs.append(s.replace('DRV:', '').split(','))
        src_disc = int(''.join([d[0] for d in dvs if source in d]))
        self.log('Running makemkv')
        cmd = 'makemkvcon mkv --decrypt --cache=16 -r disc:%d all %s'
        self.shell([cmd % (src_disc, self.group)], shell=True)

        # Find which files to keep
        fl = os.listdir(self.group)
        mkvs = [os.path.join(self.group, f) for f in fl if f.endswith('.mkv')]
        destroy = list(mkvs)
        sizes = [os.path.getsize(f) for f in destroy]
        if sizes:
            biggest = sizes.index(max(sizes))
            # remove the largest mkv from the list
            del destroy[biggest]
            save_path = self.paths['actual']['mkv']
            os.rename(mkvs[biggest], save_path)

            self.log('Cleaning up')
            for path in destroy:
                try:
                    os.remove(path)
                except Exception:
                    self.log('Failed to remove: %s' % path)

        else:
            self.log(cmd % (source_disc, self.group))

    def make_preview(self):
        self.shell(
            'ffmpeg -i %(mkv)s -t 9 -ss 00:02:00 -vf scale=320:-1 -y %(gif)s' %
            self.paths['quoted'], shell=True, as_string=True)
        if os.path.isfile(self.paths['actual']['gif']):
            self.log('Priview GIF created.')
        else:
            self.log('Priview GIF failed to create.')

    def send_email(self, **kwargs):
        sender = kwargs.get('sender', False)
        receivers = kwargs.get('receivers', False)
        subject = kwargs.get('subject', False)
        message = kwargs.get('message', False)
        host = kwargs.get('host', 'localhost')
        port = kwargs.get('port', 25)
        starttls = kwargs.get('starttls', False)
        user = kwargs.get('user', False)
        password = kwargs.get('password', False)
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
                smtpObj.login(user, password)
            smtpObj.sendmail(sender, receivers, body)
            smtpObj.quit()
            self.log("Successfully sent email")
        except Exception as err:
            self.log("Error: unable to send email")
            self.log(err)

    def shell(self, cmd, **kwargs):
        if type(cmd) == str and not kwargs.get('as_string', False):
            cmd = shlex.split(cmd)

        if kwargs.get('stream', False):
            call(cmd)
        elif kwargs.get('shell', False):
            r = Popen(cmd, stdout=PIPE, shell=True)
            (output, err) = r.communicate()
            if self.logging and kwargs.get('log', True):
                if output:
                    self.log(output.decode('utf-8'))
                if err:
                    self.log(err.decode('utf-8'))
            return output.decode('utf-8')
        elif kwargs.get('standalone', False):
            return Popen(cmd).pid
        else:
            return check_output(cmd)
