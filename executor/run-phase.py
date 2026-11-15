#!/usr/bin/env python3
"""Finite native launcher; fixed mounts, literal schemas, isolated credential sets."""
import argparse,datetime,fcntl,hashlib,importlib.util,json,os,pathlib,shutil,stat,subprocess,sys,tempfile
BASE=pathlib.Path('/opt/platform/big-bang-bootstrap/configuration/packages/gitlab/enrollment')
sys.path.insert(0,str(BASE/'phases'));import contract
sys.path.insert(0,str(BASE));import verify_group_paths as guard
from pathlib import Path

def bounded(p,n):
 fd=os.open(p,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
 try:
  s=os.fstat(fd)
  if not stat.S_ISREG(s.st_mode) or s.st_size>n:raise ValueError('file')
  with os.fdopen(fd,'rb',closefd=False) as f:b=f.read(n+1)
  if len(b)>n:raise ValueError('size')
  return b
 finally:os.close(fd)
def projection(root,name,n):
 r=Path(root)
 if r.is_symlink() or not r.is_dir():raise ValueError('mount')
 p=(r/name).resolve(strict=True)
 if not p.is_relative_to(r) or p==r:raise ValueError('escape')
 return bounded(p,n)
def write(p,b):
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def atomic(p,d):
 fd,tmp=tempfile.mkstemp(prefix='.result-',dir=p.parent)
 try:
  with os.fdopen(fd,'w') as f:json.dump(d,f,sort_keys=True);f.flush();os.fsync(f.fileno())
  os.replace(tmp,p)
 finally:
  if os.path.exists(tmp):os.unlink(tmp)
def run(a):
 raw=projection('/inputs','inputs.json',262144)
 if hashlib.sha256(raw).hexdigest()!=a.inputs_sha256:raise ValueError('input hash')
 body=json.loads(raw,object_pairs_hook=contract.unique)
 if not isinstance(body,dict) or set(body)!=({'identity','group'} if a.phase=='foundation' else {'identity'}):raise ValueError('wrapper fields')
 w=Path(tempfile.mkdtemp(prefix='phase-',dir='/tmp'));os.chmod(w,0o700)
 lock=None
 try:
  write(w/'phase-inputs.json',json.dumps(body['identity']).encode())
  d=contract.inputs(str(w/'phase-inputs.json'),'attest' if a.phase=='foundation' else a.phase)
  revisions=json.loads(projection('/opt','revisions.json',4096))
  if revisions!={'enrollment':d['identity_source_revision'],'platform':d['identity_platform_revision']} or d['identity_invocation']!=a.invocation:raise ValueError('source/attempt')
  if a.phase=='foundation':
   write(w/'group-inputs.json',json.dumps(body['group']).encode());g=guard.validate_inputs(str(w/'group-inputs.json'))
   if g['gitlab_group_context']!=d['identity_context'] or g['gitlab_group_source_revision']!=d['identity_source_revision'] or g['gitlab_native_origin']!=d['identity_gitlab_origin'] or g['gitlab_native_ca_file']!='/credentials/lab-ca.crt' or g['gitlab_group_run'] is not True or g.get('gitlab_group_allow_parent_create',False) is not False or type(g.get('gitlab_group_expected_parent_id')) is not int or g['gitlab_group_expected_parent_id']<=0:raise ValueError('group binding')
  names=['gitlab-reader','kc-client-id','kc-client-secret','lab-ca.crt'] if a.phase=='attest' else ['group-writer','lab-ca.crt']
  for n in names:write(w/n,projection('/credentials',n,262144 if n.endswith('.crt') else 4096))
  if a.phase=='attest':
   write(w/'api-token',projection('/identity-api','token',4096));write(w/'api-ca.crt',projection('/identity-api','ca.crt',262144))
   subprocess.run([str(BASE/'phases/run-attestor.sh'),'--apply',str(w/'phase-inputs.json'),str(w)],check=True)
   return
  root=Path('/receipts');s=root.lstat()
  if not stat.S_ISDIR(s.st_mode) or s.st_uid!=os.getuid() or stat.S_IMODE(s.st_mode)!=0o700:raise ValueError('receipt root')
  context=root/d['identity_context'];context.mkdir(mode=0o700,exist_ok=True);group=context/'gitlab-group.json'
  guard.verify(str(w/'group-writer'),str(context/'trigger'),prepare=True)
  lock=os.open(context/'trigger.lock',os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  os.environ['PERKFORGE_PHASE_LOCK_OWNER']=str(os.getpid());os.environ['PERKFORGE_GROUP_LOCK_OWNER']=str(os.getpid())
  subprocess.run(['python3',str(BASE/'phases/phase-lock.py'),'--locked',str(w),str(group)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  if a.phase=='memberships':
   subprocess.run(['/opt/perkforge/bin/refresh-identity-evidence',str(w/'phase-inputs.json'),str(w)],check=True)
   subprocess.run([str(BASE/'phases/run-memberships.sh'),'--apply',str(w/'phase-inputs.json'),str(w),str(group)],check=True);return
  result=context/'foundation-result.json'
  if os.path.lexists(result):
   old=contract.read(str(result))
   keys={'schema','phase','context','invocation','source_revision','platform_revision','parent_id','group_id','captured_at'}
   if set(old)!=keys or old['schema']!=1 or old['phase']!='GroupReady' or old['context']!=d['identity_context'] or old['invocation'] not in {d['identity_invocation'],d['identity_previous_invocation']}:raise ValueError('prior attempt')
  g['gitlab_native_ca_file']=str(w/'lab-ca.crt');(w/'group-inputs.json').unlink();write(w/'group-inputs.json',json.dumps(g).encode())
  cmd=[str(BASE/'run-groups.sh'),'--apply',str(w/'group-writer'),str(group),str(w/'group-inputs.json')]
  p=subprocess.run(cmd,capture_output=True,timeout=240)
  if p.returncode:raise ValueError('foundation failed')
  cmd[1]='--validate';subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  actual=contract.read(str(group))
  if actual['stage']!='group-ready' or actual['context']!=d['identity_context'] or actual['source_revision']!=d['identity_source_revision'] or actual['parent_id']!=g['gitlab_group_expected_parent_id'] or type(actual['group_id']) is not int or actual['group_id']<=0:raise ValueError('readback')
  atomic(result,{'schema':1,'phase':'GroupReady','context':d['identity_context'],'invocation':d['identity_invocation'],'source_revision':d['identity_source_revision'],'platform_revision':d['identity_platform_revision'],'parent_id':actual['parent_id'],'group_id':actual['group_id'],'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
  print('GroupReady; membership not yet evaluated.')
 finally:
  if lock is not None:os.close(lock)
  shutil.rmtree(w)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--phase',choices=['foundation','attest','memberships'],required=True);p.add_argument('--invocation',required=True);p.add_argument('--inputs-sha256',required=True);a=p.parse_args()
 try:run(a)
 except Exception:raise SystemExit('Finite identity phase rejected or failed; no completion claim.')
