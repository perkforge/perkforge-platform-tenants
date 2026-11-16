"""Every fixed syscall stage refuses EACCES without content or fallback."""
import contextlib,errno,importlib.util,io,json,pathlib,unittest
from unittest import mock
s=importlib.util.spec_from_file_location('original',pathlib.Path(__file__).with_name('test_original_receipts.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
r=f.r
class Stages(f.Original):
 def run_cli(self,target=None):
  native=r.syscall;extract=r.extract;seen=[]
  def denied(*a,**kw):raise PermissionError(errno.EACCES,'PRIVATE exception path and content')
  def call(stage,operation,*a,**kw):
   seen.append(stage)
   if stage==target:operation=denied
   elif stage=='PodIdentityOpen':operation=lambda *a,**kw:io.BytesIO(b'35671d30-0dd4-43cb-9489-3b98fc2b1f73')
   return native(stage,operation,*a,**kw)
  out,err=io.StringIO(),io.StringIO()
  with mock.patch.object(r,'syscall',call),mock.patch.object(r,'extract',lambda expected:extract(expected,str(self.p))),contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
   status=r.main(['reader',json.dumps(self.e)])
  return status,out.getvalue(),err.getvalue(),seen
 def test_every_eacces_stage(self):
  before={p.name:p.read_bytes() for p in self.p.iterdir()}
  for stage in sorted(r.STAGES):
   with self.subTest(stage=stage):
    status,out,err,seen=self.run_cli(stage)
    self.assertEqual(status,1);self.assertEqual(out,'')
    self.assertEqual(err,'OriginalReceiptExtractionRefused:'+stage+'FilesystemErrno13\n')
    self.assertEqual(seen[-1],stage)
    self.assertEqual({p.name:p.read_bytes() for p in self.p.iterdir()},before)
 def test_success_visits_all_stages(self):
  status,out,err,seen=self.run_cli()
  self.assertEqual(status,0);self.assertEqual(err,'');self.assertEqual(set(seen),r.STAGES)
  self.assertEqual(set(json.loads(out)['files']),{'gitlab-group.json','foundation-result.json'})
 def test_unknown_stage_refused(self):
  with self.assertRaises(ValueError):r.syscall('PRIVATE path',lambda:None)
if __name__=='__main__':unittest.main()
