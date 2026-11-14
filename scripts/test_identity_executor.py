#!/usr/bin/env python3
import importlib.util,pathlib,tempfile,unittest,os,subprocess,sys,json
sys.dont_write_bytecode=True
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
 def test_pinned_group_input_guard_rejects_injection(self):
  guardpath=os.environ.get('GROUP_GUARD')
  if not guardpath:self.skipTest('exact pinned adapter required')
  sp=importlib.util.spec_from_file_location('guard',guardpath);guard=importlib.util.module_from_spec(sp);sp.loader.exec_module(guard)
  valid={'gitlab_group_run':True,'gitlab_group_scope':'gitlab-enrollment-group-foundation-v1','gitlab_group_context':'portal','gitlab_group_source_revision':'a'*40,'gitlab_group_expected_parent_id':1,'gitlab_native_origin':'https://gitlab.example.test','gitlab_native_ca_file':'/credentials/ca.crt'}
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d)/'inputs.json';p.write_text(json.dumps(valid));self.assertEqual(guard.validate_inputs(str(p)),valid)
   for patch in ({'group_prior':{}},{'executor_token_file':'/escape'},{'gitlab_native_origin':"{{ lookup('pipe','touch /tmp/forbidden') }}"},{'gitlab_group_expected_parent_id':True}):
    p.write_text(json.dumps(valid|patch))
    with self.assertRaises(ValueError):guard.validate_inputs(str(p))
   p.write_text('{"gitlab_group_context":"portal","gitlab_group_context":"foreign"}')
   with self.assertRaises(ValueError):guard.validate_inputs(str(p))
 def test_source_has_no_runtime_install_or_network_fetch(self):
  s=(ROOT/'executor/reconcile-identity').read_text()
  for bad in ('pip install','apt-get','git clone','curl ','wget '):self.assertNotIn(bad,s)
  self.assertIn('flock -n 9',s)
  self.assertIn('sha256sum --strict -c provenance.sha256',s)
if __name__=='__main__':unittest.main()
