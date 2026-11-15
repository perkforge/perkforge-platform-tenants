import contextlib,copy,hashlib,io,json,pathlib,runpy,unittest,tempfile
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
  rendered=render(F['D'])
  self.assertEqual(sha(rendered),'77f13c73245d33ae2a92fafe3e17bc1b9b172cf0d8db462a22d9a1e4c653dc8f')
  # Assert and remove only the reviewed desired-label preservation delta.
  base={'platform.perkforge.io/owner':'tenant-identity-foundation-v1','app.kubernetes.io/managed-by':'perkforge-identity','perkforge.dev/context':'portal'}
  self.assertEqual(rendered['receipt-intent.yaml']['metadata'].pop('labels'),base)
  self.assertEqual(sha(rendered),'108e4f1162eb99fa3d614616c6dd2c618c013c72a030969b6a5f8e4fe4b19970')
  foundation=build(F['D'],F['network'],F['custody'],F['I'])
  self.assertEqual(sha(foundation),'596391c60b7b10797eac3d98af560e56bd31bc12d793b2a116528f9c381f03cd')
  # Normalize only the exact declaration maintenance branch to its reviewed
  # predecessor, retaining every earlier full-tree golden assertion below.
  enc=lambda x:json.dumps(x,separators=(',',':'))
  tracked={**base,'kustomize.toolkit.fluxcd.io/name':'identity-portal','kustomize.toolkit.fluxcd.io/namespace':'flux-system'}
  adoption='(oldObject.metadata.labels == '+enc(base)+' || oldObject.metadata.labels == '+enc(tracked)+') && object.metadata.labels == '+enc(tracked)
  maintenance='(oldObject.metadata.labels == '+enc(base)+' || oldObject.metadata.labels == '+enc(tracked)+') && object.metadata.labels == oldObject.metadata.labels && has(object.metadata.annotations) == has(oldObject.metadata.annotations) && (!has(object.metadata.annotations) || object.metadata.annotations == oldObject.metadata.annotations)'
  annotation="object.metadata.annotations == {'perkforge.dev/desired-invocation': "+enc(F['D']['invocation'])+"}"
  data='has(object.data) == has(oldObject.data) && (!has(object.data) || object.data == oldObject.data)'
  current='(('+adoption+' && '+annotation+') || ('+maintenance+')) && '+data
  prior=adoption+' && '+data+' && '+annotation
  policy=next(o for o in foundation if o['kind']=='ValidatingAdmissionPolicy' and o['metadata']['name']=='identity-evidence-fields')
  expression=policy['spec']['validations'][0]['expression'];self.assertEqual(expression.count(current),1)
  policy['spec']['validations'][0]['expression']=expression.replace(current,prior)
  self.assertEqual(sha(foundation),'f75a32e5944a02d1b7569fa7aaa3add3492df2c6b13c37cdc29fbb1c92a61987')
  # Native SSA normalization adds only these exact API defaults; retain the
  # historical complete-tree assertion after removing that explicit delta.
  legacy=copy.deepcopy(foundation)
  # Explicitly deny new Pod-level budgets; retain prior complete-tree checks.
  count=0
  for o in legacy:
   if o['kind']!='ValidatingAdmissionPolicy':continue
   for validation in o['spec']['validations']:
    for prefix in ('object.spec.template.spec','object.spec'):
     term=' && !has(dyn('+prefix+').resources)'
     count+=validation['expression'].count(term)
     validation['expression']=validation['expression'].replace(term,'')
  self.assertEqual(count,7)
  self.assertEqual(sha(legacy),'79d213170c987fe1fd92bb87a5cfd4973321d7d41e254af9866c5a56607aafb0')
  # Exact reviewed declaration-only Flux tracking-label delta; retain prior tree.
  base={'platform.perkforge.io/owner':'tenant-identity-foundation-v1','app.kubernetes.io/managed-by':'perkforge-identity','perkforge.dev/context':'portal'}
  tracked={**base,'kustomize.toolkit.fluxcd.io/name':'identity-portal','kustomize.toolkit.fluxcd.io/namespace':'flux-system'}
  enc=lambda x:json.dumps(x,separators=(',',':'))
  adoption='(oldObject.metadata.labels == '+enc(base)+' || oldObject.metadata.labels == '+enc(tracked)+') && object.metadata.labels == '+enc(tracked)
  policy=next(o for o in legacy if o['kind']=='ValidatingAdmissionPolicy' and o['metadata']['name']=='identity-evidence-fields')
  expression=policy['spec']['validations'][0]['expression'];self.assertEqual(expression.count(adoption),1)
  policy['spec']['validations'][0]['expression']=expression.replace(adoption,'object.metadata.labels == oldObject.metadata.labels')
  self.assertEqual(sha(legacy),'1ee707a03eeb3b016bedceda1232de5fcacfeef92c21d328ef116b416895c9d6')
  # Only the reviewed empty gate API representation changed since the prior pin.
  old='object.data.size() <= 1 && object.data.all(k, k == "approval.json" && object.data[k].size() <= 4096)'
  new='(!has(object.data) || ('+old+'))'
  changed=0
  for o in legacy:
   if o['kind']=='ValidatingAdmissionPolicy':
    for v in o['spec']['validations']:
     if new in v['expression']:
      self.assertEqual(v['expression'].count(new),1)
      v['expression']=v['expression'].replace(new,old);changed+=1
  self.assertEqual(changed,1)
  self.assertEqual(sha(legacy),'0d47090d9e93120116d7ae36d1ad0d597de45833c4decee8db6c2441ee35eb03')
  for o in legacy:
   if o['kind']!='ValidatingAdmissionPolicy':continue
   m=o['spec']['matchConstraints']
   self.assertEqual(m.pop('matchPolicy'),'Equivalent')
   self.assertEqual(m.pop('namespaceSelector'),{});self.assertEqual(m.pop('objectSelector'),{})
   for r in m['resourceRules']:self.assertEqual(r.pop('scope'),'*')
  self.assertEqual(sha(legacy),'4bf1e03b405b43ef30da018dae81ffae5aead2e0027e0d5a964b9053a5978dd7')
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
  with tempfile.TemporaryDirectory() as tmp:
   root=pathlib.Path(tmp);(root/'scripts').mkdir();(root/'profiles/identity').mkdir(parents=True)
   module=root/'scripts/identity_target_profile.py';module.write_text(pathlib.Path(__file__).with_name('identity_target_profile.py').read_text());(root/'profiles/identity/portal-rke2-longhorn.json').write_text(json.dumps(p))
   with self.assertRaisesRegex(ValueError,'legacy profile example changed'):runpy.run_path(str(module))
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
