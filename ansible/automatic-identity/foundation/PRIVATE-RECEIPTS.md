# Private receipt initialization: implemented source, not activated

This default-off operator workflow creates only a fresh private child on the exact
new retained 1Gi Longhorn claim. No cluster execution has occurred. It reuses the
reviewed Alloy WFFC preflight pattern (platform PR459): exact claim UID first,
held restricted first consumer, native binding and replica checks, UID-precondition
cleanup, and detach/no-consumer proof. It never changes root ownership or PSA.

## Inputs and ordering

`scripts/private_receipts.py` is inert without `--render` or `--execute`.
`--render --inputs FILE` emits a source ConfigMap, initialization inputs, empty
operator release gate and restricted helper Pod. The exact input keys are
`clusterUID`, `claim`, `claimUID`, `pv`, `pvUID`, `volumeHandle`, `node`,
`pullSecret`, `operatorUser`. Use null PV fields before WFFC binds. Real cluster,
claim and authenticated operator identities must be verified, not invented.

Pass these same inputs to the foundation renderer's optional `--initializer FILE`
to include exact helper admission before any helper/source creation. No broader
worker permissions are added. Network egress now selects only actual phase Pods;
the initializer has no phase label, API token, credentials or network allowance.
The existing foundation operator, not worker/reconciler, runs this bounded step.
Its required operation batch includes creating the exact three ConfigMaps/Pod,
reading node/claim/PV/Pod/Longhorn engine-volume and CSI metadata, patching the sole
release gate, reading only initializer output and UID-precondition helper deletion.
These permissions and execution remain unapproved; this source grants none of them.

`--execute` first verifies cluster/PVC ownership and fresh filesystem provenance
(no restore/clone source), and absence of every other namespace Pod mounting the
claim, including terminated Pods. ConfigMaps and helper are create-only: an existing
object stops execution rather than adoption. The helper mounts but does not inspect
or initialize the filesystem until its fixed projected gate arrives (maximum180s).
The operator proves the actual Bound claim→PV UID→Longhorn CSI handle, the intended
node/helper UID and exact reviewed spec, healthy attached two-replica volume and
exact active engine with two RW replicas. It rechecks consumers, then uses a
UID/resourceVersion JSON-patch gate. The gate binds helperUID, claimUID, PVUID,
volume handle and source hash. The helper cannot query Kubernetes itself.

The fixed maintained Ansible image runs Python directly (overriding its default
Ansible entrypoint), UID/GID1001, no capabilities, readonly root and no API token.
Budget stays requests100m/256Mi, limits500m/512Mi, deadline300s. Scheduling and
household I/O must be checked again at execution; this is not permission to stop
or postpone any copy. Current worker2 reservation fit is narrow, not spare capacity.

## Private mode and persistence

Kubelet initially establishes the volume's fsGroup root. Helper and writer Pods
use `fsGroupChangePolicy: OnRootMismatch`. Before writing, helper requires root
GID1001 and matching group-rwx/setgid bits, so subsequent writer mounts should not
recursively reopen the private child. This still requires actual CSI/kubelet proof.
It exclusively creates `private`, then fchmods **only that newly created directory**
to0700 to remove inherited setgid. No chown, volume-root chmod or foreign-path repair.
Foreign contents, existing private path, symlinks and unreadable/nonempty lost+found
fail closed. Empty readable real lost+found is allowed. The bounded marker is
fsynced/read back/hashed and removed, including injected write-following failures.

Foundation and membership Job mounts are now fixed `subPath: private` at `/receipts`.
Admission binds that exact subPath and rejects overrides. No mount of the parent
is exposed to writer code; the existing strict ancestor guard remains unchanged.

## Cleanup, failure and acceptance

The operator checks bounded initializer output, deletes only the exact helperUID
using native DeleteOptions in `finally`, then proves no consumers/CSI attachments,
Longhorn detached state and unchanged claim/PV/volume identities. Cleanup also runs
on failed initialization. Claim, private child and source/gate artifacts are retained;
there is no PVC deletion, regeneration, automatic second execution or fallback.
A partial private child intentionally blocks retry pending explicit inspection.
A cleanup error is a failure, never a success claim.

Verified offline: 3 operator guard tests (WFFC binding/CAS/foreign consumers and
cleanup), 4 actual maintained-image filesystem cases, and actual fixed-path gated
entrypoint on rootless synthetic bind storage returned owner1001/group1001/mode0700,
marker removed. Host IDs are user-namespace mapped, not cluster ownership proof.
Native CEL/OpenAPI verifies exact helper positives and injected-image/command/gate
negatives alongside existing phase boundaries. No provider credentials used.

Still required before activation: independently reviewed exact source, approved
operator/admission batch, actual server default/SSA behavior, current scheduling
and household load decision, private child ownership across real subsequent mounts,
then existing zero-roster three-phase acceptance. No lossless/onboarding-complete
claim follows from this storage test.
