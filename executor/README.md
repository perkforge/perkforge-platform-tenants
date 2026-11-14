# Executor source candidate, not a published artifact

This candidate implements the native trigger ABI and private staging. It is built and tested only as an isolated synthetic fixture, not published or
approved for deployment. The embedded stage and dependency lock are
now source candidates; clean published source archives, wheel availability, complete
source hash manifest and exact revisions.json must pass build preparation. No placeholder image digest is supplied.

The official Python base manifest was read from Docker's registry on 2026-11-14.
It is a reputable candidate, not Registry1: an explicit reviewed exception or
verified equivalent Registry1 base is required before rollout. Official Ansible
runner `latest` was rejected as a stale schema1 April2022 image, not silently used.
A local rootless fixture image was subsequently built; no image was published. Build checks require bash/flock/sha256sum;
missing native tools are a build failure, not permission to install at runtime.

Packaging must hash every archived enrollment/platform executable file (not merely
a Git SHA label) into /opt/provenance.sha256; include launcher/verifier/embedded
stage, reject symlinks/extra source files, and independently compare archives to
published commits. The immutable image digest binds the manifest. Input bytes are
checked both before credentials and after private staging; projection rotation can
fail closed. Group writer only; no admin attestor in this container.

The embedded Ansible stage must bind context, source revision, exact parent ID,
HTTPS origin and CA; refuse parent bootstrap with the scoped writer; invoke the
reviewed native adapter and validate group-ready receipt. It must not call the
operator remote GitHub release checker or claim user approval/membership ready.

No existing enrollment release workflow publishes executors: configuration-release
publishes source releases only. A separately reviewed, manually dispatched
image-build workflow may publish exact reviewed archives/digests after approval;
this source adds no workflow or CI activation. Production credentials/provider operations still require independent review and
the applicable concrete runtime approval.

`prepare-build.sh` now defines a default-inert, explicit build-preparation path:
require clean exact source heads, verify published tags through the existing gh
CLI verifier at PREPARATION time, archive Git-tracked files only, reject symlinks,
require embedded stage, and hash all archived source bytes. No image operation is
performed. A failed preparation leaves a private inspectable context, never a
successful receipt; do not reuse it without explicit cleanup/review.
`requirements.lock` pins published PyPI wheel hashes. Approved build preparation
must download matching wheels with `--require-hashes --only-binary=:all:` into
`wheels/`; build installs only from that offline directory. Dependency resolution
and native image tool availability still require an actual isolated build test.


## Isolated native acceptance, 2026-11-14

A rootless local build of the exact launcher succeeded with the official pinned
Python base and hash-verified locked wheels. Native bash/flock/Ansible tools were
present. No host software installation, registry publication or live cluster/API
access occurred. The fixture overrides only the source selection to synthetic
explicit revisions, so it is NOT published-release provenance evidence.

`scripts/test_identity_executor_container.py` ran inside that image with network
NONE (loopback synthetic HTTPS server only), UID/GID65532, readonly root, no
capabilities and no-new-privileges. Actual launcher created one private child of
a preexisting fake parent; repeat performed no extra POST. Input hash mismatch,
unknown extra variable and Jinja injection failed before provider calls. A
mode0770 receipt root failed before provider calls; owned0700 succeeded. Receipt
readback and temporary credential cleanup passed. Fake token was absent from
stdout/stderr. Native CA verification was used, not insecure TLS.

This proves the group-foundation executable path, not Kubernetes admission,
real GitLab token authority, runtime network routing, scheduling or user/membership
automation. Admission must constrain the writer Job so it cannot mount an attestor
credential. Real receipt PVC root requires narrow owner/mode initialization; do
not globally chmod storage or assume fsGroup alone meets the custody guard.
