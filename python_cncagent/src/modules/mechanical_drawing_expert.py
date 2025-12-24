"""
机械制图专家模块
用于处理机械图纸的视图分析、尺寸公差提取等功能
"""
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class ViewType(Enum):
    """视图类型枚举"""
    TOP = "top"
    BOTTOM = "bottom"
    FRONT = "front"
    REAR = "rear"
    LEFT = "left"
    RIGHT = "right"
    ISOMETRIC = "isometric"
    SECTION = "section"


class FeatureType(Enum):
    """特征类型枚举"""
    CIRCLE = "circle"
    COUNTERBORE = "counterbore"
    COUNTERSINK = "countersink"
    DRILLED_HOLE = "drilled_hole"
    TAPPED_HOLE = "tapped_hole"
    POCKET = "pocket"
    SLOT = "slot"


@dataclass
class Dimension:
    """尺寸对象"""
    value: float
    tolerance: Optional[str] = None
    unit: str = "mm"
    dimension_type: str = "linear"
    reference_point: Optional[Tuple[float, float]] = None
    direction: Optional[str] = None  # 'horizontal', 'vertical', 'diagonal'


@dataclass
class Feature:
    """特征对象"""
    type: FeatureType
    center: Tuple[float, float]
    dimensions: Dict[str, float]  # 如 {'diameter': 10.0, 'depth': 5.0}
    annotation: str = ""  # 图纸中的标注
    confidence: float = 1.0


@dataclass
class View:
    """视图对象"""
    name: str
    type: ViewType
    dimensions: List[Dimension]
    features: List[Feature]
    reference_points: Dict[str, Tuple[float, float]]
    scale: float = 1.0


@dataclass
class DrawingInfo:
    """图纸信息"""
    views: List[View]
    overall_dimensions: List[Dimension]
    features: List[Feature]
    material: Optional[str] = None
    drawing_number: Optional[str] = None
    revision: Optional[str] = None
    drawing_scale: Optional[float] = None  # 图纸比例


class MechanicalDrawingExpert:
    """机械制图专家类"""
    
    def __init__(self):
        self.dimension_patterns = [
            r'(\d+\.?\d*)\s*([+-]\s*\d+\.?\d*)',  # 带公差的尺寸
            r'(\d+\.?\d*)\s*\(?\s*±\s*(\d+\.?\d*)\s*\)?',  # 正负公差
            r'(\d+\.?\d*)',  # 简单尺寸
        ]
        
        self.view_patterns = {
            'front': [r'正视图', r'前视图', r'front', r'front view'],
            'top': [r'俯视图', r'top', r'top view'],
            'side': [r'侧视图', r'side', r'side view', r'left', r'right'],
        }
    
    def parse_drawing(self, drawing_content: str) -> DrawingInfo:
        """
        解析机械图纸内容
        
        Args:
            drawing_content: 图纸内容字符串
            
        Returns:
            DrawingInfo: 解析后的图纸信息
        """
        views = self._identify_views(drawing_content)
        overall_dimensions = self._extract_overall_dimensions(drawing_content)
        features = self._extract_features_from_text(drawing_content)
        
        drawing_info = DrawingInfo(
            views=views,
            overall_dimensions=overall_dimensions,
            features=features
        )
        
        # 提取材料、图号、版本等信息
        drawing_info.material = self._extract_material(drawing_content)
        drawing_info.drawing_number = self._extract_drawing_number(drawing_content)
        drawing_info.revision = self._extract_revision(drawing_content)
        drawing_info.drawing_scale = self._extract_drawing_scale(drawing_content)
        
        return drawing_info
    
    def _extract_features_from_text(self, content: str) -> List[Feature]:
        """
        从图纸文本中提取加工特征
        
        Args:
            content: 图纸文本内容
            
        Returns:
            List[Feature]: 提取到的特征列表
        """
        features = []
        
        # 匹配沉孔特征 - 更宽泛的模式匹配
        counterbore_patterns = [
            r'φ?(\d+\.?\d*)\s*沉孔.*?深\s*(\d+\.?\d*)\s*mm.*?φ?(\d+\.?\d*)\s*底孔',
            r'沉孔.*?φ?(\d+\.?\d*).*?深\s*(\d+\.?\d*)\s*mm.*?φ?(\d+\.?\d*)\s*底孔',
            r'φ?(\d+\.?\d*)\s*counterbore.*?deep\s*(\d+\.?\d*)\s*mm.*?φ?(\d+\.?\d*)\s*thru',
            r'counterbore.*?φ?(\d+\.?\d*).*?deep\s*(\d+\.?\d*)\s*mm.*?φ?(\d+\.?\d*)\s*thru',
            # 增加更多模式以匹配"3个φ22沉孔深20mm，φ14.5贯通底孔"这样的描述
            r'(\d+)\s*个.*?φ?(\d+\.?\d*)\s*沉孔.*?深\s*(\d+\.?\d*)\s*mm.*?φ?(\d+\.?\d*)\s*(?:贯通底孔|底孔|thru)',
            r'(\d+)\s*φ?(\d+\.?\d*)\s*沉孔.*?深\s*(\d+\.?\d*)\s*mm.*?φ?(\d+\.?\d*)\s*(?:贯通底孔|底孔|thru)',
            # 简单模式匹配
            r'沉孔.*?φ?(\d+\.?\d*).*?深\s*(\d+\.?\d*)\s*mm',
            r'φ?(\d+\.?\d*)\s*沉孔.*?深\s*(\d+\.?\d*)\s*mm'
        ]
        
        for pattern in counterbore_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    if len(match) >= 3:
                        # 处理多孔模式 (数量, 外径, 深度, 内径)
                        if len(match) == 4 and match[0].isdigit():
                            # 这是多孔模式，第一个元素是数量
                            count = int(match[0])
                            outer_diameter = float(match[1])
                            depth = float(match[2])
                            inner_diameter = float(match[3])
                        else:
                            # 标准模式 (外径, 深度, 内径)
                            outer_diameter = float(match[0])
                            depth = float(match[1])
                            inner_diameter = float(match[2])
                    
                        feature = Feature(
                            type=FeatureType.COUNTERBORE,
                            center=(0, 0),  # 实际中心坐标需要与图像识别结果匹配
                            dimensions={
                                'outer_diameter': outer_diameter,
                                'depth': depth,
                                'inner_diameter': inner_diameter
                            },
                            annotation=f"φ{outer_diameter}沉孔深{depth}mm + φ{inner_diameter}贯通底孔",
                            confidence=0.9
                        )
                        features.append(feature)
                    elif len(match) == 2:
                        # 简单模式 (外径, 深度)，假设内径为外径的65%
                        outer_diameter = float(match[0])
                        depth = float(match[1])
                        inner_diameter = outer_diameter * 0.65  # 假设内径是外径的65%
                        
                        feature = Feature(
                            type=FeatureType.COUNTERBORE,
                            center=(0, 0),
                            dimensions={
                                'outer_diameter': outer_diameter,
                                'depth': depth,
                                'inner_diameter': inner_diameter
                            },
                            annotation=f"φ{outer_diameter}沉孔深{depth}mm",
                            confidence=0.7  # 稍低的置信度因为是估算的内径
                        )
                        features.append(feature)
                except (ValueError, IndexError):
                    continue
        
        # 匹配锪孔特征
        countersink_patterns = [
            r'φ?(\d+\.?\d*)\s*锪孔',
            r'锪孔.*?φ?(\d+\.?\d*)'
        ]
        
        for pattern in countersink_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    diameter = float(match)
                    feature = Feature(
                        type=FeatureType.COUNTERSINK,
                        center=(0, 0),
                        dimensions={'diameter': diameter},
                        annotation=f"φ{diameter}锪孔",
                        confidence=0.8
                    )
                    features.append(feature)
                except ValueError:
                    continue
        
        # 匹配螺纹孔特征
        tapped_hole_patterns = [
            r'(M\d+\.?\d*).*?深\s*(\d+\.?\d*)\s*mm',
            r'螺纹.*?(M\d+\.?\d*).*?深\s*(\d+\.?\d*)\s*mm'
        ]
        
        for pattern in tapped_hole_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                try:
                    thread_type = match[0]
                    depth = float(match[1])
                    
                    feature = Feature(
                        type=FeatureType.TAPPED_HOLE,
                        center=(0, 0),
                        dimensions={
                            'thread_type': thread_type,
                            'depth': depth
                        },
                        annotation=f"{thread_type}螺纹孔深{depth}mm",
                        confidence=0.85
                    )
                    features.append(feature)
                except (ValueError, IndexError):
                    continue
        
        return features

    def _extract_drawing_scale(self, content: str) -> Optional[float]:
        """
        从图纸中提取比例信息
        """
        scale_patterns = [
            r'比例[:：]\s*1\s*[:：]\s*(\d+\.?\d*)',
            r'scale[:：]\s*1\s*[:：]\s*(\d+\.?\d*)',
            r'1[:：/](\d+\.?\d*)\s*比例',
            r'1[:：/](\d+\.?\d*)'
        ]
        
        for pattern in scale_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                try:
                    return 1.0 / float(matches[0])
                except ValueError:
                    continue
        
        return None
    
    def _identify_views(self, content: str) -> List[View]:
        """识别图纸中的视图"""
        views = []
        
        # 查找视图标识
        for view_type, patterns in self.view_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # 提取该视图的尺寸信息
                    view_dims = self._extract_dimensions_for_view(content, pattern)
                    reference_points = self._extract_reference_points(content)
                    
                    view = View(
                        name=pattern,
                        type=ViewType(view_type),
                        dimensions=view_dims,
                        reference_points=reference_points
                    )
                    views.append(view)
                    break
        
        return views
    
    def _extract_dimensions_for_view(self, content: str, view_pattern: str) -> List[Dimension]:
        """为特定视图提取尺寸"""
        # 在视图附近查找尺寸标注
        # 这里简化处理，实际实现可能需要更复杂的文本分析
        dimensions = []
        
        for pattern in self.dimension_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if len(match) == 2:  # 带公差的尺寸
                    value = float(match[0])
                    tolerance = match[1]
                    dim = Dimension(value=value, tolerance=tolerance)
                else:  # 简单尺寸
                    value = float(match[0])
                    dim = Dimension(value=value)
                
                dimensions.append(dim)
        
        return dimensions
    
    def _extract_reference_points(self, content: str) -> Dict[str, Tuple[float, float]]:
        """提取参考点信息"""
        reference_points = {}
        
        # 查找可能的参考点标识
        # 例如: "以左下角为原点", "基准A", "datum A" 等
        patterns = [
            r'以\s*([东南西北上下前后左右中])\s*([东南西北上下前后左右中])\s*角为原点',
            r'基准\s*([A-Z])',
            r'datum\s*([A-Z])',
            r'reference\s*([A-Z])',
            r'原点\s*[:：]\s*([-\d.]+)\s*,\s*([-\d.]+)',
            r'origin\s*[:：]\s*([-\d.]+)\s*,\s*([-\d.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) == 2 and match[0].isdigit() and match[1].isdigit():
                    # 原点坐标
                    x, y = float(match[0]), float(match[1])
                    reference_points['origin'] = (x, y)
                elif len(match) == 1:
                    # 基准点
                    reference_points[f'datum_{match[0]}'] = (0, 0)  # 默认坐标
        
        return reference_points
    
    def _extract_overall_dimensions(self, content: str) -> List[Dimension]:
        """提取整体尺寸"""
        dimensions = []
        
        # 查找整体尺寸标注
        patterns = [
            r'总体尺寸[:：]\s*([-\d.]+)\s*x\s*([-\d.]+)',
            r'外形尺寸[:：]\s*([-\d.]+)\s*x\s*([-\d.]+)',
            r'长宽[:：]\s*([-\d.]+)\s*x\s*([-\d.]+)',
            r'尺寸[:：]\s*([-\d.]+)\s*x\s*([-\d.]+)',
            r'([-\d.]+)\s*x\s*([-\d.]+)\s*mm',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                if len(match) >= 2:
                    width = float(match[0])
                    height = float(match[1])
                    dimensions.append(Dimension(value=width, dimension_type='width'))
                    dimensions.append(Dimension(value=height, dimension_type='height'))
        
        return dimensions
    
    def _extract_material(self, content: str) -> Optional[str]:
        """提取材料信息"""
        patterns = [
            r'材料[:：]\s*([A-Z0-9\-\s]+)',
            r'material[:：]\s*([A-Z0-9\-\s]+)',
            r'材质[:：]\s*([A-Z0-9\-\s]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_drawing_number(self, content: str) -> Optional[str]:
        """提取图号"""
        patterns = [
            r'图号[:：]\s*([A-Z0-9\-_]+)',
            r'drawing\s+no\.?\s*[:：]?\s*([A-Z0-9\-_]+)',
            r'图纸编号[:：]\s*([A-Z0-9\-_]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def _extract_revision(self, content: str) -> Optional[str]:
        """提取版本信息"""
        patterns = [
            r'版本[:：]\s*([A-Z0-9]+)',
            r'rev\.?\s*[:：]?\s*([A-Z0-9]+)',
            r'版本号[:：]\s*([A-Z0-9]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                return matches[0].strip()
        
        return None
    
    def analyze_view_relationships(self, drawing_info: DrawingInfo) -> Dict[str, List[str]]:
        """
        分析视图之间的关系
        
        Args:
            drawing_info: 图纸信息
            
        Returns:
            Dict: 视图关系映射
        """
        relationships = {}
        
        view_names = [view.name for view in drawing_info.views]
        
        # 简化实现：建立视图之间的关联
        for i, view in enumerate(drawing_info.views):
            related_views = []
            for j, other_view in enumerate(drawing_info.views):
                if i != j:
                    related_views.append(other_view.name)
            
            relationships[view.name] = related_views
        
        return relationships
    
    def normalize_coordinates(self, drawing_info: DrawingInfo, 
                            target_reference: str = 'origin') -> Dict[str, Tuple[float, float]]:
        """
        根据指定的参考基准标准化坐标
        
        Args:
            drawing_info: 图纸信息
            target_reference: 目标参考基准
            
        Returns:
            Dict: 标准化后的坐标映射
        """
        normalized_coords = {}
        
        # 如果有多个视图，需要根据参考点进行坐标转换
        for view in drawing_info.views:
            for ref_name, ref_point in view.reference_points.items():
                if target_reference == ref_name or target_reference == 'origin':
                    # 使用该参考点作为基准
                    normalized_coords[ref_name] = ref_point
        
        return normalized_coords