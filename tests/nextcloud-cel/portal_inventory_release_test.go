package nextcloudcel

import (
 "context"
 "encoding/json"
 "os/exec"
 "testing"
 admissionv1 "k8s.io/api/admissionregistration/v1"
 "k8s.io/apimachinery/pkg/util/version"
 admissioncel "k8s.io/apiserver/pkg/admission/plugin/cel"
 "k8s.io/apiserver/pkg/cel/environment"
)

// Evaluate exact HelmRelease source-reference boundaries with the native CEL
// compiler. Live policy status additionally checks the installed CRD schema.
func TestPortalInventoryReleaseReferences(t *testing.T) {
 raw, err := exec.Command("python3", "../../scripts/portal_inventory_release_cases.py").CombinedOutput()
 if err != nil { t.Fatalf("%s: %v", raw, err) }
 var f struct { Policy admissionv1.ValidatingAdmissionPolicy; Cases []struct { Name string; Object map[string]any; Allowed bool } }
 if err = json.Unmarshal(raw, &f); err != nil { t.Fatal(err) }
 compiler := admissioncel.NewCompiler(environment.MustBaseEnvSet(version.MajorMinor(1,36)))
 for _, tc := range f.Cases { t.Run(tc.Name, func(t *testing.T) {
  allowed := true
  for _, v := range f.Policy.Spec.Validations {
   result := compiler.CompileCELExpression(expression{v.Expression,false}, admissioncel.OptionalVariableDeclarations{}, environment.NewExpressions)
   if result.Error != nil { t.Fatal(result.Error) }
   value,_,err := result.Program.ContextEval(context.Background(), map[string]any{"object":tc.Object,"oldObject":nil,"namespaceObject":nil,"request":map[string]any{}})
   if err != nil || value.Value() != true { allowed = false }
  }
  if allowed != tc.Allowed { t.Fatalf("allowed=%v want=%v",allowed,tc.Allowed) }
 }) }
}
