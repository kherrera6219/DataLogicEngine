import yaml
import sys
import logging
from backend.knowledge_algorithm.registry import KARegistry
# Import all modules to ensure registration
from backend.knowledge_algorithm import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("KAAudit")

def audit_suite():
    registry_path = 'data/registries/ka_registry.yaml'
    output_path = 'audit_results.md'
    
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write("# KA Suite Audit Report\n\n")
        
        try:
            with open(registry_path, 'r') as f:
                yaml_registry = yaml.safe_load(f)
        except Exception as e:
            out.write(f"FATAL: Could not read registry: {e}\n")
            return
        
        yaml_kas = {item['KA_ID']: item for item in yaml_registry if item.get('Status') == 'Active'}
        yaml_ids = set(yaml_kas.keys())
        
        code_kas = KARegistry._registry
        code_ids = set(code_kas.keys())
        
        out.write(f"- **YAML Registry Active Count**: {len(yaml_ids)}\n")
        out.write(f"- **Code Implemented Count**: {len(code_ids)}\n\n")
        
        missing_in_code = yaml_ids - code_ids
        extra_in_code = code_ids - yaml_ids
        
        if missing_in_code:
            out.write(f"## ❌ MISSING KAs ({len(missing_in_code)})\n")
            for ka_id in sorted(missing_in_code):
                name = yaml_kas[ka_id].get('KA_Name', 'Unknown')
                out.write(f"- {ka_id}: {name}\n")
        else:
            out.write("## ✅ All Active KAs from YAML are implemented.\n")
            
        if extra_in_code:
            out.write(f"\n## ⚠️ EXTRA KAs in Code ({len(extra_in_code)})\n")
            for ka_id in sorted(extra_in_code):
                out.write(f"- {ka_id}\n")
                
        out.write("\n## Metadata Mismatches\n")
        mismatches = 0
        for ka_id in yaml_ids.intersection(code_ids):
            yaml_item = yaml_kas[ka_id]
            code_item = KARegistry._metadata[ka_id]
            
            y_name = yaml_item.get('KA_Name', '').strip()
            c_name = code_item.name.strip()
            if y_name != c_name:
                out.write(f"- **{ka_id}**: YAML='{y_name}' vs Code='{c_name}'\n")
                mismatches += 1
        
        if mismatches == 0:
            out.write("No metadata mismatches found.\n")

if __name__ == "__main__":
    audit_suite()
