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

## Actual kubelet checkpoint

`identity_kubelet_preflight.build(declaration, initializer)` emits one offline,
content-addressed Pod. It is not appended to GitOps output, automatically started,
or retried. The exact initializer operator identity alone is admitted; no new
Role is created. It uses the same init, tmp volume, security and configured budget
as the phase Jobs, but mounts no source, credentials, API projection or receipt
PVC. Its fixed supervised main checks UID/GID,0700, empty private tmp and PID>1.
No phase label is present, so existing namespace default-deny egress applies.

Before an explicitly authorized creation, verify the configured cluster UID and
namespace, exact source/admission, absent name and native dry-run defaults. A
preexisting Pod is a stop, not an adoption or retry. Record the returned UID; wait
within the native300s deadline, verify exact node and successful init/main exit,
and use UID-precondition deletion followed by absence readback. Retain evidence
on ambiguity. Failure does not authorize phase Jobs. This checkpoint proves
kubelet/subPath/security behavior, not provider access, receipt persistence or
positive membership. No execution/cleanup runner is supplied here.
