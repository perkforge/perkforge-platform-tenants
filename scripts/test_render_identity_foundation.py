import copy,json,pathlib,tempfile,unittest
from render_identity_foundation import render,materialize
from test_identity_foundation import F
from test_identity_gitops_ownership import sample
class Source(unittest.TestCase):
 def config(self):
  _,s=sample();s['sourceName']=F['D']['sourceName'];s['sourcePath']='./generated/identity-foundation/portal'
  return {'schemaVersion':1,'enabled':True,'network':F['network'],'custody':F['custody'],'initializer':None,'ownership':s}
 def test_disabled_empty(self):
  files,b=render({'schemaVersion':1,'context':'portal','enabled':False},{'schemaVersion':1,'enabled':False})
  self.assertEqual(files['kustomization.yaml']['resources'],[]);self.assertEqual(b,{'enabled':False})
 def test_stages_and_bootstrap_separate(self):
  files,b=render(F['D'],self.config());self.assertEqual(len(files['kustomization.yaml']['resources']),2)
  self.assertEqual(len(b['bootstrapGuards']),4);self.assertEqual(len(b['bootstrapGrants']),8)
  for o in files.values():self.assertNotIn(o['kind'],('Secret','Namespace','PersistentVolumeClaim','Pod','Job','ClusterRole','ClusterRoleBinding'))
  self.assertEqual((files,b),render(F['D'],self.config()))
 def test_mismatch_refused(self):
  for key,value in [('runtimeNamespaces',['foreign','other']),('sourceName','foreign'),('sourceNamespace','foreign'),('sourcePath','./foreign'),('foundationSHA256','0'*64)]:
   c=self.config();c['ownership'][key]=value
   with self.assertRaises(ValueError):render(F['D'],c)
 def test_disabled_unknowns_refused(self):
  with self.assertRaises(ValueError):render(F['D'],{'schemaVersion':1,'enabled':False,'extra':True})
 def test_freshness_and_no_implicit_cleanup(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=pathlib.Path(tmp);p=r/'declarations/identity';p.mkdir(parents=True)
   (p/'portal.json').write_text(json.dumps({'schemaVersion':1,'context':'portal','enabled':False}))
   (p/'foundation.json').write_text(json.dumps({'schemaVersion':1,'enabled':False}))
   materialize(r);materialize(r,True)
   (r/'generated/identity-foundation/portal/foreign.yml').write_text('{}')
   with self.assertRaises(ValueError):materialize(r,True)
   with self.assertRaises(ValueError):materialize(r)
if __name__=='__main__':unittest.main()
