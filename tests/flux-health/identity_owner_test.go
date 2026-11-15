package fluxhealth

import (
	"encoding/json"
	"github.com/fluxcd/pkg/ssa"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"os/exec"
	"reflect"
	"testing"
)

// kustomize-controller v1.9.5 uses SSA v0.76.2 SetOwnerLabels before apply.
// This ties the native admission fixture's tracked object to that actual transform;
// it is not a fake implementation of the controller or a live SSA ownership proof.
func TestIdentityEvidenceOwnerLabels(t *testing.T) {
	for _, ctx := range []string{"portal", "abcdefghijklmnopqrstuvwxyzabcde"} {
		t.Run(ctx, func(t *testing.T) {
			cmd := exec.Command("python3", "../../scripts/identity_foundation_cases.py")
			cmd.Env = append(cmd.Environ(), "IDENTITY_CONTEXT_FIXTURE="+ctx)
			raw, err := cmd.CombinedOutput()
			if err != nil {
				t.Fatalf("fixture: %v %s", err, raw)
			}
			var f struct {
				Cases []struct {
					Name              string
					Object, OldObject map[string]any
				}
			}
			if err = json.Unmarshal(raw, &f); err != nil {
				t.Fatal(err)
			}
			for _, tc := range f.Cases {
				if tc.Name != "intent-preserves-issuer" {
					continue
				}
				expected := &unstructured.Unstructured{Object: tc.Object}
				actual := expected.DeepCopy()
				actual.SetLabels((&unstructured.Unstructured{Object: tc.OldObject}).GetLabels())
				payloadCmd := exec.Command("python3", "-c", `import sys,json;sys.path.insert(0,'../../scripts');from test_finite_identity import Tests;from finite_identity import render;print(json.dumps(render(Tests().sample())['receipt-intent.yaml']))`)
				payloadRaw, payloadErr := payloadCmd.CombinedOutput()
				if payloadErr != nil {
					t.Fatalf("payload: %v %s", payloadErr, payloadRaw)
				}
				var payload map[string]any
				if err = json.Unmarshal(payloadRaw, &payload); err != nil {
					t.Fatal(err)
				}
				payloadLabels := (&unstructured.Unstructured{Object: payload}).GetLabels()
				if payloadLabels["platform.perkforge.io/owner"] != "tenant-identity-foundation-v1" || payloadLabels["app.kubernetes.io/managed-by"] != "perkforge-identity" || payloadLabels["perkforge.dev/context"] != "portal" || len(payloadLabels) != 3 {
					t.Fatal("desired payload must explicitly preserve bootstrap labels")
				}

				manager := ssa.NewResourceManager(nil, nil, ssa.Owner{Group: "kustomize.toolkit.fluxcd.io", Field: "kustomize-controller"})
				manager.SetOwnerLabels([]*unstructured.Unstructured{actual}, expected.GetLabels()["kustomize.toolkit.fluxcd.io/name"], "flux-system")
				if !reflect.DeepEqual(actual.Object, expected.Object) {
					t.Fatal("native SetOwnerLabels differs from admission fixture")
				}
				if len(actual.GetLabels()) != 5 {
					t.Fatal("expected exact bootstrap three plus tracking two")
				}
				manager.SetOwnerLabels([]*unstructured.Unstructured{actual}, expected.GetLabels()["kustomize.toolkit.fluxcd.io/name"], "flux-system")
				if !reflect.DeepEqual(actual.Object, expected.Object) {
					t.Fatal("owner-label repeat changed object")
				}
				return
			}
			t.Fatal("missing intent fixture")
		})
	}
}
