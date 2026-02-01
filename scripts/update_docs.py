
import os
import csv
import json
from pathlib import Path

ROOT_DIR = Path(r"c:\software\DataLogicEngine")
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", ".next", "dist", "build", 
    ".pytest_cache", ".vscode", ".idea", "htmlcov", "coverage"
}

def generate_inventory():
    inventory = []
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            file_path = Path(root) / file
            rel_path = file_path.relative_to(ROOT_DIR)
            try:
                stat = file_path.stat()
                inventory.append({
                    "FullName": str(file_path),
                    "Length": stat.st_size,
                    "LastWriteTime": stat.st_mtime
                })
            except Exception:
                pass
    
    csv_path = ROOT_DIR / "FULL_FILE_INVENTORY.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["FullName", "Length", "LastWriteTime"])
        writer.writeheader()
        writer.writerows(inventory)
    print(f"Generated {csv_path}")

def generate_structure_map():
    output = ["Project Structure Map (Updated)\n"]
    
    def walk(path, prefix=""):
        items = sorted(os.listdir(path))
        items = [i for i in items if i not in IGNORE_DIRS and not i.startswith('.')]
        
        for i, item in enumerate(items):
            item_path = path / item
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            output.append(f"{prefix}{current_prefix}{item}")
            
            if item_path.is_dir():
                next_prefix = prefix + ("    " if is_last else "│   ")
                walk(item_path, next_prefix)

    walk(ROOT_DIR)
    
    map_path = ROOT_DIR / "FILE_STRUCTURE_MAP.txt"
    with open(map_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(output))
    print(f"Generated {map_path}")

if __name__ == "__main__":
    generate_inventory()
    generate_structure_map()
