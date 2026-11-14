# Automatic identity trigger prototype (unselected)

This offline, default-off Ansible renderer proposes the native trigger for an
explicit platform-owned tenant-identity selection. It changes no existing root.
`platformRevision: null` deliberately prevents rendering current production input.
It does not build an image, provision a foundation or run a Job. Successful render
is not approval, admission, runtime readiness, or customer onboarding.

Run `ansible-playbook ansible/automatic-identity/render.yaml -e @reviewed-inputs.yaml`
only to render a candidate. Required variables are declared without usable defaults
in the playbook. `automatic_identity_render: true` and explicit approved foundation
assertion are required; check mode remains inert. Resource requests/limits have no
assumed sizing default. All names/digests/revisions must come from reviewed inputs,
not guessed IDs. Output contains only references/nonsecret revision metadata.

## Native trigger

Publish the selected context Job directory in enrollment Git, and have a dedicated
platform-owned Flux Kustomization select that exact published path. Its existing
GitRepository must be pinned to the reviewed enrollment commit; independently
verify this prerequisite at activation. The Job name binds the context, platform
and enrollment revisions, executor digest and immutable pod inputs. An unchanged
selection retains the completed Job; it does not repeat each Flux interval.
Changed inputs create a new named Job rather than forcing deletion. No TTL,
force-replacement, automatic failed-Job replay or active-predecessor pruning.
The generated Kustomization waits for native Job completion, not application
readiness. This is a group-foundation stage only: `ReadyGroup` may coexist with
`PendingIdentity`/`PendingFirstLogin`. It must never advertise full tenant Ready.
External Keycloak membership changes do not themselves create a Git revision.

## Executor is a missing prerequisite, not a fabricated image

The explicit image digest must identify a separately reviewed/published image
implementing `/opt/perkforge/bin/reconcile-identity` with the rendered path-only
arguments. That adapter is NOT implemented by this prototype. It must embed exact
clean `/opt/enrollment` and `/opt/platform` sources and verify build provenance
against both revision arguments before invoking the reviewed Ansible stage. The
current operator stage checks published tags over GitHub: a reviewed embedded
provenance path is needed before claiming a network-free executor. No runtime Git
fetch, unpinned package install or global CI activation is proposed.

The adapter must securely stage only the exact parent-writer token from the
read-only Kubernetes projection into private 0600 regular files in `/tmp` (current
helper intentionally rejects symlinks), then remove staged credentials on exit.
Never weaken path guards or put secrets in logs/environment/arguments. Image UID
65532 must own embedded checkouts; set `GIT_OPTIONAL_LOCKS=0`. Confirm native
bash/flock/Ansible/Python/git dependencies and restricted filesystem execution.
The worker has no Kubernetes API token, status writer or Secret read RBAC.

## Foundation and approvals before selection

- Dedicated namespace, worker service account (no API token), registry credential
  delivery, read-only public input ConfigMap, exact parent-writer Secret via scoped
  ESO and trusted CA; no root/attestor credential implicit in this proposal.
- Dedicated platform reconciler identity and reviewed Job management/health rights.
  Existing enrollment-root-writer handles Flux objects only, not Jobs. Creating
  Jobs permits mounting credentials, so this boundary must remain platform-owned.
- Default-deny network with only actual DNS and exact GitLab/Keycloak destinations
  required by implemented stages; no speculative GitHub egress.
- Retained receipt PVC, bounded storage budget, supported storage-worker placement,
  fresh scheduler/surge/I/O preflight. Control node lacks Longhorn CSI; worker2 may
  be busy with household export. No provisional request is proof of headroom.
- Native create-only group helper, source ownership, parent ID, exact custody and
  phase verification must pass independently before live trigger approval.

## Receipts, concurrency and cleanup

Use one stable context lock `/receipts/<context>.lock` across ALL revision Jobs,
not a revision-specific receipt lock. Hold native exclusive nonblocking flock for
the whole adapter operation. Store bounded private receipts by invocation and
retain the latest successful stage plus latest failed-stage evidence; no user
lists or tokens in termination messages. Losing the lock must fail visibly, not
report success. RWO alone does not enforce single-writer access on one node.

No automatic cleanup is implemented. Before later approved cleanup, confirm all
Jobs using the context are terminal, keep source-selected Job and current/last-good
receipts, and remove obsolete Jobs from desired source before deleting them. Never
delete an active predecessor, PVC, lock file, or selected Job to force replay.
Receipt retention/capacity and operator cleanup remain activation prerequisites;
removing a declaration does not delete a GitLab group or revoke users.

Native references: https://fluxcd.io/flux/use-cases/running-jobs/ and
https://kubernetes.io/docs/concepts/workloads/controllers/job/ .
