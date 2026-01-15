
import json
import os
import glob
import re

REGISTRY_PATH = r"c:\software\DataLogicEngine\sdk\UKG_Python_SDK\ukg_sdk\data\ka_registry_by_id.json"
KA_DIR = r"c:\software\DataLogicEngine\knowledge_algorithms"

def audit_kas():
    with open(REGISTRY_PATH, 'r', encoding='utf-8') as f:
        registry = json.load(f)

    # Get existing files
    existing_files = glob.glob(os.path.join(KA_DIR, "ka_*.py"))
    
    # Map ID to File
    id_to_file = {}
    file_map = {} # filename -> id (inferred)
    
    for fw in existing_files:
        fname = os.path.basename(fw)
        # Try extract ID
        match = re.search(r"ka_(\d+)", fname)
        if match:
            kid = f"KA-{int(match.group(1)):03d}" # KA-001
            # Handle 2-digit naming in file vs 3-digit in registry
            kid_alt = f"KA-{int(match.group(1)):02d}"
            
            # Use 3-digit standard
            kid_std = f"KA-{int(match.group(1)):03d}"
            
            id_to_file[kid_std] = fname
            file_map[fname] = kid_std

    audit_results = []
    
    for ka_id in sorted(registry.keys()):
        ka_meta = registry[ka_id]
        name = ka_meta.get("KA_Name", "Unknown")
        status = "MISSING"
        existing = id_to_file.get(ka_id)
        
        # Check if 2-digit version exists (e.g. KA-20 vs KA-020)
        ka_num = int(ka_id.split("-")[1])
        # Try looking for ka_20... or ka_020...
        if not existing:
             # loose search
             for f in existing_files:
                 if f"ka_{ka_num}_" in os.path.basename(f) or f"ka_{ka_num:02d}_" in os.path.basename(f):
                     existing = os.path.basename(f)
                     break

        if existing:
            status = "EXISTS"
        
        audit_results.append({
            "id": ka_id,
            "name": name,
            "status": status,
            "file": existing or ""
        })

    print(f"{'ID':<10} | {'Status':<10} | {'File':<40} | {'Name'}")
    print("-" * 100)
    for row in audit_results:
        print(f"{row['id']:<10} | {row['status']:<10} | {row['file']:<40} | {row['name']}")

if __name__ == "__main__":
    audit_kas()
