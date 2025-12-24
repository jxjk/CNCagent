"""
测试修复后的角度提取
"""
import re

def test_angle_extraction():
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。分度圆PCD 188，角度-30，90，210。"
    
    print("用户描述:", user_description)
    
    # 测试第一种正则表达式
    angle_matches1 = re.findall(r'角度[^\d]*([-\d\s,，.\s]+?)(?:[^\d，,\s]|$)', user_description)
    print("第一种匹配结果:", angle_matches1)
    
    # 如果第一种没找到，测试第二种
    angles = []
    if angle_matches1:
        for angle_match in angle_matches1:
            print(f"处理第一种匹配: '{angle_match}'")
            angle_nums = re.findall(r'-?\d+\.?\d*', angle_match)
            print(f"提取到的数字: {angle_nums}")
            try:
                angles = [float(a) for a in angle_nums if a]
                print(f"转换后的角度: {angles}")
                if angles:
                    break
            except ValueError:
                continue
    
    if not angles:
        # 尝试第二种格式
        angle_pattern2 = r'角度\s*([-\d\s,，.]+)'
        angle_matches2 = re.findall(angle_pattern2, user_description)
        print("第二种匹配结果:", angle_matches2)
        if angle_matches2:
            for angle_match in angle_matches2:
                print(f"处理第二种匹配: '{angle_match}'")
                angle_nums = re.findall(r'-?\d+\.?\d*', angle_match)
                print(f"提取到的数字: {angle_nums}")
                try:
                    angles = [float(a) for a in angle_nums if a]
                    print(f"转换后的角度: {angles}")
                    if angles:
                        break
                except ValueError:
                    continue
    
    print(f"最终提取的角度: {angles}")

if __name__ == "__main__":
    test_angle_extraction()