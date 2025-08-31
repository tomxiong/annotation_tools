#!/usr/bin/env python3
"""
Simplified packaging script for Panoramic Annotation Tool
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Main packaging function"""
    print("=== Panoramic Annotation Tool Packaging Script ===")
    
    # Ensure we're in the correct directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print(f"Working directory: {project_root}")
    
    # Build GUI version
    print("\nBuilding GUI executable...")
    cmd = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=PanoramicAnnotationTool",
        "--windowed",
        "--onefile",
        "--clean",
        "--add-data=src;src",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=yaml",
        "--collect-all=PIL",
        "--collect-all=cv2",
        "--collect-all=numpy",
        "--collect-all=yaml",
        "run_gui.py"
    ]
    
    try:
        print("Running PyInstaller...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("GUI executable built successfully!")
        print(f"Location: {project_root / 'dist' / 'PanoramicAnnotationTool.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    # Build CLI version
    print("\nBuilding CLI executable...")
    cmd_cli = [
        sys.executable,
        "-m", "PyInstaller",
        "--name=annotation-cli",
        "--console",
        "--onefile", 
        "--clean",
        "--add-data=src;src",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=yaml",
        "--collect-all=cv2",
        "--collect-all=numpy",
        "--collect-all=yaml",
        "run_cli.py"
    ]
    
    try:
        print("Running PyInstaller for CLI...")
        result = subprocess.run(cmd_cli, check=True, capture_output=True, text=True)
        print("CLI executable built successfully!")
        print(f"Location: {project_root / 'dist' / 'annotation-cli.exe'}")
    except subprocess.CalledProcessError as e:
        print(f"CLI build failed: {e}")
        print(f"Error output: {e.stderr}")
        return False
    
    # Create release directory
    print("\nCreating release package...")
    release_dir = project_root / "release"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()
    
    # Copy executables
    dist_dir = project_root / "dist"
    for exe_file in dist_dir.glob("*.exe"):
        shutil.copy2(exe_file, release_dir)
    
    # Create readme
    readme_content = """Panoramic Annotation Tool
========================

Usage:
1. GUI Version: Double-click PanoramicAnnotationTool.exe
2. CLI Version: Run annotation-cli.exe in command line

System Requirements:
- Windows 10/11
- 4GB+ RAM
- Supported formats: PNG, JPG, JPEG, BMP

Notes:
- First run may take some time to initialize
- Recommended to run from a path without Chinese characters
- If antivirus software reports false positive, add to whitelist

Technical Support:
Contact support for any issues.
"""
    
    (release_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    
    print(f"\nRelease package created: {release_dir}")
    print("\nPackaging completed successfully!")
    print("Files created:")
    for file in release_dir.iterdir():
        print(f"  - {file.name}")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\nDone!")
    else:
        print("\nPackaging failed!")
        sys.exit(1)