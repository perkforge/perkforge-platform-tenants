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
print(json.dumps({'Policies':[x for x in plan['bootstrapGuards'] if x['kind']=='ValidatingAdmissionPolicy'],'Cases':cases}))
