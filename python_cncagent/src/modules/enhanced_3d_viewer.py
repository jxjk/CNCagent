"""
增强的3D查看器和AI分析器模块
提供交互式3D模型查看和AI驱动的CNC加工分析功能
"""
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import numpy as np
try:
    import open3d as o3d
    OPEN3D_AVAILABLE = True
except ImportError:
    OPEN3D_AVAILABLE = False
    print("警告: 未安装open3d库，3D查看功能将受限")

try:
    import trimesh
    TRIMESH_AVAILABLE = True
except ImportError:
    TRIMESH_AVAILABLE = False
    print("警告: 未安装trimesh库，部分3D功能将受限")


class Enhanced3DViewer:
    """
    增强的3D模型查看器
    提供交互式3D模型查看功能，包括旋转、缩放、平移等
    """
    
    def __init__(self, parent_window=None):
        self.parent_window = parent_window
        self.model_path = None
        self.mesh = None
        self.geometry = None
        
        if not OPEN3D_AVAILABLE:
            print("注意: open3d库不可用，将使用简化3D查看功能")
    
    def load_model(self, model_path):
        """
        加载3D模型
        
        Args:
            model_path: 3D模型文件路径
        """
        self.model_path = model_path
        
        if OPEN3D_AVAILABLE:
            try:
                # 尝试使用open3d加载模型
                file_ext = model_path.lower().split('.')[-1]
                
                if file_ext in ['.stl', '.obj', '.ply', '.off']:
                    self.mesh = o3d.io.read_triangle_mesh(model_path)
                    if not self.mesh.has_vertices():
                        raise Exception(f"无法从{model_path}读取有效的网格数据")
                    self.geometry = self.mesh
                elif file_ext in ['.step', '.stp', '.igs', '.iges']:
                    # 对于STEP/IGES格式，我们先尝试用trimesh加载然后转为open3d格式
                    if TRIMESH_AVAILABLE:
                        trimesh_mesh = trimesh.load(model_path)
                        vertices = np.array(trimesh_mesh.vertices)
                        triangles = np.array(trimesh_mesh.faces)
                        self.mesh = o3d.geometry.TriangleMesh(
                            o3d.utility.Vector3dVector(vertices),
                            o3d.utility.Vector3iVector(triangles)
                        )
                        self.geometry = self.mesh
                    else:
                        raise Exception(f"需要安装trimesh库来处理{file_ext}格式")
                else:
                    raise Exception(f"不支持的文件格式: {file_ext}")
                    
            except Exception as e:
                print(f"使用open3d加载模型失败: {str(e)}")
                self.geometry = None
        else:
            # 如果没有open3d，仍然记录模型路径
            self.geometry = None
    
    def create_interactive_window(self):
        """
        创建交互式3D查看窗口
        """
        if not OPEN3D_AVAILABLE:
            self._create_simple_3d_viewer()
            return
        
        if self.geometry is None:
            messagebox.showerror("错误", "无法加载3D模型或open3d不可用")
            return
        
        # 在新线程中启动open3d可视化器
        vis_thread = threading.Thread(target=self._run_open3d_visualizer, daemon=True)
        vis_thread.start()
    
    def _run_open3d_visualizer(self):
        """
        在新线程中运行open3d可视化器
        """
        try:
            vis = o3d.visualization.Visualizer()
            vis.create_window(window_name=f"3D模型查看器 - {self.model_path}", width=800, height=600)
            
            # 添加几何体到可视化器
            vis.add_geometry(self.geometry)
            
            # 设置渲染选项
            render_option = vis.get_render_option()
            render_option.mesh_show_back_face = True
            render_option.mesh_show_wireframe = False
            
            # 运行可视化器
            vis.run()
            vis.destroy_window()
        except Exception as e:
            print(f"运行open3d可视化器时出错: {str(e)}")
    
    def _create_simple_3d_viewer(self):
        """
        创建简化的3D查看器（当open3d不可用时）
        """
        viewer_window = tk.Toplevel(self.parent_window)
        viewer_window.title(f"3D模型查看器 - {self.model_path}")
        viewer_window.geometry("600x500")
        
        # 创建说明文本
        info_frame = ttk.Frame(viewer_window)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text="3D模型查看器", font=("Arial", 14, "bold")).pack()
        ttk.Label(info_frame, text="当前系统缺少open3d库，无法提供交互式3D查看", foreground="red").pack(pady=5)
        ttk.Label(info_frame, text="请运行: pip install open3d", font=("Courier", 10)).pack(pady=2)
        
        # 尝试显示模型的基本信息
        if TRIMESH_AVAILABLE:
            try:
                import trimesh
                mesh = trimesh.load(self.model_path)
                info_text = f"""
模型信息:
- 顶点数: {len(mesh.vertices)}
- 面数: {len(mesh.faces)}
- 体积: {mesh.volume if hasattr(mesh, 'volume') else 'N/A'}
- 表面积: {mesh.area if hasattr(mesh, 'area') else 'N/A'}
                """.strip()
                
                info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT)
                info_label.pack(pady=10)
            except Exception as e:
                ttk.Label(info_frame, text=f"读取模型信息失败: {str(e)}", foreground="red").pack(pady=5)
        else:
            ttk.Label(info_frame, text="安装trimesh库可显示模型详细信息", foreground="blue").pack(pady=5)


class AIEnhanced3DAnalyzer:
    """
    AI增强的3D模型分析器
    使用AI技术分析3D模型并提供CNC加工建议
    """
    
    def __init__(self):
        self.model_path = None
        self.model_data = None
        self.processing_features = []
        
    def analyze_model_for_cnc(self, model_path):
        """
        分析3D模型以提供CNC加工建议
        
        Args:
            model_path: 3D模型文件路径
            
        Returns:
            dict: 包含分析结果的字典
        """
        try:
            # 使用trimesh加载模型进行分析
            if not TRIMESH_AVAILABLE:
                return self._fallback_analysis(model_path)
            
            import trimesh
            mesh = trimesh.load(model_path)
            
            # 获取基本模型信息
            basic_info = {
                'vertices_count': len(mesh.vertices),
                'faces_count': len(mesh.faces),
                'volume': mesh.volume if hasattr(mesh, 'volume') and mesh.is_volume else 0,
                'surface_area': mesh.area,
                'bounds': mesh.bounds.tolist() if mesh.bounds is not None else None,
                'extents': mesh.extents.tolist() if mesh.extents is not None else None
            }
            
            # 分析几何特征
            geometric_analysis = self._analyze_geometric_features(mesh)
            
            # 识别CNC加工特征
            processing_features = self._identify_processing_features(mesh)
            
            # 生成CNC加工建议
            cnc_recommendations = self._generate_cnc_recommendations(mesh, processing_features)
            
            # 返回综合分析结果
            analysis_result = {
                'basic_info': basic_info,
                'geometric_analysis': geometric_analysis,
                'processing_features': processing_features,
                'cnc_recommendations': cnc_recommendations,
                'material_suggestions': self._suggest_materials(mesh),
                'tool_recommendations': self._recommend_tools(processing_features)
            }
            
            return analysis_result
            
        except Exception as e:
            print(f"AI分析3D模型时出错: {str(e)}")
            # 返回基本分析结果
            return self._fallback_analysis(model_path)
    
    def _analyze_geometric_features(self, mesh):
        """
        分析模型的几何特征
        
        Args:
            mesh: trimesh对象
            
        Returns:
            list: 几何特征列表
        """
        features = []
        
        # 分析边界框和尺寸
        if mesh.bounds is not None:
            min_bound, max_bound = mesh.bounds
            dimensions = max_bound - min_bound
            features.append({
                'type': 'bounding_box',
                'dimensions': dimensions.tolist(),
                'min_bound': min_bound.tolist(),
                'max_bound': max_bound.tolist()
            })
        
        # 检测平面
        try:
            plane_origins, plane_normals, plane_eq = mesh.face_adjacency_unshared
            # 计算平面数量（近似）
            planar_regions = len(np.unique(plane_eq, axis=0)) if len(plane_eq) > 0 else 0
            features.append({
                'type': 'planar_regions',
                'count': planar_regions
            })
        except:
            pass
        
        # 检测孔和凹陷
        if hasattr(mesh, 'faces') and len(mesh.faces) > 0:
            # 通过检查边界边来检测孔
            boundary_edges = mesh.edges[mesh.edges_unique_inverse[mesh.edges_face_count == 1]]
            hole_count = len(boundary_edges) // 2 if len(boundary_edges) > 0 else 0
            features.append({
                'type': 'potential_holes',
                'count': hole_count
            })
        
        return features
    
    def _identify_processing_features(self, mesh):
        """
        识别适合CNC加工的特征
        
        Args:
            mesh: trimesh对象
            
        Returns:
            list: 加工特征列表
        """
        features = []
        
        # 分析边界框以确定主要加工面
        if mesh.bounds is not None:
            min_bound, max_bound = mesh.bounds
            dimensions = max_bound - min_bound
            
            # 确定Z方向的加工深度
            z_depth = dimensions[2]
            if z_depth > 0.1:  # 假设最小加工深度为0.1mm
                features.append({
                    'type': 'z_depth_processing',
                    'depth': z_depth,
                    'dimensions': dimensions.tolist(),
                    'volume': mesh.volume if hasattr(mesh, 'volume') and mesh.is_volume else 0
                })
        
        # 分析表面特征
        surface_area = mesh.area
        if surface_area > 10:  # 仅对较大表面进行分析
            features.append({
                'type': 'surface_processing',
                'surface_area': surface_area,
                'recommended_tool': 'end_mill'
            })
        
        # 分析孔特征（如果检测到边界边）
        try:
            # 检查是否有圆柱形特征
            if len(mesh.vertices) > 100:  # 确保有足够的顶点
                # 使用顶点分布来估计可能的孔或圆柱特征
                vertex_variance = np.var(mesh.vertices, axis=0)
                if np.min(vertex_variance) < 0.1:  # 检测线性特征
                    features.append({
                        'type': 'linear_feature',
                        'variance': vertex_variance.tolist()
                    })
        except:
            pass
        
        return features
    
    def _generate_cnc_recommendations(self, mesh, processing_features):
        """
        生成CNC加工建议
        
        Args:
            mesh: trimesh对象
            processing_features: 加工特征列表
            
        Returns:
            list: CNC加工建议列表
        """
        recommendations = []
        
        # 基于模型尺寸的建议
        if mesh.bounds is not None:
            min_bound, max_bound = mesh.bounds
            dimensions = max_bound - min_bound
            
            if max(dimensions) > 100:
                recommendations.append("模型较大，建议分区域加工以提高效率")
            elif max(dimensions) < 10:
                recommendations.append("模型较小，注意刀具选择避免过切")
        
        # 基于加工特征的建议
        for feature in processing_features:
            if feature['type'] == 'z_depth_processing':
                depth = feature['depth']
                if depth > 20:
                    recommendations.append(f"加工深度较大({depth:.2f}mm)，建议分层铣削")
                elif depth < 1:
                    recommendations.append(f"加工深度较浅({depth:.2f}mm)，可考虑一次性加工")
        
        # 基于表面面积的建议
        surface_area = mesh.area
        if surface_area > 1000:  # 假设单位是平方毫米
            recommendations.append("表面积较大，建议优化刀具路径以提高效率")
        elif surface_area < 100:
            recommendations.append("表面积较小，注意细节加工精度")
        
        # 安全建议
        recommendations.append("加工前请进行仿真验证，确保刀具路径安全")
        recommendations.append("建议使用适当的切削参数，避免过载")
        
        return recommendations
    
    def _suggest_materials(self, mesh):
        """
        基于模型特征建议材料
        
        Args:
            mesh: trimesh对象
            
        Returns:
            list: 材料建议列表
        """
        suggestions = []
        
        # 基于模型尺寸建议材料
        if mesh.bounds is not None:
            dimensions = mesh.extents if hasattr(mesh, 'extents') else (mesh.bounds[1] - mesh.bounds[0])
            volume = mesh.volume if hasattr(mesh, 'volume') and mesh.is_volume else 0
            
            if volume > 10000:  # 体积大于10000mm³
                suggestions.extend(["Aluminum", "Plastic", "Composite"])
            elif volume > 1000:
                suggestions.extend(["Aluminum", "Brass", "Plastic"])
            else:
                suggestions.extend(["Aluminum", "Brass", "Stainless Steel"])
        
        return suggestions
    
    def _recommend_tools(self, processing_features):
        """
        基于加工特征推荐刀具
        
        Args:
            processing_features: 加工特征列表
            
        Returns:
            list: 刀具推荐列表
        """
        recommendations = []
        
        for feature in processing_features:
            if feature['type'] == 'z_depth_processing':
                depth = feature['depth']
                if depth > 10:
                    recommendations.append("粗铣刀 → 精铣刀 (分层加工)")
                else:
                    recommendations.append("直接使用精铣刀")
            elif feature['type'] == 'surface_processing':
                recommendations.append("端铣刀进行表面加工")
        
        if not recommendations:
            recommendations.append("根据具体特征选择合适刀具")
        
        return recommendations
    
    def _fallback_analysis(self, model_path):
        """
        降级分析方法（当缺少必要库时）
        
        Args:
            model_path: 模型路径
            
        Returns:
            dict: 基本分析结果
        """
        return {
            'basic_info': {
                'vertices_count': 'N/A',
                'faces_count': 'N/A', 
                'volume': 'N/A',
                'surface_area': 'N/A'
            },
            'geometric_analysis': [{'type': 'not_available', 'message': '需要安装trimesh库进行详细分析'}],
            'processing_features': [],
            'cnc_recommendations': [
                'AI分析功能受限，建议安装trimesh库',
                '请运行: pip install trimesh',
                '加工前请仔细检查模型和加工参数'
            ],
            'material_suggestions': ['Aluminum (推荐)'],
            'tool_recommendations': ['通用端铣刀']
        }


# 简单的测试函数
def test_3d_viewer():
    """
    测试3D查看器功能
    """
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    viewer = Enhanced3DViewer(root)
    analyzer = AIEnhanced3DAnalyzer()
    
    print("3D查看器测试完成")
    print(f"Open3D可用: {OPEN3D_AVAILABLE}")
    print(f"Trimesh可用: {TRIMESH_AVAILABLE}")


if __name__ == "__main__":
    test_3d_viewer()