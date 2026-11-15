package fluxhealth

import (
	"context"
	"encoding/json"
	"fmt"
	jsonpatch "github.com/evanphx/json-patch/v5"
	"github.com/fluxcd/pkg/ssa"
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/apis/meta/v1/unstructured"
	"k8s.io/apimachinery/pkg/types"
	"reflect"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"testing"
)

// No API server: intercept the actual pinned manager's sequence. Simulated SSA
// merging below is deliberately not a claim of native field-owner acceptance.
type cleanupClient struct {
	client.Client
	live          *unstructured.Unstructured
	stages        []string
	before, after *unstructured.Unstructured
}

func (c *cleanupClient) Get(_ context.Context, _ client.ObjectKey, o client.Object, _ ...client.GetOption) error {
	*o.(*unstructured.Unstructured) = *c.live.DeepCopy()
	return nil
}
func (c *cleanupClient) Patch(_ context.Context, o client.Object, p client.Patch, opts ...client.PatchOption) error {
	options := &client.PatchOptions{}
	for _, v := range opts {
		v.ApplyToPatch(options)
	}
	if p.Type() == types.JSONPatchType {
		c.stages = append(c.stages, "cleanup")
		raw, e := p.Data(o)
		if e != nil {
			return e
		}
		var ops []map[string]any
		if e = json.Unmarshal(raw, &ops); e != nil {
			return e
		}
		if len(ops) != 1 || ops[0]["op"] != "replace" || ops[0]["path"] != "/metadata/managedFields" {
			return fmt.Errorf("unexpected cleanup %s", raw)
		}
		c.before = c.live.DeepCopy()
		b, _ := json.Marshal(c.live.Object)
		patch, e := jsonpatch.DecodePatch(raw)
		if e != nil {
			return e
		}
		b, e = patch.Apply(b)
		if e != nil {
			return e
		}
		if e = json.Unmarshal(b, &c.live.Object); e != nil {
			return e
		}
		c.after = c.live.DeepCopy()
		*o.(*unstructured.Unstructured) = *c.live.DeepCopy()
		return nil
	}
	if p.Type() != types.ApplyPatchType {
		return fmt.Errorf("unexpected patch type")
	}
	merged := c.live.DeepCopy()
	desired := o.(*unstructured.Unstructured)
	labels := merged.GetLabels()
	for k, v := range desired.GetLabels() {
		labels[k] = v
	}
	merged.SetLabels(labels)
	annotations := merged.GetAnnotations()
	for k, v := range desired.GetAnnotations() {
		annotations[k] = v
	}
	merged.SetAnnotations(annotations)
	if len(options.DryRun) > 0 {
		c.stages = append(c.stages, "dryrun")
	} else {
		c.stages = append(c.stages, "apply")
		c.live = merged.DeepCopy()
	}
	*o.(*unstructured.Unstructured) = *merged
	return nil
}
func TestIdentityActualCleanupSequence(t *testing.T) {
	for _, receipt := range []string{"", "nonempty-private-receipt"} {
		t.Run(fmt.Sprintf("receipt-%d", len(receipt)), func(t *testing.T) {
			base := map[string]string{"app.kubernetes.io/managed-by": "perkforge-identity", "perkforge.dev/context": "portal", "platform.perkforge.io/owner": "tenant-identity-foundation-v1"}
			old := &unstructured.Unstructured{Object: map[string]any{"apiVersion": "v1", "kind": "ConfigMap", "metadata": map[string]any{"name": "portal-identity-evidence", "namespace": "tenant-identity-writer", "uid": "522e96ed-77e1-4dc9-b57c-e8281c761928", "resourceVersion": "1"}, "data": map[string]any{"receipt.json": receipt}}}
			old.SetLabels(base)
			old.SetAnnotations(map[string]string{"perkforge.dev/desired-invocation": "selected"})
			old.SetManagedFields([]metav1.ManagedFieldsEntry{{Manager: "kubectl-create", Operation: metav1.ManagedFieldsOperationUpdate, APIVersion: "v1", FieldsType: "FieldsV1", FieldsV1: &metav1.FieldsV1{Raw: []byte(`{"f:metadata":{"f:labels":{}}}`)}}})
			old.SetManagedFields(append(old.GetManagedFields(),
				metav1.ManagedFieldsEntry{Manager: "kustomize-controller", Operation: metav1.ManagedFieldsOperationUpdate, APIVersion: "v1", FieldsType: "FieldsV1", FieldsV1: &metav1.FieldsV1{Raw: []byte(`{"f:metadata":{"f:annotations":{}}}`)}},
				metav1.ManagedFieldsEntry{Manager: "identity-attestor", Operation: metav1.ManagedFieldsOperationUpdate, APIVersion: "v1", FieldsType: "FieldsV1", FieldsV1: &metav1.FieldsV1{Raw: []byte(`{"f:data":{"f:receipt.json":{}}}`)}}))
			c := &cleanupClient{live: old.DeepCopy()}
			m := ssa.NewResourceManager(c, nil, ssa.Owner{Group: "kustomize.toolkit.fluxcd.io", Field: "kustomize-controller"})
			desired := &unstructured.Unstructured{Object: map[string]any{"apiVersion": "v1", "kind": "ConfigMap", "metadata": map[string]any{"name": old.GetName(), "namespace": old.GetNamespace(), "uid": string(old.GetUID())}}}
			desired.SetAnnotations(old.GetAnnotations())
			desired.SetLabels(old.GetLabels())
			m.SetOwnerLabels([]*unstructured.Unstructured{desired}, "identity-portal", "flux-system")
			opts := ssa.DefaultApplyOptions()
			opts.Cleanup.FieldManagers = []ssa.FieldManager{{Name: "kubectl", OperationType: metav1.ManagedFieldsOperationUpdate}, {Name: "kustomize-controller", OperationType: metav1.ManagedFieldsOperationUpdate}}
			if _, e := m.Apply(context.Background(), desired, opts); e != nil {
				t.Fatal(e)
			}
			if !reflect.DeepEqual(c.stages, []string{"dryrun", "cleanup", "apply"}) {
				t.Fatalf("sequence %v", c.stages)
			}
			before, after := c.before.DeepCopy(), c.after.DeepCopy()
			before.SetManagedFields(nil)
			after.SetManagedFields(nil)
			if !reflect.DeepEqual(before.Object, after.Object) {
				t.Fatal("cleanup changed protected data/metadata")
			}
			if !reflect.DeepEqual(c.live.Object["data"], old.Object["data"]) || len(c.live.GetLabels()) != 5 {
				t.Fatal("apply receipt/owner mismatch")
			}
		})
	}
}
