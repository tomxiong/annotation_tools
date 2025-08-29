# Method/Property Conflict Fix for to_label

## 🎯 Problem Summary

When clicking "保存并下一个" (Save and Next), the application crashed with the error:
```
保存标注失败: 'str' object is not callable
```

## 🔍 Root Cause Analysis

The issue was caused by **TWO different FeatureCombination classes** with conflicting `to_label` implementations:

### 1. UI Panel FeatureCombination (`src/ui/enhanced_annotation_panel.py`)
```python
class FeatureCombination:
    @property
    def to_label(self):
        """生成标注标签"""
        # Returns a string directly
        return "_".join(label_parts)
```

### 2. Models FeatureCombination (`src/models/enhanced_annotation.py`)
```python
@dataclass
class FeatureCombination:
    def to_label(self) -> str:
        """生成标签字符串"""
        # Returns a string when called as method
        return "_".join(parts)
```

## 🚨 The Conflict

In our previous JSON serialization fix, we changed all references from:
```python
self.label = self.feature_combination.to_label  # Property reference (OLD)
```

To:
```python
self.label = self.feature_combination.to_label()  # Method call (BROKE UI)
```

This worked for the Models FeatureCombination but **broke** when using the UI Panel FeatureCombination because:
1. UI Panel: `to_label` is a **property** that returns a string
2. When we call `to_label()`, we're trying to call that **string** as a function
3. Result: `'str' object is not callable`

## ✅ Complete Fix

### File: `src/models/enhanced_annotation.py`

**Enhanced compatibility handling in 4 locations**:

#### 1. Line 115 - `EnhancedPanoramicAnnotation.__init__()`
```python
# Handle both method and property for to_label
if hasattr(self.feature_combination.to_label, '__call__'):
    self.label = self.feature_combination.to_label()  # Method call
else:
    self.label = self.feature_combination.to_label  # Property access
```

#### 2. Line 134 - `update_feature_combination()`
```python
# Handle both method and property for to_label
if hasattr(feature_combination.to_label, '__call__'):
    self.label = feature_combination.to_label()  # Method call
else:
    self.label = feature_combination.to_label  # Property access
```

#### 3. Line 166 - `_sync_fields()`
```python
# Handle both method and property for to_label
if hasattr(self.feature_combination.to_label, '__call__'):
    self.label = self.feature_combination.to_label()  # Method call
else:
    self.label = self.feature_combination.to_label  # Property access
```

#### 4. Line 177 - `get_training_label()`
```python
# Handle both method and property for to_label
if hasattr(self.feature_combination.to_label, '__call__'):
    return self.feature_combination.to_label()  # Method call
else:
    return self.feature_combination.to_label  # Property access
```

#### 5. Line 399 - `TrainingDataGenerator._create_label_encodings()`
```python
# Handle both method and property for to_label
if hasattr(feature_combo.to_label, '__call__'):
    extended_labels.append(feature_combo.to_label())  # Method call
else:
    extended_labels.append(feature_combo.to_label)  # Property access
```

## 🧪 How the Fix Works

The fix uses Python's `hasattr()` function to detect whether `to_label` is callable:

1. **If callable** (`hasattr(obj.to_label, '__call__')` returns `True`):
   - It's a method → call it: `feature_combination.to_label()`

2. **If not callable** (`hasattr(obj.to_label, '__call__')` returns `False`):
   - It's a property → access it: `feature_combination.to_label`

## 🎉 Benefits

1. **Full Compatibility**: Works with both UI Panel and Models FeatureCombination classes
2. **No Breaking Changes**: Existing code continues to work
3. **Future-Proof**: Handles any future implementations of to_label
4. **JSON Serialization**: Maintains the JSON persistence fixes
5. **Error-Free**: Eliminates the "'str' object is not callable" error

## 📋 Testing

After this fix, the following should work without errors:
1. Click "保存并下一个" (Save and Next)
2. Enhanced annotations are properly saved
3. JSON persistence works correctly
4. No more "'str' object is not callable" errors

This fix ensures that the enhanced annotation system works seamlessly regardless of which FeatureCombination class implementation is used.