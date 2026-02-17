
import os
import glob

KA_DIR = r"c:\software\DataLogicEngine\backend\knowledge_algorithms"
OUT_PATH = os.path.join(KA_DIR, "ka_registry.yaml")

def gen_registry():
    files = glob.glob(os.path.join(KA_DIR, "ka_*.py"))
    
    entries = {}
    
    for f in files:
        fname = os.path.basename(f)
        if fname == "ka_master_controller.py":
            continue
        if fname.startswith("ka_legacy"):
            continue # just in case
        
        # ka_01_... -> KA-001
        # ka_113_... -> KA-113
        parts = fname.split("_")
        if len(parts) < 2:
            continue
        
        num_str = parts[1]
        if not num_str.isdigit():
            continue
        
        ka_id = f"KA-{int(num_str):03d}"
        mod_name = fname.replace(".py", "")
        entries[ka_id] = f"backend.knowledge_algorithms.{mod_name}.run"

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        f.write("ka_registry:\n")
        # Sort keys
        for kid in sorted(entries.keys()):
            f.write(f'  "{kid}": "{entries[kid]}"\n')
            
        f.write('\n  # Master Controller\n')
        f.write('  "KA-Master": "backend.knowledge_algorithms.ka_master_controller.run"\n')

    print(f"Generated registry with {len(entries)} entries.")

if __name__ == "__main__":
    gen_registry()
