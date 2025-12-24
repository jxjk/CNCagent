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
        self.description = tk.StringVar(value="")
        self.file_types = [
            ("图像文件", "*.png *.jpg *.jpeg *.bmp *.tiff"),
            ("PDF文件", "*.pdf"),
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
        
        # 材料选择
        ttk.Label(control_frame, text="材料:").pack(side=tk.LEFT, padx=(20, 5))
        material_combo = ttk.Combobox(control_frame, textvariable=self.material, values=["Aluminum", "Steel", "Stainless Steel", "Brass", "Plastic"], state="readonly")
        material_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # 用户描述输入
        ttk.Label(control_frame, text="描述:").pack(side=tk.LEFT, padx=(0, 5))
        desc_entry = ttk.Entry(control_frame, textvariable=self.description, width=30)
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
        
        # 右侧NC代码预览区域
        nc_frame = ttk.Frame(main_frame)
        nc_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        nc_frame.rowconfigure(0, weight=1)
        nc_frame.columnconfigure(0, weight=1)
        
        self.nc_text = scrolledtext.ScrolledText(nc_frame, wrap=tk.NONE, width=60, height=15)
        self.nc_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 分析报告区域
        report_frame = ttk.Frame(main_frame)
        report_frame.grid(row=3, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        report_frame.rowconfigure(0, weight=1)
        report_frame.columnconfigure(0, weight=1)
        
        ttk.Label(report_frame, text="分析报告:").grid(row=0, column=0, sticky=tk.W)
        self.report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, width=60, height=8)
        self.report_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
    
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
                if ext in ['.pdf']:
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
        if self.current_image is None:
            messagebox.showwarning("警告", "请先加载图纸并检测特征")
            return
        
        self.status_var.set("正在生成NC代码...")
        self.root.update()
        
        try:
            # 从用户描述中获取额外信息
            drawing_text = self.description.get()
            material = self.material.get()
            user_description = self.description.get()
            
            # 在后台线程中生成NC代码
            def generate_in_thread():
                try:
                    nc_code = self.nc_helper.quick_nc_generation(
                        self.current_image, 
                        drawing_text, 
                        material, 
                        user_description
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
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(export_code)
                messagebox.showinfo("成功", f"NC代码已保存到: {file_path}")
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