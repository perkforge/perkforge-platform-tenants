"""Offline opt-in receipt reader plan. No Kubernetes operations or file restoration."""
import copy,json,pathlib,re
from finite_identity import render,digest,IMAGE
from identity_context_binding import selection
from private_receipts import validate,BUDGET

def build(d,i):
 generated=render(d);validate(i);b=selection(d)
 if (i['claim'],i['node'],i['pullSecret'])!=(d['receiptClaim'],d['workerNode'],d['pullSecret']):raise ValueError('receipt target mismatch')
 from private_receipts import selected
 if selected(i)!=b:raise ValueError('receipt context mismatch')
 group=d['phaseInputs']['foundation']['group']
 expected={'context':d['context'],'invocation':d['invocation'],'source_revision':d['enrollmentRevision'],'platform_revision':d['platformRevision'],'parent_id':group['gitlab_group_expected_parent_id'],'origin':group['gitlab_native_origin'],'claim_uid':i['claimUID'],'cluster_uid':i['clusterUID']}
 script=(pathlib.Path(__file__).resolve().parents[1]/'executor/read-original-receipts.py').read_text()
 p={'serviceAccountName':generated['foundation/job.yaml']['spec']['template']['spec']['serviceAccountName'],'automountServiceAccountToken':False,'nodeSelector':{'kubernetes.io/hostname':i['node']},'restartPolicy':'Never','activeDeadlineSeconds':60,'imagePullSecrets':[{'name':i['pullSecret']}],'securityContext':{'runAsUser':1001,'runAsGroup':1001,'runAsNonRoot':True,'seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'read-original-receipts','image':IMAGE,'command':['/home/python/python-env/bin/python3','-B','-c',script,json.dumps(expected,sort_keys=True,separators=(',',':'))],'args':[],'resources':copy.deepcopy(BUDGET),'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'volumeMounts':[{'name':'receipts','mountPath':'/original-receipts','subPath':'private/'+d['context'],'readOnly':True},{'name':'identity','mountPath':'/reader-identity','readOnly':True}]}],'volumes':[{'name':'receipts','persistentVolumeClaim':{'claimName':i['claim'],'readOnly':True}},{'name':'identity','downwardAPI':{'items':[{'path':'uid','fieldRef':{'fieldPath':'metadata.uid'}}]}}]}
 sha=digest({'spec':p,'operator':i['operatorUser']})
 return {'apiVersion':'v1','kind':'Pod','metadata':{'name':'identity-receipt-export-'+sha[:16],'namespace':b['writer_namespace'],'labels':{'platform.perkforge.io/owner':'identity-receipt-export-v1'},'annotations':{'platform.perkforge.io/receipt-export-sha256':sha}},'spec':p}

def clause(d,i):
 from identity_foundation import pod_checks,cel
 h=build(d,i);checks=pod_checks(h['spec'],'object.spec')
 checks=[x for x in checks if x not in ('object.spec.securityContext.fsGroup == 1001','object.spec.securityContext.fsGroupChangePolicy == "OnRootMismatch"','!has(object.spec.tolerations)')]
 checks += ['!has(object.spec.securityContext.fsGroup)','!has(object.spec.securityContext.fsGroupChangePolicy)','request.userInfo.username == '+cel(i['operatorUser']),'object.metadata.name == '+cel(h['metadata']['name']),'object.metadata.annotations == '+cel(h['metadata']['annotations']),'object.metadata.labels == '+cel(h['metadata']['labels']),'!has(object.metadata.ownerReferences)','!has(object.metadata.finalizers)','!has(object.metadata.generateName)','object.spec.activeDeadlineSeconds == 60','(!has(object.spec.tolerations) || (object.spec.tolerations.size() <= 2 && object.spec.tolerations.all(t, t.key in ["node.kubernetes.io/not-ready","node.kubernetes.io/unreachable"] && t.operator == "Exists" && t.effect == "NoExecute" && t.tolerationSeconds == 300)))']
 return '('+' && '.join(checks)+')'

def verify_transport(raw,pod_uid,expected):
 """Return original bytes only; caller owns private exclusive local persistence."""
 import base64,hashlib
 if not isinstance(raw,bytes) or len(raw)>16384:raise ValueError('transport bound')
 def unique(pairs):
  out={}
  for k,v in pairs:
   if k in out:raise ValueError('duplicate transport key')
   out[k]=v
  return out
 e=json.loads(raw,object_pairs_hook=unique)
 if set(e)!={'schemaVersion','podUID','selection','files'} or e['schemaVersion']!=1 or e['podUID']!=pod_uid or e['selection']!=expected:raise ValueError('transport binding')
 if set(e['files'])!={'gitlab-group.json','foundation-result.json'}:raise ValueError('transport files')
 out={}
 for n,v in e['files'].items():
  if set(v)!={'bytes','sha256','base64'} or type(v['bytes']) is not int or not 0<v['bytes']<=4096:raise ValueError('transport file shape')
  b=base64.b64decode(v['base64'],validate=True)
  if len(b)!=v['bytes'] or hashlib.sha256(b).hexdigest()!=v['sha256']:raise ValueError('transport integrity')
  out[n]=b
 return out
