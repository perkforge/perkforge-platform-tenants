# Nextcloud pilot enrollment candidate

Paused. Only the dormant `clusters/local-nextcloud` selector includes this folder;
the existing local/dev roots and live platform do not. Its app
tag is intentionally UNCONFIGURED until the app PR is merged, published and
verified. No branch or fabricated release is a deployment input. Foundation is
operator-owned and separately applied from a clean published enrollment checkout;
the tenant child cannot reconcile its own authority.

The Nextcloud-only selector contains no Portal resources and does not change any
suspension flag. It removes the source Secret reference because the app repository
is public. The shared base retains an optional scoped read reference for a future
private repository; the current public path requires no Git token. Do not select
the existing `clusters/local` root to activate Nextcloud: that root enables Portal.
Before deployment, publish/verify the app release, pin it with resolved source
evidence, publish the reviewed enrollment selection, and add a matching published
platform stage pointing its enrollment parent at `./clusters/local-nextcloud`.
Preserve the current GitLab/runner stage. The platform's existing enrollment
prerequisite gate is tied to the old default local root and needs a reviewed
selected-root update before use; do not bypass it or apply Portal's path instead.

The app candidate is perkforge/perkforge-tenant-nextcloud PR #1. Its pilot uses
32Gi files plus 16Gi PostgreSQL on the accepted two-replica longhorn-dedicated
tier (platform v0.19.0). Storage expansion requires coordinated app values,
admission and quota review before household import. No single-excess claim is
allowed here. One web process, one database instance and serial cron are an empty
pilot, not application HA or accepted household load. Both prefer worker-2; worker-1
remains eligible. Leave cron suspended until web initialization is accepted.

## What the foundation owns

Corey retains full platform administration. This foundation adds no ClusterRole,
ClusterRoleBinding, OIDC authentication change or replacement of existing owner
bindings. Its policies scope the tenant's resources; the owner still controls
those policies and can perform reviewed recovery. The reconciler/deployer identities
are limited automation accounts, not Corey's personal administrator identity.
Nextcloud's initial application administrator is separately bootstrapped from its
operator-delivered admin Secret and must be verified in the app. No Keycloak
platform-admin-to-Nextcloud-admin mapping or SSO plugin is assumed or enabled.
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
have no API or general internet egress. No public routing, SSO, Redis or household
import is supplied. DNS/TLS and network enforcement on RKE2 must be tested live.

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

1. Review the app and enrollment candidates together. Verify chart 9.4.1 archive
   hash and both image digests, version/security compatibility and the accepted
   dedicated disks. Merge/publish app first; replace UNCONFIGURED with its exact
   verified release tag and record resolved source evidence through the repository's
   release procedure before selecting this folder in a local root. Keep sources,
   child and both app HelmReleases suspended through preparation.
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
python3 -m unittest discover -s tests -p 'test_*.py' -v
mkdir -m 700 /ABS/FRESH/schema-fixtures
bash tests/nextcloud-cel/fetch-schemas.sh /ABS/FRESH/schema-fixtures
export NEXTCLOUD_APP_CHECKOUT=/ABS/REVIEWED/nextcloud-checkout
export NEXTCLOUD_CHART=/ABS/VERIFIED/nextcloud-9.4.1.tgz
export NEXTCLOUD_OPENAPI=/ABS/FRESH/schema-fixtures/openapi.json
export NEXTCLOUD_CRD_DIR=/ABS/FRESH/schema-fixtures
cd tests/nextcloud-cel && go test -count=1 -v .
```

The schema fetcher pins source commits for Kubernetes 1.36.5, Flux helm-controller
1.6.4/source-controller 1.9.5/kustomize-controller 1.9.5 and CNPG 1.30.1, matching
the reviewed target. No cluster API is called. CI pins the proposed app commit as
a **test fixture only**; it does not replace UNCONFIGURED or select deployment.
Every policy is type-checked, including an intentionally invalid-field control,
before positive real renders and negative mutations are evaluated. Repeat against
the eventual released app/source and actual controller schema/defaults before live
acceptance. Never treat a successful offline case as proof of authorization or
network isolation.

`-count=1` is required: Go's test cache cannot reliably track YAML and external app
files read by the Python render subprocess. Build/dependency caching remains safe.
