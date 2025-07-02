import subprocess
import shutil
from pathlib import Path

def main():
    """Build Cython extensions and integrate with Poetry"""
    
    # Clean previous builds
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)
    
    # Get package name from poetry
    result = subprocess.run(["poetry", "version"], capture_output=True, text=True)
    package_name = result.stdout.split()[0].replace("-", "_")
    
    print(f"Building Cython extensions for {package_name}...")
    
    # Backup original Python files
    backup_dir = f"{package_name}_backup"
    if Path(backup_dir).exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(package_name, backup_dir)
    
    try:
        # Compile with Cython
        subprocess.run([
            "python", "setup_cython.py", 
            "build_ext", "--inplace"
        ], check=True)
        
        # Remove original .py files (except __init__.py)
        for py_file in Path(package_name).rglob("*.py"):
            if py_file.name != "__init__.py":
                py_file.unlink()
        
        # Clean up Cython-generated .c files
        for c_file in Path(".").rglob("*.c"):
            if c_file.is_file():
                c_file.unlink()
        
        # Build with Poetry
        print("Building package with Poetry...")
        subprocess.run(["poetry", "build"], check=True)
        
        print("✅ Build complete! Check dist/ folder")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        
    finally:
        # Restore original files
        if Path(package_name).exists():
            shutil.rmtree(package_name)
        shutil.move(backup_dir, package_name)

if __name__ == "__main__":
    main()