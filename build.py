import os
import shutil
import subprocess
import sys

def clean_build_dirs():
    """Remove build and dist directories if they exist."""
    dirs = ['build', 'dist']
    for d in dirs:
        if os.path.exists(d):
            print(f"Cleaning {d}...")
            shutil.rmtree(d)

def run_pyinstaller():
    """Run PyInstaller with the spec file."""
    print("Running PyInstaller...")
    # Use sys.executable to ensure we use the same python environment
    cmd = [sys.executable, '-m', 'PyInstaller', 'main.spec']
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error during build:")
        print(result.stderr)
        sys.exit(1)
    else:
        print("Build successful.")

def verify_secrets_exclusion():
    """Verify that secrets.json is NOT in the output directory."""
    dist_path = os.path.join('dist', 'SistemaPrestamos')
    secrets_path = os.path.join(dist_path, 'secrets.json')
    
    if os.path.exists(secrets_path):
        print("CRITICAL ERROR: secrets.json found in output directory!")
        print("Removing it immediately...")
        os.remove(secrets_path)
        print("secrets.json removed. Please check your spec file.")
    else:
        print("Verification Successful: secrets.json is NOT present in the build.")

def create_portable_zip():
    """Create a zip file of the dist directory for portable use."""
    dist_dir = os.path.join('dist', 'SistemaPrestamos')
    zip_name = 'SistemaPrestamos_Portable'
    
    if os.path.exists(dist_dir):
        print(f"Creating portable zip: {zip_name}.zip...")
        shutil.make_archive(zip_name, 'zip', 'dist', 'SistemaPrestamos')
        print(f"Portable zip created: {zip_name}.zip")
    else:
        print("Error: Dist directory not found, cannot zip.")

def main():
    print("Starting Secure Build Process...")
    clean_build_dirs()
    run_pyinstaller()
    verify_secrets_exclusion()
    create_portable_zip()
    print("\nBuild process completed.")
    print(f"Executable folder: dist/SistemaPrestamos")
    print(f"Portable ZIP: SistemaPrestamos_Portable.zip")

if __name__ == "__main__":
    main()
