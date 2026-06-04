import asyncio
import os
import sys
import logging
from pyinstrument import Profiler

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from core.simulation.legacy_simulation_engine import SimulationEngine

# Mock LLM Gateway to avoid real API costs/latency for profiling logic
class MockLLMGateway:
    async def chat_completion(self, messages, temperature, max_tokens):
        await asyncio.sleep(0.1) # Simulate network latency
        return {'content': "Mocked response for profiling."}

async def run_profile():
    print("Initializing Profiler...")
    profiler = Profiler(async_mode='enabled')
    profiler.start()

    print("Running Simulation...")
    engine = SimulationEngine(llm_gateway=MockLLMGateway())
    sim_id = engine.create_simulation("Test Query", {})
    
    try:
        result = await engine.run_simulation(sim_id, depth="quick", timeout=10)
        print(f"Simulation completed. Events: {len(result['events'])}")
    except Exception as e:
        print(f"Simulation failed: {e}")

    profiler.stop()
    
    output_html = profiler.output_html()
    with open('simulation_profile.html', 'w') as f:
        f.write(output_html)
    
    print("Profile saved to simulation_profile.html")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_profile())
