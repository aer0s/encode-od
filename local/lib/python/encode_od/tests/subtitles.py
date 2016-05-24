import sys, os, shutil
proj_dir = os.path.realpath(__file__)
for i in range(6):
    proj_dir = os.path.dirname(proj_dir)
sys.path.append(os.path.join(proj_dir,'local','lib','python'))
from encode_od.utils import odTools

testdir = os.path.join('/tmp', 'Dvd')

cli = odTools(output='/tmp', title='Dvd')


def preload_data():
    os.makedirs(testdir, exist_ok=True)
    for fp in ['Dvd.mkv']:
        print('Coping %s ...' % fp)
        shutil.copy(os.path.join(proj_dir, 'testdata', fp), testdir)
        print('done.')


def main():
    print('...............Testing Subtitles.............')
    cli.convert_subtitles()


if __name__ == '__main__':
    main()
