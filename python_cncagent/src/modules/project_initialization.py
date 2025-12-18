"""
项目初始化模块，负责创建和管理项目实例
"""
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
import uuid


class Project:
    """项目类定义"""
    def __init__(self, name: str = "New Project"):
        self.id = self._generate_id()
        self.name = name
        self.file_path = None
        self.drawing_info = None
        self.geometry_elements = []
        self.dimensions = []
        self.features = []
        self.gcode_blocks = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.workspace_path = None
        self.material_type = None  # 添加材料类型属性
        self.collision_warnings = []  # 添加碰撞警告属性

    def _generate_id(self) -> str:
        """生成唯一ID"""
        return f"proj_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"

    def update_metadata(self):
        """更新元数据"""
        self.updated_at = datetime.now()

    def serialize(self) -> Dict[str, Any]:
        """将项目对象序列化为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'file_path': self.file_path,
            'drawing_info': self.drawing_info,
            'geometry_elements': self.geometry_elements,
            'dimensions': self.dimensions,
            'features': self.features,
            'gcode_blocks': self.gcode_blocks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'workspace_path': self.workspace_path,
            'material_type': self.material_type,
            'collision_warnings': self.collision_warnings
        }


def initialize_project(project_name: str = "New Project") -> Project:
    """
    初始化项目
    
    Args:
        project_name: 项目名称
        
    Returns:
        Project: 初始化的项目对象
    """
    if not isinstance(project_name, str):
        raise ValueError('项目名必须是字符串')

    project = Project(project_name)
    project.workspace_path = os.path.join(os.path.dirname(__file__), '..', '..', 'workspace', project.id)
    
    # 创建工作目录
    os.makedirs(project.workspace_path, exist_ok=True)
    
    return project


def clear_workspace():
    """
    清理工作区
    """
    workspace_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'workspace')
    if os.path.exists(workspace_dir):
        for project_dir in os.listdir(workspace_dir):
            full_path = os.path.join(workspace_dir, project_dir)
            if os.path.isdir(full_path):
                import shutil
                shutil.rmtree(full_path, ignore_errors=True)


def handle_drawing_import(file_path: str) -> Project:
    """
    处理图纸导入
    
    Args:
        file_path: 文件路径
        
    Returns:
        Project: 包含导入文件信息的项目对象
    """
    if not file_path or not isinstance(file_path, str):
        raise ValueError('文件路径无效')

    # 检查文件是否存在
    if not os.path.exists(file_path):
        raise ValueError(f'文件不存在: {file_path}')

    # 模拟文件导入处理
    file_extension = os.path.splitext(file_path)[1].lower()
    valid_extensions = ['.pdf', '.dxf', '.svg', '.dwg', '.step', '.iges']
    
    if file_extension not in valid_extensions:
        raise ValueError(f'不支持的文件格式: {file_extension}')

    # 创建项目实例
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    project = initialize_project(file_name)
    project.file_path = file_path
    project.update_metadata()

    return project


if __name__ == "__main__":
    # 测试代码
    test_project = initialize_project("Test Project")
    print(f"创建项目: {test_project.name} (ID: {test_project.id})")
    print(f"工作空间路径: {test_project.workspace_path}")