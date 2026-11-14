# Isolated identity foundation: proposed source only

This is an offline, default-inert plan. It has not created namespaces, permissions,
credentials, Jobs, volumes or network changes. Runtime authority is still unapproved.
It consumes the exact selected finite declaration, public trust and verified target
endpoint inputs. It does not read Kubernetes or OpenBao credentials.

## Proposed concrete scope

- `tenant-identity-writer`: `identity-group-worker` (no API token/Role), retained
  1Gi Longhorn RWO claim, writer-only destination Secret. Job reconciler
  `flux-system/identity-group-reconciler` can create Jobs and ConfigMaps only inside
  this namespace; admission locks them to exact approved objects. Existing named
  Jobs get GET/PATCH, namespace Job/Pod metadata gets LIST/WATCH for native health.
  No Job delete, force recreation, logs, exec, Secret read or arbitrary workload kind.
- `tenant-identity-attestor`: `identity-attestor`, isolated reader/KC destination
  Secret; `flux-system/identity-attestor-reconciler` has the same constrained Job
  controller pattern. Worker receives only the existing short projected API token
  for GET/PATCH of writer-namespace `portal-identity-evidence`, no Secret/list/create.
- `flux-system/identity-declaration-reconciler`: creates only the three exact
  child Kustomizations under admission, named GET/PATCH/UPDATE, and GET/PATCH of
  the exact precreated evidence ConfigMap. It has no ConfigMap create grant there.
  Admission fixes child service accounts, source, path, health and dependencies;
  remote kubeConfig, decryption, post-build substitution and patches are denied.
- Three dedicated ESO identities/stores: writer, reader and Keycloak. Exact record
  paths/properties are explicit inputs, matching the separate setup proposal.
  Destinations are CREATE-ONLY empty placeholders and Merge/Retain consumers.
  ESO receives only named Secret GET/UPDATE/PATCH, its own TokenRequest and named
  status resources. No Secret CREATE/DELETE/LIST. OpenBao policy/role creation and
  initial operator custody authority are separate, not configured by this renderer.
- Public lab CA is source data, rendered into each destination as `lab-ca.crt`,
  not assumed to exist in secret records. Public API CA is also an explicit input.
  Existing ESO-controller network reachability to OpenBao is a preflight requirement;
  writer and attestor workloads get no OpenBao access.

## Fail-closed native admission and network

Eight VAPs and bindings use failurePolicy Fail and Deny. Job templates and actual
controller Pod creation must match exact executable image/command/arguments,
source/input bytes, projections, worker placement and security profile. Extra
containers, hooks, probes, env injection, host namespaces, raw host volumes,
container user overrides and priority escalation are denied. In particular a
terminationMessagePath pointing at a credential cannot leak it into Pod status.
Pod defaults allowed are explicit; actual server-default/PSA checks remain required.

Code ConfigMaps use ordinary UTF-8 `data`, not `binaryData`: exact string comparisons
work consistently in pinned native CEL schema checking and evaluation. The native
VAP evaluator's unstructured binaryData representation differs from its bytes type
schema. The still-inactive source format was corrected rather than bypassing types.
Manifest hashes and projected executable bytes are unchanged. No source bundle is
live, so no in-place immutable ConfigMap migration has occurred.

The two namespaces are restricted PSA and default deny ingress/egress. Only existing
CoreDNS selectors UDP/TCP53, exact supplied ingress host CIDRs TCP443 and the verified
RKE2 Traefik selector TCP8443 are proposed; attestor additionally gets exact API host
CIDRs443. No Internet wildcard/new ingress. Traefik is a shared L4 destination: this
is not HTTP-path isolation. Exact trusted-TLS origins remain enforced by adapters.
Fresh DNS, DNAT, source labels and API audience evidence are required before use.

## Required ordered activation, never one blanket apply

The renderer emits individually named **planning artifacts**, no runnable Kustomize
root or apply command. A reviewed future activation must:

1. Verify cluster identity, current target endpoints/capacity/household I/O, runtime
   approvals and exact source manifests. No borrowed permission from prior tasks.
2. Create exact isolated namespaces and stable evidence CM through the approved
   foundation owner; record its real UID and existing labels. Do not invent a UID.
3. Render that UID/attempt into source intent and admission. Apply/verify policies
   before granting the Job/ConfigMap creators or releasing any credentials.
4. Precreate exact empty Secret destinations **create-only**, refusing any foreign
   existing data/ownership. Never apply empty Secret data over a populated target.
5. Establish narrowly approved Bao auth and ESO delivery, verify payload keys and
   issuer/writer separation without printing values; confirm actual permission
   denials. Existing `Merge/Retain` patterns are reused, not an activated claim.
6. Verify private receipt ownership, scheduling and source bundle bytes before
   selecting Jobs. No root/chmod/PSA relaxation is implicit. A possible safer
   initialization is a restricted UID1001 helper creating an owned0700 child on the
   fresh fsGroup-writable claim, then fixed subPath mounting only that private child.
   The default-off profile proposal below defines the boundary; no executable helper
   or initialization is authorized or selected by this change.
7. Select reviewed source only after native SSA and server-default tests below pass.

## Stable receipt native SSA test design

Local CEL cases prove logical boundaries, not actual API server field management.
Before activation, use a separately approved isolated fixture or the bounded exact
precreated object with captured UID/resourceVersion/data hash:

- Apply the metadata-only desired-invocation intent using the actual dedicated
  field manager and impersonated declaration identity, initially server dry-run.
- Assert UID preserved and issuer-owned data bytes/hash unchanged. There must be no
  force-conflicts or transfer/adoption of the issuer data field manager.
- UID-mismatch UPDATE must fail; CREATE of missing evidence must fail both the
  absence of declaration create permission and admission's UPDATE-only boundary.
- Issuer-only data PATCH succeeds; issuer metadata/desired-invocation changes fail.
  Declaration attempts to erase or replace data fail. Unrelated actor fails.
- Actual SSA success must be read back before claiming preservation; dry-run is not
  a persistence test. Cleanup must remove only clearly owned fixture objects and
  preserve the real evidence object. No such native test has run for this candidate.

Code/CA ConfigMaps are immutable. Trust rotation or a new executable/declaration
requires reviewed new policy/source before selecting that attempt. Cleanup of old
completed Jobs requires source retirement plus explicit owner action; controller
roles intentionally cannot delete/replay them.

## Default-off private receipt initialization profile proposal

`private-receipt-profile.yaml` is deliberately not a Kubernetes object and is not
consumed by the renderer. A future reviewed helper would mount the exact fresh
claim at `/volume`, as UID/GID1001 with fsGroup1001, no API token, network access,
capabilities or writable root. It creates only `/volume/private` with mode0700,
using exclusive creation and no symlink traversal. The helper must fail if that
path already exists, any unknown contents exist, the claim/PV UID differs, or
another Pod mounts the claim. A real empty filesystem-created `lost+found` may
be allowed only after bounded readable/no-symlink/empty verification, never
recursive permission repair. It writes and reads back only its own bounded marker,
verifies owner1001 and mode0700, then removes that marker. No chmod/chown of volume
root, existing files or unrelated children is permitted.

Success requires helper Pod UID-guarded cleanup, absent PVC consumers and actual
CSI detach/readback. Failure retains the claim and reports the exact boundary;
there is no deletion/recreation fallback. Later writer Jobs would mount only fixed
`subPath: private` at `/receipts`; the existing strict ancestry checks must pass
inside the actual image before any provider credentials are delivered. Current
finite Job/admission source has **not** been changed to that mount, so this proposal
cannot silently activate it. A separately reviewed exact profile change and native
permission/storage preflight are required. Resource values remain the declaration's
explicit provisional budget, not a claim that current worker capacity fits.
