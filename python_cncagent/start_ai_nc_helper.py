"""
AI辅助NC编程工具启动脚本
提供命令行和图形界面两种使用方式
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """主入口函数"""
    if len(sys.argv) < 2:
        print("AI辅助NC编程工具")
        print("=" * 50)
        print("使用方法:")
        print("  python start_ai_nc_helper.py gui          # 启动图形界面")
        print("  python start_ai_nc_helper.py process      # 处理PDF生成NC代码")
        print("  python start_ai_nc_helper.py demo         # 运行演示")
        print("  python start_ai_nc_helper.py help         # 显示帮助")
        print("=" * 50)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "gui":
        # 启动图形界面
        try:
            import os
            from pathlib import Path
            
            # 确保src目录在Python路径中
            project_root = Path(__file__).parent
            src_path = project_root / "src"
            if str(src_path) not in sys.path:
                sys.path.insert(0, str(src_path))
            
            from modules.simple_nc_gui import run_gui
            print("启动AI辅助NC编程工具界面...")
            run_gui()
        except ImportError as e:
            print(f"无法启动图形界面: {e}")
            print("请确保已安装所有依赖项: pip install -r requirements.txt")
        except Exception as e:
            print(f"启动图形界面时出错: {e}")
    
    elif command == "process":
        # 处理PDF生成NC代码
        if len(sys.argv) < 3:
            print("错误: 需要提供PDF文件路径")
            print("用法: python start_ai_nc_helper.py process <pdf_path> [description] [material]")
            sys.exit(1)
        
        pdf_path = sys.argv[2]
        description = sys.argv[3] if len(sys.argv) > 3 else "自动识别特征并生成NC代码"
        material = sys.argv[4] if len(sys.argv) > 4 else "Aluminum"
        
        try:
            from src.main import generate_nc_with_ai_helper
            print(f"正在处理PDF文件: {pdf_path}")
            print(f"加工描述: {description}")
            print(f"材料类型: {material}")
            
            nc_code = generate_nc_with_ai_helper(pdf_path, description, material)
            
            print("\n生成的NC代码:")
            print("=" * 50)
            print(nc_code)
            print("=" * 50)
            
            # 保存到文件
            output_path = "generated_nc.nc"
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(nc_code)
            print(f"\nNC代码已保存到: {output_path}")
            
        except Exception as e:
            print(f"处理过程中出现错误: {e}")
            import traceback
            traceback.print_exc()
    
    elif command == "demo":
        # 运行演示
        print("AI辅助NC编程工具 - 演示模式")
        print("=" * 50)
        print("此工具包含以下功能:")
        print("1. 快速特征识别 - 自动识别图纸中的几何特征")
        print("2. 智能工艺推荐 - 根据特征推荐合适的加工工艺")
        print("3. 简化NC生成 - 一键生成NC代码")
        print("4. 多格式导出 - 支持多种CAM软件格式")
        print("5. 参数快速调整 - 简单的滑块和下拉菜单")
        print("")
        print("使用 'python start_ai_nc_helper.py gui' 启动图形界面开始使用")
    
    elif command == "help":
        # 显示帮助信息
        print("AI辅助NC编程工具 - 帮助信息")
        print("=" * 50)
        print("命令说明:")
        print("  gui      - 启动图形界面，提供可视化操作")
        print("  process  - 命令行模式处理PDF文件")
        print("  demo     - 运行功能演示")
        print("  help     - 显示此帮助信息")
        print("")
        print("图形界面功能:")
        print("  - 拖拽导入PDF、DXF、DWG等格式文件")
        print("  - 一键识别主要加工特征")
        print("  - 简单确认界面，减少用户操作")
        print("  - 工艺模板拖拽：将预定义工艺直接拖到特征上")
        print("  - 点击特征直接调整相关参数")
        print("  - 支持导出到CamBam、Mastercam、Fusion 360等格式")
        print("")
        print("技术特点:")
        print("  - 插件式架构设计，易于扩展")
        print("  - 基于现有CNCagent项目，稳定可靠")
        print("  - 支持多种材料类型和加工工艺")
        print("  - 内置代码验证功能，确保生成代码的正确性")
    
    else:
        print(f"未知命令: {command}")
        print("使用 'python start_ai_nc_helper.py help' 查看帮助信息")

if __name__ == "__main__":
    main()
