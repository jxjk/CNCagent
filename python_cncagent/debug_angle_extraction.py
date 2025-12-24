"""
调试PCD分析过程 - 修复角度提取
"""
import sys
import os
import math
import re
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def debug_angle_extraction():
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。分度圆PCD 188，角度-30，90，210。"
    
    print("用户描述:", user_description)
    
    # 原始的PCD匹配
    pcd_matches = re.findall(r'PCD\s*(\d+\.?\d*)|(\d+\.?\d*)\s*PCD', user_description)
    print("PCD匹配结果:", pcd_matches)
    
    # 修复后的角度匹配
    angle_matches = re.findall(r'角度[^\d]*([-\d\s,，.]+?)(?:[^\d]|$)', user_description)
    print("角度匹配结果:", angle_matches)
    
    angles = []
    if angle_matches:
        for angle_match in angle_matches:
            print(f"处理角度匹配: '{angle_match}'")
            angle_nums = re.findall(r'-?\d+\.?\d*', angle_match)
            print(f"提取到的角度数字: {angle_nums}")
            try:
                angles = [float(a) for a in angle_nums if a]
                print(f"转换后的角度: {angles}")
                break  # 找到第一个角度列表就停止
            except ValueError as e:
                print(f"角度转换错误: {e}")
                continue
    
    print(f"最终提取的角度: {angles}")

def debug_pcd_analysis():
    # 模拟数据
    circle_features = [
        {
            "shape": "circle",
            "center": (500.0, 500.0),  # 基准点
            "radius": 117.0,  # φ234的半径
            "circularity": 0.95,
            "confidence": 0.95,
            "area": 42988,  # π * 117^2
            "bounding_box": (383, 383, 234, 234),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle", 
            "center": (592.0, 406.0),  # 角度-30°: (500 + 94*cos(-30°), 500 + 94*sin(-30°)) ≈ (592, 406)
            "radius": 11.0,  # φ22的半径
            "circularity": 0.92,
            "confidence": 0.90,
            "area": 380,
            "bounding_box": (481, 395, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (500.0, 594.0),  # 角度90°: (500 + 94*cos(90°), 500 + 94*sin(90°)) = (500, 594)
            "radius": 11.0,  # φ22的半径
            "circularity": 0.90,
            "confidence": 0.88,
            "area": 380,
            "bounding_box": (489, 583, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (408.0, 406.0),  # 角度210°: (500 + 94*cos(210°), 500 + 94*sin(210°)) ≈ (408, 406)
            "radius": 11.0,  # φ22的半径
            "circularity": 0.91,
            "confidence": 0.87,
            "area": 380,
            "bounding_box": (397, 395, 22, 22),
            "contour": [],
            "aspect_ratio": 1.0
        },
        {
            "shape": "circle",
            "center": (700.0, 700.0),
            "radius": 5.0,  # 小孔
            "circularity": 0.85,
            "confidence": 0.75,
            "area": 78,
            "bounding_box": (695, 695, 10, 10),
            "contour": [],
            "aspect_ratio": 1.0
        }
    ]
    
    baseline_feature = circle_features[0]  # (500, 500) - φ234基准圆
    hole_count = 3
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。分度圆PCD 188，角度-30，90，210。"
    
    print("\n用户描述:", user_description)
    
    # 手动执行修复后的逻辑
    import re
    
    # PCD匹配
    pcd_matches = re.findall(r'PCD\s*(\d+\.?\d*)|(\d+\.?\d*)\s*PCD', user_description)
    pcd_diameter = 188.0  # 默认值
    if pcd_matches:
        try:
            pcd_val = pcd_matches[0][0] if pcd_matches[0][0] else pcd_matches[0][1]
            pcd_diameter = float(pcd_val)
            print(f"提取到PCD直径: {pcd_diameter}")
        except (ValueError, IndexError):
            print("无法提取PCD直径信息")
    
    # 修复后的角度匹配
    angle_matches = re.findall(r'角度[^\d]*([\-\d\s,，.]+?)(?:[^\d]|$)', user_description)
    angles = []
    if angle_matches:
        for angle_match in angle_matches:
            print(f"角度匹配文本: '{angle_match}'")
            angle_nums = re.findall(r'-?\d+\.?\d*', angle_match)
            print(f"角度数字: {angle_nums}")
            try:
                angles = [float(a) for a in angle_nums if a]
                print(f"最终角度: {angles}")
                break
            except ValueError:
                continue
    
    baseline_center = baseline_feature["center"]
    baseline_x, baseline_y = baseline_center
    pcd_radius = pcd_diameter / 2
    print(f"PCD半径: {pcd_radius}")
    
    if angles and len(angles) >= hole_count:
        print(f"有明确角度信息 {angles}，计算预期位置:")
        expected_positions = []
        for angle in angles[:hole_count]:
            # 将角度转换为弧度
            rad = math.radians(angle)
            # 计算相对于基准点的位置
            pos_x = baseline_x + pcd_radius * math.cos(rad)
            pos_y = baseline_y + pcd_radius * math.sin(rad)
            expected_positions.append((pos_x, pos_y))
            print(f"  角度{angle}° -> 位置({pos_x:.1f}, {pos_y:.1f})")
        
        # 查找与预期位置最接近的圆形特征
        matched_features = []
        for i, exp_pos in enumerate(expected_positions):
            closest_feature = None
            min_dist = float('inf')
            print(f"查找最接近位置{exp_pos}的圆形特征:")
            for j, feature in enumerate(circle_features):
                center = feature["center"]
                dist = math.sqrt((center[0] - exp_pos[0])**2 + (center[1] - exp_pos[1])**2)
                print(f"  特征{j}: {center}, 距离 = {dist:.2f}")
                # 检查距离是否在PCD容差范围内（如PCD半径的10%）
                if dist < pcd_radius * 0.1 and dist < min_dist:  # 9.4的容差
                    min_dist = dist
                    closest_feature = feature
                    print(f"    -> 候选匹配，距离: {dist:.2f}")
            
            if closest_feature:
                matched_features.append(closest_feature)
                print(f"  -> 找到匹配特征: {closest_feature['center']}")
            else:
                print(f"  -> 未找到匹配特征，使用最近的")
                # 再次搜索，找到最近的特征（即使超出容差）
                closest_any = None
                min_any_dist = float('inf')
                for feature in circle_features:
                    center = feature["center"]
                    dist = math.sqrt((center[0] - exp_pos[0])**2 + (center[1] - exp_pos[1])**2)
                    if dist < min_any_dist:
                        min_any_dist = dist
                        closest_any = feature
                if closest_any and min_any_dist < 50:  # 合理的搜索半径
                    matched_features.append(closest_any)
                    print(f"  -> 使用最近特征: {closest_any['center']}, 距离: {min_any_dist:.2f}")
        
        print(f"基于角度的PCD分析找到 {len(matched_features)} 个特征")
        for i, f in enumerate(matched_features):
            print(f"  PCD特征{i+1}: {f['center']}")
    else:
        print("没有明确的角度信息，查找PCD半径附近的特征:")
        pcd_features = []
        pcd_tolerance = pcd_radius * 0.15  # 使用PCD半径的15%作为容差
        
        for i, feature in enumerate(circle_features):
            center_x, center_y = feature["center"]
            dx = center_x - baseline_x
            dy = center_y - baseline_y
            distance = math.sqrt(dx*dx + dy*dy)
            expected_distance = pcd_radius
            dist_diff = abs(distance - expected_distance)
            
            print(f"  特征{i}: {feature['center']}, 距离基准: {distance:.2f}, 与PCD差值: {dist_diff:.2f}")
            
            # 检查距离是否接近PCD半径
            if dist_diff <= pcd_tolerance:
                pcd_features.append(feature)
                print(f"    -> 在PCD范围内 (容差: {pcd_tolerance:.2f})")
        
        print(f"PCD分析找到 {len(pcd_features)} 个特征:")
        for i, f in enumerate(pcd_features):
            print(f"  PCD特征{i+1}: {f['center']}")

if __name__ == "__main__":
    debug_angle_extraction()
    debug_pcd_analysis()
