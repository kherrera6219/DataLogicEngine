
import os
import csv
import time

ROOT_DIR = r"c:\software\DataLogicEngine"
IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', 'dist', '.next', 'venv', 'env', 
    '.pytest_cache', '.agent', '.gemini', 'coverage', '.idea', '.vscode',
    'build', 'egg-info', '.mypy_cache'
}

inventory_file = os.path.join(ROOT_DIR, "FULL_FILE_INVENTORY.csv")
map_file = os.path.join(ROOT_DIR, "FILE_STRUCTURE_MAP.txt")

def generate_inventory_and_map():
    print(f"Scanning {ROOT_DIR}...")
    
    # Data collection for map
    file_structure = {}

    with open(inventory_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Path', 'Size_Bytes', 'Extension', 'Last_Modified']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for root, dirs, files in os.walk(ROOT_DIR):
            # In-place filtering of directories to prune traversal
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for f in files:
                if f == "update_docs.py": continue 
                
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, ROOT_DIR)
                
                try:
                    stats = os.stat(full_path)
                    writer.writerow({
                        'Path': rel_path, 
                        'Size_Bytes': stats.st_size, 
                        'Extension': os.path.splitext(f)[1],
                        'Last_Modified': time.ctime(stats.st_mtime)
                    })
                except OSError:
                    pass # Skip errors
                    
    print(f"Inventory written to {inventory_file}")

    # Generate Tree Map
    with open(map_file, 'w', encoding='utf-8') as f:
        f.write(f"Project: DataLogicEngine (File Structure Map)\n")
        f.write(f"Generated: {time.ctime()}\n")
        f.write(f"Root: {ROOT_DIR}\n")
        f.write("="*50 + "\n\n")
        
        for root, dirs, files in os.walk(ROOT_DIR):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            level = root.replace(ROOT_DIR, '').count(os.sep)
            indent = '    ' * level
            folder_name = os.path.basename(root)
            if folder_name == '': folder_name = '.'
            
            f.write(f"{indent}[{folder_name}/]\n")
            
            subindent = '    ' * (level + 1)
            for file in sorted(files):
                 f.write(f"{subindent}{file}\n")

    print(f"Map written to {map_file}")

if __name__ == "__main__":
    generate_inventory_and_map()
