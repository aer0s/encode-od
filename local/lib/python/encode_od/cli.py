import os
import click
from encode_od.utils import odTools


@click.command()
@click.option('--source', '-s', default=0,
              help='Device Source Integer, ie /dev/sr0 [default: 0]')
@click.option('--output', '-o', default=os.path.join(os.getcwd(), 'output'),
              help='Absolute path of Output Directory [default: ./output]')
@click.option('--force', is_flag=True, help='Force overwrite')
@click.option('--no-logging', is_flag=True, help='Disable logging')
@click.option('--eject-disc', is_flag=True, help='Eject\'s on completion')
@click.option('--mkv-only', is_flag=True, help='Restricts output to MKV')
@click.option('--title', help='Override disc title')
@click.option('--notify', '-n', default=False, multiple=True,
              help='Email address to notify')
@click.option('--email-sender', '-f', default='encode@optical.disc',
              help='Email sender address')
@click.option('--email-host', '-h', default='localhost', help='Email provider')
@click.option('--email-port', '-l', default=25, help='Email port')
@click.option('--starttls', '-t', is_flag=True, help='Email starttls')
@click.option('--email-user', '-u', default=False, help='Email user')
@click.option('--email-pass', '-p', default=False, help='Email password')
@click.option('--event-start', default=False,
              help='Shell execute this command on Start Event')
@click.option('--event-disc-done', default=False,
              help='Shell execute this command on Done with Disc Event')
@click.option('--event-done', default=False,
              help='Shell execute this command on All Done Event')
def main(source, output, force, no_logging, eject_disc, mkv_only, title,
         notify, email_sender, email_host, email_port, starttls, email_user,
         email_pass, event_start, event_disc_done, event_done):
    email_obj, send = False, False
    logging = True if not no_logging else False
    if notify:
        send = True
        email_obj = {
            'sender': email_sender,
            'receivers': notify,
            'subject': 'Encoding %(title)s',
            'host': email_host,
            'port': email_port,
            'starttls': starttls,
            'user': email_user,
            'password': email_pass,
            }
    t = title if title else False
    cli = odTools(output=output, email=email_obj, logging=logging, title=t)
    # get the movie title
    cli.get_dvd_name(source)
    cli.log('Encoding started.', notify=send)

    # If this has already been done then kill this attempt unless forced
    if not any([cli.isdone(), cli.islocked()]) or force:
        if event_start:
            cli.shell(event_start, shell=True, standalone=True)

        # rip to mkv
        cli.lock()  # Lock the optical mediums from additional encodeOD process
        cli.log('Rip to mkv')
        try:
            cli.makemkv(source)
        except Exception as Err:
            cli.log('MakeMKV encode Failure!:\n%s' % str(Err), notify=send)
            try:
                cli.log('Attempting to encode with HandBrake', notify=send)
                cli.handbrake('/dev/sr%d' % source, 'mkv')
            except Exception as Err:
                cli.log(
                    'HandBrake MKV encode Failure!:\n%s' % str(Err),
                    notify=send
                    )
                cli.lock(False)
                exit()

        cli.lock(False)  # Unlock the optical mediums for add encodeOD process
        if event_disc_done:
            cli.shell(event_disc_done, shell=True, standalone=True)
        if eject_disc:
            cli.eject(source)

        # Convert and insert subtitles
        cli.log('Convert and insert subtitles')
        try:
            cli.convert_subtitles()
        except Exception as Err:
            cli.log('Subtitle Failure!:\n%s' % str(Err), notify=send)

        if not mkv_only:
            # Encode mp4
            cli.log('Encode mp4')
            try:
                cli.ffmpeg()
            except Exception as Err:
                cli.log('FFmpeg Failure!:\n%s' % str(Err), notify=send)
                exit()

        with open(cli.paths['actual']['done'], 'w') as f:
            pass
        cli.log('Encoding finished.', notify=send)
        if event_done:
            cli.shell(event_done, shell=True, standalone=True)
    else:
        if cli.islocked:
            cli.log(' '.join([
                'The od devices are locked because some other process is',
                'using one of them. If you would like to do it anyway plese ',
                'use --force option.'
                ]), notify=send)
        else:
            cli.log(' '.join([
                'This od has been encoded already. If you would like to do it',
                'anyway plese use --force option.'
                ]), notify=send)


if __name__ == "__main__":
    main()
