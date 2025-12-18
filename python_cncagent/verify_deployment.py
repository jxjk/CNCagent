"""
部署验证脚本 - 验证Docker部署准备就绪
"""
import os
import subprocess
import sys


def check_docker():
    """检查Docker是否可用"""
    try:
        result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker已安装: {result.stdout.strip()}")
            return True
        else:
            print("✗ Docker未安装或不可用")
            return False
    except FileNotFoundError:
        print("✗ Docker命令未找到")
        return False


def check_docker_compose():
    """检查Docker Compose是否可用"""
    try:
        result = subprocess.run(['docker-compose', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Docker Compose已安装: {result.stdout.strip()}")
            return True
        else:
            print("✗ Docker Compose未安装或不可用")
            return False
    except FileNotFoundError:
        print("✗ Docker Compose命令未找到")
        return False


def check_files():
    """检查必要的部署文件"""
    required_files = [
        'Dockerfile',
        'docker-compose.yml',
        'requirements.txt',
        'src/main.py'
    ]
    
    all_present = True
    for file in required_files:
        if os.path.exists(file):
            print(f"✓ {file} 存在")
        else:
            print(f"✗ {file} 缺失")
            all_present = False
    
    return all_present


def main():
    print("="*50)
    print("CNCagent Docker部署准备检查")
    print("="*50)
    
    docker_ok = check_docker()
    compose_ok = check_docker_compose()
    files_ok = check_files()
    
    print("\n" + "="*50)
    print("检查结果:")
    
    if docker_ok:
        print("✓ Docker环境: 可用")
    else:
        print("✗ Docker环境: 不可用")
    
    if compose_ok:
        print("✓ Docker Compose环境: 可用")
    else:
        print("✗ Docker Compose环境: 不可用")
    
    if files_ok:
        print("✓ 部署文件: 完整")
    else:
        print("✗ 部署文件: 不完整")
    
    print("\n部署说明:")
    print("1. 使用Docker Compose部署: docker-compose up -d")
    print("2. 或使用Docker命令部署:")
    print("   - docker build -t cncagent:latest .")
    print("   - docker run -d --name cncagent -p 3000:3000 cncagent:latest")
    print("3. 访问应用: http://localhost:3000")
    
    if docker_ok and files_ok:
        print("\n🎉 环境已准备好部署CNCagent!")
        return True
    else:
        print("\n❌ 环境未准备好部署，请先解决上述问题")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
