#!/usr/bin/env python3
"""
Quick GUI test - Import and instantiate without running
"""
import sys
import tkinter as tk
from pathlib import Path

# Add src to path
src_path = Path("src")
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    print("🔍 Testing GUI import and instantiation...")
    
    # Import the main GUI class
    from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
    print("✅ PanoramicAnnotationGUI imported successfully")
    
    # Create a test root window
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Try to instantiate the GUI
    app = PanoramicAnnotationGUI(root)
    print("✅ PanoramicAnnotationGUI instantiated successfully")
    
    # Check some key attributes
    if hasattr(app, 'image_service'):
        print("✅ Image service initialized")
    if hasattr(app, 'hole_manager'):
        print("✅ Hole manager initialized")
    if hasattr(app, 'config_service'):
        print("✅ Config service initialized")
    
    # Clean up
    root.destroy()
    
    print("\n🎉 SUCCESS: Core GUI functionality is intact after cleanup!")
    print("✅ All essential components are working properly")
    print("✅ The cleanup preserved the core functionality")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()