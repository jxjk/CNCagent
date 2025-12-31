"""
AI辅助NC编程工具用户界面模块
实现极简操作界面和拖拽式参数配置
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import cv2
import numpy as np
import os
from src.modules.ai_nc_helper import AI_NC_Helper
import threading
from PIL import Image, ImageTk

# 尝试导入3D查看相关库
try:
    import plotly.graph_objects as go
    from plotly.offline import plot
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
    print("警告: 未安装plotly库，3D模型可视化功能受限。请运行: pip install plotly")


class SimpleNC_GUI:
    """
    简单的NC编程工具用户界面
    遵循极简设计理念，提供核心功能按钮
    """
    def __init__(self, root):
        self.root = root
        self.root.title("AI辅助NC编程工具 - 简易版")
        self.root.geometry("1000x700")
        self.nc_helper = AI_NC_Helper()
        self.current_image = None
        self.current_image_path = None
        self.current_nc_code = ""
        self.material = tk.StringVar(value="Aluminum")
        self.processing_type = tk.StringVar(value="general")
        # 将描述改为普通字符串变量，因为我们会用单独的文本区域
        self.description_text = tk.StringVar(value="")
        # 保持原来的小输入框作为快捷输入
        self.description = tk.StringVar(value="")
        self.only_description_mode = tk.BooleanVar(value=False)  # 新增：仅描述模式
        self.file_types = [
            ("图像文件", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("PDF文件", "*.pdf"),
            ("3D模型文件", "*.stl *.step *.stp *.igs *.iges *.obj *.ply"),
            ("所有文件", "*.*")
        ]
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        main_frame.rowconfigure(3, weight=2)
        main_frame.rowconfigure(4, weight=2)
        
        # 顶部控制栏
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 核心功能按钮
        ttk.Button(control_frame, text="导入图纸", command=self.load_drawing).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="识别特征", command=self.detect_features).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="生成NC", command=self.generate_nc).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="导出代码", command=self.export_nc).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="验证代码", command=self.validate_nc).pack(side=tk.LEFT, padx=(0, 5))
        
        # 仅描述模式复选框
        description_mode_check = ttk.Checkbutton(control_frame, text="仅描述模式", variable=self.only_description_mode, command=self.toggle_description_mode)
        description_mode_check.pack(side=tk.LEFT, padx=(20, 10))
        
        # 材料选择
        ttk.Label(control_frame, text="材料:").pack(side=tk.LEFT, padx=(10, 5))
        material_combo = ttk.Combobox(control_frame, textvariable=self.material, values=["Aluminum", "Steel", "Stainless Steel", "Brass", "Plastic"], state="readonly")
        material_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # 用户描述输入
        ttk.Label(control_frame, text="描述:").pack(side=tk.LEFT, padx=(0, 5))
        desc_entry = ttk.Entry(control_frame, textvariable=self.description, width=50)  # 增加宽度
        desc_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 预览窗口标签
        ttk.Label(main_frame, text="图纸预览:").grid(row=1, column=0, sticky=tk.W, pady=(0, 5))
        ttk.Label(main_frame, text="NC代码预览:").grid(row=1, column=1, sticky=tk.W, pady=(0, 5))
        
        # 左侧图纸预览区域
        preview_frame = ttk.Frame(main_frame)
        preview_frame.grid(row=2, column=0, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        preview_frame.rowconfigure(1, weight=1)
        preview_frame.columnconfigure(0, weight=1)
        
        # 预览画布
        self.canvas = tk.Canvas(preview_frame, bg='white', width=400, height=300)
        self.canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # 添加滚动事件支持
        self.canvas.bind("<MouseWheel>", self.on_canvas_scroll)  # Windows
        self.canvas.bind("<Button-4>", self.on_canvas_scroll)    # Linux
        self.canvas.bind("<Button-5>", self.on_canvas_scroll)    # Linux
        
        # 添加拖拽支持
        self.canvas.bind("<ButtonPress-2>", self.on_canvas_drag_start)
        self.canvas.bind("<B2-Motion>", self.on_canvas_drag)
        
        # 添加缩放和旋转支持
        self.canvas.bind("<Control-KeyPress-plus>", self.zoom_in)
        self.canvas.bind("<Control-KeyPress-minus>", self.zoom_out)
        self.canvas.bind("<Control-KeyPress-r>", self.rotate_image)
        
        # 初始化视图参数
        self.canvas_scale = 1.0
        self.canvas_rotation = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        
        # 初始化时显示欢迎信息
        self.show_welcome_message()
        
        # 添加滚动条
        canvas_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        canvas_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.canvas.configure(yscrollcommand=canvas_scrollbar.set)
        
        # 特征列表
        ttk.Label(preview_frame, text="识别特征列表:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        self.feature_listbox = tk.Listbox(preview_frame)
        self.feature_listbox.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.feature_listbox.bind("<<ListboxSelect>>", self.on_feature_select)
        preview_frame.rowconfigure(3, weight=1)
        
        # 右侧用户描述输入区域
        desc_frame = ttk.Frame(main_frame)
        desc_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        desc_frame.rowconfigure(0, weight=1)
        desc_frame.columnconfigure(0, weight=1)
        
        ttk.Label(desc_frame, text="加工描述:").grid(row=0, column=0, sticky=tk.W)
        self.desc_text = scrolledtext.ScrolledText(desc_frame, wrap=tk.WORD, width=60, height=8)
        self.desc_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(5, 5))
        
        # 右侧NC代码预览区域
        nc_frame = ttk.Frame(main_frame)
        nc_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        nc_frame.rowconfigure(0, weight=1)
        nc_frame.columnconfigure(0, weight=1)
        
        self.nc_text = scrolledtext.ScrolledText(nc_frame, wrap=tk.NONE, width=60, height=12)
        self.nc_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 分析报告区域
        report_frame = ttk.Frame(main_frame)
        report_frame.grid(row=4, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        report_frame.rowconfigure(0, weight=1)
        report_frame.columnconfigure(0, weight=1)
        
        ttk.Label(report_frame, text="分析报告:").grid(row=0, column=0, sticky=tk.W)
        self.report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, width=60, height=6)
        self.report_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def toggle_description_mode(self):
        """切换仅描述模式"""
        if self.only_description_mode.get():
            self.status_var.set("已切换到仅描述模式 - 无需导入图纸")
            # 在仅描述模式下，自动创建虚拟图像
            self.create_virtual_image()
            # 更新画布以显示虚拟图像
            self.display_cv_image()
        else:
            self.status_var.set("已切换到正常模式 - 请导入图纸")
            # 重置当前图像
            self.current_image = None
            # 重置3D模型数据
            if hasattr(self, 'current_3d_model_path'):
                delattr(self, 'current_3d_model_path')
            if hasattr(self, 'current_3d_model_data'):
                delattr(self, 'current_3d_model_data')
            self.show_welcome_message()
    
    def create_virtual_image_from_3d(self, model_data):
        """根据3D模型数据创建虚拟2D图像"""
        # 创建一个空白的虚拟图像
        width, height = 800, 600
        virtual_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 获取3D模型信息
        geometric_features = model_data.get('geometric_features', {})
        bounding_box = geometric_features.get('bounding_box', {})
        
        if bounding_box:
            # 根据3D模型的边界框信息创建2D投影
            min_coords = bounding_box.get('min', [0, 0, 0])
            max_coords = bounding_box.get('max', [10, 10, 10])
            
            # 计算中心点和尺寸
            center_x = (min_coords[0] + max_coords[0]) / 2
            center_y = (min_coords[1] + max_coords[1]) / 2
            size_x = max_coords[0] - min_coords[0]
            size_y = max_coords[1] - min_coords[1]
            
            # 将3D坐标映射到2D图像空间
            img_center_x = width // 2
            img_center_y = height // 2
            
            # 计算缩放比例，确保模型适合图像
            scale_x = width * 0.6 / (size_x if size_x > 0 else 10)
            scale_y = height * 0.6 / (size_y if size_y > 0 else 10)
            scale = min(scale_x, scale_y)
            
            # 绘制边界框
            half_size_x = int((size_x * scale) / 2)
            half_size_y = int((size_y * scale) / 2)
            
            top_left = (img_center_x - half_size_x, img_center_y - half_size_y)
            bottom_right = (img_center_x + half_size_x, img_center_y + half_size_y)
            
            cv2.rectangle(virtual_image, top_left, bottom_right, (255, 255, 255), 2)
        
        # 添加3D模型信息文本
        vertices_count = geometric_features.get('vertices_count', 0)
        faces_count = geometric_features.get('faces_count', 0)
        volume = geometric_features.get('volume', 0)
        
        cv2.putText(virtual_image, f"3D模型预览 - 顶点: {vertices_count}, 面: {faces_count}", 
                   (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(virtual_image, f"体积: {volume:.2f}", 
                   (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # 如果检测到几何基元，也显示出来
        geometric_primitives = geometric_features.get('geometric_primitives', [])
        if geometric_primitives:
            cv2.putText(virtual_image, f"基元: {len(geometric_primitives)}个", 
                       (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        self.current_image = virtual_image
        self.current_image_path = None  # 表示这是虚拟图像
    
    def create_virtual_image(self):
        """创建虚拟图像用于仅描述模式"""
        # 创建一个空白的虚拟图像
        width, height = 800, 600
        virtual_image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加一些简单的几何图形作为示例
        # 在图像中央添加一个矩形
        cv2.rectangle(virtual_image, (300, 200), (500, 400), (255, 255, 255), 2)
        
        # 添加一个圆形
        cv2.circle(virtual_image, (400, 300), 50, (255, 255, 255), 2)
        
        # 添加一些文本说明
        cv2.putText(virtual_image, "虚拟图纸", (350, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(virtual_image, "仅描述模式", (330, 500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        self.current_image = virtual_image
        self.current_image_path = None  # 表示这是虚拟图像
    
    def show_3d_model_plotly(self, file_path):
        """使用Plotly显示3D模型"""
        if not HAS_PLOTLY:
            # 如果没有Plotly，回退到虚拟图像
            from src.modules.model_3d_processor import process_3d_model
            model_data = process_3d_model(file_path)
            self.create_virtual_image_from_3d(model_data)
            self.display_cv_image()
            return
        
        try:
            # 尝试加载STL文件进行可视化
            ext = file_path.lower().split('.')[-1]
            
            if ext == 'stl':
                # 使用numpy-stl库加载STL文件
                try:
                    import numpy as np
                    from stl import mesh
                    import tkinterweb  # 用于在Tkinter中显示HTML
                    
                    # 加载STL文件
                    stl_mesh = mesh.Mesh.from_file(file_path)
                    
                    # 创建Plotly 3D图形
                    figure = go.Figure(data=go.Mesh3d(
                        x=stl_mesh.x.flatten(),
                        y=stl_mesh.y.flatten(),
                        z=stl_mesh.z.flatten(),
                        alphahull=0,  # 使用凸包
                        opacity=0.8,
                        color='lightblue'
                    ))
                    
                    figure.update_layout(
                        title="3D模型预览",
                        scene=dict(
                            xaxis_title="X轴",
                            yaxis_title="Y轴", 
                            zaxis_title="Z轴"
                        ),
                        width=600,
                        height=400
                    )
                    
                    # 生成HTML并在新窗口中显示
                    html_str = figure.to_html(include_plotlyjs='cdn', config={'displayModeBar': True})
                    
                    # 创建新窗口显示3D模型
                    model_window = tk.Toplevel(self.root)
                    model_window.title("3D模型查看器")
                    model_window.geometry("800x600")
                    
                    # 如果有tkinterweb可用，使用它显示3D模型
                    try:
                        import tkinterweb as web
                        browser = web.HtmlFrame(model_window)
                        browser.load_html(html_str)
                        browser.pack(fill=tk.BOTH, expand=True)
                    except ImportError:
                        # 如果没有tkinterweb，显示一个简单的消息
                        label = tk.Label(model_window, text="3D模型已加载，需要安装tkinterweb以可视化显示", 
                                       font=("Arial", 12))
                        label.pack(pady=50)
                        # 同时在命令行输出提示
                        print("提示：安装tkinterweb以在GUI中查看3D模型：pip install tkinterweb")
                
                except ImportError:
                    print("提示：安装numpy-stl以支持STL文件可视化：pip install numpy-stl")
                    # 回退到虚拟图像
                    from src.modules.model_3d_processor import process_3d_model
                    model_data = process_3d_model(file_path)
                    self.create_virtual_image_from_3d(model_data)
                    self.display_cv_image()
            else:
                # 对于其他3D格式，显示一个信息窗口
                info_window = tk.Toplevel(self.root)
                info_window.title("3D模型信息")
                info_window.geometry("400x200")
                
                tk.Label(info_window, text=f"已加载3D模型: {os.path.basename(file_path)}", 
                         font=("Arial", 12, "bold")).pack(pady=10)
                
                # 显示模型统计信息
                from src.modules.model_3d_processor import process_3d_model
                model_data = process_3d_model(file_path)
                features = model_data.get('geometric_features', {})
                
                stats = f"""
格式: {file_path.split('.')[-1].upper()}
顶点数: {features.get('vertices_count', '未知')}
面数: {features.get('faces_count', '未知')}
体积: {features.get('volume', '未知'):.2f}
表面积: {features.get('surface_area', '未知'):.2f}
                """.strip()
                
                tk.Label(info_window, text=stats, justify=tk.LEFT, font=("Courier", 10)).pack(pady=10)
                
                tk.Button(info_window, text="关闭", command=info_window.destroy).pack(pady=10)
                
        except Exception as e:
            print(f"显示3D模型时出错: {e}")
            # 出错时回退到虚拟图像
            from src.modules.model_3d_processor import process_3d_model
            model_data = process_3d_model(file_path)
            self.create_virtual_image_from_3d(model_data)
            self.display_cv_image()
    
    def load_drawing(self):
        """加载图纸文件"""
        file_path = filedialog.askopenfilename(
            title="选择图纸文件",
            filetypes=self.file_types
        )
        if file_path:
            self.current_image_path = file_path
            try:
                # 检查文件扩展名
                _, ext = os.path.splitext(file_path.lower())
                
                if ext in ['.stl', '.step', '.stp', '.igs', '.iges', '.obj', '.ply', '.off', '.gltf', '.glb']:
                    # 处理3D模型文件
                    from src.modules.model_3d_processor import process_3d_model
                    try:
                        model_data = process_3d_model(file_path)
                        self.current_3d_model_path = file_path
                        self.current_3d_model_data = model_data
                        
                        # 尝试显示3D模型（如果支持）
                        if HAS_PLOTLY:
                            self.show_3d_model_plotly(file_path)
                        else:
                            # 创建虚拟2D图像用于显示
                            self.create_virtual_image_from_3d(model_data)
                            self.display_cv_image()
                        
                        self.status_var.set(f"已加载3D模型: {os.path.basename(file_path)} - {model_data['geometric_features'].get('vertices_count', '未知')}顶点")
                    except Exception as e:
                        messagebox.showerror("错误", f"处理3D模型时出错: {str(e)}")
                        return
                elif ext in ['.pdf']:
                    # 处理PDF文件
                    from src.modules.pdf_parsing_process import pdf_to_images
                    images = pdf_to_images(file_path)
                    if images:
                        # 使用第一页
                        from PIL import Image
                        pil_image = images[0]  # 第一页的PIL图像
                        # 转换为numpy数组用于特征检测
                        self.current_image = np.array(pil_image.convert('L'))  # 转为灰度图
                        # 保存原始PIL图像用于显示
                        self.current_pil_image = pil_image
                        self.display_pil_image()
                        self.status_var.set(f"已加载PDF: {os.path.basename(file_path)} (第1页)")
                    else:
                        messagebox.showerror("错误", "无法从PDF中提取图像")
                else:
                    # 处理图像文件
                    self.current_image = cv2.imread(file_path)
                    if self.current_image is not None:
                        self.display_cv_image()
                        self.status_var.set(f"已加载: {os.path.basename(file_path)}")
                    else:
                        messagebox.showerror("错误", "无法读取图像文件")
            except Exception as e:
                messagebox.showerror("错误", f"加载文件时出错: {str(e)}")
    
    def display_pil_image(self):
        """在画布上显示PIL图像"""
        if hasattr(self, 'current_pil_image') and self.current_pil_image is not None:
            try:
                # 转换PIL图像为Tkinter可用的格式
                pil_image = self.current_pil_image
                
                # 应用用户缩放比例
                img_width, img_height = pil_image.size
                new_width = int(img_width * self.canvas_scale)
                new_height = int(img_height * self.canvas_scale)
                
                # 调整图像大小
                resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # 如果需要旋转，则旋转图像
                if self.canvas_rotation != 0:
                    resized_image = resized_image.rotate(self.canvas_rotation, expand=True)
                    # 更新宽高以适应旋转后的尺寸
                    new_width, new_height = resized_image.size
                
                self.photo = ImageTk.PhotoImage(resized_image)
                
                # 清除画布并绘制图像
                self.canvas.delete("all")
                # 居中显示，考虑缩放和平移
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                if canvas_width <= 1: canvas_width = 400
                if canvas_height <= 1: canvas_height = 300
                
                x = (canvas_width - new_width) // 2 + self.canvas_offset_x
                y = (canvas_height - new_height) // 2 + self.canvas_offset_y
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            except Exception as e:
                print(f"显示PIL图像时出错: {e}")
    
    def detect_features(self):
        """检测图纸中的特征"""
        # 检查是否处于仅描述模式
        if self.only_description_mode.get():
            self.status_var.set("仅描述模式：跳过特征检测，直接使用描述信息")
            # 仅描述模式不需要检测特征，直接使用描述信息
            messagebox.showinfo("提示", "当前为仅描述模式，已跳过特征检测步骤。\n请直接点击'生成NC'按钮。")
            return
        
        if self.current_image is None:
            messagebox.showwarning("警告", "请先加载图纸")
            return
        
        self.status_var.set("正在检测特征...")
        self.root.update()
        
        try:
            # 从用户描述中获取额外信息
            drawing_text = self.description.get()
            features_data = self.nc_helper.feature_detector.detect_features(self.current_image, drawing_text)
            
            # 更新特征列表
            self.feature_listbox.delete(0, tk.END)
            for i, feature in enumerate(features_data["all_features"]):
                shape = feature.get("shape", "unknown")
                center = feature.get("center", (0, 0))
                self.feature_listbox.insert(tk.END, f"{i+1}. {shape.upper()} at ({center[0]:.1f}, {center[1]:.1f}) - Confidence: {feature.get('confidence', 0):.2f}")
            
            self.status_var.set(f"特征检测完成: {len(features_data['all_features'])} 个特征")
        except Exception as e:
            messagebox.showerror("错误", f"特征检测时出错: {str(e)}")
            self.status_var.set("就绪")
    
    def generate_nc(self):
        """生成NC代码"""
        # 检查是否在仅描述模式下，且没有描述
        if self.only_description_mode.get() and not self.description.get().strip():
            messagebox.showwarning("警告", "请在仅描述模式下输入加工描述")
            return
        
        # 在仅描述模式下，不应使用图像，直接从描述生成NC代码
        if self.only_description_mode.get():
            self.generate_nc_from_description_only()
        elif self.current_image is None and not hasattr(self, 'current_3d_model_path'):
            messagebox.showwarning("警告", "请先加载图纸或3D模型并检测特征")
            return
        else:
            self.status_var.set("正在生成NC代码...")
            self.root.update()
            
            try:
                # 从用户描述中获取额外信息
                drawing_text = self.description.get()
                material = self.material.get()
                user_description = self.description.get()
                
                # 获取2D文件路径（如果存在）
                pdf_path = self.current_image_path if hasattr(self, 'current_image_path') and self.current_image_path else None
                
                # 获取3D模型路径（如果存在）
                model_3d_path = getattr(self, 'current_3d_model_path', None)
                
                # 在后台线程中生成NC代码
                def generate_in_thread():
                    try:
                        # 使用统一生成器来处理2D/3D输入
                        from src.modules.unified_generator import generate_cnc_with_unified_approach
                        import os
                        
                        # 从环境变量获取API配置 - 与WEB端保持一致
                        api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
                        model_name = os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'deepseek-chat'))
                        
                        # 与WEB端使用完全相同的调用方式和参数
                        nc_code = generate_cnc_with_unified_approach(
                            user_prompt=user_description,
                            pdf_path=pdf_path,  # 可能为None
                            model_3d_path=model_3d_path,  # 可能为None
                            api_key=api_key,
                            model=model_name,
                            material=material  # 添加材料参数以保持一致性
                        )
                        
                        self.current_nc_code = nc_code
                        self.root.after(0, self.display_nc_code, nc_code)
                        self.root.after(0, self.update_report)
                        self.root.after(0, lambda: self.status_var.set("NC代码生成完成"))
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("错误", f"生成NC代码时出错: {str(e)}"))
                        self.root.after(0, lambda: self.status_var.set("就绪"))
                
                thread = threading.Thread(target=generate_in_thread)
                thread.daemon = True
                thread.start()
            except Exception as e:
                messagebox.showerror("错误", f"生成NC代码时出错: {str(e)}")
                self.status_var.set("就绪")
    
    def generate_nc_from_description_only(self):
        """从仅描述生成NC代码的备选方法"""
        try:
            from src.modules.unified_generator import unified_generator  # 导入全局实例
            
            # 使用统一生成器的描述分析功能
            nc_code = unified_generator.generate_from_description_only(
                self.description.get(),
                self.material.get()
            )
            
            self.current_nc_code = nc_code
            self.display_nc_code(nc_code)
            self.update_report()
            self.status_var.set("NC代码生成完成（仅描述模式）")
        except Exception as e:
            messagebox.showerror("错误", f"从描述生成NC代码失败: {str(e)}")
            self.status_var.set("就绪")
    
    def display_nc_code(self, nc_code):
        """显示NC代码"""
        self.nc_text.delete(1.0, tk.END)
        self.nc_text.insert(1.0, nc_code)
    
    def update_report(self):
        """更新分析报告"""
        report = self.nc_helper.get_analysis_report()
        report_text = f"分析报告:\n\n"
        report_text += f"识别特征数量: {report['features_count']}\n"
        report_text += f"工艺过程数量: {report['processes_count']}\n"
        report_text += f"NC代码行数: {report['nc_code_length']}\n\n"
        report_text += "特征统计:\n"
        for feature_type, count in report['features'].items():
            report_text += f"  {feature_type}: {count}\n"
        
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report_text)
    
    def validate_nc(self):
        """验证NC代码"""
        if not self.current_nc_code:
            messagebox.showwarning("警告", "请先生成NC代码")
            return
        
        errors = self.nc_helper.validate_output()
        if errors:
            error_text = "NC代码验证发现以下错误:\n\n" + "\n".join([f"• {error}" for error in errors])
            messagebox.showwarning("验证结果", error_text)
        else:
            messagebox.showinfo("验证结果", "NC代码验证通过，无明显错误")
    
    def export_nc(self):
        """导出NC代码"""
        if not self.current_nc_code:
            messagebox.showwarning("警告", "请先生成NC代码")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存NC代码",
            defaultextension=".nc",
            filetypes=[("NC文件", "*.nc"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                # 根据文件扩展名选择导出格式
                _, ext = os.path.splitext(file_path)
                if ext.lower() == '.nc' or ext.lower() == '.txt':
                    export_code = self.nc_helper.cam_interface.export_to_generic(self.current_nc_code)
                elif 'cambam' in file_path.lower():
                    export_code = self.nc_helper.cam_interface.export_to_cambam(self.current_nc_code)
                elif 'mastercam' in file_path.lower():
                    export_code = self.nc_helper.cam_interface.export_to_mastercam(self.current_nc_code)
                elif 'fusion' in file_path.lower():
                    export_code = self.nc_helper.cam_interface.export_to_fusion360(self.current_nc_code)
                else:
                    export_code = self.current_nc_code
                
                # 确保导出代码使用UTF-8编码处理中文字符
                if isinstance(export_code, str):
                    # 如果是字符串，直接使用UTF-8写入
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(export_code)
                else:
                    # 如果是字节串，先解码再写入
                    try:
                        export_code_str = export_code.decode('utf-8')
                    except UnicodeError:
                        export_code_str = export_code.decode('utf-8', errors='replace')
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(export_code_str)
                messagebox.showinfo("成功", f"NC代码已保存到: {file_path}")
            except UnicodeError as e:
                # 如果出现编码错误，尝试其他处理方法
                try:
                    # 以二进制模式写入
                    with open(file_path, 'wb') as f:
                        if isinstance(export_code, str):
                            f.write(export_code.encode('utf-8'))
                        else:
                            f.write(export_code)
                    messagebox.showinfo("成功", f"NC代码已保存到: {file_path} (使用二进制模式)")
                except Exception as binary_error:
                    messagebox.showerror("错误", f"保存文件时出错: {str(binary_error)}")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件时出错: {str(e)}")
    
    def on_canvas_click(self, event):
        """画布点击事件处理"""
        # 这里可以添加点击画布来选择特征的功能
        pass
    
    def on_feature_select(self, event):
        """特征列表选择事件处理"""
        # 这里可以添加选择特征后高亮显示在画布上的功能
        pass
    
    def on_canvas_scroll(self, event):
        """画布滚动事件处理（缩放）"""
        # 检测是否按住了Ctrl键进行缩放
        if event.state & 0x4:  # Ctrl键
            if event.delta > 0 or event.num == 4:  # 向上滚动或Linux的Button-4
                self.zoom_in()
            elif event.delta < 0 or event.num == 5:  # 向下滚动或Linux的Button-5
                self.zoom_out()
        else:
            # 普通滚动（上下平移）
            if event.delta > 0 or event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.delta < 0 or event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def on_canvas_drag_start(self, event):
        """开始拖拽"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def on_canvas_drag(self, event):
        """拖拽事件处理（平移）"""
        # 计算拖拽距离
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        
        # 更新画布偏移量
        self.canvas_offset_x += dx
        self.canvas_offset_y += dy
        
        # 移动画布上的所有项目
        self.canvas.move(tk.ALL, dx, dy)
        
        # 更新起始位置
        self.drag_start_x = event.x
        self.drag_start_y = event.y

    def zoom_in(self, event=None):
        """放大图像"""
        self.canvas_scale *= 1.2
        self.redraw_canvas_image()

    def zoom_out(self, event=None):
        """缩小图像"""
        self.canvas_scale /= 1.2
        if self.canvas_scale < 0.1:  # 最小缩放限制
            self.canvas_scale = 0.1
        self.redraw_canvas_image()

    def rotate_image(self, event=None):
        """旋转图像90度"""
        self.canvas_rotation = (self.canvas_rotation + 90) % 360
        self.redraw_canvas_image()

    def redraw_canvas_image(self):
        """重新绘制画布图像"""
        if self.current_image is not None:
            self.display_cv_image()
        elif hasattr(self, 'current_pil_image') and self.current_pil_image is not None:
            self.display_pil_image()
        elif self.only_description_mode.get():
            self.create_virtual_image()
            self.display_cv_image()
    
    def display_cv_image(self):
        """在画布上显示OpenCV图像"""
        if self.current_image is not None:
            try:
                # 转换BGR到RGB
                image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                # 调整图像大小以适应画布
                height, width = image_rgb.shape[:2]
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                if canvas_width <= 1: canvas_width = 400
                if canvas_height <= 1: canvas_height = 300
                
                # 应用用户缩放比例
                new_width = int(width * self.canvas_scale)
                new_height = int(height * self.canvas_scale)
                
                # 调整图像大小
                resized_image = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
                
                # 如果需要旋转，则旋转图像
                if self.canvas_rotation != 0:
                    center = (new_width // 2, new_height // 2)
                    rotation_matrix = cv2.getRotationMatrix2D(center, self.canvas_rotation, 1.0)
                    resized_image = cv2.warpAffine(resized_image, rotation_matrix, (new_width, new_height))
                    # 更新宽高以适应旋转后的尺寸
                    height, width = resized_image.shape[:2]
                
                # 转换为Tkinter可用的格式
                from PIL import Image, ImageTk
                pil_image = Image.fromarray(resized_image)
                self.photo = ImageTk.PhotoImage(pil_image)
                
                # 清除画布并绘制图像
                self.canvas.delete("all")
                # 居中显示，考虑缩放和平移
                x = (canvas_width - new_width) // 2 + self.canvas_offset_x
                y = (canvas_height - new_height) // 2 + self.canvas_offset_y
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            except Exception as e:
                print(f"显示图像时出错: {e}")
    
    def show_welcome_message(self):
        """显示欢迎信息"""
        self.canvas.delete("all")
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1: canvas_width = 400
        if canvas_height <= 1: canvas_height = 300
        
        x = canvas_width // 2
        y = canvas_height // 2
        
        self.canvas.create_text(x, y-20, text="AI辅助NC编程工具", font=("Arial", 14, "bold"), fill="gray")
        self.canvas.create_text(x, y+10, text="请导入图纸文件", font=("Arial", 10), fill="gray")
        self.canvas.create_text(x, y+30, text="支持PDF、PNG、JPG等格式", font=("Arial", 8), fill="gray")


def run_gui():
    """运行GUI界面"""
    root = tk.Tk()
    app = SimpleNC_GUI(root)
    root.mainloop()


# 如果直接运行此文件，则启动GUI
if __name__ == "__main__":
    run_gui()