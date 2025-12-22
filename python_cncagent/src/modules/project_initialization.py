"""
项目初始化模块
负责初始化CNC Agent的所有组件
"""
import os
import sys
from pathlib import Path


def initialize_project():
    """
    初始化项目环境
    """
    # 创建必要的目录
    directories = [
        "logs",
        "temp",
        "output",
        "workspace"
    ]
    
    for directory in directories:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f"创建目录: {directory}")
    
    print("项目初始化完成")


def setup_logging():
    """
    设置日志记录
    """
    import logging
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / "cnc_agent.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    print("日志系统已设置")


if __name__ == "__main__":
    initialize_project()
    setup_logging()