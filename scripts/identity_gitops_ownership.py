#!/usr/bin/env python3
"""Offline adoption plan only. Consumes exact reviewed foundation, never credentials/API."""
import argparse, hashlib, json, pathlib, re
import yaml

def sha(x): return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def literal(x):
 if not isinstance(x,str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,62}',x): raise ValueError('literal name required')
 return x
def cel(x): return json.dumps(x,separators=(',',':'))
def resource(kind,name,ns=None,**kw):
 m={'name':name}
 if ns:m['namespace']=ns
 return {'apiVersion':'rbac.authorization.k8s.io/v1','kind':kind,'metadata':m,**kw}
def rule(group,kind,names,verbs=('get','patch')):
 return {'apiGroups':[group],'resources':[kind],'resourceNames':sorted(names),'verbs':list(verbs)}
def guard(kind,objects,prefix):
 """Root-owned guard: platform reconciler never receives mutation rights to it."""
 clauses=[];targets=[]
 for o in objects:
  m=o['metadata'];base='object.metadata.namespace == '+cel(m['namespace'])+' && object.metadata.name == '+cel(m['name']);targets.append('('+base+')');checks=[base,'!has(object.metadata.ownerReferences)','!has(object.metadata.finalizers)']
  if kind=='Role':
   checks.append('object.rules.size() == '+str(len(o['rules'])))
   for i,r in enumerate(o['rules']):
    p='object.rules['+str(i)+']'
    for k in ('apiGroups','resources','verbs','resourceNames','nonResourceURLs'):
     checks.append(p+'.'+k+' == '+cel(r[k]) if k in r else '!has('+p+'.'+k+')')
  else:
   for k in ('apiGroup','kind','name'):checks.append('object.roleRef.'+k+' == '+cel(o['roleRef'][k]))
   checks.append('object.subjects.size() == '+str(len(o['subjects'])))
   for i,s in enumerate(o['subjects']):
    p='object.subjects['+str(i)+']'
    for k in ('kind','name','namespace'):checks.append(p+'.'+k+' == '+cel(s[k]))
    checks.append('(!has('+p+'.apiGroup) || '+p+'.apiGroup == "")')
  clauses.append('('+' && '.join(checks)+')')
 name=prefix+'-owned-'+kind.lower()
 p={'apiVersion':'admissionregistration.k8s.io/v1','kind':'ValidatingAdmissionPolicy','metadata':{'name':name},'spec':{'failurePolicy':'Fail','matchConstraints':{'resourceRules':[{'apiGroups':['rbac.authorization.k8s.io'],'apiVersions':['v1'],'operations':['CREATE','UPDATE'],'resources':[kind.lower()+'s']}]},'matchConditions':[{'name':'exact-owned-names','expression':' || '.join(targets)}],'validations':[{'expression':' || '.join(clauses),'message':'Owned identity RBAC template drift requires root-reviewed guard update.','reason':'Forbidden'}]}}
 if any(len(x)>90000 for x in [p['spec']['matchConditions'][0]['expression'],p['spec']['validations'][0]['expression']]):raise ValueError('policy too large')
 b={'apiVersion':p['apiVersion'],'kind':'ValidatingAdmissionPolicyBinding','metadata':{'name':name},'spec':{'policyName':name,'validationActions':['Deny']}}
 return [p,b]

def build(objects,c):
 keys={'scope','foundationSHA256','runtimeNamespaces','controlNamespace','platformServiceAccount','sourceName','sourceNamespace','sourcePath','namePrefix'}
 if set(c)!=keys or c['scope']!='identity-foundation-gitops-v1' or c['foundationSHA256']!=sha(objects):raise ValueError('exact reviewed foundation selection required')
 for k in ('controlNamespace','platformServiceAccount','sourceName','sourceNamespace','namePrefix'):literal(c[k])
 if len(c['namePrefix'])>40:raise ValueError('bounded derived names')
 ns=c['runtimeNamespaces']
 if not isinstance(ns,list) or len(ns)!=2 or len(set(ns))!=2 or c['controlNamespace'] in ns:raise ValueError('two isolated namespaces required')
 for n in ns:literal(n)
 if not re.fullmatch(r'\./[a-zA-Z0-9/_-]+',c['sourcePath']) or '..' in c['sourcePath']:raise ValueError('source path')
 allowed={'Namespace','ServiceAccount','Role','RoleBinding','ValidatingAdmissionPolicy','ValidatingAdmissionPolicyBinding','NetworkPolicy','ConfigMap','PersistentVolumeClaim','Secret','SecretStore','ExternalSecret'}
 seen=set();roles=[];bindings=[];admission=[];controls=[];excluded=[]
 for o in objects:
  k=o['kind'];m=o['metadata'];name=literal(m['name']);n=m.get('namespace');key=(k,n,name)
  if k not in allowed or key in seen:raise ValueError('unknown or duplicate object')
  seen.add(key)
  expected_api={'Namespace':'v1','ServiceAccount':'v1','ConfigMap':'v1','PersistentVolumeClaim':'v1','Secret':'v1','Role':'rbac.authorization.k8s.io/v1','RoleBinding':'rbac.authorization.k8s.io/v1','ValidatingAdmissionPolicy':'admissionregistration.k8s.io/v1','ValidatingAdmissionPolicyBinding':'admissionregistration.k8s.io/v1','NetworkPolicy':'networking.k8s.io/v1','SecretStore':'external-secrets.io/v1','ExternalSecret':'external-secrets.io/v1'}
  if o['apiVersion']!=expected_api[k]:raise ValueError('unexpected API version')
  if n is not None and n not in ns+[c['controlNamespace']]:raise ValueError('foreign namespace')
  if k in ('Role','RoleBinding'):
   if n is None:raise ValueError('namespaced RBAC required')
   (roles if k=='Role' else bindings).append(o)
  if k in ('Namespace','PersistentVolumeClaim','Secret') or (k=='ConfigMap' and (name!='identity-openbao-ca' or n not in ns)):
   excluded.append({'kind':k,'namespace':n,'name':name});continue
  if k in ('ValidatingAdmissionPolicy','ValidatingAdmissionPolicyBinding'):
   if name in {c['namePrefix']+'-owned-role',c['namePrefix']+'-owned-rolebinding'}:raise ValueError('guard cannot grant its own modification')
   admission.append(o)
  elif k=='NetworkPolicy':admission.append(o)
  else:controls.append(o)
 if len(roles)!=8 or len(bindings)!=8:raise ValueError('expected reviewed eight-role foundation')
 rolemap={(o['metadata']['namespace'],o['metadata']['name']):o for o in roles}
 for b in bindings:
  ref=b['roleRef'];n=b['metadata']['namespace']
  if ref['apiGroup']!='rbac.authorization.k8s.io' or ref['kind']!='Role' or (n,ref['name']) not in rolemap:raise ValueError('foreign role binding')
  for s in b['subjects']:
   if set(s)-{'kind','name','namespace','apiGroup'} or s['kind']!='ServiceAccount' or s.get('apiGroup','')!='' or s['namespace'] not in ns+[c['controlNamespace'],'external-secrets']:raise ValueError('unreviewed subject')
 for r in roles:
  for q in r['rules']:
   if set(q)-{'apiGroups','resources','resourceNames','verbs'} or any('*' in v for values in q.values() for v in values):raise ValueError('wildcard or nonresource grant')
   if any(v in q['verbs'] for v in ('bind','escalate','impersonate','delete','deletecollection')):raise ValueError('unexpected delegated authority')
 # Only the existing Flux declaration role qualifies for underlying-authority exception.
 exempt=[r for r in roles if r['metadata']['namespace']==c['controlNamespace'] and all(q['apiGroups']==['kustomize.toolkit.fluxcd.io'] and q['resources']==['kustomizations'] and set(q['verbs'])<=set(('create','get','patch','update')) for q in r['rules'])]
 if len(exempt)!=1:raise ValueError('exact declaration authority exception required')
 excluded_names={(r['metadata']['namespace'],r['metadata']['name']) for r in exempt}
 grants=[];by_ns={n:[] for n in ns+[c['controlNamespace']]};cluster={}
 mapping={'ServiceAccount':('','serviceaccounts'),'Role':('rbac.authorization.k8s.io','roles'),'RoleBinding':('rbac.authorization.k8s.io','rolebindings'),'NetworkPolicy':('networking.k8s.io','networkpolicies'),'ConfigMap':('','configmaps'),'SecretStore':('external-secrets.io','secretstores'),'ExternalSecret':('external-secrets.io','externalsecrets')}
 for n in by_ns:
  groups={}
  for o in admission+controls:
   if o['metadata'].get('namespace')==n:
    g,r=mapping[o['kind']];groups.setdefault((g,r),[]).append(o['metadata']['name'])
  for (g,r),names in groups.items():by_ns[n].append(rule(g,r,names))
  escalated=[r['metadata']['name'] for r in roles if r['metadata']['namespace']==n and (n,r['metadata']['name']) not in excluded_names]
  if escalated:by_ns[n].append(rule('rbac.authorization.k8s.io','roles',escalated,('bind','escalate')))
  name=c['namePrefix']+'-owner';grants += [resource('Role',name,n,rules=by_ns[n]),resource('RoleBinding',name,n,roleRef={'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':name},subjects=[{'kind':'ServiceAccount','name':c['platformServiceAccount'],'namespace':c['controlNamespace']}])]
 for k in ('ValidatingAdmissionPolicy','ValidatingAdmissionPolicyBinding'):
  r='validatingadmissionpolicies' if k=='ValidatingAdmissionPolicy' else 'validatingadmissionpolicybindings';cluster[r]=[o['metadata']['name'] for o in admission if o['kind']==k]
 name=c['namePrefix']+'-admission-owner';grants += [resource('ClusterRole',name,rules=[rule('admissionregistration.k8s.io',r,v) for r,v in cluster.items()]),resource('ClusterRoleBinding',name,roleRef={'apiGroup':'rbac.authorization.k8s.io','kind':'ClusterRole','name':name},subjects=[{'kind':'ServiceAccount','name':c['platformServiceAccount'],'namespace':c['controlNamespace']}])]
 policies=guard('Role',roles,c['namePrefix'])+guard('RoleBinding',bindings,c['namePrefix'])
 stages={}
 for stage,objs in [('admission',admission),('controls',controls)]:
  files={str(i).zfill(3)+'-'+o['kind'].lower()+'.yaml':o for i,o in enumerate(objs)}
  files['kustomization.yaml']={'apiVersion':'kustomize.config.k8s.io/v1beta1','kind':'Kustomization','resources':list(files)};stages[stage]=files
 flux=[]
 for stage in ('admission','controls'):
  spec={'interval':'5m','timeout':'5m','path':c['sourcePath']+'/'+stage,'sourceRef':{'kind':'GitRepository','name':c['sourceName'],'namespace':c['sourceNamespace']},'serviceAccountName':c['platformServiceAccount'],'prune':False,'force':False,'wait':True}
  if stage=='admission':spec['healthCheckExprs']=[{'apiVersion':'admissionregistration.k8s.io/v1','kind':'ValidatingAdmissionPolicy','current':'has(status) && has(status.observedGeneration) && status.observedGeneration == metadata.generation && has(status.typeChecking) && (!has(status.typeChecking.expressionWarnings) || status.typeChecking.expressionWarnings.size() == 0)'}]
  else:spec['dependsOn']=[{'name':c['namePrefix']+'-admission'}]
  flux.append({'apiVersion':'kustomize.toolkit.fluxcd.io/v1','kind':'Kustomization','metadata':{'name':c['namePrefix']+'-'+stage,'namespace':c['controlNamespace']},'spec':spec})
 return {'bootstrapGuards':policies,'bootstrapGrants':grants,'stages':stages,'reconciliations':flux,'excludedBootstrapObjects':excluded,'preconditions':['exact native cluster/UID inventory','root installs guards first; observedGeneration and zero warnings','precreate every named object; never recreate lost evidence/PVC','verify existing underlying Flux authority for exempt declaration role','SSA adoption under actual Flux identity, no Secret/issuer data fields','runtime approval and separate private receipt/issuer acceptance before Jobs']}

def main():
 p=argparse.ArgumentParser();p.add_argument('--render',action='store_true');p.add_argument('--foundation');p.add_argument('--selection');p.add_argument('--output');a=p.parse_args()
 if not a.render:print('INERT: offline ownership design only');return
 if not all((a.foundation,a.selection,a.output)):raise ValueError('explicit inputs/output')
 out=build(json.loads(pathlib.Path(a.foundation).read_text()),json.loads(pathlib.Path(a.selection).read_text()));path=pathlib.Path(a.output)
 with path.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
if __name__=='__main__':main()
