import pyudev
import sys
import os
from os.path import dirname, join, abspath
from subprocess import Popen
import pdb


def main():
    context = pyudev.Context()
    monitor = pyudev.Monitor.from_netlink(context)
    monitor.filter_by('block', 'disk')
    encode_od_dir = dirname(abspath(__file__))

    for device in iter(monitor.poll, None):
        if 'ID_CDROM_DVD' in device and 'ID_CDROM_MEDIA_TRACK_COUNT' in device:
            # This will trigger each time a DVD with content is inserted
            # cli = join(dirname(mypath), 'cli.py')
            # Popen([sys.executable, cli, '-s%s' % device.sys_number])
            # pdb.set_trace()
            epath = join(
                dirname(dirname(dirname(encode_od_dir))), 'bin', 'encode-od'
            )
            Popen(['nohup', epath, '-s%s' % device.sys_number])


if __name__ == "__main__":
    main()
