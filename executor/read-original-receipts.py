"""Fixed read-only original-byte transport. No credentials, API or network."""
import base64,fcntl,hashlib,json,os,re,stat,sys

def unique(pairs):
 out={}
 for k,v in pairs:
  if k in out:raise ValueError('duplicate receipt key')
  out[k]=v
 return out

def read_at(directory,name):
 fd=os.open(name,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=directory)
 try:
  s=os.fstat(fd)
  if not stat.S_ISREG(s.st_mode) or s.st_uid!=1001 or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1 or s.st_size>4096:raise ValueError('receipt file guard')
  raw=os.read(fd,4097)
  if len(raw)>4096 or len(raw)!=s.st_size:raise ValueError('receipt size')
  after=os.fstat(fd)
  if (s.st_ino,s.st_size,s.st_mtime_ns)!=(after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('receipt changed')
  return raw
 finally:os.close(fd)

def extract(expected,root='/original-receipts'):
 fd=os.open(root,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
 lock=None
 try:
  s=os.fstat(fd)
  if s.st_uid!=1001 or stat.S_IMODE(s.st_mode)!=0o700:raise ValueError('receipt directory guard')
  lock=os.open('trigger.lock',os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK,dir_fd=fd)
  s=os.fstat(lock)
  if not stat.S_ISREG(s.st_mode) or s.st_uid!=1001 or stat.S_IMODE(s.st_mode)!=0o600 or s.st_nlink!=1 or s.st_size!=0:raise ValueError('lock guard')
  fcntl.flock(lock,fcntl.LOCK_SH|fcntl.LOCK_NB)
  raw={n:read_at(fd,n) for n in ('gitlab-group.json','foundation-result.json')}
  g,f=[json.loads(raw[n],object_pairs_hook=unique) for n in ('gitlab-group.json','foundation-result.json')]
  if set(g)!={'context','group_id','origin','parent_id','previous_revisions','schema','source_revision','stage'} or g['schema']!=1 or g['stage']!='group-ready':raise ValueError('group schema')
  if set(f)!={'schema','phase','context','invocation','source_revision','platform_revision','parent_id','group_id','captured_at'} or f['schema']!=1 or f['phase']!='GroupReady':raise ValueError('foundation schema')
  for k in ('context','source_revision','parent_id'):
   if g[k]!=expected[k] or f[k]!=expected[k]:raise ValueError('selection mismatch')
  if g['origin']!=expected['origin'] or any(f[k]!=expected[k] for k in ('invocation','platform_revision')):raise ValueError('attempt mismatch')
  if type(g['group_id']) is not int or g['group_id']<1 or type(f['group_id']) is not int or f['group_id']!=g['group_id']:raise ValueError('group mismatch')
  if not isinstance(g['previous_revisions'],list) or any(not isinstance(x,str) or not re.fullmatch('[a-f0-9]{40}',x) for x in g['previous_revisions']):raise ValueError('history schema')
  if not isinstance(f['captured_at'],str) or len(f['captured_at'])>64:raise ValueError('capture schema')
  return {n:{'bytes':len(v),'sha256':hashlib.sha256(v).hexdigest(),'base64':base64.b64encode(v).decode()} for n,v in raw.items()}
 finally:
  if lock is not None:os.close(lock)
  os.close(fd)

if __name__=='__main__':
 try:
  expected=json.loads(sys.argv[1]);files=extract(expected)
  # Kubelet-owned DownwardAPI AtomicWriter projection, not PVC input.
  with open('/reader-identity/uid','rb') as f:uid=f.read(65).decode()
  if not re.fullmatch('[a-f0-9]{8}(-[a-f0-9]{4}){3}-[a-f0-9]{12}',uid):raise ValueError('pod identity')
  print(json.dumps({'schemaVersion':1,'podUID':uid,'selection':expected,'files':files},sort_keys=True,separators=(',',':')))
 except Exception:
  print('OriginalReceiptExtractionRefused',file=sys.stderr);sys.exit(1)
