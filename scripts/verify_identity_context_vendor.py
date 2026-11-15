#!/usr/bin/env python3
"""Compare vendored pure ABI against exact platform Git object. Read only."""
import argparse,subprocess
from identity_context_binding import PROVENANCE,CONTRACT_BYTES
from identity_source_bundle import source
p=argparse.ArgumentParser();p.add_argument('--platform',required=True);a=p.parse_args()
if source(a.platform,PROVENANCE['revision'],PROVENANCE['path'])!=CONTRACT_BYTES:raise SystemExit('Vendored context ABI does not match pinned platform source.')
print('Exact shared context ABI provenance verified.')
