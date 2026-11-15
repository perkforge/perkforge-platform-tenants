"""Native CEL cases for absent/held/resumed scheduling in two contexts."""
import contextlib,copy,io,json,pathlib,runpy
from finite_identity import render,PHASES
from identity_foundation import build
from identity_context_binding import selection
from identity_context_fixture import alternate
with contextlib.redirect_stdout(io.StringIO()):F=runpy.run_path(str(pathlib.Path(__file__).with_name('identity_foundation_cases.py')))
policies=[];cases=[]
for context in ('portal','atlas'):
 d,i,c=copy.deepcopy(F['D']),copy.deepcopy(F['I']),copy.deepcopy(F['custody'])
 if context!='portal':d,i,c=alternate(d,i,c,context)
 d['membershipReleased']=False;d.pop('phasesSuspended',None);b=selection(d)
 for mode in ('absent','held','resume'):
  selected=copy.deepcopy(d)
  if mode!='absent':selected['phasesSuspended']=mode=='held'
  policy=next(p for p in build(selected,F['network'],c,i) if p['kind']=='ValidatingAdmissionPolicy' and p['metadata']['name']==b['declaration_policy'])
  policy['metadata']['name']=context+'-'+mode;policies.append(policy);out=render(selected)
  for phase in PHASES:
   obj=out[phase+'-reconcile.yaml'];base={'Name':context+'-'+mode+'-'+phase,'Policy':policy['metadata']['name'],'Username':'system:serviceaccount:flux-system:'+b['declaration_reconciler'],'Operation':'UPDATE'}
   cases.append(dict(base,Object=obj,Allowed=True))
   bad=copy.deepcopy(obj);bad['spec']['suspend']=not obj['spec'].get('suspend',False)
   cases.append(dict(base,Name=base['Name']+'-opposite',Object=bad,Allowed=False))
   if 'suspend' in obj['spec']:
    bad=copy.deepcopy(obj);bad['spec'].pop('suspend');cases.append(dict(base,Name=base['Name']+'-omission',Object=bad,Allowed=False))
print(json.dumps({'Policies':policies,'Schemas':F['schemas'],'Cases':cases}))
