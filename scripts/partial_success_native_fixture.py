"""Scenario text injected into the isolated launcher fixture; never a live API client."""

def replace_once(text, old, new):
 if text.count(old)!=1:raise ValueError('partial-success fixture seam drift')
 return text.replace(old,new)

def transform(text):
 text=replace_once(text,"   if p=='/api/v4/users':return", "   if p=='/api/v4/users' and state.get('deny_attestor'):state['denied_lookups']=state.get('denied_lookups',0)+1;return self.reply(403,{})\n   if p=='/api/v4/users':return")
 text=replace_once(text,"'uid':uid,'name'", "'uid':state.get('cm_uid',uid),'name'")
 start=text.index('start=time.monotonic()\ntry:')
 if text.count('start=time.monotonic()\ntry:')!=1:raise ValueError('partial-success scenario seam drift')
 return (text[:start]+SCENARIO).replace('OFFLINE-READER','OFFLINE.READER')

SCENARIO='''start=time.monotonic()
try:
 # Obtain actual native-shaped foundation receipts; do not fabricate a predecessor.
 p=phase('foundation');assert p.returncode==0,(p.stdout,p.stderr)
 assert state['groupWrites']==1 and state['patches']==0 and state['data']=={}
 state['deny_attestor']=True
 p=phase('attest');assert p.returncode!=0 and state['denied_lookups']==1
 assert state['data']=={} and state['patches']==0 and state['membershipWrites']==0
 state['deny_attestor']=False
 newer=dict(d,identity_previous_invocation=d['identity_invocation'],identity_previous_attestation_invocation='',identity_retry_generation=1)
 newer['identity_invocation']=invocation(newer);assert newer['identity_invocation']!=d['identity_invocation']
 state['desired']=newer['identity_invocation']
 p=phase('foundation',newer);assert p.returncode==0,(p.stdout,p.stderr)
 assert state['groupWrites']==1
 before=state['calls'];p=phase('foundation');assert p.returncode!=0 and state['calls']==before
 # Native receipt-object UID and current desired invocation remain publication gates.
 state['cm_uid']='33333333-3333-4333-8333-333333333333'
 p=phase('attest',newer);assert p.returncode!=0 and state['patches']==0 and state['data']=={}
 del state['cm_uid'];state['desired']=d['identity_invocation']
 p=phase('attest',newer);assert p.returncode!=0 and state['patches']==0 and state['data']=={}
 state['desired']=newer['identity_invocation']
 p=phase('attest',newer);assert p.returncode==0,(p.stdout,p.stderr)
 assert state['patches']==1
 envelope=json.loads(state['data']['receipt.json'])
 assert envelope['invocation']==newer['identity_invocation'] and envelope['previous_attestation_invocation']==''
 saved=dict(state['data'])
 # An explicit empty issuer predecessor cannot overwrite even its own existing receipt.
 p=phase('attest',newer);assert p.returncode!=0 and state['patches']==1 and state['data']==saved
 P('/identity-evidence/receipt.json').write_text(state['data']['receipt.json'])
 p=phase('memberships',newer);assert p.returncode==0,(p.stdout,p.stderr)
 assert state['membershipWrites']==1
 p=phase('memberships',newer);assert p.returncode==0 and state['membershipWrites']==1
 before=state['calls'];p=phase('memberships');assert p.returncode!=0 and state['calls']==before
 assert not list(P('/tmp').glob('phase-*'))
 r=resource.getrusage(resource.RUSAGE_CHILDREN)
 print(json.dumps({'result':'PASS','scope':'same-artifact partial-success retry: actual foundation, synthetic attestor403 with empty issuer, explicit retry1, idempotent foundation, UID/desired/no-overwrite denials, attestation and membership; not artifact migration or credential isolation proof','wall_seconds':time.monotonic()-start,'cpu_user_seconds':r.ru_utime,'cpu_system_seconds':r.ru_stime,'largest_child_rss_kib':r.ru_maxrss}))
finally:srv.shutdown();srv.server_close()
'''
