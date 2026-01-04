import pytest
import sys
from pathlib import Path
import numpy as np
import cv2
import tempfile
import os

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from resource_manager import ResourceManager, resource_manager, managed_pdf_document, managed_image_file


class TestResourceManager:
    """测试资源管理器类"""
    
    def test_resource_manager_initialization(self):
        """测试资源管理器初始化"""
        manager = ResourceManager()
        assert isinstance(manager, ResourceManager)
        assert manager.opened_resources == []
        
    def test_pdf_document_context_manager(self):
        """测试PDF文档上下文管理器"""
        try:
            import fitz  # 尝试导入PyMuPDF
        except ImportError:
            # 如果库不可用，跳过此测试
            pytest.skip("PyMuPDF库不可用，跳过PDF测试")
        
        # 在Windows环境下，PyMuPDF可能无法处理临时文件，跳过此测试
        import platform
        if platform.system().lower() == "windows":
            pytest.skip("在Windows环境下跳过PDF测试（PyMuPDF临时文件权限问题）")
        
        manager = ResourceManager()
        
        # 首先创建一个临时PDF文件用于测试
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
            
            try:
                # 创建一个简单的PDF文件
                doc = fitz.open()
                page = doc.new_page()
                page.insert_text((50, 50), "Test PDF for resource management")
                doc.save(tmp_path)
                doc.close()
            
                # 检查初始状态
                assert len(manager.opened_resources) == 0
                
                # 使用PDF文档上下文管理器
                with manager.pdf_document(tmp_path) as doc:
                    # 检查资源是否被添加
                    assert len(manager.opened_resources) == 1
                    assert f"PDF: {tmp_path}" in manager.opened_resources
                    
                    # 验证文档对象有效
                    assert doc.page_count == 1
                
                # 检查资源是否被清理
                assert len(manager.opened_resources) == 0
            finally:
                # 清理临时文件
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except:
                    pass  # 如果无法删除文件，跳过（可能被PyMuPDF锁定）
    
    def test_pdf_document_context_manager_error(self):
        """测试PDF文档上下文管理器错误处理"""
        manager = ResourceManager()
        
        # 尝试打开不存在的PDF文件
        fake_path = "nonexistent.pdf"
        assert len(manager.opened_resources) == 0
        
        with pytest.raises(Exception):
            with manager.pdf_document(fake_path) as doc:
                pass  # 这里应该抛出异常
        
        # 确保资源列表仍然为空（即使出错也清理了）
        assert len(manager.opened_resources) == 0
    
    def test_image_file_context_manager(self):
        """测试图像文件上下文管理器"""
        manager = ResourceManager()
        
        # 创建一个临时图像文件用于测试
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            
            # 创建一个简单的图像
            img = np.zeros((100, 100, 3), dtype=np.uint8)
            img.fill(255)  # 白色图像
            cv2.imwrite(tmp_path, img)
        
        try:
            # 检查初始状态
            assert len(manager.opened_resources) == 0
            
            # 使用图像文件上下文管理器
            with manager.image_file(tmp_path) as img:
                # 检查资源是否被添加
                assert len(manager.opened_resources) == 1
                assert f"Image: {tmp_path}" in manager.opened_resources
                
                # 验证图像对象有效
                assert img is not None
                assert img.shape == (100, 100, 3)
            
            # 检查资源是否被清理
            assert len(manager.opened_resources) == 0
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    def test_image_file_context_manager_error(self):
        """测试图像文件上下文管理器错误处理"""
        manager = ResourceManager()
        
        # 尝试打开不存在的图像文件
        fake_path = "nonexistent.png"
        assert len(manager.opened_resources) == 0
        
        with pytest.raises(Exception):
            with manager.image_file(fake_path) as img:
                pass  # 这里应该抛出异常
        
        # 确保资源列表仍然为空（即使出错也清理了）
        assert len(manager.opened_resources) == 0
    
    def test_temporary_array_context_manager(self):
        """测试临时数组上下文管理器"""
        manager = ResourceManager()
        
        # 创建一个数组
        arr = np.array([1, 2, 3, 4, 5])
        
        # 使用临时数组上下文管理器
        with manager.temporary_array(arr) as managed_arr:
            # 验证数组对象有效
            assert managed_arr is arr  # 应该是同一个对象
            assert np.array_equal(managed_arr, arr)
    
    def test_get_active_resources(self):
        """测试获取活跃资源列表"""
        manager = ResourceManager()
        
        # 初始状态
        active = manager.get_active_resources()
        assert active == []
        assert len(active) == 0
        
        # 模拟添加一些资源（注意：这仅用于测试get_active_resources方法）
        manager.opened_resources.append("Resource 1")
        manager.opened_resources.append("Resource 2")
        
        active = manager.get_active_resources()
        assert len(active) == 2
        assert "Resource 1" in active
        assert "Resource 2" in active
        
        # 验证返回的是副本
        active.append("Resource 3")
        assert len(manager.opened_resources) == 2  # 原列表未被修改
    
    def test_cleanup_all(self):
        """测试清理所有资源"""
        manager = ResourceManager()
        
        # 添加一些虚拟资源
        manager.opened_resources.append("Resource 1")
        manager.opened_resources.append("Resource 2")
        
        # 验证资源存在
        assert len(manager.opened_resources) == 2
        
        # 执行清理
        manager.cleanup_all()
        
        # 验证资源被清理
        assert len(manager.opened_resources) == 0


class TestGlobalResourceManager:
    """测试全局资源管理器"""
    
    def test_global_resource_manager_exists(self):
        """测试全局资源管理器存在"""
        assert resource_manager is not None
        assert isinstance(resource_manager, ResourceManager)
        
    def test_global_resource_manager_singleton(self):
        """测试全局资源管理器实例存在"""
        manager2 = ResourceManager()
        # 验证全局实例存在
        assert resource_manager is not None
        assert isinstance(resource_manager, ResourceManager)
        # 验证新创建的实例与全局实例不同
        assert resource_manager is not manager2


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_managed_pdf_document(self):
        """测试便捷的PDF文档管理函数"""
        try:
            import fitz  # 尝试导入PyMuPDF
        except ImportError:
            # 如果库不可用，跳过此测试
            pytest.skip("PyMuPDF库不可用，跳过PDF测试")
        
        # 在Windows环境下，PyMuPDF可能无法处理临时文件，跳过此测试
        import platform
        if platform.system().lower() == "windows":
            pytest.skip("在Windows环境下跳过PDF测试（PyMuPDF临时文件权限问题）")
        
        # 首先创建一个临时PDF文件用于测试
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            tmp_path = tmp.name
            
            try:
                # 创建一个简单的PDF文件
                doc = fitz.open()
                page = doc.new_page()
                page.insert_text((50, 50), "Test PDF for convenience function")
                doc.save(tmp_path)
                doc.close()
            
                # 使用便捷函数
                with managed_pdf_document(tmp_path) as doc:
                    # 验证文档对象有效
                    assert doc.page_count == 1
                    assert len(resource_manager.opened_resources) == 1  # 检查全局管理器
                
                # 验证资源被清理
                assert len(resource_manager.opened_resources) == 0
            finally:
                # 清理临时文件
                try:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
                except:
                    pass  # 如果无法删除文件，跳过（可能被PyMuPDF锁定）
    
    def test_managed_image_file(self):
        """测试便捷的图像文件管理函数"""
        # 创建一个临时图像文件用于测试
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
            
            # 创建一个简单的图像
            img = np.zeros((50, 50, 3), dtype=np.uint8)
            img.fill(128)  # 灰色图像
            cv2.imwrite(tmp_path, img)
        
        try:
            # 使用便捷函数
            with managed_image_file(tmp_path) as img:
                # 验证图像对象有效
                assert img is not None
                assert img.shape == (50, 50, 3)
                assert len(resource_manager.opened_resources) == 1  # 检查全局管理器
            
            # 验证资源被清理
            assert len(resource_manager.opened_resources) == 0
            
        finally:
            # 清理临时文件
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)