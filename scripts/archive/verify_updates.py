import sys
sys.path.append('c:\\software\\DataLogicEngine')

def test_imports():
    print("Testing imports...")
    try:
        from core.axes.axis_system import AxisSystem
        print("PASS: AxisSystem imported")
        
        system = AxisSystem()
        print("PASS: AxisSystem initialized")
        
        # Verify Axes 1-17 names
        expected_axes = {
            3: "Honeycomb System",
            6: "Octopus Node",
            7: "Spiderweb Node", 
            14: "Risk & Impact",
            15: "Performance & Optimization",
            16: "Ethics & Bias",
            17: "Learning & Adaptation"
        }
        
        for k, name in expected_axes.items():
            actual = system.axes.get(k, {}).get("name")
            if actual == name:
                print(f"PASS: Axis {k} name is '{name}'")
            else:
                print(f"FAIL: Axis {k} name expected '{name}', got '{actual}'")
                
    except Exception as e:
        print(f"FAIL: AxisSystem error: {e}")

    try:
        from simulation.layer6_neural_analysis import Layer6NeuralAnalysis
        print("PASS: Layer6NeuralAnalysis imported")
        Layer6NeuralAnalysis()
        print("PASS: Layer6NeuralAnalysis initialized")
    except Exception as e:
        print(f"FAIL: Layer6NeuralAnalysis error: {e}")

    try:
        from simulation.refinement_workflow import RefinementWorkflow
        print("PASS: RefinementWorkflow imported")
        rw = RefinementWorkflow()
        steps = rw._define_default_workflow()
        print(f"PASS: RefinementWorkflow initialized with {len(steps)} steps")
        if len(steps) == 12:
            print("PASS: Workflow has exact 12 steps")
        else:
            print(f"FAIL: Workflow has {len(steps)} steps, expected 12")
    except Exception as e:
        print(f"FAIL: RefinementWorkflow error: {e}")

    try:
        from backend.truth_engine.truth_core.personas import PersonaEnhancer
        print("PASS: PersonaEnhancer imported")
        pe = PersonaEnhancer()
        personas = pe.TRUTH_PERSONAS
        expected_p = ['knowledge_expert', 'sector_expert', 'regulatory_expert', 'compliance_expert']
        if all(p in personas for p in expected_p):
            print("PASS: All 4 Quad Personas present")
        else:
            print(f"FAIL: Missing personas. Found: {list(personas.keys())}")
    except Exception as e:
        print(f"FAIL: PersonaEnhancer error: {e}")

if __name__ == "__main__":
    test_imports()
