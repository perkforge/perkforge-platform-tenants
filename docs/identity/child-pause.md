# Declarative child pause before an executable transition

`phasesSuspended` is an optional strict boolean on an enabled context declaration.
It is a scheduling gate, not a provider operation or retry identity. Omission
preserves the previous render byte-for-byte. `true` requires
`membershipReleased: false` and renders `suspend: true` on all three child Flux
Kustomizations. Explicit `false` renders `suspend: false` on foundation/attest;
membership remains suspended until its independent release gate is true.
Explicit false matters when resuming an SSA-owned true field; do not rely on
omission to release a hold.

The field is excluded from the attempt digest, exactly like membershipReleased.
Jobs, Pods, inputs, source bundles, credentials, resource requests and provider
invocation remain unchanged when only this gate changes. Admission accepts only
the selected exact child suspend state; no Role, subject or wildcard expands.
The same contract applies to Portal and other supported context ABI selections.
Absent remains the compatibility default, not a safe resume operation after a hold.

## Ordered adopter/GitOps sequence

1. Keep the current executable, provider invocation, retry generation, bundle,
   Jobs and inputs. Review a source stage selecting `phasesSuspended: true` and
   `membershipReleased: false`, with its exact regenerated admission/hash. The
   parent must reconcile this reviewed child-pause stage; a suspended parent
   alone cannot pause already existing independent children.
2. Verify all three exact child UIDs have suspend true and have reached the
   pinned controller's suspension branch after their latest generation changes.
   Recheck controller/leader continuity and workload state. Suspension does not
   cancel a running Job or an in-flight reconciliation. Stop if any active
   workload remains; no deletion, restart or arbitrary timeout is authorized by
   this flag. A failed backoffLimit=0 Job remains retained and is not retried.
3. Only after quiescence, select the reviewed corrected executable/release and
   its new content-addressed bundle, explicit provider attempt/predecessor and
   policies while keeping **all children held**. Validate provenance, source
   freshness, native shape/readiness and retained receipt ownership separately.
4. Select stage A with explicit `phasesSuspended: false` and
   `membershipReleased: false`. Foundation/attest may run; membership stays held.
   Release B only through the existing independent evidence/freshness/ownership
   acceptance gates. Neither a pause nor a successful render is completion proof.

All sourceRef consumers must be audited before each shared-source revision
change. The first pause stage must not already select a new executable: child
reconcilers can observe source updates independently of their parent. Preserve
both old-attempt pause and later new-artifact held stage as immutable reviewable
ancestors. This document and generic renderer do not select a live stage, grant
permissions, mint credentials, delete a Job or automatically retry a provider.
