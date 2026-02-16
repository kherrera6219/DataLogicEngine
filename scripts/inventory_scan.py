
import os
import hashlib
import json
from collections import defaultdict

ROOT_DIR = r"c:\software\DataLogicEngine"
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", ".next", "dist", "build", 
    ".pytest_cache", ".vscode", ".idea", "htmlcov", "coverage"
}
IGNORE_EXTS = {".pyc", ".pyd", ".pyo", ".exe", ".dll", ".so", ".dylib", ".bin", ".obj", ".o", ".a", ".lib"}

def calculate_checksum(file_path):
    """Calculates SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def scan_directory(root_path):
    inventory = []
    content_map = defaultdict(list)
    name_map = defaultdict(list)
    
    print(f"Scanning {root_path}...")

    for root, dirs, files in os.walk(root_path):
        # Modify dirs in-place to skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if any(file.endswith(ext) for ext in IGNORE_EXTS):
                continue
                
            file_path = os.path.join(root, file)
            relative_path = os.path.relpath(file_path, root_path)
            
            try:
                stat = os.stat(file_path)
                size = stat.st_size
                
                # Calculate hash for duplicate content detection
                checksum = calculate_checksum(file_path)
                
                entry = {
                    "path": relative_path,
                    "name": file,
                    "size": size,
                    "hash": checksum
                }
                
                inventory.append(entry)
                
                if checksum:
                    content_map[checksum].append(relative_path)
                
                name_map[file].append(relative_path)
                
            except Exception as e:
                print(f"Error processing {relative_path}: {e}")

    return inventory, content_map, name_map

def main():
    inventory, content_map, name_map = scan_directory(ROOT_DIR)
    
    # Filter for actual duplicates
    content_duplicates = {k: v for k, v in content_map.items() if len(v) > 1}
    name_duplicates = {k: v for k, v in name_map.items() if len(v) > 1}
    
    report = {
        "summary": {
            "total_files": len(inventory),
            "unique_content_files": len(content_map),
            "content_duplicates_sets": len(content_duplicates),
            "name_duplicates_sets": len(name_duplicates)
        },
        "content_duplicates": content_duplicates,
        "name_duplicates": name_duplicates,
        # "inventory": inventory # Omit full inventory from main printed report to save space, save to file
    }
    
    output_path = os.path.join(ROOT_DIR, "inventory_report.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
        
    print(json.dumps(report["summary"], indent=2))
    print(f"\nReport saved to {output_path}")

    # Print top 10 content duplicates by size savings
    print("\n--- Top Duplicate Content Sets (Potential Cleanup) ---")
    sorted_dupes = sorted(content_duplicates.items(), key=lambda x: os.stat(os.path.join(ROOT_DIR, x[1][0])).st_size * (len(x[1]) - 1), reverse=True)
    
    for i, (checksum, paths) in enumerate(sorted_dupes[:20]):
        size = os.stat(os.path.join(ROOT_DIR, paths[0])).st_size
        print(f"{i+1}. Size: {size} bytes | Count: {len(paths)}")
        for p in paths:
            print(f"   - {p}")

if __name__ == "__main__":
    main()
