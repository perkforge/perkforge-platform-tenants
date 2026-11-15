"""Consume exact vendored platform context ABI; never derive authority names here."""
import hashlib,json,pathlib
VENDOR=pathlib.Path(__file__).with_name('vendor')
PROVENANCE=json.loads((VENDOR/'identity_context.provenance.json').read_text())
CONTRACT_BYTES=(VENDOR/'identity_context.py').read_bytes()
if hashlib.sha256(CONTRACT_BYTES).hexdigest()!=PROVENANCE['sha256']:raise ValueError('context vendor integrity')
from vendor.identity_context import derive

def selection(d):
 b=derive(d['context'])
 supplied=d.get('contextDigest')
 if supplied!=b['digest'] and not (d['context']=='portal' and 'contextDigest' not in d):raise ValueError('context ABI digest mismatch')
 return b
