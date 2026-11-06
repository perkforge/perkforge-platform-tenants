"""Read-only fixtures from real app/chart rendering, not a manifest generator."""
import copy
import json
import os
from pathlib import Path
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
APP = Path(os.environ['NEXTCLOUD_APP_CHECKOUT']).resolve()
HELM = os.environ.get('HELM', 'helm')
CHART = os.environ['NEXTCLOUD_CHART']


def render(chart, base, local):
    return [x for x in yaml.safe_load_all(subprocess.check_output([
        HELM, 'template', 'nextcloud', str(chart), '-n', 'tenant-home-nextcloud',
        '-f', str(APP / base), '-f', str(APP / local)], text=True)) if x]


app = render(CHART, 'gitops/base/app-values.yaml', 'gitops/clusters/local/app-values.yaml')
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
