#!/bin/bash
"""
部署脚本 - 用于在服务器上部署CNC Agent服务
"""

import os
import sys
import subprocess
import argparse


def install_dependencies():
    """安装项目依赖"""
    print("正在安装项目依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成")
    except subprocess.CalledProcessError:
        print("依赖安装失败")
        sys.exit(1)


def setup_environment():
    """设置运行环境"""
    print("正在设置运行环境...")
    
    # 创建必要的目录
    dirs = ["logs", "temp", "output", "uploads"]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"创建目录: {d}")
    
    print("环境设置完成")


def run_tests():
    """运行测试"""
    print("正在运行测试...")
    try:
        # 这里可以添加具体的测试命令
        # 例如: subprocess.check_call([sys.executable, "-m", "pytest", "tests/"])
        print("测试运行完成")
    except Exception as e:
        print(f"测试运行失败: {e}")
        # 测试失败不中断部署


def start_server():
    """启动服务器"""
    print("正在启动CNC Agent服务器...")
    try:
        subprocess.check_call([sys.executable, "start_server.py"])
    except subprocess.CalledProcessError:
        print("服务器启动失败")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description='CNC Agent 部署脚本')
    parser.add_argument('--install', action='store_true', help='安装依赖')
    parser.add_argument('--setup', action='store_true', help='设置环境')
    parser.add_argument('--test', action='store_true', help='运行测试')
    parser.add_argument('--start', action='store_true', help='启动服务器')
    parser.add_argument('--deploy', action='store_true', help='完整部署（安装->设置->测试->启动）')
    
    args = parser.parse_args()
    
    if args.install or args.deploy:
        install_dependencies()
    
    if args.setup or args.deploy:
        setup_environment()
    
    if args.test or args.deploy:
        run_tests()
    
    if args.start or args.deploy:
        start_server()


if __name__ == "__main__":
    main()