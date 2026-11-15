# Portal identity target profile v1

This is a build-once, explicitly configured supported environment profile, not
arbitrary provider support. Current live rollout remains the Portal pilot. The same pinned executable bundle and maintained image run
in both source fixtures. The alternate fixture is synthetic, not a deployed cluster.
No source change activates a namespace, credential, controller grant or Job.

## Source ownership and normal render

An enabled `declarations/identity/portal.json` must contain the complete literal
`targetProfile` object. Copy and review a profile from `profiles/identity/`; do not
rely on workstation defaults or private-only rendering. The validator in
`scripts/identity_target_profile.py` is the strict versioned schema: missing/unknown
keys, empty selectors, nonliteral/invalid ports and unsupported providers fail.

Commit the sanitized enabled declaration, its full target profile and generated
`generated/identity/portal` resources through the normal PR workflow. Run
`python3 scripts/finite_identity.py`, then `--check`; normal offline CI checks
freshness and source provenance. Select that reviewed Git revision through the
existing enrollment GitRepository and opt-in Kustomization, preserving unrelated
application composition. No enabled declaration is selected by this source PR.

| Profile key | Meaning / allowed values |
|---|---|
| `schemaVersion` | integer `1`, not boolean |
| `apiAudience` | literal HTTPS API token audience; must match target API issuer |
| `dns.namespaceLabels`, `dns.podLabels` | nonempty exact match-label maps, max 8 entries each |
| `dns.port` | DNS TCP/UDP port, integer 1..65535 |
| `ingress.namespaceLabels`, `ingress.podLabels` | nonempty exact backend selectors |
| `ingress.frontendPort`, `ingress.backendPort` | integer target frontend and translated backend ports |
| `api.servicePort`, `api.backendPort` | integer API service and translated backend ports |
| `storage.provider` | only `longhorn-v1`; unknown providers are rejected |
| `storage.className` | explicit target StorageClass name |
| `storage.size` | explicit 1..16 GiB receipt claim, integer `Gi` quantity |

Existing explicit target inputs still supply bounded single-host endpoint CIDRs,
public API/lab CAs, worker hostname, requests/limits, immutable source pins, native
UIDs, canonical identity IDs and custody references. `traefikBackend:true` in the
existing network-input schema is a legacy acknowledgement that the translated
backend rule is required; the profile now defines its selectors/ports, not a
mandatory Traefik implementation. It does not authorize arbitrary broad egress.

The initializer additionally requires `storageProfile` equal to the declaration's
`targetProfile.storage`. It rejects a mismatched class/size/provider before use.

## Support matrix and non-negotiable boundaries

- Supported storage: Longhorn CSI `driver.longhorn.io`, fresh filesystem RWO,
  Retain PV, exactly two healthy RW replicas, explicit worker with CSI, owned
  claim/PV/volume UIDs, held first-consumer gate and confirmed detach. A renamed
  StorageClass is supported only when those actual runtime properties hold.
  There is no generic CSI fallback, chown/root initializer or PSA relaxation.
- Tested source profiles: existing RKE2/CoreDNS/Traefik/Longhorn pilot and a
  synthetic alternate DNS/ingress/API audience/ports/Longhorn class+size profile.
  Native CEL/OpenAPI fixtures validate exact allowed objects and denials for both.
- Fixed reviewed security/runtime ABI: image digest, UID/GID1001, read-only root,
  private0700 receipt directory, no writer API token, isolated reader/writer,
  exact source bytes, bounded TTL/deadline and no retries/polling controller.
  Changing these requires compatibility/security review, not a free-form knob.
- Context naming and provider bindings consume the single reviewed shared ABI; see
  CONTEXT-CONTRACT.md. The current live rollout is still Portal only and each attempt
  is limited to three subjects. Environment portability does not authorize another
  tenant or imply that its provider/credential setup has been performed.

## Compatibility, retry and cleanup

The complete explicit profile is validated before attempt hashing. Only exact
structural equality to the checked-in canonical pilot profile omits the profile
from the historical attempt hash. This one documented compatibility normalization
preserves all existing pilot rendered objects byte-for-byte. There are no implicit
profile defaults or partial matches. Every nonlegacy profile participates in the
attempt hash; changes to any deployment field produce a new immutable attempt.

Never change a selected profile in place to work around a denial. Review the new
attempt and its admission expectations, preserve source provenance and inspect
native defaulting/type warnings before granting creator authority. A changed
storage class/size is **not** permission to resize, replace or adopt an existing
claim. A retained claim must match exactly or the operation stops.

Late first-login/manual approval uses an explicit reviewed retryGeneration and
fresh evidence. Membership release changes only the prepared scheduling gate;
it does not extend the five-minute evidence lifetime. No CronJob, automatic retry,
TTL deletion or force replacement is introduced. Do not delete a completed Job
while still desired in Git. Cleanup first removes its desired reference through a
reviewed source transition, verifies no active predecessor, and retains receipts
and PVC unless separately authorized otherwise.

## Honest GitOps boundary

Phase Jobs, source/input ConfigMaps and dependent Flux Kustomizations have a normal
checked-in deterministic render/CI/selected-Git path. The current declaration remains
disabled until a separate activation PR is reviewed. Bootstrap provider credentials,
actual native IDs, private setup tokens and issuer receipt data never belong in Git.

Foundation admission/RBAC/network/ESO currently use a reviewed operator bootstrap
renderer, **not continuous Flux ownership**. Its nonsecret desired state still needs
a dedicated reviewed Git owner/ordering integration before describing the complete
adopter foundation as GitOps. Provider account/policy creation and retained-volume
initialization are guarded one-time operations, not an ongoing reconciliation claim.
This profile extraction does not hide or resolve those ownership and cross-context
gaps, and does not grant live creator permissions.
