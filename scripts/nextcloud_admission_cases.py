"""Read-only fixtures from real app/chart rendering, not a manifest generator."""
import copy
import json
import os
from pathlib import Path
import subprocess
import tempfile
import hashlib
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = Path(os.environ['NEXTCLOUD_APP_CHECKOUT']).resolve()
SSO_APP = Path(os.environ['NEXTCLOUD_SSO_APP_CHECKOUT']).resolve()
OLD_IMAGE = 'docker.io/library/nextcloud:35.0.2-apache@sha256:d88929dc8386420b8963f86cabb667fdaf733eef9dcf8fc98e226801a32c023c'
SSO_IMAGE = 'ghcr.io/perkforge/nextcloud-sso:35.0.2-oidc8.13.0@sha256:57c90b70d3c7261debbd5f2f2d760222fd6db65b8235a5c75f4ae7cb59df1d03'
HELM = os.environ.get('HELM', 'helm')
CHART = os.environ['NEXTCLOUD_CHART']


def render(chart, base, local, extra=(), checkout=APP):
    return [x for x in yaml.safe_load_all(subprocess.check_output([
        HELM, 'template', 'nextcloud', str(chart), '-n', 'tenant-home-nextcloud',
        '-f', str(checkout / base), '-f', str(checkout / local), *extra], text=True)) if x]


app = render(CHART, 'gitops/base/app-values.yaml', 'gitops/clusters/local/app-values.yaml')
# Exercise the opt-in same-pod candidate as well as the disabled default.
sidecar_app = render(CHART, 'gitops/base/app-values.yaml', 'gitops/clusters/local/app-values.yaml', ['--set', 'cronjob.enabled=true'])
sidecar_deploy = next(x for x in sidecar_app if x['kind'] == 'Deployment')

data = render(APP / 'charts/data', 'gitops/base/data-values.yaml', 'gitops/clusters/local/data-values.yaml')
selection = list(yaml.safe_load_all(subprocess.check_output(['kubectl', 'kustomize', str(APP / 'gitops/clusters/local')], text=True)))
enrollment = list(yaml.safe_load_all(subprocess.check_output(['kubectl', 'kustomize', str(ROOT / 'tenants/nextcloud')], text=True)))
foundation = list(yaml.safe_load_all(subprocess.check_output(['kubectl', 'kustomize', str(ROOT / 'tenants/nextcloud/foundation')], text=True)))
policies = [x for x in foundation if x['kind'] == 'ValidatingAdmissionPolicy']
cases = []
resources = {'Deployment':'deployments','CronJob':'cronjobs','Service':'services','Ingress':'ingresses','PersistentVolumeClaim':'persistentvolumeclaims','Cluster':'clusters','ConfigMap':'configmaps','HelmRelease':'helmreleases','Kustomization':'kustomizations','GitRepository':'gitrepositories','HelmRepository':'helmrepositories'}


def case(name, policy, obj, allowed=True, path=None, value=None):
    obj = copy.deepcopy(obj)
    if path:
        target = obj
        for key in path[:-1]: target = target[key]
        target[path[-1]] = value
    cases.append(dict(Name=name, Policy=policy, Resource=resources[obj['kind']], Object=obj, Allowed=allowed))


# Older pinned apps have no opt-in sidecar yet. Derive that allowed mutation
# from their real rendered web container so policy CI never skips this coverage.
containers = sidecar_deploy['spec']['template']['spec']['containers']
if len(containers) == 1:
    containers.append(dict(copy.deepcopy(containers[0]), name='nextcloud-cron'))
case('allow-same-pod-cron', 'nextcloud-app-pod-templates', sidecar_deploy)
prefix = ['spec','template','spec','containers']
for name,path,value in [
    ('unreviewed-sidecar',[1,'name'],'other'),
    ('root-sidecar',[1,'securityContext','runAsUser'],0),
    ('sidecar-escalation',[1,'securityContext','allowPrivilegeEscalation'],True),
    ('sidecar-image',[1,'image'],'attacker.invalid/image:latest')]:
    case('deny-'+name,'nextcloud-app-pod-templates',sidecar_deploy,False,prefix+path,value)
case('deny-third-container','nextcloud-app-pod-templates',sidecar_deploy,False,prefix,containers+[dict(containers[1],name='other')])

for obj in app + data:
    case('rendered-' + obj['kind'] + '-' + obj['metadata']['name'], 'nextcloud-rendered-resources', obj)
    specific = {'PersistentVolumeClaim':'nextcloud-files','Cluster':'nextcloud-database','Ingress':'nextcloud-ingress','Service':'nextcloud-service','Deployment':'nextcloud-web-shape','CronJob':'nextcloud-cron-shape'}.get(obj['kind'])
    if specific:
        case('shape-' + obj['kind'], specific, obj)
        if obj['kind']=='Deployment':
            case('deny-overlap',specific,obj,False,['spec','replicas'],2)
        if obj['kind']=='CronJob':
            case('deny-overlapping-cron',specific,obj,False,['spec','concurrencyPolicy'],'Allow')
        if obj['kind']=='Ingress':
            case('deny-other-ingress',specific,obj,False,['spec','rules',0,'host'],'other.invalid')
            case('deny-plaintext-entrypoint',specific,obj,False,['metadata','annotations','traefik.ingress.kubernetes.io/router.entrypoints'],'web')
            case('deny-cross-namespace-middleware',specific,obj,False,['metadata','annotations','traefik.ingress.kubernetes.io/router.middlewares'],'other-private@kubernetescrd')
    if obj['kind'] in {'Deployment','CronJob'}:
        case('pod-' + obj['kind'], 'nextcloud-app-pod-templates', obj)
        prefix = ['spec','template','spec'] if obj['kind']=='Deployment' else ['spec','jobTemplate','spec','template','spec']
        for name,path,value in [
            ('credential-identity',['serviceAccountName'],'nextcloud-db'),
            ('token',['automountServiceAccountToken'],True),
            ('image',['containers',0,'image'],'attacker.invalid/image:latest'),
            ('secret-volume',['volumes',0],{'name':'private','secret':{'secretName':'nextcloud-db-ca'}}),
            ('secret-env',['containers',0,'env'],[{'name':'PRIVATE','valueFrom':{'secretKeyRef':{'name':'nextcloud-db-ca','key':'ca.key'}}}]),
            ('worker',['nodeSelector'],{'kubernetes.io/hostname':'control-1'})]:
            case(obj['kind']+'-deny-'+name,'nextcloud-app-pod-templates',obj,False,prefix+path,value)
        case(obj['kind']+'-deny-cnpg-label','nextcloud-app-pod-templates',obj,False,
             prefix[:-1]+['metadata','labels','cnpg.io/cluster'],'nextcloud-db')
        if obj['kind']=='Deployment':
            case('deny-init-secret-env','nextcloud-app-pod-templates',obj,False,
                 prefix+['initContainers',0,'env'],[{'name':'PRIVATE','valueFrom':{'secretKeyRef':{'name':'nextcloud-db-ca','key':'ca.key'}}}])
for obj in selection:
    if obj['kind']=='HelmRelease':
        case('release-'+obj['metadata']['name'],'nextcloud-releases',obj)
        # Flux preserves inline values as untyped JSON. Safety is enforced on
        # rendered objects (e.g. deny-overlap), not by unsupported CEL field access.
        case('inline-values-runtime-enforced-'+obj['metadata']['name'],'nextcloud-releases',obj,True,['spec','values'],{'replicaCount':2})
        for name,path,value in [('identity',['spec','serviceAccountName'],'default'),('namespace',['spec','targetNamespace'],'gitlab'),('remote',['spec','kubeConfig'],{'secretRef':{'name':'escape'}})]:
            case(obj['metadata']['name']+'-deny-'+name,'nextcloud-releases',obj,False,path,value)
for obj in enrollment:
    policy = {'Kustomization':'nextcloud-child','GitRepository':'nextcloud-sources','HelmRepository':'nextcloud-chart-source'}[obj['kind']]
    case('enrollment-'+obj['kind'],policy,obj)
    if obj['kind']=='GitRepository':
        case('deny-unconfigured-resume',policy,obj,False,['spec','suspend'],False)
        case('deny-other-repository',policy,obj,False,['spec','url'],'https://attacker.invalid/repo.git')
    if obj['kind']=='Kustomization':
        case('deny-child-patches',policy,obj,False,['spec','patches'],[])
        case('deny-child-identity',policy,obj,False,['spec','serviceAccountName'],'default')
for obj in yaml.safe_load_all(subprocess.check_output(['kubectl','kustomize',str(ROOT/'clusters/local-nextcloud')],text=True)):
    policy={'Kustomization':'nextcloud-child','GitRepository':'nextcloud-sources','HelmRepository':'nextcloud-chart-source'}[obj['kind']]
    case('nextcloud-only-'+obj['kind'],policy,obj)
    if obj['kind']=='GitRepository':
        case('deny-public-source-unconfigured-resume',policy,obj,False,['spec','ref'],{'tag':'UNCONFIGURED'})
db = data[0]
for name,path,value in [('generic-storage',['spec','storage','storageClass'],'longhorn'),('db-image',['spec','imageName'],'postgres:latest'),('db-plaintext',['spec','postgresql','pg_hba'],['host all all all trust']),('db-credential',['spec','bootstrap','initdb','secret','name'],'nextcloud-admin')]:
    case('deny-'+name,'nextcloud-database',db,False,path,value)
claim = next(x for x in app if x['kind']=='PersistentVolumeClaim')
case('deny-single-excess','nextcloud-files',claim,False,['spec','storageClassName'],'longhorn-single-excess')
case('deny-unreviewed-expansion','nextcloud-files',claim,False,['spec','resources','requests','storage'],'250Gi')
case('deny-existing-pv-adoption','nextcloud-files',claim,False,['spec','volumeName'],'existing-pv')
service = next(x for x in app if x['kind']=='Service')
case('deny-nodeport','nextcloud-service',service,False,['spec','type'],'NodePort')
cm = next(x for x in app if x['kind']=='ConfigMap')
case('deny-delivered-ca-write','nextcloud-rendered-resources',cm,False,['metadata','name'],'nextcloud-db-ca')
# The published app remains the release/rollback fixture. Independently render
# the exact cross-repository SSO candidate without advancing any deployment pin.
sso_app = render(CHART, 'gitops/base/app-values.yaml', 'gitops/clusters/local/app-values.yaml', checkout=SSO_APP)
sso_deploy = next(x for x in sso_app if x['kind'] == 'Deployment')
pod = sso_deploy['spec']['template']['spec']
assert {c['image'] for c in pod['containers'] + pod.get('initContainers', [])} == {SSO_IMAGE}
assert pod['imagePullSecrets'] == [{'name': 'nextcloud-registry-existing'}]
assert {v['name'] for v in pod['volumes']} >= {'oidc-ca', 'oidc-secret'}
assert {c['name'] for c in pod['containers']} == {'nextcloud', 'nextcloud-cron'}
policy = 'nextcloud-app-pod-templates'
case('allow-published-sso-app-render', policy, sso_deploy)
case('sso-render-shape', 'nextcloud-web-shape', sso_deploy)
case('sso-render-resource', 'nextcloud-rendered-resources', sso_deploy)
prefix = ['spec', 'template', 'spec']
for name, path, value in [
    ('wrong-pull-secret', ['imagePullSecrets'], [{'name': 'other-app'}]),
    ('extra-pull-secret', ['imagePullSecrets'], pod['imagePullSecrets'] + [{'name': 'other-app'}]),
    ('missing-pull-secret', ['imagePullSecrets'], []),
    ('root', ['containers', 0, 'securityContext', 'runAsUser'], 0),
    ('escalation', ['containers', 0, 'securityContext', 'allowPrivilegeEscalation'], True),
    ('token', ['automountServiceAccountToken'], True),
    ('service-account', ['serviceAccountName'], 'nextcloud-db'),
]:
    case('published-sso-deny-' + name, policy, sso_deploy, False, prefix + path, value)
missing_pull = copy.deepcopy(sso_deploy)
del missing_pull['spec']['template']['spec']['imagePullSecrets']
case('published-sso-deny-absent-pull-secret', policy, missing_pull, False)
for group in ['containers', 'initContainers']:
    for index, container in enumerate(pod.get(group, [])):
        case('published-sso-deny-mixed-' + container['name'], policy, sso_deploy, False,
             prefix + [group, index, 'image'], OLD_IMAGE)
        for mount_index, mount in enumerate(container.get('volumeMounts', [])):
            if mount['name'] not in ['oidc-ca', 'oidc-secret']:
                continue
            mount_prefix = prefix + [group, index, 'volumeMounts', mount_index]
            for field, value in [('readOnly', False), ('mountPath', '/var/www/html'),
                                 ('subPath', 'client-secret'), ('subPathExpr', '$(FILE)')]:
                case('published-sso-deny-' + container['name'] + '-' + mount['name'] + '-' + field,
                     policy, sso_deploy, False, mount_prefix + [field], value)
for index, volume in enumerate(pod['volumes']):
    if volume['name'] == 'oidc-secret':
        for name, path, value in [
            ('secret', ['secret', 'secretName'], 'other-app'),
            ('secret-key', ['secret', 'items', 0, 'key'], 'other-key'),
            ('secret-path', ['secret', 'items', 0, 'path'], 'other-path'),
            ('secret-mode', ['secret', 'defaultMode'], 420),
            ('secret-item-mode', ['secret', 'items', 0, 'mode'], 511),
            ('secret-alias', ['name'], 'other-name'),
        ]:
            case('published-sso-deny-' + name, policy, sso_deploy, False, prefix + ['volumes', index] + path, value)
    if volume['name'] == 'oidc-ca':
        case('published-sso-deny-ca-alias', policy, sso_deploy, False, prefix + ['volumes', index, 'name'], 'other-name')
for image_name, image in [('different-digest', SSO_IMAGE.split('@')[0] + '@sha256:' + 'b'*64),
                          ('tag-only', SSO_IMAGE.split('@')[0])]:
    invalid = copy.deepcopy(sso_deploy)
    invalid_pod = invalid['spec']['template']['spec']
    for container in invalid_pod['containers'] + invalid_pod.get('initContainers', []):
        container['image'] = image
    case('published-sso-deny-' + image_name, policy, invalid, False)
rollback = copy.deepcopy(sidecar_deploy)
rollback['spec']['template']['spec']['imagePullSecrets'] = [{'name': 'nextcloud-registry-existing'}]
case('allow-public-image-retained-pull-secret', policy, rollback)
case('public-image-deny-wrong-pull-secret', policy, rollback, False, prefix + ['imagePullSecrets'], [{'name': 'other-app'}])

# Compile the actual unselected SSO renderer output, preserving the active policy.
with tempfile.TemporaryDirectory(prefix='nextcloud-sso-cel-') as temporary:
    work = Path(temporary)
    subprocess.run(['openssl','req','-x509','-newkey','rsa:2048','-nodes','-days','1',
                    '-subj','/CN=Offline SSO CEL fixture','-keyout',str(work/'key'),'-out',str(work/'ca')],
                   check=True,capture_output=True)
    image='ghcr.io/perkforge/nextcloud-sso:35.0.2-oidc8.13.0@sha256:'+'a'*64
    values={'nextcloud_sso_render':True,'nextcloud_sso_delivery_contract':True,
            'nextcloud_sso_image':image,'nextcloud_sso_issuer_ipv4':'192.168.100.10',
            'nextcloud_sso_ca_file':str(work/'ca'),'nextcloud_sso_ca_sha256':hashlib.sha256((work/'ca').read_bytes()).hexdigest(),
            'nextcloud_sso_output':str(work/'output')}
    result=subprocess.run(['ansible-playbook',str(ROOT/'tenants/nextcloud/sso/prepare.yaml'),'-e',json.dumps(values)],
                          env=dict(os.environ,ANSIBLE_LOCAL_TEMP=str(work/'local'),ANSIBLE_REMOTE_TEMP=str(work/'remote')),
                          capture_output=True,text=True)
    if result.returncode:raise RuntimeError(result.stdout+result.stderr)
    policy=yaml.safe_load((work/'output/runtime-policy.yaml').read_text())
    policy['metadata']['name']='nextcloud-sso-app-pod-templates'
    policies.append(policy)
    candidate=copy.deepcopy(sidecar_deploy)
    pod=candidate['spec']['template']['spec']
    pod['imagePullSecrets']=[{'name':'nextcloud-registry-existing'}]
    for container in pod['containers']+pod.get('initContainers',[]):container['image']=image
    pod['volumes'] += [{'name':'oidc-ca','configMap':{'name':'nextcloud-oidc-ca'}},
                       {'name':'oidc-secret','secret':{'secretName':'nextcloud-oidc','defaultMode':288,'items':[{'key':'client-secret','path':'client-secret'}]}}]
    for container in pod['containers']:
        container.setdefault('volumeMounts',[]).extend([{'name':'oidc-ca','mountPath':'/etc/nextcloud-oidc','readOnly':True},
                                                       {'name':'oidc-secret','mountPath':'/run/nextcloud-oidc','readOnly':True}])
    case('allow-exact-unselected-sso-contract','nextcloud-sso-app-pod-templates',candidate)
    case('active-policy-denies-unselected-sso','nextcloud-app-pod-templates',candidate,False)
    prefix=['spec','template','spec']
    for name,path,value in [('image',['containers',0,'image'],'ghcr.io/perkforge/nextcloud-sso:latest'),
                            ('secret',['volumes',len(pod['volumes'])-1,'secret','secretName'],'other-app'),
                            ('secret-key',['volumes',len(pod['volumes'])-1,'secret','items',0,'key'],'other-key'),
                            ('mount-write',['containers',0,'volumeMounts',len(pod['containers'][0]['volumeMounts'])-1,'readOnly'],False),
                            ('mount-path',['containers',0,'volumeMounts',len(pod['containers'][0]['volumeMounts'])-1,'mountPath'],'/var/www/html'),
                            ('token',['automountServiceAccountToken'],True)]:
        case('sso-deny-'+name,'nextcloud-sso-app-pod-templates',candidate,False,prefix+path,value)
schemas = {}
crds = []
if os.environ.get('NEXTCLOUD_CRDS'):
    crds += json.loads(Path(os.environ['NEXTCLOUD_CRDS']).read_text())['items']
if os.environ.get('NEXTCLOUD_CRD_DIR'):
    for path in Path(os.environ['NEXTCLOUD_CRD_DIR']).glob('*.yaml'):
        crds += [x for x in yaml.safe_load_all(path.read_text()) if x and x.get('kind') == 'CustomResourceDefinition']
for crd in crds:
    for version in crd['spec']['versions']:
        if version.get('served'):
            key = 'io.k8s.api.' + crd['spec']['group'] + '.' + version['name'] + '.' + crd['spec']['names']['kind']
            schemas[key] = version['schema']['openAPIV3Schema']
print(json.dumps(dict(Policies=policies,Cases=cases,Schemas=schemas)))
