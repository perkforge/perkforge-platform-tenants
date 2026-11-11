"""Offline source/schema checks only; never access a cluster or credential API."""
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import unittest
import jsonschema
import yaml
from test_portal_eso_foundation import ROOT, BUNDLE_SHA, build

STAGE = ROOT / 'tenants/portal/eso-consumers'
CONTRACT = {
    'portal-oidc': ('portal-oidc-existing', 'Opaque', 'tenant-portal/oidc', {'client-secret': 'client-secret'}),
    'portal-registry': ('portal-registry-existing', 'kubernetes.io/dockerconfigjson',
                        'tenant-portal/registry/ghcr', {'.dockerconfigjson': 'dockerconfigjson'}),
    'portal-tls': ('portal-local-tls', 'kubernetes.io/tls', 'tenant-portal/tls', {'tls.crt': 'certificate', 'tls.key': 'private-key'}),
}


def exact_consumer(obj):
    name = obj['metadata']['name']
    assert name in CONTRACT
    target, secret_type, key, fields = CONTRACT[name]
    assert obj == {
        'apiVersion': 'external-secrets.io/v1', 'kind': 'ExternalSecret',
        'metadata': {'name': name, 'namespace': 'tenant-portal'},
        'spec': {
            'refreshPolicy': 'OnChange',
            'secretStoreRef': {'name': 'openbao-tenant', 'kind': 'SecretStore'},
            'target': {'name': target, 'creationPolicy': 'Orphan', 'deletionPolicy': 'Retain',
                       'template': {'engineVersion': 'v2', 'type': secret_type, 'mergePolicy': 'Merge'}},
            'data': [{'secretKey': field, 'remoteRef': {
                'key': key, 'property': prop, 'conversionStrategy': 'Default',
                'decodingStrategy': 'None', 'metadataPolicy': 'None'}} for field, prop in fields.items()],
        },
    }


class PortalESOConsumers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.objects = build(STAGE)
        bundle = Path(os.environ['ESO_CRD_BUNDLE']).read_bytes()
        assert hashlib.sha256(bundle).hexdigest() == BUNDLE_SHA
        crd = next(o for o in yaml.safe_load_all(bundle)
                   if o and o['metadata']['name'] == 'externalsecrets.external-secrets.io')
        assert [v['name'] for v in crd['spec']['versions'] if v['served']] == ['v1']
        schema = next(v for v in crd['spec']['versions'] if v['name'] == 'v1')['schema']['openAPIV3Schema']
        cls.validator = jsonschema.Draft7Validator(schema)

    def test_exact_three_typed_consumers_only(self):
        self.assertEqual(sorted(o['metadata']['name'] for o in self.objects), sorted(CONTRACT))
        for obj in self.objects:
            exact_consumer(obj)
            self.validator.validate(obj)

    def test_reject_scope_ownership_refresh_and_field_drift(self):
        mutations = [
            lambda o: o.update(apiVersion='external-secrets.io/v1beta1'),
            lambda o: o['metadata'].update(namespace='tenant-home-nextcloud'),
            lambda o: o['spec']['secretStoreRef'].update(kind='ClusterSecretStore'),
            lambda o: o['spec']['secretStoreRef'].update(name='openbao-platform'),
            lambda o: o['spec']['target'].update(name='portal-identity-ca'),
            lambda o: o['spec']['target'].update(creationPolicy='Owner'),
            lambda o: o['spec']['target'].update(deletionPolicy='Delete'),
            lambda o: o['spec']['target'].update(immutable=True),
            lambda o: o['spec']['target']['template'].update(type='Opaque'),
            lambda o: o['spec']['target']['template'].update(mergePolicy='Replace'),
            lambda o: o['spec'].update(refreshPolicy='Periodic'),
            lambda o: o['spec'].update(dataFrom=[{'find': {'path': 'tenant-portal'}}]),
            lambda o: o['spec']['data'][0]['remoteRef'].update(key='tenant-other/oidc'),
            lambda o: o['spec']['data'][0]['remoteRef'].update(key='tenants/data/tenant-portal/tls'),
            lambda o: o['spec']['data'][0]['remoteRef'].update(property='other'),
            lambda o: o['spec']['data'][0]['remoteRef'].update(decodingStrategy='Auto'),
            lambda o: o['spec']['data'][0].update(secretKey='other'),
            lambda o: o['spec']['data'].pop(),
        ]
        tls = next(o for o in self.objects if o['metadata']['name'] == 'portal-tls')
        for mutate in mutations:
            obj = deepcopy(tls)
            mutate(obj)
            with self.assertRaises(AssertionError):
                exact_consumer(obj)

    def test_source_properties_are_unambiguous_and_target_keys_stay_exact(self):
        # Provider JSON-path parsing must not be needed for top-level source fields.
        # This is an explicit contract regression, not a simulated provider test.
        for obj in self.objects:
            for item in obj['spec']['data']:
                prop = item['remoteRef']['property']
                self.assertRegex(prop, r'^[a-z][a-z-]*$')
                self.assertNotIn('.', prop)
        registry = next(o for o in self.objects if o['metadata']['name'] == 'portal-registry')
        self.assertEqual(registry['spec']['data'][0]['secretKey'], '.dockerconfigjson')
        for name, dotted in [('portal-registry', '.dockerconfigjson'), ('portal-tls', 'tls.crt')]:
            obj = deepcopy(next(o for o in self.objects if o['metadata']['name'] == name))
            obj['spec']['data'][0]['remoteRef']['property'] = dotted
            with self.assertRaises(AssertionError):
                exact_consumer(obj)

    def test_native_schema_rejects_invalid_shapes(self):
        for mutate in [
            lambda o: o['spec']['target'].update(creationPolicy='Invalid'),
            lambda o: o['spec']['target'].update(deletionPolicy='Invalid'),
            lambda o: o['spec'].update(refreshPolicy='Invalid'),
            lambda o: o['spec']['data'][0]['remoteRef'].update(decodingStrategy='Invalid'),
            lambda o: o['spec']['data'][0]['remoteRef'].pop('key'),
        ]:
            obj = deepcopy(self.objects[0])
            mutate(obj)
            self.assertTrue(list(self.validator.iter_errors(obj)))

    def test_consumers_are_absent_from_every_existing_entrypoint(self):
        paths = [*sorted((ROOT / 'clusters').iterdir()), ROOT / 'tenants/portal',
                 ROOT / 'tenants/portal/foundation', ROOT / 'tenants/portal/eso',
                 ROOT / 'tenants/nextcloud', ROOT / 'tenants/nextcloud/foundation']
        for path in paths:
            self.assertFalse(any(o['kind'] == 'ExternalSecret' for o in build(path)), str(path))


if __name__ == '__main__':
    unittest.main()
