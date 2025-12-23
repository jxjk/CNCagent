"""
几何特征识别模块
从图像中识别几何形状，如圆形、矩形、多边形等，并提取其尺寸和位置信息
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple
import math
import logging


def identify_features(image: np.ndarray, min_area: float = 100, min_perimeter: float = 10, 
                      canny_low: int = 50, canny_high: int = 150, 
                      gaussian_kernel: tuple = (5, 5), morph_kernel: tuple = (2, 2)) -> List[Dict]:
    """
    从图像中识别几何特征（圆形、矩形、多边形等）
    
    Args:
        image (numpy.ndarray): 输入图像（预处理后的灰度图）
        min_area (float): 最小面积阈值
        min_perimeter (float): 最小周长阈值
        canny_low (int): Canny边缘检测低阈值
        canny_high (int): Canny边缘检测高阈值
        gaussian_kernel (tuple): 高斯模糊核大小
        morph_kernel (tuple): 形态学操作核大小
    
    Returns:
        list: 识别出的特征列表，每个特征包含形状、位置、尺寸等信息
    """
    # 应用高斯模糊以减少噪声
    blurred = cv2.GaussianBlur(image, gaussian_kernel, 0)
    
    # 边缘检测
    edges = cv2.Canny(blurred, canny_low, canny_high)
    
    # 形态学操作以连接断开的边缘
    kernel = np.ones(morph_kernel, np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)  # 只进行闭操作，避免去除有用边缘
    
    # 寻找轮廓（使用RETR_LIST以获取所有轮廓，不限制层级）
    contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    features = []
    
    for contour in contours:
        area = cv2.contourArea(contour)
        
        # 过滤小面积轮廓
        if area < min_area:
            continue
        
        # 计算轮廓的周长
        perimeter = cv2.arcLength(contour, True)
        
        # 跳过周长过小的轮廓
        if perimeter < min_perimeter:
            continue
        
        # 计算轮廓的圆度，用于识别圆形
        _, radius = cv2.minEnclosingCircle(contour)
        radius = int(radius)
        circle_area = math.pi * radius * radius
        
        # 计算边界框
        x, y, w, h = cv2.boundingRect(contour)
        
        # 计算长宽比
        aspect_ratio = float(w) / h if h != 0 else 0
        
        # 多种形状识别方法的融合
        shape, confidence = identify_shape_advanced(contour, area, circle_area, aspect_ratio)
        
        if shape and confidence > 0.3:  # 降低置信度阈值，但使用更高级的筛选
            # 计算几何中心
            m = cv2.moments(contour)
            if m["m00"] != 0:
                cx = int(m["m10"] / m["m00"])
                cy = int(m["m01"] / m["m00"])
            else:
                cx, cy = x + w//2, y + h//2
            
            feature = {
                "shape": shape,
                "contour": contour,
                "bounding_box": (x, y, w, h),
                "area": area,
                "center": (cx, cy),
                "dimensions": (w, h),
                "confidence": confidence,
                "aspect_ratio": aspect_ratio  # 添加长宽比信息
            }
            
            # 添加特定形状的额外信息
            if shape == "circle":
                feature["radius"] = radius
                # 计算圆形度作为一个额外的特征
                circularity = 4 * math.pi * area / (perimeter * perimeter)
                feature["circularity"] = circularity
            elif shape in ["rectangle", "square", "parallelogram"]:
                feature["length"] = max(w, h)
                feature["width"] = min(w, h)
                feature["aspect_ratio"] = aspect_ratio
            elif shape == "triangle":
                feature["vertices"] = [tuple(point[0]) for point in cv2.approxPolyDP(contour, 0.03 * perimeter, True)]
            elif shape == "ellipse":
                # 拟合椭圆
                if len(contour) >= 5:  # 至少需要5个点才能拟合椭圆
                    try:
                        ellipse = cv2.fitEllipse(contour)
                        center, axes, angle = ellipse
                        feature["ellipse_params"] = {
                            "center": center,
                            "axes": axes,
                            "angle": angle
                        }
                        feature["major_axis"] = max(axes)
                        feature["minor_axis"] = min(axes)
                    except:
                        pass  # 如果拟合失败，忽略椭圆参数
            
            features.append(feature)
    
    # 过滤重复特征
    features = filter_duplicate_features_advanced(features)
    
    # 识别复合孔特征（如沉孔）
    features = identify_counterbore_features(features)
    
    return features


def identify_shape_advanced(contour: np.ndarray, area: float, circle_area: float, aspect_ratio: float) -> Tuple[str, float]:
    """
    使用多种方法识别形状并返回置信度（改进版）
    
    Args:
        contour: 原始轮廓
        area: 轮廓面积
        circle_area: 最小外接圆面积
        aspect_ratio: 长宽比
    
    Returns:
        tuple: (形状名称, 置信度)
    """
    perimeter = cv2.arcLength(contour, True)
    
    # 计算轮廓的实心度（solidity）
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = float(area) / hull_area if hull_area > 0 else 0
    
    # 计算轮廓的延伸度（extent）
    x, y, w, h = cv2.boundingRect(contour)
    rect_area = w * h
    extent = float(area) / rect_area if rect_area > 0 else 0
    
    # 计算圆形度
    circularity = 0
    if perimeter > 0:
        circularity = 4 * math.pi * area / (perimeter * perimeter)
    
    # 估算顶点数
    epsilon = 0.03 * perimeter  # 使用更大的epsilon值以减少噪声影响
    approx = cv2.approxPolyDP(contour, epsilon, True)
    num_vertices = len(approx)
    
    # 检查是否是椭圆（通过拟合椭圆或圆形度判断）
    if len(contour) >= 5 and area > 0 and circularity < 0.8:
        try:
            # 尝试拟合椭圆
            ellipse = cv2.fitEllipse(contour)
            center, axes, angle = ellipse
            major_axis = max(axes)
            minor_axis = min(axes)
            eccentricity = math.sqrt(1 - (minor_axis / major_axis) ** 2) if major_axis > 0 else 0
            
            # 如果离心率适中（接近椭圆而非圆形），并且形状比较规则
            if 0.4 <= eccentricity <= 0.9 and solidity > 0.7:
                return "ellipse", min(1.0, solidity * extent * 0.8)
        except:
            pass  # 拟合失败则继续其他形状判断
    
    # 三角形判断
    if num_vertices == 3 and solidity > 0.7:
        return "triangle", min(1.0, solidity * 1.2)
    
    # 四边形判断
    if num_vertices == 4 and solidity > 0.8:
        # 根据长宽比判断正方形还是矩形
        if 0.8 <= aspect_ratio <= 1.2:
            return "square", min(1.0, solidity * extent * 1.5)
        else:
            return "rectangle", min(1.0, solidity * extent * 1.3)
    elif num_vertices == 4 and solidity > 0.7:
        # 可能是平行四边形
        return "parallelogram", min(1.0, solidity * extent * 1.1)
    
    # 圆形判断：使用更广泛的圆形度范围和多条件验证
    if area > 0 and circle_area > 0:
        area_ratio = area / circle_area
        if 0.7 <= area_ratio <= 1.3 and circularity > 0.8 and solidity > 0.8:
            return "circle", min(1.0, circularity * solidity)
    
    # 多边形判断：顶点数大于4且形状比较规则
    if num_vertices > 4 and num_vertices <= 10 and solidity > 0.8:
        shape_name = f"polygon_{num_vertices}_sides"
        return "polygon", min(1.0, solidity * 0.9)
    
    # 如果无法确定具体形状，但有一定规则性，标记为其他形状
    if solidity > 0.9 and extent > 0.8:
        return "irregular", min(1.0, (solidity + extent) / 2.0)
    
    # 无法识别的形状
    return "unknown", 0.0


def filter_duplicate_features_advanced(features: List[Dict]) -> List[Dict]:
    """
    使用更精确的方法过滤重复的特征（改进版）
    
    Args:
        features: 特征列表
    
    Returns:
        过滤后的特征列表
    """
    if not features:
        return []
    
    # 按中心点距离和形状类型综合判断重复
    filtered_features = []
    
    for current_feature in features:
        is_duplicate = False
        best_match_idx = -1
        best_confidence = current_feature.get("confidence", 0)
        
        for i, existing_feature in enumerate(filtered_features):
            # 计算中心点距离
            curr_center = current_feature["center"]
            exist_center = existing_feature["center"]
            distance = math.sqrt((curr_center[0] - exist_center[0])**2 + (curr_center[1] - exist_center[1])**2)
            
            # 检查形状是否相同
            same_shape = current_feature["shape"] == existing_feature["shape"]
            
            # 计算边界框重叠度
            curr_x, curr_y, curr_w, curr_h = current_feature["bounding_box"]
            exist_x, exist_y, exist_w, exist_h = existing_feature["bounding_box"]
            
            # 计算重叠区域
            x_overlap = max(0, min(curr_x + curr_w, exist_x + exist_w) - max(curr_x, exist_x))
            y_overlap = max(0, min(curr_y + curr_h, exist_y + curr_h) - max(curr_y, exist_y))
            overlap_area = x_overlap * y_overlap
            
            # 计算并集面积
            union_area = curr_w * curr_h + exist_w * curr_h - overlap_area
            iou = overlap_area / union_area if union_area > 0 else 0
            
            # 综合判断：位置接近、形状相同、且有较大重叠度
            curr_max_dim = max(current_feature["dimensions"])
            exist_max_dim = max(existing_feature["dimensions"])
            avg_max_dim = (curr_max_dim + exist_max_dim) / 2
            position_threshold = avg_max_dim * 0.5  # 使用平均尺寸的50%作为位置阈值
            
            if distance < position_threshold and same_shape and iou > 0.3:
                # 找到重复特征，保留置信度更高的
                existing_conf = existing_feature.get("confidence", 0)
                if current_feature.get("confidence", 0) > existing_conf:
                    best_match_idx = i
                    best_confidence = current_feature.get("confidence", 0)
                else:
                    is_duplicate = True
                break
        
        if is_duplicate and best_match_idx != -1:
            # 替换现有的低置信度特征
            filtered_features[best_match_idx] = current_feature
        elif not is_duplicate:
            filtered_features.append(current_feature)
    
    return filtered_features


def identify_counterbore_features(features: List[Dict]) -> List[Dict]:
    """
    识别沉孔（Counterbore）特征，即φ22沉孔深20mm + φ14.5贯通底孔的组合特征
    
    Args:
        features: 识别出的几何特征列表
    
    Returns:
        识别后特征列表，包含复合沉孔特征
    """
    # 首先筛选出圆形特征，并按中心点分组
    circle_features = [f for f in features if f.get("shape") == "circle"]
    
    # 按中心点位置分组可能的沉孔组合
    grouped_features = {}
    tolerance = 5.0  # 减小中心点距离容差，单位像素，更精确地匹配同心圆
    
    for feature in circle_features:
        center = feature["center"]
        found_group = False
        
        for group_center, group in grouped_features.items():
            dist = math.sqrt((center[0] - group_center[0])**2 + (center[1] - group_center[1])**2)
            if dist < tolerance:
                grouped_features[group_center].append(feature)
                found_group = True
                break
        
        if not found_group:
            grouped_features[center] = [feature]
    
    # 过滤后的特征列表
    filtered_features = [f for f in features if f.get("shape") != "circle"]
    
    # 检查每个分组是否为沉孔特征
    for group_center, group_features in grouped_features.items():
        if len(group_features) >= 2:
            # 按半径排序，找到最大和最小的圆（沉孔和底孔）
            sorted_by_radius = sorted(group_features, key=lambda x: x.get("radius", 0), reverse=True)
            
            # 尝试识别沉孔和底孔
            largest_circle = sorted_by_radius[0]
            smallest_circle = sorted_by_radius[-1]
            
            # 判断是否可能是沉孔特征 (φ22沉孔 + φ14.5底孔)
            largest_radius = largest_circle.get("radius", 0)
            smallest_radius = smallest_circle.get("radius", 0)
            
            # 检查半径比例是否符合沉孔特征
            # φ22沉孔 vs φ14.5底孔，半径比约为 11:7.25 ≈ 1.52
            radius_ratio = largest_radius / smallest_radius if smallest_radius > 0 else 0
            
            if 1.2 <= radius_ratio <= 3.0:  # 宽松一些的半径比范围，适应不同的沉孔规格
                # 创建沉孔特征
                counterbore_feature = {
                    "shape": "counterbore",  # 沉孔特征
                    "center": group_center,
                    "outer_radius": largest_radius,  # 沉孔半径
                    "inner_radius": smallest_radius,  # 底孔半径
                    "outer_diameter": largest_radius * 2,  # 沉孔直径
                    "inner_diameter": smallest_radius * 2,  # 底孔直径
                    "depth": 20.0,  # 沉孔深度
                    "contour": largest_circle["contour"],  # 使用外圆轮廓
                    "bounding_box": largest_circle["bounding_box"],
                    "area": largest_circle["area"],
                    "confidence": (largest_circle.get("confidence", 0) + smallest_circle.get("confidence", 0)) / 2,
                    "aspect_ratio": largest_circle.get("aspect_ratio", 0)
                }
                
                filtered_features.append(counterbore_feature)
            else:
                # 如果不是沉孔特征，将原始圆形特征添加回列表
                filtered_features.extend(group_features)
        else:
            # 只有一个圆，添加回列表
            filtered_features.extend(group_features)
    
    return filtered_features


def extract_highest_y_center_point(features: List[Dict]) -> Tuple[float, float]:
    """
    提取所有圆形特征中Y坐标最高的圆心点作为坐标原点
    
    Args:
        features: 包含圆形特征的特征列表
    
    Returns:
        Tuple[float, float]: 最高Y坐标圆心点的坐标 (x, y)
    """
    circle_features = [f for f in features if f.get("shape") in ["circle", "counterbore"]]
    if not circle_features:
        return (0.0, 0.0)  # 如果没有圆形特征，返回原点
    
    # 找到Y坐标最小的圆心点（在图像坐标系中，Y越小越靠上）
    highest_point = min(circle_features, key=lambda f: f["center"][1])
    return highest_point["center"]


def adjust_coordinate_system(features: List[Dict], origin: Tuple[float, float], 
                           reference_strategy: str = "absolute", 
                           custom_origin: Tuple[float, float] = None) -> List[Dict]:
    """
    根据指定的坐标原点调整所有特征的坐标
    
    Args:
        features: 特征列表
        origin: 新的坐标原点 (x, y)
        reference_strategy: 坐标基准策略 ("absolute", "relative", "custom", "highest_y")
        custom_origin: 自定义原点坐标，当reference_strategy为"custom"时使用
    
    Returns:
        坐标调整后的特征列表
    """
    adjusted_features = []
    
    # 根据策略确定实际的原点
    actual_origin = origin
    if reference_strategy == "custom" and custom_origin:
        actual_origin = custom_origin
    elif reference_strategy == "highest_y":
        actual_origin = extract_highest_y_center_point(features)
    elif reference_strategy == "relative":
        # 相对坐标策略：以第一个特征的中心点为原点
        if features:
            actual_origin = features[0]["center"]
    
    for feature in features:
        adjusted_feature = feature.copy()
        
        # 调整中心点坐标
        old_center_x, old_center_y = feature["center"]
        new_center_x = old_center_x - actual_origin[0]
        new_center_y = old_center_y - actual_origin[1]
        adjusted_feature["center"] = (new_center_x, new_center_y)
        
        # 调整边界框坐标
        x, y, w, h = feature["bounding_box"]
        adjusted_feature["bounding_box"] = (x - actual_origin[0], y - actual_origin[1], w, h)
        
        adjusted_features.append(adjusted_feature)
    
    return adjusted_features


def select_coordinate_reference(features: List[Dict], strategy: str = "highest_y", 
                              custom_reference: Tuple[float, float] = None) -> Tuple[float, float]:
    """
    根据指定策略选择坐标参考点
    
    Args:
        features: 特征列表
        strategy: 参考点选择策略
                 - "highest_y": Y坐标最高的点
                 - "lowest_y": Y坐标最低的点
                 - "leftmost_x": X坐标最左的点
                 - "rightmost_x": X坐标最右的点
                 - "center": 图纸中心点
                 - "custom": 使用自定义参考点
                 - "geometric_center": 所有特征的几何中心
        
        custom_reference: 自定义参考点坐标
    
    Returns:
        Tuple[float, float]: 选定的参考点坐标
    """
    if strategy == "custom" and custom_reference:
        return custom_reference
    
    if not features:
        return (0.0, 0.0)
    
    if strategy == "highest_y":
        return extract_highest_y_center_point(features)
    elif strategy == "lowest_y":
        return extract_lowest_y_center_point(features)
    elif strategy == "leftmost_x":
        return extract_leftmost_x_point(features)
    elif strategy == "rightmost_x":
        return extract_rightmost_x_point(features)
    elif strategy == "center":
        return calculate_geometric_center(features)
    elif strategy == "geometric_center":
        return calculate_all_features_center(features)
    else:
        # 默认使用最高Y坐标点
        return extract_highest_y_center_point(features)


def extract_highest_y_center_point(features: List[Dict]) -> Tuple[float, float]:
    """
    提取所有圆形特征中Y坐标最高的圆心点作为坐标原点
    
    Args:
        features: 包含圆形特征的特征列表
    
    Returns:
        Tuple[float, float]: 最高Y坐标圆心点的坐标 (x, y)
    """
    circle_features = [f for f in features if f.get("shape") in ["circle", "counterbore"]]
    if not circle_features:
        # 如果没有圆形特征，则在所有特征中查找
        if not features:
            return (0.0, 0.0)
        highest_point = min(features, key=lambda f: f["center"][1])
        return highest_point["center"]
    
    # 找到Y坐标最小的圆心点（在图像坐标系中，Y越小越靠上）
    highest_point = min(circle_features, key=lambda f: f["center"][1])
    return highest_point["center"]


def extract_lowest_y_center_point(features: List[Dict]) -> Tuple[float, float]:
    """
    提取所有特征中Y坐标最低的点作为坐标原点
    
    Args:
        features: 特征列表
    
    Returns:
        Tuple[float, float]: 最低Y坐标点的坐标 (x, y)
    """
    if not features:
        return (0.0, 0.0)
    
    lowest_point = max(features, key=lambda f: f["center"][1])
    return lowest_point["center"]


def extract_leftmost_x_point(features: List[Dict]) -> Tuple[float, float]:
    """
    提取所有特征中X坐标最左的点作为坐标原点
    
    Args:
        features: 特征列表
    
    Returns:
        Tuple[float, float]: 最左X坐标点的坐标 (x, y)
    """
    if not features:
        return (0.0, 0.0)
    
    leftmost_point = min(features, key=lambda f: f["center"][0])
    return leftmost_point["center"]


def extract_rightmost_x_point(features: List[Dict]) -> Tuple[float, float]:
    """
    提取所有特征中X坐标最右的点作为坐标原点
    
    Args:
        features: 特征列表
    
    Returns:
        Tuple[float, float]: 最右X坐标点的坐标 (x, y)
    """
    if not features:
        return (0.0, 0.0)
    
    rightmost_point = max(features, key=lambda f: f["center"][0])
    return rightmost_point["center"]


def calculate_geometric_center(features: List[Dict]) -> Tuple[float, float]:
    """
    计算所有特征的几何中心点作为坐标原点
    
    Args:
        features: 特征列表
    
    Returns:
        Tuple[float, float]: 几何中心点的坐标 (x, y)
    """
    if not features:
        return (0.0, 0.0)
    
    total_x = sum(f["center"][0] for f in features)
    total_y = sum(f["center"][1] for f in features)
    count = len(features)
    
    return (total_x / count, total_y / count)


def calculate_all_features_center(features: List[Dict]) -> Tuple[float, float]:
    """
    计算所有特征边界框的中心点作为坐标原点
    
    Args:
        features: 特征列表
    
    Returns:
        Tuple[float, float]: 所有特征边界框的中心点 (x, y)
    """
    if not features:
        return (0.0, 0.0)
    
    # 计算所有边界框的最小包围矩形
    min_x = min(f["bounding_box"][0] for f in features)
    min_y = min(f["bounding_box"][1] for f in features)
    max_x = max(f["bounding_box"][0] + f["bounding_box"][2] for f in features)
    max_y = max(f["bounding_box"][1] + f["bounding_box"][3] for f in features)
    
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    
    return (center_x, center_y)


def extract_dimensions(features: List[Dict], scale: float = 1.0) -> List[Dict]:
    """
    根据比例尺提取特征的实际尺寸
    
    Args:
        features (list): 识别出的特征列表
        scale (float): 图纸比例尺因子
    
    Returns:
        list: 包含实际尺寸的特征列表
    """
    scaled_features = []
    
    for feature in features:
        scaled_feature = feature.copy()
        
        # 根据比例尺调整尺寸
        if 'length' in scaled_feature:
            scaled_feature['length'] = scaled_feature['length'] * scale
        if 'width' in scaled_feature:
            scaled_feature['width'] = scaled_feature['width'] * scale
        if 'radius' in scaled_feature:
            scaled_feature['radius'] = scaled_feature['radius'] * scale
        if 'dimensions' in scaled_feature:
            w, h = scaled_feature['dimensions']
            scaled_feature['dimensions'] = (w * scale, h * scale)
        
        scaled_features.append(scaled_feature)
    
    return scaled_features


def find_reference_scale(image: np.ndarray, text_regions: List[str]) -> float:
    """
    在图纸中查找比例尺信息
    
    Args:
        image (numpy.ndarray): 输入图像
        text_regions (list): OCR识别出的文本区域
    
    Returns:
        float: 比例尺因子，如果未找到则返回1.0
    """
    # 在文本中查找比例尺信息
    for text in text_regions:
        text_lower = text.lower()
        # 查找比例尺格式，如 1:1, 1:2, 1:5, 1:10, 等
        import re
        scale_match = re.search(r'(\d+):(\d+)', text_lower)
        if scale_match:
            numerator = int(scale_match.group(1))
            denominator = int(scale_match.group(2))
            if denominator != 0:
                return numerator / denominator
    
    # 检查中文比例尺描述
    for text in text_regions:
        text_lower = text.lower()
        if '比例' in text_lower or 'scale' in text_lower:
            scale_match = re.search(r'(\d+):(\d+)', text_lower)
            if scale_match:
                numerator = int(scale_match.group(1))
                denominator = int(scale_match.group(2))
                if denominator != 0:
                    return numerator / denominator
    
    # 如果没有找到明确的比例尺信息，返回默认值
    return 1.0