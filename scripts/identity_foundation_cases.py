from test_finite_identity import Tests
from identity_foundation import build
from finite_identity import render
import copy,json,os,yaml
D=Tests().sample()
if os.environ.get('IDENTITY_BUNDLE_FIXTURE'):
 b=json.load(open(os.environ['IDENTITY_BUNDLE_FIXTURE']));D.update(sourceBundle=b,sourceItems=b['items'],sourceBundleSHA256=b['sha256'],sourceBundleName='identity-source-'+b['sha256'][:20])
network={'ingressHosts':['192.0.2.1/32'],'apiHosts':['192.0.2.2/32'],'apiBackendHosts':['192.0.2.3/32'],'apiCA':'-----BEGIN CERTIFICATE-----\nSYNTHETIC-API\n-----END CERTIFICATE-----','traefikBackend':True}
custody={'server':'https://bao.example.test','publicCA':'-----BEGIN CERTIFICATE-----\nSYNTHETIC\n-----END CERTIFICATE-----','writer':{'record':'identity/gitlab/tenants-writer-v1','properties':{'group-writer':'token'}},'reader':{'record':'identity/gitlab/tenant-reader-v1','properties':{'gitlab-reader':'token'}},'keycloak':{'record':'identity/keycloak/portal-membership-reader-v1','properties':{'kc-client-id':'client_id','kc-client-secret':'client_secret'}}}
from test_private_receipts import Private
I=Private().fixture()[0];I.update(claim=D['receiptClaim'],node=D['workerNode'],pullSecret=D['pullSecret'])
if os.environ.get('IDENTITY_TARGET_PROFILE_FIXTURE'):
 D['targetProfile']=json.load(open(os.environ['IDENTITY_TARGET_PROFILE_FIXTURE']));I['storageProfile']=D['targetProfile']['storage']
policies=[o for o in build(D,network,custody,I) if o['kind']=='ValidatingAdmissionPolicy'];g=render(D);cases=[]
for phase in ('foundation','attest','memberships'):
 j=g[phase+'/job.yaml'];policy='identity-jobs-'+j['metadata']['namespace'];cases.append({'Name':phase,'Policy':policy,'Object':j,'Allowed':True})
 for name,mutate in [('image',lambda p:p['containers'][0].update(image='foreign')),('sidecar',lambda p:p['containers'].append(copy.deepcopy(p['containers'][0]))),('token',lambda p:p.update(automountServiceAccountToken=True)),('command',lambda p:p['containers'][0].update(command=['bash','-c','false'])),('hostpath',lambda p:p['volumes'].append({'name':'host','hostPath':{'path':'/'}})),('envfrom',lambda p:p['containers'][0].update(envFrom=[{'secretRef':{'name':'foreign'}}])),('termination-secret',lambda p:p['containers'][0].update(terminationMessagePath='/credentials/group-writer')),('priority',lambda p:p.update(priorityClassName='system-node-critical')),('container-root',lambda p:p['containers'][0]['securityContext'].update(runAsUser=0))]:
  bad=copy.deepcopy(j);mutate(bad['spec']['template']['spec']);cases.append({'Name':phase+'-'+name,'Policy':policy,'Object':bad,'Allowed':False})
for phase in ('foundation','attest','memberships'):
 j=g[phase+'/job.yaml']
 for label,mutate in [('request-budget',lambda p:p['containers'][0]['resources']['requests'].update(cpu='200m')),('limit-budget',lambda p:p['containers'][0]['resources']['limits'].update(memory='1024Mi')),('tmp-limit',lambda p:next(v for v in p['volumes'] if v['name']=='tmp')['emptyDir'].update(sizeLimit='256Mi')),('overhead',lambda p:p.update(overhead={'cpu':'1m'}))]:
  bad=copy.deepcopy(j);mutate(bad['spec']['template']['spec']);cases.append({'Name':phase+'-'+label,'Policy':'identity-jobs-'+j['metadata']['namespace'],'Object':bad,'Allowed':False})
for phase in ('foundation','attest','memberships'):
 j=g[phase+'/job.yaml'];p={'apiVersion':'v1','kind':'Pod','metadata':{'namespace':j['metadata']['namespace'],'name':j['metadata']['name']+'-abcde','generateName':j['metadata']['name']+'-','ownerReferences':[{'apiVersion':'batch/v1','kind':'Job','name':j['metadata']['name'],'uid':'22222222-2222-4222-8222-222222222222','controller':True}],'annotations':j['spec']['template']['metadata']['annotations']},'spec':copy.deepcopy(j['spec']['template']['spec'])}
 p['spec']['schedulerName']='default-scheduler';p['spec']['priority']=0;p['spec']['containers'][0].update(terminationMessagePath='/dev/termination-log',terminationMessagePolicy='File');p['spec']['tolerations']=[{'key':k,'operator':'Exists','effect':'NoExecute','tolerationSeconds':300} for k in ('node.kubernetes.io/not-ready','node.kubernetes.io/unreachable')]
 cases.append({'Name':phase+'-controller-pod','Policy':'identity-pods-'+j['metadata']['namespace'],'Object':p,'Allowed':True})
 bad=copy.deepcopy(p);bad['spec']['containers'].append(copy.deepcopy(bad['spec']['containers'][0]));cases.append({'Name':phase+'-injected-sidecar','Policy':'identity-pods-'+j['metadata']['namespace'],'Object':bad,'Allowed':False})
for phase in ('foundation','attest'):
 c=g[phase+'/source.yaml'];pn='identity-config-'+c['metadata']['namespace'];cases.append({'Name':phase+'-code','Policy':pn,'Object':c,'Allowed':True})
 for label,mutate in [('bytes',lambda x:x['data'].update({next(iter(x['data'])):'tampered'})),('extra-key',lambda x:x['data'].update(extra='foreign')),('missing-key',lambda x:x['data'].pop(next(iter(x['data'])))),('foreign-name',lambda x:x['metadata'].update(name='foreign'))]:
  bad=copy.deepcopy(c);mutate(bad);cases.append({'Name':phase+'-'+label,'Policy':pn,'Object':bad,'Allowed':False})
for phase in ('foundation','attest','memberships'):
 k=g[phase+'-reconcile.yaml'];user='system:serviceaccount:flux-system:identity-declaration-reconciler'
 cases.append({'Name':phase+'-declaration','Policy':'identity-declaration-scope','Object':k,'Username':user,'Allowed':True})
 for label,mutation in [('sa',lambda s:s.update(serviceAccountName='foreign-admin')),('source',lambda s:s['sourceRef'].update(namespace='foreign')),('patch',lambda s:s.update(patches=[{'patch':'foreign'}])),('wait',lambda s:s.update(wait=False))]:
  bad=copy.deepcopy(k);mutation(bad['spec']);cases.append({'Name':phase+'-declaration-'+label,'Policy':'identity-declaration-scope','Object':bad,'Username':user,'Allowed':False})
bad=copy.deepcopy(g['memberships-reconcile.yaml']);bad['spec']['suspend']=False
cases.append({'Name':'membership-release-before-policy-update','Policy':'identity-declaration-scope','Object':bad,'Username':'system:serviceaccount:flux-system:identity-declaration-reconciler','Allowed':False})
old={'apiVersion':'v1','kind':'ConfigMap','metadata':{'uid':'22222222-2222-4222-8222-222222222222','name':'portal-identity-evidence','namespace':'tenant-identity-writer','labels':{'app.kubernetes.io/managed-by':'perkforge-identity','perkforge.dev/context':'portal'},'annotations':{'perkforge.dev/desired-invocation':'old'}},'data':{'receipt.json':'old'}}
issuer='system:serviceaccount:tenant-identity-attestor:identity-attestor';intent='system:serviceaccount:flux-system:identity-declaration-reconciler'
new=copy.deepcopy(old);new['data']['receipt.json']='new'
cases.append({'Name':'issuer-data-only','Policy':'identity-evidence-fields','Object':new,'OldObject':old,'Operation':'UPDATE','Username':issuer,'Allowed':True})
for label,mutation in [('uid',lambda o:o['metadata'].update(uid='33333333-3333-4333-8333-333333333333')),('intent',lambda o:o['metadata']['annotations'].update({'perkforge.dev/desired-invocation':'foreign'})),('owner',lambda o:o['metadata'].update(finalizers=['foreign'])),('extra',lambda o:o['data'].update(extra='foreign'))]:
 bad=copy.deepcopy(new);mutation(bad);cases.append({'Name':'issuer-'+label,'Policy':'identity-evidence-fields','Object':bad,'OldObject':old,'Operation':'UPDATE','Username':issuer,'Allowed':False})
new=copy.deepcopy(old);new['metadata']['annotations']={'perkforge.dev/desired-invocation':D['invocation']}
cases.append({'Name':'intent-preserves-issuer','Policy':'identity-evidence-fields','Object':new,'OldObject':old,'Operation':'UPDATE','Username':intent,'Allowed':True})
bad=copy.deepcopy(new);bad['data']={};cases.append({'Name':'intent-cannot-erase','Policy':'identity-evidence-fields','Object':bad,'OldObject':old,'Operation':'UPDATE','Username':intent,'Allowed':False})
cases.append({'Name':'missing-evidence-no-adoption','Policy':'identity-evidence-fields','Object':new,'Operation':'CREATE','Username':intent,'Allowed':False})
from private_receipts import plan
H=plan(I)
cases.append({'Name':'private-init','Policy':'identity-pods-tenant-identity-writer','Object':H['pod'],'Allowed':True})
defaulted=copy.deepcopy(H['pod']);defaulted['spec']['containers'][0].pop('args')
cases.append({'Name':'private-init-omitted-empty-args','Policy':'identity-pods-tenant-identity-writer','Object':defaulted,'Allowed':True})
for field,value in [('command',['false']),('image','foreign'),('args',['foreign'])]:
 bad=copy.deepcopy(H['pod']);bad['spec']['containers'][0][field]=value;cases.append({'Name':'private-init-'+field,'Policy':'identity-pods-tenant-identity-writer','Object':bad,'Allowed':False})
for key in ('configMap','inputs','gate'):
 cases.append({'Name':'private-init-'+key,'Policy':'identity-config-tenant-identity-writer','Object':H[key],'Username':I['operatorUser'],'Allowed':True})
cases.append({'Name':'private-gate-foreign','Policy':'identity-config-tenant-identity-writer','Object':H['gate'],'Username':'foreign','Allowed':False})
schemas={}
crd_path=os.environ.get('IDENTITY_FLUX_CRD') or (os.path.join(os.environ['NEXTCLOUD_CRD_DIR'],'kustomization.yaml') if os.environ.get('NEXTCLOUD_CRD_DIR') else None)
if crd_path:
 crd=yaml.safe_load(open(crd_path));v=next(v for v in crd['spec']['versions'] if v['name']=='v1');schemas['io.k8s.api.kustomize.toolkit.fluxcd.io.v1.Kustomization']=v['schema']['openAPIV3Schema']
print(json.dumps({'Policies':policies,'Cases':cases,'Schemas':schemas}))
