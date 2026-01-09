
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
    print(f"- {server.name} (v{server.version}): {server.description}")
    print(f"  Tools: {[t.name for t in server.tools.values()]}")
