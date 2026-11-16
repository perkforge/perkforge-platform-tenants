"""Bounded metadata only after the exact directory-open EACCES."""
import contextlib,errno,importlib.util,io,json,pathlib,stat,unittest
from types import SimpleNamespace
from unittest import mock
s=importlib.util.spec_from_file_location('reader',pathlib.Path(__file__).with_name('read-original-receipts.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Metadata(unittest.TestCase):
 def run_failure(self,stage='DirectoryOpen',code=errno.EACCES):
  exc=OSError(code,'PRIVATE path/content');exc.receipt_stage=stage
  out,err=io.StringIO(),io.StringIO()
  with mock.patch.object(r,'extract',side_effect=exc),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):status=r.main(['reader','{}'])
  self.assertEqual(status,1);self.assertEqual(out.getvalue(),'');self.assertNotIn('PRIVATE',err.getvalue())
  self.assertEqual(err.getvalue().splitlines()[0],f'OriginalReceiptExtractionRefused:{stage}FilesystemErrno{code}')
  return err.getvalue().splitlines()
 def test_metadata(self):
  meta=SimpleNamespace(st_uid=1001,st_gid=1001,st_mode=stat.S_IFDIR|0o700)
  with mock.patch.object(r.os,'lstat',return_value=meta) as probe,mock.patch.object(r.os,'geteuid',return_value=1001),mock.patch.object(r.os,'getegid',return_value=1001),mock.patch.object(r.os,'open',side_effect=AssertionError('no extra opens')),mock.patch.object(r.os,'read',side_effect=AssertionError('no reads')),mock.patch.object(r.os,'listdir',side_effect=AssertionError('no listing')),mock.patch.object(r.os,'chmod',side_effect=AssertionError('no writes')):
   lines=self.run_failure();probe.assert_called_once_with('/original-receipts')
  record=json.loads(lines[1].split(':',1)[1]);self.assertEqual(record,dict(schemaVersion=1,outcome='metadata',euid=1001,egid=1001,uid=1001,gid=1001,mode=448,type='directory'));self.assertLessEqual(len((lines[1]+'\n').encode()),1024)
 def test_unrelated_no_probe(self):
  with mock.patch.object(r.os,'lstat') as probe:
   for stage,code in [('LockOpen',13),('DirectoryOpen',2)]:self.assertEqual(len(self.run_failure(stage,code)),1)
   probe.assert_not_called()
 def test_success_no_probe(self):
  with mock.patch.object(r.os,'lstat') as probe,mock.patch.object(r,'extract',return_value={}),mock.patch('builtins.open',mock.mock_open(read_data=b'35671d30-0dd4-43cb-9489-3b98fc2b1f73')),contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()) as err:
   self.assertEqual(r.main(['reader','{}']),0);self.assertEqual(err.getvalue(),'');probe.assert_not_called()
 def test_probe_failure(self):
  for exc,outcome in [(PermissionError(13,'PRIVATE'),'lstat_errno'),(RuntimeError('PRIVATE'),'diagnostic_unavailable')]:
   with mock.patch.object(r.os,'lstat',side_effect=exc):lines=self.run_failure()
   self.assertEqual(json.loads(lines[1].split(':',1)[1])['outcome'],outcome)
 def test_symlink_is_metadata_only(self):
  with mock.patch.object(r.os,'lstat',return_value=SimpleNamespace(st_uid=1001,st_gid=1001,st_mode=stat.S_IFLNK|0o777)),mock.patch.object(r.os,'stat',side_effect=AssertionError('no follow')):lines=self.run_failure()
  self.assertEqual(json.loads(lines[1].split(':',1)[1])['type'],'symlink')
 def test_invalid_numeric(self):
  for value in [-1,2**32,True]:
   with mock.patch.object(r.os,'lstat',return_value=SimpleNamespace(st_uid=value,st_gid=1001,st_mode=stat.S_IFDIR|0o700)):lines=self.run_failure()
   self.assertEqual(json.loads(lines[1].split(':',1)[1])['outcome'],'diagnostic_unavailable')
 def test_invalid_errno_and_identity(self):
  exc=OSError('PRIVATE');exc.errno=None
  with mock.patch.object(r.os,'lstat',side_effect=exc):lines=self.run_failure()
  self.assertEqual(json.loads(lines[1].split(':',1)[1])['outcome'],'diagnostic_unavailable')
  for field in ('geteuid','getegid'):
   with mock.patch.object(r.os,'lstat',return_value=SimpleNamespace(st_uid=1001,st_gid=1001,st_mode=stat.S_IFDIR|0o700)),mock.patch.object(r.os,field,return_value=-1):lines=self.run_failure()
   self.assertEqual(json.loads(lines[1].split(':',1)[1])['outcome'],'diagnostic_unavailable')
 def test_oversize_suppressed(self):
  with mock.patch.object(r.json,'dumps',return_value='x'*1024):self.assertEqual(len(self.run_failure()),1)
 def test_serialization_and_write_failure(self):
  class Broken:
   def write(self,*a):raise OSError('PRIVATE')
  exc=PermissionError(13,'PRIVATE');exc.receipt_stage='DirectoryOpen'
  with mock.patch.object(r,'extract',side_effect=exc),mock.patch.object(r.sys,'stderr',Broken()):self.assertEqual(r.main(['reader','{}']),1)
  with mock.patch.object(r.json,'dumps',side_effect=RuntimeError('PRIVATE')):self.assertEqual(len(self.run_failure()),1)
if __name__=='__main__':unittest.main()
