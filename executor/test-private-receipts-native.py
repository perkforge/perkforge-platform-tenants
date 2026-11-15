"""Runs inside exact maintained image; synthetic disposable filesystem only."""
import importlib.util,os,pathlib,tempfile,unittest
s=importlib.util.spec_from_file_location('init','/source/initialize-private-receipts.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Native(unittest.TestCase):
 def root(self):
  t=tempfile.TemporaryDirectory(dir='/tmp');os.chmod(t.name,0o2770);return t
 def test_success_and_no_adoption(self):
  with self.root() as d:
   r=m.initialize(d);self.assertTrue(r['markerRemoved']);p=pathlib.Path(d)/'private';self.assertEqual(p.stat().st_mode&0o777,0o700);self.assertEqual(p.stat().st_uid,1001);self.assertEqual(list(p.iterdir()),[])
   with self.assertRaises(ValueError):m.initialize(d)
 def test_foreign_and_symlink(self):
  for kind in ('file','symlink','lost-content','lost-link'):
   with self.root() as d:
    p=pathlib.Path(d)
    if kind=='file':(p/'foreign').write_text('keep')
    elif kind=='symlink':(p/'private').symlink_to('/tmp')
    elif kind=='lost-link':(p/'lost+found').symlink_to('/tmp')
    else:(p/'lost+found').mkdir();(p/'lost+found'/'foreign').write_text('keep')
    with self.assertRaises((ValueError,OSError)):m.initialize(d)
 def test_empty_lostfound(self):
  with self.root() as d:(pathlib.Path(d)/'lost+found').mkdir();self.assertTrue(m.initialize(d)['markerRemoved'])
 def test_failure_removes_only_marker(self):
  with self.root() as d:
   old=m.os.fsync
   def fail(fd):raise OSError('synthetic fsync failure')
   m.os.fsync=fail
   try:
    with self.assertRaises(OSError):m.initialize(d)
   finally:m.os.fsync=old
   self.assertEqual(list((pathlib.Path(d)/'private').iterdir()),[])
unittest.main()
