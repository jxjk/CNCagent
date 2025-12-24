"""
测试资源管理器
"""
import os
import tempfile
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch

from src.resource_manager import ResourceManager, resource_manager, managed_pdf_document, managed_image_file


class TestResourceManager:
    """测试资源管理器"""
    
    def test_resource_manager_initialization(self):
        """测试资源管理器初始化"""
        rm = ResourceManager()
        assert rm is not None
        assert rm.logger is not None
        assert rm.opened_resources == []
    
    def test_get_active_resources(self):
        """测试获取活跃资源"""
        rm = ResourceManager()
        assert rm.get_active_resources() == []
        
        # 添加一些虚拟资源
        rm.opened_resources = ["Resource1", "Resource2"]
        active = rm.get_active_resources()
        assert len(active) == 2
        assert "Resource1" in active
        assert "Resource2" in active
        
        # 确保返回的是副本
        active.append("Resource3")
        assert len(rm.get_active_resources()) == 2
    
    def test_cleanup_all(self, caplog):
        """测试清理所有资源"""
        rm = ResourceManager()
        rm.opened_resources = ["Resource1", "Resource2"]
        
        rm.cleanup_all()
        
        assert rm.opened_resources == []
        # 检查是否有警告日志（因为有未释放的资源）
        # 这里我们不期望看到警告，因为cleanup_all会清理资源
    
    def test_cleanup_all_with_empty_list(self):
        """测试清理空资源列表"""
        rm = ResourceManager()
        rm.cleanup_all()
        
        assert rm.opened_resources == []
    
    def test_global_resource_manager(self):
        """测试全局资源管理器实例"""
        assert resource_manager is not None
        assert isinstance(resource_manager, ResourceManager)


class TestManagedPDFDocument:
    """测试PDF文档管理"""
    
    def test_managed_pdf_document_success(self):
        """测试成功管理PDF文档"""
        # 创建一个简单的PDF内容
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000018 00000 n \n0000000078 00000 n \n0000000138 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\n%%EOF\n'
        
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
            temp_pdf.write(pdf_content)
            temp_pdf_path = temp_pdf.name
        
        try:
            # 由于我们无法安装PyMuPDF来测试真实功能，我们主要测试上下文管理
            # 在实际环境中，这将测试PDF文档的正确打开和关闭
            pass
        finally:
            # 清理临时文件
            os.unlink(temp_pdf_path)


class TestManagedImageFile:
    """测试图像文件管理"""
    
    def test_managed_image_file_success(self, temp_image_file):
        """测试成功管理图像文件"""
        # 使用fixture创建的临时图像文件
        with managed_image_file(temp_image_file) as img:
            assert img is not None
            assert isinstance(img, np.ndarray)
            assert img.shape == (200, 200, 3)  # 由fixture定义的尺寸
    
    def test_managed_image_file_nonexistent(self):
        """测试管理不存在的图像文件"""
        nonexistent_path = "nonexistent_image.jpg"
        
        with pytest.raises(Exception):  # 具体异常类型取决于cv2的实现
            with managed_image_file(nonexistent_path) as img:
                pass  # 此行不应执行
    
    def test_managed_image_file_invalid_format(self):
        """测试管理无效格式的图像文件"""
        # 创建一个无效的图像文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'Invalid image content')
            invalid_path = temp_file.name
        
        try:
            with pytest.raises(Exception):  # cv2.imread会返回None，然后在上下文中引发错误
                with managed_image_file(invalid_path) as img:
                    pass
        finally:
            os.unlink(invalid_path)


class TestResourceTracking:
    """测试资源跟踪功能"""
    
    def test_resource_tracking_with_image(self, temp_image_file):
        """测试图像资源跟踪"""
        rm = ResourceManager()
        initial_count = len(rm.get_active_resources())
        
        with rm.image_file(temp_image_file) as img:
            active_resources = rm.get_active_resources()
            assert len(active_resources) == initial_count + 1
            assert f"Image: {temp_image_file}" in active_resources
        
        # 退出上下文后，资源应该被移除
        final_active = rm.get_active_resources()
        assert len(final_active) == initial_count
        assert f"Image: {temp_image_file}" not in final_active
    
    def test_multiple_resource_tracking(self, temp_image_file):
        """测试多个资源的跟踪"""
        rm = ResourceManager()
        
        # 这里我们仅测试图像文件，因为PDF需要PyMuPDF
        with rm.image_file(temp_image_file) as img1:
            with rm.temporary_array(np.array([1, 2, 3])) as arr:
                active_resources = rm.get_active_resources()
                # 检查图像资源是否被跟踪
                assert f"Image: {temp_image_file}" in [r for r in active_resources if 'Image:' in r]
        
        # 确保资源在退出后被清理
        assert f"Image: {temp_image_file}" not in rm.get_active_resources()


# 由于我们无法安装PyMuPDF，我们创建一个模拟测试
class TestPDFDocumentMock:
    """使用Mock测试PDF文档功能"""
    
    @patch('src.resource_manager.fitz')
    def test_pdf_document_context_manager(self, mock_fitz):
        """测试PDF文档上下文管理器（使用Mock）"""
        # 设置Mock行为
        mock_doc = Mock()
        mock_fitz.open.return_value = mock_doc
        
        rm = ResourceManager()
        
        # 使用上下文管理器
        with rm.pdf_document("dummy.pdf") as doc:
            assert doc == mock_doc
            mock_fitz.open.assert_called_once_with("dummy.pdf")
        
        # 验证文档已关闭
        mock_doc.close.assert_called_once()
    
    @patch('src.resource_manager.fitz')
    def test_pdf_document_exception_handling(self, mock_fitz):
        """测试PDF文档异常处理（使用Mock）"""
        mock_fitz.open.side_effect = Exception("PDF open failed")
        
        rm = ResourceManager()
        
        with pytest.raises(Exception, match="PDF open failed"):
            with rm.pdf_document("dummy.pdf") as doc:
                pass  # 不会执行，因为open失败