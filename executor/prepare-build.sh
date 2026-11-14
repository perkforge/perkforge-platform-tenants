#!/usr/bin/env bash
# Source packaging only; explicit opt-in. Does not build, push, install or fetch source.
set -euo pipefail
[[ ${1:-} == --prepare ]] || { echo 'INERT: --prepare ENROLLMENT_REPO TAG SHA PLATFORM_REPO TAG SHA OUTPUT required'; exit 0; }
[[ $# == 8 ]] || exit 2
er=$2 et=$3 es=$4 pr=$5 pt=$6 ps=$7 out=$8
[[ $es =~ ^[0-9a-f]{40}$ && $ps =~ ^[0-9a-f]{40}$ && $out == /* && ! -e $out ]] || exit 2
for repo in "$er" "$pr"; do
 [[ -z $(git -C "$repo" status --porcelain) ]] || exit 2
done
[[ $(git -C "$er" rev-parse HEAD) == "$es" && $(git -C "$pr" rev-parse HEAD) == "$ps" ]] || exit 2
# Network is build-preparation only; require actual published immutable sources.
"$er/scripts/verify-release-ref.sh" perkforge/perkforge-platform-tenants "$et" "$es"
"$er/scripts/verify-release-ref.sh" perkforge/perkforge-platform "$pt" "$ps"
umask 077
mkdir "$out"; mkdir "$out/enrollment" "$out/platform"
git -C "$er" archive "$es" | tar -x -C "$out/enrollment"
git -C "$pr" archive "$ps" | tar -x -C "$out/platform"
# Archives must be regular source only; no symlink/dangling executable escape.
[[ -z $(find "$out/enrollment" "$out/platform" ! -type f ! -type d -print -quit) ]] || exit 2
[[ -f $out/enrollment/executor/embedded-stage.yaml ]] || exit 2
cp "$out/enrollment/executor/Containerfile" "$out/Containerfile"
cp "$out/enrollment/executor/requirements.lock" "$out/requirements.lock"
cp "$out/enrollment/executor/reconcile-identity" "$out/reconcile-identity"
printf '{"enrollment":"%s","platform":"%s"}\n' "$es" "$ps" > "$out/revisions.json"
(cd "$out"; find enrollment platform -type f -print0 | sort -z | xargs -0 sha256sum > provenance.sha256)
echo 'Prepared source-only context. Wheel download, container build/publication and runtime approval still required.'
