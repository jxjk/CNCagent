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
    
    def analyze_drawing_features(self, features: List[Dict], user_description: str) -> Dict[str, any]:
        """
        使用机械制图专业知识分析图纸特征
        
        Args:
            features: 识别出的几何特征列表
            user_description: 用户描述
            
        Returns:
            Dict: 包含分析结果的字典
        """
        analysis = {
        "features": features,
        "user_description": user_description,
        "interpretation": "根据机械制图标准分析图纸特征",
        "recommendations": [],
        "potential_issues": [],
        "processing_sequence": [],
        "processing_structure": "single_sided",  # "single_sided", "multi_sided"
        "clamping_suggestions": [],
        "tool_path_recommendations": []
        }
    
        # 分析特征类型分布
        feature_counts = {}
        for feature in features:
            shape = feature.get("shape", "unknown")
        feature_counts[shape] = feature_counts.get(shape, 0) + 1
    
        # 生成解释
        explanations = []
        if "circle" in feature_counts:
            explanations.append(f"识别到 {feature_counts['circle']} 个圆形特征，通常用于钻孔或螺栓孔")
        if "rectangle" in feature_counts:
            explanations.append(f"识别到 {feature_counts['rectangle']} 个矩形特征，可能用于键槽或其他矩形孔")
        if "counterbore" in feature_counts:
            explanations.append(f"识别到 {feature_counts['counterbore']} 个沉孔特征，用于螺钉头部沉孔")
        if "rectangular_pocket" in feature_counts:
            explanations.append(f"识别到 {feature_counts['rectangular_pocket']} 个矩形腔槽特征，用于安装或减重")
        if "rounded_rectangular_pocket" in feature_counts:
            explanations.append(f"识别到 {feature_counts['rounded_rectangular_pocket']} 个圆角矩形腔槽特征，用于减少应力集中")
    
        analysis["interpretation"] = ";".join(explanations) if explanations else "未识别到明显的几何特征"
    
        # 生成建议
        recommendations = []
        if user_description and ("攻丝" in user_description or "螺纹" in user_description):
            recommendations.append("建议按先钻孔、后攻丝的顺序进行加工")
        if user_description and ("沉孔" in user_description or "锪孔" in user_description):
            recommendations.append("建议按先点孔、再钻孔、最后锪孔的顺序进行加工")
        if user_description and ("腔" in user_description or "pocket" in user_description.lower()):
            recommendations.append("腔槽加工建议采用分层铣削，避免刀具受力过大")
        if user_description and ("槽" in user_description or "slot" in user_description.lower()):
            recommendations.append("槽加工建议使用合适的槽铣刀，注意排屑")
    
        analysis["recommendations"] = recommendations
    
        # 检查潜在问题
        potential_issues = []
        if not features:
            potential_issues.append("未识别到任何几何特征，可能需要检查图纸质量或调整识别参数")
        if len(features) > 20:
            potential_issues.append(f"识别到 {len(features)} 个特征，数量较多，建议分批处理或验证识别结果")
    
        # 检查多面加工需求
        has_deep_features = any(
        feature.get("dimensions") and 
        len(feature.get("dimensions", [])) >= 3 and 
        feature["dimensions"][2] > 20  # 假设深度大于20mm需要多面加工
        for feature in features
        )
    
        if has_deep_features:
            potential_issues.append("检测到深度较大的特征，可能需要多面加工或特殊刀具")
        analysis["processing_structure"] = "multi_sided"
    
        analysis["potential_issues"] = potential_issues
    
        # 推荐加工顺序
        processing_sequence = []
        for i, feature in enumerate(features):
            if feature["shape"] == "counterbore":
                processing_sequence.extend([
                f"第{i*3+1}步: {feature['center']} 位置进行点孔加工",
                f"第{i*3+2}步: {feature['center']} 位置进行钻孔加工", 
                f"第{i*3+3}步: {feature['center']} 位置进行锪孔加工"
            ])
            elif feature["shape"] in ["rectangular_pocket", "rounded_rectangular_pocket"]:
                processing_sequence.append(f"第{i+1}步: {feature['center']} 位置进行腔槽铣削加工，尺寸{feature['dimensions'][:2]}")
            elif feature["shape"] in ["circle", "rectangle", "square"]:
                processing_sequence.append(f"第{i+1}步: {feature['center']} 位置进行 {feature['shape']} 加工")
    
        analysis["processing_sequence"] = processing_sequence
    
        # 生成夹紧建议
        clamping_suggestions = []
        if analysis["processing_structure"] == "multi_sided":
            clamping_suggestions.append("对于多面加工，建议使用专用夹具或分度装置")
            clamping_suggestions.append("考虑加工顺序以减少工件翻转次数")
        else:
            clamping_suggestions.append("标准夹紧方式即可满足加工要求")
    
        if len([f for f in features if f.get("dimensions", [0,0])[0] > 100 or f.get("dimensions", [0,0])[1] > 100]) > 3:
            clamping_suggestions.append("多个大尺寸特征，建议增加夹紧点以提高刚性")
    
        analysis["clamping_suggestions"] = clamping_suggestions
    
        # 刀具路径建议
        tool_path_recommendations = []
        for feature in features:
            if feature["shape"] in ["rectangular_pocket", "rounded_rectangular_pocket"]:
                tool_path_recommendations.append(
                f"腔槽({feature['center']})建议采用螺旋铣削或环切路径，步距为刀具直径的60%"
            )
            elif feature["shape"] == "slot":
                tool_path_recommendations.append(
                f"槽({feature['center']})建议采用往复铣削路径，确保两端圆角处理"
            )
    
        analysis["tool_path_recommendations"] = tool_path_recommendations if tool_path_recommendations else [
        "根据特征形状选择合适的刀具路径策略"
        ]
    
        return analysis


# 全局实例
mechanical_drawing_expert = MechanicalDrawingExpert()