# First identity provisioner runtime: proposed, not activated

## Boundaries

- Portal-only, explicit tenant identity declaration; no inference from app folders.
- One Flux revision-triggered foundation → attestor → membership sequence.
- No CronJob, continuous synchronization or automatic first-login callback.
- Manual account approval remains on. Pending login/approval requires an explicit
  reviewed retry generation. Empty roster proves no positive membership grant.
- Reuse the maintained IronBank Ansible 14.6.0 image, pinned to
  `sha256:3308322cc09f20a813c00e9087c166a3d97dbb7789c059f1020f3c0b092fdf02`,
  with immutable verified source bundles. Local compatibility and complete three-phase synthetic launcher fixture passed;
  actual cluster deployment and native tenant acceptance remain separate gates.

## One-time native GitLab bootstrap proposal

- Explicitly approved audited toolbox administrative execution, not a persistent
  unrestricted automation token. Revalidate the selected existing administrator
  by immutable OIDC subject/native ID and active state before any write.
- Use installed native `Groups::CreateService` for private top-level `tenants`.
  No adoption of an unreceipted existing path, projects, imports or chat team.
  This service adds the acting human as parent Owner and inherits active default
  integrations: both are material approval consequences, not hidden side effects.
- Create a dedicated parent group access-token bot with `api`, Owner (50), using
  native `ResourceAccessTokens::CreateService`. Its authority extends through the
  entire tenants subtree, not only Portal. Verify non-admin bot, exact parent
  membership, token resource binding, scope and explicit expiry before custody.
- Create the separately approved administrator-owned read-only attestor token
  through native `PersonalAccessTokens::CreateService`, with `read_api` and only
  an explicit `self_rotate` scope only if the runtime approval selects it. This can read broadly
  across the instance; wrapper filters do not reduce native authority.
- Do not mint credentials until the executor and custody path are runnable.
  GitLab expiry dates end at UTC midnight, not 24 hours after issuance. Record the
  exact expiry/effective lifetime; no automatic rotation service is implied.
- Token values flow only through a protected process pipe/in-memory custody
  operation. No command argument, chat output, application log or host plaintext
  copy. Native token creation/revocation can produce audit/account notifications.
- On custody failure revoke only tokens created by this bootstrap, retain group
  and nonsecret failure receipt, and require explicit recovery. Do not delete the
  parent or blindly repeat a potentially successful creation.
- The real Flux foundation, not this bootstrap, creates `tenants/portal`.

## Proposed custody and execution identities

| Consumer | Exact intended custody record | Native authority |
| --- | --- | --- |
| Attestor only | `platform/data/identity/gitlab/tenant-reader-v1` | Disclosed instance-wide read-only GitLab token |
| Writer only | `platform/data/identity/gitlab/tenants-writer-v1` | Non-admin Owner bot for the tenants parent subtree |
| Attestor only | `platform/data/identity/keycloak/portal-membership-reader-v1` | Dedicated client credentials; exact group policies still to be configured and verified |

- These are proposed new record paths, not statements that records exist.
- Initial OpenBao writer identity/authority is unresolved. Prior approval to use
  an unrestricted bootstrap credential for unrelated home alerts does not cover
  these records. Obtain exact informed authorization or establish a supported
  narrow operator first. Never distribute an OpenBao root token to workloads.
- Each namespace gets its own exact-record ESO authentication policy and Secret
  delivery. No wildcard path policy or shared reader/writer credential bundle.
- Writer namespace: `tenant-identity-writer`, worker SA `identity-group-worker`,
  separate GitOps job reconciler `identity-group-reconciler`.
- Attestor namespace: `tenant-identity-attestor`, worker SA `identity-attestor`,
  separate GitOps job reconciler `identity-attestor-reconciler`.
- Writer has no Kubernetes token. Attestor gets a short projected Kubernetes API
  token only for GET/PATCH of the precreated writer-namespace
  `portal-identity-evidence` ConfigMap. No list/create/delete/Secret access.
- Namespace Job-create permission can mount secrets even without Secret verbs.
  Admission must constrain exact phase image, executable/arguments, SA, approved
  Secret/ConfigMap/PVC projections, source/input hashes and worker placement.
  No arbitrary containers, privileged/host namespaces or unapproved token mounts.

## Keycloak gate

- Pinned 26.8.1 supports group-level view and view-members semantics. The target
  realm currently has fine-grained admin permissions disabled; a narrow reader
  is not already available. Enabling and configuring it is a security change.
- Use a dedicated confidential service client with only policies for the three
  canonical Portal leaf groups. Do not substitute broad realm `view-users` or
  `manage-users`; those bypass the intended fine-grained boundary.
- Pinned official 26.8.1 REST recipe, still requiring independently reviewed
  default-off setup implementation before activation:
  1. Create a dedicated confidential OIDC service client with service accounts
     enabled, fullScopeAllowed false; browser/password/implicit flows disabled.
     Record its returned ID
     and exact service-account user ID; reject conflicting existing identities.
  2. PUT the selected realm with only `adminPermissionsEnabled: true`, preserving
     other settings. Discover its newly initialized `admin-permissions` client
     by exact clientId; require exactly one result matching the realm
     adminPermissionsClient field, and record its UUID.
  3. Under that client's `/authz/resource-server/policy/user`, create a uniquely
     named type `user`, POSITIVE User policy selecting only the service-account
     user UUID.
     A Client policy is not a substitute: documented partial view evaluation
     supports User/Group/Role/Aggregated policies, not Client policy.
  4. POST `/authz/resource-server/permission/scope` with type `scope`,
     resourceType `Groups`,
     exactly the three canonical leaf UUIDs in resources, only `view` and
     `view-members` scopes, and the sole owned User policy. Use POSITIVE logic
     and UNANIMOUS evaluation. Empty resources would mean all Groups and must
     fail validation before any request.
  5. Read back exact IDs, policy references, scopes and resources. Check that the
     service account has no broad administrative roles before verifying its
     own read/denial behavior. Retain nonsecret owned-resource receipts; refuse
     foreign names/IDs rather than adopting or overwriting them.
- Dedicated Keycloak client-secret persistence/rotation must be disclosed
  separately from GitLab's dated token expiry. Do not describe the whole setup
  as expiring automatically when only one credential does.
- Recipe source: [pinned Keycloak fine-grained administration documentation](https://github.com/keycloak/keycloak/blob/26.8.1/docs/documentation/server_admin/topics/admin-console-permissions/fine-grain-v2.adoc).
  No legacy group-management-permissions endpoint is used for V2.
- Native Groups view-members also permits user-view for members of the selected
  groups. Their profiles may be readable; this is not a subject-ID-only native
  permission. The observer minimizes output fields but cannot narrow that API
  authority. Disclose this consequence explicitly.
- Acceptance must prove exact group metadata/member reads, denial for unrelated
  groups/users and denial for mutation endpoints. Do not reuse bootstrap-admin credentials
  for routine observation. Canonical group→GitLab role is the selected contract,
  not an inferred conjunction with unrelated realm-role claims.

## Native resource and network gate

- Precreate the exact namespaces/SAs, per-namespace ESO resources, receipt
  ConfigMap with recorded UID, and writer receipt PVC before selecting Jobs.
- Writer phases share one stable context receipt directory and `trigger.lock`.
  Adapter lock remains `gitlab-group.json.lock`; no nested same-lock deadlock.
- Actual mounted ancestry must satisfy strict owner/mode guards. `fsGroup` alone
  may create group-writable ancestors and is not sufficient proof. Any narrowly
  targeted initialization permission change needs explicit approval; do not
  relax guards to accept overflow IDs or writable shared ancestors.
- Proposed egress only: both phases to existing GitLab HTTPS ingress and DNS;
  attestor additionally to existing Keycloak HTTPS and Kubernetes API endpoint.
  Verify exact live ingress/DNAT destinations before admitting policies. No new
  public ingress, broad Internet egress or runtime package installation.
- Fresh placement/resource headroom and concrete PVC sizing remain preflight
  gates. Local runtime compatibility is not proof of cluster scheduling capacity.

## Source and phase sequencing gate

- Select one declared Portal identity input through the normal checked-in
  enrollment build/render path, with deterministic generated resources and a
  CI regeneration comparison. No manual Job substitutes for that integration.
- Bind code release revisions separately from declaration hash/retry generation
  and actual Flux configuration revision; avoid self-referential source hashes.
- Each phase Kustomization spec changes for its attempt, including explicit new
  Job health check and invocation common metadata. Dependency expressions must
  require matching invocation, Ready and observedGeneration==generation; old Ready
  alone is insufficient. Verify the pinned Flux CRD supports those fields.
- Jobs: restart Never, bounded deadline, backoff 0, one completion/parallelism;
  no TTL on a desired completed Job and no automatic recreation/retry loop.
- Foundation writes the exact current-invocation success capsule only after
  native readback. Under the context lock it accepts only the expected previous
  or same current attempt, never an arbitrary stale overwrite.
- Attestor publication uses stable UID/resourceVersion/desired-attempt CAS.
  Admission must prohibit issuer metadata changes; exact-name RBAC alone does
  not protect fields. Writer refreshes and pins complete evidence per operation.
- Preserve explicit Pending, PartialFailure and manual recovery outcomes. A
  successful Job is a phase result, not a claim that every user is onboarded.

## Separate owner decisions, not implicit completion

- Current Portal groups contain no members. Choose a non-admin/test candidate
  separately for positive native membership acceptance, or explicitly accept an
  empty-group pilot. Do not add the platform owner as an ordinary tenant by guess.
- Platform-admin-wide GitLab visibility is not currently synchronized from the
  Keycloak group. Native instance-admin grants are broader than subtree viewing;
  this decision and implementation must not be hidden in the provisioner bot.
- No Portal project/pipeline purpose has been selected. The original native
  project/event integration portion of #334 remains open; an empty group is not
  a pipeline/event acceptance substitute.
