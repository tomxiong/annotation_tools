#!/usr/bin/env python3
"""
Comprehensive GUI Test and Launch Script
Automatically sets up environment, tests functionality, and launches the GUI
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def setup_environment():
    """Set up the Python environment and paths"""
    project_root = Path(__file__).parent.absolute()
    src_path = project_root / 'src'
    
    # Add paths to sys.path
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    
    print(f"Project root: {project_root}")
    print(f"Source path: {src_path}")
    
    return project_root, src_path

def install_dependencies():
    """Install required dependencies"""
    print("Installing dependencies...")
    
    try:
        # Install Pillow
        subprocess.run([sys.executable, "-m", "pip", "install", "Pillow"], 
                      check=True, capture_output=True)
        print("✓ Pillow installed")
        
        # Install other common dependencies
        subprocess.run([sys.executable, "-m", "pip", "install", "pathlib"], 
                      capture_output=True)  # Usually built-in, but just in case
        
        return True
    except Exception as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

def test_imports():
    """Test critical imports"""
    print("Testing imports...")
    
    import_tests = [
        ("tkinter", "import tkinter as tk"),
        ("PIL", "from PIL import Image, ImageTk"),
        ("pathlib", "from pathlib import Path"),
        ("json", "import json"),
        ("typing", "from typing import Optional, Dict, List"),
    ]
    
    for name, import_stmt in import_tests:
        try:
            exec(import_stmt)
            print(f"✓ {name}")
        except Exception as e:
            print(f"✗ {name}: {e}")
            return False
    
    return True

def create_test_directory():
    """Create test directory with sample images if needed"""
    test_dir = Path("D:/test/images")
    
    if not test_dir.exists():
        print(f"Creating test directory: {test_dir}")
        try:
            test_dir.mkdir(parents=True, exist_ok=True)
            
            # Create a simple test image
            try:
                from PIL import Image
                
                # Create a simple test panoramic image
                img = Image.new('RGB', (3088, 2064), color='lightgray')
                
                # Add some grid lines to simulate holes
                from PIL import ImageDraw
                draw = ImageDraw.Draw(img)
                
                # Draw grid for 12x10 holes
                for row in range(10):
                    for col in range(12):
                        x = 750 + col * 145 - 45
                        y = 392 + row * 145 - 45
                        draw.rectangle([x, y, x+90, y+90], outline='black', width=2)
                        # Add hole number
                        hole_num = row * 12 + col + 1
                        draw.text((x+35, y+35), str(hole_num), fill='black')
                
                test_image_path = test_dir / "test_panoramic_001.jpg"
                img.save(test_image_path)
                print(f"✓ Created test image: {test_image_path}")
                
                return True
                
            except Exception as e:
                print(f"✗ Failed to create test image: {e}")
                return False
                
        except Exception as e:
            print(f"✗ Failed to create test directory: {e}")
            return False
    else:
        print(f"✓ Test directory exists: {test_dir}")
        return True

def test_gui_components():
    """Test GUI components step by step"""
    print("Testing GUI components...")
    
    try:
        # Test basic Tkinter
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()  # Hide the window
        root.destroy()
        print("✓ Tkinter test passed")
        
        # Test PIL with Tkinter
        from PIL import Image, ImageTk
        img = Image.new('RGB', (100, 100), 'red')
        photo = ImageTk.PhotoImage(img)
        print("✓ PIL + Tkinter integration test passed")
        
        return True
        
    except Exception as e:
        print(f"✗ GUI component test failed: {e}")
        return False

def launch_gui():
    """Launch the panoramic annotation GUI"""
    print("Launching GUI...")
    
    try:
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # Create main window
        root = tk.Tk()
        root.title("全景图像标注工具 - 微生物药敏检测")
        
        # Set window size and position
        root.geometry("2400x1300+100+50")
        
        # Create application
        app = PanoramicAnnotationGUI(root)
        
        print("✓ GUI created successfully!")
        print("\nGUI Features to Test:")
        print("1. Set panoramic directory to: D:\\test\\images")
        print("2. Click 'Load Data' to load test images")
        print("3. Test hole navigation (arrows keys or hole number input)")
        print("4. Test annotation features (growth level, microbe type)")
        print("5. Test save/load annotation functionality")
        print("6. Test panoramic image navigation")
        print("\nGUI is now running. Close the window when finished testing.")
        
        # Start the GUI main loop
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI launch failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_comprehensive_test():
    """Run comprehensive test and launch sequence"""
    print("Panoramic Annotation GUI - Comprehensive Test & Launch")
    print("=" * 60)
    
    # Step 1: Setup environment
    print("\n1. Setting up environment...")
    project_root, src_path = setup_environment()
    
    # Step 2: Install dependencies
    print("\n2. Installing dependencies...")
    if not install_dependencies():
        print("Continuing without dependency installation...")
    
    # Step 3: Test imports
    print("\n3. Testing imports...")
    if not test_imports():
        print("✗ Import tests failed. Cannot continue.")
        return False
    
    # Step 4: Create test directory
    print("\n4. Setting up test directory...")
    create_test_directory()
    
    # Step 5: Test GUI components
    print("\n5. Testing GUI components...")
    if not test_gui_components():
        print("✗ GUI component tests failed. Cannot continue.")
        return False
    
    # Step 6: Launch GUI
    print("\n6. Launching GUI...")
    success = launch_gui()
    
    print("\n" + "=" * 60)
    if success:
        print("✓ Testing and launch completed successfully!")
        print("The GUI should have been displayed and functional.")
    else:
        print("✗ Testing or launch failed. Check the errors above.")
    
    return success

def main():
    """Main function"""
    try:
        return run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user.")
        return False
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\nTesting completed. You can now use the panoramic annotation tool!")
    else:
        print("\nTesting failed. Please check the errors and try again.")
    
    input("\nPress Enter to exit...")