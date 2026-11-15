#!/usr/bin/env python3
"""Fixed-path, nonroot fresh-volume initialization. Never adopts existing private state."""
import hashlib,json,os,stat,sys,time

def initialize(root='/volume'):
 if os.geteuid()!=1001 or os.getegid()!=1001:raise ValueError('expected UID/GID1001')
 flags=os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW
 fd=os.open(root,flags); child=None;marker=False
 try:
  rootstat=os.fstat(fd)
  if rootstat.st_gid!=1001 or (stat.S_IMODE(rootstat.st_mode)&0o2070)!=0o2070:raise ValueError('fsGroup root mismatch')
  names=os.listdir(fd)
  if set(names)-{'lost+found'}:raise ValueError('foreign volume contents')
  if 'lost+found' in names:
   lf=os.open('lost+found',flags,dir_fd=fd)
   try:
    if os.listdir(lf):raise ValueError('nonempty lost+found')
   finally:os.close(lf)
  os.mkdir('private',0o700,dir_fd=fd)
  child=os.open('private',flags,dir_fd=fd)
  # Only this exclusively created child: remove inherited setgid, never root/foreign state.
  os.fchmod(child,0o700);s=os.fstat(child)
  if (s.st_uid,s.st_gid,stat.S_IMODE(s.st_mode))!=(1001,1001,0o700):raise ValueError('private ownership mismatch')
  data=b'perkforge-private-receipt-initialization-v1\n'
  m=os.open('.initialization-check',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600,dir_fd=child);marker=True
  try:
   if os.write(m,data)!=len(data):raise ValueError('short write')
   os.fsync(m)
  finally:os.close(m)
  m=os.open('.initialization-check',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=child)
  try:
   st=os.fstat(m)
   if not stat.S_ISREG(st.st_mode) or st.st_size!=len(data) or os.read(m,len(data)+1)!=data:raise ValueError('marker verification')
  finally:os.close(m)
  os.unlink('.initialization-check',dir_fd=child);marker=False;os.fsync(child);os.fsync(fd)
  if os.listdir(child):raise ValueError('unexpected private contents')
  return {'schemaVersion':1,'owner':1001,'group':1001,'mode':'0700','path':'private','markerSHA256':hashlib.sha256(data).hexdigest(),'markerRemoved':True}
 finally:
  if marker and child is not None:os.unlink('.initialization-check',dir_fd=child)
  if child is not None:os.close(child)
  os.close(fd)
def bounded_projection(path,cap=4096):
 # Kubelet projections legitimately contain symlinks; target must remain within
 # the fixed mount. Read and validate exact bytes from one bounded regular fd.
 resolved=os.path.realpath(path);root=os.path.dirname(path)
 if not resolved.startswith(root+'/'):raise ValueError('projection escape')
 f=os.open(resolved,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK)
 try:
  st=os.fstat(f)
  if not stat.S_ISREG(st.st_mode) or st.st_size>cap:raise ValueError('projection type/size')
  b=os.read(f,cap+1)
  if len(b)>cap:raise ValueError('projection size')
  return b
 finally:os.close(f)

def await_gate():
 inputs=json.loads(bounded_projection('/inputs/initialization.json'))
 poduid=bounded_projection('/identity/poduid').decode().strip()
 deadline=time.monotonic()+180
 while time.monotonic()<deadline:
  try:b=bounded_projection('/gate/approval.json')
  except FileNotFoundError:time.sleep(1);continue
  g=json.loads(b)
  if set(g)!={'schemaVersion','claimUID','helperUID','pvUID','volumeHandle','sourceSHA256'} or g['schemaVersion']!=1 or g['claimUID']!=inputs['claimUID'] or g['helperUID']!=poduid or g['sourceSHA256']!=inputs['sourceSHA256']:raise ValueError('gate identity')
  if not all(isinstance(g[k],str) and g[k] for k in ('pvUID','volumeHandle')):raise ValueError('gate binding')
  return
 raise ValueError('binding approval deadline')

if __name__=='__main__':
 try:
  if len(sys.argv)!=1:raise ValueError('no path override')
  await_gate()
  print(json.dumps(initialize(),sort_keys=True))
 except Exception:
  print('Private receipt initialization failed closed; retain claim for inspection.',file=sys.stderr);sys.exit(1)
