"""
调试孔位置提取的脚本
"""
import re

def debug_hole_position_extraction():
    description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征使用极坐标位置X94.0Y-30. X94.0Y90. X94.0Y210.，使用点孔、钻孔、沉孔工艺。坐标原点（0,0）选择正视图φ234的圆的圆心最高点。"
    
    print(f"原始描述: {description}")
    print()
    
    # 匹配 "X10.0Y-16.0" 格式
    pattern1_general = r'X\s*([+-]?\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)'
    all_matches = re.findall(pattern1_general, description)
    print(f"匹配到的X...Y格式: {all_matches}")
    
    for match in all_matches:
        x = float(match[0])
        y = float(match[1])
        # 检查这个X-Y坐标是否紧跟在φ数字后面
        x_pattern = r'X\s*' + re.escape(match[0])
        x_matches = list(re.finditer(x_pattern, description))
        
        is_valid = True
        for x_match in x_matches:
            # 检查X坐标前是否有"φ数字"模式
            start_search = max(0, x_match.start() - 15)  # 向前搜索15个字符
            preceding_text = description[start_search:x_match.start()]
            # 检查是否有φ+数字的模式
            phi_pattern = r'φ\s*\d+\.?\d*'
            if re.search(phi_pattern, preceding_text):
                print(f"  坐标 ({x}, {y}) 被φ数字模式排除: '{preceding_text.strip()}'")
                is_valid = False
                break
        
        if is_valid and 0 <= abs(x) <= 200 and -200 <= y <= 200:
            print(f"  有效坐标: ({x}, {y})")
        else:
            print(f"  无效坐标或超出范围: ({x}, {y})")

if __name__ == "__main__":
    debug_hole_position_extraction()