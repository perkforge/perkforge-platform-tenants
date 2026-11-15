#!/usr/bin/env python3
"""Offline checks of this explicit Portal activation; no Kubernetes/API calls."""
import copy,json,pathlib,unittest
from finite_identity import render,IMAGE
from identity_foundation import build
from identity_gitops_ownership import sha
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Activation(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((ROOT/'declarations/identity/portal.json').read_text());self.c=json.loads((ROOT/'declarations/identity/foundation.json').read_text())
 def test_release_pins_and_explicit_scope(self):
  self.assertEqual(self.d['enrollmentRevision'],'5621e9b05bd94566c1bfdc6bcf8b75b0404e8ff0');self.assertEqual(self.d['platformRevision'],'b904017158100944a81129899e8fc64a3ed976b8')
  self.assertEqual(self.d['context'],'portal');self.assertEqual(self.d['image'],IMAGE);self.assertEqual(self.d['sourceName'],'tenant-enrollments')
  self.assertEqual(self.d['resources'],{'requests':{'cpu':'100m','memory':'256Mi'},'limits':{'cpu':'500m','memory':'512Mi'}})
  self.assertEqual(self.d['phaseInputs']['foundation']['group']['gitlab_group_expected_parent_id'],7)
  self.assertFalse(self.d['phaseInputs']['foundation']['group']['gitlab_group_allow_parent_create'])
 def test_explicit_reviewed_foundation_hash(self):
  c=self.c;self.assertEqual(c['ownership']['foundationSHA256'],sha(build(self.d,c['network'],c['custody'],c['initializer'])))
 def test_A_B_differ_only_membership_scheduling_and_its_admission(self):
  a=copy.deepcopy(self.d);a['membershipReleased']=False
  if 'phasesSuspended' in a:a['phasesSuspended']=False
  b=copy.deepcopy(a);b['membershipReleased']=True
  fa,fb=render(a),render(b)
  self.assertEqual(set(fa),set(fb));self.assertEqual([k for k in fa if fa[k]!=fb[k]],['memberships-reconcile.yaml'])
  self.assertTrue(fa['memberships-reconcile.yaml']['spec']['suspend']);self.assertFalse(fb['memberships-reconcile.yaml']['spec']['suspend'])
  c=self.c;oa=build(a,c['network'],c['custody'],c['initializer']);ob=build(b,c['network'],c['custody'],c['initializer'])
  changed=[(x['kind'],x['metadata']['name']) for x,y in zip(oa,ob) if x!=y]
  self.assertEqual(changed,[('ValidatingAdmissionPolicy','identity-declaration-scope')])
 def test_selected_child_hold_is_exact(self):
  if self.d.get('phasesSuspended') is True:
   self.assertFalse(self.d['membershipReleased']);f=render(self.d)
   for phase in ('foundation','attest','memberships'):self.assertIs(f[phase+'-reconcile.yaml']['spec']['suspend'],True)
   with self.assertRaises(ValueError):render(dict(self.d,membershipReleased=True))
 def test_receipt_and_readers_remain_separate(self):
  f=render(self.d)
  for phase in ('foundation','attest','memberships'):
   pod=f[phase+'/job.yaml']['spec']['template']['spec'];self.assertFalse(pod['automountServiceAccountToken'])
   self.assertEqual([v['secret']['secretName'] for v in pod['volumes'] if 'secret' in v],['isolated-attestor' if phase=='attest' else 'group-writer'])
   self.assertNotIn('ttlSecondsAfterFinished',f[phase+'/job.yaml']['spec'])
  self.assertNotIn('data',f['receipt-intent.yaml'])
if __name__=='__main__':unittest.main()
