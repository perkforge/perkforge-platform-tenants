"""Versioned, literal adopter profile. No runtime discovery or provider fallback."""
import copy,json,pathlib,re
PILOT=json.loads((pathlib.Path(__file__).resolve().parents[1]/'profiles/identity/portal-rke2-longhorn.json').read_text())
def exact(d,keys):
 if not isinstance(d,dict) or set(d)!=set(keys):raise ValueError('target profile exact fields required')
def port(v):
 if type(v) is not int or not 1<=v<=65535:raise ValueError('literal port required')
def labels(d):
 if not isinstance(d,dict) or not 1<=len(d)<=8:raise ValueError('nonempty exact label selectors required')
 for k,v in d.items():
  if not isinstance(k,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.\-/]{0,252}',k) or not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,62}',v):raise ValueError('literal selector')
def storage(d):
 exact(d,('provider','className','size'))
 if d['provider']!='longhorn-v1':raise ValueError('unsupported storage provider; no fallback')
 if not isinstance(d['className'],str) or not re.fullmatch(r'[a-z][a-z0-9.-]{0,62}',d['className']):raise ValueError('storage class')
 if not isinstance(d['size'],str) or not re.fullmatch(r'(?:[1-9]|1[0-6])Gi',d['size']):raise ValueError('bounded receipt size 1..16Gi')
 return copy.deepcopy(d)
def validate(p):
 exact(p,('schemaVersion','apiAudience','dns','ingress','api','storage'))
 if type(p['schemaVersion']) is not int or p['schemaVersion']!=1:raise ValueError('profile version')
 if not isinstance(p['apiAudience'],str) or not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::[0-9]{1,5})?',p['apiAudience']):raise ValueError('exact HTTPS API audience')
 for k,ports in [('dns',('port',)),('ingress',('frontendPort','backendPort'))]:
  exact(p[k],('namespaceLabels','podLabels',*ports));labels(p[k]['namespaceLabels']);labels(p[k]['podLabels'])
  for f in ports:port(p[k][f])
 exact(p['api'],('servicePort','backendPort'))
 for v in p['api'].values():port(v)
 storage(p['storage']);return copy.deepcopy(p)
def attempt_input(d):
 # Explicit legacy-equivalent profile preserves already reviewed pilot names.
 # Every other validated profile participates in attempt identity.
 p=validate(d['targetProfile']);out={k:v for k,v in d.items() if k!='membershipReleased'}
 if p==PILOT:out.pop('targetProfile')
 return out
def initializer_identity(i):
 out={k:v for k,v in i.items() if k not in ('pv','pvUID','volumeHandle')}
 if storage(i['storageProfile'])==PILOT['storage']:out.pop('storageProfile')
 return out
