"""
几何特征识别模块
从图像中识别几何形状，如圆形、矩形、多边形等，并提取其尺寸和位置信息
注意：此模块现在主要作为AI驱动系统的补充，提供传统图像处理能力
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional, Union
import math
import logging

# 导入配置参数
from src.config import IMAGE_PROCESSING_CONFIG, FEATURE_RECOGNITION_CONFIG, COORDINATE_CONFIG, OCR_CONFIG
from src.exceptions import FeatureRecognitionError, handle_exception

# 导入AI驱动模块和OCR模块
from src.modules.ai_driven_generator import AIDrivenCNCGenerator
from src.modules.ocr_ai_inference import extract_features_from_pdf_with_ai


def identify_features(image: np.ndarray, min_area: float = None, min_perimeter: float = None, 
                      canny_low: int = None, canny_high: int = None, 
                      gaussian_kernel: tuple = None, morph_kernel: tuple = None, 
                      drawing_text: str = "") -> List[Dict]:
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
        drawing_text (str): 图纸OCR文本，用于辅助特征识别
    
    Returns:
        list: 识别出的特征列表，每个特征包含形状、位置、尺寸等信息
    """
    # 使用配置中的默认值（如果参数未指定）
    if min_area is None:
        min_area = IMAGE_PROCESSING_CONFIG['default_min_area']
    if min_perimeter is None:
        min_perimeter = IMAGE_PROCESSING_CONFIG['default_min_perimeter']
    if canny_low is None:
        canny_low = IMAGE_PROCESSING_CONFIG['default_canny_low']
    if canny_high is None:
        canny_high = IMAGE_PROCESSING_CONFIG['default_canny_high']
    if gaussian_kernel is None:
        gaussian_kernel = IMAGE_PROCESSING_CONFIG['default_gaussian_kernel']
    if morph_kernel is None:
        morph_kernel = IMAGE_PROCESSING_CONFIG['default_morph_kernel']
    
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
        
        if shape and confidence > IMAGE_PROCESSING_CONFIG['min_confidence_threshold']:
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
                                except cv2.error:
                                    pass  # 如果拟合失败，忽略椭圆参数
                                except ValueError:
                                    pass  # 如果其他错误，忽略椭圆参数            
            features.append(feature)
    
    # 过滤重复特征
    features = filter_duplicate_features_advanced(features)
    
    # 识别复合孔特征（如沉孔）- 现在使用图纸文本辅助识别
    features = identify_counterbore_features(features, "", drawing_text)
    
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
    if len(contour) >= 5 and area > 0 and circularity < FEATURE_RECOGNITION_CONFIG['circularity_threshold']:
        try:
            # 尝试拟合椭圆
            ellipse = cv2.fitEllipse(contour)
            center, axes, angle = ellipse
            major_axis = max(axes)
            minor_axis = min(axes)
            eccentricity = math.sqrt(1 - (minor_axis / major_axis) ** 2) if major_axis > 0 else 0
            
            # 如果离心率适中（接近椭圆而非圆形），并且形状比较规则
            if (FEATURE_RECOGNITION_CONFIG['ellipse_eccentricity_min'] <= eccentricity <= 
                FEATURE_RECOGNITION_CONFIG['ellipse_eccentricity_max'] and 
                solidity > FEATURE_RECOGNITION_CONFIG['solidity_threshold']):
                return "ellipse", min(1.0, solidity * extent * 0.8)
        except cv2.error:
            pass  # 拟合失败则继续其他形状判断
    
    # 三角形判断
    if num_vertices == 3 and solidity > FEATURE_RECOGNITION_CONFIG['solidity_threshold']:
        return "triangle", min(1.0, solidity * 1.2)
    
    # 四边形判断
    if num_vertices == 4 and solidity > FEATURE_RECOGNITION_CONFIG['solidity_threshold']:
        # 根据长宽比判断正方形还是矩形
        aspect_ratio_tolerance = FEATURE_RECOGNITION_CONFIG['aspect_ratio_tolerance']
        if 1.0 - aspect_ratio_tolerance <= aspect_ratio <= 1.0 + aspect_ratio_tolerance:
            return "square", min(1.0, solidity * extent * 1.5)
        else:
            return "rectangle", min(1.0, solidity * extent * 1.3)
    elif num_vertices == 4 and solidity > FEATURE_RECOGNITION_CONFIG['solidity_threshold'] - 0.1:  # 0.7
        # 可能是平行四边形
        return "parallelogram", min(1.0, solidity * extent * 1.1)
    
    # 圆形判断：使用更广泛的圆形度范围和多条件验证
    if area > 0 and circle_area > 0:
        area_ratio = area / circle_area
        if (FEATURE_RECOGNITION_CONFIG['circularity_threshold'] - 0.1 <= area_ratio <= 
            FEATURE_RECOGNITION_CONFIG['circularity_threshold'] + 0.3 and 
            circularity > FEATURE_RECOGNITION_CONFIG['circularity_threshold'] and 
            solidity > FEATURE_RECOGNITION_CONFIG['solidity_threshold']):
            return "circle", min(1.0, circularity * solidity)
    
    # 多边形判断：顶点数大于4且形状比较规则
    if num_vertices > 4 and num_vertices <= 10 and solidity > FEATURE_RECOGNITION_CONFIG['solidity_threshold']:
        shape_name = f"polygon_{num_vertices}_sides"
        return "polygon", min(1.0, solidity * 0.9)
    
    # 如果无法确定具体形状，但有一定规则性，标记为其他形状
    if solidity > FEATURE_RECOGNITION_CONFIG['solidity_threshold'] + 0.2 and extent > FEATURE_RECOGNITION_CONFIG['extent_threshold']:
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


def identify_counterbore_features(features: List[Dict], user_description: str = "", drawing_text: str = "") -> List[Dict]:
    """
    识别沉孔（Counterbore）特征，即φ22沉孔深20mm + φ14.5贯通底孔的组合特征
    根据机械制图规则，通过几何特征和工程关系进行智能识别
    
    注意：此函数现在主要作为AI驱动系统的补充，
    在AI系统未能充分解析用户需求时提供后备支持
    
    Args:
        features: 识别出的几何特征列表
        user_description: 用户描述，用于辅助判断是否需要识别沉孔特征
        drawing_text: 图纸OCR文本，用于辅助判断沉孔特征
    
    Returns:
        识别后特征列表，包含复合沉孔特征
    """
    # 首先筛选出圆形特征
    circle_features = [f for f in features if f.get("shape") == "circle"]
    
    # 检查用户描述和图纸文本中是否明确提到沉孔加工需求
    user_wants_counterbore = False
    drawing_has_counterbore = False
    
    if user_description:
        description_lower = user_description.lower()
        if "沉孔" in description_lower or "counterbore" in description_lower or "锪孔" in description_lower:
            user_wants_counterbore = True
    
    if drawing_text:
        drawing_lower = drawing_text.lower()
        if "沉孔" in drawing_lower or "counterbore" in drawing_lower or "锪孔" in drawing_lower:
            drawing_has_counterbore = True
    
    # 如果用户明确要求沉孔加工，或图纸文本中包含沉孔信息，则提高识别阈值
    strict_threshold = user_wants_counterbore or drawing_has_counterbore
    
    # 按中心点位置分组可能的沉孔组合（同心圆识别）
    grouped_features = {}
    tolerance = IMAGE_PROCESSING_CONFIG['duplicate_distance_threshold']  # 减小中心点距离容差，单位像素，更精确地匹配同心圆
    
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
    
    # 检查用户描述中的孔数量信息
    import re
    hole_count = OCR_CONFIG['default_hole_count']  # 默认3个孔
    count_matches = re.findall(r'(\d+)\s*个', user_description)
    if count_matches:
        try:
            hole_count = int(count_matches[0])
        except ValueError:
            hole_count = 3
    
    # 检查每个分组是否为同心圆沉孔特征
    counterbore_features = []
    valid_counterbore_groups = []  # 记录已经识别为沉孔的组
    for group_center, group_features in grouped_features.items():
        if len(group_features) >= 2:
            # 按半径排序，找到最大和最小的圆（沉孔和底孔）
            sorted_by_radius = sorted(group_features, key=lambda x: x.get("radius", 0), reverse=True)
            
            # 尝试识别沉孔和底孔
            largest_circle = sorted_by_radius[0]
            smallest_circle = sorted_by_radius[1] if len(sorted_by_radius) > 1 else sorted_by_radius[0]  # 取第二大，如果只有一组则取本身
            
            # 判断是否可能是沉孔特征 (φ22沉孔 + φ14.5底孔)
            largest_radius = largest_circle.get("radius", 0)
            smallest_radius = smallest_circle.get("radius", 0)
            
            # 检查半径比例是否符合沉孔特征
            # φ22沉孔 vs φ14.5底孔，半径比约为 11:7.25 ≈ 1.52
            radius_ratio = largest_radius / smallest_radius if smallest_radius > 0 and smallest_radius != largest_radius else 0
            
            # 根据是否严格要求设置不同的半径比范围
            if strict_threshold:
                # 如果用户明确要求沉孔，使用更精确的范围
                valid_ratio = 1.4 <= radius_ratio <= 1.6  # 针对φ22/φ14.5的情况
            else:
                # 默认范围
                valid_ratio = (FEATURE_RECOGNITION_CONFIG['radius_ratio_min'] <= 
                               radius_ratio <= 
                               FEATURE_RECOGNITION_CONFIG['radius_ratio_max'])
            
            # 检查圆形度以确保是真正的圆形
            largest_circularity = largest_circle.get("circularity", 0)
            smallest_circularity = smallest_circle.get("circularity", 0)
            circularity_threshold = FEATURE_RECOGNITION_CONFIG['solidity_threshold'] if strict_threshold else FEATURE_RECOGNITION_CONFIG['circularity_threshold']  # 如果用户明确要求，降低圆形度要求
            
            if valid_ratio and largest_circularity > circularity_threshold and smallest_circularity > circularity_threshold:
                # 创建沉孔特征 - 这是同心圆沉孔
                counterbore_feature = {
                    "shape": "counterbore",  # 沉孔特征
                    "center": group_center,
                    "outer_radius": largest_radius,  # 沉孔半径
                    "inner_radius": smallest_radius,  # 底孔半径
                    "outer_diameter": largest_radius * 2,  # 沉孔直径
                    "inner_diameter": smallest_radius * 2,  # 底孔直径
                    "depth": 20.0,  # 沉孔深度 - 可以从用户描述或图纸中提取
                    "contour": largest_circle["contour"],  # 使用外圆轮廓
                    "bounding_box": largest_circle["bounding_box"],
                    "area": largest_circle["area"],
                    "confidence": (largest_circle.get("confidence", 0) + smallest_circle.get("confidence", 0)) / 2,
                    "aspect_ratio": largest_circle.get("aspect_ratio", 0),
                    "circularity": largest_circularity
                }
                
                # 从用户描述或图纸中提取深度信息
                depth_from_description = extract_depth_from_description(user_description + " " + drawing_text)
                if depth_from_description is not None:
                    counterbore_feature["depth"] = depth_from_description
                
                # 如果用户要求沉孔加工，或者图纸中提到沉孔，或者没有明确要求但识别到了沉孔特征，则保留
                if user_wants_counterbore or drawing_has_counterbore:
                    # 提高置信度，因为有文本支持
                    counterbore_feature["confidence"] = min(1.0, counterbore_feature["confidence"] + 0.2)
                    counterbore_features.append(counterbore_feature)
                else:
                    # 如果用户没有明确要求沉孔加工，也保留沉孔特征，但降低置信度
                    # 以便在后续处理中可以基于用户需求进行过滤
                    counterbore_feature["confidence"] = min(counterbore_feature["confidence"], 0.6)  # 降低置信度
                    counterbore_features.append(counterbore_feature)
                
                # 记录这个组已经识别为沉孔
                valid_counterbore_groups.append(group_center)
            else:
                # 如果不是同心圆沉孔特征，将原始圆形特征添加回列表
                filtered_features.extend(group_features)
        else:
            # 只有一个圆，添加回列表
            filtered_features.extend(group_features)
    
    # 如果用户明确要求沉孔加工，但没有找到明确的同心圆沉孔特征，
    # 则采用基于工程图纸规则的分度圆分析方法
    if user_wants_counterbore:
        # 查找图纸中的基准特征（如φ234圆）
        baseline_feature = find_baseline_feature(circle_features, drawing_text)
        
        if baseline_feature:
            # 基于基准特征分析分度圆
            pcd_features = analyze_pcd_features(circle_features, baseline_feature, hole_count, user_description)
            
            # 如果找到了分度圆上的特征点，则创建沉孔特征
            if len(pcd_features) >= hole_count:
                # 选择置信度最高的几个作为沉孔位置
                pcd_features = sorted(pcd_features, key=lambda x: x.get("confidence", 0), reverse=True)[:hole_count]
                
                for i, feature in enumerate(pcd_features):
                    # 创建基于分度圆分析的沉孔特征
                    counterbore_feature = {
                        "shape": "counterbore",  # 沉孔特征
                        "center": feature["center"],
                        "outer_radius": 11.0,  # φ22沉孔的半径
                        "inner_radius": 7.25,  # φ14.5底孔的半径
                        "outer_diameter": 22.0,  # 沉孔直径
                        "inner_diameter": 14.5,  # 底孔直径
                        "depth": 20.0,  # 沉孔深度
                        "contour": feature.get("contour", []),
                        "bounding_box": feature.get("bounding_box", (0, 0, 10, 10)),
                        "area": feature.get("area", 380),
                        "confidence": feature.get("confidence", 0.85),  # 基于几何关系的较高置信度
                        "aspect_ratio": feature.get("aspect_ratio", 1.0),
                        "circularity": feature.get("circularity", 0.9)
                    }
                    
                    # 从用户描述或图纸中提取深度信息
                    depth_from_description = extract_depth_from_description(user_description + " " + drawing_text)
                    if depth_from_description is not None:
                        counterbore_feature["depth"] = depth_from_description
                    
                    counterbore_features.append(counterbore_feature)
        
        # 如果通过PCD分析没有找到足够的沉孔特征，或者没有进行PCD分析，则使用基于规则的圆形特征选择
        if len(counterbore_features) < hole_count:
            # 获取还没有被识别为沉孔的圆形特征
            remaining_circles = []
            for group_center, group_features in grouped_features.items():
                if group_center not in [cb["center"] for cb in counterbore_features]:
                    # 添加组中最大半径的圆形
                    sorted_by_radius = sorted(group_features, key=lambda x: x.get("radius", 0), reverse=True)
                    remaining_circles.append(sorted_by_radius[0])
            
            # 如果有太多剩余圆形特征，根据工程图纸规则进行筛选
            # 例如，排除明显是基准圆的特征（通常是最大的圆）
            if baseline_feature and len(remaining_circles) > hole_count:
                # 移除基准特征（如果它被包含在剩余圆形中）
                remaining_circles = [c for c in remaining_circles if c["center"] != baseline_feature["center"]]
            
            if remaining_circles:
                # 根据用户描述中的孔数量选择圆形特征
                remaining_circles = sorted(remaining_circles, key=lambda x: x.get("confidence", 0), reverse=True)
                selected_circles = remaining_circles[:hole_count - len(counterbore_features)]  # 只选择还需要的特征数量
                
                for i, circle in enumerate(selected_circles):
                    # 创建模拟的沉孔特征，使用用户描述中的典型尺寸
                    counterbore_feature = {
                        "shape": "counterbore",  # 沉孔特征
                        "center": circle["center"],
                        "outer_radius": 11.0,  # φ22沉孔的半径
                        "inner_radius": 7.25,  # φ14.5底孔的半径
                        "outer_diameter": 22.0,  # 沉孔直径
                        "inner_diameter": 14.5,  # 底孔直径
                        "depth": 20.0,  # 沉孔深度
                        "contour": circle.get("contour", []),
                        "bounding_box": circle.get("bounding_box", (0, 0, 10, 10)),
                        "area": circle.get("area", 380),
                        "confidence": circle.get("confidence", 0.8),
                        "aspect_ratio": circle.get("aspect_ratio", 1.0),
                        "circularity": circle.get("circularity", 0.9)
                    }
                    
                    # 从用户描述或图纸中提取深度信息
                    depth_from_description = extract_depth_from_description(user_description + " " + drawing_text)
                    if depth_from_description is not None:
                        counterbore_feature["depth"] = depth_from_description
                    
                    # 提高置信度，因为用户明确要求沉孔加工
                    counterbore_feature["confidence"] = min(1.0, counterbore_feature["confidence"] + 0.1)
                    counterbore_features.append(counterbore_feature)
    
    # 根据用户描述的孔数量过滤沉孔特征
    if user_wants_counterbore and counterbore_features:
        # 按置信度排序，只保留用户要求的数量
        counterbore_features = sorted(counterbore_features, key=lambda x: x.get("confidence", 0), reverse=True)
        counterbore_features = counterbore_features[:hole_count]
    
    # 添加沉孔特征到最终列表
    filtered_features.extend(counterbore_features)
    
    # 重要：如果AI优先模式被使用，我们应减少对几何特征的依赖
    # 这里我们只保留那些与用户描述高度匹配的特征
    return filtered_features


def find_baseline_feature(circle_features: List[Dict], drawing_text: str) -> Dict:
    """
    查找图纸基准特征（如φ234圆的圆心）
    
    Args:
        circle_features: 圆形特征列表
        drawing_text: 图纸文本信息
    
    Returns:
        基准特征，如果没有找到则返回None
    """
    import re
    
    # 从图纸文本中查找基准直径信息（如φ234）
    # 优先查找可能的基准直径（通常是较大值）
    baseline_matches = re.findall(r'φ(\d+\.?\d*)', drawing_text)
    if baseline_matches:
        try:
            # 将所有匹配的直径转换为浮点数并排序（降序）
            diameters = [float(d) for d in baseline_matches]
            diameters.sort(reverse=True)  # 从大到小排序，优先匹配大的直径（基准圆）
            
            # 优先匹配最大的直径（通常是基准圆）
            for baseline_diameter in diameters:
                # 查找接近基准直径的圆形特征
                for feature in circle_features:
                    feature_diameter = feature.get("radius", 0) * 2
                    # 允许一定误差范围（如±5%），但优先匹配直径最接近的
                    if abs(feature_diameter - baseline_diameter) <= baseline_diameter * 0.05:
                        return feature
        except ValueError:
            pass
    
    # 如果没有在文本中找到特定的基准直径，返回最大的圆形特征作为可能的基准
    if circle_features:
        return max(circle_features, key=lambda x: x.get("radius", 0))
    
    return None


def analyze_pcd_features(circle_features: List[Dict], baseline_feature: Dict, hole_count: int, user_description: str) -> List[Dict]:
    """
    基于分度圆（PCD）分析特征位置
    
    Args:
        circle_features: 圆形特征列表
        baseline_feature: 基准特征
        hole_count: 预期孔数量
        user_description: 用户描述
    
    Returns:
        分度圆上可能的沉孔特征列表
    """
    import re
    
    # 从用户描述中提取分度圆信息（PCD 188）
    pcd_matches = re.findall(r'PCD\s*(\d+\.?\d*)|(\d+\.?\d*)\s*PCD', user_description)
    pcd_diameter = 188.0  # 默认值
    if pcd_matches:
        try:
            pcd_val = pcd_matches[0][0] if pcd_matches[0][0] else pcd_matches[0][1]
            pcd_diameter = float(pcd_val)
        except (ValueError, IndexError):
            pass
    
    # 从用户描述中提取角度信息（-30, 90, 210）
    # 尝试匹配 "角度-30，90，210" 或 "角度 -30, 90, 210" 这种格式
    angle_pattern1 = r'角度\s*([-\d\s,，.]+)'
    angle_matches1 = re.findall(angle_pattern1, user_description)
    angles = []
    if angle_matches1:
        for angle_match in angle_matches1:
            if angle_match.strip():
                angle_nums = re.findall(r'-?\d+\.?\d*', angle_match)
                try:
                    angles = [float(a) for a in angle_nums if a]
                    if angles:  # 如果找到了角度，就停止
                        break
                except ValueError:
                    continue

    # 如果上面的正则没有找到，尝试另一种格式
    if not angles:
        angle_pattern2 = r'角度[^\d]*([-\d\s,，.\s]+?)(?:[^\d，,\s-]|$)'
        angle_matches2 = re.findall(angle_pattern2, user_description)
        if angle_matches2:
            for angle_match in angle_matches2:
                angle_nums = re.findall(r'-?\d+\.?\d*', angle_match)
                try:
                    angles = [float(a) for a in angle_nums if a]
                    if angles:
                        break
                except ValueError:
                    continue
    
    # 还要支持极坐标格式如 "R=50 θ=30°" 或 "R50θ30" 等
    polar_patterns = [
        r'R\s*[=:]\s*(\d+\.?\d*)\s*(?:θ|theta|角度|θ=|θ:)\s*(\d+\.?\d*)\s*(?:°|度)?',  # R=50 θ=30°
        r'R\s*(\d+\.?\d*)\s*(?:θ|theta|角度)\s*(\d+\.?\d*)\s*(?:°|度)?',  # R50θ30
        r'(?:极径|半径)\s*(\d+\.?\d*)\s*(?:极角|角度)\s*(\d+\.?\d*)\s*(?:°|度)?',  # 极径50 极角30度
    ]
    
    for pattern in polar_patterns:
        polar_matches = re.findall(pattern, user_description, re.IGNORECASE)
        for match in polar_matches:
            try:
                radius = float(match[0])
                angle_deg = float(match[1])
                # 添加到极坐标列表中
                if not angles:
                    angles = [angle_deg]
                    pcd_diameter = radius * 2  # 使用极径作为PCD直径
                else:
                    angles.append(angle_deg)
                    # 如果极径与当前PCD直径差异较大，可能需要处理多个PCD
            except (ValueError, TypeError):
                continue
    
    baseline_center = baseline_feature["center"]
    baseline_x, baseline_y = baseline_center
    pcd_radius = pcd_diameter / 2
    
    # 如果有明确的角度信息，计算预期位置
    if angles and len(angles) >= hole_count:
        expected_positions = []
        for angle in angles[:hole_count]:
            # 将角度转换为弧度
            rad = math.radians(angle)
            # 计算相对于基准点的位置
            pos_x = baseline_x + pcd_radius * math.cos(rad)
            pos_y = baseline_y + pcd_radius * math.sin(rad)
            expected_positions.append((pos_x, pos_y))
        
        # 查找与预期位置最接近的圆形特征
        matched_features = []
        for exp_pos in expected_positions:
            closest_feature = None
            min_dist = float('inf')
            for feature in circle_features:
                center = feature["center"]
                dist = math.sqrt((center[0] - exp_pos[0])**2 + (center[1] - exp_pos[1])**2)
                # 检查距离是否在PCD容差范围内（如PCD半径的10%）
                if dist < pcd_radius * COORDINATE_CONFIG['position_match_tolerance'] and dist < min_dist:
                    min_dist = dist
                    closest_feature = feature            
            if closest_feature:
                matched_features.append(closest_feature)
        
        return matched_features
    else:
        # 如果没有明确的角度信息，查找围绕基准点在PCD半径附近的圆形特征
        # 计算所有圆形特征相对于基准点的距离和角度
        pcd_features = []
        pcd_tolerance = pcd_radius * COORDINATE_CONFIG['polar_coordinate_tolerance']  # 使用PCD半径的15%作为容差
        
        for feature in circle_features:
            center_x, center_y = feature["center"]
            dx = center_x - baseline_x
            dy = center_y - baseline_y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # 检查距离是否接近PCD半径
            if abs(distance - pcd_radius) <= pcd_tolerance:
                # 计算角度信息
                angle_rad = math.atan2(dy, dx)
                angle_deg = math.degrees(angle_rad)
                feature["polar_angle"] = angle_deg  # 添加极坐标角度信息
                pcd_features.append(feature)
        
        # 如果找到的特征数量符合预期，返回这些特征
        if len(pcd_features) >= hole_count:
            # 按距离PCD半径的精确度排序，返回最接近的几个
            pcd_features.sort(key=lambda f: abs(
                math.sqrt((f["center"][0] - baseline_x)**2 + (f["center"][1] - baseline_y)**2) - pcd_radius
            ))
            return pcd_features[:hole_count]
        elif len(pcd_features) > 0:
            # 如果找到的特征数量少于预期，但大于0，返回找到的所有特征
            return pcd_features
    
    return []


def extract_depth_from_description(description: str) -> float:
    """
    从描述文本中提取深度信息
    
    Args:
        description: 用户描述或图纸文本
        
    Returns:
        float: 提取的深度值，如果没有找到则返回None
    """
    import re
    
    # 匹配各种深度格式，如"沉孔深20mm", "深度20", "20mm深"等
    patterns = [
        r'沉孔深(\d+\.?\d*)\s*mm?',
        r'锪孔深(\d+\.?\d*)\s*mm?',
        r'深度\s*(\d+\.?\d*)\s*mm?',
        r'(\d+\.?\d*)\s*mm\s*深',
        r'深\s*(\d+\.?\d*)\s*mm?',
        r'counterbore.*?(\d+\.?\d*)\s*mm',
        r'(\d+\.?\d*)\s*mm.*?counterbore'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, description, re.IGNORECASE)
        if matches:
            try:
                return float(matches[0])
            except ValueError:
                continue
    
    return None


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


def adjust_coordinate_system(features: List[Dict], origin: Tuple[float, float], 
                           reference_strategy: str = "absolute", 
                           custom_origin: Tuple[float, float] = None) -> List[Dict]:
    """
    根据指定的坐标原点调整所有特征的坐标
    
    Args:
        features: 特征列表
        origin: 新的坐标原点 (x, y)
        reference_strategy: 坐标基准策略 ("absolute", "relative", "custom", "highest_y", "lowest_y", "leftmost_x", "rightmost_x", "center", "geometric_center")
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
    elif reference_strategy == "lowest_y":
        actual_origin = extract_lowest_y_center_point(features)
    elif reference_strategy == "leftmost_x":
        actual_origin = extract_leftmost_x_point(features)
    elif reference_strategy == "rightmost_x":
        actual_origin = extract_rightmost_x_point(features)
    elif reference_strategy == "center":
        actual_origin = calculate_geometric_center(features)
    elif reference_strategy == "geometric_center":
        actual_origin = calculate_all_features_center(features)
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