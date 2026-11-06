# Unselected Nextcloud OIDC boundary preparation

This directory is deliberately absent from every Kustomization. Run `ansible-playbook
tenants/nextcloud/sso/prepare.yaml` for a noncontacting plan; `--check` also skips
all inputs/contact even with `nextcloud_sso_render=true`. With explicit render,
supply an external absolute fresh output directory, reviewed private-LAN issuer
IPv4, public CA file and exact SHA256. Only offline local files are produced.
The certificate parser rejects invalid/expired leaf material; trust-chain and
issuer SAN/CA suitability require operator validation. Private keys are refused.

Output grants only app-labelled Pods TCP443 to one /32 and supplies a public CA
ConfigMap. It grants no runtime app-store or registry access. DNS retains the
existing DNS policy. A shared ingress IP exposes other virtual hosts at L3/L4:
this is not FQDN-level isolation. Review actual issuer routing, CNI pre/post-DNAT
semantics and negative probes; prefer a dedicated verified issuer endpoint when
shared ingress does not meet the required boundary. No guessed live IP is tracked.

Neither this renderer nor publication applies policy/trust. Existing admission
continues rejecting the additional CA volume and derived image. A later exact
review must admit only the built image digest and read-only public-CA mount and
configure actual HTTPS client trust without disabling verification or replacing
PostgreSQL trust. It must account for same-Pod cron sharing web egress. The
operator-owned boundary must precede native SSO activation and be independently
removable. Preserve DNS, database, existing ingress, PVCs and other applications.

Live acceptance must show correct issuer discovery/token/JWKS HTTPS, wrong CA/
hostname denial, unrelated destination/port and other tenant denial, no API token,
unchanged resource identity and recovery login. Rollback disables the dedicated
client and native provider before withdrawing only this policy/config after safe
writer quiescence; revoke application sessions separately. No live tests ran here.

## Exact admission and delivery candidate

With `nextcloud_sso_delivery_contract=true` and an actual reviewed
`nextcloud_sso_image=ghcr.io/perkforge/nextcloud-sso:35.0.2-oidc8.13.0@sha256:<digest>`,
preparation also renders a full replacement runtime Pod policy outside all roots.
It retains existing UID33/namespace/identity protections, replaces only the exact
image and adds only fixed public-CA and one-key 0440 client-secret
volumes at fixed read-only mount paths. Other Secrets/mounts/digests remain denied.
The actual native Kubernetes CEL compiler exercises this generated policy and
positive/negative mutations in CI; active policy must continue denying the candidate.
Do not apply it or select generated app values merely because rendering succeeds.

`deliver.yaml` is a separate default-off/check-noncontacting operator stage. Future
use requires `nextcloud_sso_deliver=true`, exact
`nextcloud_sso_delivery_approval=nextcloud-sso-delivery-v1`, explicit kubeconfig/
context/cluster UID and the expected restricted runtime namespace. It consumes an
EXISTING external 0600 client secret and checksummed public CA; no key is generated.
It creates only missing immutable `nextcloud-oidc` and `nextcloud-oidc-ca` inputs.
Exact owned inputs are reused; foreign objects, changed data or rotation are
refused. Partial delivery can resume without overwriting the first object. No
new RBAC, user enrollment, image selection, network apply or native activation
occurs. Secret hashes used by the app adapter must match trimmed mounted bytes.

The upstream Nextcloud HTTP client blocks private issuer addresses by default.
The app adapter has a distinct private-HTTP approval gate. That setting allows
private HTTP destinations at app level; approve/test this exact egress boundary
first and reject a shared ingress endpoint if other virtual hosts are unacceptable.
No app-store or general runtime internet access is needed.
