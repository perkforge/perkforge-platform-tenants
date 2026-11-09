# Nextcloud OIDC delivery and boundary review

The [current selection and acceptance](../README.md#selected-source-contract)
uses native SSO with retained local recovery. This directory is deliberately absent
from every Kustomization. Its delivery playbook is an operator workflow; its
boundary/runtime-policy renderer is offline review tooling, not the owner of the
adopted live issuer policy. Platform Git owns that policy. Do not apply generated
network or narrower runtime-policy output over accepted objects as routine upkeep.
The enrollment foundation remains the runtime-policy source of truth.

Run `ansible-playbook
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

Neither this renderer nor publication applies policy/trust. The source admission
candidate now permits immutable images from the exact `ghcr.io/perkforge/`
namespace and fixed read-only OIDC mounts, while preserving only the released
public image for rollback. Applying that
operator-owned policy and configuring actual HTTPS client trust remain separate
approval gates. Never disable verification or replace PostgreSQL trust. Account
for same-Pod cron sharing web egress. The
operator-owned boundary must precede native SSO activation and be independently
removable. Preserve DNS, database, existing ingress, PVCs and other applications.

Live acceptance must show correct issuer discovery/token/JWKS HTTPS, wrong CA/
hostname denial, unrelated destination/port and other tenant denial, no API token,
unchanged resource identity and recovery login. Rollback disables the dedicated
client and native provider before withdrawing only this policy/config after safe
writer quiescence; revoke application sessions separately. Offline rendering does not establish any of those live outcomes.

## Offline exact-policy review and immutable input delivery

With `nextcloud_sso_delivery_contract=true` and an actual reviewed
`nextcloud_sso_image=ghcr.io/perkforge/nextcloud-sso:35.0.2-oidc8.13.0@sha256:<digest>`,
preparation also renders a full replacement runtime Pod policy outside all roots.
It retains all source policy validations and replaces only the image predicate
with that one exact review image, deliberately narrower than the org-wide source
policy. The public-CA and one-key 0440 client-secret
volumes use fixed read-only paths without subPath/subPathExpr. App, init and cron
must use the same image; only `nextcloud-registry-existing` may be a pull Secret,
and the private image requires it. Other Secrets/mounts remain denied; this rendered policy denies every other image.
The native Kubernetes CEL compiler exercises both the source policy and generated
unselected policy. A synthetic PerkForge digest passes the source org rule but
only the renderer's exact supplied image passes its narrower review predicate.
Do not apply it or select generated app values merely because rendering succeeds.

`deliver.yaml` is a separate default-off/check-noncontacting operator stage. Any
new delivery requires `nextcloud_sso_deliver=true`, exact
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

## Confirmed identity intent does not change the tenant boundary

Corey's existing Keycloak identity retains platform administration; native admin
inside this dedicated Nextcloud instance was explicitly configured and owner-
confirmed. The separate local Nextcloud admin remains recovery. The app/client adapters must verify that native
mapping explicitly; no platform group is assumed to grant app admin. Jett's future
ordinary household access is deferred: no account creation, enrollment or grants
are authorized by these procedures. This intent adds no Kubernetes RBAC, credential delivery,
policy selection or live permissions. Keep every boundary/delivery flag off until
its own action-time approval and actual positive/negative acceptance.

## Registry trust and private-pull review prerequisite

The source policy trusts the exact `ghcr.io/perkforge/` organization namespace,
not all GHCR publishers. It accepts valid lowercase package paths with an optional
tag and requires an immutable `@sha256:<64 lowercase hex>` reference. App, init
and cron must use the same exact image in each Pod template. Another PerkForge
package or digest does not require a tenant policy release; app Git still pins
and reviews the exact artifact. This trusts PerkForge package publishers. It does
not verify signatures, attestations, vulnerability scans or image contents.

The selected published app v1.1.1 pins
`ghcr.io/perkforge/nextcloud-sso:35.0.2-oidc8.13.0@sha256:57c90b70d3c7261debbd5f2f2d760222fd6db65b8235a5c75f4ae7cb59df1d03`.
Only the previous public rollback image
`docker.io/library/nextcloud:35.0.2-apache@sha256:d88929dc8386420b8963f86cabb667fdaf733eef9dcf8fc98e226801a32c023c`
is also admitted for policy-first rollout and rollback. There is no general Docker
Hub allowance; retire that exception only after accepted migration and a reviewed
rollback plan. Other GHCR organizations, lookalike hosts/namespaces, malformed
paths/digests and tag-only images are rejected.

Every PerkForge GHCR image requires the singleton Pod `imagePullSecrets` reference
`nextcloud-registry-existing`. The old image may omit it or retain that exact
reference during rollback. No other pull Secret or mixed-image Pod is admitted.
The upstream chart's input is `image.pullSecrets: [nextcloud-registry-existing]`.
Node-side registry authentication needs no application Pod registry egress.

No registry credential is created, copied or delivered by this source change.
Before any separately approved rollout, the operator must arrange an existing,
read-only GHCR credential with only the approved package access, then separately
approve delivery to the exact `tenant-home-nextcloud/nextcloud-registry-existing`
Secret with type `kubernetes.io/dockerconfigjson` and a `ghcr.io` entry. Keep the
credential in protected operator inputs, never Git, chat, arguments or logs. Do
not reuse the developer's `gh` keyring credentials or the Portal delivery playbook.
Verify the reviewed published enrollment source, intended cluster UID/context and
restricted runtime namespace before delivery. Refuse an existing foreign or
mismatched Secret; rotation/replacement needs its own approval. Verify node-side
pull success for the exact digest before selection. That external prerequisite,
OIDC input delivery, issuer egress and native provider activation remain distinct
gates. Selecting the published app in enrollment source does not apply a live
boundary, deliver these inputs, advance the platform pin or activate native SSO.

### Dedicated registry delivery entrypoint

The default-off [Nextcloud registry input playbook](../../../ansible/nextcloud-registry.md)
captures this exact approved delivery route without using Portal's workflow. It
requires protected existing dockerconfigjson, explicit release/cluster/namespace
checks and action-specific approval. It creates only a missing named immutable
input or reuses an exact owned match; foreign/mutable/mismatched inputs stop without
rotation or adoption. Publication does not run it or verify the live Secret.
