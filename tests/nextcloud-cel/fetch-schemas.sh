#!/usr/bin/env bash
# Read-only public test fixture downloads at exact source commits; no cluster API.
set -euo pipefail
test "$#" = 1
destination=$1
test -d "$destination"
test -z "$(ls -A "$destination")"
fetch() {
  curl --fail --show-error --location --retry 3 --connect-timeout 20 --max-time 120 "$1" -o "$destination/$2"
}
fetch https://raw.githubusercontent.com/kubernetes/kubernetes/ad950d1cc78b0183c476bd4d3f1934c104229727/api/openapi-spec/swagger.json openapi.json
fetch https://raw.githubusercontent.com/fluxcd/helm-controller/561379cd309d56a5037f2261848065eeee6a1a7a/config/crd/bases/helm.toolkit.fluxcd.io_helmreleases.yaml helmrelease.yaml
fetch https://raw.githubusercontent.com/fluxcd/source-controller/53194ad4730ebf07718b29d58f66efd6938fd3da/config/crd/bases/source.toolkit.fluxcd.io_gitrepositories.yaml gitrepository.yaml
fetch https://raw.githubusercontent.com/fluxcd/source-controller/53194ad4730ebf07718b29d58f66efd6938fd3da/config/crd/bases/source.toolkit.fluxcd.io_helmrepositories.yaml helmrepository.yaml
fetch https://raw.githubusercontent.com/fluxcd/kustomize-controller/d5d5d2bf9d9cf3cb33c3150f47990bb22781334a/config/crd/bases/kustomize.toolkit.fluxcd.io_kustomizations.yaml kustomization.yaml
fetch https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/2a35abb4628f209d149825ef3c38011e0701ff2f/config/crd/bases/postgresql.cnpg.io_clusters.yaml cnpg.yaml
