# Enrollment preview contract v1 (proposal only)

This source contract is **not activation authority**. It permits offline review
of one existing application's release-pin change, not customer provisioning.
The mapping names the existing integrated Portal selector and its exact source
patch. Cluster/environment/profile are explicit existing selection metadata, not
new isolation policy. The consistency test fails on duplicate/missing mappings,
source targets or divergent inventory pins. Source YAML remains authoritative.

Customer and membership template lists are deliberately empty. Requests to
create customer tenants or change users must fail closed. No name-to-namespace,
Keycloak group/role, quota, admission or native-service mapping is inferred.
Before those operations are implemented, platform owners must review that
contract, immutable identity/collision rules and tenant-scoped revocation.

A consumer receives this contract and declared inventory from the **same reviewed
immutable source commit**. Browser requests cannot choose repository, source
file, namespace, resource kind or patch path. Pin previews compare the expected
old tag to the supplied inventory, reject duplicates/collisions and produce a
semantic proposal, not an applied patch or submitted MR. The repository writer
must later re-read the target at the same base commit and verify the proposed
release, cross-repository compatibility and normal CI before an MR is submitted.
A new release/tag never constitutes deployment or identity readiness.

Run `python3 scripts/test_preview_contract.py`. No API or credential is used.
This draft does not change cluster selection, release versions or generated
inventory, and does not enable any Portal endpoint.

## Explicit tenant identity selection (source candidate)

`tenant-identity-v1.json` is separate from application inventory and preview CRUD.
It explicitly selects canonical platform identity contexts. Its platform revision
is deliberately null until the reviewed adapter is published and selected; live
execution fails closed. It neither creates users nor enables Portal CRUD.

The operator entrypoint is `ansible/reconcile-tenant-identity.yaml`, with the normal
published enrollment tag and protected target input paths. It verifies clean pinned
source, selected context and exact enrollment revision before invoking the platform
adapter under its lock. Group receipt status is propagated as `ReadyGroup` alongside
`PendingIdentity`, never whole-tenant Ready. Failure stops execution; a previous
receipt is not emitted as fresh success. Native identity attestation, membership
execution and invocation from future self-service remain pending separately.

This is an operator-invoked stage, not an unattended controller. Nothing here runs
on an arbitrary Keycloak change or schedules a job. Existing customer/membership
preview templates remain disabled. No repository/project/CI migration is implied.
