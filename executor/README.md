# Executor source candidate, not a published artifact

This candidate implements the native trigger ABI and private staging. It remains
unbuildable until a reviewed `embedded-stage.yaml`, hashed dependency wheel lock,
clean source archives, complete source hash manifest and exact revisions.json are
provided by the build preparation. No placeholder image digest is supplied.

The official Python base manifest was read from Docker's registry on 2026-11-14.
It is a reputable candidate, not Registry1: an explicit reviewed exception or
verified equivalent Registry1 base is required before rollout. Official Ansible
runner `latest` was rejected as a stale schema1 April2022 image, not silently used.
No image was pulled, built or published. Build checks require bash/flock/sha256sum;
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
this source adds no workflow or CI activation. Current launcher needs native tests
and independent review before any credential or provider operation.
