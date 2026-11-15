#!/usr/bin/env python3
"""Offline, default-off foundation plan. Does not apply objects or read credentials."""
import argparse,copy,ipaddress,json,pathlib,re
import yaml
from finite_identity import render,PHASES
OWNER={'platform.perkforge.io/owner':'tenant-identity-foundation-v1'}
WRITER='tenant-identity-writer';ATTESTOR='tenant-identity-attestor'
def obj(api,kind,name,namespace=None,**fields):
 m={'name':name,'labels':OWNER.copy()}
 if namespace:m['namespace']=namespace
 return {'apiVersion':api,'kind':kind,'metadata':m,**fields}
def sa(name,ns):return obj('v1','ServiceAccount',name,ns,automountServiceAccountToken=False)
def role(name,ns,rules,subject,subject_ns):
 return [obj('rbac.authorization.k8s.io/v1','Role',name,ns,rules=rules),obj('rbac.authorization.k8s.io/v1','RoleBinding',name,ns,roleRef={'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':name},subjects=[{'kind':'ServiceAccount','name':subject,'namespace':subject_ns}])]
def rule(group,resources,verbs,names=None):
 d={'apiGroups':[group],'resources':resources,'verbs':verbs}
 if names:d['resourceNames']=names
 return d
def cel(v):return json.dumps(v,separators=(',',':'))
def policy(name,group,version,resource,ns,validations,operations=('CREATE','UPDATE')):
 p=obj('admissionregistration.k8s.io/v1','ValidatingAdmissionPolicy',name,spec={'failurePolicy':'Fail','matchConstraints':{'resourceRules':[{'apiGroups':[group],'apiVersions':[version],'operations':list(operations),'resources':[resource]}]},'matchConditions':[{'name':'exact-namespace','expression':'request.namespace == '+cel(ns)}],'validations':[{'expression':x,'message':'Identity foundation boundary refused an unreviewed mutation.','reason':'Forbidden'} for x in validations]})
 return [p,obj('admissionregistration.k8s.io/v1','ValidatingAdmissionPolicyBinding',name,spec={'policyName':name,'validationActions':['Deny']})]
def pod_checks(p,prefix='object.spec.template.spec'):
 x=prefix;c=x+'.containers[0]';v=p['containers'][0]
 checks=[x+'.containers.size() == 1',x+'.serviceAccountName == '+cel(p['serviceAccountName']),x+'.automountServiceAccountToken == false',x+'.restartPolicy == "Never"',x+'.nodeSelector == '+cel(p['nodeSelector'])]
 for k in ('hostNetwork','hostPID','hostIPC','shareProcessNamespace'):checks.append('(!has('+x+'.'+k+') || '+x+'.'+k+' == false)')
 for k in ('nodeName','initContainers','ephemeralContainers','hostAliases','dnsConfig','runtimeClassName','affinity','tolerations','topologySpreadConstraints','resourceClaims','os'):checks.append('!has('+x+'.'+k+')')
 checks.append('!has(dyn('+x+').overhead)')
 for k in ('name','image','command'):checks.append(c+'.'+k+' == '+cel(v[k]))
 checks.append('(!has('+c+'.args) || '+c+'.args.size() == 0)' if v['args']==[] else c+'.args == '+cel(v['args']))
 for k in ('env','envFrom','lifecycle','livenessProbe','readinessProbe','startupProbe','ports','workingDir','volumeDevices','restartPolicy','restartPolicyRules'):checks.append('!has('+c+'.'+k+')')
 for field,value in (('terminationMessagePath','/dev/termination-log'),('terminationMessagePolicy','File')):checks.append('(!has('+c+'.'+field+') || '+c+'.'+field+' == '+cel(value)+')')
 for field in ('stdin','stdinOnce','tty'):checks.append('(!has('+c+'.'+field+') || '+c+'.'+field+' == false)')
 checks += ['(!has('+x+'.schedulerName) || '+x+'.schedulerName == \"default-scheduler\")','(!has('+x+'.priorityClassName) || '+x+'.priorityClassName == \"\")','(!has('+x+'.priority) || '+x+'.priority == 0)']
 for k in ('runAsUser','runAsGroup','runAsNonRoot','seccompProfile','seLinuxOptions','appArmorProfile','procMount'):checks.append('!has('+c+'.securityContext.'+k+')')
 for k in ('seLinuxOptions','supplementalGroups','sysctls','appArmorProfile'):checks.append('!has('+x+'.securityContext.'+k+')')
 checks += [c+'.securityContext.allowPrivilegeEscalation == false',c+'.securityContext.readOnlyRootFilesystem == true',c+'.securityContext.capabilities.drop == ["ALL"]','(!has('+c+'.securityContext.capabilities.add) || '+c+'.securityContext.capabilities.add.size() == 0)','(!has('+c+'.securityContext.privileged) || '+c+'.securityContext.privileged == false)',x+'.securityContext.runAsNonRoot == true',x+'.securityContext.runAsUser == 1001',x+'.securityContext.runAsGroup == 1001',x+'.securityContext.fsGroup == 1001',x+'.securityContext.fsGroupChangePolicy == "OnRootMismatch"',x+'.securityContext.seccompProfile.type == "RuntimeDefault"','dyn('+c+'.resources).requests == '+cel(v['resources']['requests']),'dyn('+c+'.resources).limits == '+cel(v['resources']['limits'])]
 checks += [x+'.imagePullSecrets.size() == 1',x+'.imagePullSecrets[0].name == '+cel(p['imagePullSecrets'][0]['name']),x+'.volumes.size() == '+str(len(p['volumes'])),c+'.volumeMounts.size() == '+str(len(v['volumeMounts']))]
 # Compare explicit source/mount leaves, not permissive name-only allowlists.
 def leaves(value,path):
  if isinstance(value,dict):
   out=[]
   for key,val in value.items():out += leaves(val,path+'.'+key)
   return out
  if isinstance(value,list):
   return [path+'.size() == '+str(len(value))]+[z for i,val in enumerate(value) for z in leaves(val,path+'['+str(i)+']')]
  if path.endswith('.emptyDir.sizeLimit'):path='dyn('+path.rsplit('.',1)[0]+').sizeLimit'
  return [path+' == '+cel(value)]
 for i,volume in enumerate(p['volumes']):checks+=leaves(volume,x+'.volumes['+str(i)+']')
 for i,mount in enumerate(v['volumeMounts']):
  q=c+'.volumeMounts['+str(i)+']';checks+=leaves(mount,q)
  for k in ('subPath','subPathExpr','mountPropagation'):
   if k not in mount:checks+=['!has('+q+'.'+k+')']
 return checks

def build(d,network,custody,initializer=None):
 generated=render(d)
 if not d.get('enabled'):return []
 if set(network)!={'ingressHosts','apiHosts','apiBackendHosts','apiCA','traefikBackend'} or network['traefikBackend'] is not True:raise ValueError('explicit target endpoints required')
 if not isinstance(network['apiCA'],str) or not network['apiCA'].startswith('-----BEGIN CERTIFICATE-----'):raise ValueError('explicit public API CA')
 for k in ('ingressHosts','apiHosts','apiBackendHosts'):
  if not isinstance(network[k],list) or not 1<=len(network[k])<=4:raise ValueError('bounded endpoints')
  for ip in network[k]:
   n=ipaddress.ip_network(ip,strict=True)
   if n.prefixlen!=n.max_prefixlen:raise ValueError('single-host CIDRs only')
 if set(custody)!={'server','publicCA','writer','reader','keycloak'} or not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::[0-9]+)?',custody['server']):raise ValueError('exact custody inputs')
 if not isinstance(custody['publicCA'],str) or not custody['publicCA'].startswith('-----BEGIN CERTIFICATE-----'):raise ValueError('public CA required')
 expected={'writer':{'group-writer'},'reader':{'gitlab-reader'},'keycloak':{'kc-client-id','kc-client-secret'}}
 for k,fields in expected.items():
  if set(custody[k])!={'record','properties'} or set(custody[k]['properties'])!=fields or not re.fullmatch(r'identity/[a-z0-9/-]+',custody[k]['record']):raise ValueError('exact scoped record')
  if any(not re.fullmatch(r'[a-z][a-z0-9_-]{0,40}',v) for v in custody[k]['properties'].values()):raise ValueError('property')
 init=None
 if initializer is not None:
  from private_receipts import plan
  if (initializer['claim'],initializer['node'],initializer['pullSecret'])!=(d['receiptClaim'],d['workerNode'],d['pullSecret']):raise ValueError('initializer declaration mismatch')
  init=plan(initializer)
 out=[]
 for ns,worker,reconciler in ((WRITER,'identity-group-worker','identity-group-reconciler'),(ATTESTOR,'identity-attestor','identity-attestor-reconciler')):
  n=obj('v1','Namespace',ns);n['metadata']['labels'].update({'pod-security.kubernetes.io/enforce':'restricted','pod-security.kubernetes.io/enforce-version':'latest'});out += [n,sa(worker,ns),sa(reconciler,'flux-system')]
  phases=['foundation','memberships'] if ns==WRITER else ['attest'];jobs=[generated[p+'/job.yaml'] for p in phases];cms=[generated[p+'/inputs.yaml'] for p in phases]+[generated[phases[0]+'/source.yaml']]
  names=[j['metadata']['name'] for j in jobs];cmnames=[c['metadata']['name'] for c in cms]
  out+=role(reconciler,ns,[rule('batch',['jobs'],['create']),rule('batch',['jobs'],['get','patch'],names),rule('batch',['jobs'],['list','watch']),rule('',['pods'],['get','list','watch']),rule('',['configmaps'],['create']),rule('',['configmaps'],['get','patch','update'],cmnames)],reconciler,'flux-system')
  # CREATE cannot be restricted by resourceNames. Admission is mandatory first.
  out+=policy('identity-jobs-'+ns,'batch','v1','jobs',ns,[" || ".join('('+ ' && '.join(['object.metadata.name == '+cel(j['metadata']['name']),'object.metadata.annotations == '+cel(j['metadata']['annotations']),'object.spec.completions == 1','object.spec.parallelism == 1','object.spec.backoffLimit == 0','object.spec.activeDeadlineSeconds == 300','!has(object.spec.ttlSecondsAfterFinished)','(!has(object.spec.suspend) || object.spec.suspend == false)','(!has(object.spec.completionMode) || object.spec.completionMode == \"NonIndexed\")','!has(object.spec.podFailurePolicy)','!has(object.spec.successPolicy)', 'object.spec.template.metadata.annotations == '+cel(j['spec']['template']['metadata']['annotations'])]+pod_checks(j['spec']['template']['spec']))+')' for j in jobs)])
  pod_clauses=[]
  for j in jobs:
   checks=pod_checks(j['spec']['template']['spec'],'object.spec')
   checks=[x for x in checks if x!='!has(object.spec.tolerations)']
   checks += ["(!has(object.spec.tolerations) || (object.spec.tolerations.size() <= 2 && object.spec.tolerations.all(t, t.key in ['node.kubernetes.io/not-ready','node.kubernetes.io/unreachable'] && t.operator == 'Exists' && t.effect == 'NoExecute' && t.tolerationSeconds == 300)))",'object.metadata.ownerReferences.size() == 1','object.metadata.ownerReferences[0].apiVersion == "batch/v1"','object.metadata.ownerReferences[0].kind == "Job"','object.metadata.ownerReferences[0].controller == true','object.metadata.ownerReferences[0].name == '+cel(j['metadata']['name']),'object.metadata.generateName == '+cel(j['metadata']['name']+'-'),'object.metadata.annotations == '+cel(j['spec']['template']['metadata']['annotations'])]
   pod_clauses.append('('+' && '.join(checks)+')')
  if init and ns==WRITER:
   h=init['pod'];checks=pod_checks(h['spec'],'object.spec');checks=[x for x in checks if x!='!has(object.spec.tolerations)'];checks += ['object.metadata.name == '+cel(h['metadata']['name']),'object.metadata.annotations == '+cel(h['metadata']['annotations']),'object.metadata.labels == '+cel(h['metadata']['labels']),'!has(object.metadata.ownerReferences)','object.spec.activeDeadlineSeconds == 300','(!has(object.spec.tolerations) || (object.spec.tolerations.size() <= 2 && object.spec.tolerations.all(t, t.key in ["node.kubernetes.io/not-ready","node.kubernetes.io/unreachable"] && t.operator == "Exists" && t.effect == "NoExecute" && t.tolerationSeconds == 300)))'];pod_clauses.append('('+' && '.join(checks)+')')
  out+=policy('identity-pods-'+ns,'','v1','pods',ns,[' || '.join(pod_clauses)],operations=('CREATE',))
  # One bounded implication per exact name/key, never one giant OR literal.
  # Exact key sets preserve full-map equality; unknown object names remain denied.
  checks=[];names=[]
  def exact_cm(name,data,immutable):
   names.append(name);prefix='object.metadata.name != '+cel(name)+' || '
   checks.append(prefix+'(!has(object.binaryData) && '+('object.immutable == true && ' if immutable else '')+'object.data.size() == '+str(len(data))+' && object.data.all(k, k in '+cel(list(data))+'))')
   for key,value in data.items():checks.append(prefix+'object.data['+cel(key)+'] == '+cel(value))
  exact_cm('kube-root-ca.crt',{'ca.crt':network['apiCA']},False)
  exact_cm('identity-openbao-ca',{'ca.crt':custody['publicCA']},True)
  for cm in cms:exact_cm(cm['metadata']['name'],cm['data'],True)
  if init and ns==WRITER:
   for cm in (init['configMap'],init['inputs']):exact_cm(cm['metadata']['name'],cm['data'],True)
   name=init['gate']['metadata']['name'];names.append(name)
   checks.append('object.metadata.name != '+cel(name)+' || (request.userInfo.username == '+cel(initializer['operatorUser'])+' && !has(object.binaryData) && object.data.size() <= 1 && object.data.all(k, k == "approval.json" && object.data[k].size() <= 4096))')
  if ns==WRITER:names.append('portal-identity-evidence')
  checks.insert(0,'object.metadata.name in '+cel(names))
  if any(len(x)>90000 for x in checks):raise ValueError('admission expression exceeds conservative source budget')
  out+=policy('identity-config-'+ns,'','v1','configmaps',ns,checks)
  out.append(obj('networking.k8s.io/v1','NetworkPolicy','identity-default-deny',ns,spec={'podSelector':{},'policyTypes':['Ingress','Egress']}))
  dns={'to':[{'namespaceSelector':{'matchLabels':{'kubernetes.io/metadata.name':'kube-system'}},'podSelector':{'matchLabels':{'k8s-app':'kube-dns'}}}],'ports':[{'protocol':'UDP','port':53},{'protocol':'TCP','port':53}]}
  egress=[dns,{'to':[{'ipBlock':{'cidr':ip}} for ip in network['ingressHosts']],'ports':[{'protocol':'TCP','port':443}]},{'to':[{'namespaceSelector':{'matchLabels':{'kubernetes.io/metadata.name':'kube-system'}},'podSelector':{'matchLabels':{'app.kubernetes.io/name':'rke2-traefik','app.kubernetes.io/instance':'rke2-traefik-kube-system'}}}],'ports':[{'protocol':'TCP','port':8443}]}]
  if ns==ATTESTOR:egress += [{'to':[{'ipBlock':{'cidr':ip}} for ip in network[key]],'ports':[{'protocol':'TCP','port':port}]} for key,port in [('apiHosts',443),('apiBackendHosts',6443)]]
  out.append(obj('networking.k8s.io/v1','NetworkPolicy','identity-worker-egress',ns,spec={'podSelector':{'matchLabels':{'platform.perkforge.io/identity-phase':'true'}},'policyTypes':['Egress'],'egress':egress}))
 out.append(sa('identity-declaration-reconciler','flux-system'))
 children=[generated[p+'-reconcile.yaml'] for p in PHASES]
 out += role('identity-declaration-reconciler','flux-system',[rule('kustomize.toolkit.fluxcd.io',['kustomizations'],['create']),rule('kustomize.toolkit.fluxcd.io',['kustomizations'],['get','patch','update'],[c['metadata']['name'] for c in children])],'identity-declaration-reconciler','flux-system')
 out += role('identity-receipt-intent',WRITER,[rule('',['configmaps'],['get','patch'],['portal-identity-evidence'])],'identity-declaration-reconciler','flux-system')
 allowed=[]
 for child in children:
  q=child['spec'];checks=['object.metadata.name == '+cel(child['metadata']['name'])]
  for key in ('interval','timeout','path','serviceAccountName','prune','force','wait'):checks.append('object.spec.'+key+' == '+cel(q[key]))
  checks.append('object.spec.suspend == '+cel(q['suspend']) if 'suspend' in q else '!has(object.spec.suspend) || object.spec.suspend == false')
  checks += ['object.spec.commonMetadata.annotations == '+cel(q['commonMetadata']['annotations']),'!has(object.spec.commonMetadata.labels)','object.spec.healthChecks.size() == 1']
  checks += ['object.spec.healthChecks[0].'+k+' == '+cel(v) for k,v in q['healthChecks'][0].items()]
  checks += ['object.spec.sourceRef.kind == "GitRepository"','object.spec.sourceRef.name == '+cel(q['sourceRef']['name']),'!has(object.spec.sourceRef.namespace)']
  checks += (['object.spec.dependsOn.size() == 1','!has(object.spec.dependsOn[0].namespace)']+['object.spec.dependsOn[0].'+k+' == '+cel(v) for k,v in q['dependsOn'][0].items()]) if 'dependsOn' in q else ['!has(object.spec.dependsOn)']
  for key in ('kubeConfig','decryption','postBuild','patches','images','components','targetNamespace','namePrefix','nameSuffix','healthCheckExprs'):checks.append('!has(object.spec.'+key+')')
  allowed.append('('+' && '.join(checks)+')')
 declaration_user='system:serviceaccount:flux-system:identity-declaration-reconciler'
 out += policy('identity-declaration-scope','kustomize.toolkit.fluxcd.io','v1','kustomizations','flux-system',['request.userInfo.username != '+cel(declaration_user)+' || ('+' || '.join(allowed)+')'])
 out += role('identity-evidence-issuer',WRITER,[rule('',['configmaps'],['get','patch'],['portal-identity-evidence'])],'identity-attestor',ATTESTOR)
 uid=d['phaseInputs']['attest']['identity']['identity_receipt_uid'];issuer='system:serviceaccount:'+ATTESTOR+':identity-attestor'
 out+=policy('identity-evidence-fields','','v1','configmaps',WRITER,["object.metadata.name != 'portal-identity-evidence' || (request.operation == 'UPDATE' && oldObject != null && object.metadata.uid == "+cel(uid)+" && oldObject.metadata.uid == "+cel(uid)+" && !has(object.binaryData) && (!has(object.immutable) || object.immutable == false) && ((request.userInfo.username == "+cel(issuer)+" && object.metadata.annotations == oldObject.metadata.annotations && object.metadata.labels == oldObject.metadata.labels && object.data.size() == 1 && 'receipt.json' in object.data && object.data['receipt.json'].size() <= 262144) || (request.userInfo.username == "+cel(declaration_user)+" && object.metadata.labels == oldObject.metadata.labels && has(object.data) == has(oldObject.data) && (!has(object.data) || object.data == oldObject.data) && object.metadata.annotations == {'perkforge.dev/desired-invocation': "+cel(d['invocation'])+"})))"])
 for field in ('ownerReferences','finalizers'):
  out[-2]['spec']['validations'].append({'expression':"object.metadata.name != 'portal-identity-evidence' || (oldObject != null && has(object.metadata."+field+") == has(oldObject.metadata."+field+") && (!has(object.metadata."+field+") || object.metadata."+field+" == oldObject.metadata."+field+"))",'message':'Evidence ownership metadata is immutable.','reason':'Forbidden'})
 out.append(obj('v1','PersistentVolumeClaim',d['receiptClaim'],WRITER,spec={'accessModes':['ReadWriteOnce'],'storageClassName':'longhorn','resources':{'requests':{'storage':'1Gi'}}}))
 # Empty destination Secrets are CREATE-ONLY separate artifacts, never reapplied.
 for ns,name in ((WRITER,d['writerSecret']),(ATTESTOR,d['attestorSecret'])):out.append(obj('v1','Secret',name,ns,type='Opaque',data={}))
 for purpose,ns,target in (('writer',WRITER,d['writerSecret']),('reader',ATTESTOR,d['attestorSecret']),('keycloak',ATTESTOR,d['attestorSecret'])):
  name='eso-identity-'+purpose;record=custody[purpose]
  out += [sa(name,ns),obj('v1','ConfigMap','identity-openbao-ca',ns,immutable=True,data={'ca.crt':custody['publicCA']})]
  out+=role(name,ns,[rule('',['secrets'],['get','update','patch'],[target]),rule('',['serviceaccounts/token'],['create'],[name]),rule('',['configmaps'],['get'],['identity-openbao-ca']),rule('external-secrets.io',['externalsecrets'],['patch'],[name]),rule('external-secrets.io',['externalsecrets/status'],['update','patch'],[name]),rule('external-secrets.io',['secretstores/status'],['patch'],[name])],'external-secrets','external-secrets')
  out.append(obj('external-secrets.io/v1','SecretStore',name,ns,spec={'controller':'perkforge','provider':{'vault':{'server':custody['server'],'path':'platform','version':'v2','caProvider':{'type':'ConfigMap','name':'identity-openbao-ca','key':'ca.crt'},'auth':{'kubernetes':{'mountPath':'kubernetes-eso','role':name,'serviceAccountRef':{'name':name,'audiences':['openbao-eso']}}}}}}))
  out.append(obj('external-secrets.io/v1','ExternalSecret',name,ns,spec={'refreshInterval':'1h','secretStoreRef':{'kind':'SecretStore','name':name},'target':{'name':target,'creationPolicy':'Merge','deletionPolicy':'Retain','template':{'engineVersion':'v2','mergePolicy':'Merge','type':'Opaque','data':{'lab-ca.crt':custody['publicCA']}}},'data':[{'secretKey':k,'remoteRef':{'key':record['record'],'property':v,'conversionStrategy':'Default','decodingStrategy':'None'}} for k,v in record['properties'].items()]}))
 # Return split phases, not one apply-able stream: admission/namespace review first,
 # create-only placeholders and UID recording next; consumers/jobs remain separate.
 unique={}
 for o in out:
  key=(o['apiVersion'],o['kind'],o['metadata'].get('namespace'),o['metadata']['name'])
  if key in unique and unique[key]!=o:raise ValueError('conflicting duplicate object')
  unique[key]=o
 return list(unique.values())
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--declaration',type=pathlib.Path,required=True);p.add_argument('--network',type=pathlib.Path);p.add_argument('--custody',type=pathlib.Path);p.add_argument('--initializer',type=pathlib.Path);p.add_argument('--output',type=pathlib.Path);p.add_argument('--render',action='store_true');a=p.parse_args()
 if not a.render:print('INERT: source planning only.');raise SystemExit(0)
 d=json.loads(a.declaration.read_text());network=json.loads(a.network.read_text()) if a.network else {};custody=json.loads(a.custody.read_text()) if a.custody else {};objects=build(d,network,custody,json.loads(a.initializer.read_text()) if a.initializer else None)
 if not a.output:raise SystemExit('Explicit offline output required.')
 a.output.mkdir(parents=True,exist_ok=False)
 for i,o in enumerate(objects):(a.output/(str(i).zfill(3)+'-'+o['kind'].lower()+'.yaml')).write_text(yaml.safe_dump(o,sort_keys=False))
