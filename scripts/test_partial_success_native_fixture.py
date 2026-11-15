"""Offline fixture-generation guards; no container/API invocation."""
import pathlib,unittest
from partial_success_native_fixture import transform,replace_once
SOURCE=pathlib.Path(__file__).with_name('test_native_finite_container.py').read_text()
class Fixture(unittest.TestCase):
 def test_partial_compiles_and_uses_real_phase_calls(self):
  s=transform(SOURCE);compile(s,'synthetic-fixture','exec')
  for v in ("identity_previous_attestation_invocation=''","state['denied_lookups']==1","state['patches']==1 and state['data']==saved","OFFLINE.READER"):
   self.assertIn(v,s)
 def test_seam_drift_refused(self):
  for old in ("   if p=='/api/v4/users':return","'uid':uid,'name'",'start=time.monotonic()\ntry:'):
   with self.assertRaises(ValueError):transform(SOURCE.replace(old,'missing-seam'))
  with self.assertRaises(ValueError):replace_once('xx','x','y')
if __name__=='__main__':unittest.main()
