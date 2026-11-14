#!/usr/bin/env python3
import base64,copy,hashlib,pathlib,subprocess,unittest
from finite_identity import render,IMAGE,digest
class Tests(unittest.TestCase):
 def sample(self):
  d={'schemaVersion':1,'context':'portal','enabled':True,'foundationApproved':True,'sourceName':'cluster-config','sourcePath':'./generated/identity/portal','enrollmentRevision':'a'*40,'platformRevision':'b'*40,'invocation':'c'*64,'retryGeneration':0,'image':IMAGE,'sourceItems':[{'key':'file-'+str(i),'path':x} for i,x in enumerate(['perkforge/bin/launch','perkforge/bin/run-phase.py','perkforge/bin/refresh-identity-evidence','revisions.json','provenance.sha256'])],'sourceBundleSHA256':'d'*64,'sourceBundleName':'identity-source-'+('d'*20),'workerNode':'synthetic-worker','receiptClaim':'identity-receipts','writerSecret':'group-writer','attestorSecret':'isolated-attestor','pullSecret':'private-registry','resources':{'requests':{'cpu':'100m','memory':'256Mi'},'limits':{'cpu':'500m','memory':'512Mi'}},'phaseInputs':{'foundation':{}}}
  for phase in ('foundation','attest','memberships'):d['phaseInputs'][phase]={'identity':{'identity_context':'portal','identity_invocation':d['invocation'],'identity_retry_generation':0,'identity_source_revision':d['enrollmentRevision'],'identity_platform_revision':d['platformRevision'],'identity_scope':'gitlab-identity-'+('attest' if phase=='foundation' else phase)+'-v1','identity_run':True}}
  d['phaseInputs']['foundation']['group']={}
  for p in ('foundation','attest','memberships'):d['phaseInputs'][p]['identity']['identity_receipt_uid']='22222222-2222-4222-8222-222222222222'
  items=d['sourceItems'];raw={x['path']:b'fixture' for x in items if x['path']!='provenance.sha256'}
  manifest=''.join(hashlib.sha256(b).hexdigest()+'  '+p+'\n' for p,b in sorted(raw.items())).encode();sha=hashlib.sha256(manifest).hexdigest();raw['provenance.sha256']=manifest
  data={x['key']:base64.b64encode(raw[x['path']]).decode() for x in items};d['sourceBundleSHA256']=sha;d['sourceBundleName']='identity-source-'+sha[:20]
  d['sourceBundle']={'sha256':sha,'items':items,'configMaps':[{'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':d['sourceBundleName'],'namespace':ns},'immutable':True,'binaryData':data} for ns in ('tenant-identity-writer','tenant-identity-attestor')]}
  return d
 def test_current_opt_in_root_is_empty(self):
  root=pathlib.Path(__file__).resolve().parents[1]
  self.assertEqual(subprocess.check_output(['kubectl','kustomize',str(root/'clusters/local-identity-portal')],text=True).strip(),'')
 def test_disabled(self):self.assertEqual(render({'schemaVersion':1,'context':'portal','enabled':False})['kustomization.yaml']['resources'],[])
 def test_identity_and_sequencing(self):
  d=self.sample();a=render(d);self.assertEqual(a,render(copy.deepcopy(d)))
  for phase in ('foundation','attest','memberships'):
   j=a[phase+'/job.yaml'];self.assertNotIn('ttlSecondsAfterFinished',j['spec']);self.assertEqual(j['spec']['backoffLimit'],0)
   k=a[phase+'-reconcile.yaml']['spec'];self.assertFalse(k['force']);self.assertFalse(k['prune']);self.assertEqual(k['healthChecks'][0]['name'],j['metadata']['name'])
   if phase!='foundation':
    expr=k['dependsOn'][0]['readyExpr'];self.assertIn('observedGeneration',expr);self.assertIn("'platform.perkforge.io/attempt'",expr);self.assertIn("'Ready'",expr)
  d['retryGeneration']=1
  for phase in ('foundation','attest','memberships'):d['phaseInputs'][phase]['identity']['identity_retry_generation']=1
  b=render(d);self.assertNotEqual(a['foundation/job.yaml']['metadata']['name'],b['foundation/job.yaml']['metadata']['name'])
 def test_credentials_separated(self):
  a=render(self.sample())
  for phase in ('foundation','attest','memberships'):
   pod=a[phase+'/job.yaml']['spec']['template']['spec'];self.assertFalse(pod['automountServiceAccountToken'])
   secrets=[v['secret']['secretName'] for v in pod['volumes'] if 'secret' in v]
   self.assertEqual(secrets,['isolated-attestor' if phase=='attest' else 'group-writer'])
   self.assertEqual(any(v['name']=='api' for v in pod['volumes']),phase=='attest')
 def test_changed_source_refuses_same_digest(self):
  d=self.sample();d["sourceBundle"]["configMaps"][0]["binaryData"]["file-0"]=base64.b64encode(b"different").decode()
  with self.assertRaises(ValueError):render(d)
 def test_fail_closed(self):
  for key,value in [('foundationApproved',False),('image','bad'),('workerNode',''),('retryGeneration',True),('sourceBundleName','mutable')]:
   d=self.sample();d[key]=value
   with self.assertRaises(ValueError):render(d)
if __name__=='__main__':unittest.main()
