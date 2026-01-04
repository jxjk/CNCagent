"""
几何推理引擎模块
专门处理复杂几何特征的推理和工艺规划
"""
import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from dataclasses import field
import numpy as np
import cv2
from scipy import ndimage


@dataclass
class Feature3D:
    """3D特征数据类"""
    shape_type: str  # 'rectangular_cavity', 'circular_cavity', 'slot', 'pocket', 'thread', 'gear_tooth', etc.
    center: Tuple[float, float, float]
    dimensions: Tuple[float, float, float]  # (length, width, depth)
    corner_radius: Optional[float] = None
    bottom_radius: Optional[float] = None
    coordinate_system: str = "absolute"  # "absolute", "relative", "datum_based"
    processing_sides: List[str] = field(default_factory=list)  # ['top', 'bottom', 'side1', 'side2', ...]
    processing_sequence: List[int] = field(default_factory=list)  # 加工顺序
    confidence: float = 1.0  # 几何特征识别的置信度
    semantic_info: Optional[Dict[str, Any]] = None  # 语义信息


@dataclass
class ProcessPlan:
    """工艺规划数据类"""
    feature_id: str
    operation_type: str  # drilling, milling, tapping, etc.
    tool_selection: str
    cutting_parameters: Dict[str, float]  # spindle_speed, feed_rate, depth_of_cut, stepover
    toolpath_strategy: str  # linear, circular, zigzag, spiral, etc.
    processing_order: int
    estimated_time: float  # 估计加工时间


class GeometricReasoningEngine:
    """
    几何推理引擎
    专门处理复杂几何特征的推理和工艺规划
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_cavity_features(self, image: np.ndarray) -> List[Feature3D]:
        """
        分析图像中的腔槽特征，增强对复杂几何特征的识别能力
        """
        features = []
        
        # 使用OpenCV进行边缘检测
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        edges = cv2.Canny(gray, 50, 150)
        
        # 进行形态学操作以连接断开的边缘
        kernel = np.ones((3,3), np.uint8)
        edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
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
            
            # 判断形状类型 - 增强识别能力
            shape_type, confidence = self._identify_shape_type_enhanced(contour, w, h)
            
            if shape_type in ['rectangular_cavity', 'circular_cavity', 'slot', 'thread', 'polygon_cavity']:
                # 计算圆角半径
                corner_radius = self._estimate_corner_radius_enhanced(contour, w, h)
                
                # 分析深度信息（如果可用）
                # 这里简化处理，使用默认深度，实际应用中应从3D信息获取
                depth = 0.0
                
                # 创建特征对象
                feature = Feature3D(
                    shape_type=shape_type,
                    center=(float(center_x), float(center_y), 0.0),  # Z坐标需要根据深度信息确定
                    dimensions=(float(w), float(h), depth),  # 深度需要根据Z信息确定
                    corner_radius=corner_radius,
                    confidence=confidence,
                    semantic_info={'area': area, 'perimeter': cv2.arcLength(contour, True)}
                )
                
                features.append(feature)
        
        return features
    
    def _identify_shape_type_enhanced(self, contour, width, height) -> Tuple[str, float]:
        """
        增强的形状类型识别，能够识别更多几何特征
        返回形状类型和置信度
        """
        # 计算轮廓的近似多边形
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)
        
        # 计算轮廓的圆形度
        area = cv2.contourArea(contour)
        perimeter = cv2.arcLength(contour, True)
        
        if perimeter == 0:
            return 'unknown', 0.0
        
        circularity = 4 * math.pi * area / (perimeter * perimeter)
        
        # 计算长宽比
        aspect_ratio = float(width) / height if height != 0 else 0
        
        # 计算轮廓的凸性
        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0
        
        # 计算轮廓的伸长率
        extent = float(area) / (width * height) if width * height > 0 else 0
        
        # 判断形状 - 增强识别能力
        if len(approx) == 3:
            # 三角形
            return 'triangular_cavity', 0.9
        elif len(approx) == 4:
            # 检查是否为矩形或槽
            if 0.8 <= aspect_ratio <= 1.2:
                # 接近正方形，可能是圆形腔槽
                if circularity > 0.8:
                    return 'circular_cavity', 0.95
                else:
                    return 'rectangular_cavity', 0.85
            else:
                # 长宽比大，可能是槽
                return 'slot', 0.8
        elif len(approx) > 4 and circularity > 0.8:
            # 圆形或椭圆
            return 'circular_cavity', 0.9
        elif len(approx) > 4 and 0.7 <= circularity <= 0.8:
            # 近似圆形
            return 'circular_cavity', 0.85
        elif len(approx) > 5 and solidity < 0.9:
            # 凹形特征，可能是特殊腔槽
            return 'polygon_cavity', 0.75
        elif len(approx) > 5 and extent < 0.6:
            # 不规则特征
            return 'irregular_cavity', 0.7
        elif circularity < 0.5 and aspect_ratio > 3:
            # 长条形特征
            return 'slot', 0.75
        else:
            # 默认为矩形腔槽
            return 'rectangular_cavity', 0.6
    
    def _estimate_corner_radius_enhanced(self, contour, width, height) -> Optional[float]:
        """
        增强的圆角半径估算
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
        分析加工结构（单面/多面）- 增强版本
        """
        analysis = {
            'single_sided_features': [],
            'multi_sided_features': [],
            'processing_sequence': [],
            'clamping_suggestions': [],
            'tool_accessibility': [],
            'process_feasibility': {}
        }
        
        for i, feature in enumerate(features):
            # 简化分析：根据Z坐标和深度判断加工面
            if feature.center[2] == 0 and feature.dimensions[2] > 0:
                # 从顶面加工，单面结构
                analysis['single_sided_features'].append(feature)
            else:
                # 可能需要多面加工
                analysis['multi_sided_features'].append(feature)
                
            # 分析刀具可达性
            tool_access = self._analyze_tool_accessibility(feature)
            analysis['tool_accessibility'].append({
                'feature_id': i,
                'accessibility': tool_access['accessibility'],
                'recommended_tools': tool_access['recommended_tools']
            })
        
        # 推荐加工顺序
        analysis['processing_sequence'] = self._recommend_processing_sequence(features)
        
        # 夹紧建议
        analysis['clamping_suggestions'] = self._generate_clamping_suggestions(features)
        
        # 工艺可行性分析
        analysis['process_feasibility'] = self._analyze_process_feasibility(features)
        
        return analysis
    
    def _analyze_tool_accessibility(self, feature: Feature3D) -> Dict:
        """
        分析刀具可达性
        """
        accessibility = "good"
        recommended_tools = []
        accessibility_issues = []
        
        # 根据特征类型和尺寸推荐刀具
        length, width, depth = feature.dimensions
        
        if feature.shape_type in ["circular_cavity", "rectangular_cavity"]:
            # 根据腔槽尺寸推荐刀具
            min_dimension = min(length, width)
            
            if min_dimension < 5:
                recommended_tools.append("小型立铣刀(φ3-φ5)")
                if accessibility == "good" and min_dimension < 3:
                    accessibility = "challenging"
            elif min_dimension < 10:
                recommended_tools.append("标准立铣刀(φ6-φ10)")
            elif min_dimension < 20:
                recommended_tools.append("中型立铣刀(φ10-φ20)")
            else:
                recommended_tools.append("大直径铣刀(φ20+)")
                
            # 深腔槽需要长径比较大的刀具
            if depth > 3 * min_dimension:
                accessibility = "challenging"
                recommended_tools.append("长刃铣刀或分层铣削")
                accessibility_issues.append(f"深径比过大({depth/min_dimension:.1f}:1)，需分层加工")
            elif depth > min_dimension:
                accessibility = "moderate"
                recommended_tools.append("考虑分层铣削")
                accessibility_issues.append(f"深度大于最小尺寸，建议分层加工")
        
        elif feature.shape_type == "slot":
            # 槽加工的刀具选择
            min_dimension = min(length, width)
            if min_dimension < 3:
                recommended_tools.append("超窄槽铣刀")
                accessibility = "challenging"
                accessibility_issues.append("槽宽过窄，刀具选择受限")
            elif min_dimension < 5:
                recommended_tools.append("窄槽铣刀")
            elif min_dimension < 10:
                recommended_tools.append("标准铣刀")
            else:
                recommended_tools.append("宽槽加工刀具")
        
        elif feature.shape_type == "circular_hole":
            # 圆孔加工刀具选择
            diameter = min(length, width)
            if diameter < 3:
                recommended_tools.append("微型钻头")
                accessibility = "challenging"
            elif diameter < 10:
                recommended_tools.append("标准钻头")
            elif diameter < 20:
                recommended_tools.append("大直径钻头")
            else:
                recommended_tools.append("镗刀或扩孔钻")
        
        # 检查是否有特殊要求
        if feature.corner_radius and feature.corner_radius > 0:
            recommended_tools.append(f"球头刀或圆角铣刀(R{feature.corner_radius})")
            
        # 检查壁厚是否过薄
        if hasattr(feature, 'wall_thickness') and feature.wall_thickness < 1:
            accessibility = "challenging"
            accessibility_issues.append(f"壁厚过薄({feature.wall_thickness}mm)，易变形")
        
        return {
            'accessibility': accessibility,
            'recommended_tools': recommended_tools,
            'accessibility_issues': accessibility_issues
        }
    
    def _analyze_process_feasibility(self, features: List[Feature3D]) -> Dict:
        """
        分析工艺可行性
        """
        feasibility = {
            'overall_feasibility': 'high',
            'potential_issues': [],
            'suggestions': []
        }
        
        for feature in features:
            # 检查特征尺寸是否在加工能力范围内
            length, width, depth = feature.dimensions
            
            # 深宽比检查
            min_dimension = min(length, width) if length > 0 and width > 0 else max(length, width)
            if min_dimension > 0 and depth / min_dimension > 5:
                feasibility['potential_issues'].append(f"特征{feature.shape_type}深宽比过大，可能需要特殊刀具或工艺")
                feasibility['suggestions'].append("考虑分层铣削或使用加长刀具")
            
            # 检查精度要求
            if feature.confidence < 0.7:
                feasibility['potential_issues'].append(f"特征{feature.shape_type}识别置信度较低，可能影响加工精度")
        
        # 综合评估
        if len(feasibility['potential_issues']) > 3:
            feasibility['overall_feasibility'] = 'low'
        elif len(feasibility['potential_issues']) > 0:
            feasibility['overall_feasibility'] = 'medium'
        
        return feasibility
    
    def analyze_geometric_features(self, features_data: List[Dict]) -> List[Feature3D]:
        """
        分析几何特征，增强版本
        """
        analyzed_features = []
        
        for i, feature_data in enumerate(features_data):
            # 根据特征数据创建Feature3D对象
            shape_type = feature_data.get('shape', 'unknown')
            center = feature_data.get('center', [0, 0, 0])
            dimensions = feature_data.get('dimensions', [0, 0, 0])
            confidence = feature_data.get('confidence', 0.8)
            
            # 确保center和dimensions是正确的格式
            if isinstance(center, (list, tuple)) and len(center) >= 2:
                center = (float(center[0]), float(center[1]), float(center[2]) if len(center) > 2 else 0.0)
            else:
                center = (0.0, 0.0, 0.0)
                
            if isinstance(dimensions, (list, tuple)) and len(dimensions) >= 3:
                dimensions = (float(dimensions[0]), float(dimensions[1]), float(dimensions[2]))
            else:
                dimensions = (0.0, 0.0, 0.0)
            
            # 获取圆角半径
            corner_radius = feature_data.get('corner_radius')
            if corner_radius is not None:
                corner_radius = float(corner_radius)
            
            # 创建特征对象
            feature = Feature3D(
                shape_type=shape_type,
                center=center,
                dimensions=dimensions,
                corner_radius=corner_radius,
                confidence=confidence,
                semantic_info=feature_data.get('semantic_info', {})
            )
            
            analyzed_features.append(feature)
        
        return analyzed_features

    def infer_geometric_relationships(self, features: List[Feature3D]) -> Dict:
        """
        推断几何关系，增强版本
        """
        relationships = {
            'spatial_relationships': [],
            'dimensional_constraints': [],
            'tolerance_zones': [],
            'feature_interactions': []
        }
        
        # 分析特征间的空间关系
        for i, feat1 in enumerate(features):
            for j, feat2 in enumerate(features):
                if i >= j:  # 避免重复计算
                    continue
                    
                # 计算两特征中心距离
                dist_x = abs(feat1.center[0] - feat2.center[0])
                dist_y = abs(feat1.center[1] - feat2.center[1])
                center_distance = math.sqrt(dist_x**2 + dist_y**2)
                
                # 检查是否可能有相互作用
                interaction_type = None
                if center_distance < (max(feat1.dimensions[0], feat1.dimensions[1]) + max(feat2.dimensions[0], feat2.dimensions[1])) / 2:
                    interaction_type = "close_proximity"
                
                if interaction_type:
                    relationships['feature_interactions'].append({
                        'feature1_id': i,
                        'feature2_id': j,
                        'interaction_type': interaction_type,
                        'center_distance': center_distance
                    })
        
        # 分析尺寸约束
        for i, feature in enumerate(features):
            # 检查是否在工件边界内
            if feature.center[0] - feature.dimensions[0]/2 < 0 or feature.center[0] + feature.dimensions[0]/2 > 200:  # 假设工件宽度为200mm
                relationships['dimensional_constraints'].append({
                    'feature_id': i,
                    'constraint_type': 'boundary_limit',
                    'dimension': 'x'
                })
            if feature.center[1] - feature.dimensions[1]/2 < 0 or feature.center[1] + feature.dimensions[1]/2 > 200:  # 假设工件高度为200mm
                relationships['dimensional_constraints'].append({
                    'feature_id': i,
                    'constraint_type': 'boundary_limit',
                    'dimension': 'y'
                })
        
        return relationships

    def generate_process_plan(self, features: List[Feature3D], material: str = "Aluminum") -> List[ProcessPlan]:
        """
        生成工艺规划，增强版本
        """
        process_plans = []
        
        for i, feature in enumerate(features):
            # 根据特征类型和材料确定加工工艺
            operation_type = self._determine_operation_type(feature)
            tool_selection = self._select_tool(feature, material)
            cutting_parameters = self._determine_cutting_parameters(feature, material)
            toolpath_strategy = self._select_toolpath_strategy(feature)
            
            # 创建工艺规划对象
            plan = ProcessPlan(
                feature_id=f"feature_{i}",
                operation_type=operation_type,
                tool_selection=tool_selection,
                cutting_parameters=cutting_parameters,
                toolpath_strategy=toolpath_strategy,
                processing_order=i,  # 简单顺序，实际应用中应更复杂
                estimated_time=self._estimate_processing_time(feature, cutting_parameters)
            )
            
            process_plans.append(plan)
        
        return process_plans
    
    def _determine_operation_type(self, feature: Feature3D) -> str:
        """
        确定加工类型
        """
        if 'circular' in feature.shape_type.lower():
            if feature.dimensions[2] > 10:  # 深度大于10mm
                return 'drilling'
            else:
                return 'spot_drilling'
        elif 'rectangular' in feature.shape_type.lower() or 'cavity' in feature.shape_type.lower():
            if feature.dimensions[2] > 5:  # 深度大于5mm
                return 'pocket_milling'
            else:
                return 'profile_milling'
        elif 'slot' in feature.shape_type.lower():
            return 'slot_milling'
        else:
            return 'general_milling'
    
    def _select_tool(self, feature: Feature3D, material: str) -> str:
        """
        选择刀具
        """
        min_dimension = min(feature.dimensions[0], feature.dimensions[1])
        
        if 'circular' in feature.shape_type.lower():
            # 孔加工
            if min_dimension < 3:
                return 'center_drill'
            elif min_dimension < 10:
                return 'standard_drill'
            else:
                return 'large_diameter_drill'
        elif 'cavity' in feature.shape_type.lower() or 'rectangular' in feature.shape_type.lower():
            # 腔槽加工
            if min_dimension < 5:
                return 'φ3_flat_endmill'
            elif min_dimension < 10:
                return 'φ6_flat_endmill'
            elif min_dimension < 20:
                return 'φ10_flat_endmill'
            else:
                return 'φ16+_flat_endmill'
        else:
            # 其他加工
            return 'standard_endmill'
    
    def _determine_cutting_parameters(self, feature: Feature3D, material: str) -> Dict[str, float]:
        """
        确定切削参数
        """
        # 基础参数根据材料设定
        base_params = {
            'aluminum': {'spindle_speed': 1200, 'feed_rate': 800, 'depth_of_cut': 2.0},
            'steel': {'spindle_speed': 600, 'feed_rate': 200, 'depth_of_cut': 1.0},
            'stainless_steel': {'spindle_speed': 400, 'feed_rate': 150, 'depth_of_cut': 0.8},
            'cast_iron': {'spindle_speed': 800, 'feed_rate': 400, 'depth_of_cut': 1.5}
        }
        
        material_lower = material.lower()
        if material_lower in base_params:
            params = base_params[material_lower].copy()
        else:
            params = base_params['aluminum'].copy()  # 默认使用铝合金参数
        
        # 根据特征尺寸调整参数
        min_dimension = min(feature.dimensions[0], feature.dimensions[1])
        depth = feature.dimensions[2]
        
        # 对于小特征，降低进给速度以保证精度
        if min_dimension < 5:
            params['feed_rate'] *= 0.7
        elif min_dimension < 10:
            params['feed_rate'] *= 0.85
        
        # 对于深特征，降低进给和切削深度
        if depth > 10:
            params['feed_rate'] *= 0.8
            params['depth_of_cut'] = min(params['depth_of_cut'], 1.0)
        elif depth > 5:
            params['feed_rate'] *= 0.9
        
        # 计算步距（用于腔槽加工）
        params['stepover'] = min(params['depth_of_cut'] * 0.8, min_dimension * 0.6)
        
        return params
    
    def _select_toolpath_strategy(self, feature: Feature3D) -> str:
        """
        选择刀具路径策略
        """
        if 'circular' in feature.shape_type.lower():
            return 'circular' if feature.dimensions[2] > 5 else 'peck_drilling'
        elif 'rectangular' in feature.shape_type.lower() or 'cavity' in feature.shape_type.lower():
            if feature.dimensions[0] > 30 or feature.dimensions[1] > 30:
                return 'zigzag_clearing'
            else:
                return 'spiral_clearing'
        elif 'slot' in feature.shape_type.lower():
            return 'linear_milling'
        else:
            return 'contour_following'
    
    def _estimate_processing_time(self, feature: Feature3D, cutting_params: Dict[str, float]) -> float:
        """
        估算加工时间
        """
        # 简化的加工时间估算
        volume = feature.dimensions[0] * feature.dimensions[1] * feature.dimensions[2]
        material_removal_rate = cutting_params['feed_rate'] * cutting_params['depth_of_cut'] * cutting_params['stepover'] / 1000  # cm³/min
        
        if material_removal_rate > 0:
            estimated_time = volume / 1000 / material_removal_rate  # 转换为cm³并计算时间
            # 添加一些安全时间
            estimated_time *= 1.3
        else:
            estimated_time = 1.0  # 默认1分钟
        
        return max(estimated_time, 0.5)  # 最少0.5分钟


    def _recommend_processing_sequence(self, features: List[Feature3D]) -> List[int]:
        """
        推荐加工顺序，增强版本
        """
        # 改进的加工顺序推荐算法
        # 考虑特征类型、尺寸、位置、深度等因素
        feature_indices = list(range(len(features)))
        
        # 定义加工顺序的优先级函数
        def get_priority(i):
            feature = features[i]
            # 优先级因素：
            # 1. 特征类型：先钻孔后铣削
            type_priority = {
                'circular_cavity': 1,  # 钻孔类
                'slot': 2,             # 槽加工
                'rectangular_cavity': 3,  # 腔槽
                'irregular_cavity': 4, # 不规则腔槽
                'polygon_cavity': 4    # 多边形腔槽
            }
            type_score = type_priority.get(feature.shape_type, 5)
            
            # 2. 深度：浅的先加工
            depth_score = feature.dimensions[2]
            
            # 3. 尺寸：小的特征先加工（避免影响其他特征）
            size_score = min(feature.dimensions[0], feature.dimensions[1])
            
            # 4. 置信度：置信度高的先加工
            confidence_score = -feature.confidence  # 负号是因为置信度高应该优先
            
            # 综合评分（权重可以根据实际情况调整）
            total_score = (type_score * 100) + depth_score + (1 / (size_score + 1) * 10) + (confidence_score * 50)
            
            return total_score
        
        # 根据综合评分排序
        feature_indices.sort(key=get_priority)
        return feature_indices
    
    def _generate_clamping_suggestions(self, features: List[Feature3D]) -> List[str]:
        """
        生成夹紧建议，增强版本
        """
        suggestions = []
        
        # 检查是否需要多面加工
        has_deep_features = any(f.dimensions[2] > 20 for f in features)  # 深度大于20mm
        has_large_features = any(max(f.dimensions[0], f.dimensions[1]) > 50 for f in features)  # 尺寸大于50mm
        feature_count = len(features)
        
        if has_deep_features:
            suggestions.append("对于深度超过20mm的特征，建议使用专用夹具或考虑分多面加工")
        
        if has_large_features:
            suggestions.append("存在较大尺寸特征，确保夹紧力分布均匀，避免工件变形")
        
        if feature_count > 10:
            suggestions.append("特征数量较多，建议使用专用工装或分区域加工")
        elif feature_count > 5:
            suggestions.append("特征数量较多，考虑合理安排加工顺序以减少刀具更换")
        
        # 检查特征分布
        if features:
            x_coords = [f.center[0] for f in features]
            y_coords = [f.center[1] for f in features]
            x_span = max(x_coords) - min(x_coords)
            y_span = max(y_coords) - min(y_coords)
            
            if x_span > 150 or y_span > 150:  # 假设工件较大
                suggestions.append("特征分布范围较大，需确保夹紧点分布合理，避免悬臂加工")
        
        return suggestions if suggestions else ["标准夹紧方式即可"]
    
    def generate_coordinate_system_description(self, features: List[Feature3D]) -> str:
        """
        生成坐标系统描述，增强版本
        """
        descriptions = []
        
        for i, feature in enumerate(features):
            # 根据特征类型和位置推荐坐标系统
            coord_desc = f"特征{i+1}({feature.shape_type}): "
            
            if feature.coordinate_system == "datum_based":
                coord_desc += f"以特征中心({feature.center[0]:.2f}, {feature.center[1]:.2f})为原点，"
            elif feature.coordinate_system == "relative":
                coord_desc += f"相对于基准点偏移({feature.center[0]:.2f}, {feature.center[1]:.2f})，"
            else:  # absolute
                coord_desc += f"绝对坐标({feature.center[0]:.2f}, {feature.center[1]:.2f})，"
            
            coord_desc += f"尺寸({feature.dimensions[0]:.2f}×{feature.dimensions[1]:.2f}×{feature.dimensions[2]:.2f})mm"
            
            # 添加置信度信息
            coord_desc += f"，置信度:{feature.confidence:.2f}"
            
            descriptions.append(coord_desc)
        
        return "\n".join(descriptions)

# 全局实例
geometric_reasoning_engine = GeometricReasoningEngine()
