#!/usr/bin/env python3
"""
JSON Enhanced Data Persistence Test
Tests that enhanced_data is properly saved to and loaded from JSON files
"""

import sys
import os
from pathlib import Path
import json
import tempfile

# Add src directory to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

def test_json_enhanced_data_persistence():
    """Test that enhanced_data survives JSON save/load cycles"""
    print("🔍 JSON Enhanced Data Persistence Test")
    print("=" * 60)
    
    try:
        # Import required modules
        from models.panoramic_annotation import PanoramicAnnotation, PanoramicDataset
        from models.enhanced_annotation import FeatureCombination, GrowthLevel, GrowthPattern, EnhancedPanoramicAnnotation
        
        print("✅ Module imports successful")
        
        # Test 1: Create positive_clustered feature combination
        print("\n📝 Test 1: Create positive_clustered feature combination")
        feature_combination = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.CLUSTERED,
            interference_factors=set(),
            confidence=1.0
        )
        print(f"✓ Feature combination: {feature_combination.growth_level}, {feature_combination.growth_pattern}")
        
        # Test 2: Create enhanced annotation
        print("\n📝 Test 2: Create enhanced annotation")
        enhanced_annotation = EnhancedPanoramicAnnotation(
            image_path="test_hole_25.png",
            bbox=[0, 0, 70, 70],
            panoramic_image_id="TEST001",
            hole_number=25,
            hole_row=2,
            hole_col=1,
            microbe_type="bacteria",
            feature_combination=feature_combination,
            annotation_source="enhanced_manual",
            is_confirmed=True
        )
        print(f"✓ Enhanced annotation created")
        
        # Test 3: Create panoramic annotation with enhanced_data
        print("\n📝 Test 3: Create panoramic annotation with enhanced_data")
        annotation = PanoramicAnnotation.from_filename(
            "test_hole_25.png",
            label=enhanced_annotation.get_training_label(),
            bbox=[0, 0, 70, 70],
            confidence=feature_combination.confidence,
            microbe_type="bacteria",
            growth_level=feature_combination.growth_level.value,
            interference_factors=[],
            annotation_source="enhanced_manual",
            is_confirmed=True,
            panoramic_id="TEST001"
        )
        
        # Set enhanced_data
        annotation.enhanced_data = enhanced_annotation.to_dict()
        print(f"✓ Set enhanced_data: {len(str(annotation.enhanced_data))} characters")
        print(f"✓ Enhanced_data contains: {list(annotation.enhanced_data.keys())}")
        
        # Test 4: Create dataset and save to JSON
        print("\n📝 Test 4: Save to JSON")
        dataset = PanoramicDataset("Test Dataset", "Testing enhanced_data persistence")
        dataset.add_annotation(annotation)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_filename = f.name
        
        try:
            dataset.save_to_json(temp_filename, confirmed_only=False)
            print(f"✓ Dataset saved to: {temp_filename}")
            
            # Verify JSON content
            with open(temp_filename, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            saved_annotation = json_data['annotations'][0]
            has_enhanced_data = 'enhanced_data' in saved_annotation
            print(f"✓ JSON contains enhanced_data: {has_enhanced_data}")
            
            if has_enhanced_data:
                enhanced_data = saved_annotation['enhanced_data']
                print(f"✓ Enhanced_data type: {type(enhanced_data)}")
                print(f"✓ Enhanced_data keys: {list(enhanced_data.keys())}")
                
                if 'feature_combination' in enhanced_data:
                    fc_data = enhanced_data['feature_combination']
                    print(f"✓ Feature combination: level={fc_data.get('growth_level')}, pattern={fc_data.get('growth_pattern')}")
            
            # Test 5: Load from JSON
            print("\n📝 Test 5: Load from JSON")
            loaded_dataset = PanoramicDataset.load_from_json(temp_filename)
            print(f"✓ Dataset loaded successfully")
            
            loaded_annotation = loaded_dataset.annotations[0]
            has_enhanced_data_loaded = hasattr(loaded_annotation, 'enhanced_data') and loaded_annotation.enhanced_data
            print(f"✓ Loaded annotation has enhanced_data: {has_enhanced_data_loaded}")
            
            if has_enhanced_data_loaded:
                loaded_enhanced_data = loaded_annotation.enhanced_data
                print(f"✓ Loaded enhanced_data type: {type(loaded_enhanced_data)}")
                print(f"✓ Loaded enhanced_data keys: {list(loaded_enhanced_data.keys())}")
                
                if 'feature_combination' in loaded_enhanced_data:
                    fc_data = loaded_enhanced_data['feature_combination']
                    loaded_level = fc_data.get('growth_level')
                    loaded_pattern = fc_data.get('growth_pattern')
                    print(f"✓ Loaded feature combination: level={loaded_level}, pattern={loaded_pattern}")
                    
                    # Test 6: Verify data integrity
                    print("\n📝 Test 6: Verify data integrity")
                    original_level = feature_combination.growth_level.value
                    original_pattern = feature_combination.growth_pattern.value
                    
                    level_match = loaded_level == original_level
                    pattern_match = loaded_pattern == original_pattern
                    
                    print(f"✓ Growth level match: {level_match} (original: {original_level}, loaded: {loaded_level})")
                    print(f"✓ Growth pattern match: {pattern_match} (original: {original_pattern}, loaded: {loaded_pattern})")
                    
                    if level_match and pattern_match:
                        print("\n🎉 SUCCESS: Enhanced data persistence works correctly!")
                        print("✓ positive_clustered annotations will be properly restored after JSON save/load")
                        return True
                    else:
                        print("\n❌ FAILURE: Data integrity check failed")
                        return False
            else:
                print("\n❌ FAILURE: Enhanced data not found in loaded annotation")
                return False
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_filename)
            except:
                pass
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔧 JSON Enhanced Data Persistence Test")
    print("Goal: Verify that enhanced_data survives JSON save/load cycles")
    print()
    
    success = test_json_enhanced_data_persistence()
    
    if success:
        print("\n✅ JSON persistence fix verified successfully")
        print("🎯 Now positive_clustered annotations should be properly restored after:")
        print("   1. Saving annotations to JSON")
        print("   2. Restarting the software")
        print("   3. Loading the JSON file")
        print("   4. The pattern should remain 'clustered' instead of 'heavy_growth'")
    else:
        print("\n❌ JSON persistence fix needs further investigation")
    
    print("\n📋 Next Steps:")
    print("1. Test in the actual application:")
    print("   - Set hole 25 to positive_clustered")
    print("   - Save annotations to JSON")
    print("   - Restart software and load JSON")
    print("   - Verify hole 25 shows positive_clustered, not positive_heavy_growth")
    print("2. Watch for new debug output:")
    print("   - [SERIALIZE] 保存 enhanced_data 到字典")
    print("   - [DESERIALIZE] 恢复 enhanced_data 从字典")
    print("   - [DEBUG] enhanced_data包含字段: ['feature_combination', ...]")
    
    sys.exit(0 if success else 1)