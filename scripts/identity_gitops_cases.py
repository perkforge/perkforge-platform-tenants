"""Synthetic exact-RBAC fixtures. No API access or credentials."""
import copy,json
from test_identity_gitops_ownership import sample
from identity_gitops_ownership import build
objects,selection=sample();plan=build(objects,selection);cases=[]
for o in objects:
 if o['kind'] not in ('Role','RoleBinding'):continue
 policy='identity-foundation-owned-'+o['kind'].lower();label=o['metadata']['namespace']+'-'+o['metadata']['name']
 cases.append({'Name':label,'Policy':policy,'Object':o,'Allowed':True})
 if o['kind']=='Role':
  mutations=[('verb',lambda x:x['rules'][0]['verbs'].append('delete')),('resource',lambda x:x['rules'][0]['resources'].append('secrets')),('wildcard',lambda x:x['rules'][0].update(resourceNames=['*'])),('rule',lambda x:x['rules'].append({'apiGroups':[''],'resources':['secrets'],'verbs':['get']})),('url',lambda x:x['rules'][0].update(nonResourceURLs=['/']))]
 else:
  mutations=[('subject',lambda x:x['subjects'][0].update(name='foreign')),('namespace',lambda x:x['subjects'][0].update(namespace='foreign')),('kind',lambda x:x['subjects'][0].update(kind='User',apiGroup='rbac.authorization.k8s.io')),('role',lambda x:x['roleRef'].update(name='cluster-admin')),('extra-subject',lambda x:x['subjects'].append(copy.deepcopy(x['subjects'][0])))]
 mutations += [('gc-owner',lambda x:x['metadata'].update(ownerReferences=[{'apiVersion':'v1','kind':'ConfigMap','name':'foreign','uid':'11111111-1111-4111-8111-111111111111'}])),('finalizer',lambda x:x['metadata'].update(finalizers=['foreign']))]
 for name,mutate in mutations:
  bad=copy.deepcopy(o);mutate(bad);cases.append({'Name':label+'-'+name,'Policy':policy,'Object':bad,'Allowed':False})
# Evaluate a future retry against the ORIGINAL root guard, not regenerated guards.
from test_identity_foundation import F
from identity_foundation import build as foundation
D=copy.deepcopy(F['D']);D['retryGeneration']+=1
for body in D['phaseInputs'].values():body['identity']['identity_retry_generation']=D['retryGeneration']
future=foundation(D,F['network'],F['custody'])
for o in future:
 if o['kind']!='Role' or not any(r.get('resources')==['jobs'] for r in o['rules']):continue
 label=o['metadata']['namespace'];policy='identity-foundation-owned-role'
 cases.append({'Name':label+'-future-retry','Policy':policy,'Object':o,'Allowed':True})
 new=copy.deepcopy(o);new['rules'][5]['resourceNames'][-1]='identity-source-'+'f'*20
 cases.append({'Name':label+'-future-source','Policy':policy,'Object':new,'Allowed':True})
 for mutation in ('extra-job','extra-cm','wildcard','foreign-context','wrong-phase','short-hash','uppercase-hash','bad-input','foreign-source','long-source','secret-rule','mixed-attempt'):
  bad=copy.deepcopy(new);js=bad['rules'][1]['resourceNames'];cms=bad['rules'][5]['resourceNames']
  if mutation=='extra-job':js.append(js[0])
  elif mutation=='extra-cm':cms.append(cms[0])
  elif mutation=='wildcard':js[0]='*'
  elif mutation=='foreign-context':js[0]='foreign-'+js[0];cms[0]=js[0]+'-inputs'
  elif mutation=='wrong-phase':js[0]=js[0].replace('foundation','attest').replace('attest','memberships');cms[0]=js[0]+'-inputs'
  elif mutation=='short-hash':js[0]=js[0][:-1];cms[0]=js[0]+'-inputs'
  elif mutation=='uppercase-hash':js[0]=js[0][:-16]+'A'*16;cms[0]=js[0]+'-inputs'
  elif mutation=='bad-input':cms[0]+='x'
  elif mutation=='foreign-source':cms[-1]='foreign-'+cms[-1]
  elif mutation=='long-source':cms[-1]+='a'
  elif mutation=='secret-rule':bad['rules'][5]['resources']=['secrets']
  elif len(js)>1:js[1]=js[1][:-16]+'b'*16;cms[1]=js[1]+'-inputs'
  else:continue
  cases.append({'Name':label+'-'+mutation,'Policy':policy,'Object':bad,'Allowed':False})
dep=plan['reconciliations'][1]['spec']['dependsOn'][0]['readyExpr']
base={'spec':{'commonMetadata':{'annotations':{'platform.perkforge.io/foundation-sha256':selection['foundationSHA256']}}},'metadata':{'generation':2},'status':{'observedGeneration':2,'conditions':[{'type':'Ready','status':'True'}]}}
dependencies=[]
for name in ('current','stale-hash','stale-generation','not-ready','missing-status'):
 x=copy.deepcopy(base)
 if name=='stale-hash':x['spec']['commonMetadata']['annotations']['platform.perkforge.io/foundation-sha256']='a'*64
 if name=='stale-generation':x['status']['observedGeneration']=1
 if name=='not-ready':x['status']['conditions'][0]['status']='False'
 if name=='missing-status':del x['status']
 dependencies.append({'Name':name,'Dep':x,'Self':base,'Allowed':name=='current'})
print(json.dumps({'Policies':[x for x in plan['bootstrapGuards'] if x['kind']=='ValidatingAdmissionPolicy'],'Cases':cases,'DependencyExpression':dep,'Dependencies':dependencies}))
