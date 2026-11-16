#!/usr/bin/env python3
"""Offline checks of this explicit Portal activation; no Kubernetes/API calls."""
import copy,json,pathlib,unittest
from finite_identity import render,IMAGE
from identity_foundation import build
from identity_gitops_ownership import sha
from render_identity_foundation import render as render_foundation
ROOT=pathlib.Path(__file__).resolve().parents[1]
class Activation(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((ROOT/'declarations/identity/portal.json').read_text());self.c=json.loads((ROOT/'declarations/identity/foundation.json').read_text())
 def test_release_pins_and_explicit_scope(self):
  self.assertEqual(self.d['enrollmentRevision'],'3f3d630e70a5f6db7282779cae059202229cb517');self.assertEqual(self.d['platformRevision'],'95ef0f103a89fe71b7e5aff93d0f3dd2ce31947c')
  self.assertEqual(self.d['context'],'portal');self.assertEqual(self.d['image'],IMAGE);self.assertEqual(self.d['sourceName'],'tenant-enrollments')
  self.assertEqual(self.d['resources'],{'requests':{'cpu':'100m','memory':'256Mi'},'limits':{'cpu':'500m','memory':'512Mi'}})
  self.assertEqual(self.d['phaseInputs']['foundation']['group']['gitlab_group_expected_parent_id'],7)
  self.assertFalse(self.d['phaseInputs']['foundation']['group']['gitlab_group_allow_parent_create'])
 def test_partial_success_predecessors(self):
  self.assertEqual(self.d['retryGeneration'],1)
  for phase in ('foundation','attest','memberships'):
   i=self.d['phaseInputs'][phase]['identity'];self.assertEqual(i['identity_previous_invocation'],'89fa3d6348444b25ede774bebe27287c083b5932d4ea192b4dc5826a7e6191c5');self.assertEqual(i['identity_previous_attestation_invocation'],'')
  self.assertEqual(self.d['phaseInputs']['foundation']['group']['gitlab_group_previous_revision'],'4b027b7a50ebf477a36746b88d0f034cc6a7d454')
 def test_explicit_reviewed_foundation_hash(self):
  c=self.c;_,bootstrap=render_foundation(self.d,c) # validates strict persisted opt-in and exact full object hash
  self.assertEqual(c['ownership']['foundationSHA256'],bootstrap['foundationSHA256'])
  stale=copy.deepcopy(c);stale['ownership']['foundationSHA256']='0'*64
  with self.assertRaises(ValueError):render_foundation(self.d,stale)
 def test_A_B_differ_only_membership_scheduling_and_its_admission(self):
  a=copy.deepcopy(self.d);a['membershipReleased']=False
  if 'phasesSuspended' in a:a['phasesSuspended']=False
  b=copy.deepcopy(a);b['membershipReleased']=True
  fa,fb=render(a),render(b)
  self.assertEqual(set(fa),set(fb));self.assertEqual([k for k in fa if fa[k]!=fb[k]],['memberships-reconcile.yaml'])
  self.assertTrue(fa['memberships-reconcile.yaml']['spec']['suspend']);self.assertFalse(fb['memberships-reconcile.yaml']['spec']['suspend'])
  c=self.c;render_foundation(self.d,c) # validate selected opt-in before forwarding it
  export=c.get('receiptExport',{}).get('enabled',False)
  oa=build(a,c['network'],c['custody'],c['initializer'],receipt_export=export);ob=build(b,c['network'],c['custody'],c['initializer'],receipt_export=export)
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
