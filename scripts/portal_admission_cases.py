"""Actual selected active Portal release rendered offline without enablement overrides.
Historical v1.0.0 render remains a denial fixture, never a selected dependency.
"""
from copy import deepcopy
import json
import os
from test_enrollment_release import render_local_app, active_portal_release
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
p=next(yaml.safe_load_all((ROOT/'tenants/portal/foundation/deployment-policy.yaml').read_text()))
base=next(obj for obj in render_local_app(Path(os.environ['ACTIVE_PORTAL_APP_CHECKOUT']), release=active_portal_release()) if obj['kind']=='Deployment')
assert base == json.loads((ROOT/'scripts/fixtures/portal-active-deployment.json').read_text())
params=yaml.safe_load((ROOT/'tenants/portal/foundation/runtime-contract.yaml').read_text())
cases=[]
def add(name,mutate=None):
    obj=deepcopy(base)
    if mutate: mutate(obj['spec']['template']['spec'])
    cases.append({'name':name,'object':obj,'allowed':mutate is None})
add('published-active-physical')
cases.append({'name':'old-auth-image-rejected','object':json.loads((ROOT/'scripts/fixtures/portal-v2.0.0-deployment.json').read_text()),'allowed':False})
add('old-vm-selector',lambda x:x.update(nodeSelector={'kubernetes.io/hostname':'cks-worker'}))
add('missing-affinity',lambda x:x.pop('affinity'))
add('node-name-bypass',lambda x:x.update(nodeName='control-plane'))
add('toleration-bypass',lambda x:x.update(tolerations=[{'operator':'Exists'}]))
add('extra-or-term',lambda x:x['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'].append({'matchExpressions':[{'key':'any','operator':'Exists'}]}))
add('missing-master-exclusion',lambda x:x['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0]['matchExpressions'].pop())
add('wrong-image',lambda x:x['containers'][0].update(image='ghcr.io/perkforge/perkforge-portal:latest'))
add('resource-drift',lambda x:x['containers'][0]['resources']['requests'].update(cpu='26m'))
for key,val in [('PORTAL_ACCESS_POLICY','home'),('PORTAL_ORIGIN','https://portal-local-il2.local-lab.test'),('OIDC_ISSUER','https://keycloak-local-il2.local-lab.test/auth/realms/perkforge'),('OIDC_CLIENT_ID','other'),('OIDC_AUDIENCE','other'),('NODE_EXTRA_CA_CERTS','/tmp/ca')]:
    add(key,lambda x,key=key,val=val:next(e for e in x['containers'][0]['env'] if e['name']==key).update(value=val))
add('host-alias',lambda x:x.update(hostAliases=[{'ip':'192.168.100.11','hostnames':['keycloak.perkforge.home.arpa']}]))
add('dns-override',lambda x:x.update(dnsPolicy='Default'))
add('eso-token-service-account',lambda x:x.update(serviceAccountName='eso-tenant-portal'))
add('api-token',lambda x:x.update(automountServiceAccountToken=True))
add('additional-volume',lambda x:x['volumes'].append({'name':'data','emptyDir':{}}))
add('extra-env',lambda x:x['containers'][0]['env'].append({'name':'NODE_TLS_REJECT_UNAUTHORIZED','value':'0'}))
# Actual rendered published v1.0.0 (dcb6e3fc56961a977172bac3f2c493df2eb806e3).
cases.append({'name':'published-v1.0.0-rejected','object':json.loads((ROOT/'scripts/fixtures/portal-v1.0.0-deployment.json').read_text()),'allowed':False})
# Optional inventory remains inside exact named public-config boundary.
def inventory_pod(pod):
    if any(v['name']=='enrollment-inventory' for v in pod['volumes']):
        return
    pod['volumes'].append({'name':'enrollment-inventory','configMap':{'name':'portal-enrollment-inventory'}})
    pod['containers'][0]['volumeMounts'].append({'name':'enrollment-inventory','mountPath':'/etc/portal/enrollment','readOnly':True})
    pod['containers'][0]['env'].extend([
        {'name':'ENROLLMENT_SOURCE','value':'gitops-configmap'},
        {'name':'ENROLLMENT_SOURCE_COMMIT','value':'a'*40},
        {'name':'ENROLLMENT_INVENTORY_SHA256','value':'b'*64},
        {'name':'ENROLLMENT_SELECTOR','value':'local-nextcloud-portal'}])
positive=deepcopy(base)
inventory_pod(positive['spec']['template']['spec'])
cases.append({'name':'exact-inventory-mounted','object':positive,'allowed':True})
ca_only=deepcopy(positive)
cp=ca_only['spec']['template']['spec']
cp['volumes']=[v for v in cp['volumes'] if v['name']=='identity-ca']
cp['containers'][0]['volumeMounts']=[v for v in cp['containers'][0]['volumeMounts'] if v['name']=='identity-ca']
cp['containers'][0]['env']=[e for e in cp['containers'][0]['env'] if not e['name'].startswith('ENROLLMENT_')]
cases.append({'name':'ca-only-still-allowed','object':ca_only,'allowed':True})
for label, change in [
    ('wrong-cm',lambda x:next(v for v in x['volumes'] if v['name']=='enrollment-inventory')['configMap'].update(name='other')),
    ('writable',lambda x:next(v for v in x['containers'][0]['volumeMounts'] if v['name']=='enrollment-inventory').update(readOnly=False)),
    ('wrong-path',lambda x:next(v for v in x['containers'][0]['volumeMounts'] if v['name']=='enrollment-inventory').update(mountPath='/tmp')),
    ('subpath',lambda x:next(v for v in x['containers'][0]['volumeMounts'] if v['name']=='enrollment-inventory').update(subPath='other')),
    ('missing-pin',lambda x:x['containers'][0].update(env=[e for e in x['containers'][0]['env'] if e['name']!='ENROLLMENT_SOURCE_COMMIT'])),
    ('bad-hash',lambda x:next(e for e in x['containers'][0]['env'] if e['name']=='ENROLLMENT_INVENTORY_SHA256').update(value='bad')),
    ('network-mode',lambda x:next(e for e in x['containers'][0]['env'] if e['name']=='ENROLLMENT_SOURCE').update(value='github-public'))]:
    obj=deepcopy(positive); change(obj['spec']['template']['spec'])
    cases.append({'name':'inventory-'+label,'object':obj,'allowed':False})
print(json.dumps({'policy':p,'params':params,'cases':cases}))
