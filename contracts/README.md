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
