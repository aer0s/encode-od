# encode-od
Auto encode optical disc with makemkv-cli, hanbrake-cli, ffmpeg with subtitles. Currently, subttles are limited to English only.
This script will create two encoded files: __mkv__ & __m4v__

## Prerequisites
 - python >= 2.7
 - ffmpeg
 - makemkvcon
 - HandBrakeCLI
 - vobsub2srt
 - tesseract
 - tesseract-eng
 - mkvtoolnix

## Usage Quick Guide
Insert a DVD or BD and then execute the following command:
```bash
$ ./local/bin/encode-od #will encode the content of /dev/sr0

# encode /dev/sr1 to a folder in the /tmp directory.
$ ./local/bin/encode-od -s 1 -o /tmp/movies

```

### Options:
 - __-s, --source__ *INTEGER*      Specify the Device Source of the optical media. ie __0__ for */dev/sr__0__*
 - __-o, --output__ *TEXT*         Specify the absolute path Output Directory for the encode. By default it will use a folder called __*output*__ in the encode_od git directory.
 - __--no-logging__                Disable logging [this is a flag; if passed logging is disabled otherwise a rip.log is created in the output dir]
 - __-n, --notify__ *TEXT*         Email address to notify
 - __-f, --email-sender__ *TEXT*   Email sender address
 - __-h, --email-host__ *TEXT*     Email provider
 - __-l, --email-port__ *INTEGER*  Email port
 - __-t, --starttls__              Email using starttls [this is a flag; if passed then True, default is False]
 - __-u, --email-user__ *TEXT*     Email user
 - __-p, --email-pass__ *TEXT*     Email password
 - __--help__                    Show this message and exit.

### TODO
 - Make options importable by yaml file
 - Simplify notifications
 - Add event triggers
 - Add Telegram bot command integration
 - Make handbrake/makemkv optional switch
 - Add self install/removal script
