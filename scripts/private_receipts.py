#!/usr/bin/env python3
"""Offline exact helper plan and read-only runtime identity gate. No apply/delete API."""
import argparse,hashlib,json,pathlib,re,copy,subprocess,time
from finite_identity import IMAGE
from identity_target_profile import storage,initializer_identity
NS='tenant-identity-writer'
BUDGET={'requests':{'cpu':'100m','memory':'256Mi'},'limits':{'cpu':'500m','memory':'512Mi'}}
def validate(i):
 if set(i)!={'storageProfile','clusterUID','claim','claimUID','pv','pvUID','volumeHandle','node','pullSecret','operatorUser'}:raise ValueError('exact inputs')
 storage(i['storageProfile'])
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
 if (m['name'],m['namespace'],m['uid'])!=(i['claim'],NS,i['claimUID']) or m.get('deletionTimestamp'):raise ValueError('claim identity')
 if m.get('labels',{}).get('platform.perkforge.io/owner')!='tenant-identity-foundation-v1':raise ValueError('claim owner')
 if pvc['status']['phase']!='Bound' or s['volumeName']!=i['pv'] or s['storageClassName']!=i['storageProfile']['className'] or s['accessModes']!=['ReadWriteOnce'] or s['resources']['requests']['storage']!=i['storageProfile']['size']:raise ValueError('claim spec')
 if pv['metadata']['name']!=i['pv'] or pv['metadata']['uid']!=i['pvUID'] or pv['metadata'].get('deletionTimestamp'):raise ValueError('PV identity')
 p=pv['spec'];r=p['claimRef'];c=p['csi']
 if (r['name'],r['namespace'],r['uid'])!=(i['claim'],NS,i['claimUID']) or c['driver']!='driver.longhorn.io' or c['volumeHandle']!=i['volumeHandle'] or p['persistentVolumeReclaimPolicy']!='Retain':raise ValueError('PV binding')
 for pod in pods:
  if helper_uid is not None and pod['metadata'].get('uid')==helper_uid:continue
  if pod['metadata']['namespace']==NS and any(v.get('persistentVolumeClaim',{}).get('claimName')==i['claim'] for v in pod['spec'].get('volumes',[])):raise ValueError('PVC consumer exists, including completed/terminating helpers')
 return True

def pending_guard(i,cluster,pvc,pods):
 validate(i)
 m=pvc['metadata'];s=pvc['spec']
 if s.get('volumeMode','Filesystem')!='Filesystem' or s.get('dataSource') is not None or s.get('dataSourceRef') is not None:raise ValueError('fresh filesystem only')
 if cluster['metadata']['uid']!=i['clusterUID'] or (m['name'],m['namespace'],m['uid'])!=(i['claim'],NS,i['claimUID']):raise ValueError('prebind identity')
 if m.get('deletionTimestamp') or m.get('labels',{}).get('platform.perkforge.io/owner')!='tenant-identity-foundation-v1':raise ValueError('prebind ownership')
 if pvc['status']['phase'] not in ('Pending','Bound') or s['storageClassName']!=i['storageProfile']['className'] or s['accessModes']!=['ReadWriteOnce'] or s['resources']['requests']['storage']!=i['storageProfile']['size']:raise ValueError('prebind spec')
 if any(p['metadata']['namespace']==NS and any(v.get('persistentVolumeClaim',{}).get('claimName')==i['claim'] for v in p['spec'].get('volumes',[])) for p in pods):raise ValueError('prebind consumer')
 return True

def release_patch(i,cluster,pvc,pv,pods,helper,gate):
 # Caller supplies fresh metadata, never credentials. This only emits a CAS patch.
 h=plan(i);m=helper['metadata'];uid=m['uid']
 if (m['name'],m['namespace'])!=(h['pod']['metadata']['name'],NS) or m.get('annotations')!=h['pod']['metadata']['annotations'] or m.get('labels')!=h['pod']['metadata']['labels'] or m.get('deletionTimestamp'):raise ValueError('helper identity')
 if helper['spec'].get('nodeName')!=i['node'] or helper['status']['phase']!='Running':raise ValueError('helper placement')
 for k in ('containers','volumes','serviceAccountName','automountServiceAccountToken','nodeSelector','securityContext','restartPolicy','activeDeadlineSeconds','imagePullSecrets'):
  # Runtime default representation must be independently reviewed before use.
  actual=copy.deepcopy(helper['spec'][k]);expected=h['pod']['spec'][k]
  if k=='containers':
   for c in actual:
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
 if gate['metadata']['name']!=h['gate']['metadata']['name'] or gate['metadata']['namespace']!=NS or gate.get('data',{})!={}:raise ValueError('gate must be fresh/empty')
 approval={'schemaVersion':1,'claimUID':i['claimUID'],'helperUID':uid,'pvUID':bound['pvUID'],'volumeHandle':bound['volumeHandle'],'sourceSHA256':h['pod']['metadata']['annotations']['platform.perkforge.io/source-sha256']}
 return {'boundInputs':bound,'patch':[{'op':'test','path':'/metadata/uid','value':gate['metadata']['uid']},{'op':'test','path':'/metadata/resourceVersion','value':gate['metadata']['resourceVersion']},{'op':'add','path':'/data','value':{'approval.json':json.dumps(approval,sort_keys=True)}}]}

def cleanup_proof(i,cluster,pvc,pv,pods,volumeattachments,longhorn):
 guard(i,cluster,pvc,pv,pods)
 if any(v['spec'].get('source',{}).get('persistentVolumeName')==i['pv'] for v in volumeattachments):raise ValueError('CSI attachment remains')
 if longhorn['metadata']['name']!=i['volumeHandle'] or longhorn['status']['state']!='detached' or longhorn['spec'].get('nodeID'):raise ValueError('volume not detached')
 return True

def plan(i):
 validate(i);script=(pathlib.Path(__file__).resolve().parents[1]/'executor/initialize-private-receipts.py').read_text();sha=hashlib.sha256(script.encode()).hexdigest();name='identity-private-init-'+hashlib.sha256(json.dumps(initializer_identity(i),sort_keys=True).encode()).hexdigest()[:16]
 cm={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':'identity-private-init-'+sha[:20],'namespace':NS},'immutable':True,'data':{'initialize.py':script}}
 pod={'apiVersion':'v1','kind':'Pod','metadata':{'name':name,'namespace':NS,'labels':{'platform.perkforge.io/owner':'identity-private-init-v1'},'annotations':{'platform.perkforge.io/claim-uid':i['claimUID'],'platform.perkforge.io/source-sha256':sha}},'spec':{'serviceAccountName':'identity-group-worker','automountServiceAccountToken':False,'nodeSelector':{'kubernetes.io/hostname':i['node']},'restartPolicy':'Never','activeDeadlineSeconds':300,'imagePullSecrets':[{'name':i['pullSecret']}],'securityContext':{'runAsUser':1001,'runAsGroup':1001,'runAsNonRoot':True,'fsGroup':1001,'fsGroupChangePolicy':'OnRootMismatch','seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'initialize','image':IMAGE,'command':['/home/python/python-env/bin/python3','-B','/source/initialize.py'],'args':[],'resources':BUDGET,'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'volumeMounts':[{'name':'receipts','mountPath':'/volume'},{'name':'source','mountPath':'/source','readOnly':True}]}],'volumes':[{'name':'receipts','persistentVolumeClaim':{'claimName':i['claim']}},{'name':'source','configMap':{'name':cm['metadata']['name']}}]}}
 inputs={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':name+'-inputs','namespace':NS},'immutable':True,'data':{'initialization.json':json.dumps({'claimUID':i['claimUID'],'sourceSHA256':sha},sort_keys=True)}}
 gate={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':name+'-gate','namespace':NS},'data':{}}
 pod['spec']['volumes'] += [{'name':'inputs','configMap':{'name':inputs['metadata']['name']}},{'name':'gate','configMap':{'name':gate['metadata']['name']}},{'name':'identity','downwardAPI':{'items':[{'path':'poduid','fieldRef':{'fieldPath':'metadata.uid'}}]}}]
 pod['spec']['containers'][0]['volumeMounts'] += [{'name':'inputs','mountPath':'/inputs','readOnly':True},{'name':'gate','mountPath':'/gate','readOnly':True},{'name':'identity','mountPath':'/identity','readOnly':True}]
 return {'configMap':cm,'inputs':inputs,'gate':gate,'pod':pod}

def kube(*args,body=None):
 return json.loads(subprocess.check_output(['kubectl',*args],input=json.dumps(body).encode() if body is not None else None,timeout=30))
def get(kind,name=None,namespace=None):
 args=['get',kind]+([name] if name else [])+(['-n',namespace] if namespace else [])+['-o','json']
 return kube(*args)
def wait_for(fn,seconds):
 end=time.monotonic()+seconds
 while time.monotonic()<end:
  result=fn()
  if result:return result
  time.sleep(2)
 raise ValueError('bounded wait expired')
def execute(i):
 """Explicit future operator action; never invoked by default or offline tests."""
 validate(i);h=plan(i);created=None;binding=None;volume_uid=None
 cluster=get('namespace','kube-system');pvc=get('pvc',i['claim'],NS)
 pending_guard(i,cluster,pvc,get('pods',namespace=NS)['items'])
 try:
  # Create-only. No adoption or empty apply over existing objects.
  for key in ('configMap','inputs','gate'):kube('create','-f','-','-o','json',body=h[key])
  created=kube('create','-f','-','-o','json',body=h['pod'])
  def bound():
   p=get('pvc',i['claim'],NS)
   return p if p['status']['phase']=='Bound' else None
  pvc=wait_for(bound,90);pv=get('pv',pvc['spec']['volumeName']);handle=pv['spec']['csi']['volumeHandle']
  binding=dict(i,pv=pv['metadata']['name'],pvUID=pv['metadata']['uid'],volumeHandle=handle)
  def healthy():
   v=get('volumes.longhorn.io',handle,'longhorn-system')
   return v if v['status']['state']=='attached' and v['status']['robustness']=='healthy' else None
  volume=wait_for(healthy,30);volume_uid=volume['metadata']['uid']
  engines=get('engines.longhorn.io',namespace='longhorn-system')['items'];engines=[e for e in engines if e['spec'].get('volumeName')==handle and e['spec'].get('active')]
  if volume['spec'].get('nodeID')!=i['node']:raise ValueError('volume attachment node')
  if volume['spec']['numberOfReplicas']!=2 or len(engines)!=1 or list(engines[0]['status'].get('replicaModeMap',{}).values()).count('RW')!=2:raise ValueError('two healthy replica proof')
  helper=get('pod',h['pod']['metadata']['name'],NS)
  if helper['metadata']['uid']!=created['metadata']['uid']:raise ValueError('helper replaced')
  release=release_patch(i,get('namespace','kube-system'),get('pvc',i['claim'],NS),get('pv',binding['pv']),get('pods',namespace=NS)['items'],helper,get('cm',h['gate']['metadata']['name'],NS))
  kube('patch','cm',h['gate']['metadata']['name'],'-n',NS,'--type=json','-p',json.dumps(release['patch']),'-o','json')
  def finished():
   p=get('pod',h['pod']['metadata']['name'],NS)
   if p['metadata']['uid']!=created['metadata']['uid']:raise ValueError('helper replaced')
   if p['status']['phase']=='Failed':raise ValueError('initializer failed')
   return p if p['status']['phase']=='Succeeded' else None
  wait_for(finished,90)
  output=subprocess.check_output(['kubectl','logs','-n',NS,h['pod']['metadata']['name'],'-c','initialize','--limit-bytes=2048'],timeout=15)
  r=json.loads(output)
  if r!={'schemaVersion':1,'owner':1001,'group':1001,'mode':'0700','path':'private','markerSHA256':hashlib.sha256(b'perkforge-private-receipt-initialization-v1\n').hexdigest(),'markerRemoved':True}:raise ValueError('initializer readback')
 finally:
  if created is not None:
   kube('delete','--raw','/api/v1/namespaces/'+NS+'/pods/'+h['pod']['metadata']['name'],'-f','-',body={'apiVersion':'v1','kind':'DeleteOptions','preconditions':{'uid':created['metadata']['uid']}})
   wait_for(lambda:not any(p['metadata'].get('uid')==created['metadata']['uid'] for p in get('pods',namespace=NS)['items']),90)
   if binding is None:
    p=get('pvc',i['claim'],NS)
    if p.get('spec',{}).get('volumeName'):
     pv=get('pv',p['spec']['volumeName']);binding=dict(i,pv=pv['metadata']['name'],pvUID=pv['metadata']['uid'],volumeHandle=pv['spec']['csi']['volumeHandle'])
   if binding is not None:
    def detached():
     v=get('volumes.longhorn.io',binding['volumeHandle'],'longhorn-system')
     if volume_uid is not None and v['metadata']['uid']!=volume_uid:raise ValueError('Longhorn replaced')
     return v if v['status']['state']=='detached' else None
    v=wait_for(detached,90)
    cleanup_proof(binding,get('namespace','kube-system'),get('pvc',i['claim'],NS),get('pv',binding['pv']),get('pods',namespace=NS)['items'],get('volumeattachments')['items'],v)
   else:pending_guard(i,get('namespace','kube-system'),get('pvc',i['claim'],NS),get('pods',namespace=NS)['items'])
 return {'initialized':True,'boundInputs':binding,'helperRemoved':True,'detached':True}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--inputs',type=pathlib.Path);g=p.add_mutually_exclusive_group();g.add_argument('--render',action='store_true');g.add_argument('--execute',action='store_true');a=p.parse_args()
 if not (a.render or a.execute):print('INERT: no API operations.');raise SystemExit(0)
 i=json.loads(a.inputs.read_text())
 print(json.dumps(execute(i) if a.execute else plan(i),indent=2))
