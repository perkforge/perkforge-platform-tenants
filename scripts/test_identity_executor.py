#!/usr/bin/env python3
import importlib.util,pathlib,tempfile,unittest,os,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('runtime',ROOT/'executor/verify-runtime.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Runtime(unittest.TestCase):
 def test_projection_inside_and_escape(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)/'projection';root.mkdir();(root/'version').mkdir()
   (root/'version'/'token').write_bytes(b'fixture');(root/'token').symlink_to('version/token')
   self.assertEqual(m.projected(str(root/'token'),str(root),32),b'fixture')
   (root/'bad').symlink_to('/etc/passwd')
   with self.assertRaises(ValueError):m.projected(str(root/'bad'),str(root),65536)
 def test_bounds_fifo(self):
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'file';p.write_bytes(b'x'*33)
   with self.assertRaises(ValueError):m.bounded(str(p),32)
   fifo=pathlib.Path(d)/'fifo';os.mkfifo(fifo)
   with self.assertRaises(ValueError):m.bounded(str(fifo),32)
 def test_launcher_rejects_before_provider(self):
  r=subprocess.run(['bash',str(ROOT/'executor/reconcile-identity'),'--context','../foreign'],capture_output=True,timeout=3)
  self.assertEqual(r.returncode,2)
 def test_source_has_no_runtime_install_or_network_fetch(self):
  s=(ROOT/'executor/reconcile-identity').read_text()
  for bad in ('pip install','apt-get','git clone','curl ','wget '):self.assertNotIn(bad,s)
  self.assertIn('flock -n 9',s)
  self.assertIn('sha256sum --strict -c provenance.sha256',s)
if __name__=='__main__':unittest.main()
