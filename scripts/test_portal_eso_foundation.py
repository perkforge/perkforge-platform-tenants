"""Offline native schema and scoped-source checks. No cluster, auth or secret API."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import subprocess
import unittest
import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'tenants/portal/eso'
BUNDLE_SHA = '2b2aa2e85a4c081a11688f0b31ebdb33153c0885d4c2e3604d11058995a11b75'

def build(path):
    return [x for x in yaml.safe_load_all(subprocess.check_output(['kubectl','kustomize',str(path)],
            text=True,env={**os.environ,'KUBECONFIG':'/dev/null'})) if x]

EXPECTED_STORE = {
    'controller':'perkforge',
    'provider':{'vault':{
        'server':'https://openbao.perkforge.home.arpa','path':'tenants','version':'v2',
        'caProvider':{'type':'ConfigMap','name':'eso-openbao-ca','key':'ca.crt'},
        'auth':{'kubernetes':{'mountPath':'kubernetes-eso','role':'eso-tenant-portal',
            'serviceAccountRef':{'name':'eso-tenant-portal','audiences':['openbao-eso']}}}}}}

EXPECTED_RULES = [
    {'apiGroups':[''],'resources':['secrets'],'verbs':['get','create','update','patch','delete']},
    {'apiGroups':['external-secrets.io'],'resources':['externalsecrets'],'verbs':['get','list','watch','update','patch']},
    {'apiGroups':['external-secrets.io'],'resources':['externalsecrets/status'],'verbs':['update','patch']},
    {'apiGroups':['external-secrets.io'],'resources':['externalsecrets/finalizers'],'verbs':['update']},
    {'apiGroups':['external-secrets.io'],'resources':['secretstores'],'verbs':['get','list','watch']},
    {'apiGroups':['external-secrets.io'],'resources':['secretstores/status'],'verbs':['patch']},
    {'apiGroups':[''],'resources':['configmaps'],'resourceNames':['eso-openbao-ca'],'verbs':['get']},
    {'apiGroups':[''],'resources':['serviceaccounts/token'],'resourceNames':['eso-tenant-portal'],'verbs':['create']},
    {'apiGroups':[''],'resources':['events'],'verbs':['create','patch']},
]

def exact_store(store):
    assert store['apiVersion']=='external-secrets.io/v1'
    assert store['kind']=='SecretStore'
    assert store['metadata']=={'name':'openbao-tenant','namespace':'tenant-portal'}
    assert store['spec']==EXPECTED_STORE

# Source-level namespaced grants only, not a claim about live/global RBAC.
def allowed(objects, subject, namespace, group, resource, verb, name=''):
    roles={(o['metadata']['namespace'],o['metadata']['name']):o for o in objects if o['kind']=='Role'}
    for binding in (o for o in objects if o['kind']=='RoleBinding' and o['metadata']['namespace']==namespace):
        if not any(s.get('kind')=='ServiceAccount' and (s.get('namespace',namespace),s['name'])==subject for s in binding['subjects']):
            continue
        assert binding['roleRef']['kind']=='Role'
        for rule in roles[(namespace,binding['roleRef']['name'])]['rules']:
            if group in rule['apiGroups'] and resource in rule['resources'] and verb in rule['verbs']:
                if 'resourceNames' not in rule or name in rule['resourceNames']: return True
    return False

class PortalESOFoundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objects=build(STAGE)
        cls.store=next(o for o in cls.objects if o['kind']=='SecretStore')
        bundle=Path(os.environ['ESO_CRD_BUNDLE']).read_bytes()
        assert hashlib.sha256(bundle).hexdigest()==BUNDLE_SHA
        crd=next(o for o in yaml.safe_load_all(bundle) if o and o['metadata']['name']=='secretstores.external-secrets.io')
        versions=crd['spec']['versions']
        assert [v['name'] for v in versions if v['served']]==['v1']
        cls.schema=next(v for v in versions if v['name']=='v1')['schema']['openAPIV3Schema']
        cls.validator=jsonschema.Draft7Validator(cls.schema)

    def test_native_v1_schema_accepts_stage_and_rejects_invalid_provider_shapes(self):
        self.validator.validate(self.store)
        mutations=[lambda s:s['spec']['provider']['vault'].update(version='v3'),
                   lambda s:s['spec']['provider']['vault']['caProvider'].update(type='Unknown'),
                   lambda s:s['spec']['provider']['vault']['auth']['kubernetes']['serviceAccountRef'].pop('name'),
                   lambda s:s['spec']['provider']['vault']['auth']['kubernetes']['serviceAccountRef'].update(audiences='openbao-eso')]
        for mutate in mutations:
            value=deepcopy(self.store);mutate(value)
            self.assertTrue(list(self.validator.iter_errors(value)))

    def test_exact_store_rejects_cross_namespace_fallback_and_provider_drift(self):
        exact_store(self.store)
        mutations=[lambda s:s.update(apiVersion='external-secrets.io/v1beta1'),
                   lambda s:s.update(kind='ClusterSecretStore'),
                   lambda s:s['spec'].update(controller='other'),
                   lambda s:s['spec']['provider']['vault'].update(server='http://openbao.perkforge.home.arpa'),
                   lambda s:s['spec']['provider']['vault'].update(path='platform'),
                   lambda s:s['spec']['provider']['vault']['caProvider'].update(name='portal-identity-ca'),
                   lambda s:s['spec']['provider']['vault']['caProvider'].update(namespace='other'),
                   lambda s:s['spec']['provider']['vault']['auth']['kubernetes'].update(secretRef={'name':'legacy'}),
                   lambda s:s['spec']['provider']['vault']['auth']['kubernetes'].update(role='other'),
                   lambda s:s['spec']['provider']['vault']['auth']['kubernetes']['serviceAccountRef'].update(namespace='other'),
                   lambda s:s['spec']['provider']['vault']['auth']['kubernetes']['serviceAccountRef'].update(audiences=['other'])]
        for mutate in mutations:
            value=deepcopy(self.store);mutate(value)
            with self.assertRaises(AssertionError): exact_store(value)

    def test_stage_contains_no_consumers_credentials_trust_or_cluster_grants(self):
        self.assertEqual(sorted(o['kind'] for o in self.objects),['Role','RoleBinding','SecretStore','ServiceAccount'])
        self.assertTrue(all(o['metadata']['namespace']=='tenant-portal' for o in self.objects))
        sa=next(o for o in self.objects if o['kind']=='ServiceAccount')
        self.assertEqual(sa,{'apiVersion':'v1','kind':'ServiceAccount','metadata':{'name':'eso-tenant-portal','namespace':'tenant-portal'},'automountServiceAccountToken':False})
        binding=next(o for o in self.objects if o['kind']=='RoleBinding')
        self.assertEqual(binding['subjects'],[{'kind':'ServiceAccount','name':'external-secrets','namespace':'external-secrets'}])
        self.assertEqual(binding['roleRef'],{'apiGroup':'rbac.authorization.k8s.io','kind':'Role','name':'portal-eso-controller'})
        role=next(o for o in self.objects if o['kind']=='Role')
        self.assertEqual(role['rules'],EXPECTED_RULES)

    def test_every_ordinary_root_and_foundation_omits_stage(self):
        for path in [*sorted((ROOT/'clusters').iterdir()),ROOT/'tenants/portal/foundation',ROOT/'tenants/nextcloud/foundation']:
            objects=build(path)
            self.assertFalse(any(o['kind'] in ['SecretStore','ExternalSecret','ClusterSecretStore'] or
                o['metadata'].get('name') in ['eso-tenant-portal','portal-eso-controller'] for o in objects),str(path))

    def test_controller_namespaced_positive_and_negative_grants(self):
        actor=('external-secrets','external-secrets')
        for group,resource,verb,name in [('', 'secrets','create','portal-oidc-existing'),
                ('','configmaps','get','eso-openbao-ca'),('','serviceaccounts/token','create','eso-tenant-portal'),
                ('external-secrets.io','externalsecrets/status','patch','portal'),('external-secrets.io','secretstores/status','patch','openbao-tenant')]:
            self.assertTrue(allowed(self.objects,actor,'tenant-portal',group,resource,verb,name))
        for namespace,group,resource,verb,name in [
                ('tenant-home-nextcloud','','secrets','create','x'),
                ('tenant-portal','','secrets','list',''),('tenant-portal','','secrets','watch',''),
                ('tenant-portal','','configmaps','get','portal-identity-ca'),
                ('tenant-portal','','serviceaccounts/token','create','portal-runtime'),
                ('tenant-portal','','serviceaccounts','get','eso-tenant-portal'),
                ('tenant-portal','external-secrets.io','secretstores','create','other'),
                ('tenant-portal','external-secrets.io','clustersecretstores','get','platform'),
                ('tenant-portal','external-secrets.io','externalsecrets','create','new'),
                ('tenant-portal','rbac.authorization.k8s.io','roles','create','new')]:
            self.assertFalse(allowed(self.objects,actor,namespace,group,resource,verb,name))

    def test_app_and_token_subject_receive_no_store_token_or_runtime_secret_grants(self):
        objects=build(ROOT/'tenants/portal/foundation')+self.objects
        for actor in [('tenant-portal','eso-tenant-portal'),('tenant-portal','portal-runtime'),
                      ('tenant-portal-config','portal-reconciler'),('tenant-portal-config','portal-deployer')]:
            for group,resource,verb,name in [('', 'secrets','get','portal-oidc-existing'),
                    ('','serviceaccounts/token','create','eso-tenant-portal'),('','serviceaccounts','create','new'),
                    ('external-secrets.io','secretstores','create','openbao-tenant'),
                    ('external-secrets.io','clustersecretstores','get','platform'),
                    ('external-secrets.io','externalsecrets','create','new')]:
                self.assertFalse(allowed(objects,actor,'tenant-portal',group,resource,verb,name))
        # Existing deployment admission must still reject use of ESO's token SA.
        policy=next(o for o in build(ROOT/'tenants/portal/foundation') if o['kind']=='ValidatingAdmissionPolicy' and o['metadata']['name']=='portal-runtime-boundary')
        self.assertIn("variables.pod.serviceAccountName == 'portal-runtime'",policy['spec']['validations'][0]['expression'])

if __name__=='__main__': unittest.main()
