import os

def fix_imports(file_path):
    with open(file_path, 'r') as f:
        content = f.read()

    changed = False
    if 'from pydantic import BaseModel, Field, List' in content:
        content = content.replace('from pydantic import BaseModel, Field, List', 'from pydantic import BaseModel, Field')
        changed = True
    
    if 'from pydantic import BaseModel, Field, Optional' in content:
        content = content.replace('from pydantic import BaseModel, Field, Optional', 'from pydantic import BaseModel, Field')
        changed = True

    if changed:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

if __name__ == "__main__":
    ka_dir = os.path.join("backend", "knowledge_algorithms")
    files = [f for f in os.listdir(ka_dir) if f.startswith("ka_") and f.endswith(".py")]
    count = 0
    for f in files:
        if fix_imports(os.path.join(ka_dir, f)):
            count += 1
    print(f"Corrected imports in {count} KAs.")
