#!/usr/bin/env python3
"""
Simple GUI Functionality Tester
Tests the panoramic annotation GUI functionality step by step
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import traceback

# Add project paths
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

def test_imports():
    """Test critical imports"""
    print("Testing imports...")
    
    try:
        # Test PIL import
        from PIL import Image, ImageTk
        print("✓ PIL/Pillow import successful")
        
        # Test tkinter import
        import tkinter as tk
        from tkinter import ttk
        print("✓ Tkinter import successful")
        
        # Test project modules
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        print("✓ PanoramicAnnotationGUI import successful")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_gui_creation():
    """Test GUI window creation"""
    print("Testing GUI creation...")
    
    try:
        root = tk.Tk()
        root.title("Test Window")
        root.geometry("800x600")
        
        # Create a simple test interface
        label = tk.Label(root, text="GUI Test Successful!")
        label.pack(pady=20)
        
        button = tk.Button(root, text="Close", command=root.quit)
        button.pack(pady=10)
        
        print("✓ GUI window created successfully")
        print("  Window will appear - close it to continue testing")
        
        # Show window briefly
        root.update()
        root.after(3000, root.quit)  # Auto-close after 3 seconds
        root.mainloop()
        root.destroy()
        
        return True
        
    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        return False

def test_directory_access():
    """Test directory access"""
    print("Testing directory access...")
    
    test_dir = "D:\\test\\images"
    
    try:
        if os.path.exists(test_dir):
            print(f"✓ Test directory exists: {test_dir}")
            
            # List contents
            files = os.listdir(test_dir)
            image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.bmp'))]
            
            print(f"  Found {len(files)} total files")
            print(f"  Found {len(image_files)} image files")
            
            if image_files:
                print(f"  Sample image: {image_files[0]}")
                return True
            else:
                print("  No image files found")
                return False
        else:
            print(f"✗ Test directory not found: {test_dir}")
            return False
            
    except Exception as e:
        print(f"✗ Directory access failed: {e}")
        return False

def test_image_loading():
    """Test image loading capability"""
    print("Testing image loading...")
    
    test_dir = "D:\\test\\images"
    
    try:
        from PIL import Image
        
        # Find first image file
        for root, dirs, files in os.walk(test_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.tiff', '.bmp')):
                    image_path = os.path.join(root, file)
                    
                    # Try to load image
                    with Image.open(image_path) as img:
                        width, height = img.size
                        print(f"✓ Successfully loaded image: {file}")
                        print(f"  Dimensions: {width}x{height}")
                        return True
                        
        print("✗ No loadable images found")
        return False
        
    except Exception as e:
        print(f"✗ Image loading failed: {e}")
        return False

def test_full_gui():
    """Test full GUI application"""
    print("Testing full GUI application...")
    
    try:
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        root = tk.Tk()
        app = PanoramicAnnotationGUI(root)
        
        print("✓ PanoramicAnnotationGUI created successfully")
        print("  GUI window should be visible now")
        print("  Please test the following features:")
        print("  1. Set panoramic directory to: D:\\test\\images")
        print("  2. Click 'Load Data' to load images")
        print("  3. Test navigation between panoramic images")
        print("  4. Test hole positioning and navigation")
        print("  5. Test annotation features")
        print("  6. Close the window when testing is complete")
        
        # Start the GUI
        root.mainloop()
        
        return True
        
    except Exception as e:
        print(f"✗ Full GUI test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main testing function"""
    print("Panoramic Annotation GUI - Simple Functionality Tester")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("GUI Creation Test", test_gui_creation),
        ("Directory Access Test", test_directory_access),
        ("Image Loading Test", test_image_loading),
        ("Full GUI Test", test_full_gui)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}")
        print("-" * 40)
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
                
        except Exception as e:
            print(f"✗ {test_name} ERROR: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! GUI is ready for use.")
    else:
        print("✗ Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()