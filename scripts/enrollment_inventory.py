"""Derived source-selection inventory, never deployment or customer-tenant evidence."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import yaml

ROOT = Path(__file__).resolve().parents[1]
# Reviewed roots only; never discover directories or arbitrary repository sources.
SELECTORS = ('local', 'dev', 'local-nextcloud', 'local-nextcloud-portal')
OUTPUT = ROOT / 'enrollment-inventory.json'


def project(objects):
    sources = {(o['metadata'].get('namespace', ''), o['metadata']['name']): o
               for o in objects if o and o.get('kind') == 'GitRepository'}
    entries = []
    for obj in objects:
        if not obj or obj.get('kind') != 'Kustomization' or obj.get('apiVersion') != 'kustomize.toolkit.fluxcd.io/v1':
            continue
        meta, spec = obj['metadata'], obj['spec']
        namespace = meta.get('namespace', '')
        reference = spec['sourceRef']
        if reference.get('kind') != 'GitRepository':
            raise ValueError('Unsupported enrollment source kind')
        source = sources[(reference.get('namespace', namespace), reference['name'])]
        source_spec = source['spec']
        # Public selection metadata only; exclude credentials, status, annotations,
        # policies and arbitrary repository content from the generated artifact.
        entries.append({
            'name': meta['name'], 'namespace': namespace,
            'targetNamespace': spec.get('targetNamespace'),
            'path': spec['path'], 'suspended': bool(spec.get('suspend', False)),
            'source': {'name': reference['name'], 'namespace': source['metadata'].get('namespace', ''),
                       'ref': {k: v for k, v in source_spec.get('ref', {}).items() if k in ('tag', 'commit', 'branch', 'semver')},
                       'suspended': bool(source_spec.get('suspend', False))},
        })
    return sorted(entries, key=lambda item: (item['namespace'], item['name']))


def generate():
    selections = {}
    for selector in SELECTORS:
        rendered = subprocess.check_output(['kubectl', 'kustomize', str(ROOT / 'clusters' / selector)],
                                           env={**os.environ, 'KUBECONFIG': '/dev/null'}, text=True)
        selections[selector] = project(list(yaml.safe_load_all(rendered)))
    return json.dumps({'schemaVersion': 1, 'evidenceType': 'declared-enrollment-selection',
                       'selections': selections}, indent=2, sort_keys=True) + '\n'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    content = generate()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != content:
            raise SystemExit('Enrollment inventory is stale: run python3 scripts/enrollment_inventory.py')
    else:
        OUTPUT.write_text(content)
