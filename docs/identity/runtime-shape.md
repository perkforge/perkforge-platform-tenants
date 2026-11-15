# Private temporary workspace and supervised execution

New selections use explicit `runtimeProfile: private-tmp-supervised-v1`. The field
participates in the attempt digest, producing new Job/input names. Omission is
legacy source compatibility only, not the corrected runtime. Unknown profiles
fail closed. Membership release still does not change the attempt.

The same pinned maintained image runs one non-root init container. It sees only
the existing 128Mi emptyDir at `/work`, not source, credentials, API projection or
receipt PVC. The expected native root is root:1001 mode2777. A nonempty, symlink,
foreign or unexpected root is rejected. Exclusive creation of `private` precedes
no-follow opening and inode/owner/mode/content verification. Only that new child
FD is normalized to0700 to remove inherited setgid; no existing path is repaired,
no chown/root action occurs. Failure is terminal; there is no init retry policy.

The main container mounts only that child at `/tmp`. Fixed `/usr/bin/timeout`
uses TERM at270s and KILL10s later with its normal supervisor behavior, without
foreground or preserve-status. The existing launcher remains its child, so its
lock owner is not PID1. The Job's300s deadline includes init/image startup, so a
full270s of execution is not promised. Init and main use the same configured
resource request/limit; sequential init does not add concurrent reservations.
The selected pilot remains100m/256Mi request,500m/512Mi limit.

Admission allows exactly the rendered init command, image, mount, security,
resources and cardinality; extra init/sidecars, env, secret mounts and command
changes are denied. Legacy declarations still forbid init containers. Offline
native cases cover defaulted fields and adversarial changes. Maintained-image
filesystem, supervisor/signal and full phase checks plus actual kubelet lifecycle
acceptance remain separate required evidence before provider execution. This
source is not a claim of live completion or permission to start Jobs.
