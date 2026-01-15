
import json
import os
import re

REGISTRY_PATH = r"c:\software\DataLogicEngine\sdk\UKG_Python_SDK\ukg_sdk\data\ka_registry_by_id.json"
KA_DIR = r"c:\software\DataLogicEngine\knowledge_algorithms"

def create_stubs():
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    created_count = 0
    
    for ka_id, meta in registry.items():
        # KA-XXX
        num_str = ka_id.split("-")[1]
        num = int(num_str)
        
        # We only auto-create stubs for 61-114, plus specific ones we know we want (113, 004, etc) if missing
        # Actually user said "move them all... ID the KAs that need to be created".
        # I will create ALL missing ones to ensure complete coverage 1-114.
        
        # Check if exists
        # Pattern: ka_XX_... or ka_XXX_...
        pattern = f"ka_{num:02d}_"
        pattern3 = f"ka_{num:03d}_"
        
        exists = False
        for f in os.listdir(KA_DIR):
            if f.startswith(pattern) or f.startswith(pattern3):
                exists = True
                break
        
        if exists:
            continue
            
        # Create it
        name_slug = meta.get("KA_Name", "unknown").lower().replace(" ", "_").replace("-", "_").replace("/", "_")
        # remove special chars
        name_slug = re.sub(r'[^a-z0-9_]', '', name_slug)
        
        filename = f"ka_{num:02d}_{name_slug}.py" # Using 2 digit for consistency with existing 01-60
        if num >= 100:
             filename = f"ka_{num:03d}_{name_slug}.py"
             
        filepath = os.path.join(KA_DIR, filename)
        
        # Content
        content = f'''"""
{ka_id}: {meta.get("KA_Name")}
{meta.get("Purpose")}

Category: {meta.get("Category")}
Primary Layers: {meta.get("Primary_Layers")}
Version: {meta.get("Version")}
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def run(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute {ka_id}: {meta.get("KA_Name")}
    
    Args:
        context (Dict): Shared context
        
    Returns:
        Dict: Updated context or result
    """
    logger.info(f"Executing {ka_id} ({meta.get("KA_Name")})")
    
    # Placeholder Logic
    # In a real implementation, this would perform {meta.get("Category")} logic.
    
    return {{
        "ka_id": "{ka_id}",
        "status": "executed_stub",
        "description": "{meta.get("Purpose")}"
    }}

class {meta.get("Short_Name", "KA").replace("-", "")}Engine:
    def process(self, context):
        return run(context)
'''
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"Created {filename}")
        created_count += 1

    print(f"Total Created: {created_count}")

if __name__ == "__main__":
    create_stubs()
