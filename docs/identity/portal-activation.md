# Portal finite onboarding selection

This source selects the approved Portal pilot only. It does not deploy by merging:
the live platform root must explicitly select an independently reviewed enclosing
overlay and immutable enrollment commit after native preflight and the remaining
security approvals. Existing Nextcloud/Portal application enrollment is unchanged.
No CronJob, periodic synchronization, project/repository migration or image build
is introduced.

## Immutable executable provenance

- Platform release v0.47.0: `b904017158100944a81129899e8fc64a3ed976b8`.
- Enrollment release v2.8.0: `5621e9b05bd94566c1bfdc6bcf8b75b0404e8ff0`.
- Maintained IronBank Ansible image remains pinned by its existing SHA256 digest.
- Selected minimal source bundle: 27 files, 98,834 bytes; manifest SHA256
  `43bad232454e5fb0698b417270dfbd329efa64cef34862c98af97dba0a311aaa`.
- The normal CI checks actual Git object bytes against those pins. Operator-only
  render/admission/ownership changes after these releases do not replace the
  executor. Artifact revision, desired-state revision and invocation are separate.

Build-once proof covers the maintained image and executable module bytes, not an
identical full ConfigMap across tenants: selected canonical context policy,
revision metadata and resulting manifest may differ. The supported storage
profile is explicitly Longhorn, with two healthy RW replicas, retained ownership
and detach checks; unsupported providers fail closed.

## Source ownership and staged selection

`declarations/identity/portal.json` owns the selected context, public native IDs,
profile, exact artifact pins and attempt. `foundation.json` owns public network/CA,
custody references, exact owned claim identity and reviewed foundation digest.
Generated output is checked for freshness in normal CI. Bootstrap plans are NOT
included in either generated Kustomization.

Prepublish and review both immutable source stages before any attestation:

1. Stage A keeps `membershipReleased: false`. Platform Git first reconciles
   admission/network, then controls, then the finite declaration. Controls and the
   declaration must depend on the exact current foundation digest and observed
   generation, not an old Ready condition. Initial namespaces, existing evidence
   UID, retained claim, credential custody and root-owned guards/grants remain
   guarded bootstrap exceptions, not fictitious continuously managed secrets.
2. After actual current-attempt attestation, prove metadata-only SSA under the
   real declaration identity preserves nonempty issuer data and UID. Only then
   select reviewed stage B, changing membership suspension/admission expectations.
   Job names, inputs and executable bytes remain identical across A/B.
3. Five-minute evidence freshness is enforced. If source/policy readiness or SSA
   takes too long, do not unsuspend stale evidence as acceptance: use a new
   explicitly reviewed retryGeneration with previousInvocation and fresh phases.
   There is no automatic retrigger after first login/manual approval.

Do not add commonMetadata to the enclosing declaration root: it would also alter
the exact evidence ConfigMap metadata. Fence that root using its dependency
expression with the reviewed literal foundation digest instead.

## Runtime gates, limits and cleanup

No helper or Job has been started by this source preparation. Before starting,
verify exact cluster/namespace/evidence/PVC identities; native defaulted admission
positives/denials; narrowly scoped controller/issuer authority and SSA ownership;
current provider/ESO readiness; and fresh scheduler plus worker-2 disk load while
the independent HGST copy continues. Do not interrupt that copy implicitly.
Notify Corey immediately before the initializer Pod and before the first Job,
using the final generated names and namespaces.

The restricted UID1001 initializer alone establishes the private 0700 subdirectory
on the owned fresh claim. It requires the held-first-consumer gate, exact PV/CSI
and two healthy replicas, bounded owned-marker verification, no foreign content
or competing users, UID-conditioned helper removal and detach proof. No root,
chown, host/CSI changes, PVC deletion or adoption is authorized by this source.
Each phase requests 100m/256Mi, capped at 500m/512Mi, with a sequential 300s deadline and backoff 0.
One-context synthetic execution is not a production load or scheduling guarantee.

The writer never receives admin-reader, Keycloak or Kubernetes credentials.
Attestor reads only selected identity scope and updates its exact owned evidence
object. Membership remains limited to reviewed receipt-owned subjects, with a
three-subject union cap. Recovery_verified records the prior November 5 recovery
proof and separately observed enabled/unlocked local route; current recovery
password validity and a fresh login were NOT tested or asserted.

PendingFirstLogin/PendingAccountApproval is not MembershipReady. Native positive,
foreign-denial and actual membership/removal outcomes must be recorded separately.
Retain evidence and claim on failure; do not automatically delete Jobs or restart
older attempts. Any credential revocation, authority removal or provider rollback
needs its scoped approved operation. This is not continuous sync or lossless audit.
