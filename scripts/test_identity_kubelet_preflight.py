import copy,unittest
from test_finite_identity import Tests
from test_private_receipts import Private
from finite_identity import RUNTIME_PROFILE,SUPERVISOR,render
from identity_kubelet_preflight import build
class Preflight(unittest.TestCase):
 def fixture(self):
  d=Tests().sample();d['runtimeProfile']=RUNTIME_PROFILE;i=Private().fixture()[0];i.update(node=d['workerNode'],pullSecret=d['pullSecret']);return d,i
 def test_exact_restricted_lifecycle(self):
  d,i=self.fixture();h=build(d,i);p=h['spec'];phase=render(d)['foundation/job.yaml']['spec']['template']['spec']
  self.assertEqual(p['initContainers'],phase['initContainers']);self.assertEqual(p['securityContext'],phase['securityContext'])
  self.assertEqual(p['volumes'],[{'name':'tmp','emptyDir':{'sizeLimit':'128Mi'}}]);self.assertEqual(p['containers'][0]['volumeMounts'],[{'name':'tmp','mountPath':'/tmp','subPath':'private'}])
  self.assertFalse(p['automountServiceAccountToken']);self.assertEqual(p['containers'][0]['command'][:4],SUPERVISOR[:4]);self.assertEqual(p['containers'][0]['resources'],d['resources']);self.assertEqual(p['activeDeadlineSeconds'],300)
  self.assertNotIn('platform.perkforge.io/identity-phase',h['metadata']['labels']);self.assertNotIn('ownerReferences',h['metadata']);self.assertEqual(h,build(copy.deepcopy(d),copy.deepcopy(i)))
 def test_target_refusals(self):
  for key,value in [('node','foreign'),('pullSecret','foreign')]:
   d,i=self.fixture();i[key]=value
   with self.assertRaises(ValueError):build(d,i)
  d,i=self.fixture();d.pop('runtimeProfile')
  with self.assertRaises(ValueError):build(d,i)
if __name__=='__main__':unittest.main()
