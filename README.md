# encode-od
Auto encode optical disc with makemkv-cli, hanbrake-cli, ffmpeg with subtitles. This script will create two encoded files: __mkv__ & __m4v__

## Prerequisites
 - python >= 2.7
 - makemkvcon
 - HandBrakeCLI
 - vobsub2srt
 - mkvtoolnix

## Usage Quick Guide
Insert a DVD or BD and then execute the following command:
```bash
$ ./local/bin/encode-od #will encode the content of /dev/sr0

# encode /dev/sr1 to a folder in the /tmp directory.
$ ./local/bin/encode-od -s 1 -o /tmp/movies

```

### Options
 - __--source, -s__ : Specify the Device Source of the optical media. ie __0__ for */dev/sr__0__*
 - __--output, -o__ : Specify the absoulte path Output Directory for the encode. By default it will use a folder called __*output*__ in the encode_od git directory.
