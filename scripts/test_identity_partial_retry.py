"""Separate issuer predecessor stays explicit and bound to every native phase."""
import copy,contextlib,io,json,pathlib,runpy,unittest
from finite_identity import render,PHASES
from identity_context_fixture import alternate
with contextlib.redirect_stdout(io.StringIO()): F=runpy.run_path(str(pathlib.Path(__file__).with_name('identity_foundation_cases.py')))
KEY='identity_previous_attestation_invocation'
class PartialRetry(unittest.TestCase):
 def fixtures(self):
  yield copy.deepcopy(F['D'])
  yield alternate(F['D'],F['I'],F['custody'],'atlas')[0]
 def bind(self,d,issuer=''):
  for p in PHASES:
   d['phaseInputs'][p]['identity'][KEY]=issuer
   d['phaseInputs'][p]['identity']['identity_previous_invocation']='a'*64
 def test_explicit_empty_and_prior_are_hashed_and_preserved(self):
  for d in self.fixtures():
   legacy=render(d);self.bind(d);empty=render(d)
   self.bind(d,'b'*64);prior=render(d)
   for p in PHASES:
    self.assertNotEqual(legacy[p+'/job.yaml']['metadata']['name'],empty[p+'/job.yaml']['metadata']['name'])
    self.assertNotEqual(empty[p+'/job.yaml']['metadata']['name'],prior[p+'/job.yaml']['metadata']['name'])
    for out,value in ((empty,''),(prior,'b'*64)):
     body=json.loads(out[p+'/inputs.yaml']['data']['inputs.json'])
     self.assertEqual(body['identity'][KEY],value)
     self.assertEqual(body['identity']['identity_previous_invocation'],'a'*64)
    self.assertEqual(empty[p+'/job.yaml']['spec']['template']['spec']['containers'][0]['resources'],legacy[p+'/job.yaml']['spec']['template']['spec']['containers'][0]['resources'])
 def test_malformed_missing_and_cross_phase_fail_closed(self):
  for base in self.fixtures():
   for value in (None,True,0,[],{},'a'*63,'A'*64,'a'*65,'a'*64+'\n'):
    d=copy.deepcopy(base);self.bind(d,value)
    with self.assertRaises(ValueError):render(d)
   d=copy.deepcopy(base);self.bind(d);del d['phaseInputs']['attest']['identity'][KEY]
   with self.assertRaises(ValueError):render(d)
   d=copy.deepcopy(base);self.bind(d);d['phaseInputs']['memberships']['identity'][KEY]='b'*64
   with self.assertRaises(ValueError):render(d)
   d=copy.deepcopy(base);self.bind(d);d['phaseInputs']['foundation']['identity']['identity_previous_invocation']='c'*64
   with self.assertRaises(ValueError):render(d)
   d=copy.deepcopy(base);self.bind(d,'b'*64)
   for p in PHASES:d['phaseInputs'][p]['identity']['identity_previous_invocation']=''
   with self.assertRaises(ValueError):render(d)
 def test_scheduling_never_changes_partial_attempt(self):
  for d in self.fixtures():
   self.bind(d);d['membershipReleased']=False;d['phasesSuspended']=True;held=render(d)
   d['phasesSuspended']=False;active=render(d)
   for p in PHASES:
    self.assertEqual(held[p+'/job.yaml'],active[p+'/job.yaml'])
    self.assertEqual(held[p+'/inputs.yaml'],active[p+'/inputs.yaml'])
if __name__=='__main__':unittest.main()
