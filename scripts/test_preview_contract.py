"""Offline proposal-contract consistency; no cluster or identity access."""
import json
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]

class PreviewContract(unittest.TestCase):
    def test_only_existing_reviewable_app_mapping(self):
        contract = json.loads((ROOT / 'contracts/preview-v1.json').read_text())
        self.assertEqual(contract['schemaVersion'], 1)
        self.assertEqual(contract['status'], 'proposal-only')
        self.assertEqual(contract['customerTemplates'], [])
        self.assertEqual(contract['membershipTemplates'], [])
        inventory = json.loads((ROOT / 'enrollment-inventory.json').read_text())
        seen = set()
        for mapping in contract['applicationProfiles']:
            self.assertNotIn(mapping['id'], seen)
            seen.add(mapping['id'])
            path = ROOT / mapping['template']
            self.assertTrue(path.resolve().is_relative_to(ROOT.resolve()))
            doc = yaml.safe_load(path.read_text())
            matches = [p for p in doc['patches'] if p['target']['kind'] == mapping['resourceKind'] and p['target']['name'] == mapping['application'] and p['target'].get('namespace') == mapping['namespace']]
            self.assertEqual(len(matches), 1)
            ops = yaml.safe_load(matches[0]['patch'])
            pins = [op for op in ops if op['path'] == mapping['field']]
            self.assertEqual(len(pins), 1)
            self.assertEqual(pins[0]['op'], 'replace')
            entries = [e for e in inventory['selections'][mapping['selector']] if e['name'] == mapping['application'] and e['namespace'] == mapping['namespace']]
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0]['source']['ref']['tag'], pins[0]['value'])
            context = yaml.safe_load((ROOT / 'clusters/local/kustomization.yaml').read_text())['commonAnnotations']
            for key in ('cluster', 'environment', 'profile'):
                self.assertEqual(mapping[key], context['platform.perkforge.io/' + key])

if __name__ == '__main__':
    unittest.main()
