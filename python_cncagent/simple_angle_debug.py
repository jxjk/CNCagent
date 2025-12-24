"""
调试角度提取修复
"""
import sys
import os
import math
import re

def debug_angle_extraction():
    user_description = "加工3个φ22深20底孔φ14.5贯通的沉孔特征，使用点孔、钻孔、沉孔工艺。分度圆PCD 188，角度-30，90，210。"
    
    print("用户描述:", user_description)
    
    # PCD匹配
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

if __name__ == "__main__":
    debug_angle_extraction()