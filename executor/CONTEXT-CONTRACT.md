# One context contract, separate environment profile

Source-only downstream integration. No additional tenant is selected and no native
roles, credential records, jobs or provider accounts are created by this change.

## Authority derives from one reviewed source

The canonical pure ABI is platform
`configuration/packages/gitlab/enrollment/identity_context.py` (beneath
`big-bang-bootstrap`). Enrollment vendors its **exact bytes**, not a second naming
implementation. `scripts/vendor/identity_context.provenance.json` records the source
commit/path/hash; normal CI checks the exact Git object against those bytes before
rendering. The module has no provider or cluster I/O. A changed upstream ABI requires
reviewing and updating the pin, vendor bytes and all bound declaration digests.

`context` selects the canonical context. New declarations provide `contextDigest`
and each phase supplies `identity_context_digest`, both equal to the shared ABI
result. The latter is separate from `identity_contract_sha256`, which remains the
canonical tenant policy file hash. No raw namespace, policy, role or KV-path override
is accepted in the declaration. Context-specific namespaces, evidence name,
reconciler identities, global admission names, KC record and ESO auth identities
come from the contract. GitLab platform reader/writer records deliberately remain
shared; their Kubernetes auth roles/SAs are isolated per context.

The existing Portal legacy binding preserves all names. An explicitly legacy Portal
declaration may omit the new digest, preserving its existing input bytes and attempt.
Alternate contexts must supply the digest in declaration and every phase and include
the exact ABI module in the source bundle. Foreign receipt names/namespaces, context
digests, ConfigMap namespaces, initializer context and KC record are rejected.
Writers still have no API/admin-reader/Keycloak token; namespace separation and exact
admission remain mandatory, not replaced by naming or a digest.

## Immutable source and selected Git state

`identity_source_bundle.py --context <context>` reads only that context's tracked
canonical `authorization/contexts/<context>.yaml` at the exact platform commit,
plus the allowlisted phase code and shared ABI. Missing policy files are an error,
not an implicit new tenant. The module bytes must equal the reviewed enrollment
vendor. An older Portal-only platform release may omit the ABI only in the explicit
legacy path; new-digest/alternate rendering cannot use that omission.

The existing `declarations/identity/portal.json` remains the historical **single
selection slot**, not a naming authority. It is still disabled. Its literal `context`
can select another reviewed context; normal deterministic rendering uses the same
legacy directory `generated/identity/portal` and opt-in cluster root. Those directory
names are compatibility paths, not runtime namespace/tenant identifiers. `sourcePath`
must point to the corresponding reviewed generated location. This change does not
select two tenants at once or invent an onboarding inventory. A multi-context source
composition needs a separate reviewed selection/ownership plan.

For a newly selected context, bootstrap its exact canonical IDs/UIDs and approved
custody first, commit the sanitized declaration/environment profile/generated objects
through a PR, verify normal CI and native admission, and select the immutable Git
revision through the existing source. Credentials/issuer payloads stay off Git.
`verify_identity_source.py` compares the complete bundle against the selected pinned
Git objects. The environment profile remains independent of the context contract;
the same built executable works across supported target profiles.

## Initializer and lifecycle

New initializer input includes `context` and `contextDigest`; the selected writer
namespace must match the declaration. Legacy Portal initializer inputs may omit both
for byte compatibility. Claim/PV/volume UIDs, owner, exact storage profile, no other
consumers, held gate, healthy two-replica Longhorn/Retain and detach checks are unchanged.
No old namespace, receipt or claim is adopted when switching context.

Job names retain a readable prefix bounded to46characters plus a hyphen and16hex
characters of the full attempt digest, which binds the entire context. Existing
Portal names are unchanged; maximum-length/shared-prefix contexts are regression
tested with the native Kubernetes label validator.

Retry, membership-held release, receipt freshness, single-writer locks and cleanup
follow ADOPTER-PROFILE.md and MAINTAINED-RUNTIME.md. A new digest changes the attempt;
no conversion of old live receipts or automatic migration is performed.

## Evidence and remaining gates

Offline tests cover the exact legacy Portal golden outputs, an alternate context,
foreign receipt/credential-record/namespace/digest rejection, initializer namespace
ownership and pinned canonical-file bundling. Native CEL/OpenAPI cases run for the
alternate context as well as Portal. These source tests are **not** actual provider
provisioning, a second tenant deployment or live authorization proof.

The cached maintained-image full three-phase fixture also passed for synthetic atlas
under500m CPU/512Mi memory, network-none, nonroot1001/read-only root/dropALL:
foundation, isolated attestation, one developer grant, idempotent repeats, explicit
newer-attempt fencing and stale projection denial. Wall125.93s, child CPU62.82s,
largest child RSS62652KiB (not aggregate container peak). Only synthetic loopback
providers/credentials were used; this is not live tenant or three-subject capacity
acceptance. Reproduce with `scripts/test_context_native_container.py --run
--platform <pinned-platform-checkout> --output <fresh-private-directory>`; it is inert
without --run, never pulls, and generates only test TLS. Final published source pins
and native admission/CSI/provider readiness still need runtime acceptance. Shared
ABI/provider source, issuer custody, ongoing foundation GitOps ownership and exact
runtime consent remain separately reviewed gates. No creator grants are introduced
by this enrollment source change.
