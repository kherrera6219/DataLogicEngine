import pytest
from knowledge_algorithms.ka_120_purple_team import KA120PurpleTeam

class TestAdversarial:
    
    def test_purple_team_execution(self):
        """Verify KA-120 runs attacks and reports results."""
        agent = KA120PurpleTeam()
        
        # Run in simulation mode (LOW intensity)
        result = agent.run({
            "data": {
                "target": "mock_truth_engine",
                "intensity": "LOW",
                "vectors": ["JAILBREAK_CLASSIC", "PII_EXTRACTION"]
            }
        })
        
        assert result["success"] is True
        output = result["output"]
        assert len(output["results"]) == 2
        
        # Check specific attack outcome (Simulation logic should block these)
        jailbreak = next(r for r in output["results"] if r["vector"] == "JAILBREAK_CLASSIC")
        assert jailbreak["outcome"] == "BLOCKED"
        assert "KA-61" in jailbreak["defense_layer"]

    def test_purple_team_scoring(self):
        """Verify security score calculation."""
        agent = KA120PurpleTeam()
        
        # Logic ensures score is 100 if all blocked
        result = agent.run({
            "data": {
                "target": "mock",
                "vectors": ["JAILBREAK_CLASSIC"]
            }
        })
        
        assert result["success"] is True
        output = result["output"]
        assert output["security_score"] == 100
