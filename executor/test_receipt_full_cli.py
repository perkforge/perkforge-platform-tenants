"""Cached-image only: exact -c command and AtomicWriter-style UID projection."""
import importlib.util,json,os,pathlib,subprocess,sys,unittest
BASE=pathlib.Path(__file__).parent
s=importlib.util.spec_from_file_location('fixtures',BASE/'test_original_receipts.py');f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
class CLI(unittest.TestCase):
 def test_cli(self):
  fixture=f.Original();fixture.setUp()
  try:
   root=pathlib.Path('/original-receipts');os.chmod(root,0o700)
   for p in fixture.p.iterdir():
    q=root/p.name;q.write_bytes(p.read_bytes());os.chmod(q,0o600)
   identity=pathlib.Path('/reader-identity');version=identity/'..2026';version.mkdir();(version/'uid').write_text('35671d30-0dd4-43cb-9489-3b98fc2b1f73');(identity/'..data').symlink_to(version.name);(identity/'uid').symlink_to('..data/uid')
   script=(BASE/'read-original-receipts.py').read_text();command=[sys.executable,'-B','-c',script,json.dumps(fixture.e)]
   p=subprocess.run(command,capture_output=True);self.assertEqual(p.returncode,0,p.stderr.decode());self.assertEqual(json.loads(p.stdout)['podUID'],'35671d30-0dd4-43cb-9489-3b98fc2b1f73')
   os.chmod(root,0o2770);p=subprocess.run(command,capture_output=True);self.assertEqual(p.returncode,1);self.assertEqual(p.stderr,b'OriginalReceiptExtractionRefused:DirectoryGuard\n');self.assertEqual(p.stdout,b'')
  finally:fixture.tearDown()
if __name__=='__main__':unittest.main()
