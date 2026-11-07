# Nextcloud pilot enrollment candidate

The separate `clusters/local-nextcloud` private-image candidate pins published app
v1.1.0 at 8c8ed5e140049b41e676dffd1c45a953ff1ef23b; release evidence is recorded
in release-evidence.json and checked before CI checkout. It preserves the enabled
database/web releases and guarded non-root same-Pod cron runner, selects the
digest-pinned private SSO image, and adds its fixed read-only OIDC input mounts.
This activation candidate requires the accepted disabled rollout, scoped sidecar policy and bounded same-Pod
pre-activation checks before promotion. The preceding data-only acceptance uses published
enrollment v1.2.1 and app v1.0.1. Complete that gate and public CA delivery before
selecting this web stage. Existing local/dev roots and the live
platform do not select it. Shared defaults remain paused/UNCONFIGURED. No branch
or fabricated release is a deployment input. Foundation is
operator-owned and separately applied from a clean published enrollment checkout;
the tenant child cannot reconcile its own authority.

**Do not promote this candidate before all three runtime inputs exist:** the
read-only GHCR pull Secret `nextcloud-registry-existing`, OIDC client Secret
`nextcloud-oidc`, and public CA ConfigMap `nextcloud-oidc-ca`, all in
`tenant-home-nextcloud`. None is created by this pin change; the published app
requires these references and cannot start correctly without them. Credential
creation/delivery and live policy application require separate approval. Follow
[the delivery and registry prerequisites](sso/README.md) and verify node-side pull
of the exact digest before eventual live selection.

Merge and publish the reviewed enrollment change first, then verify its actual
published tag before preparing a separate platform pin change. Never fabricate a
future enrollment tag. This PR changes no platform selection and does not deploy
or activate native SSO. Issuer egress application and Nextcloud's private-HTTP
setting remain separate approval and positive/negative acceptance gates.

The Nextcloud-only selector contains no Portal resources. Its sources and child
are enabled only after separately reviewed platform promotion; no live change is
made by editing this folder. It removes the source Secret reference because the app repository
is public. The shared base retains an optional scoped read reference for a future
private repository; the current public path requires no Git token. Do not select
the existing `clusters/local` root to activate Nextcloud: that root enables Portal.
Before deployment, reverify the recorded app release, publish the reviewed
enrollment selection, and add a matching published
platform stage pointing its enrollment parent at `./clusters/local-nextcloud`.
Preserve the current GitLab/runner stage. The platform's existing enrollment
prerequisite gate is tied to the old default local root and needs a reviewed
selected-root update before use; do not bypass it or apply Portal's path instead.

The guarded same-Pod activation originated in app v1.0.4 and is preserved in
v1.1.0. The pilot uses
32Gi files plus 16Gi PostgreSQL on the accepted two-replica longhorn-dedicated
tier (platform v0.19.0). Storage expansion requires coordinated app values,
admission and quota review before household import. No single-excess claim is
allowed here. One web process, one database instance and serial cron are an empty
pilot, not application HA or accepted household load. Both prefer worker-2; worker-1
remains eligible. Before selecting this candidate, accept initialization, trusted HTTPS, synthetic retention and bounded same-Pod execution with the released policy. Verify matching container/volume SELinux labels and two successful background runs after the controlled rollout.

## What the foundation owns

Corey retains full platform administration. This foundation adds no ClusterRole,
ClusterRoleBinding, OIDC authentication change or replacement of existing owner
bindings. Its policies scope the tenant's resources; the owner still controls
those policies and can perform reviewed recovery. The reconciler/deployer identities
are limited automation accounts, not Corey's personal administrator identity.
Nextcloud's initial application administrator is separately bootstrapped from its
operator-delivered admin Secret and must be verified in the app. No Keycloak
platform-admin-to-Nextcloud-admin mapping or native SSO activation is assumed.
The released private image includes the plugin, but provider activation is a
separate gated operation.
Use the app runbook's local-admin-first, explicit-SSO-mapping-later procedure;
preserve local recovery and existing platform administration.

Three restricted namespaces separate configuration, runtime and Helm release
Secrets. No Pods are allowed in configuration/release namespaces. Reconciler and
deployer Roles cannot modify namespaces, RBAC, NetworkPolicies, admission or source
selection. Runtime credentials cannot be read through deployer RBAC; Helm storage
Secret access is confined to its own release namespace. Retained files claims
and CNPG Clusters cannot be directly deleted by the deployer. Application Helm
uninstall/reset is not an approved operation. It would still remove app workloads;
keep it separate from data-retention and restore claims.

Admission fixes the release/chart/source/values contracts, private route, image
digests, dedicated claim budgets, single Recreate web replica and serial colocated
cron. It prevents arbitrary Secret/token mounts, CNPG identity use by app templates
and spoofed CNPG labels. Restricted PSA supplies container/host security checks.
Flux's inline values are preserved untyped JSON and cannot be directly inspected
by typed CEL. Named values references are constrained; safety is enforced on the
rendered resources, including inline overrides. Source pins and operator review
remain necessary. No unsupported `has(object.spec.values)` check is used.
CNPG's existing platform operator creates its own narrowly scoped instance-manager
ServiceAccount/Role/binding, jobs, certificates and PVC. Review those actual generated
objects before acceptance; this foundation adds no operator cluster permissions.

Default deny permits only DNS, Traefik-to-web TCP80, app/cron-to-own-database TCP5432
and the observed platform-cnpg controller-to-instance-manager TCP8000. App Pods
have no API or general internet egress. No public routing, native SSO activation, Redis or household
import is supplied. DNS/TLS and network enforcement on RKE2 must be tested live.

The shared `cnpg-system/platform-cnpg` operator initially watches only `gitlab`.
This foundation adds its pinned 1.30.1 namespaced Role and RoleBinding only in
`tenant-home-nextcloud`. The subject is the platform operator, never a tenant
identity. It can reconcile database resources and read Secrets in this namespace;
it gains no other namespace or cluster-wide Secret permission. Apply the reviewed
foundation before selecting a published platform stage that sets both the actual
operator Deployment and config to `gitlab,tenant-home-nextcloud`. Do not create a
second operator or use an empty/all-namespace watch. Verify operator readiness,
watch list, positive Nextcloud and GitLab access, and denial in an unrelated
namespace before creating the Nextcloud database. Keep the existing GitLab Role
and database unchanged. The controller rollout briefly pauses reconciliation;
this is not an instruction to restart database Pods.

CNPG alone needs API egress. Before activation, privately inventory the Kubernetes
Service IP and actual API endpoints, then render an additional policy with:

```sh
ansible-playbook -i localhost, ansible/render-nextcloud-api-policy.yaml \
  -e @/ABS/PRIVATE/api-inputs.yaml -e nextcloud_api_reviewed=true
```

Inputs are nextcloud_api_cidrs (1–4 reviewed IPv4 /32 endpoints) and a fresh
nextcloud_api_output file in an owner-only 0700 directory. The renderer makes no
API calls and never applies anything. Review actual Service/DNAT behavior and the
required 443/6443 ports; broad subnet or 0.0.0.0/0 egress is refused. This is a
required hardware-specific input, not a default wildcard or a fake successful
CNPG setup. App labels cannot select this API policy.

## Ordered review and activation gates

1. Review app and enrollment together. Verify chart 9.4.1 archive
   hash and both image digests, version/security compatibility and the accepted
   dedicated disks. App v1.1.0 is published and pinned with exact evidence. Keep the
   platform parent unselected through prerequisites and credential preparation.
   First accept the published data-only stage and deliver its public database CA.
   Then promote this released web stage; accept the disabled correction and bounded same-Pod checks before this controlled activation, then verify real sidecar progress and sustained web health.
   Do not manually change HelmRelease suspension against selected Git values.
2. Choose encrypted independent backup destination, retention and key custody;
   confirm nextcloud.perkforge.home.arpa DNS and private trusted TLS. Deliver
   nextcloud-admin, nextcloud-db-app and nextcloud-tls only in runtime using the
   gated input workflow below. The public local source needs no source-read Secret. No
   Secret values belong in Git, logs or this document.
3. Under separate live approval, verify exact published source/cluster UID, apply
   foundation plus reviewed endpoint policy, and server-validate all native CEL
   policies/CRDs. Check type warnings and actual positive/negative admission before
   resuming sources/child. Test impersonated Roles, cross-tenant network denial,
   forbidden Secret/API access, alternate images/sources/identity, generic storage
   and data deletion. Offline tests do not prove those controller boundaries.
4. Activate data only. Verify CNPG Ready, TLS-only HBA, its generated RBAC/identity,
   16Gi PVC and both actual SSD replica IDs. Export only the CNPG CA's public ca.crt
   to a nextcloud-db-ca ConfigMap in runtime; never copy its signing key. Require
   its fingerprint and Service hostname SAN to match the database. App/cron mount
   this public ConfigMap read-only at /etc/nextcloud-postgres-ca. Do not weaken
   verify-full or mount certificates below an image's read-only /etc subdirectory.
5. Activate app only after DB/public-CA/TLS gates. Verify the 32Gi files claim's SSD
   replica placement, directory ownership, initialized web and trusted private
   HTTPS. Run the app repository's database TLS probe for positive verified TLS and
   wrong-CA, wrong-hostname and plaintext denials. Keep credentials out of output.
   Enable cron in a later reviewed app commit only after initialization, then
   verify its placement and successful job. Drain/recovery must quiesce all cron
   writers before moving the web workload.
6. Verify synthetic WebDAV data, paired database/files/config backup and isolated
   restore, then load/upload limits. No real files until those gates and Corey's
   separate import/housecleaning direction. Never reset or overwrite existing data.

Build foundation and paused enrollment independently with kubectl kustomize.
Tests use actual pinned-chart renders and native CEL expression evaluation;
live schema/type-check, authorization, CNPG defaults, network/DNAT, TLS and restore
remain acceptance gates. Foundation is a draft boundary, not a claim of isolation.

## DNS, HTTPS and credential delivery

Observed preparation: the proposed `nextcloud.perkforge.home.arpa` name does not
resolve on the workstation. `/etc/hosts` still has a separate historical VM name;
do not repoint it or reuse its TLS material. Physical Traefik Pods expose node
host ports 80/443, without hostNetwork; their Service is ClusterIP with no external
address. Configure private LAN DNS to reviewed reachable node ingress addresses,
not a Service/Pod IP. Keep physical addresses in protected local inputs. Verify
resolution, routing and certificate-trusted HTTPS from the workstation and another
household client. A workstation-only hosts entry is not household DNS coverage.

No cert-manager APIs are installed. Use an explicitly approved private-CA issuance
path for a server certificate with DNS SAN `nextcloud.perkforge.home.arpa`, matching
leaf key and full intermediate chain. Trust the public root on each browser/sync
client. Keep the signing key in operator custody; only the leaf key enters the TLS
Secret. This ingress/client trust is separate from CNPG's database CA. Issuance,
DNS changes, credentials and delivery remain separate live approvals, not side
effects of this source change.

After the namespace foundation exists, supply an external 0700 directory containing
0600 regular owner files `admin-username`, `admin-password`, `db-password`, `tls.crt`
and `tls.key`. Choose the owner-controlled bootstrap admin name explicitly; do not
reuse old VM passwords. Password inputs are one-line strings of at least 20
characters; lookup removes trailing whitespace. Store/recover these inputs through
the approved encrypted backup workflow, never Git or chat. Supply the public
ingress CA trust bundle separately. From a clean, published enrollment checkout:

```sh
ansible-playbook -i localhost, ansible/deliver-nextcloud-inputs.yaml \
  -e @/ABS/PRIVATE/nextcloud-inputs.yml -e nextcloud_inputs_apply=true
```

Private YAML supplies `enrollment_tag`, `target_kubeconfig`, `target_context`,
`expected_cluster_uid`, `nextcloud_private_dir` and `nextcloud_ingress_ca_file`.
Default/check modes touch no API or private file. Apply verifies the exact clean
published checkout, cluster UID and namespace label, file ownership/modes, HTTPS
chain/purpose/hostname/expiry and leaf key match. It sends only the three intended
Secrets through hidden stdin, server-validates all before creation and refuses
existing objects. It never rotates credentials, overwrites or emits private files.
Certificate bundles must contain no private key; the leaf key file must contain
one matching, unencrypted private key. Bundled signing keys are rejected.
Partial creation must be inspected; do not retry blindly or delete retained inputs.
No local sudo is required when using the existing authorized admin kubeconfig.

After separately approved data activation, verify CNPG Ready and its server
certificate Service SAN/fingerprint, then project **only** public `ca.crt` to the
runtime `nextcloud-db-ca` ConfigMap. Do not copy `ca.key`, a signing key or the
server private key. This public-CA delivery is not performed by the bootstrap
Secret playbook and must precede web activation. Then run the existing read-only
app TLS probe and require wrong-CA, wrong-hostname and plaintext failures. Neither
that runtime probe nor household client TLS/backup restore is accepted by a build.

Repeat the offline checks with Python/PyYAML/Ansible, kubectl, Helm and Go 1.27.3:

```sh
mkdir -m 700 /ABS/FRESH/schema-fixtures
bash tests/nextcloud-cel/fetch-schemas.sh /ABS/FRESH/schema-fixtures
export NEXTCLOUD_APP_CHECKOUT=/ABS/PUBLISHED/v1.1.0-nextcloud-checkout
export NEXTCLOUD_ROLLBACK_APP_CHECKOUT=/ABS/PUBLISHED/v1.0.4-nextcloud-checkout
export NEXTCLOUD_CHART=/ABS/VERIFIED/nextcloud-9.4.1.tgz
export NEXTCLOUD_OPENAPI=/ABS/FRESH/schema-fixtures/openapi.json
export NEXTCLOUD_CRD_DIR=/ABS/FRESH/schema-fixtures
python3 -m unittest discover -s tests -p 'test_*.py' -v
cd tests/nextcloud-cel && go test -count=1 -v .
```

The schema fetcher pins source commits for Kubernetes 1.36.5, Flux helm-controller
1.6.4/source-controller 1.9.5/kustomize-controller 1.9.5 and CNPG 1.30.1, matching
the reviewed target. No cluster API is called. CI verifies and checks out the selected v1.1.0 release
and the explicit v1.0.4 rollback fixture at their recorded commits. Both real
chart renders remain covered; the former app PR head is no longer a fixture.
Every policy is type-checked, including an intentionally invalid-field control,
before positive real renders and negative mutations are evaluated. Repeat against
the actual controller schema/defaults before live acceptance. Never treat a successful offline case as proof of authorization or
network isolation.

`-count=1` is required: Go's test cache cannot reliably track YAML and external app
files read by the Python render subprocess. Build/dependency caching remains safe.

## Same-Pod cron correction candidate

The bounded separate-Pod cron test completed, but web shared-volume access failed
until an automatic restart. Suspected SELinux MCS relabeling requires host audit
confirmation. Keep the live CronJob suspended. This policy candidate permits only
the web Deployment's existing `nextcloud` and optional `nextcloud-cron` containers,
with the same pinned image, UID33 and existing token/volume restrictions. It adds
no RBAC, Secret access, host mounts or fixed SELinux labels. Extra or substituted
sidecars remain denied. CronJob containers still have the existing single-container
limit; this policy does not enable or resume them.

The preceding app v1.0.3 deployed the same-Pod correction with its runner disabled.
This private-image candidate preserves the guarded non-root runner from v1.0.4. Review and release the policy before
selecting the opt-in app. Runtime acceptance must show continuous web health and
synthetic-file retention over multiple successful runs, matching container/volume
MCS labels, and no audit denials. No household import or backup claim is included.

## Unselected SSO boundary

[The offline SSO renderer](sso/README.md) prepares exact issuer egress/public trust
for review only. No cluster root or current foundation selects its output.

The source runtime policy also admits [immutable PerkForge GHCR images with a narrow
private-pull reference](sso/README.md#registry-trust-and-private-pull-review-prerequisite)
for coordinated review with the app candidate. Public-image rollback remains
admitted; app/init/cron cannot mix images. This candidate advances only the app
source pin to v1.1.0. It does not select issuer egress, deliver credentials or
change any live workload. The legacy v1.0.4 render remains an explicit rollback
fixture and its exact public image remains admitted.
