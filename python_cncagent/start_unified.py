# -*- coding: utf-8 -*-
"""
统一启动文件 - 同时支持GUI界面和Web服务器
提供命令行选项让用户选择启动模式（仅GUI、仅网页、或两者同时启动）

使用方法:
  python start_unified.py                    # 同时启动GUI和Web服务器（默认）
  python start_unified.py gui               # 仅启动GUI界面
  python start_unified.py gui-optimized     # 仅启动优化版GUI界面（AI优先）
  python start_unified.py gui-beautified    # 仅启动美化版GUI界面（简洁设计）
  python start_unified.py web               # 仅启动Web服务器
  python start_unified.py both              # 同时启动标准GUI和Web服务器
  python start_unified.py both-optimized    # 同时启动优化版GUI和Web服务器
  python start_unified.py both-beautified   # 同时启动美化版GUI和Web服务器
"""
import sys
import os

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 如果没有安装dotenv则跳过

import argparse
import threading
import time
import logging
from pathlib import Path
import signal

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cnc_unified.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 添加项目根目录和src目录到Python路径
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(src_path))

# 预加载必要的模块以避免线程间的导入冲突
def preload_modules():
    """预加载所有可能在多线程中使用的模块"""
    try:
        # 预加载Web服务器模块
        import start_server
        logger.info("预加载 start_server 模块成功")
    except ImportError as e:
        logger.warning(f"预加载 start_server 模块失败: {e}")
    
    try:
        # 预加载GUI模块
        from modules.simple_nc_gui import run_gui
        from modules.optimized_cnc_gui import run_optimized_gui
        from modules.beautified_cnc_gui import run_gui as run_beautified_gui
        logger.info("预加载 GUI 模块成功")
    except ImportError as e:
        logger.warning(f"预加载 GUI 模块失败: {e}")
    
    # 预加载主要的模块以避免后续导入冲突
    try:
        import src.modules.fanuc_optimization
        import src.modules.gcode_generation
        import src.modules.ai_driven_generator
        import src.modules.feature_definition
        import src.modules.material_tool_matcher
        import src.modules.pdf_parsing_process
        import src.modules.unified_generator
        logger.info("预加载核心模块成功")
    except ImportError as e:
        logger.warning(f"预加载核心模块失败: {e}")

# 在程序开始时预加载模块
preload_modules()

# 全局变量用于控制服务器线程
web_thread = None

def start_web_server_simple(port=5000, host='0.0.0.0'):
    """启动Flask Web服务器（简化版本）"""
    try:
        # 确保src目录在Python路径中
        project_root = Path(__file__).parent
        src_path = project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 使用延迟导入避免线程冲突
        import start_server
        from start_server import app
        logger.info(f"启动Web服务器，地址: {host}:{port}")
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)
    except ImportError as e:
        logger.error(f"无法导入Web服务器模块: {e}")
        print("错误: 无法启动Web服务器，请确保已安装Flask相关依赖")
        print("运行: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"Web服务器启动失败: {e}")


def start_gui(gui_type="standard"):
    """启动GUI界面"""
    try:
        # 确保src目录在Python路径中
        project_root = Path(__file__).parent
        src_path = project_root / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        
        # 使用延迟导入避免线程冲突
        if gui_type == "optimized":
            from modules.optimized_cnc_gui import run_optimized_gui
            logger.info("启动优化版GUI界面（AI优先模式）...")
            run_optimized_gui()
        elif gui_type == "beautified":
            from modules.beautified_cnc_gui import run_gui
            logger.info("启动美化版GUI界面（简洁设计）...")
            run_gui()
        else:  # standard
            from modules.simple_nc_gui import run_gui
            logger.info("启动GUI界面...")
            run_gui()
    except ImportError as e:
        logger.error(f"无法导入GUI模块: {e}")
        print("错误: 无法启动GUI界面，请确保所有依赖项已安装")
        print("运行: pip install -r requirements.txt")
    except Exception as e:
        logger.error(f"GUI界面启动失败: {e}")


def signal_handler(signum, frame):
    """处理中断信号"""
    global web_thread
    logger.info(f"收到信号 {signum}，正在关闭...")
    if web_thread and web_thread.is_alive():
        logger.info("等待Web服务器线程结束...")
    sys.exit(0)


def main():
    """主入口函数"""
    global web_thread
    
    parser = argparse.ArgumentParser(
        description='CNC Agent 统一启动器 - 同时支持GUI界面和Web服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s                    # 同时启动GUI和Web服务器（默认）
  %(prog)s gui               # 仅启动GUI界面
  %(prog)s gui-optimized     # 仅启动优化版GUI界面（AI优先）
  %(prog)s gui-beautified    # 仅启动美化版GUI界面（简洁设计）
  %(prog)s web               # 仅启动Web服务器
  %(prog)s both              # 同时启动标准GUI和Web服务器
  %(prog)s both-optimized    # 同时启动优化版GUI和Web服务器
  %(prog)s both-beautified   # 同时启动美化版GUI和Web服务器
  %(prog)s web --host 127.0.0.1 --port 3000  # 启动Web服务器在localhost:3000
        """
    )
    parser.add_argument('mode', nargs='?', choices=['gui', 'gui-optimized', 'gui-beautified', 'web', 'both', 'both-optimized', 'both-beautified'], default='both',
                        help='启动模式: gui(标准GUI界面), gui-optimized(优化版GUI界面), gui-beautified(美化版GUI界面), web(仅网页服务器), both(标准GUI+Web服务器), both-optimized(优化版GUI+Web服务器), both-beautified(美化版GUI+Web服务器)')
    parser.add_argument('--port', type=int, default=5000,
                        help='Web服务器端口 (默认: 5000)')
    parser.add_argument('--host', default='0.0.0.0',
                        help='Web服务器主机地址 (默认: 0.0.0.0)')

    args = parser.parse_args()

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    print("=" * 60)
    print("CNC Agent 统一启动器")
    print("=" * 60)
    
    if args.mode == 'gui':
        logger.info("启动模式: 仅GUI界面")
        print("启动模式: 仅GUI界面")
        start_gui("standard")
    elif args.mode == 'gui-optimized':
        logger.info("启动模式: 仅优化版GUI界面（AI优先）")
        print("启动模式: 仅优化版GUI界面（AI优先）")
        start_gui("optimized")
    elif args.mode == 'gui-beautified':
        logger.info("启动模式: 仅美化版GUI界面（简洁设计）")
        print("启动模式: 仅美化版GUI界面（简洁设计）")
        start_gui("beautified")
    elif args.mode == 'web':
        logger.info(f"启动模式: 仅Web服务器 (地址: {args.host}:{args.port})")
        print(f"启动模式: 仅Web服务器")
        print(f"Web服务器地址: http://{args.host}:{args.port}")
        start_web_server_simple(port=args.port, host=args.host)
    elif args.mode == 'both':
        logger.info(f"启动模式: GUI界面 + Web服务器 (地址: {args.host}:{args.port})")
        print(f"启动模式: GUI界面 + Web服务器")
        print(f"Web服务器地址: http://{args.host}:{args.port}")
        print(f"GUI界面将在本地启动...")
        print("-" * 60)
        
        # 创建并启动Web服务器线程
        web_thread = threading.Thread(
            target=start_web_server_simple,
            args=(args.port, args.host),
            name="WebServerThread",
            daemon=True  # 设置为守护线程，主程序退出时自动结束
        )
        web_thread.start()
        
        # 等待Web服务器启动
        time.sleep(2)
        logger.info(f"Web服务器已在 http://{args.host}:{args.port} 启动")
        print(f"✓ Web服务器已在 http://{args.host}:{args.port} 启动")
        print()
        
        # 启动GUI界面（在主线程中）
        start_gui("standard")
        
        # 等待Web服务器线程结束
        try:
            web_thread.join()
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
            sys.exit(0)
    elif args.mode == 'both-optimized':
        logger.info(f"启动模式: 优化版GUI界面 + Web服务器 (地址: {args.host}:{args.port})")
        print(f"启动模式: 优化版GUI界面 + Web服务器")
        print(f"Web服务器地址: http://{args.host}:{args.port}")
        print(f"优化版GUI界面将在本地启动...")
        print("-" * 60)
        
        # 创建并启动Web服务器线程
        web_thread = threading.Thread(
            target=start_web_server_simple,
            args=(args.port, args.host),
            name="WebServerThread",
            daemon=True  # 设置为守护线程，主程序退出时自动结束
        )
        web_thread.start()
        
        # 等待Web服务器启动
        time.sleep(2)
        logger.info(f"Web服务器已在 http://{args.host}:{args.port} 启动")
        print(f"✓ Web服务器已在 http://{args.host}:{args.port} 启动")
        print()
        
        # 启动优化版GUI界面（在主线程中）
        start_gui("optimized")
        
        # 等待Web服务器线程结束
        try:
            web_thread.join()
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
            sys.exit(0)
    elif args.mode == 'both-beautified':
        logger.info(f"启动模式: 美化版GUI界面 + Web服务器 (地址: {args.host}:{args.port})")
        print(f"启动模式: 美化版GUI界面 + Web服务器")
        print(f"Web服务器地址: http://{args.host}:{args.port}")
        print(f"美化版GUI界面将在本地启动...")
        print("-" * 60)
        
        # 创建并启动Web服务器线程
        web_thread = threading.Thread(
            target=start_web_server_simple,
            args=(args.port, args.host),
            name="WebServerThread",
            daemon=True  # 设置为守护线程，主程序退出时自动结束
        )
        web_thread.start()
        
        # 等待Web服务器启动
        time.sleep(2)
        logger.info(f"Web服务器已在 http://{args.host}:{args.port} 启动")
        print(f"✓ Web服务器已在 http://{args.host}:{args.port} 启动")
        print()
        
        # 启动美化版GUI界面（在主线程中）
        start_gui("beautified")
        
        # 等待Web服务器线程结束
        try:
            web_thread.join()
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在关闭...")
            sys.exit(0)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()