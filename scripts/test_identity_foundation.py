#!/usr/bin/env python3
import contextlib,copy,io,pathlib,runpy,unittest
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
 def test_no_broad_network_or_unknown_record(self):
  for n in ({**F['network'],'ingressHosts':['0.0.0.0/0']},{**F['network'],'apiHosts':['192.0.2.0/24']},{**F['network'],'traefikBackend':False}):
   with self.assertRaises(ValueError):build(F['D'],n,F['custody'])
  c=copy.deepcopy(F['custody']);c['writer']['record']='*'
  with self.assertRaises(ValueError):build(F['D'],F['network'],c)
 def test_duplicate_objects_identical_and_collapsed(self):
  o=self.objects();keys=[(x['apiVersion'],x['kind'],x['metadata'].get('namespace'),x['metadata']['name']) for x in o];self.assertEqual(len(keys),len(set(keys)))
if __name__=='__main__':unittest.main()
