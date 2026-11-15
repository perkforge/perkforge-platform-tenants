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
