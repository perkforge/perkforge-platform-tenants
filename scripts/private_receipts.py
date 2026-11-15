#!/usr/bin/env python3
"""Offline exact helper plan and read-only runtime identity gate. No apply/delete API."""
import argparse,hashlib,json,pathlib,re,copy,subprocess,time,ipaddress
from finite_identity import IMAGE
from identity_context_binding import selection
from identity_target_profile import storage,initializer_identity
def selected(i):
 return selection({'context':i.get('context','portal'),**({'contextDigest':i['contextDigest']} if 'contextDigest' in i else {})})
def namespace(i):return selected(i)['writer_namespace']
BUDGET={'requests':{'cpu':'100m','memory':'256Mi'},'limits':{'cpu':'500m','memory':'512Mi'}}
def validate(i):
 if set(i)-{'context','contextDigest'}!={'storageProfile','clusterUID','claim','claimUID','pv','pvUID','volumeHandle','node','pullSecret','operatorUser'}:raise ValueError('exact inputs')
 selected(i);storage(i['storageProfile'])
 if not re.fullmatch('[A-Za-z0-9:._@/-]{1,160}',i['operatorUser']):raise ValueError('exact operator identity')
 for k in ('clusterUID','claimUID'):
  if not re.fullmatch('[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}',i[k]):raise ValueError('UID required')
 for k in ('pv','pvUID','volumeHandle'):
  if i[k] is not None and not re.fullmatch('[a-z0-9][a-z0-9.-]{0,100}',i[k]):raise ValueError('binding field')
 for k in ('claim','node','pullSecret'):
  if not re.fullmatch('[a-z0-9][a-z0-9.-]{0,100}',i[k]):raise ValueError('name')
def guard(i,cluster,pvc,pv,pods,helper_uid=None):
 validate(i)
 if cluster['metadata']['uid']!=i['clusterUID']:raise ValueError('cluster mismatch')
 m=pvc['metadata'];s=pvc['spec']
 if s.get('volumeMode','Filesystem')!='Filesystem' or s.get('dataSource') is not None or s.get('dataSourceRef') is not None:raise ValueError('fresh filesystem only')
 if (m['name'],m['namespace'],m['uid'])!=(i['claim'],namespace(i),i['claimUID']) or m.get('deletionTimestamp'):raise ValueError('claim identity')
 if m.get('labels',{}).get('platform.perkforge.io/owner')!='tenant-identity-foundation-v1':raise ValueError('claim owner')
 if pvc['status']['phase']!='Bound' or s['volumeName']!=i['pv'] or s['storageClassName']!=i['storageProfile']['className'] or s['accessModes']!=['ReadWriteOnce'] or s['resources']['requests']['storage']!=i['storageProfile']['size']:raise ValueError('claim spec')
 if pv['metadata']['name']!=i['pv'] or pv['metadata']['uid']!=i['pvUID'] or pv['metadata'].get('deletionTimestamp'):raise ValueError('PV identity')
 p=pv['spec'];r=p['claimRef'];c=p['csi']
 if (r['name'],r['namespace'],r['uid'])!=(i['claim'],namespace(i),i['claimUID']) or c['driver']!='driver.longhorn.io' or c['volumeHandle']!=i['volumeHandle'] or p['persistentVolumeReclaimPolicy']!='Retain':raise ValueError('PV binding')
 for pod in pods:
  if helper_uid is not None and pod['metadata'].get('uid')==helper_uid:continue
  if pod['metadata']['namespace']==namespace(i) and any(v.get('persistentVolumeClaim',{}).get('claimName')==i['claim'] for v in pod['spec'].get('volumes',[])):raise ValueError('PVC consumer exists, including completed/terminating helpers')
 return True

def pending_guard(i,cluster,pvc,pods):
 validate(i)
 m=pvc['metadata'];s=pvc['spec']
 if s.get('volumeMode','Filesystem')!='Filesystem' or s.get('dataSource') is not None or s.get('dataSourceRef') is not None:raise ValueError('fresh filesystem only')
 if cluster['metadata']['uid']!=i['clusterUID'] or (m['name'],m['namespace'],m['uid'])!=(i['claim'],namespace(i),i['claimUID']):raise ValueError('prebind identity')
 if m.get('deletionTimestamp') or m.get('labels',{}).get('platform.perkforge.io/owner')!='tenant-identity-foundation-v1':raise ValueError('prebind ownership')
 if pvc['status']['phase'] not in ('Pending','Bound') or s['storageClassName']!=i['storageProfile']['className'] or s['accessModes']!=['ReadWriteOnce'] or s['resources']['requests']['storage']!=i['storageProfile']['size']:raise ValueError('prebind spec')
 if any(p['metadata']['namespace']==namespace(i) and any(v.get('persistentVolumeClaim',{}).get('claimName')==i['claim'] for v in p['spec'].get('volumes',[])) for p in pods):raise ValueError('prebind consumer')
 return True

def helper_annotations(actual,expected,status):
 # Only observed Calico metadata is normalized; protected fields stay exact.
 if not isinstance(actual,dict):raise ValueError('helper annotations')
 extra=set(actual)-set(expected)
 keys={'cni.projectcalico.org/containerID','cni.projectcalico.org/podIP','cni.projectcalico.org/podIPs'}
 if extra:
  if extra!=keys:raise ValueError('unknown or partial CNI annotations')
  cid,one,many=[actual[k] for k in ('cni.projectcalico.org/containerID','cni.projectcalico.org/podIP','cni.projectcalico.org/podIPs')]
  if not isinstance(cid,str) or not re.fullmatch(r'[0-9a-f]{64}',cid):raise ValueError('CNI container identity')
  if not isinstance(one,str) or len(one)>64 or '/' not in one or many!=one:raise ValueError('CNI single-IP representation')
  address=ipaddress.ip_interface(one)
  if address.network.prefixlen!=address.max_prefixlen or str(address.ip)!=status.get('podIP'):raise ValueError('CNI address mismatch')
 if {k:v for k,v in actual.items() if k not in extra}!=expected:raise ValueError('protected helper annotations')
 return True

def release_patch(i,cluster,pvc,pv,pods,helper,gate):
 # Caller supplies fresh metadata, never credentials. This only emits a CAS patch.
 h=plan(i);m=helper['metadata'];uid=m['uid']
 if (m['name'],m['namespace'])!=(h['pod']['metadata']['name'],namespace(i)) or not helper_annotations(m.get('annotations'),h['pod']['metadata']['annotations'],helper.get('status',{})) or m.get('labels')!=h['pod']['metadata']['labels'] or m.get('deletionTimestamp'):raise ValueError('helper identity')
 if helper['spec'].get('nodeName')!=i['node'] or helper['status']['phase']!='Running':raise ValueError('helper placement')
 for k in ('containers','volumes','serviceAccountName','automountServiceAccountToken','nodeSelector','securityContext','restartPolicy','activeDeadlineSeconds','imagePullSecrets'):
  # Runtime default representation must be independently reviewed before use.
  actual=copy.deepcopy(helper['spec'][k]);expected=h['pod']['spec'][k]
  if k=='containers':
   for index,c in enumerate(actual):
    if index<len(expected) and expected[index].get('args')==[] and 'args' not in c:c['args']=[]
    for key,default in [('imagePullPolicy','IfNotPresent'),('terminationMessagePath','/dev/termination-log'),('terminationMessagePolicy','File')]:
     if key in c:
      if c.pop(key)!=default:raise ValueError('unsafe container default')
  if k=='volumes':
   for v in actual:
    for key in ('configMap','downwardAPI'):
     if key in v:
      if v[key].pop('defaultMode',420)!=420:raise ValueError('volume mode')
      for item in v[key].get('items',[]):
       if 'fieldRef' in item and item['fieldRef'].pop('apiVersion','v1')!='v1':raise ValueError('field API')
  if actual!=expected:raise ValueError('helper spec/default mismatch')
 bound=dict(i,pv=pv['metadata']['name'],pvUID=pv['metadata']['uid'],volumeHandle=pv['spec']['csi']['volumeHandle'])
 for key in ('pv','pvUID','volumeHandle'):
  if i[key] is not None and i[key]!=bound[key]:raise ValueError('supplied binding mismatch')
 guard(bound,cluster,pvc,pv,pods,uid)
 if gate['metadata']['name']!=h['gate']['metadata']['name'] or gate['metadata']['namespace']!=namespace(i) or gate.get('data',{})!={}:raise ValueError('gate must be fresh/empty')
 approval={'schemaVersion':1,'claimUID':i['claimUID'],'helperUID':uid,'pvUID':bound['pvUID'],'volumeHandle':bound['volumeHandle'],'sourceSHA256':h['pod']['metadata']['annotations']['platform.perkforge.io/source-sha256']}
 return {'boundInputs':bound,'patch':[{'op':'test','path':'/metadata/uid','value':gate['metadata']['uid']},{'op':'test','path':'/metadata/resourceVersion','value':gate['metadata']['resourceVersion']},{'op':'add','path':'/data','value':{'approval.json':json.dumps(approval,sort_keys=True)}}]}

def cleanup_proof(i,cluster,pvc,pv,pods,volumeattachments,longhorn):
 guard(i,cluster,pvc,pv,pods)
 if any(v['spec'].get('source',{}).get('persistentVolumeName')==i['pv'] for v in volumeattachments):raise ValueError('CSI attachment remains')
 if longhorn['metadata']['name']!=i['volumeHandle'] or longhorn['status']['state']!='detached' or longhorn['spec'].get('nodeID'):raise ValueError('volume not detached')
 return True

def plan(i):
 validate(i);script=(pathlib.Path(__file__).resolve().parents[1]/'executor/initialize-private-receipts.py').read_text();sha=hashlib.sha256(script.encode()).hexdigest();name='identity-private-init-'+hashlib.sha256(json.dumps(initializer_identity(i),sort_keys=True).encode()).hexdigest()[:16]
 cm={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':'identity-private-init-'+sha[:20],'namespace':namespace(i)},'immutable':True,'data':{'initialize.py':script}}
 pod={'apiVersion':'v1','kind':'Pod','metadata':{'name':name,'namespace':namespace(i),'labels':{'platform.perkforge.io/owner':'identity-private-init-v1'},'annotations':{'platform.perkforge.io/claim-uid':i['claimUID'],'platform.perkforge.io/source-sha256':sha}},'spec':{'serviceAccountName':'identity-group-worker','automountServiceAccountToken':False,'nodeSelector':{'kubernetes.io/hostname':i['node']},'restartPolicy':'Never','activeDeadlineSeconds':300,'imagePullSecrets':[{'name':i['pullSecret']}],'securityContext':{'runAsUser':1001,'runAsGroup':1001,'runAsNonRoot':True,'fsGroup':1001,'fsGroupChangePolicy':'OnRootMismatch','seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'initialize','image':IMAGE,'command':['/home/python/python-env/bin/python3','-B','/source/initialize.py'],'args':[],'resources':BUDGET,'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'volumeMounts':[{'name':'receipts','mountPath':'/volume'},{'name':'source','mountPath':'/source','readOnly':True}]}],'volumes':[{'name':'receipts','persistentVolumeClaim':{'claimName':i['claim']}},{'name':'source','configMap':{'name':cm['metadata']['name']}}]}}
 inputs={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':name+'-inputs','namespace':namespace(i)},'immutable':True,'data':{'initialization.json':json.dumps({'claimUID':i['claimUID'],'sourceSHA256':sha},sort_keys=True)}}
 gate={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':name+'-gate','namespace':namespace(i)},'data':{}}
 pod['spec']['volumes'] += [{'name':'inputs','configMap':{'name':inputs['metadata']['name']}},{'name':'gate','configMap':{'name':gate['metadata']['name']}},{'name':'identity','downwardAPI':{'items':[{'path':'poduid','fieldRef':{'fieldPath':'metadata.uid'}}]}}]
 pod['spec']['containers'][0]['volumeMounts'] += [{'name':'inputs','mountPath':'/inputs','readOnly':True},{'name':'gate','mountPath':'/gate','readOnly':True},{'name':'identity','mountPath':'/identity','readOnly':True}]
 return {'configMap':cm,'inputs':inputs,'gate':gate,'pod':pod}

def kube(*args,body=None):
 return json.loads(subprocess.check_output(['kubectl',*args],input=json.dumps(body).encode() if body is not None else None,timeout=30))
def get(kind,name=None,namespace=None):
 args=['get',kind]+([name] if name else [])+(['-n',namespace] if namespace else [])+['-o','json']
 return kube(*args)
def remaining(deadline):
 seconds=deadline-time.monotonic()
 if seconds<=0:raise ValueError('pre-release deadline expired')
 return seconds

def wait_for(fn,seconds,deadline=None):
 end=time.monotonic()+seconds
 if deadline is not None:end=min(end,deadline)
 while time.monotonic()<end:
  result=fn()
  if time.monotonic()>=end:break
  if result:return result
  time.sleep(min(2,max(0,end-time.monotonic())))
 raise ValueError('bounded wait expired')

def helper_state(i,h,uid):
 p=get('pod',h['pod']['metadata']['name'],namespace(i))
 if p['metadata']['uid']!=uid:raise ValueError('helper replaced')
 if p['metadata'].get('deletionTimestamp') or p.get('status',{}).get('phase') in ('Failed','Succeeded'):raise ValueError('helper terminal before release')
 return p

def execute(i):
 """Explicit future operator action; never invoked by default or offline tests."""
 validate(i);h=plan(i);created=None;binding=None;volume_uid=None
 cluster=get('namespace','kube-system');pvc=get('pvc',i['claim'],namespace(i))
 pending_guard(i,cluster,pvc,get('pods',namespace=namespace(i))['items'])
 try:
  # Create-only. No adoption or empty apply over existing objects.
  for key in ('configMap','inputs','gate'):kube('create','-f','-','-o','json',body=h[key])
  release_deadline=time.monotonic()+180
  created=kube('create','-f','-','-o','json',body=h['pod'])
  def bound():
   helper_state(i,h,created['metadata']['uid'])
   p=get('pvc',i['claim'],namespace(i))
   return p if p['status']['phase']=='Bound' else None
  pvc=wait_for(bound,90,release_deadline);pv=get('pv',pvc['spec']['volumeName']);handle=pv['spec']['csi']['volumeHandle']
  binding=dict(i,pv=pv['metadata']['name'],pvUID=pv['metadata']['uid'],volumeHandle=handle)
  def healthy():
   helper_state(i,h,created['metadata']['uid'])
   v=get('volumes.longhorn.io',handle,'longhorn-system')
   return v if v['status']['state']=='attached' and v['status']['robustness']=='healthy' else None
  volume=wait_for(healthy,30,release_deadline);volume_uid=volume['metadata']['uid']
  engines=get('engines.longhorn.io',namespace='longhorn-system')['items'];engines=[e for e in engines if e['spec'].get('volumeName')==handle and e['spec'].get('active')]
  if volume['spec'].get('nodeID')!=i['node']:raise ValueError('volume attachment node')
  if volume['spec']['numberOfReplicas']!=2 or len(engines)!=1 or list(engines[0]['status'].get('replicaModeMap',{}).values()).count('RW')!=2:raise ValueError('two healthy replica proof')
  def running():
   p=helper_state(i,h,created['metadata']['uid'])
   return p if p.get('status',{}).get('phase')=='Running' else None
  helper=wait_for(running,remaining(release_deadline),release_deadline)
  release=release_patch(i,get('namespace','kube-system'),get('pvc',i['claim'],namespace(i)),get('pv',binding['pv']),get('pods',namespace=namespace(i))['items'],helper,get('cm',h['gate']['metadata']['name'],namespace(i)))
  remaining(release_deadline) # No late release after slow metadata reads.
  kube('patch','cm',h['gate']['metadata']['name'],'-n',namespace(i),'--type=json','-p',json.dumps(release['patch']),'-o','json')
  def finished():
   p=get('pod',h['pod']['metadata']['name'],namespace(i))
   if p['metadata']['uid']!=created['metadata']['uid']:raise ValueError('helper replaced')
   if p['status']['phase']=='Failed':raise ValueError('initializer failed')
   return p if p['status']['phase']=='Succeeded' else None
  wait_for(finished,90)
  output=subprocess.check_output(['kubectl','logs','-n',namespace(i),h['pod']['metadata']['name'],'-c','initialize','--limit-bytes=2048'],timeout=15)
  r=json.loads(output)
  if r!={'schemaVersion':1,'owner':1001,'group':1001,'mode':'0700','path':'private','markerSHA256':hashlib.sha256(b'perkforge-private-receipt-initialization-v1\n').hexdigest(),'markerRemoved':True}:raise ValueError('initializer readback')
 finally:
  if created is not None:
   kube('delete','--raw','/api/v1/namespaces/'+namespace(i)+'/pods/'+h['pod']['metadata']['name'],'-f','-',body={'apiVersion':'v1','kind':'DeleteOptions','preconditions':{'uid':created['metadata']['uid']}})
   wait_for(lambda:not any(p['metadata'].get('uid')==created['metadata']['uid'] for p in get('pods',namespace=namespace(i))['items']),90)
   if binding is None:
    p=get('pvc',i['claim'],namespace(i))
    if p.get('spec',{}).get('volumeName'):
     pv=get('pv',p['spec']['volumeName']);binding=dict(i,pv=pv['metadata']['name'],pvUID=pv['metadata']['uid'],volumeHandle=pv['spec']['csi']['volumeHandle'])
   if binding is not None:
    def detached():
     v=get('volumes.longhorn.io',binding['volumeHandle'],'longhorn-system')
     if volume_uid is not None and v['metadata']['uid']!=volume_uid:raise ValueError('Longhorn replaced')
     return v if v['status']['state']=='detached' else None
    v=wait_for(detached,90)
    cleanup_proof(binding,get('namespace','kube-system'),get('pvc',i['claim'],namespace(i)),get('pv',binding['pv']),get('pods',namespace=namespace(i))['items'],get('volumeattachments')['items'],v)
   else:pending_guard(i,get('namespace','kube-system'),get('pvc',i['claim'],namespace(i)),get('pods',namespace=namespace(i))['items'])
 return {'initialized':True,'boundInputs':binding,'helperRemoved':True,'detached':True}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=pathlib.Path);g=p.add_mutually_exclusive_group();g.add_argument('--render',action='store_true');g.add_argument('--execute',action='store_true');a=p.parse_args()
 if not (a.render or a.execute):print('INERT: no API operations.');raise SystemExit(0)
 i=json.loads(a.inputs.read_text())
 print(json.dumps(execute(i) if a.execute else plan(i),indent=2))
