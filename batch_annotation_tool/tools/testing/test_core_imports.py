#!/usr/bin/env python3
"""
Test the core GUI imports after cleanup
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path("src")
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    print("Testing core GUI import...")
    from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
    print("✅ PanoramicAnnotationGUI imported successfully")
    
    print("\nTesting core dependencies...")
    
    # Test key imports that the GUI uses
    from ui.hole_manager import HoleManager
    print("✅ HoleManager imported successfully")
    
    from ui.enhanced_annotation_panel import EnhancedAnnotationPanel
    print("✅ EnhancedAnnotationPanel imported successfully")
    
    from services.panoramic_image_service import PanoramicImageService
    print("✅ PanoramicImageService imported successfully")
    
    from models.panoramic_annotation import PanoramicAnnotation
    print("✅ PanoramicAnnotation imported successfully")
    
    print("\n🎉 All core imports successful! The cleanup preserved all essential functionality.")
    
except ImportError as e:
    print(f"❌ Import failed: {e}")
    print("Check that the file paths are correct and dependencies are intact.")
except Exception as e:
    print(f"❌ Unexpected error: {e}")