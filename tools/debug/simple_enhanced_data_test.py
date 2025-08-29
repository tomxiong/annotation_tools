#!/usr/bin/env python3
"""
Simple test to verify enhanced_data is preserved in to_dict/from_dict
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
current_file = Path(__file__).resolve()
project_root = current_file.parent
src_dir = project_root / "src"

if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

try:
    from models.panoramic_annotation import PanoramicAnnotation
    
    # Create annotation with enhanced_data
    annotation = PanoramicAnnotation(
        image_path="test.png",
        label="positive_clustered", 
        bbox=[0, 0, 70, 70],
        panoramic_image_id="TEST001",
        hole_number=25,
        hole_row=2,
        hole_col=1,
        microbe_type="bacteria",
        growth_level="positive",
        annotation_source="enhanced_manual"
    )
    
    # Set enhanced_data
    annotation.enhanced_data = {
        'feature_combination': {
            'growth_level': 'positive',
            'growth_pattern': 'clustered',
            'interference_factors': [],
            'confidence': 1.0
        },
        'annotation_source': 'enhanced_manual'
    }
    
    print("✓ Created annotation with enhanced_data")
    print(f"✓ Enhanced_data keys: {list(annotation.enhanced_data.keys())}")
    
    # Test to_dict
    data_dict = annotation.to_dict()
    has_enhanced_data = 'enhanced_data' in data_dict
    print(f"✓ to_dict() includes enhanced_data: {has_enhanced_data}")
    
    if has_enhanced_data:
        print(f"✓ Enhanced_data preserved: {data_dict['enhanced_data']}")
        
        # Test from_dict
        restored_annotation = PanoramicAnnotation.from_dict(data_dict)
        has_restored_enhanced_data = hasattr(restored_annotation, 'enhanced_data') and restored_annotation.enhanced_data
        print(f"✓ from_dict() restores enhanced_data: {has_restored_enhanced_data}")
        
        if has_restored_enhanced_data:
            print("🎉 SUCCESS: Enhanced data persistence fix works!")
        else:
            print("❌ FAILURE: from_dict() doesn't restore enhanced_data")
    else:
        print("❌ FAILURE: to_dict() doesn't include enhanced_data")
        
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()