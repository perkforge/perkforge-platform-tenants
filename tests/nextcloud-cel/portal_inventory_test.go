package nextcloudcel

import (
	"context"
	"encoding/json"
	"github.com/google/cel-go/cel"
	admissionv1 "k8s.io/api/admissionregistration/v1"
	"k8s.io/apimachinery/pkg/api/meta"
	"k8s.io/apimachinery/pkg/runtime/schema"
	"k8s.io/apimachinery/pkg/util/version"
	admissioncel "k8s.io/apiserver/pkg/admission/plugin/cel"
	"k8s.io/apiserver/pkg/admission/plugin/policy/validating"
	"k8s.io/apiserver/pkg/cel/environment"
	"os"
	"os/exec"
	"testing"
)

// Render the actual published app offline; this does not activate the paused chain.
func TestPortalInventoryConfigMapAdmission(t *testing.T) {
	raw, err := exec.Command("python3", "../../scripts/portal_inventory_admission_cases.py").CombinedOutput()
	if err != nil {
		t.Fatalf("%s: %v", raw, err)
	}
	var f struct {
		Policy admissionv1.ValidatingAdmissionPolicy
		Params map[string]any
		Cases  []struct {
			Name    string
			Object  map[string]any
			Allowed bool
		}
	}
	if err = json.Unmarshal(raw, &f); err != nil {
		t.Fatal(err)
	}
	// Require the same exact native OpenAPI schema used by the existing CI job.
	path := os.Getenv("NEXTCLOUD_OPENAPI")
	if path == "" {
		t.Fatal("NEXTCLOUD_OPENAPI is required for physical admission type checking")
	}
	schemaBytes, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var schemas struct{ Definitions fixtureSchemas }
	if err = json.Unmarshal(schemaBytes, &schemas); err != nil {
		t.Fatal(err)
	}
	mapper := meta.NewDefaultRESTMapper(nil)
	mapper.Add(schema.GroupVersionKind{Group: "apps", Version: "v1", Kind: "Deployment"}, meta.RESTScopeNamespace)
	mapper.Add(schema.GroupVersionKind{Group: "", Version: "v1", Kind: "ConfigMap"}, meta.RESTScopeNamespace)
	checker := validating.TypeChecker{SchemaResolver: schemas.Definitions, RestMapper: mapper}
	if warnings := checker.Check(&f.Policy); len(warnings) > 0 {
		t.Fatalf("type warnings: %+v", warnings)
	}
	base := environment.MustBaseEnvSet(version.MajorMinor(1, 36))
	env, err := base.Extend(environment.VersionedOptions{IntroducedVersion: version.MajorMinor(1, 36), EnvOptions: []cel.EnvOption{cel.Variable("variables", cel.DynType)}})
	if err != nil {
		t.Fatal(err)
	}
	compiler := admissioncel.NewCompiler(env)
	for _, tc := range f.Cases {
		t.Run(tc.Name, func(t *testing.T) {
			vars := map[string]any{}
			bindings := map[string]any{"object": tc.Object, "oldObject": nil, "namespaceObject": nil, "request": map[string]any{"userInfo": map[string]any{"username": "system:serviceaccount:tenant-portal-config:portal-deployer"}}, "params": f.Params, "variables": vars}
			evaluate := func(source string, variable bool) (any, error) {
				r := compiler.CompileCELExpression(expression{source, variable}, admissioncel.OptionalVariableDeclarations{HasParams: true}, environment.NewExpressions)
				if r.Error != nil {
					t.Fatalf("compile %s: %v", source, r.Error)
				}
				value, _, err := r.Program.ContextEval(context.Background(), bindings)
				return value, err
			}
			for _, v := range f.Policy.Spec.Variables {
				value, err := evaluate(v.Expression, true)
				if err != nil {
					t.Fatal(err)
				}
				vars[v.Name] = value
			}
			allowed := true
			for _, v := range f.Policy.Spec.Validations {
				value, err := evaluate(v.Expression, false)
				if err != nil {
					allowed = false
					continue
				}
				if value.(interface{ Value() any }).Value() != true {
					allowed = false
				}
			}
			if allowed != tc.Allowed {
				t.Fatalf("allowed=%v want=%v", allowed, tc.Allowed)
			}
		})
	}
}
