# Original receipt extraction (default off)

`identity_receipt_export.build(declaration, initializer)` emits one exact,
credential-free operator Pod. `identity_foundation.build(..., receipt_export=True)`
adds only that selected Pod's operator-only CREATE alternative. Ordinary render
and all checked-in selected output are unchanged. This is additional admission
authority requiring explicit approval before native policy adoption or Pod creation.
It is not a provider phase, restore, receipt reconstruction, or replay.

The fixed Python command uses the maintained image, UID/GID1001, no fsGroup,
no init, no token or provider credentials and no network-egress label. Both PVC
source and mount are readonly; only `private/<context>` is exposed. Two bounded
regular0600 originals are read under a shared nonblocking existing trigger.lock
(no creation), validated together against exact context/source/attempt/parent,
and transported as original bytes with sizes/SHA256/base64. Historical timestamps
are preserved, not refreshed. This does not reassert fresh provider acceptance.

Before use, operator must verify cluster/PVC/PV/CSI ownership and node bindings,
retention/health, no active or terminating consumer, and no phase scheduling race.
Existing terminal consumer UIDs may be explicitly inventoried, never deleted to
reuse the fresh-volume initializer. Validate native defaulted positive/negative
admission and policy generation/type warnings before create. No grants/network
changes are part of this source.

Capture logs only into private0600 local storage, bind exact Pod UID before/after,
reject malformed/extra/oversize output, and verify SHA256 and original lengths
before use. Do not print receipt bodies to chat or substitute reconstructed JSON.
Delete only this helper using UID precondition, verify absence and unchanged
PVC/PV identities, and preserve any prior attachment. No forced detach/claim
cleanup. This source intentionally contains no live apply/log/delete command.

Tests: `PYTHONPATH=scripts python3 -m unittest scripts/test_identity_receipt_export.py`.
Native CEL uses saved schemas plus `IDENTITY_RECEIPT_EXPORT_FIXTURE=1` and
`IDENTITY_SELECTION_FIXTURE_DIR` pointing to the enabled selected fixture; generic
minimal phase fixtures deliberately lack required provider fields. Cached-image
filesystem tests use explicit Python entrypoint, readonly root/source, no network,
UID1001 and synthetic tmpfs. No live credential or receipt is a fixture.

## Persistent selection

Foundation declaration may explicitly contain `receiptExport: {schemaVersion: 1,
enabled: true}`. Unknown keys/types are refused; absent or false preserves legacy
output. The normal materializer recomputes nothing silently: the complete reviewed
`ownership.foundationSHA256` must be updated to the exact new object list first.
Generated admission and stage hashes change; bootstrap RBAC guards/grants do not.
No helper Pod enters the GitOps selected tree. Keep the phase declaration, bundle,
attempt, Jobs and input bytes unchanged, review generated output and enclosing
foundation readiness hash, then use normal immutable source selection. Disable
the option through source after the one-off extraction if no longer authorized.
