import base64,fcntl,hashlib,importlib.util,json,os,pathlib,tempfile,unittest
s=importlib.util.spec_from_file_location('reader',pathlib.Path(__file__).with_name('read-original-receipts.py'));r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
class Original(unittest.TestCase):
 def setUp(self):
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
 def test_exclusive_lock(self):
  with open(self.p/'trigger.lock','rb') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
   with self.assertRaises(BlockingIOError):r.extract(self.e,str(self.p))
if __name__=='__main__':unittest.main()
