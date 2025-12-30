"""
几何推理引擎模块
专门处理复杂几何特征的推理和工艺规划
"""
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import numpy as np
import cv2
from scipy import ndimage


@dataclass
class Feature3D:
    """3D特征数据类"""
    shape_type: str  # 'rectangular_cavity', 'circular_cavity', 'slot', 'pocket'
    center: Tuple[float, float, float]
    dimensions: Tuple[float, float, float]  # (length, width, depth)
    corner_radius: Optional[float] = None
    bottom_radius: Optional[float] = None
    coordinate_system: str = "absolute"  # "absolute", "relative", "datum_based"
    processing_sides: List[str] = None  # ['top', 'bottom', 'side1', 'side2', ...]
    processing_sequence: List[int] = None  # 加工顺序


class GeometricReasoningEngine:
    """
    几何推理引擎
    专门处理复杂几何特征的推理和工艺规划
    """
    
    def __init__(self):
        self.logger = None  # 可以接入日志系统
        
    def analyze_cavity_features(self, image: np.ndarray) -> List[Feature3D]:
        """
        分析图像中的腔槽特征
        """
        features = []
        
        # 使用OpenCV进行边缘检测
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        edges = cv2.Canny(gray, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # 过滤小面积轮廓
            area = cv2.contourArea(contour)
            if area < 100:  # 面积阈值
                continue
                
            # 计算轮廓的边界框
            x, y, w, h = cv2.boundingRect(contour)
            center_x, center_y = x + w/2, y + h/2
            
            # 判断形状类型
            shape_type = self._identify_shape_type(contour, w, h)
            
            if shape_type in ['rectangular_cavity', 'circular_cavity', 'slot']:
                # 计算圆角半径
                corner_radius = self._estimate_corner_radius(contour, w, h)
                
                # 创建特征对象
                feature = Feature3D(
                    shape_type=shape_type,
                    center=(float(center_x), float(center_y), 0.0),  # Z坐标需要根据深度信息确定
                    dimensions=(float(w), float(h), 0.0),  # 深度需要根据Z信息确定
                    corner_radius=corner_radius
                )
                
                features.append(feature)
        
        return features
    
    def _identify_shape_type(self, contour, width, height) -> str:
        """
        识别轮廓的形状类型
        """
        # 计算轮廓的近似多边形
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 计算轮廓的圆形度
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return 'rectangular_cavity'
        
        circularity = 4 * math.pi * area / (perimeter * perimeter)
        
        # 判断形状
        if len(approx) == 4:
            # 检查是否为矩形或槽
            aspect_ratio = float(width) / height
            if 0.8 <= aspect_ratio <= 1.2:
                # 接近正方形，可能是圆形腔槽
                if circularity > 0.8:
                    return 'circular_cavity'
                else:
                    return 'rectangular_cavity'
            else:
                # 长宽比大，可能是槽
                return 'slot'
        elif circularity > 0.8:
            return 'circular_cavity'
        else:
            return 'rectangular_cavity'
    
    def _estimate_corner_radius(self, contour, width, height) -> Optional[float]:
        """
        估算圆角半径
        """
        # 计算轮廓的凸包
        hull = cv2.convexHull(contour)
        
        # 计算轮廓与凸包的差异来估算圆角
        hull_area = cv2.contourArea(hull)
        contour_area = cv2.contourArea(contour)
        
        if hull_area > 0:
            # 圆角程度可以通过面积差异来估算
            corner_factor = (hull_area - contour_area) / hull_area
            # 简化估算：圆角半径约为宽度或高度的某个比例
            min_dim = min(width, height)
            estimated_radius = min_dim * 0.05 * corner_factor  # 简化估算
            return estimated_radius if estimated_radius > 0.1 else None
        return None
    
    def analyze_processing_structure(self, features: List[Feature3D]) -> Dict:
        """
        分析加工结构（单面/多面）
        """
        analysis = {
            'single_sided_features': [],
            'multi_sided_features': [],
            'processing_sequence': [],
            'clamping_suggestions': []
        }
        
        for feature in features:
            # 简化分析：根据Z坐标和深度判断加工面
            if feature.center[2] == 0 and feature.dimensions[2] > 0:
                # 从顶面加工，单面结构
                analysis['single_sided_features'].append(feature)
            else:
                # 可能需要多面加工
                analysis['multi_sided_features'].append(feature)
        
        # 推荐加工顺序
        analysis['processing_sequence'] = self._recommend_processing_sequence(features)
        
        # 夹紧建议
        analysis['clamping_suggestions'] = self._generate_clamping_suggestions(features)
        
        return analysis
    
    def _recommend_processing_sequence(self, features: List[Feature3D]) -> List[int]:
        """
        推荐加工顺序
        """
        # 简化规则：按深度排序，由浅到深
        feature_indices = list(range(len(features)))
        feature_indices.sort(key=lambda i: features[i].dimensions[2])  # 按深度排序
        return feature_indices
    
    def _generate_clamping_suggestions(self, features: List[Feature3D]) -> List[str]:
        """
        生成夹紧建议
        """
        suggestions = []
        
        # 检查是否需要多面加工
        has_deep_features = any(f.dimensions[2] > 20 for f in features)  # 深度大于20mm
        
        if has_deep_features:
            suggestions.append("对于深腔槽，考虑使用特殊夹具或分多面加工")
        
        # 检查特征分布
        if len(features) > 5:
            suggestions.append("特征数量较多，考虑分步加工或使用专用工装")
        
        return suggestions if suggestions else ["标准夹紧方式即可"]
    
    def generate_coordinate_system_description(self, features: List[Feature3D]) -> str:
        """
        生成坐标系统描述
        """
        descriptions = []
        
        for i, feature in enumerate(features):
            if feature.coordinate_system == "datum_based":
                descriptions.append(
                    f"特征{i+1}: 以腔槽中心({feature.center[0]:.2f}, {feature.center[1]:.2f})为原点，"
                    f"尺寸({feature.dimensions[0]:.2f}x{feature.dimensions[1]:.2f})，"
                    f"深度{feature.dimensions[2]:.2f}mm"
                )
            elif feature.coordinate_system == "relative":
                descriptions.append(
                    f"特征{i+1}: 相对于基准点偏移({feature.center[0]:.2f}, {feature.center[1]:.2f})，"
                    f"尺寸({feature.dimensions[0]:.2f}x{feature.dimensions[1]:.2f})，"
                    f"深度{feature.dimensions[2]:.2f}mm"
                )
            else:  # absolute
                descriptions.append(
                    f"特征{i+1}: 绝对坐标({feature.center[0]:.2f}, {feature.center[1]:.2f})，"
                    f"尺寸({feature.dimensions[0]:.2f}x{feature.dimensions[1]:.2f})，"
                    f"深度{feature.dimensions[2]:.2f}mm"
                )
        
        return "\n".join(descriptions)


# 全局实例
geometric_reasoning_engine = GeometricReasoningEngine()
