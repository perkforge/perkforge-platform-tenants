import copy
import unittest
from enrollment_inventory import project


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.source = {'kind': 'GitRepository', 'metadata': {'name': 'app', 'namespace': 'config'},
                       'spec': {'ref': {'tag': 'v1.2.3'}, 'suspend': True, 'secretRef': {'name': 'excluded'}}}
        self.reconcile = {'apiVersion': 'kustomize.toolkit.fluxcd.io/v1', 'kind': 'Kustomization',
                          'metadata': {'name': 'app', 'namespace': 'config'},
                          'spec': {'sourceRef': {'kind': 'GitRepository', 'name': 'app'},
                                   'path': './gitops/local', 'targetNamespace': 'runtime', 'suspend': False},
                          'status': {'conditions': [{'type': 'Ready', 'status': 'True'}]}}

    def test_projection_excludes_secrets_status_and_tenant_inference(self):
        result = project([self.source, self.reconcile])
        self.assertEqual(result[0]['source']['ref'], {'tag': 'v1.2.3'})
        self.assertTrue(result[0]['source']['suspended'])
        self.assertFalse(result[0]['suspended'])
        self.assertNotIn('excluded', str(result))
        self.assertNotIn('Ready', str(result))
        self.assertNotIn('tenantId', result[0])

    def test_missing_source_fails_instead_of_inventing_entry(self):
        with self.assertRaises(KeyError):
            project([self.reconcile])

    def test_source_join_is_namespaced_and_unknown_kind_fails(self):
        other = copy.deepcopy(self.source)
        other['metadata']['namespace'] = 'other'
        with self.assertRaises(KeyError):
            project([other, self.reconcile])
        self.reconcile['spec']['sourceRef']['kind'] = 'Bucket'
        with self.assertRaises(ValueError):
            project([self.source, self.reconcile])

    def test_empty_selection(self):
        self.assertEqual(project([]), [])


if __name__ == '__main__':
    unittest.main()
