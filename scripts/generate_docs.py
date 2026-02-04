import os
import csv
from datetime import datetime
from pathlib import Path

# Configuration
ROOT_DIR = Path(r"c:\software\DataLogicEngine")
OUTPUT_CSV = ROOT_DIR / "docs" / "FILE_INVENTORY.csv"
OUTPUT_STRUCTURE = ROOT_DIR / "docs" / "GENERATED_STRUCTURE.md"

IGNORE_DIRS = {
    '.git', '.venv', '.idea', '__pycache__', 'node_modules', 
    'dist', 'build', '.next', 'coverage', '.pytest_cache', 
    'htmlcov', 'logs', 'tmp', '.gemini'
}

IGNORE_FILES = {
    '.DS_Store', 'Thumbs.db'
}

def get_file_info(path):
    stats = path.stat()
    return {
        'Path': str(path.relative_to(ROOT_DIR)),
        'Size_Bytes': stats.st_size,
        'Extension': path.suffix,
        'Last_Modified': datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }

def generate_inventory():
    print(f"Scanning {ROOT_DIR}...")
    file_list = []
    
    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES:
                continue
                
            file_path = Path(root) / file
            try:
                file_list.append(get_file_info(file_path))
            except Exception as e:
                print(f"Error reading {file_path}: {e}")

    # Write CSV
    print(f"Writing inventory to {OUTPUT_CSV}...")
    OUTPUT_CSV.parent.mkdir(exist_ok=True)
    with open(OUTPUT_CSV, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Path', 'Size_Bytes', 'Extension', 'Last_Modified'])
        writer.writeheader()
        writer.writerows(file_list)
    print(f"Inventory complete. {len(file_list)} files indexed.")
    return file_list

def generate_tree(file_list):
    print("Generating directory tree...")
    tree_lines = []
    
    # Simple tree generator for specific high-value directories
    target_dirs = ['backend', 'core', 'frontend', 'docs', 'tests']
    
    for target in target_dirs:
        target_path = ROOT_DIR / target
        if not target_path.exists():
            continue
            
        tree_lines.append(f"### {target}/")
        tree_lines.append("```text")
        
        # Get relative paths for this target
        paths = [f['Path'] for f in file_list if f['Path'].startswith(target)]
        
        # Build specific nested structure (simplified for docs)
        # We'll just show depth 2 for clarity in the summary
        seen_dirs = set()
        for p in sorted(paths):
            parts = Path(p).parts
            if len(parts) > 4: # Limit depth 
                continue
            
            # Print directories
            for i in range(1, len(parts)-1):
                d_path = Path(*parts[:i+1])
                if str(d_path) not in seen_dirs:
                    indent = "│   " * (i-1)
                    if i == 1:
                        tree_lines.append(f"{parts[i]}/")
                    else:
                         tree_lines.append(f"{indent}├── {parts[i]}/")
                    seen_dirs.add(str(d_path))
            
            # Print files (optional, maybe too noisy for full tree, keep to key files?)
            # interactive toggle: show only root files of dirs
            if len(parts) == 2:
                 tree_lines.append(f"├── {parts[-1]}")
        
        tree_lines.append("```\n")

    with open(OUTPUT_STRUCTURE, 'w', encoding='utf-8') as f:
        f.write("\n".join(tree_lines))
    print(f"Tree structure written to {OUTPUT_STRUCTURE}")

if __name__ == "__main__":
    files = generate_inventory()
    generate_tree(files)
