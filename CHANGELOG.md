# Changelog

## [1.5.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.4.0...v1.5.0) (2026-11-07)


### Features

* **nextcloud:** admit digest-pinned PerkForge GHCR images ([#37](https://github.com/perkforge/perkforge-platform-tenants/issues/37)) ([3962820](https://github.com/perkforge/perkforge-platform-tenants/commit/39628204fbfb8bdd0df92e4c76b7c134fe5aefc7))


### Bug Fixes

* **nextcloud:** select published app configuration v1.1.0 ([#39](https://github.com/perkforge/perkforge-platform-tenants/issues/39)) ([d61c33e](https://github.com/perkforge/perkforge-platform-tenants/commit/d61c33e0937f9e5f22d18bbba129f378846c2a3d))

## [1.4.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.3.2...v1.4.0) (2026-11-07)


### Features

* **nextcloud:** add unselected SSO delivery and admission contracts ([#35](https://github.com/perkforge/perkforge-platform-tenants/issues/35)) ([056dbef](https://github.com/perkforge/perkforge-platform-tenants/commit/056dbefcc4d5d421d484cfae9d7981b297b45140))

## [1.3.2](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.3.1...v1.3.2) (2026-11-06)


### Bug Fixes

* **nextcloud:** select guarded same-pod cron release ([d219c08](https://github.com/perkforge/perkforge-platform-tenants/commit/d219c0815edec3d56860255c032122f7f101ac12))
* **nextcloud:** select guarded same-pod cron release ([0431259](https://github.com/perkforge/perkforge-platform-tenants/commit/043125944e60f774edfd0e72801b1959c768de83))

## [1.3.1](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.3.0...v1.3.1) (2026-11-06)


### Bug Fixes

* **nextcloud:** admit only the named non-root cron sidecar ([701730f](https://github.com/perkforge/perkforge-platform-tenants/commit/701730f69fa908a1bfd234a36d5655389a13d726))
* **nextcloud:** admit only the named non-root cron sidecar ([58fabd5](https://github.com/perkforge/perkforge-platform-tenants/commit/58fabd5eb005fb563f2d282ad4bb6133354ab7cd))
* **nextcloud:** pin published disabled cron correction ([182efc2](https://github.com/perkforge/perkforge-platform-tenants/commit/182efc228f416480bd46aae6cb26c11febad5f14))
* **nextcloud:** pin published disabled cron correction ([0ed049f](https://github.com/perkforge/perkforge-platform-tenants/commit/0ed049f8d46aacc26bbf64dbbb098a0609c1d3ee))

## [1.3.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.2.1...v1.3.0) (2026-11-06)


### Features

* **nextcloud:** select published web initialization stage ([#28](https://github.com/perkforge/perkforge-platform-tenants/issues/28)) ([52c13c1](https://github.com/perkforge/perkforge-platform-tenants/commit/52c13c15205f526d3af99bbe558832fdf7c93fbb))

## [1.2.1](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.2.0...v1.2.1) (2026-11-06)


### Bug Fixes

* **nextcloud:** enroll shared CNPG namespace authority ([eb73fd9](https://github.com/perkforge/perkforge-platform-tenants/commit/eb73fd9994019809095ceb76d35765e4dc5e314e))
* **nextcloud:** enroll shared CNPG namespace authority ([dbda902](https://github.com/perkforge/perkforge-platform-tenants/commit/dbda9024ccb3f6e8d159af2bef2156f20b7ad468))

## [1.2.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.1.0...v1.2.0) (2026-11-06)


### Features

* **nextcloud:** add isolated enrollment path and gated inputs ([fd2fc4a](https://github.com/perkforge/perkforge-platform-tenants/commit/fd2fc4a84a9b98e818d08249026a580761dc6244))
* **nextcloud:** isolate enrollment selection and gate bootstrap inputs ([edab5a6](https://github.com/perkforge/perkforge-platform-tenants/commit/edab5a610e46b0300b5c3ada19b30aabab5498f5))
* **nextcloud:** pin the published database-only deployment stage ([dbb9c55](https://github.com/perkforge/perkforge-platform-tenants/commit/dbb9c55734c7d9514473e5f2b20e7db0000326f8))


### Bug Fixes

* **nextcloud:** reject signing-key bundles during TLS delivery ([b8e1bd3](https://github.com/perkforge/perkforge-platform-tenants/commit/b8e1bd3d1cc1e568598d996ca78fe9dac1558cf6))

## [1.1.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v1.0.0...v1.1.0) (2026-11-06)


### Features

* **nextcloud:** prepare paused pilot enrollment and boundaries ([#22](https://github.com/perkforge/perkforge-platform-tenants/issues/22)) ([057109b](https://github.com/perkforge/perkforge-platform-tenants/commit/057109b9ffd9717b5ee6c6b73f562e9cd4d56ff1))

## [1.0.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.4.4...v1.0.0) (2026-10-31)


### ⚠ BREAKING CHANGES

* **enrollment:** cluster selection annotations now use platform.perkforge.io. Consumers must advance to this compatible enrollment release after publication; old release tags remain unchanged.

### Bug Fixes

* **enrollment:** align selection metadata and pin portal v1.0.0 ([#20](https://github.com/perkforge/perkforge-platform-tenants/issues/20)) ([dc18a4b](https://github.com/perkforge/perkforge-platform-tenants/commit/dc18a4bbf5bd3b6e41aeacc7fa69f661c096233d))

## [0.4.4](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.4.3...v0.4.4) (2026-10-29)


### Bug Fixes

* **portal:** stabilize groups mapper after token use ([#18](https://github.com/perkforge/perkforge-platform-tenants/issues/18)) ([e0d885b](https://github.com/perkforge/perkforge-platform-tenants/commit/e0d885bc06b419bbbcb1f61a2517c11b69926d8a))

## [0.4.3](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.4.2...v0.4.3) (2026-10-29)


### Bug Fixes

* **portal:** require existing basic subject scope ([#16](https://github.com/perkforge/perkforge-platform-tenants/issues/16)) ([781da8f](https://github.com/perkforge/perkforge-platform-tenants/commit/781da8f5601678b05d99c31f78f74a3e059cb986))

## [0.4.2](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.4.1...v0.4.2) (2026-10-29)


### Bug Fixes

* **portal:** declare normalized mapper userinfo defaults ([#14](https://github.com/perkforge/perkforge-platform-tenants/issues/14)) ([24fd530](https://github.com/perkforge/perkforge-platform-tenants/commit/24fd530841f519f264370e58b69dc0c10a093c76))

## [0.4.1](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.4.0...v0.4.1) (2026-10-29)


### Bug Fixes

* **portal:** validate Keycloak server-added attributes ([#12](https://github.com/perkforge/perkforge-platform-tenants/issues/12)) ([fe4d279](https://github.com/perkforge/perkforge-platform-tenants/commit/fe4d279d677ff912b1b7772e5489b0ba425902af))

## [0.4.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.3.0...v0.4.0) (2026-10-29)


### Features

* **portal:** select local tenant activation release ([#10](https://github.com/perkforge/perkforge-platform-tenants/issues/10)) ([bed8fdc](https://github.com/perkforge/perkforge-platform-tenants/commit/bed8fdc248ead2ca7ab4cb32135fef430c9eb360))

## [0.3.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.2.0...v0.3.0) (2026-10-29)


### Features

* **portal:** gate private registry credential delivery ([#8](https://github.com/perkforge/perkforge-platform-tenants/issues/8)) ([ce8402b](https://github.com/perkforge/perkforge-platform-tenants/commit/ce8402bad810d36f05308f8f422711037f702c9d))

## [0.2.0](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.1.1...v0.2.0) (2026-10-29)


### Features

* **portal:** prepare scoped local tenant enrollment ([#6](https://github.com/perkforge/perkforge-platform-tenants/issues/6)) ([369e1e3](https://github.com/perkforge/perkforge-platform-tenants/commit/369e1e3d29c80a4e3be3b2f1b5f5ced9b5cf5ccc))

## [0.1.1](https://github.com/perkforge/perkforge-platform-tenants/compare/v0.1.0...v0.1.1) (2026-10-28)


### Bug Fixes

* **gitops:** select published portal configuration tag ([#4](https://github.com/perkforge/perkforge-platform-tenants/issues/4)) ([45e8cb0](https://github.com/perkforge/perkforge-platform-tenants/commit/45e8cb01f0a1c8503b16a35163e3e76485443eee))

## 0.1.0 (2026-10-28)


### Features

* **release:** add reviewed configuration version tags ([#2](https://github.com/perkforge/perkforge-platform-tenants/issues/2)) ([683a6cb](https://github.com/perkforge/perkforge-platform-tenants/commit/683a6cbbdecb08b28cc9d94fa8c65ba3e78152be))
