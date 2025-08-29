#!/usr/bin/env python3
"""
Panoramic Annotation Workflow Test Script

This script tests the complete workflow of the panoramic annotation GUI,
including loading data, navigating holes, making annotations, and saving results.

Usage:
    python test_panoramic_workflow.py
    python test_panoramic_workflow.py --test-dir D:\test\images
    python test_panoramic_workflow.py --quick
"""

import sys
import os
import argparse
import time
import json
from pathlib import Path
from datetime import datetime

# Add project paths
project_root = Path(__file__).parent.absolute().parent.parent
src_path = project_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def setup_test_environment(test_image_dir: str = "D:\\test\\images"):
    """Setup test environment and create test data if needed"""
    print("🔧 Setting up test environment...")
    
    try:
        # Create test directory
        test_dir = Path(test_image_dir)
        test_dir.mkdir(parents=True, exist_ok=True)
        
        # Check if we have test images
        image_files = list(test_dir.glob("*.jpg")) + list(test_dir.glob("*.png"))
        
        if len(image_files) < 3:
            print("   Creating sample test images...")
            create_sample_panoramic_images(test_dir)
        else:
            print(f"   Found {len(image_files)} existing test images")
            
        return True
        
    except Exception as e:
        print(f"❌ Failed to setup test environment: {e}")
        return False

def create_sample_panoramic_images(test_dir: Path):
    """Create sample panoramic images for testing"""
    try:
        from PIL import Image, ImageDraw
        
        # Create 3 sample panoramic images
        for i in range(1, 4):
            panoramic_id = f"EB1000000{i}"
            image_path = test_dir / f"{panoramic_id}.jpg"
            
            # Create a large image (3088x2064) to match real panoramic images
            img = Image.new('RGB', (3088, 2064), color='lightgray')
            draw = ImageDraw.Draw(img)
            
            # Draw grid for 12x10 holes
            first_hole_x = 750
            first_hole_y = 392
            spacing = 145
            hole_size = 90
            
            for row in range(10):
                for col in range(12):
                    x = first_hole_x + col * spacing - hole_size // 2
                    y = first_hole_y + row * spacing - hole_size // 2
                    draw.rectangle([x, y, x + hole_size, y + hole_size], 
                                 outline='black', width=2)
                    # Add hole number
                    hole_num = row * 12 + col + 1
                    draw.text((x + 35, y + 35), str(hole_num), fill='black')
            
            # Add some sample annotations for specific holes
            sample_annotations = {
                25: "positive",  # Center hole
                1: "negative",   # First hole
                120: "weak_growth"  # Last hole
            }
            
            for hole_num, growth_level in sample_annotations.items():
                if hole_num <= 120:
                    row = (hole_num - 1) // 12
                    col = (hole_num - 1) % 12
                    x = first_hole_x + col * spacing - hole_size // 2
                    y = first_hole_y + row * spacing - hole_size // 2
                    
                    # Draw different patterns based on growth level
                    if growth_level == "positive":
                        # Draw clustered growth pattern
                        for dx in range(20, 70, 15):
                            for dy in range(20, 70, 15):
                                draw.ellipse([x + dx, y + dy, x + dx + 8, y + dy + 8], 
                                           fill='darkgreen')
                    elif growth_level == "weak_growth":
                        # Draw light gray pattern
                        draw.rectangle([x + 20, y + 20, x + 70, y + 70], 
                                     fill='lightgray', outline='gray')
                    # negative holes remain empty
            
            img.save(image_path)
            print(f"   ✅ Created sample image: {image_path.name}")
            
    except Exception as e:
        print(f"❌ Failed to create sample images: {e}")

def test_data_loading(test_image_dir: str = "D:\\test\\images"):
    """Test loading panoramic data"""
    print("\n🔍 Testing Data Loading...")
    
    try:
        # Import required modules
        import tkinter as tk
        from ui.panoramic_annotation_gui import PanoramicAnnotationGUI
        
        # Create a hidden root window
        root = tk.Tk()
        root.withdraw()  # Hide the window
        
        # Create application instance
        app = PanoramicAnnotationGUI(root)
        
        # Set the test directory
        app.panoramic_directory = test_image_dir
        app.panoramic_dir_var.set(test_image_dir)
        
        # Test loading data
        print("   Loading data from test directory...")
        app.load_data()
        
        # Check if data was loaded
        if app.panoramic_ids:
            print(f"   ✅ Successfully loaded {len(app.panoramic_ids)} panoramic images")
            print(f"   📋 Panoramic IDs: {app.panoramic_ids}")
            success = True
        else:
            print("   ⚠️ No panoramic images found in directory")
            success = False
            
        # Clean up
        root.destroy()
        
        return success
        
    except Exception as e:
        print(f"   ❌ Data loading test failed: {e}")
        return False

def test_hole_navigation():
    """Test hole navigation functionality"""
    print("\n🧭 Testing Hole Navigation...")
    
    try:
        from ui.hole_manager import HoleManager
        
        # Create hole manager
        hole_manager = HoleManager()
        
        # Test basic navigation
        test_holes = [1, 25, 60, 120]  # First, center, middle, last
        
        for hole_num in test_holes:
            # Test number to position conversion
            row, col = hole_manager.number_to_position(hole_num)
            print(f"   Hole {hole_num}: Row {row}, Col {col}")
            
            # Test position to number conversion
            converted_num = hole_manager.position_to_number(row, col)
            assert converted_num == hole_num, f"Mismatch: {converted_num} != {hole_num}"
            
            # Test coordinates
            x, y, w, h = hole_manager.get_hole_coordinates(hole_num)
            print(f"   Coordinates: ({x}, {y}, {w}, {h})")
        
        print("   ✅ Hole navigation tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Hole navigation test failed: {e}")
        return False

def test_annotation_creation():
    """Test creating panoramic annotations"""
    print("\n📝 Testing Annotation Creation...")
    
    try:
        from models.panoramic_annotation import PanoramicAnnotation
        from models.enhanced_annotation import EnhancedPanoramicAnnotation, FeatureCombination, GrowthLevel, GrowthPattern, InterferenceType
        
        # Test basic panoramic annotation
        annotation = PanoramicAnnotation(
            image_path="test/EB10000026_hole_25.png",
            label="positive",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=25,
            hole_row=2,
            hole_col=0,
            microbe_type="bacteria",
            growth_level="positive"
        )
        
        print(f"   ✅ Basic annotation created: {annotation.hole_number}")
        
        # Test enhanced annotation
        feature_combo = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.CLUSTERED,
            interference_factors={InterferenceType.PORES},
            confidence=0.95
        )
        
        enhanced_annotation = EnhancedPanoramicAnnotation(
            image_path="test/EB10000026_hole_25.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="EB10000026",
            hole_number=25,
            hole_row=2,
            hole_col=0,
            microbe_type="bacteria",
            feature_combination=feature_combo
        )
        
        print(f"   ✅ Enhanced annotation created: {enhanced_annotation.label}")
        
        # Test serialization
        annotation_dict = annotation.to_dict()
        enhanced_dict = enhanced_annotation.feature_combination.to_dict()
        
        print(f"   ✅ Serialization tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Annotation creation test failed: {e}")
        return False

def test_data_persistence():
    """Test saving and loading annotations"""
    print("\n💾 Testing Data Persistence...")
    
    try:
        from models.panoramic_annotation import PanoramicAnnotation
        import tempfile
        import json
        
        # Create a temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test annotation
            annotation = PanoramicAnnotation(
                image_path="test/EB10000026_hole_25.png",
                label="positive",
                bbox=[10, 20, 70, 70],
                confidence=0.88,
                panoramic_image_id="EB10000026",
                hole_number=25,
                hole_row=2,
                hole_col=0,
                microbe_type="bacteria",
                growth_level="positive"
            )
            
            # Test serialization
            annotation_dict = annotation.to_dict()
            
            # Save to file
            json_file = temp_path / "test_annotation.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(annotation_dict, f, indent=2, ensure_ascii=False)
            
            # Load from file
            with open(json_file, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            loaded_annotation = PanoramicAnnotation.from_dict(loaded_data)
            
            # Verify data integrity
            assert loaded_annotation.image_path == annotation.image_path
            assert loaded_annotation.hole_number == annotation.hole_number
            assert loaded_annotation.growth_level == annotation.growth_level
            
            print("   ✅ Save/load test passed")
            return True
            
    except Exception as e:
        print(f"   ❌ Data persistence test failed: {e}")
        return False

def run_comprehensive_workflow_test(test_image_dir: str = "D:\\test\\images"):
    """Run comprehensive panoramic annotation workflow test"""
    print("🎯 Panoramic Annotation Workflow Test")
    print("=" * 50)
    
    # Setup environment
    if not setup_test_environment(test_image_dir):
        print("❌ Failed to setup test environment")
        return False
    
    # Run individual tests
    tests = [
        ("Data Loading", lambda: test_data_loading(test_image_dir)),
        ("Hole Navigation", test_hole_navigation),
        ("Annotation Creation", test_annotation_creation),
        ("Data Persistence", test_data_persistence)
    ]
    
    results = []
    start_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} Test...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"   ✅ {test_name} test PASSED")
            else:
                print(f"   ❌ {test_name} test FAILED")
        except Exception as e:
            print(f"   ❌ {test_name} test ERROR: {e}")
            results.append((test_name, False))
    
    total_time = time.time() - start_time
    
    # Print summary
    print(f"\n{'='*50}")
    print("📊 TEST RESULTS SUMMARY")
    print(f"{'='*50}")
    print(f"⏱️  Total Execution Time: {total_time:.2f} seconds")
    
    passed_tests = sum(1 for _, result in results if result)
    total_tests = len(results)
    
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")
    
    overall_success = all(result for _, result in results)
    
    if overall_success:
        print(f"\n🎉 All tests PASSED! Panoramic annotation workflow is functional.")
    else:
        print(f"\n⚠️  Some tests FAILED. Please check the issues above.")
    
    return overall_success

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Panoramic Annotation Workflow Test",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--test-dir',
        type=str,
        default="D:\\test\\images",
        help='Test image directory path (default: D:\\test\\images)'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Run quick tests only'
    )
    
    args = parser.parse_args()
    
    success = run_comprehensive_workflow_test(args.test_dir)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()