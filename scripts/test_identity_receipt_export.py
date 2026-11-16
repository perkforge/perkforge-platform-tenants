import copy,contextlib,io,json,pathlib,runpy,unittest
from identity_receipt_export import build
from identity_foundation import build as foundation
root=pathlib.Path(__file__).resolve().parents[1]
d=json.loads((root/'declarations/identity/portal.json').read_text());f=json.loads((root/'declarations/identity/foundation.json').read_text())
F={'D':d,'I':f['initializer'],'network':f['network'],'custody':f['custody']}
class Export(unittest.TestCase):
 def test_default_unchanged_and_optin_only_writer(self):
  a=foundation(F['D'],F['network'],F['custody'],F['I']);b=foundation(F['D'],F['network'],F['custody'],F['I'],True)
  changes=[(x,y) for x,y in zip(a,b) if x!=y];self.assertEqual(len(changes),1);self.assertEqual(changes[0][0]['metadata']['name'],'identity-pods-'+build(F['D'],F['I'])['metadata']['namespace'])
 def test_fixed_readonly(self):
  p=build(F['D'],F['I']);s=p['spec'];self.assertFalse(s['automountServiceAccountToken']);self.assertNotIn('fsGroup',s['securityContext']);self.assertNotIn('initContainers',s);self.assertTrue(s['volumes'][0]['persistentVolumeClaim']['readOnly']);self.assertTrue(all(m['readOnly'] for m in s['containers'][0]['volumeMounts']));self.assertNotIn('platform.perkforge.io/identity-phase',p['metadata']['labels'])
 def test_service_account_from_reviewed_phase(self):
  from finite_identity import render
  self.assertEqual(build(F['D'],F['I'])['spec']['serviceAccountName'],render(F['D'])['foundation/job.yaml']['spec']['template']['spec']['serviceAccountName'])
 def test_materialized_optin(self):
  from render_identity_foundation import render as material
  from identity_gitops_ownership import sha
  base=copy.deepcopy(f);base.pop('receiptExport',None)
  base['ownership']['foundationSHA256']=sha(foundation(d,base['network'],base['custody'],base['initializer']))
  original=material(d,base)
  off=copy.deepcopy(base);off['receiptExport']={'schemaVersion':1,'enabled':False};self.assertEqual(material(d,off),original)
  on=copy.deepcopy(off);on['receiptExport']['enabled']=True
  with self.assertRaises(ValueError):material(d,on) # old complete foundation digest is refused
  on['ownership']['foundationSHA256']=sha(foundation(d,on['network'],on['custody'],on['initializer'],True))
  files,bootstrap=material(d,on)
  self.assertFalse(any(o['kind'] in ('Pod','Job') for o in files.values()))
  for k in ('bootstrapGuards','bootstrapGrants'):self.assertEqual(bootstrap[k],original[1][k])
  for invalid in (True,{'enabled':True},{'schemaVersion':True,'enabled':True},{'schemaVersion':1,'enabled':1},{'schemaVersion':1,'enabled':True,'extra':1}):
   bad=copy.deepcopy(f);bad['receiptExport']=invalid
   with self.assertRaises(ValueError):material(d,bad)
 def test_transport(self):
  from identity_receipt_export import verify_transport
  import base64,hashlib
  raw=b'{ "original": true }\n';v={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'base64':base64.b64encode(raw).decode()}
  e={'schemaVersion':1,'podUID':'uid','selection':{'context':'portal'},'files':{n:dict(v) for n in ('gitlab-group.json','foundation-result.json')}}
  self.assertTrue(all(x==raw for x in verify_transport(json.dumps(e).encode(),'uid',e['selection']).values()))
  with self.assertRaises(ValueError):verify_transport(json.dumps(e).encode(),'foreign',e['selection'])
  e['files']['gitlab-group.json']['sha256']='0'*64
  with self.assertRaises(ValueError):verify_transport(json.dumps(e).encode(),'uid',e['selection'])
 def test_target_mismatch(self):
  for k in ('claim','node','pullSecret'):
   i=copy.deepcopy(F['I']);i[k]='foreign'
   with self.assertRaises(ValueError):build(F['D'],i)
if __name__=='__main__':unittest.main()
