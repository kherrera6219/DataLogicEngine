
from ukg_sdk.workflow import WorkflowRunner, ComplexityTier, WorkflowResult
from ukg_sdk.truth_engine.core import TruthEngine

class TestWorkflowRunner:
    def test_load_default(self):
        # This requires workflow.json to exist in data dir
        runner = WorkflowRunner.load_default()
        assert runner.workflow is not None
        assert runner.truth_engine is not None
        assert isinstance(runner.truth_engine, TruthEngine)

    def test_tier_selection(self):
        # Create a mock workflow dict
        workflow = {
            "tiers": {
                "TRIVIAL": {"pipeline": ["KA-001"]},
                "HARD": {"pipeline": ["KA-001", "KA-002"]}
            }
        }
        runner = WorkflowRunner(workflow=workflow)
        
        tier = runner.choose_tier(complexity_score=0.1)
        assert tier == ComplexityTier.trivial
        
        tier = runner.choose_tier(complexity_score=0.9)
        assert tier == ComplexityTier.extreme

    def test_run_local_stub(self):
        workflow = {
            "tiers": {
                "TRIVIAL": {"pipeline": ["KA-001"]}
            }
        }
        runner = WorkflowRunner(workflow=workflow, truth_engine=TruthEngine())
        
        result = runner.run_local_stub(query="test", tier=ComplexityTier.trivial)
        assert isinstance(result, WorkflowResult)
        assert result.tier == "TRIVIAL"
        assert result.answer["recommended_pipeline"] == ["KA-001"]

    def test_run_local_stub_supports_default_tier_system_schema(self):
        workflow = {
            "tier_system": {
                "tiers": [
                    {
                        "tier": "trivial",
                        "workflow_steps": ["step1", "step2"],
                        "ka_pipeline_hint": ["KA-004", "KA-005"],
                    }
                ]
            }
        }
        runner = WorkflowRunner(workflow=workflow, truth_engine=TruthEngine())

        result = runner.run_local_stub(query="test", tier=ComplexityTier.trivial)

        assert result.tier == "TRIVIAL"
        assert result.answer["recommended_pipeline"] == ["KA-004", "KA-005"]
