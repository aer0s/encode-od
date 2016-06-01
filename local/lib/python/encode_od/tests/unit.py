import unittest
import sys
import os
import shutil
proj_dir = os.path.realpath(__file__)
for i in range(6):
    proj_dir = os.path.dirname(proj_dir)
sys.path.append(os.path.join(proj_dir, 'local', 'lib', 'python'))
from encode_od.utils import odTools

testdir = os.path.join('/tmp', 'Dvd')

cli = odTools(output='/tmp', tile='Dvd')


def preload_data():
    os.makedirs(testdir, exist_ok=True)
    for fp in ['Dvd.mkv']:
        print('Coping %s ...' % fp)
        shutil.copy(os.path.join(proj_dir, 'testdata', fp), testdir)
        print('done.')


class TestUtilMethods(unittest.TestCase):

    def test_get_name(self):
        self.assertTrue(type(cli.get_dvd_name(0)) is str)

    def test_paths(self):
        mkv = '/tmp/Dvd/Dvd.mkv'
        m4v = '/tmp/Dvd/Dvd.m4v'
        mkvCopy = '/tmp/Dvd/Dvd-working.mkv'
        idx = '/tmp/Dvd/Dvd.idx'
        srt = '/tmp/Dvd/Dvd.srt'
        sub = '/tmp/Dvd/Dvd.sub'
        subPath = '/tmp/Dvd/Dvd'
        log = '/tmp/Dvd/rip.log'
        self.assertEqual(cli.paths['actual']['mkv'], mkv)
        self.assertEqual(cli.paths['actual']['m4v'], m4v)
        self.assertEqual(cli.paths['actual']['mkvCopy'], mkvCopy)
        self.assertEqual(cli.paths['actual']['idx'], idx)
        self.assertEqual(cli.paths['actual']['srt'], srt)
        self.assertEqual(cli.paths['actual']['sub'], sub)
        self.assertEqual(cli.paths['actual']['subPath'], subPath)
        self.assertEqual(cli.paths['actual']['log'], log)

    def test_lock(self):
        cli.lock()
        self.assertTrue(cli.islocked())
        cli.lock(False)
        self.assertFalse(cli.islocked())

    def test_done(self):
        self.assertFalse(cli.isdone())
        with open(cli.paths['actual']['done']):
            pass
        self.assertTrue(cli.isdone())
        os.remove(cli.paths['actual']['done'])
        with open(cli.paths['actual']['moved']):
            pass
        self.assertTrue(cli.isdone())
        os.remove(cli.paths['actual']['moved'])

if __name__ == '__main__':
    unittest.main()
