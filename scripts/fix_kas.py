import os
import re

def fix_ka(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    # Check if it overrides run and missing _run_logic
    if 'def run(self, input_data: Dict[str, Any])' in content and '_run_logic' not in content:
        print(f"Fixing {file_path}...")
        
        # 1. Add Pydantic imports if missing
        if 'from pydantic import BaseModel, Field' not in content:
            content = content.replace('from typing import Dict, Any', 'from typing import Dict, Any, List, Optional\nfrom pydantic import BaseModel, Field')

        # 2. Extract KA ID from filename/content
        ka_match = re.search(r'KA-(\d+)', content)
        ka_num = ka_match.group(1) if ka_match else "XXX"
        
        # 3. Create a generic Input Schema based on observed usage
        # We'll use a flexible schema that allows extra fields to avoid breaking legacy calls
        schema_name = f"KA{ka_num}Input"
        schema_code = f"\nclass {schema_name}(BaseModel):\n    class Config:\n        extra = 'allow'\n"
        
        # Insert schema before the class definition
        class_start = re.search(r'class \w+\(KnowledgeAlgorithm\):', content).start()
        content = content[:class_start] + schema_code + content[class_start:]
        
        # 4. Update the class to use the new schema
        content = re.sub(r'(class \w+\(KnowledgeAlgorithm\):)', rf'\1\n    input_schema = {schema_name}', content)
        
        # 5. Rename run to _run_logic and update signature
        content = content.replace('def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:', 
                                  f'def _run_logic(self, input_data: {schema_name}) -> Dict[str, Any]:')
        
        # 6. Adjust input_data usage: since we use extra='allow', we can use .model_dump() or just access model fields.
        # However, the legacy code uses .get(). We can convert input_data to dict at the start of _run_logic.
        content = content.replace(f'def _run_logic(self, input_data: {schema_name}) -> Dict[str, Any]:',
                                  f'def _run_logic(self, input_data: {schema_name}) -> Dict[str, Any]:\n        input_dict = input_data.model_dump()')
        
        # Replace input_data.get with input_dict.get
        # Simple replacement might be risky, but these KAs are very simple.
        content = content.replace('input_data.get', 'input_dict.get')
        
        # 7. Final cleanup: ensure we don't have double definitions if we ran before
        # (This is a one-off script, so we keep it simple)

        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

if __name__ == "__main__":
    ka_dir = os.path.join("backend", "knowledge_algorithms")
    files = [f for f in os.listdir(ka_dir) if f.startswith("ka_") and f.endswith(".py")]
    count = 0
    for f in files:
        if fix_ka(os.path.join(ka_dir, f)):
            count += 1
    print(f"Fixed {count} KAs.")
