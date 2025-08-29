#!/usr/bin/env python3
"""
Test script to verify label generation fix for interference factors
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

def test_label_generation():
    """Test label generation with interference factors"""
    print("🔧 Label Generation Fix Test")
    print("=" * 50)
    
    try:
        # Test the UI version
        print("\n📝 Testing UI FeatureCombination class:")
        from ui.enhanced_annotation_panel import FeatureCombination, GrowthLevel, GrowthPattern, InterferenceType
        
        # Test case 1: Negative with pores
        combination1 = FeatureCombination(
            growth_level=GrowthLevel.NEGATIVE,
            growth_pattern=GrowthPattern.CLEAN,
            interference_factors={InterferenceType.PORES},
            confidence=1.0
        )
        
        label1 = combination1.to_label
        print(f"✓ Negative with pores: '{label1}'")
        
        # Test case 2: Positive clustered with artifacts
        combination2 = FeatureCombination(
            growth_level=GrowthLevel.POSITIVE,
            growth_pattern=GrowthPattern.CLUSTERED,
            interference_factors={InterferenceType.ARTIFACTS, InterferenceType.PORES},
            confidence=1.0
        )
        
        label2 = combination2.to_label
        print(f"✓ Positive clustered with artifacts and pores: '{label2}'")
        
        # Test the models version for comparison
        print("\n📝 Testing Models FeatureCombination class:")
        from models.enhanced_annotation import FeatureCombination as ModelFeatureCombination
        from models.enhanced_annotation import GrowthLevel as ModelGrowthLevel
        from models.enhanced_annotation import GrowthPattern as ModelGrowthPattern
        from models.enhanced_annotation import InterferenceType as ModelInterferenceType
        
        # Test case 3: Negative with pores (models version)
        combination3 = ModelFeatureCombination(
            growth_level=ModelGrowthLevel.NEGATIVE,
            growth_pattern=ModelGrowthPattern.CLEAN,
            interference_factors={ModelInterferenceType.PORES},
            confidence=1.0
        )
        
        label3 = combination3.to_label()
        print(f"✓ Negative with pores (models): '{label3}'")
        
        # Verify no Chinese characters
        print("\n🔍 Chinese Character Check:")
        chinese_chars = ['带', '含', '与', '和']
        
        for i, label in enumerate([label1, label2, label3], 1):
            has_chinese = any(char in label for char in chinese_chars)
            status = "❌ Contains Chinese" if has_chinese else "✅ English only"
            print(f"Label {i}: {status} - '{label}'")
        
        # Check expected format
        print("\n📋 Expected vs. Actual:")
        print("Expected format: 'negative_with_pores'")
        print(f"UI class result: '{label1}'")
        print(f"Models class result: '{label3}'")
        
        if 'with_' in label1 and 'with_' in label3:
            print("✅ Both classes now use English format")
            return True
        else:
            print("❌ Format mismatch detected")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🔧 Label Generation Fix Verification")
    print("Goal: Ensure interference factor labels use English instead of Chinese")
    print()
    
    success = test_label_generation()
    
    if success:
        print("\n✅ Label generation fix verified successfully")
        print("Labels now use 'with_' prefix instead of '带' for interference factors")
    else:
        print("\n❌ Label generation fix needs review")
    
    print("\n📋 Benefits of English labels:")
    print("✓ System compatibility (file naming, exports)")
    print("✓ Consistent with models implementation")
    print("✓ International standard format")
    print("✓ Avoids encoding issues")
    
    sys.exit(0 if success else 1)