
import os
import shutil
import glob

KA_DIR = r"c:\software\DataLogicEngine\knowledge_algorithms"
LEGACY_DIR = os.path.join(KA_DIR, "legacy")

def migrate():
    # Find all ka_XX_*.py files
    files = glob.glob(os.path.join(KA_DIR, "ka_*.py"))
    
    count = 0
    for f in files:
        fname = os.path.basename(f)
        if fname == "ka_master_controller.py":
            continue
            
        # Move to legacy
        dst = os.path.join(LEGACY_DIR, fname)
        shutil.move(f, dst)
        print(f"Moved {fname} -> legacy/")
        count += 1
        
    print(f"Moved {count} legacy files.")

if __name__ == "__main__":
    migrate()
