
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask
from core.mcp.mcp_manager import MCPManager

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
manager = MCPManager()

print("Setting up default servers...")
manager.setup_default_servers()

print("\nRegistered Servers:")
for server in manager.servers.values():
    tools = list(server.tools.values())
    print(f"- {server.name} (v{server.version}): {server.description}")
    print(f"  Total Tools Registered: {len(tools)}")
    if len(tools) > 0:
        print(f"  Sample Tools: {[t.name for t in tools[:5]]}...")

# Check for target count
ukg_server = manager.get_server_by_name("DataLogicEngine-UKG")
if ukg_server:
    count = len(ukg_server.tools)
    if count == 277:
        print(f"\nSUCCESS: Exactly {count} tools registered in UKG server.")
    else:
        print(f"\nWARNING: Tool count mismatch. Expected 277, found {count}.")
