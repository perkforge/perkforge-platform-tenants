# Finite maintained-image runtime candidate

Source-only, disabled by default. No runtime namespaces, permissions, credentials,
image publication, scheduling changes or deployment have been made by this change.

## Real declaration and normal build seam

`declarations/identity/portal.json` is the explicit Portal selection. Running
`scripts/finite_identity.py` produces checked-in `generated/identity/portal`.
Normal `offline-enrollment` CI checks deterministic freshness, source byte provenance
and the opt-in `clusters/local-identity-portal` Kustomize path. No existing active
cluster selection includes that path. Disabled selection renders no objects.

Enabled declarations require a complete approved foundation, exact resource budget,
storage-worker placement, existing receipt UID, fixed credential references and
source bundle. They produce three finite Jobs and three dependent Flux Kustomizations.
There is no CronJob or polling. A late SSO login or manual approval requires a reviewed
new retryGeneration. Unchanged declaration produces the same completed Job; no TTL,
force replacement or garbage collection is configured. Never delete a completed Job
while its desired source remains selected, because reconciliation would recreate it.
Cleanup requires a reviewed source transition after confirming no active predecessor.

`enrollmentRevision` pins executable enrollment source, not the future declaration
commit. `platformRevision` pins the phase adapters. `identity_invocation` binds the
canonical phase contract and explicit retry generation. A separate attempt hash binds
the full declaration including source bytes, input bytes, placement and resources.
Flux's actual artifact revision remains its observed config revision. These are
intentionally distinct; no commit contains its own SHA.

Each Kustomization spec changes with the attempt through commonMetadata annotations
and its exact Job health check. Downstream readyExpr requires matching invocation AND
attempt, upstream Ready=True and observedGeneration==generation. Metadata-only updates
or an old Ready condition cannot satisfy the new dependency. 64-character digests
are annotations, not invalid overlength Kubernetes label values.

## Maintained runtime and source custody

Use only the inspected Iron Bank Ansible14.6.0 manifest
`sha256:3308322cc09f20a813c00e9087c166a3d97dbb7789c059f1020f3c0b092fdf02`.
Native compatibility verified UID/GID1001, Python3.14.8 and Ansible core2.21.6,
bash/flock/sha256sum. The launcher activates `/home/python/python-env` and directs
HOME/Ansible scratch to bounded `/tmp`. No runtime Git or package installation.

`identity_source_bundle.py` reads only an explicit allowlist of regular tracked files
from exact Git commits. It emits content-addressed immutable ConfigMaps for each
isolated namespace, a full file manifest and projection items. CI compares these
bytes against pinned Git objects, not just a user-supplied digest. The launcher checks
the manifest digest and every file before importing code or reading credentials.
The full three-phase candidate is 26 files/about95KB, not an entire repository.

Writer Jobs receive only the group writer and lab CA; the attestor receives its
separate GitLab reader, Keycloak client and narrowly projected Kubernetes API token.
Writers have no Kubernetes/Keycloak/admin-reader token. No human memberships are
created by source rendering. Native admission and exact destination RBAC/network
remain mandatory separately approved prerequisites, not implemented grants here.

The stable issuer receipt ConfigMap is precreated by approved foundation. The source
intent object carries its exact UID and only desired-invocation metadata, never data.
It is not a create/adopt mechanism: native SSA must verify this fails if missing or
UID-mismatched and preserves issuer data before runtime activation. The attestor
CAS-publishes only that object. Writer refresh rereads the fixed projection before
each adapter call and validates exact private bytes, UID/context/source/attempt/age.
Projection is eventual, not instantaneous fencing or cryptographic attestation.

## State and phase status

The retained writer PVC requires owner1001 and private0700 ancestry, not merely
fsGroup permissions. Approved bounded initialization and actual mount preflight remain
necessary. Foundation and membership share the native context `trigger.lock`; inner
adapters retain their separate `gitlab-group.json.lock`. Foundation writes an atomic
current-invocation `foundation-result.json` only after native group success and exact
readback. Existing results permit only current or explicit prior invocation; old
queued attempts cannot replace a newer result. Membership requires the fresh result.

Native Job Complete means the phase ran, NOT that all users are onboarded. Receipts
may report PendingFirstLogin, PendingAccountApproval or NoDesiredMembers. Current
Portal roster is empty; synthetic users never establish actual tenant acceptance.

## Local compatibility evidence, not cluster acceptance

2026-11-14 exact maintained image, network-none, nonroot1001, readonly root, dropALL,
no-new-privileges: full launcher foundation -> isolated attestor -> membership with
synthetic loopback TLS passed for empty roster, then one synthetic developer grant
and idempotent repeat. Explicit newer-attempt foundation CAS and stale projection
rejects made no additional provider calls. Source files mounted read-only; test-only
credential/evidence mounts writable by the local mock, unlike production mounts.

Empty-roster suite29.42s wall,29.78CPU seconds. One-member suite51.43s wall,52.52CPU
seconds, largest child RSS61.75MiB. These suites include retries/negative cases;
per-process RSS is NOT aggregate container peak. Prior group-only sampled container
memory153MB was not a peak measurement. No three-subject full-launcher or throttled
production sizing claim. The existing worker scheduler headroom was65m/110m; do not
silently lower requests to fit. Placement/budget and final300s phase deadline need
explicit actual runtime preflight. No unrelated workload movement is authorized.

## Adopter configuration boundary

Enabled source now requires a complete versioned `targetProfile`; see
[adopter profile schema, examples, support matrix and ownership boundaries](ADOPTER-PROFILE.md).
The reviewed image/security ABI remains intentionally fixed. Context naming consumes
[the shared contract](CONTEXT-CONTRACT.md); current live authority remains Portal-only.
Environment/context source tests are not proof of arbitrary provider support or
a deployed second tenant.
