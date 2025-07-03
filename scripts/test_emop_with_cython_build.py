#!/usr/bin/env python3
"""
Test script for running emop command with Cython build
"""
import sys
import os
import subprocess

def main():
    # Add the Cython build directory to PYTHONPATH
    build_dir = "build/lib.linux-x86_64-cpython-312"
    current_env = os.environ.copy()
    current_env["PYTHONPATH"] = f"{build_dir}:{current_env.get('PYTHONPATH', '')}"
    
    # Run emop command with Cython build
    cmd = [sys.executable, "-c", "from simt_emlite.cli.emop import main; main()"] + sys.argv[1:]
    
    print(f"Running emop with Cython build from: {build_dir}")
    print(f"Command: {' '.join(cmd)}")
    
    result = subprocess.run(cmd, env=current_env)
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()