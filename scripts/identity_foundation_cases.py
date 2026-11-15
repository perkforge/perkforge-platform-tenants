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
if os.environ.get('IDENTITY_CONTEXT_FIXTURE'):
 from identity_context_fixture import alternate
 D,I,custody=alternate(D,I,custody,os.environ['IDENTITY_CONTEXT_FIXTURE'])
# Test-only explicit selected-source override; never reads credentials or the API.
if os.environ.get('IDENTITY_SELECTION_FIXTURE_DIR'):
 from pathlib import Path
 root=Path(os.environ['IDENTITY_SELECTION_FIXTURE_DIR'])
 D=json.loads((root/'declarations/identity/portal.json').read_text())
 selected=json.loads((root/'declarations/identity/foundation.json').read_text())
 if D.get('enabled') is not True or selected.get('enabled') is not True:raise ValueError('enabled selected fixture required')
 network,custody,I=selected['network'],selected['custody'],selected['initializer']
if os.environ.get('IDENTITY_RUNTIME_PROFILE_FIXTURE'):
 D['runtimeProfile']=os.environ['IDENTITY_RUNTIME_PROFILE_FIXTURE']
from identity_context_binding import selection
B=selection(D)
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
 j=g[phase+'/job.yaml'];p={'apiVersion':'v1','kind':'Pod','metadata':{'namespace':j['metadata']['namespace'],'name':j['metadata']['name']+'-abcde','generateName':j['metadata']['name']+'-','ownerReferences':[{'apiVersion':'batch/v1','kind':'Job','name':j['metadata']['name'],'uid':D['phaseInputs']['attest']['identity']['identity_receipt_uid'],'controller':True}],'annotations':j['spec']['template']['metadata']['annotations']},'spec':copy.deepcopy(j['spec']['template']['spec'])}
 p['spec']['schedulerName']='default-scheduler';p['spec']['priority']=0;p['spec']['containers'][0].update(terminationMessagePath='/dev/termination-log',terminationMessagePolicy='File');p['spec']['tolerations']=[{'key':k,'operator':'Exists','effect':'NoExecute','tolerationSeconds':300} for k in ('node.kubernetes.io/not-ready','node.kubernetes.io/unreachable')]
 cases.append({'Name':phase+'-controller-pod','Policy':'identity-pods-'+j['metadata']['namespace'],'Object':p,'Allowed':True})
 bad=copy.deepcopy(p);bad['spec']['containers'].append(copy.deepcopy(bad['spec']['containers'][0]));cases.append({'Name':phase+'-injected-sidecar','Policy':'identity-pods-'+j['metadata']['namespace'],'Object':bad,'Allowed':False})
for phase in ('foundation','attest'):
 c=g[phase+'/source.yaml'];pn='identity-config-'+c['metadata']['namespace'];cases.append({'Name':phase+'-code','Policy':pn,'Object':c,'Allowed':True})
 for label,mutate in [('bytes',lambda x:x['data'].update({next(iter(x['data'])):'tampered'})),('extra-key',lambda x:x['data'].update(extra='foreign')),('missing-key',lambda x:x['data'].pop(next(iter(x['data'])))),('foreign-name',lambda x:x['metadata'].update(name='foreign'))]:
  bad=copy.deepcopy(c);mutate(bad);cases.append({'Name':phase+'-'+label,'Policy':pn,'Object':bad,'Allowed':False})
for phase in ('foundation','attest','memberships'):
 k=g[phase+'-reconcile.yaml'];user='system:serviceaccount:flux-system:'+B['declaration_reconciler']
 cases.append({'Name':phase+'-declaration','Policy':B['declaration_policy'],'Object':k,'Username':user,'Allowed':True})
 for label,mutation in [('sa',lambda s:s.update(serviceAccountName='foreign-admin')),('source',lambda s:s['sourceRef'].update(namespace='foreign')),('patch',lambda s:s.update(patches=[{'patch':'foreign'}])),('wait',lambda s:s.update(wait=False))]:
  bad=copy.deepcopy(k);mutation(bad['spec']);cases.append({'Name':phase+'-declaration-'+label,'Policy':B['declaration_policy'],'Object':bad,'Username':user,'Allowed':False})
bad=copy.deepcopy(g['memberships-reconcile.yaml']);bad['spec']['suspend']=not bad['spec']['suspend']
cases.append({'Name':'membership-gate-before-policy-update','Policy':B['declaration_policy'],'Object':bad,'Username':'system:serviceaccount:flux-system:'+B['declaration_reconciler'],'Allowed':False})
old={'apiVersion':'v1','kind':'ConfigMap','metadata':{'uid':D['phaseInputs']['attest']['identity']['identity_receipt_uid'],'name':B['evidence_name'],'namespace':B['writer_namespace'],'labels':{'app.kubernetes.io/managed-by':'perkforge-identity','perkforge.dev/context':D['context'],'platform.perkforge.io/owner':'tenant-identity-foundation-v1'},'annotations':{'perkforge.dev/desired-invocation':'old'}},'data':{'receipt.json':'old'}}
issuer='system:serviceaccount:'+B['attestor_namespace']+':identity-attestor';intent='system:serviceaccount:flux-system:'+B['declaration_reconciler']
new=copy.deepcopy(old);new['data']['receipt.json']='new'
cases.append({'Name':'issuer-data-only','Policy':B['evidence_policy'],'Object':new,'OldObject':old,'Operation':'UPDATE','Username':issuer,'Allowed':True})
for label,mutation in [('uid',lambda o:o['metadata'].update(uid='33333333-3333-4333-8333-333333333333')),('intent',lambda o:o['metadata']['annotations'].update({'perkforge.dev/desired-invocation':'foreign'})),('owner',lambda o:o['metadata'].update(finalizers=['foreign'])),('extra',lambda o:o['data'].update(extra='foreign'))]:
 bad=copy.deepcopy(new);mutation(bad);cases.append({'Name':'issuer-'+label,'Policy':B['evidence_policy'],'Object':bad,'OldObject':old,'Operation':'UPDATE','Username':issuer,'Allowed':False})
new=copy.deepcopy(old);new['metadata']['annotations']={'perkforge.dev/desired-invocation':D['invocation']}
new['metadata']['labels'].update({'kustomize.toolkit.fluxcd.io/name':B['phase_prefix'],'kustomize.toolkit.fluxcd.io/namespace':'flux-system'})
cases.append({'Name':'intent-preserves-issuer','Policy':B['evidence_policy'],'Object':new,'OldObject':old,'Operation':'UPDATE','Username':intent,'Allowed':True})
tracked=copy.deepcopy(old);tracked['metadata']['labels']=copy.deepcopy(new['metadata']['labels'])
cases.append({'Name':'intent-same-flux-owner','Policy':B['evidence_policy'],'Object':new,'OldObject':tracked,'Operation':'UPDATE','Username':intent,'Allowed':True})
for label,target,key,value in [('foreign-old','old','kustomize.toolkit.fluxcd.io/name','foreign'),('foreign-new','new','kustomize.toolkit.fluxcd.io/name','foreign'),('foreign-ns','new','kustomize.toolkit.fluxcd.io/namespace','foreign'),('bootstrap-owner','new','platform.perkforge.io/owner','foreign'),('bootstrap-context','new','perkforge.dev/context','foreign'),('extra','new','extra','foreign'),('old-extra','old','extra','foreign')]:
 prior=copy.deepcopy(old);bad=copy.deepcopy(new);(prior if target=='old' else bad)['metadata']['labels'][key]=value
 cases.append({'Name':'intent-label-'+label,'Policy':B['evidence_policy'],'Object':bad,'OldObject':prior,'Operation':'UPDATE','Username':intent,'Allowed':False})
for label in ('kustomize.toolkit.fluxcd.io/name','kustomize.toolkit.fluxcd.io/namespace','platform.perkforge.io/owner'):
 bad=copy.deepcopy(new);bad['metadata']['labels'].pop(label)
 cases.append({'Name':'intent-label-missing-'+label,'Policy':B['evidence_policy'],'Object':bad,'OldObject':tracked,'Operation':'UPDATE','Username':intent,'Allowed':False})
for who in (issuer,'foreign'):
 cases.append({'Name':'adoption-wrong-caller-'+who,'Policy':B['evidence_policy'],'Object':new,'OldObject':old,'Operation':'UPDATE','Username':who,'Allowed':False})
for field in ('ownerReferences','finalizers'):
 bad=copy.deepcopy(new);bad['metadata'][field]=[{'apiVersion':'v1','kind':'ConfigMap','name':'foreign','uid':'11111111-1111-4111-8111-111111111111'}] if field=='ownerReferences' else ['foreign']
 cases.append({'Name':'intent-forbidden-'+field,'Policy':B['evidence_policy'],'Object':bad,'OldObject':old,'Operation':'UPDATE','Username':intent,'Allowed':False})
bad=copy.deepcopy(new);bad['data']={};cases.append({'Name':'intent-cannot-erase','Policy':B['evidence_policy'],'Object':bad,'OldObject':old,'Operation':'UPDATE','Username':intent,'Allowed':False})
cases.append({'Name':'missing-evidence-no-adoption','Policy':B['evidence_policy'],'Object':new,'Operation':'CREATE','Username':intent,'Allowed':False})
if D.get('runtimeProfile'):
 for phase in ('foundation','attest','memberships'):
  job=g[phase+'/job.yaml'];pol='identity-jobs-'+job['metadata']['namespace']
  for label,mutation in [
   ('missing',lambda p:p.pop('initContainers')),
   ('extra',lambda p:p['initContainers'].append(copy.deepcopy(p['initContainers'][0]))),
   ('command',lambda p:p['initContainers'][0].update(command=['false'])),
   ('secret-mount',lambda p:p['initContainers'][0]['volumeMounts'].append({'name':'credentials','mountPath':'/credentials'})),
   ('subpath',lambda p:p['initContainers'][0]['volumeMounts'][0].update(subPath='foreign')),
   ('resources',lambda p:p['initContainers'][0]['resources']['limits'].update(cpu='999m')),
   ('sidecar',lambda p:p['initContainers'][0].update(restartPolicy='Always')),
   ('env',lambda p:p['initContainers'][0].update(env=[{'name':'FOREIGN','value':'x'}])),
   ('privileged',lambda p:p['initContainers'][0]['securityContext'].update(privileged=True)),
   ('unsupervised',lambda p:p['containers'][0].update(command=['/bin/bash','/opt/perkforge/bin/launch']))]:
   bad=copy.deepcopy(job);mutation(bad['spec']['template']['spec'])
   cases.append({'Name':phase+'-init-'+label,'Policy':pol,'Object':bad,'Allowed':False})
  defaulted=copy.deepcopy(job);init=defaulted['spec']['template']['spec']['initContainers'][0];init.pop('args');init.update(terminationMessagePath='/dev/termination-log',terminationMessagePolicy='File',imagePullPolicy='IfNotPresent')
  cases.append({'Name':phase+'-init-defaulted','Policy':pol,'Object':defaulted,'Allowed':True})
from private_receipts import plan
H=plan(I)
cases.append({'Name':'private-init','Policy':'identity-pods-'+B['writer_namespace'],'Object':H['pod'],'Allowed':True})
defaulted=copy.deepcopy(H['pod']);defaulted['spec']['containers'][0].pop('args')
cases.append({'Name':'private-init-omitted-empty-args','Policy':'identity-pods-'+B['writer_namespace'],'Object':defaulted,'Allowed':True})
for field,value in [('command',['false']),('image','foreign'),('args',['foreign'])]:
 bad=copy.deepcopy(H['pod']);bad['spec']['containers'][0][field]=value;cases.append({'Name':'private-init-'+field,'Policy':'identity-pods-'+B['writer_namespace'],'Object':bad,'Allowed':False})
for key in ('configMap','inputs','gate'):
 cases.append({'Name':'private-init-'+key,'Policy':'identity-config-'+B['writer_namespace'],'Object':H[key],'Username':I['operatorUser'],'Allowed':True})
cases.append({'Name':'private-gate-foreign','Policy':'identity-config-'+B['writer_namespace'],'Object':H['gate'],'Username':'foreign','Allowed':False})
for mode in ('absent','empty','approval','foreign-absent','binary','extra','oversize'):
 gate=copy.deepcopy(H['gate']);user=I['operatorUser'];allowed=mode in ('absent','empty','approval')
 if mode in ('absent','foreign-absent'):gate.pop('data',None)
 if mode=='approval':gate['data']={'approval.json':'{}'}
 if mode=='foreign-absent':user='foreign'
 if mode=='binary':gate.pop('data',None);gate['binaryData']={'approval.json':'e30='}
 if mode=='extra':gate['data']={'other':'{}'}
 if mode=='oversize':gate['data']={'approval.json':'x'*4097}
 cases.append({'Name':'private-gate-'+mode,'Policy':'identity-config-'+B['writer_namespace'],'Object':gate,'Username':user,'Allowed':allowed})
schemas={}
crd_path=os.environ.get('IDENTITY_FLUX_CRD') or (os.path.join(os.environ['NEXTCLOUD_CRD_DIR'],'kustomization.yaml') if os.environ.get('NEXTCLOUD_CRD_DIR') else None)
if crd_path:
 crd=yaml.safe_load(open(crd_path));v=next(v for v in crd['spec']['versions'] if v['name']=='v1');schemas['io.k8s.api.kustomize.toolkit.fluxcd.io.v1.Kustomization']=v['schema']['openAPIV3Schema']
print(json.dumps({'Policies':policies,'Cases':cases,'Schemas':schemas}))
