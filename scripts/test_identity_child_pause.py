"""Declarative scheduling gates never mint a new provider attempt."""
import contextlib,copy,io,pathlib,runpy,unittest
from finite_identity import render,PHASES
from identity_context_fixture import alternate
from identity_foundation import build
from identity_context_binding import selection
with contextlib.redirect_stdout(io.StringIO()):F=runpy.run_path(str(pathlib.Path(__file__).with_name('identity_foundation_cases.py')))
class ChildPause(unittest.TestCase):
 def fixtures(self):
  yield copy.deepcopy(F['D']),copy.deepcopy(F['I']),copy.deepcopy(F['custody'])
  yield alternate(F['D'],F['I'],F['custody'],'atlas')
 def test_preserves_every_non_scheduling_byte(self):
  for d,i,c in self.fixtures():
   d.pop('phasesSuspended',None);d['membershipReleased']=False;old=render(d)
   for flag in (True,False):
    new=render(dict(d,phasesSuspended=flag))
    for key in old:
     expected=copy.deepcopy(old[key])
     if key in [p+'-reconcile.yaml' for p in PHASES]:expected['spec']['suspend']=flag or key=='memberships-reconcile.yaml'
     self.assertEqual(new[key],expected,(d['context'],flag,key))
 def test_release_is_independent_but_cannot_cross_hold(self):
  for d,i,c in self.fixtures():
   for flag in (False,True):
    d['phasesSuspended']=flag;d['membershipReleased']=True
    if flag:
     with self.assertRaises(ValueError):render(d)
    else:
     out=render(d)
     for p in PHASES:self.assertIs(out[p+'-reconcile.yaml']['spec']['suspend'],False)
 def test_strict_boolean_and_inert_disabled(self):
  for d,i,c in self.fixtures():
   for value in (None,0,1,'true',[],{}):
    with self.assertRaises(ValueError):render(dict(d,phasesSuspended=value))
  with self.assertRaises(ValueError):render({'schemaVersion':1,'context':'portal','enabled':False,'phasesSuspended':True})
 def test_only_declaration_admission_changes(self):
  for d,i,c in self.fixtures():
   d['membershipReleased']=False;d.pop('phasesSuspended',None)
   old=build(d,F['network'],c,i);new=build(dict(d,phasesSuspended=True),F['network'],c,i)
   changed=[a['metadata']['name'] for a,b in zip(old,new) if a!=b]
   self.assertEqual(changed,[selection(d)['declaration_policy']])
if __name__=='__main__':unittest.main()
