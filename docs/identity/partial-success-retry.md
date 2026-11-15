# Partial-success retry input binding

The optional per-phase `identity_previous_attestation_invocation` is distinct
from the prior foundation invocation. It is either empty or exactly 64 lowercase
hexadecimal characters. All three phase inputs must supply the same explicit
value and the same prior foundation invocation. A nonempty issuer predecessor
requires a prior foundation. Omission in every phase preserves the legacy native
contract and rendered bytes; the renderer never silently inserts an empty value.

The native platform contract binds this field into the invocation and envelope.
The renderer preserves exact input bytes, hashes them into immutable input and
Job identities, and rejects malformed, missing-in-one-phase or conflicting
predecessors. Scheduling hold/release does not change the resulting attempt.

For a successful foundation followed by failed attestation, a reviewed new attempt
can name the actual prior foundation while explicitly expecting an empty issuer.
That expectation is not permission to clear or overwrite a receipt: native
publication still requires the exact owned UID, empty data, desired invocation
and resourceVersion CAS. A published predecessor requires its exact envelope.
Private foundation/group receipts, failed Jobs, source-revision checks and native
IDs are retained. No deletion, replay, authority change or live retry is performed
by this source component. The new platform contract and released bundle must pass
independent review and integration before selecting such inputs.

## Cached maintained-image fixture

`test_context_native_container.py --partial-success-retry --atomic-writer`
requires an explicit platform checkout; `--platform-revision` accepts a full
reviewed commit (legacy default remains unchanged). The scenario uses real local
foundation receipts, exact synthetic GitLab user-lookup 403 with a dotted fake
reader token, and explicit retry generation one/prior foundation/empty issuer.
It checks foreign UID, stale desired invocation, no overwrite and idempotent
membership. The image is cached-only, network-disabled, read-only-root and capped
at 500m/512Mi with synthetic loopback TLS. No live credentials or provider calls.

This proves same-artifact partial-success retry, not cross-artifact migration.
The fixture's synthetic AtomicWriter versions are retained, so it does not prove
credential-mount isolation or kubelet cleanup. Artifact migration, actual native
managedFields preservation and provider acceptance remain separate gates.
