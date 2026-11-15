# Adopt existing foundation into trusted platform Git (source only)

Nothing here grants permissions or applies resources. The disabled CLI consumes the
exact reviewed `identity_foundation.build()` object list plus its canonical JSON
SHA256. It does not implement another context naming contract, infer native IDs,
read credentials, or install a controller. Generated output is a **split adoption
plan**, not a runnable blanket apply. Keep the current Portal/Nextcloud enrollment
consumer unchanged; select these new roots explicitly from trusted platform Git.

## Ownership split

- Root bootstrap: precreated namespaces, retained PVC identity/initialization,
  credential placeholders and pull credentials, native provider IDs, OpenBao
  setup and ESO roles, and **the two new exact-RBAC guard policies**. These do not
  become platform-controller writable. No Secret contents belong in source.
- Platform admission stage: existing eight exact VAPs/bindings plus the four
  network policies. It becomes Ready only when each VAP's observed generation
  matches and native type-check warnings are empty.
- Platform controls stage: the exact existing SAs, eight Roles/Bindings, public
  CA ConfigMaps, SecretStores and ExternalSecrets. It depends on admission Ready.
  ESO remains Merge/Retain and exclusively owns credential payload fields.
- Enrollment declaration/worker stages remain separate; evidence payload belongs
  only to the attestor. Do not include the evidence CM, kube-root CA, empty Secret
  templates, initializer Pod/gate, or source/attempt Job objects in foundation
  adoption. Stable provider state and receipts are not desired empty templates.

`reconciliations` and `stages` are proposed artifacts to commit at the selected
platform-owned path. Their source must be immutable/pinned by the enclosing
platform selection. This generator does not change existing Flux roots. After
migration, the declaration Kustomization must depend on controls Ready as well as
explicit acceptance of initialization and issuer-receipt preservation; this plan
never releases Jobs itself. Bootstrap identities are not tenant-controlled.

## Minimal new authority is still consequential

The plan proposes named `get,patch` only on **precreated** objects. No create,
delete, Secret read/write, logs/exec, wildcard, TokenRequest or provider access is
given directly to the platform reconciler. Missing resources stop reconciliation;
recreation, especially of a UID-bound receipt/PVC, requires explicit bootstrap.

Seven exact Roles additionally need `bind,escalate`: writer group-reconciler,
receipt-intent, evidence-issuer and writer ESO; attestor reconciler and its two
ESO Roles. Native checks confirmed the platform identity lacks their underlying
Job/ConfigMap/evidence/Secret permissions. The control-namespace declaration Role
contains only existing Flux Kustomization rights, so it receives no new
bind/escalate exception. Verify that underlying authority again on another
installation; the exception is a prerequisite, not an inferred universal fact.

Named escalation is **not harmless**: absent the root-owned guards it permits any
rules in those names and binding could redirect recipients. The guards enforce
fixed rule lists, exact roleRefs and exact service-account subjects, and reject
GC ownerReferences/finalizers. Install and type-check/bind them as root **before**
the ownership grants. The generated grant names and the two guard policies are
not themselves included in platform write permissions. New authority templates
need a separately reviewed root guard update before reconciliation can change them.

This is not isolation from malicious trusted platform Git. The platform still
maintains the existing workload admission policies, network and Flux selection;
that is substantive security authority. Protected source review and its existing
root-trust boundary remain necessary. The RBAC guards do not make platform Git
untrusted or prevent all abuse of its other already-approved capabilities.

## Native SSA adoption gate

1. Capture exact cluster/object UIDs, resourceVersions, specs and managedFields.
   Verify all selected objects exist with the expected ownership; do not adopt
   merely by matching names. Exclude status and native defaults from Git.
2. Dry-run exact source under the actual Flux service-account identity and field
   manager, then verify controller ownership labels and field conflicts. Native
   RBAC anti-escalation applies to ordinary RoleBinding updates too.
3. `force:false` disables replacement behavior; it is **not** proof that Flux SSA
   will avoid force-conflicts. Stop on unexplained ownership transfer. Never strip
   managedFields or broadly force an adoption. Same-value ownership migration
   must be explicit and verified, including the controller's bookkeeping labels.
4. Retain `prune:false`; exclude namespace/PVC/Secrets/evidence data from the new
   inventories. Confirm no UID change, no payload data ownership transfer, no Job
   replay, and no unexpected resource additions or removals.
5. Verify exact-template positives and changed-role/subject negatives under actual
   admission before releasing creator identities. Prove real nonempty issuer data
   survives the declaration controller's SSA. Membership stays held until that
   succeeds. Source/policy release cannot extend the five-minute receipt TTL;
   expired evidence requires an explicit new attempt.
6. After deliberate adoption, confirm Flux drift correction on an approved harmless
   nonsecret field. A passing offline fixture is not a live reconciliation claim.

For an alternate context, pass its already-rendered exact object list and selected
namespaces. Tests prove that handoff, not a new tenant naming ABI. Initial scope
remains the eight-role design; changed role count or delegated authority fails closed.

## Bounded retry-name authority (separate live approval required)

The two reconciler Roles retain fixed six-rule authority. Their exact phase sets
are frozen from the reviewed rendered foundation: foundation+memberships in writer,
and attest in attestor. Only Job/input names may change to the same context/phase
prefix plus 16 lowercase hexadecimal characters; input names must equal the Job
name plus `-inputs`. The writer's two phases must share that attempt suffix. Each
Role permits exactly one `identity-source-` name with 20 lowercase hexadecimal
characters. No extra names, foreign prefixes, wildcards, verbs, resources or
subjects are permitted. All other six Roles and all eight bindings remain literal.

This is an expansion from one attempt's object names to future names inside that
fixed shape, not a claim of unchanged object-name authority. Root must explicitly
approve and install the changed guards. Once installed, ordinary retry/source-name
changes no longer need another root guard edit, provided authority and context
shape remain unchanged. Exact workload/ConfigMap admission must still reconcile
first. Those policies are controlled by trusted platform source; the structural
RBAC guard does not independently approve future executable content. It does not
atomically compare attempts across separate Role objects; the generated current
foundation and ordered reconciliation coordinate that state.

Both foundation Kustomizations carry the current foundation SHA in their spec's
commonMetadata annotations. Controls requires admission's matching SHA, current
observedGeneration and Ready=True, preventing an old Ready status from satisfying
a new source expectation. This is sequencing, not an atomic multi-resource
transaction. Existing jobs/receipts are not deleted and no retry is auto-triggered.
The five-minute evidence lifetime and explicit membership-release gate remain.

Offline tests evaluate future retry Roles against the original guards, deny
foreign/mixed/extra names and permission drift, and evaluate stale hash/generation
and non-Ready dependency cases. Actual GitOps reconciliation, field ownership and
live denial acceptance remain separate gates; source tests alone do not establish
that generic retries are operational.
