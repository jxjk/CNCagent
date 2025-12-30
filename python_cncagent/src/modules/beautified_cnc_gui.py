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
    
    def setup_left_panel(self, parent):
        """设置左侧输入面板"""
        # 文件上传区域
        file_frame = ttk.LabelFrame(parent, text="文件上传", padding=5)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 2D图纸上传
        ttk.Button(file_frame, text="上传2D图纸", command=self.load_2d_drawing).pack(fill=tk.X, pady=2)
        
        # 3D模型上传
        ttk.Button(file_frame, text="上传3D模型", command=self.load_3d_model).pack(fill=tk.X, pady=2)
        
        # 图纸预览
        preview_frame = ttk.LabelFrame(parent, text="图纸预览", padding=5)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 预览画布
        self.preview_canvas = tk.Canvas(preview_frame, bg='white', width=350, height=200)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
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
        
        # 生成按钮
        ttk.Button(
            parent,
            text="🚀 生成NC程序",
            command=self.generate_nc,
            style='Accent.TButton'
        ).pack(fill=tk.X, pady=(10, 0))
    
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
            except Exception as e:
                messagebox.showerror("错误", f"处理3D模型时出错: {str(e)}")
    
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
    
    def display_pil_image(self):
        """在画布上显示PIL图像"""
        if hasattr(self, 'current_pil_image') and self.current_pil_image is not None:
            try:
                # 转换PIL图像为Tkinter可用的格式
                pil_image = self.current_pil_image
                # 调整图像大小以适应画布
                canvas_width = 350  # 固定画布宽度
                canvas_height = 200  # 固定画布高度
                
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
                self.preview_canvas.delete("all")
                x = (canvas_width - new_width) // 2
                y = (canvas_height - new_height) // 2
                self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            except Exception as e:
                print(f"显示PIL图像时出错: {e}")
    
    def display_cv_image(self):
        """在画布上显示OpenCV图像"""
        if self.current_image is not None:
            try:
                # 如果是numpy数组，转换BGR到RGB
                if isinstance(self.current_image, np.ndarray):
                    image_rgb = cv2.cvtColor(self.current_image, cv2.COLOR_BGR2RGB)
                    # 调整图像大小以适应画布
                    height, width = image_rgb.shape[:2]
                    canvas_width = 350  # 固定画布宽度
                    canvas_height = 200  # 固定画布高度
                
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
                    self.preview_canvas.delete("all")
                    x = (canvas_width - new_width) // 2
                    y = (canvas_height - new_height) // 2
                    self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
                else:
                    # 如果是PIL图像，直接调整大小
                    pil_image = self.current_image
                    # 调整图像大小以适应画布
                    canvas_width = 350  # 固定画布宽度
                    canvas_height = 200  # 固定画布高度
                
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
                    self.preview_canvas.delete("all")
                    x = (canvas_width - new_width) // 2
                    y = (canvas_height - new_height) // 2
                    self.preview_canvas.create_image(x, y, anchor=tk.NW, image=self.photo)
            except Exception as e:
                print(f"显示图像时出错: {e}")
    
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


def run_gui():
    """运行GUI界面"""
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.theme_use('clam')  # 使用更现代的主题
    
    # 配置按钮样式
    style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
    
    app = CNC_GUI(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()