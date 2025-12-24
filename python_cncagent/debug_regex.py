import re

def test_counterbore_diameters(description: str):
    description_lower = description.lower()
    
    # 匹配"φ22深20底孔φ14.5贯通"或类似格式的沉孔描述
    # 使用更精确的模式，确保直径数字出现在沉孔相关上下文中，避免匹配坐标
    patterns = [
        r'(?:加工|沉孔|counterbore|锪孔).*?φ\s*(\d+\.?\d*)\s*(?:沉孔|counterbore|锪孔|深).*?深\s*(?:\d+\.?\d*)\s*(?:mm)?\s*(?:底孔|贯通|thru)?.*?φ\s*(\d+\.?\d*)\s*(?:底孔|thru|贯通)', # 加工φ22沉孔深20 φ14.5底孔/贯通
        r'φ\s*(\d+\.?\d*)\s*(?:沉孔|counterbore|锪孔).*?深\s*(?:\d+\.?\d*)\s*(?:mm)?\s*(?:底孔|贯通|thru)?.*?φ\s*(\d+\.?\d*)\s*(?:底孔|thru|贯通)',  # φ22沉孔深20 φ14.5底孔/贯通
        r'(?:沉孔|counterbore|锪孔).*?φ\s*(\d+\.?\d*).*?深\s*(?:\d+\.?\d*)\s*(?:mm)?\s*(?:底孔|贯通|thru)?.*?φ\s*(\d+\.?\d*)\s*(?:底孔|thru|贯通)',  # 沉孔φ22深20 φ14.5底孔/贯通
        r'(\d+)\s*个.*?φ\s*(\d+\.?\d*)\s*(?:沉孔|counterbore|锪孔).*?深\s*(?:\d+\.?\d*)\s*(?:mm)?.*?底孔\s*φ\s*(\d+\.?\d*)\s*贯通',  # 3个φ22沉孔深20 底孔φ14.5贯通
        r'φ\s*(\d+\.?\d*)\s*深\s*(?:\d+\.?\d*)\s*(?:mm)?\s*(?:沉孔|counterbore|锪孔).*?底孔\s*φ\s*(\d+\.?\d*)\s*贯通',  # φ22深20沉孔 底孔φ14.5贯通
    ]
    
    for i, pattern in enumerate(patterns):
        print(f"Pattern {i+1}: {pattern}")
        matches = re.findall(pattern, description_lower)
        print(f"  Matches: {matches}")
        for match in matches:
            try:
                # 根据匹配的模式，提取外径和内径
                if len(match) >= 3:  # 包含数量的模式
                    outer_diameter = float(match[1])  # 外径
                    inner_diameter = float(match[2])  # 内径
                elif len(match) == 2:  # 外径和内径的模式
                    outer_diameter = float(match[0])
                    inner_diameter = float(match[1])
                else:
                    continue
                print(f"  Extracted: outer={outer_diameter}, inner={inner_diameter}")
                return outer_diameter, inner_diameter
            except (ValueError, IndexError):
                print(f"  Error processing match: {match}")
                continue
        print()
    
    # 如果上述模式没有匹配到，尝试提取描述末尾的直径信息
    # 格式如: "...φ22深20，φ14.5贯通底孔"
    end_patterns = [
        r'φ\s*(\d+\.?\d*)\s*深\s*(?:\d+\.?\d*)\s*(?:mm)?\s*(?:沉孔|counterbore|锪孔|，|\.|;).*?φ\s*(\d+\.?\d*)\s*(?:底孔|thru|贯通|，|\.|;)',
        r'φ\s*(\d+\.?\d*).*?深.*?φ\s*(\d+\.?\d*)\s*(?:底孔|thru|贯通|，|\.|;).*?(?:底孔|thru|贯通)',  # φ22深20，φ14.5贯通底孔
    ]
    
    for i, pattern in enumerate(end_patterns, start=len(patterns)+1):
        print(f"Pattern {i}: {pattern}")
        matches = re.findall(pattern, description_lower)
        print(f"  Matches: {matches}")
        for match in matches:
            try:
                if len(match) == 2:
                    outer_diameter = float(match[0])
                    inner_diameter = float(match[1])
                    print(f"  Extracted: outer={outer_diameter}, inner={inner_diameter}")
                    return outer_diameter, inner_diameter
            except (ValueError, IndexError):
                print(f"  Error processing match: {match}")
                continue
        print()
    
    return None, None

# 测试原始描述
user_description = '沉孔加工，极坐标X94.0 Y-30.，X94.0 Y90.，X94.0 Y210.，φ22深20，φ14.5贯通底孔'
print("Testing description:", user_description)
print()
result = test_counterbore_diameters(user_description)
print(f"Final result: {result}")