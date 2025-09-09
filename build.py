#!/usr/bin/env python3
"""
Packaging script for Panoramic Annotation Tool
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Main packaging function"""
    print("=== Panoramic Annotation Tool Packaging Script ===")
    
    # Get the project root directory
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
        # Add all required tkinter imports
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk", 
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.font",
        "--hidden-import=tkinter.colorchooser",
        "--hidden-import=PIL._tkinter_finder",
        "--hidden-import=cv2",
        "--hidden-import=numpy",
        "--hidden-import=yaml",
        "--collect-all=PIL",
        "--collect-all=tkinter",
        "--collect-all=cv2",
        "--collect-all=numpy",
        "--collect-all=yaml",
        # Exclude problematic modules
        "--exclude-module=matplotlib",
        "--exclude-module=scipy",
        "--exclude-module=pandas",
        "--exclude-module=pytest",
        "--exclude-module=test_*.py",
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
    
    # CLI version build removed as requested - only GUI version is needed
    print("\nSkipping CLI executable build (removed as per requirements)")
    
    # Create release directory
    print("\nCreating release package...")
    release_dir = project_root / "release"
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir()

    # Copy only the GUI executable (not CLI)
    dist_dir = project_root / "dist"
    gui_exe = dist_dir / "PanoramicAnnotationTool.exe"
    if gui_exe.exists():
        shutil.copy2(gui_exe, release_dir)
        print(f"Copied GUI executable: {gui_exe.name}")
    else:
        print(f"Warning: GUI executable not found at {gui_exe}")
        return False
    
    # Create readme
    readme_content = """Panoramic Annotation Tool (GUI Version)
=====================================

Usage:
Double-click PanoramicAnnotationTool.exe to start the GUI application.

System Requirements:
- Windows 10/11
- 4GB+ RAM
- Supported formats: PNG, JPG, JPEG, BMP

Notes:
- First run may take some time to initialize
- Recommended to run from a path without Chinese characters
- If antivirus software reports false positive, add to whitelist

Features:
- Interactive GUI for panoramic image annotation
- Enhanced annotation with growth patterns and interference factors
- Batch import/export functionality
- Model suggestion import support
- Real-time statistics and progress tracking

Troubleshooting:
- If GUI fails to start, ensure all required libraries are included
- Check Windows Defender settings if executable is blocked
- Run from command line to see detailed error messages

Technical Support:
Contact support for any issues.
"""
    
    (release_dir / "README.txt").write_text(readme_content, encoding="utf-8")
    
    print(f"\nRelease package created: {release_dir}")
    print("\nGUI Packaging completed successfully!")
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