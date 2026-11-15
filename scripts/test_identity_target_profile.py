import contextlib,copy,hashlib,io,json,pathlib,runpy,unittest
from identity_target_profile import PILOT,validate,legacy_profile
from finite_identity import render
from identity_foundation import build
from private_receipts import plan,guard
from test_private_receipts import Private
with contextlib.redirect_stdout(io.StringIO()):F=runpy.run_path(str(pathlib.Path(__file__).with_name('identity_foundation_cases.py')))
ALT=json.loads((pathlib.Path(__file__).resolve().parents[1]/'profiles/identity/portal-alternate-example.json').read_text())
def sha(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
class Profiles(unittest.TestCase):
 def test_pilot_exact_old_tree(self):
  # Reviewed PR90 c742d8d, synthetic fixture, complete object bytes (canonical JSON).
  self.assertEqual(sha(render(F['D'])),'108e4f1162eb99fa3d614616c6dd2c618c013c72a030969b6a5f8e4fe4b19970')
  self.assertEqual(sha(build(F['D'],F['network'],F['custody'],F['I'])),'4bf1e03b405b43ef30da018dae81ffae5aead2e0027e0d5a964b9053a5978dd7')
  self.assertEqual(sha(plan(F['I'])),'b401f30b6e34028cb6f48837a22edad682282fc72c228b92f148f27946b612dc')
 def test_alternate_environment(self):
  d=copy.deepcopy(F['D']);d['targetProfile']=ALT;i=copy.deepcopy(F['I']);i['storageProfile']=ALT['storage'];g=render(d);o=build(d,F['network'],F['custody'],i)
  api=next(v for v in g['attest/job.yaml']['spec']['template']['spec']['volumes'] if v['name']=='api')
  self.assertEqual(api['projected']['sources'][0]['serviceAccountToken']['audience'],ALT['apiAudience'])
  pvc=next(x for x in o if x['kind']=='PersistentVolumeClaim');self.assertEqual(pvc['spec']['storageClassName'],'retained-longhorn');self.assertEqual(pvc['spec']['resources']['requests']['storage'],'2Gi')
  n=next(x for x in o if x['kind']=='NetworkPolicy' and x['metadata']['name']=='identity-worker-egress' and x['metadata']['namespace']=='tenant-identity-attestor')['spec']['egress']
  self.assertEqual(n[0]['to'][0]['namespaceSelector']['matchLabels'],ALT['dns']['namespaceLabels']);self.assertEqual(n[0]['ports'][0]['port'],5353);self.assertEqual(n[2]['ports'][0]['port'],9443);self.assertEqual(n[-1]['ports'][0]['port'],7443)
  self.assertNotEqual(g['foundation/job.yaml']['metadata']['name'],render(F['D'])['foundation/job.yaml']['metadata']['name'])
  self.assertEqual(g,render(copy.deepcopy(d)))
 def test_each_field_binds_attempt(self):
  changes=[('apiAudience',None,'https://api.example.test'),('dns','port',5353),('dns','podLabels',{'app':'dns'}),('dns','namespaceLabels',{'name':'dns'}),('ingress','frontendPort',4443),('ingress','backendPort',9443),('ingress','podLabels',{'app':'ingress'}),('ingress','namespaceLabels',{'name':'ingress'}),('api','servicePort',4443),('api','backendPort',7443),('storage','className','retained'),('storage','size','2Gi')]
  original=render(F['D'])['foundation/job.yaml']['metadata']['name']
  for k,f,v in changes:
   d=copy.deepcopy(F['D'])
   if f is None:d['targetProfile'][k]=v
   else:d['targetProfile'][k][f]=v
   self.assertNotEqual(render(d)['foundation/job.yaml']['metadata']['name'],original,(k,f))
 def test_legacy_identity_is_pinned(self):
  self.assertTrue(legacy_profile(PILOT));p=copy.deepcopy(PILOT);p['dns']['port']=5353;self.assertFalse(legacy_profile(p))
 def test_fail_closed(self):
  bad=[{},dict(PILOT,extra=True),dict(PILOT,schemaVersion=True),dict(PILOT,apiAudience='*')]
  for field,value in [('provider','generic'),('size','0Gi'),('size','100Gi'),('className','*')]:p=copy.deepcopy(PILOT);p['storage'][field]=value;bad.append(p)
  for field,value in [('port',True),('port',0),('port',65536),('podLabels',{}),('namespaceLabels',{})]:p=copy.deepcopy(PILOT);p['dns'][field]=value;bad.append(p)
  for p in bad:
   with self.assertRaises(ValueError):validate(p)
  d=copy.deepcopy(F['D']);d.pop('targetProfile')
  with self.assertRaises(ValueError):render(d)
  d=copy.deepcopy(F['D']);d['context']='other'
  with self.assertRaises(ValueError):render(d)
 def test_storage_guard_is_exact(self):
  i,c,p,v=Private().fixture();i['storageProfile']=ALT['storage']
  with self.assertRaises(ValueError):guard(i,c,p,v,[])
  p['spec']['storageClassName']='retained-longhorn';p['spec']['resources']['requests']['storage']='2Gi';self.assertTrue(guard(i,c,p,v,[]))
  v['spec']['csi']['driver']='other'
  with self.assertRaises(ValueError):guard(i,c,p,v,[])
if __name__=='__main__':unittest.main()
