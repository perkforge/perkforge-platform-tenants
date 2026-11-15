#!/usr/bin/env python3
import contextlib,copy,io,pathlib,runpy,unittest,hashlib
from identity_foundation import build
with contextlib.redirect_stdout(io.StringIO()):F=runpy.run_path(str(pathlib.Path(__file__).with_name('identity_foundation_cases.py')))
class Foundation(unittest.TestCase):
 def objects(self):return build(F['D'],F['network'],F['custody'])
 def test_default_inert(self):self.assertEqual(build({'schemaVersion':1,'context':'portal','enabled':False},{},{}),[])
 def test_scope_and_custody(self):
  o=self.objects();self.assertEqual(sum(x['kind']=='Namespace' for x in o),2)
  secrets=[x for x in o if x['kind']=='Secret'];self.assertEqual(len(secrets),2);self.assertTrue(all(x['data']=={} for x in secrets))
  es=[x for x in o if x['kind']=='ExternalSecret'];self.assertEqual(len(es),3)
  for x in es:
   self.assertEqual(x['spec']['target']['creationPolicy'],'Merge');self.assertEqual(x['spec']['target']['deletionPolicy'],'Retain');self.assertEqual(set(x['spec']['target']['template']['data']),{'lab-ca.crt'})
  self.assertFalse(any(x['kind'] in ('ClusterRole','ClusterRoleBinding','Job','Pod','CronJob') for x in o))
  for x in o:
   if x['kind']=='Role':
    for r in x['rules']:
     self.assertNotIn('*',r['verbs']);self.assertNotIn('*',r['resources'])
     if 'secrets' in r['resources']:self.assertEqual(r['verbs'],['get','update','patch']);self.assertEqual(len(r['resourceNames']),1)
     self.assertNotIn('pods/exec',r['resources']);self.assertNotIn('pods/log',r['resources'])
  self.assertEqual(sum(x['kind']=='ValidatingAdmissionPolicy' for x in o),8)
  self.assertTrue(all(x['spec']['failurePolicy']=='Fail' for x in o if x['kind']=='ValidatingAdmissionPolicy'))
  self.assertTrue(all(x['spec']['validationActions']==['Deny'] for x in o if x['kind']=='ValidatingAdmissionPolicyBinding'))
 def test_native_atomic_match_defaults_explicit(self):
  for o in self.objects():
   if o['kind']!='ValidatingAdmissionPolicy':continue
   m=o['spec']['matchConstraints']
   self.assertEqual(set(m),{'matchPolicy','namespaceSelector','objectSelector','resourceRules'})
   self.assertEqual(m['matchPolicy'],'Equivalent');self.assertEqual(m['namespaceSelector'],{});self.assertEqual(m['objectSelector'],{})
   self.assertTrue(all(r['scope']=='*' for r in m['resourceRules']))
   self.assertTrue(o['spec']['matchConditions']) # Namespace/name fencing remains independent.
 def test_no_broad_network_or_unknown_record(self):
  for n in ({**F['network'],'ingressHosts':['0.0.0.0/0']},{**F['network'],'apiHosts':['192.0.2.0/24']},{**F['network'],'traefikBackend':False},{**F['network'],'apiBackendHosts':['0.0.0.0/0']}):
   with self.assertRaises(ValueError):build(F['D'],n,F['custody'])
  c=copy.deepcopy(F['custody']);c['writer']['record']='*'
  with self.assertRaises(ValueError):build(F['D'],F['network'],c)
 def test_exact_backend_only_attestor(self):
  o=self.objects()
  for ns in ('tenant-identity-writer','tenant-identity-attestor'):
   p=next(x for x in o if x['kind']=='NetworkPolicy' and x['metadata']['namespace']==ns and x['metadata']['name']=='identity-worker-egress')
   backend=[r for r in p['spec']['egress'] if r['ports']==[{'protocol':'TCP','port':6443}]]
   self.assertEqual(len(backend),int(ns=='tenant-identity-attestor'))
   if backend:self.assertEqual(backend[0]['to'],[{'ipBlock':{'cidr':'192.0.2.3/32'}}])
 def test_each_escaped_expression_bounded(self):
  for p in self.objects():
   if p['kind']=='ValidatingAdmissionPolicy':
    self.assertLessEqual(len(p['spec']['validations']),64)
    for v in p['spec']['validations']:self.assertLessEqual(len(v['expression']),90000)
  d=copy.deepcopy(F['D']);b=d['sourceBundle'];items=b['items'];data=b['configMaps'][0]['data'];paths={i['path']:data[i['key']] for i in items};paths[items[0]['path']]='\\'*50000
  manifest=''.join(hashlib.sha256(v.encode()).hexdigest()+'  '+k+'\n' for k,v in sorted(paths.items()) if k!='provenance.sha256');paths['provenance.sha256']=manifest;sha=hashlib.sha256(manifest.encode()).hexdigest();b['sha256']=sha;d['sourceBundleSHA256']=sha;d['sourceBundleName']='identity-source-'+sha[:20]
  for cm in b['configMaps']:
   cm['metadata']['name']=d['sourceBundleName'];cm['data']={i['key']:paths[i['path']] for i in items}
  with self.assertRaisesRegex(ValueError,'admission expression exceeds'):build(d,F['network'],F['custody'])
 def test_duplicate_objects_identical_and_collapsed(self):
  o=self.objects();keys=[(x['apiVersion'],x['kind'],x['metadata'].get('namespace'),x['metadata']['name']) for x in o];self.assertEqual(len(keys),len(set(keys)))
if __name__=='__main__':unittest.main()
