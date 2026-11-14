#!/usr/bin/env python3
"""CI source authenticity: compare bundle against exact reviewed Git object bytes."""
import argparse,json,pathlib
from identity_source_bundle import bundle
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument('--platform',type=pathlib.Path);a=p.parse_args()
d=json.loads((ROOT/'declarations/identity/portal.json').read_text())
if d.get('enabled') is False:print('Disabled declaration: no source fetch or runtime prerequisites.');raise SystemExit(0)
if not a.platform:raise SystemExit('Enabled declaration requires exact platform source checkout for provenance verification.')
expected=bundle(ROOT,d['enrollmentRevision'],a.platform,d['platformRevision'])
if expected!=d['sourceBundle']:raise SystemExit('Declared source bundle differs from pinned Git object bytes.')
print('Minimal source bundle matches pinned enrollment/platform Git objects; runtime approval is separate.')
