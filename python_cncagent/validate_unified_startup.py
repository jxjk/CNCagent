"""
验证统一启动文件的测试脚本
"""
import argparse
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_argument_parsing():
    """测试参数解析功能"""
    import start_unified
    
    # 创建参数解析器
    parser = argparse.ArgumentParser(
        description='CNC Agent 统一启动器 - 同时支持GUI界面和Web服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                    # 同时启动GUI和Web服务器（默认）
  %(prog)s gui               # 仅启动GUI界面
  %(prog)s web               # 仅启动Web服务器
  %(prog)s both --port 8080  # 同时启动，Web服务器使用8080端口
        """
    )
    parser.add_argument('mode', nargs='?', choices=['gui', 'web', 'both'], default='both',
                        help='启动模式: gui(仅GUI界面), web(仅网页服务器), both(两者都启动)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Web服务器端口 (默认: 5000)')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Web服务器主机地址 (默认: 0.0.0.0)')
    
    # 测试不同的参数组合
    test_cases = [
        ([], {'mode': 'both', 'port': 5000, 'host': '0.0.0.0'}),  # 默认
        (['gui'], {'mode': 'gui', 'port': 5000, 'host': '0.0.0.0'}),  # GUI模式
        (['web'], {'mode': 'web', 'port': 5000, 'host': '0.0.0.0'}),  # Web模式
        (['both'], {'mode': 'both', 'port': 5000, 'host': '0.0.0.0'}),  # Both模式
        (['web', '--port', '8080'], {'mode': 'web', 'port': 8080, 'host': '0.0.0.0'}),  # 自定义端口
        (['web', '--host', '127.0.0.1', '--port', '3000'], {'mode': 'web', 'port': 3000, 'host': '127.0.0.1'}),  # 自定义主机和端口
    ]
    
    print("测试参数解析功能...")
    for i, (args, expected) in enumerate(test_cases, 1):
        parsed = parser.parse_args(args)
        actual = {'mode': parsed.mode, 'port': parsed.port, 'host': parsed.host}
        
        if actual == expected:
            print(f"  Test {i}: PASS - Args: {args}, Expected: {expected}, Actual: {actual}")
        else:
            print(f"  Test {i}: FAIL - Args: {args}, Expected: {expected}, Actual: {actual}")
    
    print("Parameter parsing test completed!")

if __name__ == "__main__":
    test_argument_parsing()