package fluxhealth

import (
	"context"
	"encoding/json"
	"github.com/fluxcd/cli-utils/pkg/kstatus/status"
	"github.com/fluxcd/pkg/apis/kustomize"
	fluxcel "github.com/fluxcd/pkg/runtime/cel"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"os/exec"
	"testing"
)

// Actual health evaluator dependencies selected by kustomize-controller v1.9.5.
func TestIdentityAdmissionHealth(t *testing.T) {
	cmd := exec.Command("python3", "-c", `import sys,json;sys.path.insert(0,'../../scripts');from test_identity_gitops_ownership import sample;from identity_gitops_ownership import build;a,c=sample();print(json.dumps(build(a,c)['reconciliations'][0]['spec']['healthCheckExprs'][0]))`)
	raw, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("fixture: %v %s", err, raw)
	}
	var hc kustomize.CustomHealthCheck
	if err = json.Unmarshal(raw, &hc); err != nil {
		t.Fatal(err)
	}
	if _, err = fluxcel.NewStatusReader([]kustomize.CustomHealthCheck{hc}); err != nil {
		t.Fatal(err)
	}
	evaluator, err := fluxcel.NewStatusEvaluator(&hc.HealthCheckExpressions)
	if err != nil {
		t.Fatal(err)
	}
	if _, err = fluxcel.NewStatusEvaluator(&kustomize.HealthCheckExpressions{Current: "has(status) && " + hc.Current}); err == nil {
		t.Fatal("old bare has(status) unexpectedly parsed")
	}
	for _, tc := range []struct {
		name   string
		status map[string]any
		ready  bool
	}{
		{"empty-warnings", map[string]any{"observedGeneration": int64(2), "typeChecking": map[string]any{"expressionWarnings": []any{}}}, true},
		{"omitted-warnings", map[string]any{"observedGeneration": int64(2), "typeChecking": map[string]any{}}, true},
		{"missing-status", nil, false},
		{"missing-generation", map[string]any{"typeChecking": map[string]any{}}, false},
		{"stale-generation", map[string]any{"observedGeneration": int64(1), "typeChecking": map[string]any{}}, false},
		{"missing-typechecking", map[string]any{"observedGeneration": int64(2)}, false},
		{"warning", map[string]any{"observedGeneration": int64(2), "typeChecking": map[string]any{"expressionWarnings": []any{map[string]any{"warning": "bad expression"}}}}, false},
		{"null-warnings", map[string]any{"observedGeneration": int64(2), "typeChecking": map[string]any{"expressionWarnings": nil}}, false},
		{"string-generation", map[string]any{"observedGeneration": "2", "typeChecking": map[string]any{}}, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			obj := map[string]any{"apiVersion": hc.APIVersion, "kind": hc.Kind, "metadata": map[string]any{"name": "fixture", "generation": int64(2)}}
			if tc.status != nil {
				obj["status"] = tc.status
			}
			result, err := evaluator.Evaluate(context.Background(), &unstructured.Unstructured{Object: obj})
			ready := err == nil && result != nil && result.Status == status.CurrentStatus
			if ready != tc.ready {
				t.Fatalf("ready=%v want=%v result=%+v err=%v", ready, tc.ready, result, err)
			}
		})
	}
}
