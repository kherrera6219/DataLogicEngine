import os
import hashlib

def get_file_hash(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        buf = f.read(65536)
        while len(buf) > 0:
            hasher.update(buf)
            buf = f.read(65536)
    return hasher.hexdigest()

def find_duplicates(root_dir):
    exclude_dirs = {'node_modules', '.git', '.next', '__pycache__', '.gemini', 'env', 'venv', 'dist', 'build', 'artifacts'}
    files_by_name = {}
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for name in files:
            if name == "__init__.py":
                continue
            path = os.path.join(root, name)
            if name not in files_by_name:
                files_by_name[name] = []
            files_by_name[name].append(path)
            
    duplicates = {name: paths for name, paths in files_by_name.items() if len(paths) > 1}
    return duplicates

if __name__ == "__main__":
    root = r"c:\software\DataLogicEngine"
    duplicates = find_duplicates(root)
    for name, paths in duplicates.items():
        print(f"--- {name} ---")
        for p in paths:
            try:
                h = get_file_hash(p)
                s = os.path.getsize(p)
                print(f"  {p} (Size: {s}, MD5: {h})")
            except Exception as e:
                print(f"  {p} (Error: {e})")
