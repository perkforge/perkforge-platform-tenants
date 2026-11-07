"""Selected release and independent legacy rollback fixtures, without cluster access."""
import copy
import json
import os
from pathlib import Path
import subprocess
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
LEGACY_COMMIT = '9c48e8d97c596533a806dcb78e33b1932d5ef04a'


class NextcloudCandidate(unittest.TestCase):
    def test_selected_release_evidence(self):
        release = json.loads((ROOT / 'release-evidence.json').read_text())['dependencies']['nextcloud']
        self.assertEqual(release, {
            'repository': 'perkforge/perkforge-tenant-nextcloud',
            'tag': 'v1.1.0',
            'resolvedCommit': '8c8ed5e140049b41e676dffd1c45a953ff1ef23b',
            'publishedAt': '2026-11-07T05:23:39Z',
            'releaseUrl': 'https://github.com/perkforge/perkforge-tenant-nextcloud/releases/tag/v1.1.0',
        })

    def test_ci_verifies_selected_and_distinct_legacy_fixtures(self):
        release = json.loads((ROOT / 'release-evidence.json').read_text())['dependencies']['nextcloud']
        workflow = yaml.safe_load((ROOT / '.github/workflows/nextcloud-candidate.yml').read_text())
        job = workflow['jobs']['candidate']
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        self.assertEqual(job['env']['KUBECONFIG'], '/dev/null')
        self.assertEqual(job['env']['NEXTCLOUD_APP_CHECKOUT'], '${{ github.workspace }}/.inputs/nextcloud')
        self.assertEqual(job['env']['NEXTCLOUD_ROLLBACK_APP_CHECKOUT'], '${{ github.workspace }}/.inputs/nextcloud-rollback')
        self.assertNotIn('NEXTCLOUD_SSO_APP_CHECKOUT', job['env'])
        fixtures = {
            '.inputs/nextcloud': (release['tag'], release['resolvedCommit']),
            '.inputs/nextcloud-rollback': ('v1.0.4', LEGACY_COMMIT),
        }
        found = set()
        for index, step in enumerate(job['steps']):
            checkout = step.get('with', {})
            if checkout.get('repository') != release['repository']:
                continue
            path = checkout['path']
            self.assertIn(path, fixtures)
            tag, commit = fixtures[path]
            self.assertEqual(checkout['ref'], tag)
            self.assertIs(checkout['persist-credentials'], False)
            verification = f"scripts/verify-release-ref.sh {release['repository']} {tag} {commit}"
            self.assertTrue(any(previous.get('run') == verification for previous in job['steps'][:index]))
            found.add(path)
        self.assertEqual(found, set(fixtures))

    @unittest.skipUnless(os.environ.get('NEXTCLOUD_APP_CHECKOUT') and
                         os.environ.get('NEXTCLOUD_ROLLBACK_APP_CHECKOUT'),
                         'both published app checkouts are required')
    def test_actual_releases_preserve_non_image_runtime_values(self):
        selected = Path(os.environ['NEXTCLOUD_APP_CHECKOUT'])
        legacy = Path(os.environ['NEXTCLOUD_ROLLBACK_APP_CHECKOUT'])
        release = json.loads((ROOT / 'release-evidence.json').read_text())['dependencies']['nextcloud']
        for checkout, expected in [(selected, release['resolvedCommit']), (legacy, LEGACY_COMMIT)]:
            self.assertEqual(subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'],
                                                    text=True).strip(), expected)
        for path in ['gitops/base/releases.yaml', 'gitops/base/data-values.yaml',
                     'gitops/clusters/local/data-values.yaml']:
            self.assertEqual(list(yaml.safe_load_all((selected / path).read_text())),
                             list(yaml.safe_load_all((legacy / path).read_text())), path)
        current_local = yaml.safe_load((selected / 'gitops/clusters/local/app-values.yaml').read_text())
        old_local = yaml.safe_load((legacy / 'gitops/clusters/local/app-values.yaml').read_text())
        self.assertEqual(current_local['nextcloud'].pop('configs'), {
            'oidc-origin.config.php': '<?php\n$CONFIG = [\'overwrite.cli.url\' => "https://nextcloud.perkforge.home.arpa"];\n',
        })
        self.assertEqual(current_local, old_local)
        current = yaml.safe_load((selected / 'gitops/base/app-values.yaml').read_text())
        old = yaml.safe_load((legacy / 'gitops/base/app-values.yaml').read_text())
        normalized = copy.deepcopy(current)
        normalized['image'] = old['image']
        for candidate, original in zip(normalized['nextcloud']['extraInitContainers'],
                                       old['nextcloud']['extraInitContainers'], strict=True):
            candidate['image'] = original['image']
        for key in ['extraVolumes', 'extraVolumeMounts']:
            normalized['nextcloud'][key] = [item for item in normalized['nextcloud'][key]
                                           if item['name'] not in {'oidc-ca', 'oidc-secret'}]
        self.assertEqual(normalized, old)


if __name__ == '__main__':
    unittest.main()
