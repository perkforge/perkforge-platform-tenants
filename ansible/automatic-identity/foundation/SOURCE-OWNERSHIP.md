# Selected foundation desired state

The normal `offline-enrollment` workflow checks both the finite declaration and
foundation output. `declarations/identity/foundation.json` is disabled by default;
no existing cluster selection includes its generated root. Run
`python3 scripts/render_identity_foundation.py` after an explicitly reviewed
nonsecret selection change, then commit inputs and generated output together.
`--check` detects drift, including extra files; removal needs explicit source
cleanup rather than implicit deletion by the renderer.

An enabled input has exactly `schemaVersion: 1`, `enabled: true`, `network`,
`custody`, `initializer`, and `ownership`. Those values use the existing strict
foundation/initializer/ownership contracts. The ownership foundationSHA256 is
an explicit reviewed object-list digest, not silently recomputed approval. The
sourceRef and two runtime namespaces must match the selected identity declaration.
The generated path is `./generated/identity-foundation/portal`; this historical
single-slot path does not grant Portal authority to another selected context.
Public CAs, exact owned UIDs and provider references are configuration; never put
tokens, passwords, private keys, or issuer receipt contents in these inputs.

`generated/identity-foundation/portal` contains the two Flux definitions and their
admission/network then controls stages. Selecting it requires a separately
reviewed enclosing platform overlay, preserving existing consumers. The existing
platform reconciler must first have the approved exact named adoption authority.
The finite declaration must depend on foundation controls. This helper does not
select a live source, grant permissions, or start any Job.

`bootstrap/identity-foundation/portal-plan.json` is deliberately outside the
selected tree and has no Kustomization. Its root-owned guards and narrowly named
grants require separate security approval and guarded installation. Namespaces,
PVCs, credentials, evidence data, initializer/gate Pods, and native provider state
remain excluded from continuous foundation ownership. This is not a claim of
fully declarative provider bootstrap. Actual-controller SSA adoption, nonempty
issuer-data preservation, policy typechecks and native RBAC denials remain runtime
gates; rendering is not evidence that they passed.
