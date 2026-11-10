"""Test selected released app inputs; never configure/deploy or call a live API."""
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import unittest
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'platform.perkforge.io/'


def selected_release(source=None, evidence=None):
    source = source or yaml.safe_load((ROOT / 'tenants/portal/source.yaml').read_text())
    evidence = evidence or json.loads((ROOT / 'release-evidence.json').read_text())['dependencies']['portal']
    assert source['spec']['ref'] == {'tag': evidence['tag']}
    assert re.fullmatch(r'v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', evidence['tag'])
    assert re.fullmatch(r'[0-9a-f]{40}', evidence['resolvedCommit'])
    assert source['spec']['url'] == f"https://github.com/{evidence['repository']}.git"
    assert source['spec']['suspend'] is True
    return evidence


def build(path):
    output = subprocess.check_output(['kubectl', 'kustomize', str(path)], text=True,
                                     env={**os.environ, 'KUBECONFIG': '/dev/null'})
    return [obj for obj in yaml.safe_load_all(output) if obj]


def context(obj):
    return {key: obj['metadata']['annotations'][PREFIX + key]
            for key in ('cluster', 'environment', 'profile')}


def app_selection(parent, app):
    selected = context(parent)
    path = (app / parent['spec']['path']).resolve()
    assert path.is_relative_to(app.resolve())
    assert path.name == selected['cluster']
    objects = build(path)
    assert {obj['kind'] for obj in objects} == {'ConfigMap', 'HelmRelease'}
    root = yaml.safe_load((path / 'kustomization.yaml').read_text())
    assert '../../environments/' + selected['environment'] in root['resources']
    assert '../../profiles/' + selected['profile'] in root['resources']
    for obj in objects:
        assert context(obj) == selected
        if obj['kind'] == 'HelmRelease':
            assert obj['spec']['suspend'] is True
            assert obj['spec']['serviceAccountName'] == 'portal-deployer'
            assert obj['spec']['storageNamespace'] == ('tenant-portal-release' if selected['cluster'] == 'local' else 'tenant-example-portal-release')
            if selected['cluster'] == 'local':
                assert obj['spec']['targetNamespace'] == 'tenant-portal'
        elif obj['kind'] == 'ConfigMap':
            enabled = yaml.safe_load(obj['data']['values.yaml']).get('enabled')
            assert enabled is not True
    return objects


def verify_app_checkout(app):
    release = selected_release()
    head = subprocess.check_output(['git', '-C', str(app), 'rev-parse', 'HEAD'], text=True).strip()
    tag = subprocess.check_output(['git', '-C', str(app), 'rev-parse', release['tag'] + '^{commit}'], text=True).strip()
    assert head == tag == release['resolvedCommit']


def render_local_app(app, enabled=False):
    """Render actual selected release with its ordered Flux values; no API access."""
    verify_app_checkout(app)
    objects = build(app / 'gitops/clusters/local')
    release = next(obj for obj in objects if obj['kind'] == 'HelmRelease')
    maps = {obj['metadata']['name']: obj for obj in objects if obj['kind'] == 'ConfigMap'}
    with tempfile.TemporaryDirectory() as tmp:
        args = [os.environ.get('HELM', 'helm'), 'template', 'portal', str(app / 'bundles/portal/chart'),
                '--namespace', release['spec']['targetNamespace']]
        for i, ref in enumerate(release['spec']['valuesFrom']):
            path = Path(tmp) / f'values-{i}.yaml'
            path.write_text(maps[ref['name']]['data'][ref['valuesKey']])
            args += ['-f', str(path)]
        if enabled:
            args += ['--set', 'enabled=true']
        output = subprocess.check_output(args, text=True)
    return [obj for obj in yaml.safe_load_all(output) if obj]


class EnrollmentReleaseTests(unittest.TestCase):
    def test_ci_release_verification_fails_closed(self):
        workflow = yaml.load((ROOT / '.github/workflows/offline-enrollment.yml').read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(workflow['permissions'], {'contents': 'read'})
        step = next(step for step in workflow['jobs']['build']['steps']
                    if 'scripts/verify-release-ref.sh' in step.get('run', ''))
        self.assertIn('set -euo pipefail', step['run'])

    def test_tag_evidence_and_actual_checkout_agree(self):
        release = selected_release()
        app = Path(os.environ['TENANT_APP_CHECKOUT'])
        head = subprocess.check_output(['git', '-C', str(app), 'rev-parse', 'HEAD'], text=True).strip()
        tag = subprocess.check_output(['git', '-C', str(app), 'rev-parse', release['tag'] + '^{commit}'], text=True).strip()
        self.assertEqual(head, release['resolvedCommit'])
        self.assertEqual(tag, head)

    def test_suspended_enrollment_retains_real_published_app_evidence(self):
        app = Path(os.environ['TENANT_APP_CHECKOUT'])
        # Portal release checks stay scoped to its two roots. Nextcloud's separate
        # paused selector has its own native/render tests and must not activate Portal.
        self.assertEqual({p.name for p in (ROOT / 'clusters').iterdir()}, {'local', 'dev', 'local-nextcloud'})
        for cluster in ('local', 'dev'):
            with self.subTest(cluster=cluster):
                objects = build(ROOT / 'clusters' / cluster)
                source = next(obj for obj in objects if obj['kind'] == 'GitRepository')
                selected_release(source)
                parent = next(obj for obj in objects if obj['kind'] == 'Kustomization')
                self.assertEqual(context(parent), {'cluster': cluster, 'environment': cluster, 'profile': 'il2'})
                self.assertTrue(parent['spec']['suspend'])
                self.assertTrue(source['spec']['suspend'])
                self.assertFalse(parent['spec']['prune'])
                self.assertEqual(parent['spec']['serviceAccountName'], 'portal-reconciler')
                self.assertEqual(parent['spec']['sourceRef']['name'], source['metadata']['name'])
                app_objects = app_selection(parent, app)
                defaults = next(obj for obj in app_objects if obj['kind'] == 'ConfigMap' and obj['metadata']['name'] == 'portal-defaults')
                self.assertFalse(yaml.safe_load(defaults['data']['values.yaml'])['enabled'])

    def test_actual_released_chart_is_disabled_and_matches_physical_boundary_fixture(self):
        app = Path(os.environ['TENANT_APP_CHECKOUT'])
        self.assertEqual(render_local_app(app), [])
        objects = render_local_app(app, enabled=True)
        self.assertEqual({obj['kind'] for obj in objects}, {'Deployment', 'Service'})
        deployment = next(obj for obj in objects if obj['kind'] == 'Deployment')
        self.assertEqual(deployment, json.loads((ROOT / 'scripts/fixtures/portal-v2.0.0-deployment.json').read_text()))

    def test_wrong_activation_state_is_rejected(self):
        for cluster in ('local', 'dev'):
            objects = build(ROOT / 'clusters' / cluster)
            source = next(o for o in objects if o['kind'] == 'GitRepository')
            source['spec']['suspend'] = not source['spec']['suspend']
            with self.assertRaises(AssertionError):
                selected_release(source)

    def test_mismatched_ref_evidence_and_context_fail(self):
        source = yaml.safe_load((ROOT / 'tenants/portal/source.yaml').read_text())
        for ref in ({'branch': 'main'}, {'tag': 'v9.9.9'}, {'tag': 'v0.1.0', 'commit': 'a' * 40}):
            bad = copy.deepcopy(source)
            bad['spec']['ref'] = ref
            with self.assertRaises(AssertionError):
                selected_release(bad)
        parent = next(obj for obj in build(ROOT / 'clusters/dev') if obj['kind'] == 'Kustomization')
        for key, value in [('environment', 'local'), ('profile', 'unselected'), ('cluster', 'local')]:
            bad = copy.deepcopy(parent)
            bad['metadata']['annotations'][PREFIX + key] = value
            with self.assertRaises(AssertionError):
                app_selection(bad, Path(os.environ['TENANT_APP_CHECKOUT']))


if __name__ == '__main__':
    unittest.main()
