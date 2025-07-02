#!/usr/bin/env python3
"""Custom build script for Cython wheels without .py files"""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

def build_cython_wheel():
    """Build wheel with Cython extensions only, excluding .py files"""
    
    # Clean previous builds
    if Path("dist").exists():
        shutil.rmtree("dist")
    if Path("build").exists():
        shutil.rmtree("build")
    
    # Run Cython build first
    print("Building Cython extensions...")
    subprocess.run(["python", "setup.py", "build_ext", "--inplace"], check=True)
    
    # Create temporary directory for wheel build
    with tempfile.TemporaryDirectory(prefix="cython_wheel_") as temp_dir:
        temp_pkg = Path(temp_dir) / "simt_emlite"
        temp_pkg.mkdir()
        
        # Copy only .so/.pyd files and __init__.py files
        source_pkg = Path("simt_emlite")
        
        for item in source_pkg.rglob("*"):
            if item.is_file():
                rel_path = item.relative_to(source_pkg)
                
                # Include compiled extensions and __init__.py files only
                if (item.suffix in ['.so', '.pyd', '.dll'] or 
                    item.name == '__init__.py'):
                    dest = temp_pkg / rel_path
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(item, dest)
        
        # Create minimal setup.py for wheel building
        setup_content = '''
from setuptools import setup, find_packages

setup(
    name="simt-emlite",
    version="0.21.4",
    packages=find_packages(),
    zip_safe=False,
    package_data={
        "": ["*.so", "*.pyd", "*.dll"],
    },
)
'''
        
        setup_file = Path(temp_dir) / "setup.py"
        setup_file.write_text(setup_content)
        
        # Copy pyproject.toml metadata
        if Path("pyproject.toml").exists():
            shutil.copy2("pyproject.toml", temp_dir)
        
        # Build wheel from temp directory
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            subprocess.run(["python", "-m", "build", "--wheel"], check=True)
            
            # Copy wheel back to original dist directory
            dist_dir = Path(old_cwd) / "dist"
            dist_dir.mkdir(exist_ok=True)
            
            for wheel in Path("dist").glob("*.whl"):
                shutil.copy2(wheel, dist_dir)
                print(f"Built wheel: {dist_dir / wheel.name}")
                
        finally:
            os.chdir(old_cwd)

if __name__ == "__main__":
    build_cython_wheel()