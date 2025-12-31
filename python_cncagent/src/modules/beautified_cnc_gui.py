"""
AI驱动的CNC编程工具 - 简洁美观版GUI界面
以大模型为技术框架，专注于核心功能，移除多余元素
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageTk
import cv2


class CNC_GUI:
    """
    AI驱动的CNC编程工具 - 简洁美观版界面
    专注于2D图纸、3D模型、描述词输入和NC程序输出
    """
    def __init__(self, root):
        self.root = root
        self.root.title("AI驱动CNC编程工具 - 简洁版")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")
        
        # 存储数据
        self.current_image = None
        self.current_image_path = None
        self.current_3d_model_path = None
        self.current_3d_model_data = None
        self.current_nc_code = ""
        
        # 变量
        self.material = tk.StringVar(value="Aluminum")
        self.description = tk.StringVar(value="")
        
        # 3D查看器相关
        self.enhanced_3d_viewer = None
        self.ai_3d_analyzer = None
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置用户界面"""
        # 主容器
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 标题
        title_label = tk.Label(
            main_container,
            text="AI驱动CNC编程工具",
            font=("Arial", 16, "bold"),
            fg="#2c3e50",
            bg="#f0f0f0"
        )
        title_label.pack(pady=(0, 10))
        
        # 创建左右分栏
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # 左侧输入区域
        left_frame = ttk.LabelFrame(content_frame, text="输入信息", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # 右侧输出区域
        right_frame = ttk.LabelFrame(content_frame, text="输出结果", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        # 左侧内容
        self.setup_left_panel(left_frame)
        
        # 右侧内容
        self.setup_right_panel(right_frame)
        
        # 初始化3D查看器和AI分析器
        try:
            from .enhanced_3d_viewer import Enhanced3DViewer, AIEnhanced3DAnalyzer
            self.enhanced_3d_viewer = Enhanced3DViewer(self.root)
            self.ai_3d_analyzer = AIEnhanced3DAnalyzer()
        except ImportError:
            print("警告: 无法导入增强3D查看器模块，3D高级功能将受限")
            self.enhanced_3d_viewer = None
            self.ai_3d_analyzer = None
    
    def setup_left_panel(self, parent):
        """设置左侧输入面板"""
        # 文件上传区域
        file_frame = ttk.LabelFrame(parent, text="文件上传", padding=5)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 2D图纸上传
        ttk.Button(file_frame, text="上传2D图纸", command=self.load_2d_drawing).pack(fill=tk.X, pady=2)
        
        # 3D模型上传
        ttk.Button(file_frame, text="上传3D模型", command=self.load_3d_model).pack(fill=tk.X, pady=2)
        
        # 3D模型查看（仅在加载3D模型后启用）
        self.view_3d_btn = ttk.Button(file_frame, text="查看3D模型", command=self.view_3d_model, state=tk.DISABLED)
        self.view_3d_btn.pack(fill=tk.X, pady=2)
        
        # AI增强分析按钮
        self.ai_analyze_3d_btn = ttk.Button(file_frame, text="AI分析3D模型", command=self.ai_analyze_3d_model, state=tk.DISABLED)
        self.ai_analyze_3d_btn.pack(fill=tk.X, pady=2)
        
        # 图纸预览
        preview_frame = ttk.LabelFrame(parent, text="图纸预览", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', width=350, height=200)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动事件支持 - 缩放功能
        self.preview_canvas.bind("<MouseWheel>", self.on_canvas_scroll)  # Windows
        self.preview_canvas.bind("<Button-4>", self.on_canvas_scroll)    # Linux
        self.preview_canvas.bind("<Button-5>", self.on_canvas_scroll)    # Linux
        
        # 添加拖拽支持 - 平移功能
        self.preview_canvas.bind("<ButtonPress-2>", self.on_canvas_drag_start)
        self.preview_canvas.bind("<B2-Motion>", self.on_canvas_drag)
        
        # 添加缩放和旋转支持
        self.preview_canvas.bind("<Control-KeyPress-plus>", self.zoom_in)
        self.preview_canvas.bind("<Control-KeyPress-minus>", self.zoom_out)
        self.preview_canvas.bind("<Control-KeyPress-equal>", self.zoom_in)  # Ctrl+= also zooms in
        self.preview_canvas.bind("<Control-KeyPress-r>", self.rotate_image)
        
        # 添加右键菜单支持
        self.preview_canvas.bind("<Button-3>", self.show_canvas_context_menu)
        
        # 初始化视图参数
        self.canvas_scale = 1.0
        self.canvas_rotation = 0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        
        # 特征点存储
        self.feature_points = []
        
        # 创建右键菜单
        self.canvas_context_menu = tk.Menu(self.preview_canvas, tearoff=0)
        self.canvas_context_menu.add_command(label="重置视图", command=self.reset_view)
        self.canvas_context_menu.add_command(label="显示特征点", command=self.toggle_feature_points)
        self.canvas_context_menu.add_separator()
        self.canvas_context_menu.add_command(label="放大 (Ctrl +)", command=self.zoom_in)
        self.canvas_context_menu.add_command(label="缩小 (Ctrl -)", command=self.zoom_out)
        self.canvas_context_menu.add_command(label="旋转 (Ctrl R)", command=self.rotate_image)
        
        # 材料选择
        material_frame = ttk.Frame(parent)
        material_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(material_frame, text="材料:").pack(side=tk.LEFT)
        material_combo = ttk.Combobox(
            material_frame,
            textvariable=self.material,
            values=["Aluminum", "Steel", "Stainless Steel", "Brass", "Plastic", "Cast Iron", "Titanium"],
            state="readonly"
        )
        material_combo.pack(side=tk.RIGHT)
        
        # 加工描述
        desc_frame = ttk.LabelFrame(parent, text="加工描述", padding=5)
        desc_frame.pack(fill=tk.BOTH, expand=True)
        
        self.desc_text = scrolledtext.ScrolledText(desc_frame, wrap=tk.WORD, height=6)
        self.desc_text.pack(fill=tk.BOTH, expand=True)
        
        # 控制按钮区域
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            control_frame,
            text="🔍 识别特征",
            command=self.detect_features
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        ttk.Button(
            control_frame,
            text="🚀 生成NC程序",
            command=self.generate_nc,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def setup_right_panel(self, parent):
        """设置右侧输出面板"""
        # NC代码显示
        nc_frame = ttk.LabelFrame(parent, text="NC程序", padding=5)
        nc_frame.pack(fill=tk.BOTH, expand=True)
        
        # NC代码文本区域
        self.nc_text = scrolledtext.ScrolledText(
            nc_frame,
            wrap=tk.NONE,
            font=("Consolas", 10)
        )
        self.nc_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        nc_scrollbar = ttk.Scrollbar(nc_frame, orient=tk.HORIZONTAL, command=self.nc_text.xview)
        nc_scrollbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.nc_text.configure(xscrollcommand=nc_scrollbar.set)
        
        # 下载按钮
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(button_frame, text="💾 保存代码", command=self.export_nc).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="📋 复制代码", command=self.copy_nc).pack(side=tk.LEFT)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪 - 等待输入")
        status_bar = ttk.Label(
            parent,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def load_2d_drawing(self):
        """加载2D图纸"""
        file_path = filedialog.askopenfilename(
            title="选择2D图纸文件",
            filetypes=[
                ("PDF文件", "*.pdf"),
                ("图像文件", "*.png *.jpg *.jpeg *.bmp *.tiff"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.current_image_path = file_path
            try:
                _, ext = os.path.splitext(file_path.lower())
                
                if ext == '.pdf':
                    # 处理PDF文件
                    from src.modules.pdf_parsing_process import pdf_to_images
                    images = pdf_to_images(file_path)
                    if images:
                        from PIL import Image
                        pil_image = images[0]  # 第一页的PIL图像
                        self.current_image = pil_image.convert('RGB')  # 转为RGB
                        self.current_pil_image = pil_image
                        self.display_pil_image()
                        self.status_var.set(f"已加载PDF: {os.path.basename(file_path)}")
                    else:
                        messagebox.showerror("错误", "无法从PDF中提取图像")
                else:
                    # 处理图像文件
                    from PIL import Image
                    pil_image = Image.open(file_path)
                    self.current_image = pil_image.convert('RGB')
                    self.display_pil_image()
                    self.status_var.set(f"已加载: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"加载文件时出错: {str(e)}")
    
    def load_3d_model(self):
        """加载3D模型"""
        file_path = filedialog.askopenfilename(
            title="选择3D模型文件",
            filetypes=[
                ("STL文件", "*.stl"),
                ("STEP文件", "*.step *.stp"),
                ("IGES文件", "*.igs *.iges"),
                ("OBJ文件", "*.obj"),
                ("PLY文件", "*.ply"),
                ("所有支持文件", "*.stl *.step *.stp *.igs *.iges *.obj *.ply")
            ]
        )
        
        if file_path:
            try:
                from src.modules.model_3d_processor import process_3d_model
                model_data = process_3d_model(file_path)
                
                self.current_3d_model_path = file_path
                self.current_3d_model_data = model_data
                
                # 创建虚拟2D图像用于显示
                self.create_virtual_image_from_3d(model_data)
                self.display_cv_image()
                
                vertices_count = model_data['geometric_features'].get('vertices_count', '未知')
                self.status_var.set(f"已加载3D模型: {os.path.basename(file_path)} - {vertices_count}顶点")
                
                # 启用3D查看和AI分析按钮
                if self.enhanced_3d_viewer:
                    self.view_3d_btn.config(state=tk.NORMAL)
                    self.ai_analyze_3d_btn.config(state=tk.NORMAL)
            except Exception as e:
                messagebox.showerror("错误", f"处理3D模型时出错: {str(e)}")
    
    def view_3d_model(self):
        """查看3D模型 - 调用增强的3D查看器"""
        if not self.current_3d_model_path:
            messagebox.showwarning("警告", "请先加载3D模型")
            return
            
        if not self.enhanced_3d_viewer:
            messagebox.showwarning("警告", "3D查看器不可用，请安装open3d库")
            return
            
        try:
            # 调用增强3D查看器
            self.enhanced_3d_viewer.load_model(self.current_3d_model_path)
            self.enhanced_3d_viewer.create_interactive_window()
        except Exception as e:
            messagebox.showerror("错误", f"启动3D查看器失败: {str(e)}")
    
    def ai_analyze_3d_model(self):
        """AI分析3D模型"""
        if not self.current_3d_model_path:
            messagebox.showwarning("警告", "请先加载3D模型")
            return
            
        if not self.ai_3d_analyzer:
            messagebox.showwarning("警告", "AI分析器不可用")
            return
            
        # 在新线程中执行AI分析，避免阻塞GUI
        def analyze_in_thread():
            try:
                analysis_result = self.ai_3d_analyzer.analyze_model_for_cnc(self.current_3d_model_path)
                
                if analysis_result:
                    # 在主线程中更新GUI
                    self.root.after(0, self.show_analysis_result, analysis_result)
                else:
                    self.root.after(0, lambda: messagebox.showerror("错误", "AI分析失败"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("错误", f"AI分析出错: {str(e)}"))
        
        analysis_thread = threading.Thread(target=analyze_in_thread, daemon=True)
        analysis_thread.start()
        self.status_var.set("AI正在分析3D模型...")
    
    def show_analysis_result(self, analysis_result):
        """显示AI分析结果"""
        # 创建新窗口显示分析结果
        result_window = tk.Toplevel(self.root)
        result_window.title("AI 3D模型分析结果")
        result_window.geometry("600x400")
        
        # 创建文本框显示结果
        text_frame = ttk.Frame(result_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # 格式化输出分析结果
        result_text = "AI 3D模型分析结果\n"
        result_text += "=" * 50 + "\n\n"
        
        # 基本信息
        basic_info = analysis_result.get('basic_info', {})
        result_text += "基本模型信息:\n"
        result_text += f"- 顶点数: {basic_info.get('vertices_count', 'N/A')}\n"
        result_text += f"- 面数: {basic_info.get('faces_count', 'N/A')}\n"
        result_text += f"- 体积: {basic_info.get('volume', 'N/A')}\n"
        result_text += f"- 表面积: {basic_info.get('surface_area', 'N/A')}\n\n"
        
        # 处理特征
        processing_features = analysis_result.get('processing_features', [])
        result_text += f"识别的加工特征: {len(processing_features)} 个\n"
        for i, feature in enumerate(processing_features, 1):
            result_text += f"{i}. {feature.get('type', 'Unknown')}: {feature.get('dimensions', {})}\n"
        result_text += "\n"
        
        # CNC建议
        recommendations = analysis_result.get('cnc_recommendations', [])
        result_text += f"CNC加工建议:\n"
        for rec in recommendations:
            result_text += f"- {rec}\n"
        result_text += "\n"
        
        # 几何分析（如果可用）
        if 'geometric_analysis' in analysis_result:
            result_text += "几何特征分析:\n"
            # 这里可以进一步格式化几何分析结果
            result_text += f"检测到 {len(analysis_result['geometric_analysis'])} 个几何特征\n\n"
        
        # 添加到文本框
        text_widget.insert(tk.END, result_text)
        text_widget.config(state=tk.DISABLED)  # 设置为只读
        
        # 更新状态
        self.status_var.set(f"AI分析完成: {len(analysis_result.get('processing_features', []))}个特征")
    
    def create_virtual_image_from_3d(self, model_data):
        """根据3D模型数据创建虚拟2D图像"""
        # 创建一个空白的虚拟图像
        width, height = 350, 200
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
        
        cv2.putText(virtual_image, f"3D模型预览", 
                   (20, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(virtual_image, f"顶点: {vertices_count}, 面: {faces_count}", 
                   (20, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        self.current_image = virtual_image
    

    
    def generate_nc(self):
        """生成NC代码"""
        description_text = self.desc_text.get(1.0, tk.END).strip()
        if not description_text and not self.current_image_path and not self.current_3d_model_path:
            messagebox.showwarning("警告", "请上传图纸或输入加工描述")
            return
        
        self.status_var.set("正在生成NC代码...")
        self.root.update()
        
        try:
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
                        user_prompt=description_text,
                        pdf_path=self.current_image_path,  # 可能为None
                        model_3d_path=self.current_3d_model_path,  # 可能为None
                        api_key=api_key,
                        model=model_name,
                        material=self.material.get()
                    )
                    
                    self.current_nc_code = nc_code
                    self.root.after(0, self.display_nc_code, nc_code)
                    self.root.after(0, lambda: self.status_var.set("NC代码生成完成"))
                except Exception as e:
                    self.root.after(0, lambda: messagebox.showerror("错误", f"生成NC代码时出错: {str(e)}"))
                    self.root.after(0, lambda: self.status_var.set("就绪"))
            
            thread = threading.Thread(target=generate_in_thread)
            thread.daemon = True
            thread.start()
        except Exception as e:
            messagebox.showerror("错误", f"启动生成线程时出错: {str(e)}")
            self.status_var.set("就绪")
    
    def display_nc_code(self, nc_code):
        """显示NC代码"""
        self.nc_text.delete(1.0, tk.END)
        self.nc_text.insert(1.0, nc_code)
    
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
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_nc_code)
                messagebox.showinfo("成功", f"NC代码已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存文件时出错: {str(e)}")
    
    def detect_features(self):
        """检测图纸中的特征"""
        if self.current_image is None and not hasattr(self, 'current_pil_image'):
            messagebox.showwarning("警告", "请先加载图纸")
            return
        
        self.status_var.set("正在检测特征...")
        self.root.update()
        
        try:
            # 使用AI_NC_Helper进行特征检测
            from src.modules.ai_nc_helper import AI_NC_Helper
            ai_helper = AI_NC_Helper()
            
            # 确定使用哪个图像进行特征检测
            image_for_detection = None
            original_size = None
            
            if hasattr(self, 'current_pil_image') and self.current_pil_image is not None:
                # 将PIL图像转换为numpy数组
                original_size = self.current_pil_image.size
                image_for_detection = np.array(self.current_pil_image.convert('L'))
            elif self.current_image is not None:
                if isinstance(self.current_image, np.ndarray):
                    # 如果是OpenCV图像，转换为灰度图
                    original_size = (self.current_image.shape[1], self.current_image.shape[0])  # width, height
                    if len(self.current_image.shape) == 3:
                        image_for_detection = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2GRAY)
                    else:
                        image_for_detection = self.current_image
                else:
                    # 如果是PIL图像，转换为numpy数组
                    original_size = self.current_image.size
                    image_for_detection = np.array(self.current_image.convert('L'))
            
            if image_for_detection is not None and original_size is not None:
                drawing_text = self.desc_text.get(1.0, tk.END).strip()
                features_data = ai_helper.feature_detector.detect_features(image_for_detection, drawing_text)
                
                # 保存检测到的特征点，用于后续显示
                self.feature_points = []
                for feature in features_data["all_features"]:
                    if 'center' in feature:
                        # 转换特征点坐标以适应当前显示比例和变换
                        orig_x, orig_y = feature['center']
                        # 考虑当前的缩放、旋转和平移
                        # 简化处理：按当前显示比例调整坐标
                        scaled_x = orig_x * self.canvas_scale
                        scaled_y = orig_y * self.canvas_scale
                        self.feature_points.append({
                            'x': scaled_x,
                            'y': scaled_y,
                            'shape': feature.get('shape', 'unknown'),
                            'confidence': feature.get('confidence', 1.0)
                        })
                
                # 显示检测结果
                feature_count = len(features_data["all_features"])
                self.status_var.set(f"特征检测完成: 检测到{feature_count}个特征")
                
                # 在状态栏显示详细信息
                if feature_count > 0:
                    shape_types = {}
                    for feature in features_data["all_features"]:
                        shape = feature.get("shape", "unknown")
                        shape_types[shape] = shape_types.get(shape, 0) + 1
                    
                    shapes_info = ", ".join([f"{shape}:{count}" for shape, count in shape_types.items()])
                    messagebox.showinfo("特征检测完成", f"检测到{feature_count}个特征:\n{shapes_info}")
                    
                    # 重新绘制图像以显示特征点
                    self.redraw_canvas_image()
                else:
                    messagebox.showinfo("特征检测完成", "未检测到明显特征")
            else:
                self.status_var.set("无法检测特征：图像格式不支持")
        except Exception as e:
            self.status_var.set("特征检测失败")
            messagebox.showerror("错误", f"特征检测时出错: {str(e)}")
    
    def copy_nc(self):
        """复制NC代码到剪贴板"""
        if not self.current_nc_code:
            messagebox.showwarning("警告", "请先生成NC代码")
            return
        
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_nc_code)
            messagebox.showinfo("成功", "NC代码已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制到剪贴板时出错: {str(e)}")

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
                self.preview_canvas.yview_scroll(-1, "units")
            elif event.delta < 0 or event.num == 5:
                self.preview_canvas.yview_scroll(1, "units")

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
        self.preview_canvas.move(tk.ALL, dx, dy)
        
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
            if isinstance(self.current_image, np.ndarray):
                self.display_cv_image()
            else:  # PIL Image
                self.display_pil_image()
        elif hasattr(self, 'current_pil_image') and self.current_pil_image is not None:
            self.display_pil_image()

    def display_pil_image(self):
        """在画布上显示PIL图像，支持缩放、旋转、平移"""
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
                self.preview_canvas.delete("all")
                x = (350 - new_width) // 2 + self.canvas_offset_x  # 固定画布宽度为350
                y = (200 - new_height) // 2 + self.canvas_offset_y  # 固定画布高度为200
                self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
                
                # 如果有特征点，绘制它们
                self.draw_feature_points()
            except Exception as e:
                print(f"显示PIL图像时出错: {e}")
    
    def display_cv_image(self):
        """在画布上显示OpenCV图像，支持缩放、旋转、平移"""
        if self.current_image is not None:
            try:
                # 如果是numpy数组，转换BGR到RGB
                if isinstance(self.current_image, np.ndarray):
                    image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                    # 应用用户缩放比例
                    height, width = image_rgb.shape[:2]
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
                    self.preview_canvas.delete("all")
                    x = (350 - new_width) // 2 + self.canvas_offset_x  # 固定画布宽度为350
                    y = (200 - new_height) // 2 + self.canvas_offset_y  # 固定画布高度为200
                    self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
                    
                    # 如果有特征点，绘制它们
                    self.draw_feature_points()
                else:
                    # 如果是PIL图像，直接调整大小
                    pil_image = self.current_image
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
                    self.preview_canvas.delete("all")
                    x = (350 - new_width) // 2 + self.canvas_offset_x  # 固定画布宽度为350
                    y = (200 - new_height) // 2 + self.canvas_offset_y  # 固定画布高度为200
                    self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
                    
                    # 如果有特征点，绘制它们
                    self.draw_feature_points()
            except Exception as e:
                print(f"显示图像时出错: {e}")

    def show_canvas_context_menu(self, event):
        """显示画布右键菜单"""
        try:
            self.canvas_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.canvas_context_menu.grab_release()

    def reset_view(self):
        """重置视图为初始状态"""
        self.canvas_scale = 1.0
        self.canvas_rotation = 0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        self.redraw_canvas_image()

    def toggle_feature_points(self):
        """切换特征点显示"""
        # 这里可以实现特征点的显示/隐藏切换
        # 临时显示一个提示信息
        messagebox.showinfo("功能提示", "特征点显示功能可与检测结果结合使用")

    def draw_feature_points(self):
        """在画布上绘制特征点"""
        if hasattr(self, 'feature_points') and self.feature_points:
            # 为每个特征点计算在当前视图中的位置
            for point in self.feature_points:
                # 获取原始图像尺寸
                if isinstance(self.current_image, np.ndarray):
                    orig_width = self.current_image.shape[1]
                    orig_height = self.current_image.shape[0]
                elif hasattr(self, 'current_pil_image') and self.current_pil_image is not None:
                    orig_width, orig_height = self.current_pil_image.size
                else:
                    continue  # 如果没有有效图像，跳过绘制
                
                # 计算缩放后图像在画布中的位置（居中）
                scaled_width = int(orig_width * self.canvas_scale)
                scaled_height = int(orig_height * self.canvas_scale)
                offset_x = (350 - scaled_width) // 2 + self.canvas_offset_x
                offset_y = (200 - scaled_height) // 2 + self.canvas_offset_y
                
                # 计算特征点在缩放后图像中的位置
                x = offset_x + point['x'] * self.canvas_scale  # 修正：使用原始坐标而不是已缩放的坐标
                y = offset_y + point['y'] * self.canvas_scale
                
                # 确保坐标在合理范围内
                if x < 350 and y < 200:  # 基本边界检查
                    # 根据特征类型使用不同颜色和形状
                    color = 'red'  # 默认颜色
                    if point['shape'] == 'circle':
                        color = 'red'
                    elif point['shape'] == 'rectangle':
                        color = 'blue'
                    elif point['shape'] == 'triangle':
                        color = 'green'
                    elif point['shape'] == 'line':
                        color = 'yellow'
                    
                    # 绘制圆形标记
                    self.preview_canvas.create_oval(
                        x - 4, y - 4, x + 4, y + 4,
                        fill=color, outline='white', width=1
                    )
                    
                    # 显示特征类型标签
                    self.preview_canvas.create_text(
                        x, y - 10, text=point['shape'][:4], fill=color, font=('Arial', 7, 'bold')
                    )


def run_gui():
    """运行GUI界面"""
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')  # 使用更现代的主题
    
    # 配置各种样式
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    style.configure('TLabelFrame', font=('Arial', 10, 'bold'))
    style.configure('TCombobox', padding=5)
    style.map('TButton', 
             foreground=[('pressed', 'blue'), ('active', 'red')],
             background=[('pressed', '!disabled', 'lightblue'), ('active', 'lightgray')])    
    app = CNC_GUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()