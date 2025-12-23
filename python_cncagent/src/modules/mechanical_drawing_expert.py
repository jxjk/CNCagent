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
class View:
    """视图对象"""
    name: str
    type: ViewType
    dimensions: List[Dimension]
    reference_points: Dict[str, Tuple[float, float]]
    scale: float = 1.0


@dataclass
class DrawingInfo:
    """图纸信息"""
    views: List[View]
    overall_dimensions: List[Dimension]
    material: Optional[str] = None
    drawing_number: Optional[str] = None
    revision: Optional[str] = None


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
        
        drawing_info = DrawingInfo(
            views=views,
            overall_dimensions=overall_dimensions
        )
        
        # 提取材料、图号、版本等信息
        drawing_info.material = self._extract_material(drawing_content)
        drawing_info.drawing_number = self._extract_drawing_number(drawing_content)
        drawing_info.revision = self._extract_revision(drawing_content)
        
        return drawing_info
    
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