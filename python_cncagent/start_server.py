#!/usr/bin/env python3
"""
CNCagent startup script
Solving module import issues in Docker container
"""
import sys
import os

# 添加src目录到Python路径，以便能够导入模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app  # 导入Flask应用实例

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 3000))
    
    # 在生产环境中，我们通常会使用像gunicorn这样的WSGI服务器
    # 但对于开发和Docker部署，使用Flask内建服务器是可以的
    app.run(host='0.0.0.0', port=port, debug=False)