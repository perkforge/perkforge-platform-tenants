#!/usr/bin/env python3
"""Run inside isolated maintained image; synthetic loopback services only."""
import datetime as dt,hashlib,json,pathlib,ssl,subprocess,threading,resource,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,parse_qs,unquote
P=pathlib.Path;uid='22222222-2222-4222-8222-222222222222'
roles={'tenant-admin':'admins','tenant-developer':'developers','tenant-viewer':'viewers'}
groups={r:f'00000000-0000-4000-8000-{i:012d}' for i,r in enumerate(roles,1)}
state={'rv':1,'data':{},'desired':'','group':False,'groupWrites':0,'patches':0,'calls':0,'members':{},'membershipWrites':0}
class H(BaseHTTPRequestHandler):
 def log_message(self,*a):pass
 def reply(self,n,v):self.send_response(n);self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(json.dumps(v).encode())
 def cm(self):return {'metadata':{'uid':uid,'name':'portal-identity-evidence','namespace':'tenant-identity-writer','resourceVersion':str(state['rv']),'labels':{'app.kubernetes.io/managed-by':'perkforge-identity','perkforge.dev/context':'portal'},'annotations':{'perkforge.dev/desired-invocation':state['desired']}},'data':state['data']}
 def do_GET(self):
  state['calls']+=1;p=unquote(urlsplit(self.path).path)
  if p.startswith('/auth/admin/'):
   if self.headers.get('Authorization')!='Bearer OFFLINE-KC-ACCESS':return self.reply(403,{})
   r=next((r for r,g in groups.items() if '/groups/'+g in p),None)
   if not r:return self.reply(403,{})
   return self.reply(200,([{'id':'11111111-1111-4111-8111-111111111111','enabled':True}] if r=='tenant-developer' else []) if p.endswith('/members') else {'id':groups[r],'path':'/tenants/portal/'+roles[r],'subGroupCount':0})
  if p.startswith('/api/v4/'):
   token=self.headers.get('PRIVATE-TOKEN')
   if token not in ('OFFLINE-WRITER','OFFLINE-READER'):return self.reply(403,{})
   if p.endswith('/personal_access_tokens/self'):return self.reply(200,{'id':80,'user_id':90,'active':True,'revoked':False,'scopes':['read_api'] if token=='OFFLINE-READER' else ['api'],'expires_at':'2099-01-01'})
   if p=='/api/v4/user':return self.reply(200,{'id':90,'bot':True,'state':'active'})
   if p=='/api/v4/groups/30/members/90':return self.reply(200,{'id':90,'access_level':50})
   if p=='/api/v4/groups/30/access_tokens/80':return self.reply(200,{'id':80,'user_id':90,'access_level':50})
   if p=='/api/v4/users':return self.reply(200,[{'id':21,'is_admin':False,'state':'active','identities':[{'provider':'openid_connect','extern_uid':'11111111-1111-4111-8111-111111111111'}]}])
   if p=='/api/v4/users/21':return self.reply(200,{'id':21,'state':'active'})
   if p in ('/api/v4/groups/31/members/21','/api/v4/groups/31/members/all/21'):return self.reply(200,{'id':21,'access_level':state['members'][21]}) if 21 in state['members'] else self.reply(404,{})
   if p.endswith('/version'):return self.reply(200,{'version':'19.4.2-ee'})
   if p in ('/api/v4/groups/30','/api/v4/groups/tenants'):return self.reply(200,{'id':30,'name':'tenants','path':'tenants','full_path':'tenants','visibility':'private','parent_id':None})
   if p in ('/api/v4/groups/31','/api/v4/groups/tenants/portal') and state['group']:return self.reply(200,{'id':31,'name':'portal','path':'portal','full_path':'tenants/portal','visibility':'private','parent_id':30,'request_access_enabled':False})
   return self.reply(404,{})
  if p=='/api/v1/namespaces/tenant-identity-writer/configmaps/portal-identity-evidence' and self.headers.get('Authorization')=='Bearer OFFLINE-API':return self.reply(200,self.cm())
  self.reply(403,{})
 def do_POST(self):
  state['calls']+=1;b=self.rfile.read(int(self.headers['Content-Length']))
  if self.path=='/auth/realms/perkforge/protocol/openid-connect/token':
   assert parse_qs(b.decode())=={'grant_type':['client_credentials'],'client_id':['snapshot-reader'],'client_secret':['OFFLINE-KC-SECRET']}
   return self.reply(200,{'token_type':'Bearer','access_token':'OFFLINE-KC-ACCESS'})
  if self.path=='/api/v4/groups/31/members' and self.headers.get('PRIVATE-TOKEN')=='OFFLINE-WRITER':
   d=json.loads(b);assert d=={'user_id':21,'access_level':30};state['members'][21]=30;state['membershipWrites']+=1;return self.reply(201,{'id':21,'access_level':30})
  if self.path=='/api/v4/groups' and self.headers.get('PRIVATE-TOKEN')=='OFFLINE-WRITER':
   d=json.loads(b);assert d['parent_id']==30 and d['path']=='portal' and d['visibility']=='private';state['group']=True;state['groupWrites']+=1
   return self.reply(201,dict(d,id=31,full_path='tenants/portal'))
  self.reply(403,{})
 def do_PATCH(self):
  state['calls']+=1
  if self.path!='/api/v1/namespaces/tenant-identity-writer/configmaps/portal-identity-evidence' or self.headers.get('Authorization')!='Bearer OFFLINE-API':return self.reply(403,{})
  ops=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  expected=[{'op':'test','path':'/metadata/uid','value':uid},{'op':'test','path':'/metadata/resourceVersion','value':str(state['rv'])},{'op':'test','path':'/metadata/annotations/perkforge.dev~1desired-invocation','value':state['desired']}]
  if ops[:3]!=expected:return self.reply(409,{})
  assert len(ops)==4 and ops[3]['path']=='/data';state['data']=ops[3]['value'];state['rv']+=1;state['patches']+=1;self.reply(200,self.cm())
srv=ThreadingHTTPServer(('127.0.0.1',0),H);tls=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);tls.load_cert_chain('/fixture/ca.crt','/fixture/key');srv.socket=tls.wrap_socket(srv.socket,server_side=True);threading.Thread(target=srv.serve_forever,daemon=True).start()
rev=json.loads(P('/opt/revisions.json').read_text());origin='https://localhost:'+str(srv.server_port)
ctx=P('/opt/platform/big-bang-bootstrap/configuration/authorization/contexts/portal.yaml').read_bytes()
d={'identity_membership_recovery_verified':True,'identity_run':True,'identity_scope':'gitlab-identity-attest-v1','identity_context':'portal','identity_source_revision':rev['enrollment'],'identity_platform_revision':rev['platform'],'identity_contract_sha256':hashlib.sha256(ctx).hexdigest(),'identity_previous_invocation':'','identity_retry_generation':0,'identity_gitlab_origin':origin,'identity_keycloak_origin':origin+'/auth','identity_keycloak_realm':'perkforge','identity_kubernetes_origin':origin,'identity_receipt_uid':uid,'identity_receipt_namespace':'tenant-identity-writer','identity_receipt_name':'portal-identity-evidence','identity_group_ids':groups}
def invocation(d):return hashlib.sha256(json.dumps({k:v for k,v in d.items() if k not in ('identity_invocation','identity_scope','identity_run')},sort_keys=True,separators=(',',':')).encode()).hexdigest()
d['identity_invocation']=invocation(d);state['desired']=d['identity_invocation']
g={'gitlab_group_run':True,'gitlab_group_scope':'gitlab-enrollment-group-foundation-v1','gitlab_group_context':'portal','gitlab_group_source_revision':rev['enrollment'],'gitlab_group_allow_parent_create':False,'gitlab_group_expected_parent_id':30,'gitlab_native_origin':origin,'gitlab_native_ca_file':'/credentials/lab-ca.crt'}
manifest=hashlib.sha256(P('/opt/provenance.sha256').read_bytes()).hexdigest()
def phase(name,identity=d):
 # Only phase-specific credential bytes are present during that invocation.
 for f in P('/credentials').iterdir():f.unlink()
 creds={'gitlab-reader':'OFFLINE-READER','kc-client-id':'snapshot-reader','kc-client-secret':'OFFLINE-KC-SECRET'} if name=='attest' else {'group-writer':'OFFLINE-WRITER'}
 for n,b in creds.items():(P('/credentials')/n).write_text(b)
 (P('/credentials')/'lab-ca.crt').write_bytes(P('/fixture/ca.crt').read_bytes())
 body={'identity':dict(identity,identity_scope='gitlab-identity-'+('attest' if name=='foundation' else name)+'-v1')}
 if name=='foundation':body['group']=g
 raw=json.dumps(body).encode();P('/inputs/inputs.json').write_bytes(raw)
 cmd=['bash','/opt/perkforge/bin/launch','--phase',name,'--invocation',identity['identity_invocation'],'--inputs-sha256',hashlib.sha256(raw).hexdigest(),'--bundle-sha256',manifest]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
 assert all(t not in p.stdout+p.stderr for t in creds.values())
 return p
start=time.monotonic()
try:
 for name in ('foundation','attest','memberships'):
  if name=='memberships':P('/identity-evidence/receipt.json').write_text(state['data']['receipt.json'])
  p=phase(name);assert p.returncode==0,(name,p.stdout,p.stderr)
 assert state['groupWrites']==1 and state['patches']==1 and state['membershipWrites']==1
 p=phase('memberships');assert p.returncode==0 and state['membershipWrites']==1
 p=phase('foundation');assert p.returncode==0 and state['groupWrites']==1
 # New foundation attempt fences an older queued attempt under stable context lock.
 newer=dict(d,identity_previous_invocation=d['identity_invocation'],identity_retry_generation=1);newer['identity_invocation']=invocation(newer)
 p=phase('foundation',newer);assert p.returncode==0
 before=state['calls'];p=phase('foundation');assert p.returncode!=0 and state['calls']==before
 # Old issuer evidence cannot authorize a new writer attempt.
 before=state['calls'];p=phase('memberships',newer);assert p.returncode!=0 and state['calls']==before
 assert not list(P('/tmp').glob('phase-*'))
 r=resource.getrusage(resource.RUSAGE_CHILDREN)
 print(json.dumps({'result':'PASS','scope':'full launcher three phases, one synthetic canonical developer grant/idempotent repeat; explicit retry/stale attempt and stale projection denials','wall_seconds':time.monotonic()-start,'cpu_user_seconds':r.ru_utime,'cpu_system_seconds':r.ru_stime,'largest_child_rss_kib':r.ru_maxrss}))
finally:srv.shutdown();srv.server_close()
