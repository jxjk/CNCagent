"""
优化的CNC Agent GUI界面
以大模型为技术框架，支持2D图纸、3D图纸、描述词输入和NC程序输出
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import cv2
import numpy as np
import os
from src.modules.ai_nc_helper import AI_NC_Helper
import threading
from PIL import Image, ImageTk


class OptimizedCNC_GUI:
    """
    优化的NC编程工具用户界面
    以大模型为技术框架，支持2D图纸、3D图纸、描述词输入和NC程序输出
    """
    def __init__(self, root):
        self.root = root
        self.root.title("CNC Agent - AI驱动的智能NC编程平台")
        self.root.geometry("1200x800")
        self.nc_helper = AI_NC_Helper()
        self.current_image = None
        self.current_image_path = None
        self.current_nc_code = ""
        self.material = tk.StringVar(value="Aluminum")
        self.processing_type = tk.StringVar(value="general")
        self.description = tk.StringVar(value="")
        self.only_description_mode = tk.BooleanVar(value=False)
        self.ai_powered_mode = tk.BooleanVar(value=True)  # 新增：AI优先模式
        self.file_types = [
            ("2D图纸文件", "*.pdf *.png *.jpg *.jpeg *.bmp *.tiff"),
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
        main_frame.rowconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=3)
        main_frame.rowconfigure(3, weight=2)
        
        # 顶部标题
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        title_label = ttk.Label(title_frame, text="CNC Agent - AI驱动的智能NC编程平台", font=("TkDefaultFont", 14, "bold"))
        title_label.pack()
        
        # 顶部控制栏
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 核心功能按钮
        ttk.Button(control_frame, text="📁 导入图纸", command=self.load_drawing).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="🔍 识别特征", command=self.detect_features).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="⚡ 生成NC", command=self.generate_nc).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="💾 导出代码", command=self.export_nc).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="✅ 验证代码", command=self.validate_nc).pack(side=tk.LEFT, padx=(0, 5))
        
        # AI优先模式复选框
        ai_mode_check = ttk.Checkbutton(control_frame, text="🤖 AI优先模式", variable=self.ai_powered_mode)
        ai_mode_check.pack(side=tk.LEFT, padx=(20, 5))
        
        # 仅描述模式复选框
        description_mode_check = ttk.Checkbutton(control_frame, text="📝 仅描述模式", variable=self.only_description_mode, command=self.toggle_description_mode)
        description_mode_check.pack(side=tk.LEFT, padx=(5, 10))
        
        # 材料选择
        ttk.Label(control_frame, text="材料:").pack(side=tk.LEFT, padx=(10, 5))
        material_combo = ttk.Combobox(control_frame, textvariable=self.material, 
                                    values=["Aluminum", "Steel", "Stainless Steel", "Brass", "Plastic", "Cast Iron", "Titanium", "Other"], 
                                    state="readonly")
        material_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        # 主内容区域
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # 左侧：输入区域
        input_frame = ttk.LabelFrame(content_frame, text="📥 输入信息", padding="10")
        input_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(2, weight=1)
        
        # 2D/3D图纸预览
        ttk.Label(input_frame, text="图纸预览:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.canvas = tk.Canvas(input_frame, bg='white', width=400, height=250)
        self.canvas.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        
        # 识别特征列表
        ttk.Label(input_frame, text="识别特征列表:").grid(row=2, column=0, sticky=tk.W, pady=(0, 5))
        self.feature_frame = ttk.Frame(input_frame)
        self.feature_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.feature_frame.columnconfigure(0, weight=1)
        self.feature_frame.rowconfigure(0, weight=1)
        
        self.feature_listbox = tk.Listbox(self.feature_frame)
        feature_scrollbar = ttk.Scrollbar(self.feature_frame, orient=tk.VERTICAL, command=self.feature_listbox.yview)
        self.feature_listbox.configure(yscrollcommand=feature_scrollbar.set)
        
        self.feature_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        feature_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.feature_listbox.bind("<<ListboxSelect>>", self.on_feature_select)
        
        # 右侧：参数和描述区域
        param_frame = ttk.LabelFrame(content_frame, text="⚙️ 参数配置", padding="10")
        param_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(5, 0))
        param_frame.columnconfigure(0, weight=1)
        param_frame.rowconfigure(1, weight=1)
        
        # 加工描述输入
        ttk.Label(param_frame, text="加工描述:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.desc_text = scrolledtext.ScrolledText(param_frame, wrap=tk.WORD, width=50, height=8)
        self.desc_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 高级参数
        advanced_frame = ttk.LabelFrame(param_frame, text="🔬 高级参数", padding="5")
        advanced_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        advanced_frame.columnconfigure(1, weight=1)
        
        ttk.Label(advanced_frame, text="比例:").grid(row=0, column=0, sticky=tk.W)
        self.scale_var = tk.DoubleVar(value=1.0)
        scale_entry = ttk.Entry(advanced_frame, textvariable=self.scale_var, width=10)
        scale_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 0))
        
        ttk.Label(advanced_frame, text="精度:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.precision_var = tk.StringVar(value="General")
        precision_combo = ttk.Combobox(advanced_frame, textvariable=self.precision_var,
                                      values=["General", "High", "Ultra"], state="readonly", width=8)
        precision_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 0), pady=(5, 0))
        
        # 输出区域
        output_frame = ttk.LabelFrame(main_frame, text="📤 输出结果", padding="10")
        output_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)
        
        # NC代码显示区域
        self.nc_text = scrolledtext.ScrolledText(output_frame, wrap=tk.NONE, width=60, height=10)
        nc_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.nc_text.yview)
        self.nc_text.configure(yscrollcommand=nc_scrollbar.set)
        
        self.nc_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        nc_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # 分析报告区域
        report_frame = ttk.Frame(output_frame)
        report_frame.grid(row=0, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        report_frame.columnconfigure(0, weight=1)
        report_frame.rowconfigure(0, weight=1)
        
        ttk.Label(report_frame, text="📊 AI分析报告:").grid(row=0, column=0, sticky=tk.W)
        self.report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, width=30, height=10)
        report_scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_text.yview)
        self.report_text.configure(yscrollcommand=report_scrollbar.set)
        
        self.report_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        report_scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪 - AI模型已加载，准备处理任务")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
    def toggle_description_mode(self):
        """切换仅描述模式"""
        if self.only_description_mode.get():
            self.status_var.set("已切换到仅描述模式 - 无需导入图纸，AI将基于描述生成代码")
            # 在仅描述模式下，自动创建虚拟图像
            self.create_virtual_image()
            # 更新画布以显示虚拟图像
            self.display_cv_image()
        else:
            self.status_var.set("已切换到正常模式 - 请导入图纸")
            # 重置当前图像
            self.current_image = None
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
        cv2.putText(virtual_image, "AI分析中", (350, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(virtual_image, "仅描述模式", (330, 500), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        self.current_image = virtual_image
        self.current_image_path = None  # 表示这是虚拟图像
    
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
                        
                        # 创建虚拟2D图像用于显示
                        self.create_virtual_image_from_3d(model_data)
                        self.display_cv_image()
                        self.status_var.set(f"✅ 已加载3D模型: {os.path.basename(file_path)} - {model_data['geometric_features'].get('vertices_count', '未知')}顶点")
                    except Exception as e:
                        messagebox.showerror("❌ 错误", f"处理3D模型时出错: {str(e)}")
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
                        self.status_var.set(f"✅ 已加载PDF: {os.path.basename(file_path)} (第1页)")
                    else:
                        messagebox.showerror("❌ 错误", "无法从PDF中提取图像")
                else:
                    # 处理图像文件
                    self.current_image = cv2.imread(file_path)
                    if self.current_image is not None:
                        self.display_cv_image()
                        self.status_var.set(f"✅ 已加载: {os.path.basename(file_path)}")
                    else:
                        messagebox.showerror("❌ 错误", "无法读取图像文件")
            except Exception as e:
                messagebox.showerror("❌ 错误", f"加载文件时出错: {str(e)}")
    
    def display_pil_image(self):
        """在画布上显示PIL图像"""
        if hasattr(self, 'current_pil_image') and self.current_pil_image is not None:
            try:
                # 转换PIL图像为Tkinter可用的格式
                pil_image = self.current_pil_image
                # 调整图像大小以适应画布
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                
                if canvas_width <= 1: canvas_width = 400
                if canvas_height <= 1: canvas_height = 300
                
                # 计算缩放比例，保持宽高比
                img_width, img_height = pil_image.size
                scale_x = canvas_width / img_width
                scale_y = canvas_height / img_height
                scale = min(scale_x, scale_y, 1.0)  # 不放大图像
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # 调整图像大小
                resized_image = pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                self.photo = ImageTk.PhotoImage(resized_image)
                
                # 清除画布并绘制图像
                self.canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            except Exception as e:
                print(f"显示PIL图像时出错: {e}")
    
    def detect_features(self):
        """检测图纸中的特征"""
        # 检查是否处于仅描述模式
        if self.only_description_mode.get():
            self.status_var.set("仅描述模式：跳过特征检测，直接使用描述信息")
            # 仅描述模式不需要检测特征，直接使用描述信息
            messagebox.showinfo("💡 提示", "当前为仅描述模式，已跳过特征检测步骤。\n请直接点击'生成NC'按钮。")
            return
        
        if self.current_image is None:
            messagebox.showwarning("⚠️ 警告", "请先加载图纸")
            return
        
        self.status_var.set("🔍 正在检测特征...")
        self.root.update()
        
        try:
            # 从用户描述中获取额外信息
            drawing_text = self.desc_text.get("1.0", tk.END).strip()
            features_data = self.nc_helper.feature_detector.detect_features(self.current_image, drawing_text)
            
            # 更新特征列表
            self.feature_listbox.delete(0, tk.END)
            for i, feature in enumerate(features_data["all_features"]):
                shape = feature.get("shape", "unknown")
                center = feature.get("center", (0, 0))
                self.feature_listbox.insert(tk.END, f"{i+1}. {shape.upper()} at ({center[0]:.1f}, {center[1]:.1f}) - 置信度: {feature.get('confidence', 0):.2f}")
            
            self.status_var.set(f"✅ 特征检测完成: {len(features_data['all_features'])} 个特征")
        except Exception as e:
            messagebox.showerror("❌ 错误", f"特征检测时出错: {str(e)}")
            self.status_var.set("就绪")
    
    def generate_nc(self):
        """生成NC代码"""
        # 检查是否在仅描述模式下，且没有描述
        if self.only_description_mode.get():
            user_description = self.desc_text.get("1.0", tk.END).strip()
            if not user_description:
                messagebox.showwarning("⚠️ 警告", "请在仅描述模式下输入加工描述")
                return
        else:
            user_description = self.desc_text.get("1.0", tk.END).strip()
            if not user_description:
                messagebox.showwarning("⚠️ 警告", "请输入加工描述")
                return
        
        # 在仅描述模式下，不应使用图像，直接从描述生成NC代码
        if self.only_description_mode.get():
            self.generate_nc_from_description_only()
        elif self.current_image is None and not hasattr(self, 'current_3d_model_path'):
            messagebox.showwarning("⚠️ 警告", "请先加载图纸或3D模型并检测特征")
            return
        else:
            self.status_var.set("🤖 AI正在分析并生成NC代码...")
            self.root.update()
            
            try:
                # 从用户描述中获取额外信息
                material = self.material.get()
                user_description = self.desc_text.get("1.0", tk.END).strip()
                scale = self.scale_var.get()
                
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
                        
                        # 从环境变量获取API配置
                        api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
                        model_name = os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'deepseek-chat'))
                        
                        nc_code = generate_cnc_with_unified_approach(
                            user_prompt=user_description,
                            pdf_path=pdf_path,  # 可能为None
                            model_3d_path=model_3d_path,  # 可能为None
                            api_key=api_key,
                            model=model_name
                        )
                        
                        self.current_nc_code = nc_code
                        self.root.after(0, self.display_nc_code, nc_code)
                        self.root.after(0, self.update_report)
                        self.root.after(0, lambda: self.status_var.set("✅ NC代码生成完成 - AI驱动"))
                    except Exception as e:
                        self.root.after(0, lambda: messagebox.showerror("❌ 错误", f"生成NC代码时出错: {str(e)}"))
                        self.root.after(0, lambda: self.status_var.set("就绪"))
                
                thread = threading.Thread(target=generate_in_thread)
                thread.daemon = True
                thread.start()
            except Exception as e:
                messagebox.showerror("❌ 错误", f"生成NC代码时出错: {str(e)}")
                self.status_var.set("就绪")
    
    def generate_nc_from_description_only(self):
        """从仅描述生成NC代码"""
        try:
            user_description = self.desc_text.get("1.0", tk.END).strip()
            material = self.material.get()
            
            from src.modules.unified_generator import generate_cnc_with_unified_approach
            import os
            
            # 从环境变量获取API配置
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
            model_name = os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'deepseek-chat'))
            
            # 使用统一生成器，仅使用描述
            nc_code = generate_cnc_with_unified_approach(
                user_prompt=user_description,
                pdf_path=None,  # 无图纸
                model_3d_path=None,  # 无3D模型
                api_key=api_key,
                model=model_name
            )
            
            self.current_nc_code = nc_code
            self.display_nc_code(nc_code)
            self.update_report()
            self.status_var.set("✅ NC代码生成完成（AI仅描述模式）")
        except Exception as e:
            messagebox.showerror("❌ 错误", f"从描述生成NC代码失败: {str(e)}")
            self.status_var.set("就绪")
    
    def display_nc_code(self, nc_code):
        """显示NC代码"""
        self.nc_text.delete(1.0, tk.END)
        self.nc_text.insert(1.0, nc_code)
    
    def update_report(self):
        """更新分析报告"""
        # 显示AI分析结果
        report_text = f"🤖 AI分析报告:\n\n"
        report_text += f"输入信息:\n"
        report_text += f"- 处理模式: {'仅描述模式' if self.only_description_mode.get() else '图纸模式'}\n"
        report_text += f"- AI优先: {'是' if self.ai_powered_mode.get() else '否'}\n"
        report_text += f"- 材料类型: {self.material.get()}\n"
        report_text += f"- 比例尺: {self.scale_var.get()}\n\n"
        
        report_text += f"输出信息:\n"
        report_text += f"- NC代码行数: {len(self.current_nc_code.split(chr(10))) if self.current_nc_code else 0}\n"
        report_text += f"- 代码大小: {len(self.current_nc_code) if self.current_nc_code else 0} 字符\n\n"
        
        report_text += f"💡 处理说明:\n"
        report_text += f"- 本系统使用大语言模型进行智能分析\n"
        report_text += f"- 结合图纸特征和用户描述生成最优加工路径\n"
        report_text += f"- AI自动优化切削参数和刀具路径\n\n"
        
        report_text += f"⚠️ 注意事项:\n"
        report_text += f"- AI存在幻觉，生成的NC需要人工复核\n"
        report_text += f"- 建议在实际加工前进行仿真验证\n"
        report_text += f"- 检查刀具路径和切削参数的合理性\n"
        
        self.report_text.delete(1.0, tk.END)
        self.report_text.insert(1.0, report_text)
    
    def validate_nc(self):
        """验证NC代码"""
        if not self.current_nc_code:
            messagebox.showwarning("⚠️ 警告", "请先生成NC代码")
            return
        
        errors = self.nc_helper.validate_output()
        if errors:
            error_text = "NC代码验证发现以下错误:\n\n" + "\n".join([f"• {error}" for error in errors])
            messagebox.showwarning("❌ 验证结果", error_text)
        else:
            messagebox.showinfo("✅ 验证结果", "NC代码验证通过，无明显错误")
    
    def export_nc(self):
        """导出NC代码"""
        if not self.current_nc_code:
            messagebox.showwarning("⚠️ 警告", "请先生成NC代码")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存NC代码",
            defaultextension=".nc",
            filetypes=[("NC文件", "*.nc"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if file_path:
            try:
                # 确保导出代码使用UTF-8编码处理中文字符
                if isinstance(self.current_nc_code, str):
                    # 如果是字符串，直接使用UTF-8写入
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(self.current_nc_code)
                else:
                    # 如果是字节串，先解码再写入
                    try:
                        code_str = self.current_nc_code.decode('utf-8')
                    except UnicodeError:
                        code_str = self.current_nc_code.decode('utf-8', errors='replace')
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(code_str)
                messagebox.showinfo("✅ 成功", f"NC代码已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("❌ 错误", f"保存文件时出错: {str(e)}")
    
    def on_canvas_click(self, event):
        """画布点击事件处理"""
        pass
    
    def on_feature_select(self, event):
        """特征列表选择事件处理"""
        pass
    
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
                
                # 计算缩放比例
                scale_x = canvas_width / width
                scale_y = canvas_height / height
                scale = min(scale_x, scale_y, 1.0)  # 不放大图像
                new_width = int(width * scale)
                new_height = int(height * scale)
                
                # 调整图像大小
                resized_image = cv2.resize(image_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
                
                # 转换为Tkinter可用的格式
                from PIL import Image, ImageTk
                pil_image = Image.fromarray(resized_image)
                self.photo = ImageTk.PhotoImage(pil_image)
                
                # 清除画布并绘制图像
                self.canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
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
        
        self.canvas.create_text(x, y-40, text="CNC Agent", font=("Arial", 16, "bold"), fill="gray")
        self.canvas.create_text(x, y-20, text="AI驱动的智能NC编程平台", font=("Arial", 12), fill="gray")
        self.canvas.create_text(x, y, text="请导入图纸文件", font=("Arial", 10), fill="gray")
        self.canvas.create_text(x, y+20, text="支持PDF、PNG、JPG、STL等格式", font=("Arial", 8), fill="gray")
        self.canvas.create_text(x, y+40, text="🤖 AI优先处理", font=("Arial", 8), fill="blue")


def run_optimized_gui():
    """运行优化的GUI界面"""
    root = tk.Tk()
    app = OptimizedCNC_GUI(root)
    root.mainloop()


# 如果直接运行此文件，则启动GUI
if __name__ == "__main__":
    run_optimized_gui()
