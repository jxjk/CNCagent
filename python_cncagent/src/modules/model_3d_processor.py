"""
3D模型处理器
处理STL、STEP等3D模型格式，提取几何特征用于CNC加工
"""
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

# 尝试导入可能需要的库
try:
    import numpy as np
    import open3d as o3d
    HAS_OPEN3D = True
except ImportError:
    HAS_OPEN3D = False
    import logging
    logging.warning("警告: 未安装open3d库，3D模型处理功能将受限")

try:
    import trimesh
    HAS_TRIMESH = True
except ImportError:
    HAS_TRIMESH = False
    import logging
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
            if HAS_OPEN3D:
                # 使用Open3D加载模型
                if file_ext in ['.stl', '.ply', '.obj']:
                    mesh = o3d.io.read_triangle_mesh(str(path))
                    if mesh.is_empty():
                        raise CNCError(f"无法加载模型: {model_path}")
                    return mesh
                elif file_ext in ['.step', '.stp', '.igs', '.iges']:
                    # 对于STEP/IGES格式，需要转换为中间格式或使用专门的CAD库
                    # 这里我们先使用trimesh尝试加载
                    if HAS_TRIMESH:
                        mesh = trimesh.load(str(path))
                        return mesh
                    else:
                        raise CNCError(f"需要安装trimesh库来处理{file_ext}格式文件")
            elif HAS_TRIMESH:
                # 使用trimesh作为备选
                mesh = trimesh.load(str(path))
                return mesh
            else:
                raise CNCError("需要安装open3d或trimesh库来处理3D模型")
        except Exception as e:
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
        
        if HAS_OPEN3D and isinstance(model, o3d.geometry.TriangleMesh):
            # 使用Open3D处理三角网格
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
            if model.is_watertight():
                features['surface_area'] = model.get_surface_area()
                features['volume'] = model.get_volume()
            
            # 检测几何基元（如圆柱、球体等）
            geometric_primitives = self._detect_geometric_primitives_o3d(model)
            features['geometric_primitives'] = geometric_primitives
            
        elif HAS_TRIMESH and hasattr(model, 'vertices'):
            # 使用trimesh处理
            features['vertices_count'] = len(model.vertices)
            features['faces_count'] = len(model.faces)
            
            # 计算边界框
            bounds = model.bounds
            if bounds is not None:
                features['bounding_box'] = {
                    'min': bounds[0].tolist(),
                    'max': bounds[1].tolist(),
                    'size': (bounds[1] - bounds[0]).tolist()
                }
            
            # 计算表面积和体积
            features['surface_area'] = model.area
            if hasattr(model, 'volume'):
                features['volume'] = model.volume
            
            # 检测几何基元
            geometric_primitives = self._detect_geometric_primitives_trimesh(model)
            features['geometric_primitives'] = geometric_primitives
            
            # 检测孔、槽等特征
            features['holes'] = self._detect_holes_trimesh(model)
            features['slots'] = self._detect_slots_trimesh(model)
            
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
    
    def _detect_geometric_primitives_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测几何基元"""
        if not HAS_TRIMESH:
            return []
        
        primitives = []
        
        # trimesh提供了一些内置的几何检测功能
        if hasattr(mesh, 'bounding_box'):
            # 检测是否近似为立方体
            extents = mesh.extents
            if extents is not None:
                # 检查各维度比例，判断是否为近似立方体
                ratios = sorted(extents / min(extents)) if min(extents) > 0 else [1, 1, 1]
                if all(0.8 < r < 1.2 for r in ratios):
                    primitives.append({
                        'type': 'cube_approximation',
                        'extents': extents.tolist() if hasattr(extents, 'tolist') else extents,
                        'center_mass': mesh.center_mass.tolist() if hasattr(mesh.center_mass, 'tolist') else mesh.center_mass
                    })
        
        return primitives
    
    def _detect_holes_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测孔"""
        if not HAS_TRIMESH:
            return []
        
        holes = []
        
        try:
            # 检查是否是开放网格（有孔）
            if not mesh.is_watertight:
                # 获取边界边
                boundaries = mesh.face_adjacency_edges[mesh.face_adjacency_angles > np.pi - 1e-6]
                if len(boundaries) > 0:
                    holes.append({
                        'boundary_edges_count': len(boundaries),
                        'is_open_mesh': not mesh.is_watertight
                    })
        except:
            pass
        
        return holes
    
    def _detect_slots_trimesh(self, mesh) -> List[Dict[str, Any]]:
        """使用trimesh检测槽"""
        if not HAS_TRIMESH:
            return []
        
        slots = []
        
        # 槽检测是复杂的，这里只做简单检测
        # 通过分析网格的几何特征来推断槽的存在
        extents = mesh.extents if hasattr(mesh, 'extents') else None
        if extents is not None:
            # 如果某一个维度相对于其他维度很小，则可能是槽
            min_extent = min(extents) if extents is not None else 0
            max_extent = max(extents) if extents is not None else 1
            if min_extent > 0 and max_extent > 0 and max_extent / min_extent > 10:
                slots.append({
                    'type': 'slot_approximation',
                    'extents': extents.tolist() if hasattr(extents, 'tolist') else extents,
                    'aspect_ratio': max_extent / min_extent
                })
        
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