"""
Comprehensive Import Test for Phases 1-4
"""
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

print("Testing imports for all Phase 1-4 files...")
print("=" * 60)

try:
    # Phase 1: Core Intelligence
    print("\n[Phase 1: Core Intelligence]")
    from backend.simulation.simulation_engine import SimulationEngine, create_simulation_engine
    print("  ✓ SimulationEngine")
    
    from backend.quad_persona.quad_engine import QuadPersonaEngine, create_quad_persona_engine
    print("  ✓ QuadPersonaEngine")
    
    # Phase 2: MCP Server
    print("\n[Phase 2: MCP Server]")
    from backend.mcp_server.router import MCPRouter
    print("  ✓ MCPRouter")
    
    from backend.mcp_server.registry import ToolRegistry, registry
    print("  ✓ ToolRegistry")
    
    from backend.mcp_server.tools import salesforce, jira
    print("  ✓ Salesforce Tools")
    print("  ✓ Jira Tools")
    
    # Phase 3: Multimodal
    print("\n[Phase 3: Multimodal Services]")
    from backend.services.document_processor import DocumentProcessor, document_processor
    print("  ✓ DocumentProcessor")
    
    from backend.services.audio_service import AudioService, audio_service
    print("  ✓ AudioService")
    
    from backend.services.video_service import VideoService, video_service
    print("  ✓ VideoService")
    
    # Phase 4: Trust & Governance
    print("\n[Phase 4: Trust & Governance]")
    from backend.truth_engine.truth_link.blockchain_adapter import BlockchainAdapter, MerkleTree, blockchain_adapter
    print("  ✓ BlockchainAdapter")
    print("  ✓ MerkleTree")
    
    from backend.security.pii_redaction import PIIRedactor, pii_redactor
    print("  ✓ PIIRedactor")
    
    from backend.security.prompt_injection_shield import PromptInjectionShield, prompt_shield
    print("  ✓ PromptInjectionShield")
    
    from backend.reports.compliance import ComplianceReportGenerator, compliance_reporter, ComplianceFramework
    print("  ✓ ComplianceReportGenerator")
    
    print("\n" + "=" * 60)
    print("ALL IMPORTS SUCCESSFUL ✓")
    print("=" * 60)
    
    # Quick instantiation test
    print("\nInstantiation Test:")
    sim_engine = create_simulation_engine()
    print("  ✓ SimulationEngine instance created")
    
    quad_engine = create_quad_persona_engine()
    print("  ✓ QuadPersonaEngine instance created")
    
    mcp_router = MCPRouter()
    print("  ✓ MCPRouter instance created")
    
    print("\n✅ All Phase 1-4 files are syntactically correct and importable!")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ Error: {e}")
    sys.exit(1)
