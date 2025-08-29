#!/usr/bin/env python3
"""
Panoramic Image Loading Functionality Tester
Tests the image loading capabilities with D:\test\images directory
"""

import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import json
from datetime import datetime

# Setup paths
project_root = Path(__file__).parent.absolute()
src_path = project_root / 'src'
sys.path.insert(0, str(src_path))

class ImageLoadingTester:
    """Test panoramic image loading functionality"""
    
    def __init__(self):
        self.test_directory = "D:\\test\\images"
        self.test_results = []
        
    def create_test_directory_structure(self):
        """Create test directory structure with sample images"""
        print("Creating test directory structure...")
        
        test_dir = Path(self.test_directory)
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sample panoramic images
        try:
            for i in range(1, 4):  # Create 3 test images
                panoramic_id = f"test_panoramic_{i:03d}"
                
                # Create panoramic image
                img = Image.new('RGB', (3088, 2064), color='lightblue')
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(img)
                
                # Draw title
                draw.text((50, 50), f"Test Panoramic Image {i}", fill='black', anchor="lt")
                draw.text((50, 100), f"ID: {panoramic_id}", fill='black', anchor="lt")
                draw.text((50, 150), f"Size: 3088x2064", fill='black', anchor="lt")
                
                # Draw 12x10 hole grid
                for row in range(10):
                    for col in range(12):
                        hole_num = row * 12 + col + 1
                        x = 750 + col * 145
                        y = 392 + row * 145
                        
                        # Draw hole circle
                        draw.ellipse([x-45, y-45, x+45, y+45], outline='black', width=2)
                        
                        # Add hole number
                        draw.text((x, y), str(hole_num), fill='black', anchor="mm")
                        
                        # Add some variety for testing
                        if hole_num % 10 == 0:  # Every 10th hole
                            draw.ellipse([x-45, y-45, x+45, y+45], fill='lightgreen', outline='black', width=2)
                        elif hole_num % 7 == 0:  # Every 7th hole
                            draw.ellipse([x-45, y-45, x+45, y+45], fill='lightcoral', outline='black', width=2)
                
                # Save panoramic image
                panoramic_path = test_dir / f"{panoramic_id}.jpg"
                img.save(panoramic_path, 'JPEG', quality=85)
                
                # Create slice directory and sample slices
                slice_dir = test_dir / panoramic_id
                slice_dir.mkdir(exist_ok=True)
                
                # Create sample slice images (just a few for testing)
                for hole_num in [1, 25, 50, 75, 100, 120]:
                    slice_img = Image.new('RGB', (200, 200), color='white')
                    slice_draw = ImageDraw.Draw(slice_img)
                    
                    # Draw a simple hole representation
                    slice_draw.ellipse([20, 20, 180, 180], outline='black', width=3)
                    slice_draw.text((100, 100), str(hole_num), fill='black', anchor="mm")
                    
                    # Add growth simulation
                    if hole_num % 3 == 0:  # Positive growth
                        slice_draw.ellipse([60, 60, 140, 140], fill='lightgreen', outline='green', width=2)
                    
                    slice_path = slice_dir / f"hole_{hole_num:03d}.jpg"
                    slice_img.save(slice_path, 'JPEG', quality=85)
                
                print(f"✓ Created test image set: {panoramic_id}")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to create test images: {e}")
            return False
    
    def test_directory_detection(self):
        """Test if the test directory can be detected and accessed"""
        print("\nTesting directory detection...")
        
        try:
            test_dir = Path(self.test_directory)
            
            if not test_dir.exists():
                print(f"✗ Test directory does not exist: {self.test_directory}")
                return False
                
            # Check for panoramic images
            panoramic_files = list(test_dir.glob("*.jpg"))
            panoramic_files.extend(list(test_dir.glob("*.jpeg")))
            panoramic_files.extend(list(test_dir.glob("*.png")))
            
            print(f"✓ Found {len(panoramic_files)} panoramic image files")
            
            # Check for slice subdirectories
            slice_dirs = [d for d in test_dir.iterdir() if d.is_dir()]
            print(f"✓ Found {len(slice_dirs)} slice subdirectories")
            
            # List files for verification
            for i, pano_file in enumerate(panoramic_files[:3]):  # Show first 3
                print(f"  Panoramic {i+1}: {pano_file.name}")
                
                # Check corresponding slice directory
                slice_dir = test_dir / pano_file.stem
                if slice_dir.exists():
                    slice_files = list(slice_dir.glob("*.jpg"))
                    print(f"    Slices: {len(slice_files)} files")
                
            return len(panoramic_files) > 0
            
        except Exception as e:
            print(f"✗ Directory detection failed: {e}")
            return False
    
    def test_image_loading_performance(self):
        """Test image loading performance"""
        print("\nTesting image loading performance...")
        
        try:
            test_dir = Path(self.test_directory)
            panoramic_files = list(test_dir.glob("*.jpg"))
            
            if not panoramic_files:
                print("✗ No panoramic files found for performance testing")
                return False
            
            # Test loading each image
            total_time = 0
            successful_loads = 0
            
            for pano_file in panoramic_files:
                try:
                    start_time = datetime.now()
                    
                    with Image.open(pano_file) as img:
                        width, height = img.size
                        load_time = (datetime.now() - start_time).total_seconds()
                        total_time += load_time
                        successful_loads += 1
                        
                        print(f"  ✓ {pano_file.name}: {width}x{height} loaded in {load_time:.3f}s")
                        
                except Exception as e:
                    print(f"  ✗ {pano_file.name}: Failed to load - {e}")
            
            if successful_loads > 0:
                avg_time = total_time / successful_loads
                print(f"✓ Average loading time: {avg_time:.3f}s per image")
                print(f"✓ Successfully loaded {successful_loads}/{len(panoramic_files)} images")
                return True
            else:
                print("✗ No images could be loaded")
                return False
                
        except Exception as e:
            print(f"✗ Performance testing failed: {e}")
            return False
    
    def test_gui_image_integration(self):
        """Test image loading integration with GUI components"""
        print("\nTesting GUI image integration...")
        
        try:
            # Create test window
            root = tk.Tk()
            root.title("Image Loading Test")
            root.geometry("800x600")
            
            # Test loading an image into Tkinter
            test_dir = Path(self.test_directory)
            panoramic_files = list(test_dir.glob("*.jpg"))
            
            if not panoramic_files:
                print("✗ No images available for GUI integration test")
                root.destroy()
                return False
            
            # Load first image
            test_image = panoramic_files[0]
            
            with Image.open(test_image) as img:
                # Resize for display
                display_img = img.resize((600, 400), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(display_img)
                
                # Create canvas and display image
                canvas = tk.Canvas(root, width=600, height=400, bg='white')
                canvas.pack(pady=20)
                
                canvas.create_image(300, 200, image=photo)
                
                # Add status label
                status_label = tk.Label(root, text=f"Displaying: {test_image.name}")
                status_label.pack()
                
                # Add close button
                close_btn = tk.Button(root, text="Close Test", command=root.quit)
                close_btn.pack(pady=10)
                
                print(f"✓ Successfully loaded {test_image.name} into GUI")
                print("  Test window is displayed. Close it to continue.")
                
                # Show window briefly
                root.update()
                root.after(3000, root.quit)  # Auto-close after 3 seconds
                root.mainloop()
                root.destroy()
                
                return True
                
        except Exception as e:
            print(f"✗ GUI integration test failed: {e}")
            try:
                root.destroy()
            except:
                pass
            return False
    
    def test_annotation_gui_loading(self):
        """Test loading images in the actual annotation GUI"""
        print("\nTesting annotation GUI image loading...")
        
        try:
            from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
            
            # Create GUI instance
            root = tk.Tk()
            root.withdraw()  # Hide initially
            
            app = PanoramicAnnotationGUI(root)
            
            # Set the test directory
            app.panoramic_dir_var.set(self.test_directory)
            
            # Test the load_data method
            try:
                app.load_data()
                
                # Check if data was loaded
                if hasattr(app, 'slice_files') and app.slice_files:
                    print(f"✓ Successfully loaded {len(app.slice_files)} image sets")
                    
                    # Test navigation
                    if app.panoramic_ids:
                        print(f"✓ Found panoramic IDs: {app.panoramic_ids}")
                        
                        # Try to load first panoramic image
                        first_id = app.panoramic_ids[0]
                        app.panoramic_id_var.set(first_id)
                        app.on_panoramic_selection()
                        
                        if app.panoramic_image:
                            width, height = app.panoramic_image.size
                            print(f"✓ Loaded panoramic image: {width}x{height}")
                        
                        print("✓ Annotation GUI image loading test passed")
                        root.destroy()
                        return True
                    else:
                        print("✗ No panoramic IDs found")
                        root.destroy()
                        return False
                else:
                    print("✗ No slice files loaded")
                    root.destroy()
                    return False
                    
            except Exception as e:
                print(f"✗ Failed to load data in GUI: {e}")
                root.destroy()
                return False
                
        except Exception as e:
            print(f"✗ Annotation GUI loading test failed: {e}")
            return False
    
    def run_all_tests(self):
        """Run all image loading tests"""
        print("Panoramic Image Loading Functionality Tester")
        print("=" * 50)
        
        tests = [
            ("Directory Structure Creation", self.create_test_directory_structure),
            ("Directory Detection", self.test_directory_detection),
            ("Image Loading Performance", self.test_image_loading_performance),
            ("GUI Image Integration", self.test_gui_image_integration),
            ("Annotation GUI Loading", self.test_annotation_gui_loading)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n{test_name}")
            print("-" * 30)
            
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
        print("\n" + "=" * 50)
        print("Image Loading Test Summary:")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "PASS" if result else "FAIL"
            print(f"  {test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print("✓ All image loading tests passed!")
            print("✓ D:\\test\\images directory is ready for use")
        else:
            print("✗ Some image loading tests failed")
        
        return passed == total

def main():
    """Main testing function"""
    tester = ImageLoadingTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n" + "=" * 50)
        print("IMAGE LOADING VALIDATION COMPLETE")
        print("✓ The GUI is ready to use with D:\\test\\images")
        print("\nTo use the GUI:")
        print("1. Run: python start_gui.py")
        print("2. Set panoramic directory to: D:\\test\\images")
        print("3. Click 'Load Data'")
        print("4. Test navigation and annotation features")
    
    return success

if __name__ == "__main__":
    main()