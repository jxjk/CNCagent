"""
几何特征识别模块 - 优化版本
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
    
    # 多尺度边缘检测以提高准确性
    edges = cv2.Canny(blurred, canny_low, canny_high)
    
    # 只进行闭操作，保留边缘
    kernel = np.ones(morph_kernel, np.uint8)
    edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    # 移除开操作，因为可能去除有用边缘信息

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
            y_overlap = max(0, min(curr_y + curr_h, exist_y + exist_h) - max(curr_y, exist_y))
            overlap_area = x_overlap * y_overlap
            
            # 计算并集面积
            union_area = curr_w * curr_h + exist_w * exist_h - overlap_area
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