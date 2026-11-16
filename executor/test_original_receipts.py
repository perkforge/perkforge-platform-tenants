import base64,fcntl,hashlib,importlib.util,json,os,pathlib,tempfile,unittest
from unittest import mock
from types import SimpleNamespace
s=importlib.util.spec_from_file_location('reader',pathlib.Path(__file__).with_name('read-original-receipts.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Original(unittest.TestCase):
 def setUp(self):
  # CI portability only: map this test process owner to the contract UID.
  # Cached-image execution at UID1001 exercises actual native ownership unchanged.
  if os.getuid()!=1001:
   native=os.fstat
   def owned(fd):
    s=native(fd);return SimpleNamespace(**{k:(1001 if k=="st_uid" and getattr(s,k)==os.getuid() else getattr(s,k)) for k in ("st_uid","st_mode","st_nlink","st_size","st_ino","st_mtime_ns")})
   proxy=SimpleNamespace(**{k:getattr(os,k) for k in dir(os) if not k.startswith("__")});proxy.fstat=owned
   patch=mock.patch.object(r,"os",proxy);patch.start();self.addCleanup(patch.stop)
  self.t=tempfile.TemporaryDirectory();self.p=pathlib.Path(self.t.name);os.chmod(self.p,0o700)
  self.e=dict(context='portal',invocation='a'*64,source_revision='b'*40,platform_revision='c'*40,parent_id=7,origin='https://example.test')
  self.g=dict(schema=1,stage='group-ready',context='portal',source_revision='b'*40,parent_id=7,origin='https://example.test',group_id=9,previous_revisions=[])
  self.f=dict(schema=1,phase='GroupReady',context='portal',invocation='a'*64,source_revision='b'*40,platform_revision='c'*40,parent_id=7,group_id=9,captured_at='2026-11-16T00:00:00Z')
  self.write('gitlab-group.json',json.dumps(self.g,indent=2).encode());self.write('foundation-result.json',json.dumps(self.f).encode());self.write('trigger.lock',b'')
 def tearDown(self):self.t.cleanup()
 def write(self,n,b):
  (self.p/n).write_bytes(b);os.chmod(self.p/n,0o600)
 def test_original_bytes(self):
  before={p.name:p.read_bytes() for p in self.p.iterdir()};out=r.extract(self.e,str(self.p));self.assertEqual({p.name:p.read_bytes() for p in self.p.iterdir()},before)
  for n,item in out.items():self.assertEqual(base64.b64decode(item['base64']),before[n]);self.assertEqual(item['sha256'],hashlib.sha256(before[n]).hexdigest())
 def test_symlink_fifo_oversize_mode(self):
  n=self.p/'gitlab-group.json';original=n.read_bytes()
  for kind in ('symlink','fifo','oversize','mode'):
   n.unlink()
   if kind=='symlink':n.symlink_to(self.p/'foundation-result.json')
   elif kind=='fifo':os.mkfifo(n,0o600)
   else:self.write(n.name,b'x'*4097 if kind=='oversize' else original)
   if kind=='mode':os.chmod(n,0o644)
   with self.assertRaises((ValueError,OSError)):r.extract(self.e,str(self.p))
 def test_wrong_attempt_and_group(self):
  for k,v in [('invocation','d'*64),('group_id',10),('context','foreign')]:
   f=dict(self.f);f[k]=v;self.write('foundation-result.json',json.dumps(f).encode())
   with self.assertRaises(ValueError):r.extract(self.e,str(self.p))
 def test_hardlinks_and_nonempty_lock(self):
  for name in ('gitlab-group.json','foundation-result.json','trigger.lock'):
   alias=self.p/'alias';os.link(self.p/name,alias)
   with self.assertRaises(ValueError):r.extract(self.e,str(self.p))
   alias.unlink()
  self.write('trigger.lock',b'x')
  with self.assertRaises(ValueError):r.extract(self.e,str(self.p))
 def test_duplicate_keys(self):
  for name in ('gitlab-group.json','foundation-result.json'):
   p=self.p/name;old=p.read_bytes();self.write(name,b'{"schema":1,'+old.lstrip()[1:])
   with self.assertRaises(ValueError):r.extract(self.e,str(self.p))
   self.write(name,old)
 def test_exclusive_lock(self):
  with open(self.p/'trigger.lock','rb') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaises(BlockingIOError):r.extract(self.e,str(self.p))
if __name__=='__main__':unittest.main()
