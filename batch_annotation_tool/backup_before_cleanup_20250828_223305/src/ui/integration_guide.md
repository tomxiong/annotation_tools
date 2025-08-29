# 全景图导航功能集成指南

本文档提供了将全景图导航功能集成到 `PanoramicAnnotationGUI` 类的详细步骤。

## 步骤 1: 修改 `__init__` 方法

在 `__init__` 方法中添加以下变量初始化：

```python
# 在初始化变量部分添加
self.panoramic_ids = []  # 存储所有全景图ID

# 在创建变量部分添加
self.panoramic_id_var = tk.StringVar()  # 当前选中的全景图ID
```

## 步骤 2: 修改 `create_navigation_panel` 方法

在 `create_navigation_panel` 方法中添加全景图导航部分：

```python
# 创建全景图导航部分
panoramic_label = ttk.Label(nav_frame, text="全景图导航")
panoramic_label.pack(anchor=tk.W, padx=5, pady=(5, 0))

panoramic_frame = ttk.Frame(nav_frame)
panoramic_frame.pack(pady=5, padx=5)

# 上一个全景图按钮
ttk.Button(panoramic_frame, text="◀ 上一全景", width=10,
          command=self.go_prev_panoramic).pack(side=tk.LEFT, padx=2)

# 全景图下拉列表
self.panoramic_combobox = ttk.Combobox(panoramic_frame, 
                                      textvariable=self.panoramic_id_var,
                                      width=20)
self.panoramic_combobox.pack(side=tk.LEFT, padx=5)
self.panoramic_combobox.bind('<<ComboboxSelected>>', self.on_panoramic_selected)

# 下一个全景图按钮
ttk.Button(panoramic_frame, text="下一全景 ▶", width=10,
          command=self.go_next_panoramic).pack(side=tk.LEFT, padx=2)

# 添加分隔线
separator1 = ttk.Separator(nav_frame, orient='horizontal')
separator1.pack(fill=tk.X, padx=5, pady=5)
```

## 步骤 3: 修改 `load_data` 方法

在 `load_data` 方法中添加全景图列表更新：

```python
# 在加载数据后，添加以下代码
self.update_panoramic_list()
```

## 步骤 4: 添加全景图导航方法

将 `panoramic_navigation_methods.py` 文件中的以下方法添加到 `PanoramicAnnotationGUI` 类中：

1. `update_panoramic_list`
2. `on_panoramic_selected`
3. `go_prev_panoramic`
4. `go_next_panoramic`
5. `go_to_panoramic`

## 步骤 5: 更新 `load_current_slice` 方法

在 `load_current_slice` 方法中添加全景图下拉列表更新：

```python
# 在更新当前全景图ID后，添加以下代码
if self.current_panoramic_id and self.current_panoramic_id in self.panoramic_ids:
    self.panoramic_id_var.set(self.current_panoramic_id)
```

## 完成集成

完成上述步骤后，全景图导航功能将被成功集成到 `PanoramicAnnotationGUI` 类中。用户将能够：

1. 使用上一个/下一个全景图按钮在全景图之间导航
2. 使用下拉列表直接选择任意全景图
3. 切换全景图时自动加载该全景图的第一个孔位