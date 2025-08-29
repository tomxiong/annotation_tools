#!/usr/bin/env python3
import os
from pathlib import Path

print("Current working directory:", os.getcwd())
print("Python executable:", __file__)

# Check if key files exist
key_files = [
    "src/ui/panoramic_annotation_gui.py",
    "src/ui/panoramic_annotation_gui_refactored.py",
    "src/ui/panoramic_annotation_gui_mixin.py"
]

for file_path in key_files:
    if Path(file_path).exists():
        print(f"✅ Found: {file_path}")
    else:
        print(f"❌ Not found: {file_path}")

print("\nTest completed successfully")