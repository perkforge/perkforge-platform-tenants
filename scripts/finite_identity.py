#!/usr/bin/env python3
"""Deterministic declared identity -> native finite Flux jobs. No API/credential access."""
import argparse,base64,hashlib,json,pathlib,re,sys
import yaml
from identity_context_binding import selection,CONTRACT_BYTES
from identity_target_profile import validate as target_profile,attempt_input
ROOT=pathlib.Path(__file__).resolve().parents[1]
IMAGE='registry1.dso.mil/ironbank/opensource/ansible/ansible@sha256:3308322cc09f20a813c00e9087c166a3d97dbb7789c059f1020f3c0b092fdf02'
PHASES=('foundation','attest','memberships')
def digest(d):return hashlib.sha256(json.dumps(d,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def match(v,p):
 if not isinstance(v,str) or not re.fullmatch(p,v):raise ValueError('invalid literal')
 return v
def unique(p):
 d={}
 for k,v in p:
  if k in d:raise ValueError('duplicate key')
  d[k]=v
 return d
def render(d):
 if isinstance(d,dict) and set(d)=={'schemaVersion','context','enabled'} and d['schemaVersion']==1 and d['enabled'] is False:
  selection(d);return {'kustomization.yaml':{'apiVersion':'kustomize.config.k8s.io/v1beta1','kind':'Kustomization','resources':[]}}
 required={'targetProfile','schemaVersion','context','enabled','foundationApproved','membershipReleased','sourceName','sourcePath','enrollmentRevision','platformRevision','invocation','retryGeneration','image','sourceBundleName','sourceBundleSHA256','sourceBundle','sourceItems','workerNode','receiptClaim','writerSecret','attestorSecret','pullSecret','resources','phaseInputs'}
 if 'contextDigest' in d:required.add('contextDigest')
 binding=selection(d)
 if set(d)!=required or d['schemaVersion']!=1 or d['enabled'] is not True or d['foundationApproved'] is not True:raise ValueError('explicit approved context declaration required')
 if type(d['membershipReleased']) is not bool:raise ValueError('explicit membership release gate')
 profile=target_profile(d['targetProfile'])
 if d['image']!=IMAGE:raise ValueError('unverified image')
 for k in ('enrollmentRevision','platformRevision'):match(d[k],r'[0-9a-f]{40}')
 for k in ('invocation','sourceBundleSHA256'):match(d[k],r'[0-9a-f]{64}')
 for k in ('sourceName','receiptClaim','writerSecret','attestorSecret','pullSecret'):match(d[k],r'[a-z][a-z0-9-]{0,62}')
 if d['sourceBundleName']!='identity-source-'+d['sourceBundleSHA256'][:20]:raise ValueError('content-addressed source required')
 items=d['sourceItems']
 if not isinstance(items,list) or not items or len(items)>64:raise ValueError('bundle items')
 seen=set()
 for item in items:
  if set(item)!={'key','path'}:raise ValueError('source item')
  match(item['key'],r'file-[0-9]+');match(item['path'],r'(?:perkforge/bin/[a-zA-Z0-9.-]+|platform/big-bang-bootstrap/configuration/[a-zA-Z0-9_./-]+|revisions.json|provenance.sha256)')
  if '..' in item['path'].split('/') or item['path'] in seen:raise ValueError('source path')
  seen.add(item['path'])
 if not {'perkforge/bin/launch','perkforge/bin/run-phase.py','perkforge/bin/refresh-identity-evidence','revisions.json','provenance.sha256'}<=seen:raise ValueError('incomplete bundle')
 bundle=d['sourceBundle']
 if set(bundle)!={'sha256','items','configMaps'} or bundle['sha256']!=d['sourceBundleSHA256'] or bundle['items']!=items or len(bundle['configMaps'])!=2:raise ValueError('bundle contract')
 for cm,namespace in zip(bundle['configMaps'],(binding['writer_namespace'],binding['attestor_namespace'])):
  if set(cm)!={'apiVersion','kind','metadata','immutable','data'} or cm['apiVersion']!='v1' or cm['kind']!='ConfigMap' or cm['immutable'] is not True or cm['metadata']!={'name':d['sourceBundleName'],'namespace':namespace}:raise ValueError('bundle scope')
  if set(cm['data'])!={x['key'] for x in items}:raise ValueError('bundle files')
  decoded={x['path']:cm['data'][x['key']].encode('utf-8') for x in items}
  if sum(map(len,decoded.values()))>524288:raise ValueError('bundle size')
  abi='platform/big-bang-bootstrap/configuration/packages/gitlab/enrollment/identity_context.py'
  if abi in decoded and decoded[abi]!=CONTRACT_BYTES:raise ValueError('foreign context ABI bytes')
  if (d['context']!='portal' or 'contextDigest' in d or any('identity_context_digest' in b.get('identity',{}) for b in d['phaseInputs'].values())) and abi not in decoded:raise ValueError('alternate context requires packaged ABI')
  manifest=decoded.pop('provenance.sha256')
  expected=''.join(hashlib.sha256(b).hexdigest()+'  '+p+'\n' for p,b in sorted(decoded.items())).encode()
  if manifest!=expected or hashlib.sha256(manifest).hexdigest()!=bundle['sha256']:raise ValueError('bundle digest')
 if bundle['configMaps'][0]['data']!=bundle['configMaps'][1]['data']:raise ValueError('different phase code')
 match(d['workerNode'],r'[a-z0-9][a-z0-9.-]{0,62}');match(d['sourcePath'],r'\./[a-zA-Z0-9/_-]+')
 if type(d['retryGeneration']) is not int or not 0<=d['retryGeneration']<=1000000:raise ValueError('retry generation')
 r=d['resources']
 if set(r)!={'requests','limits'} or any(set(r[x])!={'cpu','memory'} for x in r):raise ValueError('resources')
 for x in r:match(r[x]['cpu'],r'[1-9][0-9]*m');match(r[x]['memory'],r'[1-9][0-9]*Mi')
 if any(int(r['requests'][k].rstrip('Mi' if k=='memory' else 'm'))>int(r['limits'][k].rstrip('Mi' if k=='memory' else 'm')) for k in ('cpu','memory')):raise ValueError('resource order')
 if set(d['phaseInputs'])!=set(PHASES):raise ValueError('three explicit phase inputs')
 # Full declaration identity changes the Job name, including input bytes/placement/bundle.
 attempt=digest(attempt_input(d)); out={}; refs=[]
 for i,phase in enumerate(PHASES):
  ns=binding['attestor_namespace'] if phase=='attest' else binding['writer_namespace']
  name=binding['phase_prefix']+'-'+phase+'-'+attempt[:16]; ks=binding['phase_prefix']+'-'+phase
  body=d['phaseInputs'][phase]
  if not isinstance(body,dict) or set(body)!=({'identity','group'} if phase=='foundation' else {'identity'}):raise ValueError('literal input wrapper')
  if phase=='foundation' and body['group'] and body['group'].get('gitlab_group_context')!=d['context']:raise ValueError('foreign foundation context')
  identity=body['identity']
  if not isinstance(identity,dict):raise ValueError('identity object')
  # Native launcher is the second, strict per-phase schema/provenance gate.
  if any(identity.get(k)!=v for k,v in {'identity_context':d['context'],'identity_invocation':d['invocation'],'identity_retry_generation':d['retryGeneration'],'identity_source_revision':d['enrollmentRevision'],'identity_platform_revision':d['platformRevision'],'identity_scope':'gitlab-identity-'+('attest' if phase=='foundation' else phase)+'-v1','identity_run':True}.items()):raise ValueError('phase binding')
  if identity.get('identity_context_digest')!=binding['digest'] and not (d['context']=='portal' and 'identity_context_digest' not in identity):raise ValueError('phase context digest')
  if d['context']!='portal' and (not all(k in identity for k in ('identity_receipt_namespace','identity_receipt_name','identity_context_digest')) or 'contextDigest' not in d):raise ValueError('explicit alternate context binding')
  if identity.get('identity_receipt_namespace',binding['writer_namespace'])!=binding['writer_namespace'] or identity.get('identity_receipt_name',binding['evidence_name'])!=binding['evidence_name']:raise ValueError('foreign receipt namespace/name')
  raw=json.dumps(body,sort_keys=True,separators=(',',':')); ih=hashlib.sha256(raw.encode()).hexdigest(); cm=name+'-inputs'
  annotations={'platform.perkforge.io/invocation':d['invocation'],'platform.perkforge.io/attempt':attempt}
  volumes=[{'name':'source','configMap':{'name':d['sourceBundleName'],'defaultMode':365,'items':items}}, {'name':'inputs','configMap':{'name':cm}}, {'name':'credentials','secret':{'secretName':d['attestorSecret'] if phase=='attest' else d['writerSecret'],'defaultMode':288}}, {'name':'tmp','emptyDir':{'sizeLimit':'128Mi'}}]
  mounts=[{'name':'source','mountPath':'/opt','readOnly':True},{'name':'inputs','mountPath':'/inputs','readOnly':True},{'name':'credentials','mountPath':'/credentials','readOnly':True},{'name':'tmp','mountPath':'/tmp'}]
  if phase=='attest':
   volumes += [{'name':'api','projected':{'sources':[{'serviceAccountToken':{'path':'token','expirationSeconds':600,'audience':profile['apiAudience']}},{'configMap':{'name':'kube-root-ca.crt','items':[{'key':'ca.crt','path':'ca.crt'}]}}]}}]
   mounts += [{'name':'api','mountPath':'/identity-api','readOnly':True}]
  else:
   volumes += [{'name':'receipts','persistentVolumeClaim':{'claimName':d['receiptClaim']}}];mounts += [{'name':'receipts','mountPath':'/receipts','subPath':'private'}]
  if phase=='memberships':
   volumes += [{'name':'evidence','configMap':{'name':binding['evidence_name']}}];mounts += [{'name':'evidence','mountPath':'/identity-evidence','readOnly':True}]
  pod={'serviceAccountName':'identity-attestor' if phase=='attest' else 'identity-group-worker','automountServiceAccountToken':False,'nodeSelector':{'kubernetes.io/hostname':d['workerNode']},'restartPolicy':'Never','imagePullSecrets':[{'name':d['pullSecret']}],'securityContext':{'runAsNonRoot':True,'runAsUser':1001,'runAsGroup':1001,'fsGroup':1001,'fsGroupChangePolicy':'OnRootMismatch','seccompProfile':{'type':'RuntimeDefault'}},'containers':[{'name':'reconcile','image':IMAGE,'command':['/bin/bash','/opt/perkforge/bin/launch'],'args':['--phase',phase,'--invocation',d['invocation'],'--inputs-sha256',ih,'--bundle-sha256',d['sourceBundleSHA256']],'resources':r,'securityContext':{'allowPrivilegeEscalation':False,'readOnlyRootFilesystem':True,'capabilities':{'drop':['ALL']}},'volumeMounts':mounts}],'volumes':volumes}
  job={'apiVersion':'batch/v1','kind':'Job','metadata':{'name':name,'namespace':ns,'annotations':annotations},'spec':{'backoffLimit':0,'activeDeadlineSeconds':300,'completions':1,'parallelism':1,'template':{'metadata':{'annotations':annotations,'labels':{'platform.perkforge.io/identity-phase':'true'}},'spec':pod}}}
  out[phase+'/job.yaml']=job;out[phase+'/inputs.yaml']={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':cm,'namespace':ns},'immutable':True,'data':{'inputs.json':raw}}
  phase_resources=['inputs.yaml','job.yaml']
  if phase!='memberships':
   out[phase+'/source.yaml']=bundle['configMaps'][1 if phase=='attest' else 0];phase_resources.insert(0,'source.yaml')
  out[phase+'/kustomization.yaml']={'apiVersion':'kustomize.config.k8s.io/v1beta1','kind':'Kustomization','resources':phase_resources}
  spec={'interval':'5m','timeout':'6m','path':d['sourcePath']+'/'+phase,'sourceRef':{'kind':'GitRepository','name':d['sourceName']},'serviceAccountName':binding['attestor_reconciler'] if phase=='attest' else binding['group_reconciler'],'prune':False,'force':False,'wait':True,'commonMetadata':{'annotations':annotations},'healthChecks':[{'apiVersion':'batch/v1','kind':'Job','name':name,'namespace':ns}]}
  if phase=='memberships':spec['suspend']=not d['membershipReleased']
  if i:
   spec['dependsOn']=[{'name':binding['phase_prefix']+'-'+PHASES[i-1],'readyExpr':"dep.spec.commonMetadata.annotations['platform.perkforge.io/invocation'] == self.spec.commonMetadata.annotations['platform.perkforge.io/invocation'] && dep.spec.commonMetadata.annotations['platform.perkforge.io/attempt'] == self.spec.commonMetadata.annotations['platform.perkforge.io/attempt'] && dep.metadata.generation == dep.status.observedGeneration && dep.status.conditions.exists(e, e.type == 'Ready' && e.status == 'True')"}]
  if phase=='attest':
   ident=body['identity'];match(ident.get('identity_receipt_uid'),r'[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}')
   out['receipt-intent.yaml']={'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':binding['evidence_name'],'namespace':binding['writer_namespace'],'uid':ident['identity_receipt_uid'],'annotations':{'perkforge.dev/desired-invocation':d['invocation']}}};refs.append('receipt-intent.yaml')
  f=phase+'-reconcile.yaml';refs.append(f);out[f]={'apiVersion':'kustomize.toolkit.fluxcd.io/v1','kind':'Kustomization','metadata':{'name':ks,'namespace':'flux-system'},'spec':spec}
 out['kustomization.yaml']={'apiVersion':'kustomize.config.k8s.io/v1beta1','kind':'Kustomization','resources':refs}
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 d=json.loads((ROOT/'declarations/identity/portal.json').read_text(),object_pairs_hook=unique); files=render(d); dest=ROOT/'generated/identity/portal'
 expected={k:yaml.safe_dump(v,sort_keys=False) for k,v in files.items()}
 if a.check:
  actual={str(f.relative_to(dest)):f.read_text() for f in dest.rglob('*.yaml')}
  if actual!=expected:raise SystemExit('Stale identity output; run scripts/finite_identity.py and review generated diff.')
 else:
  existing={str(f.relative_to(dest)) for f in dest.rglob('*.yaml')}
  if existing-set(expected):raise SystemExit('Removed attempts require explicit reviewed source cleanup; refusing deletion.')
  for k,v in expected.items():
   f=dest/k;f.parent.mkdir(parents=True,exist_ok=True);f.write_text(v)
if __name__=='__main__':main()
