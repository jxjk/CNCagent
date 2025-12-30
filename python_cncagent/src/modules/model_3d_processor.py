"""
3D模型处理器
处理STL、STEP等3D模型格式，提取几何特征用于CNC加工
"""
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# 尝试导入可能需要的库
# 针对Python 3.14不支持open3d的情况，优先使用trimesh作为主要3D处理库
try:
    import numpy as np
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False
    logging.warning("警告: 未安装open3d库，将使用trimesh作为主要3D处理库")

try:
    import trimesh
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False
    logging.warning("警告: 未安装trimesh库，3D模型处理功能将受限")

from src.exceptions import CNCError, InputValidationError


class Model3DProcessor:
    """
    3D模型处理器
    支持多种3D模型格式，提取几何特征用于CNC加工
    """
    
    SUPPORTED_FORMATS = {'.stl', '.step', '.stp', '.igs', '.iges', '.obj', '.ply', '.off', '.gltf', '.glb'}
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def load_model(self, model_path: str) -> Any:
        """
        加载3D模型
        
        Args:
            model_path: 3D模型文件路径
            
        Returns:
            加载的模型对象
            
        Raises:
            InputValidationError: 模型文件格式不支持或文件不存在
        """
        path = Path(model_path)
        
        if not path.exists():
            raise InputValidationError(f"3D模型文件不存在: {model_path}")
        
        file_ext = path.suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise InputValidationError(f"不支持的3D模型格式: {file_ext}. 支持的格式: {', '.join(self.SUPPORTED_FORMATS)}")
        
        try:
            # 优先使用trimesh，因为它对Python 3.14有更好的支持
            if HAS_TRIMESH:
                # 使用trimesh加载模型（支持更多格式）
                mesh = trimesh.load(str(path))
                return mesh
            elif HAS_OPEN3D:
                # 仅在没有trimesh时使用Open3D
                if file_ext in ['.stl', '.ply', '.obj']:
                    mesh = o3d.io.read_triangle_mesh(str(path))
                    if mesh.is_empty():
                        raise CNCError(f"无法加载模型: {model_path}")
                    return mesh
                elif file_ext in ['.step', '.stp', '.igs', '.iges']:
                    # 对于STEP/IGES格式，由于Open3D支持有限，提示用户安装trimesh
                    raise CNCError(f"Open3D对{file_ext}格式支持有限，建议安装trimesh库来处理此类格式")
            else:
                raise CNCError("需要安装trimesh库来处理3D模型（推荐）或open3d库")
        except Exception as e:
            # 如果主要方法失败，尝试其他方法
            if file_ext in ['.step', '.stp', '.igs', '.iges'] and not HAS_TRIMESH:
                raise CNCError(f"需要安装trimesh库来处理{file_ext}格式文件")
            else:
                raise CNCError(f"加载3D模型失败: {str(e)}")
    
    def extract_geometric_features(self, model: Any) -> Dict[str, Any]:
        """
        从3D模型中提取几何特征
        
        Args:
            model: 3D模型对象
            
        Returns:
            几何特征字典
        """
        features = {
            'vertices_count': 0,
            'faces_count': 0,
            'volume': 0.0,
            'surface_area': 0.0,
            'bounding_box': None,
            'geometric_primitives': [],
            'holes': [],
            'pockets': [],
            'slots': [],
            'cylindrical_surfaces': [],
            'planar_surfaces': [],
            'dimensions': {}
        }
        
        # 优先使用trimesh进行处理，因为它对Python 3.14有更好的支持
        if HAS_TRIMESH and hasattr(model, 'vertices'):
            # 使用trimesh处理
            features['vertices_count'] = len(model.vertices)
            features['faces_count'] = len(model.faces)
            
            # 计算边界框
            bounds = model.bounds
            if bounds is not None and bounds.shape == (2, 3):
                features['bounding_box'] = {
                    'min': bounds[0].tolist(),
                    'max': bounds[1].tolist(),
                    'size': (bounds[1] - bounds[0]).tolist()
                }
            
            # 计算表面积和体积
            features['surface_area'] = model.area
            if hasattr(model, 'volume') and model.is_volume:
                try:
                    features['volume'] = model.volume
                except:
                    # 某些模型可能无法计算体积
                    features['volume'] = 0.0
            
            # 检测几何基元
            geometric_primitives = self._detect_geometric_primitives_trimesh(model)
            features['geometric_primitives'] = geometric_primitives
            
            # 检测孔、槽等特征
            features['holes'] = self._detect_holes_trimesh(model)
            features['slots'] = self._detect_slots_trimesh(model)
            
            # 检测更多高级特征
            features['cylindrical_surfaces'] = self._detect_cylindrical_surfaces_trimesh(model)
            features['planar_surfaces'] = self._detect_planar_surfaces_trimesh(model)
            
        elif HAS_OPEN3D and isinstance(model, o3d.geometry.TriangleMesh):
            # 如果没有trimesh但有Open3D，则使用Open3D
            vertices = np.asarray(model.vertices)
            triangles = np.asarray(model.triangles)
            
            features['vertices_count'] = len(vertices)
            features['faces_count'] = len(triangles)
            
            # 计算边界框
            if len(vertices) > 0:
                min_bound = vertices.min(axis=0)
                max_bound = vertices.max(axis=0)
                features['bounding_box'] = {
                    'min': min_bound.tolist(),
                    'max': max_bound.tolist(),
                    'size': (max_bound - min_bound).tolist()
                }
            
            # 计算表面积和体积（仅对封闭网格）
            if hasattr(model, 'is_watertight') and model.is_watertight():
                try:
                    features['surface_area'] = model.get_surface_area()
                except:
                    # 如果无法计算，使用替代方法
                    features['surface_area'] = 0.0
                try:
                    features['volume'] = model.get_volume()
                except:
                    features['volume'] = 0.0
            
            # 检测几何基元（如圆柱、球体等）
            geometric_primitives = self._detect_geometric_primitives_o3d(model)
            features['geometric_primitives'] = geometric_primitives
            
        return features
    
    def _detect_geometric_primitives_o3d(self, mesh) -> List[Dict[str, Any]]:
        """使用Open3D检测几何基元"""
        if not HAS_OPEN3D:
            return []
        
        primitives = []
        
        # 检测平面
        try:
            plane_model, inliers = mesh.segment_plane(distance_threshold=0.01,
                                                      ransac_n=3,
                                                      num_iterations=1000)
            if len(inliers) > 0:
                primitives.append({
                    'type': 'plane',
                    'inliers_count': len(inliers),
                    'equation': plane_model.tolist() if hasattr(plane_model, 'tolist') else plane_model
                })
        except:
            pass  # 如果检测失败，跳过
        
        return primitives
    
    def _detect_cylindrical_surfaces_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测圆柱面"""
        if not HAS_TRIMESH:
            return []
        
        cylindrical_surfaces = []
        
        try:
            # trimesh没有直接的圆柱检测功能，但我们可以通过分析网格的几何特性
            # 来近似检测圆柱面
            if hasattr(mesh, 'principal_inertia_vectors') and hasattr(mesh, 'volume'):
                # 使用惯性张量来检测可能的圆柱形状
                if mesh.volume > 0:
                    # 通过分析边界框和体积比来检测圆柱
                    extents = mesh.extents
                    if extents is not None and len(extents) >= 3:
                        # 检查是否两个维度近似相等（圆形截面），而第三个维度不同（长度）
                        sorted_extents = sorted(extents)
                        if (abs(sorted_extents[0] - sorted_extents[1]) < 0.1 * max(sorted_extents[0], 0.001) 
                            and sorted_extents[2] > 1.5 * sorted_extents[1]):
                            # 可能是圆柱：两个维度近似相等，第三个维度更大
                            cylindrical_surfaces.append({
                                'type': 'cylinder_approximation',
                                'diameter': sorted_extents[0],
                                'length': sorted_extents[2],
                                'orientation': 'vertical' if sorted_extents[2] == extents[2] else 'horizontal'
                            })
        except:
            pass
        
        return cylindrical_surfaces
    
    def _detect_planar_surfaces_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测平面面"""
        if not HAS_TRIMESH:
            return []
        
        planar_surfaces = []
        
        try:
            # 通过检查网格是否近似为平面状来检测平面
            extents = mesh.extents
            if extents is not None and len(extents) >= 3:
                # 如果一个维度相对于其他维度非常小，则可能是平面
                min_extent = min(extents) if extents is not None else 0
                max_extent = max(extents) if extents is not None else 1
                
                if min_extent > 0 and max_extent > 0 and max_extent / min_extent > 50:
                    # 一个维度远小于其他维度，可能是薄板
                    thickness_idx = extents.tolist().index(min_extent)
                    planar_surfaces.append({
                        'type': 'planar_surface',
                        'thickness': min_extent,
                        'area': (extents[0] * extents[1] if thickness_idx == 2 
                                else extents[0] * extents[2] if thickness_idx == 1 
                                else extents[1] * extents[2]),
                        'orientation': ['x', 'y', 'z'][thickness_idx]
                    })
        except:
            pass
        
        return planar_surfaces
    
    def _detect_geometric_primitives_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测几何基元"""
        if not HAS_TRIMESH:
            return []
        
        primitives = []
        
        # 检测球体近似
        try:
            extents = mesh.extents
            if extents is not None and len(extents) >= 3:
                # 检查各维度是否近似相等
                ratios = sorted(extents / min(extents + [0.0001]))  # 避免除零
                if len(ratios) >= 3 and all(0.8 < r < 1.2 for r in ratios[:3]):
                    primitives.append({
                        'type': 'sphere_approximation',
                        'diameter': max(extents),
                        'extents': extents.tolist() if hasattr(extents, 'tolist') else extents.tolist() if isinstance(extents, np.ndarray) else extents,
                        'center_mass': mesh.center_mass.tolist() if hasattr(mesh.center_mass, 'tolist') else mesh.center_mass.tolist() if isinstance(mesh.center_mass, np.ndarray) else mesh.center_mass
                    })
        except:
            pass
        
        # 检测立方体近似
        try:
            extents = mesh.extents
            if extents is not None and len(extents) >= 3:
                # 检查是否近似为立方体
                ratios = sorted(extents / min(extents + [0.0001]))  # 避免除零
                if all(0.8 < r < 1.5 for r in ratios):
                    primitives.append({
                        'type': 'cube_approximation',
                        'extents': extents.tolist() if hasattr(extents, 'tolist') else extents.tolist() if isinstance(extents, np.ndarray) else extents,
                        'center_mass': mesh.center_mass.tolist() if hasattr(mesh.center_mass, 'tolist') else mesh.center_mass.tolist() if isinstance(mesh.center_mass, np.ndarray) else mesh.center_mass
                    })
        except:
            pass
        
        return primitives
    
    def _detect_holes_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测孔"""
        if not HAS_TRIMESH:
            return []
        
        holes = []
        
        try:
            # 检查是否是开放网格（有孔）
            if not mesh.is_watertight:
                # 获取边界的详细信息
                boundary_entities = mesh.face_adjacency_edges[mesh.face_adjacency_angles > np.pi - 1e-6]
                if len(boundary_entities) > 0:
                    holes.append({
                        'boundary_edges_count': len(boundary_entities),
                        'is_open_mesh': not mesh.is_watertight,
                        'boundary_loops': len(mesh.face_adjacency_angles[mesh.face_adjacency_angles > np.pi - 1e-6])
                    })
        except:
            pass
        
        return holes
    
    def _detect_slots_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测槽"""
        if not HAS_TRIMESH:
            return []
        
        slots = []
        
        # 槽检测：通过分析网格的几何特征来推断槽的存在
        try:
            extents = mesh.extents if hasattr(mesh, 'extents') else None
            if extents is not None and len(extents) >= 3:
                # 如果某一个维度相对于其他维度很小，则可能是槽
                min_extent = min(extents) if extents is not None else 0.001
                max_extent = max(extents) if extents is not None else 1
                
                # 检查是否有一个维度明显小于其他维度（可能表示槽或孔）
                if min_extent > 0 and max_extent > 0 and max_extent / min_extent > 10:
                    # 计算各轴方向的尺寸比例
                    x_ratio = extents[0] / min_extent if min_extent > 0 else 0
                    y_ratio = extents[1] / min_extent if min_extent > 0 else 0
                    z_ratio = extents[2] / min_extent if min_extent > 0 else 0
                    
                    # 确定最小维度的方向
                    min_axis = ['x', 'y', 'z'][np.argmin(extents)]
                    
                    slots.append({
                        'type': 'slot_approximation',
                        'extents': extents.tolist() if hasattr(extents, 'tolist') else extents.tolist() if isinstance(extents, np.ndarray) else extents,
                        'aspect_ratio': max_extent / min_extent,
                        'orientation': min_axis,
                        'description': f'Slot oriented along {min_axis} axis with high aspect ratio ({max_extent / min_extent:.2f})'
                    })
        except:
            pass
        
        return slots
    
    def convert_to_2d_features(self, geometric_features: Dict[str, Any]) -> List[Dict]:
        """
        将3D几何特征转换为2D特征格式，以便与现有系统兼容
        
        Args:
            geometric_features: 3D几何特征
            
        Returns:
            2D特征列表，格式与feature_definition模块兼容
        """
        features_2d = []
        
        # 从边界框信息创建近似的2D特征
        bounding_box = geometric_features.get('bounding_box')
        if bounding_box:
            size = bounding_box['size']
            center = [(a + b) / 2 for a, b in zip(bounding_box['min'], bounding_box['max'])]
            
            # 根据边界框大小创建近似的矩形或圆形特征
            if abs(size[0] - size[1]) < 0.1 * max(size[0], size[1]):
                # 近似为圆形
                radius = min(size[0], size[1]) / 2
                features_2d.append({
                    "shape": "circle",
                    "center": (center[0], center[1]),
                    "dimensions": (size[0], size[1]),
                    "area": 3.14159 * radius * radius,
                    "confidence": 0.7,
                    "radius": radius
                })
            else:
                # 创建矩形
                features_2d.append({
                    "shape": "rectangle",
                    "center": (center[0], center[1]),
                    "dimensions": (size[0], size[1]),
                    "area": size[0] * size[1],
                    "confidence": 0.7
                })
        
        # 处理检测到的几何基元
        for primitive in geometric_features.get('geometric_primitives', []):
            if primitive['type'] == 'cylinder':
                # 将圆柱体转换为圆形特征
                features_2d.append({
                    "shape": "circle",
                    "center": (primitive.get('center', [0, 0, 0])[0], 
                              primitive.get('center', [0, 0, 0])[1]),
                    "dimensions": (primitive.get('diameter', 10), primitive.get('diameter', 10)),
                    "area": 3.14159 * (primitive.get('diameter', 10) / 2) ** 2,
                    "confidence": 0.8,
                    "radius": primitive.get('diameter', 10) / 2
                })
            elif primitive['type'] == 'plane':
                # 将平面转换为矩形特征
                features_2d.append({
                    "shape": "rectangle",
                    "center": (primitive.get('center', [0, 0, 0])[0], 
                              primitive.get('center', [0, 0, 0])[1]),
                    "dimensions": (primitive.get('width', 10), primitive.get('height', 10)),
                    "area": primitive.get('width', 10) * primitive.get('height', 10),
                    "confidence": 0.6
                })
        
        # 处理孔特征
        for hole in geometric_features.get('holes', []):
            features_2d.append({
                "shape": "circle",
                "center": (0, 0),  # 默认中心点，实际应用中需要计算
                "dimensions": (10, 10),  # 默认尺寸，实际应用中需要计算
                "area": 78.54,  # 默认面积
                "confidence": 0.5,
                "is_hole": True
            })
        
        return features_2d
    
    def process_3d_model(self, model_path: str) -> Dict[str, Any]:
        """
        处理3D模型的完整流程
        
        Args:
            model_path: 3D模型文件路径
            
        Returns:
            包含几何特征和其他信息的字典
        """
        self.logger.info(f"开始处理3D模型: {model_path}")
        
        # 加载模型
        model = self.load_model(model_path)
        
        # 提取几何特征
        geometric_features = self.extract_geometric_features(model)
        
        # 转换为2D特征格式
        features_2d = self.convert_to_2d_features(geometric_features)
        
        result = {
            'model_path': model_path,
            'geometric_features': geometric_features,
            'features_2d': features_2d,
            'format': Path(model_path).suffix.lower(),
            'processing_successful': True
        }
        
        self.logger.info(f"3D模型处理完成: {model_path}")
        return result


# 创建全局实例
model_3d_processor = Model3DProcessor()


def process_3d_model(model_path: str) -> Dict[str, Any]:
    """
    处理3D模型的便捷函数
    
    Args:
        model_path: 3D模型文件路径
        
    Returns:
        包含几何特征和其他信息的字典
    """
    return model_3d_processor.process_3d_model(model_path)