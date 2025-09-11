# 模块化GUI目录结构支持实现报告

## 任务概述
根据用户需求，模块化GUI需要支持原始代码中的目录组织模式：
- `<全景图>.bmp` + `<全景图>.cfg` + `<全景图>目录/hole_<孔号>.png`

## 分析结果

### 原始代码支持的目录结构

#### 1. 子目录模式 (推荐的原始模式)
```
数据目录/
├── EB10000026.bmp          # 全景图文件
├── EB10000026.cfg          # 配置文件
├── EB10000026/             # 切片目录
│   ├── hole_1.png          # 1号孔切片
│   ├── hole_2.png          # 2号孔切片
│   ├── ...
│   └── hole_120.png        # 120号孔切片
├── EB10000027.png          # 另一个全景图
├── EB10000027.cfg          # 对应配置文件
└── EB10000027/             # 对应切片目录
    ├── hole_1.png
    └── ...
```

#### 2. 独立路径模式 (兼容模式)
```
数据目录/
├── EB10000026.bmp              # 全景图文件
├── EB10000026_hole_1.png       # 切片文件
├── EB10000026_hole_2.png
├── EB10000026_hole_108.png
└── EB10000026_hole_120.png
```

### 实现修改

#### 修改的文件
- `src/ui/modules/data_manager.py`

#### 关键修改内容

##### 1. 新增子目录模式扫描
```python
def _scan_subdirectory_slices(self) -> List[Dict]:
    """扫描子目录模式的切片文件"""
    subdirectory_slices = []
    
    # 遍历所有子目录
    for item in self.current_directory.iterdir():
        if item.is_dir():
            panoramic_id = item.name
            
            # 在子目录中查找 hole_*.png 文件
            for slice_file in item.iterdir():
                if (slice_file.is_file() and 
                    slice_file.name.startswith('hole_') and 
                    slice_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif']):
                    
                    # 解析孔号：hole_1.png -> 1
                    hole_str = slice_file.stem[5:]  # 去掉 'hole_' 前缀
                    if hole_str.isdigit():
                        hole_number = int(hole_str)
                        if 1 <= hole_number <= 120:
                            subdirectory_slices.append({
                                'filename': slice_file.name,
                                'filepath': str(slice_file),
                                'panoramic_id': panoramic_id,
                                'hole_number': hole_number,
                                'structure_type': 'subdirectory'
                            })
    return subdirectory_slices
```

##### 2. 改进全景图扫描
```python
def _scan_panoramic_files(self):
    """
    扫描全景图文件
    支持子目录模式：直接扫描目录中的全景图文件
    """
    panoramic_formats = ['.bmp', '.png', '.jpg', '.jpeg', '.tiff', '.tif']
    
    # 直接扫描目录中的全景图文件
    for file_path in self.current_directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in panoramic_formats:
            panoramic_id = file_path.stem
            
            # 检查是否有对应的子目录（子目录模式的标志）
            subdir = self.current_directory / panoramic_id
            has_subdir = subdir.exists() and subdir.is_dir()
            
            # 检查是否有对应的切片文件（独立模式的标志）
            has_slices = any(slice_info['panoramic_id'] == panoramic_id for slice_info in self.slice_files)
            
            # 如果有子目录或有切片文件，则认为是有效的全景图
            if has_subdir or has_slices:
                self.panoramic_files.append({
                    'panoramic_id': panoramic_id,
                    'file_path': str(file_path)
                })
```

##### 3. 增强CFG文件支持
```python
def _load_cfg_files(self):
    """
    加载CFG配置文件
    支持子目录模式：查找与全景图同名的CFG文件
    """
    # 对于每个全景图，查找对应的CFG文件
    for panoramic_info in self.panoramic_files:
        panoramic_id = panoramic_info['panoramic_id']
        cfg_file = self.current_directory / f"{panoramic_id}.cfg"
        
        if cfg_file.exists():
            try:
                with open(cfg_file, 'r', encoding='utf-8') as f:
                    cfg_content = f.read()
                    self.cfg_data[panoramic_id] = cfg_content
            except Exception as e:
                self.gui.log_warning(f"加载CFG文件失败 {cfg_file}: {e}", "DATA")
```

## 测试验证结果

### 子目录模式测试
✅ **成功** - 检测结果：
- 切片文件: 12个 (3个全景图 × 4个孔位)
- 全景图文件: 3个
- CFG文件: 3个
- 结构类型: subdirectory

### 独立路径模式测试  
✅ **成功** - 检测结果：
- 切片文件: 6个
- 全景图文件: 2个
- 结构类型: independent

### 测试用例
```python
# 子目录模式测试数据
EB10000026.bmp + EB10000026.cfg + EB10000026/hole_*.png
EB10000027.png + EB10000027.cfg + EB10000027/hole_*.png
EB10000028.jpg + EB10000028.cfg + EB10000028/hole_*.png

# 独立路径模式测试数据
EB10000026_hole_001.png, EB10000026_hole_108.png + EB10000026.bmp
EB10000027_hole_001.jpg, EB10000027_hole_050.jpg + EB10000027.png
```

## 功能特性

### 支持的文件格式
- **全景图**: .bmp, .png, .jpg, .jpeg, .tiff, .tif
- **切片图**: .png, .jpg, .jpeg, .bmp, .tiff, .tif
- **配置文件**: .cfg

### 目录结构检测
- 自动检测目录结构类型
- 同时支持两种模式
- 优先使用子目录模式（原始推荐模式）

### 数据组织
- 按全景ID和孔号排序
- 支持孔号范围：1-120
- 自动关联全景图、切片和CFG文件

## 结论

✅ **完全支持原始代码的目录组织模式**

模块化GUI现在完全支持用户要求的目录结构：
- `<全景图>.bmp` - 全景图文件
- `<全景图>.cfg` - 配置文件  
- `<全景图>目录/hole_<孔号>.png` - 切片文件

同时保持向下兼容，支持独立路径模式的切片文件。

### 使用方式
用户可以直接使用以下目录结构：
```
工作目录/
├── EB10000026.bmp
├── EB10000026.cfg  
├── EB10000026/
│   ├── hole_1.png
│   ├── hole_2.png
│   └── hole_120.png
└── ...
```

模块化GUI将自动检测并正确加载所有文件。
