from ukg_sdk.workflow import WorkflowRunner, ComplexityTier

def test_workflow_loads():
    runner = WorkflowRunner.load_default()
    res = runner.run_local_stub(query="hello", tier=ComplexityTier.trivial)
    assert res.tier == ComplexityTier.trivial.value
