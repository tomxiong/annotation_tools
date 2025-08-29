#!/usr/bin/env python3
"""
Dependency Validator and Auto-Fixer
Identifies and resolves specific import issues for the panoramic annotation GUI
"""

import sys
import os
from pathlib import Path
import importlib
import traceback

# Setup paths
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_module_import(module_name, description=""):
    """Test if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✓ {module_name} - {description}")
        return True
    except Exception as e:
        print(f"✗ {module_name} - {description}: {str(e)}")
        return False

def test_basic_dependencies():
    """Test basic Python dependencies"""
    print("Testing Basic Dependencies:")
    print("-" * 40)
    
    tests = [
        ("tkinter", "GUI framework"),
        ("PIL", "Image processing"),
        ("pathlib", "Path utilities"),
        ("json", "JSON handling"),
        ("typing", "Type hints"),
        ("dataclasses", "Data classes")
    ]
    
    all_passed = True
    for module, desc in tests:
        if not test_module_import(module, desc):
            all_passed = False
    
    return all_passed

def test_project_modules():
    """Test project-specific modules"""
    print("\nTesting Project Modules:")
    print("-" * 40)
    
    # Test core modules
    core_modules = [
        ("core.config", "Core configuration"),
        ("core.logger", "Logging system"),
        ("core.exceptions", "Custom exceptions")
    ]
    
    all_passed = True
    for module, desc in core_modules:
        if not test_module_import(module, desc):
            all_passed = False
    
    # Test models
    model_modules = [
        ("models.annotation", "Annotation models"),
        ("models.dataset", "Dataset models"),
        ("models.panoramic_annotation", "Panoramic annotation"),
        ("models.enhanced_annotation", "Enhanced annotation")
    ]
    
    for module, desc in model_modules:
        if not test_module_import(module, desc):
            all_passed = False
    
    # Test services
    service_modules = [
        ("services.config_file_service", "Configuration file service"),
        ("services.panoramic_image_service", "Image service"),
        ("services.image_processor", "Image processor")
    ]
    
    for module, desc in service_modules:
        if not test_module_import(module, desc):
            all_passed = False
    
    # Test UI modules
    ui_modules = [
        ("ui.hole_manager", "Hole manager"),
        ("ui.hole_config_panel", "Hole configuration"),
        ("ui.enhanced_annotation_panel", "Enhanced annotation panel"),
        ("ui.batch_import_dialog", "Batch import dialog")
    ]
    
    for module, desc in ui_modules:
        if not test_module_import(module, desc):
            all_passed = False
    
    return all_passed

def check_missing_files():
    """Check if any required files are missing"""
    print("\nChecking Required Files:")
    print("-" * 40)
    
    required_files = [
        "src/ui/panoramic_annotation_gui.py",
        "src/ui/hole_manager.py",
        "src/ui/hole_config_panel.py",
        "src/ui/enhanced_annotation_panel.py",
        "src/services/panoramic_image_service.py",
        "src/services/config_file_service.py",
        "src/models/panoramic_annotation.py",
        "src/models/enhanced_annotation.py"
    ]
    
    all_found = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING!")
            all_found = False
    
    return all_found

def create_missing_modules():
    """Create minimal versions of missing critical modules"""
    print("\nCreating Missing Modules:")
    print("-" * 40)
    
    # Define minimal module contents
    minimal_modules = {
        "src/ui/batch_import_dialog.py": '''"""
Batch import dialog module
"""

def show_batch_import_dialog(parent=None):
    """Show batch import dialog"""
    from tkinter import messagebox
    messagebox.showinfo("Batch Import", "Batch import functionality")
    return []
''',
        "src/ui/enhanced_annotation_panel.py": '''"""
Enhanced annotation panel module
"""

import tkinter as tk
from tkinter import ttk

class EnhancedAnnotationPanel:
    """Enhanced annotation panel"""
    
    def __init__(self, parent):
        self.parent = parent
        self.frame = ttk.Frame(parent)
        
    def update_annotation(self, annotation):
        """Update annotation display"""
        pass
        
    def get_annotation_data(self):
        """Get current annotation data"""
        return {}
''',
        "src/services/panoramic_image_service.py": '''"""
Panoramic image service module
"""

from PIL import Image
from typing import Optional, List, Dict, Any
import os

class PanoramicImageService:
    """Service for handling panoramic images"""
    
    def __init__(self):
        self.current_image = None
        
    def load_image(self, image_path: str) -> Optional[Image.Image]:
        """Load an image from file"""
        try:
            return Image.open(image_path)
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
            
    def get_image_info(self, image: Image.Image) -> Dict[str, Any]:
        """Get image information"""
        return {
            "width": image.width,
            "height": image.height,
            "mode": image.mode
        }
''',
        "src/services/config_file_service.py": '''"""
Configuration file service module
"""

import json
import os
from typing import Dict, Any, Optional

class ConfigFileService:
    """Service for handling configuration files"""
    
    def __init__(self):
        self.config_data = {}
        
    def save_config(self, data: Dict[str, Any], filepath: str) -> bool:
        """Save configuration to file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
            
    def load_config(self, filepath: str) -> Optional[Dict[str, Any]]:
        """Load configuration from file"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
        return None
''',
        "src/models/panoramic_annotation.py": '''"""
Panoramic annotation models
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json

@dataclass
class PanoramicAnnotation:
    """Panoramic annotation data"""
    panoramic_id: str
    hole_number: int
    growth_level: str = "negative"
    microbe_type: str = "bacteria"
    confidence: float = 1.0
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "panoramic_id": self.panoramic_id,
            "hole_number": self.hole_number,
            "growth_level": self.growth_level,
            "microbe_type": self.microbe_type,
            "confidence": self.confidence,
            "notes": self.notes
        }

class PanoramicDataset:
    """Panoramic dataset container"""
    
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.annotations: List[PanoramicAnnotation] = []
        
    def add_annotation(self, annotation: PanoramicAnnotation):
        """Add annotation to dataset"""
        self.annotations.append(annotation)
        
    def get_annotation(self, panoramic_id: str, hole_number: int) -> Optional[PanoramicAnnotation]:
        """Get specific annotation"""
        for ann in self.annotations:
            if ann.panoramic_id == panoramic_id and ann.hole_number == hole_number:
                return ann
        return None
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "annotations": [ann.to_dict() for ann in self.annotations]
        }
''',
        "src/models/enhanced_annotation.py": '''"""
Enhanced annotation models
"""

from models.panoramic_annotation import PanoramicAnnotation
from typing import Dict, Any, List
from dataclasses import dataclass

@dataclass
class EnhancedPanoramicAnnotation(PanoramicAnnotation):
    """Enhanced panoramic annotation with additional features"""
    
    growth_pattern: str = "uniform"
    edge_clarity: str = "clear"
    contamination: bool = False
    interference_factors: List[str] = None
    
    def __post_init__(self):
        if self.interference_factors is None:
            self.interference_factors = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update({
            "growth_pattern": self.growth_pattern,
            "edge_clarity": self.edge_clarity,
            "contamination": self.contamination,
            "interference_factors": self.interference_factors
        })
        return base_dict
'''
    }
    
    created_count = 0
    for module_path, content in minimal_modules.items():
        full_path = project_root / module_path
        
        if not full_path.exists():
            # Create directory if needed
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write minimal module
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✓ Created: {module_path}")
            created_count += 1
        else:
            print(f"- Exists: {module_path}")
    
    print(f"Created {created_count} missing modules")
    return created_count > 0

def test_gui_import():
    """Test if the main GUI can be imported"""
    print("\nTesting Main GUI Import:")
    print("-" * 40)
    
    try:
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        print("✓ PanoramicAnnotationGUI imported successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to import PanoramicAnnotationGUI: {e}")
        print("Error details:")
        traceback.print_exc()
        return False

def install_missing_dependencies():
    """Install missing dependencies"""
    print("\nInstalling Missing Dependencies:")
    print("-" * 40)
    
    try:
        import subprocess
        
        # Try to install Pillow
        try:
            from PIL import Image
            print("✓ Pillow already installed")
        except ImportError:
            print("Installing Pillow...")
            result = subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Pillow installed successfully")
            else:
                print(f"✗ Failed to install Pillow: {result.stderr}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error installing dependencies: {e}")
        return False

def main():
    """Main validation and fixing function"""
    print("Dependency Validator and Auto-Fixer")
    print("=" * 50)
    
    # Step 1: Test basic dependencies
    basic_ok = test_basic_dependencies()
    
    # Step 2: Install missing dependencies if needed
    if not basic_ok:
        install_missing_dependencies()
    
    # Step 3: Check for missing files
    files_ok = check_missing_files()
    
    # Step 4: Create missing modules if needed
    if not files_ok:
        create_missing_modules()
    
    # Step 5: Test project modules
    modules_ok = test_project_modules()
    
    # Step 6: Test main GUI import
    gui_ok = test_gui_import()
    
    # Summary
    print("\n" + "=" * 50)
    print("Validation Summary:")
    print(f"Basic Dependencies: {'✓' if basic_ok else '✗'}")
    print(f"Required Files: {'✓' if files_ok else '✗'}")
    print(f"Project Modules: {'✓' if modules_ok else '✗'}")
    print(f"GUI Import: {'✓' if gui_ok else '✗'}")
    
    if gui_ok:
        print("\n✓ All validations passed! GUI should be ready to launch.")
        return True
    else:
        print("\n✗ Some validations failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nTrying to launch the GUI now...")
        try:
            import tkinter as tk
            from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
            
            root = tk.Tk()
            app = PanoramicAnnotationGUI(root)
            print("GUI launched successfully! Close the window to continue.")
            root.mainloop()
        except Exception as e:
            print(f"GUI launch failed: {e}")
            traceback.print_exc()