import os
import hashlib
from collections import defaultdict

def get_file_hash(filepath):
    hasher = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except Exception:
        return None

def find_duplicates(root_dir):
    exclude_dirs = {'node_modules', '.git', '.next', 'dist', 'out', 'build', '.storybook', 'storybook-static'}
    files_by_name = defaultdict(list)
    files_by_hash = defaultdict(list)
    
    print(f"Scanning {root_dir}...")
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for name in files:
            if name.startswith('.'):
                continue
            if name.endswith('.d.ts'):
                continue
            
            path = os.path.join(root, name)
            
            # Group by Name
            files_by_name[name].append(path)
            
            # Group by Content
            file_hash = get_file_hash(path)
            if file_hash:
                files_by_hash[file_hash].append(path)

    # Filter for duplicates
    dup_names = {k: v for k, v in files_by_name.items() if len(v) > 1}
    dup_content = {k: v for k, v in files_by_hash.items() if len(v) > 1}
    
    return dup_names, dup_content

if __name__ == "__main__":
    frontend_dir = os.path.join(os.getcwd(), "frontend")
    if not os.path.exists(frontend_dir):
        print("Frontend directory not found!")
        exit(1)
        
    names, contents = find_duplicates(frontend_dir)
    
    print("\n=== DUPLICATE FILENAMES (potential refactor targets) ===")
    for name, paths in names.items():
        # Filter out obvious structural duplicates like 'page.tsx', 'layout.tsx', 'index.ts'
        if name in ['page.tsx', 'layout.tsx', 'loading.tsx', 'index.ts', 'index.tsx', 'globals.css', 'styles.css']:
            continue
        print(f"\nFile: {name}")
        for p in paths:
            print(f"  {p}")

    print("\n=== IDENTICAL CONTENT (exact duplicates) ===")
    for hash_val, paths in contents.items():
        print(f"\nHash: {hash_val}")
        for p in paths:
            print(f"  {p}")
