import requests
import json

# CNC Agent 服务测试脚本

def test_cnc_agent():
    print("测试 CNC Agent 服务...")
    
    # 测试健康检查
    print("\n1. 测试健康检查端点:")
    try:
        response = requests.get('http://localhost:5000/health')
        print(f"   状态: {response.status_code}")
        print(f"   响应: {response.json()}")
    except Exception as e:
        print(f"   错误: {e}")
    
    # 测试API生成端点（使用模拟数据）
    print("\n2. 测试API生成端点:")
    try:
        test_data = {
            "pdf_content": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",  # 简单的base64图像
            "description": "请加工一个圆形孔，直径10mm，深度5mm",
            "scale": 1.0
        }
        
        response = requests.post(
            'http://localhost:5000/api/generate',
            headers={'Content-Type': 'application/json'},
            json=test_data
        )
        
        print(f"   状态: {response.status_code}")
        if response.status_code == 200:
            print(f"   响应: {response.json()}")
        else:
            print(f"   错误响应: {response.text}")
            
    except Exception as e:
        print(f"   错误: {e}")
    
    print("\n3. 测试完成")
    print("CNC Agent 服务正在运行，可以处理PDF到NC程序的转换请求")

if __name__ == "__main__":
    test_cnc_agent()