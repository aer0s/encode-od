# encode-od

Auto encode optical disc with makemkv-cli, hanbrake-cli, ffmpeg with subtitles. Currently, subtitles are limited to English only. This script will create two encoded files: **mkv** & **m4v**

## Prerequisites

-   python >= 2.7
-   ffmpeg
-   makemkvcon
-   HandBrakeCLI
-   vobsub2srt
-   tesseract
-   tesseract-eng
-   mkvtoolnix

## Usage Quick Guide

Insert a DVD or BD and then execute the following command:

```bash
$ ./local/bin/encode-od #will encode the content of /dev/sr0

# encode /dev/sr1 to a folder in the /tmp directory.
$ ./local/bin/encode-od -s 1 -o /tmp/movies
```

## Options

EncodeOD has several configuration options that can be passed via the command line or vi the [Preference File](#preference-file).

### Encoding

|     Argument     |    Type    |          Default          | Description                                                                                                                                    |
| :--------------: | :--------: | :-----------------------: | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `-s`, `--source` |  _INTEGER_ |             0             | Specify the Device Source of the optical media. ie **0** for \*/dev/sr**0\***                                                                  |
| `-o`, `--output` |  _STRING_  |         `./output`        | Specify the absolute path Output Directory for the encode. By default it will use a folder called **_output_** in the encode_od git directory. |
|     `--force`    |   _FLAG_   |                           | Force overwrite in output directory                                                                                                            |
|  `--no-logging`  |   _FLAG_   |                           | Disable logging (this is a flag; if passed logging is disabled otherwise a rip.log is created in the output directory)                         |
|  `--eject-disc`  |   _FLAG_   |                           | Eject's disc when done reading.                                                                                                                |
|   `--mkv-only`   |   _FLAG_   |                           | Restricts output to MKV                                                                                                                        |
|     `--title`    |  _STRING_  |     _Reads from disc_     | Specify disc title.                                                                                                                            |
|   `--pref-file`  | \__STRING_ | `~/.config/encode-od.yml` | Preference file location                                                                                                                       |
|     `--help`     |   _FLAG_   |                           | Show this message and exit.                                                                                                                    |

### Notifications

|        Argument        |    Type   |        Default        | Description                                                                                                                      |
| :--------------------: | :-------: | :-------------------: | -------------------------------------------------------------------------------------------------------------------------------- |
|    `-n`, `--notify`    |  _STRING_ |         False         | Email address to notify, accepts multiple addresses with additional declaration. _i.e._ `-n xx@yy.com -n yy@xx.com -n xy@yx.com` |
| `-f`, `--email-sender` |  _STRING_ | `encode@optical.disc` | Email sender address                                                                                                             |
|  `-h`, `--email-host`  |  _STRING_ |      `localhost`      | Email provider                                                                                                                   |
|  `-l`, `--email-port`  | _INTEGER_ |          `25`         | Email port                                                                                                                       |
|   `-t`, `--starttls`   |   _FLAG_  |         False         | Email using starttls (this is a flag; if passed then True, default is False)                                                     |
|  `-u`, `--email-user`  |  _STRING_ |         False         | Email user                                                                                                                       |
|  `-p`, `--email-pass`  |  _STRING_ |         False         | Email password                                                                                                                   |

### Events

|       Argument      |   Type   | Default | Description                                                      |
| :-----------------: | :------: | :-----: | ---------------------------------------------------------------- |
|   `--event-start`   | _STRING_ |         | Additional shell command to trigger when encoding is started     |
| `--event-disc-done` | _STRING_ |         | Additional shell command to trigger when done reading from disc. |
|    `--event-done`   | _STRING_ |         | Additional shell command to trigger when encoding is complete    |

## Preference File

Configuration options can be specified in a single yaml file in lue of suppling them in the command line. Use the long form of the command argument names. By default the command line tool expects this configuration yaml to be located at `~/.config/encode_od`

**NOTE:** Replace _hyphens_ with _underscores_ in option argument names. For example: `--email-host` becomes `email_host`  

```yaml
output: ~/Videos
notify:
    - xx@yy.com
    - yy@xx.com
    - xy@yx.com
email_host: smtp.gmail.com
email_port: 587
email_user: some.user
email_pass: Password
starttls: true
```

## SystemD Service

On possible way to daemonize this application as a service so that it automatically encodes Optical Disc's on insertion would be to use SystemD. Here is an example: _(provided that you have configured a [Preference File](#preference-file))_

_**`/etc/systemd/system/encode-od.service`**_

```systemd
[Unit]
Description=Encode Optical Disc Service
After=syslog.target

[Service]
Type=simple
User=username
Group=user
WorkingDirectory=/opt/encode-od/
ExecStart=python /opt/encode-od/local/lib/python/encode_od/daemon.py

[Install]
WantedBy=multi-user.target
```

### TODO

-   [x] Make options importable by yaml file
-   [ ] Simplify notifications
-   [x] Add event triggers
-   [ ] Add Telegram bot command integration
-   [ ] Make handbrake/makemkv optional switch
-   [ ] Add self install/removal script
