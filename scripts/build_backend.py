import os
import shutil
import subprocess
import sys

def build():
    print("--- Starting DataLogic_Backend Build ---")
    
    # Check for pyinstaller
    try:
        subprocess.run([sys.executable, '-m', 'PyInstaller', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: PyInstaller not found. Please install it with 'pip install pyinstaller'")
        sys.exit(1)

    # Clean previous builds
    folders_to_clean = ['build', 'dist']
    for folder in folders_to_clean:
        if os.path.exists(folder):
            print(f"Cleaning {folder}...")
            shutil.rmtree(folder)

    # Run PyInstaller
    print("Running PyInstaller...")
    try:
        # Use the spec file for configuration, run via python -m to avoid PATH issues
        subprocess.run([sys.executable, '-m', 'PyInstaller', 'backend.spec', '--noconfirm'], check=True)
        print("PyInstaller build completed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during PyInstaller build: {e}")
        sys.exit(1)

    # Verify output
    exe_path = os.path.join('dist', 'DataLogic_Backend', 'DataLogic_Backend.exe')
    if os.path.exists(exe_path):
        print(f"SUCCESS: Backend executable created at {exe_path}")
    else:
        print("WARNING: Executable not found in expected location.")

if __name__ == "__main__":
    build()
