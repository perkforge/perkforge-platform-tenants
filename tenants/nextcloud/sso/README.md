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
