#!/usr/bin/env python3
"""Offline minimal immutable ConfigMap source bundle; exact clean commit inputs only."""
import argparse,base64,hashlib,json,pathlib,subprocess
from identity_context_binding import derive,CONTRACT_BYTES
ROOT=pathlib.Path(__file__).resolve().parents[1]
PREFIX='big-bang-bootstrap/configuration/packages/gitlab/'
PLATFORM=['enrollment/'+x for x in ('run-groups.sh','verify_group_paths.py','ensure-groups.yaml','ensure-one-group.yaml','read-keycloak-context.py','resolve-subject.py')]+['enrollment/phases/'+x for x in ('contract.py','paths.py','phase-lock.py','membership-state.py','run-attestor.sh','run-memberships.sh','attest.yaml','attest-one.yaml','publish.yaml','memberships.yaml','member-one.yaml')]+['run-membership.sh','reconcile-membership.yaml','verification/membership_inputs.py']
EXECUTOR=('launch','run-phase.py','refresh-identity-evidence')
def source(repo,revision,path):
 mode=subprocess.check_output(['git','-C',str(repo),'ls-tree',revision,'--',path],text=True).split()[0]
 if mode not in ('100644','100755'):raise ValueError('not regular tracked source')
 b=subprocess.check_output(['git','-C',str(repo),'show',revision+':'+path])
 if len(b)>262144:raise ValueError('oversized source')
 return b

def bundle(enrollment,er,platform,pr,context="portal"):
 binding=derive(context)
 for repo,rev in ((enrollment,er),(platform,pr)):
  if subprocess.check_output(['git','-C',str(repo),'rev-parse',rev],text=True).strip()!=rev:raise ValueError('exact commit required')
 data={'perkforge/bin/'+x:source(enrollment,er,'executor/'+x) for x in EXECUTOR}
 data.update({'platform/'+PREFIX+x:source(platform,pr,PREFIX+x) for x in PLATFORM})
 abi=PREFIX+'enrollment/identity_context.py'
 present=subprocess.check_output(['git','-C',str(platform),'ls-tree',pr,'--',abi],text=True).strip()
 if present:
  b=source(platform,pr,abi)
  if b!=CONTRACT_BYTES:raise ValueError('platform context ABI differs from reviewed vendored contract')
  data['platform/'+abi]=b
 elif context!='portal':raise ValueError('alternate context requires reviewed ABI in pinned platform source')
 ctx='big-bang-bootstrap/configuration/authorization/contexts/'+context+'.yaml';data['platform/'+ctx]=source(platform,pr,ctx)
 data['revisions.json']=json.dumps({'enrollment':er,'platform':pr},sort_keys=True).encode()
 manifest=''.join(hashlib.sha256(b).hexdigest()+'  '+p+'\n' for p,b in sorted(data.items())).encode();sha=hashlib.sha256(manifest).hexdigest();data['provenance.sha256']=manifest
 keys={p:'file-'+str(i) for i,p in enumerate(sorted(data))};encoded={keys[p]:b.decode('utf-8') for p,b in data.items()}
 if sum(len(x) for x in encoded.values())>786432:raise ValueError('bounded ConfigMap payload')
 cms=[{'apiVersion':'v1','kind':'ConfigMap','metadata':{'name':'identity-source-'+sha[:20],'namespace':ns},'immutable':True,'data':encoded} for ns in (binding['writer_namespace'],binding['attestor_namespace'])]
 return {'sha256':sha,'items':[{'key':keys[p],'path':p} for p in sorted(data)],'configMaps':cms}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--enrollment',type=pathlib.Path,default=ROOT);p.add_argument('--enrollment-revision',required=True);p.add_argument('--platform',type=pathlib.Path,required=True);p.add_argument('--platform-revision',required=True);p.add_argument('--context',default='portal');p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
 b=bundle(a.enrollment,a.enrollment_revision,a.platform,a.platform_revision,a.context)
 with a.output.open('x') as f:json.dump(b,f,sort_keys=True,indent=2)
