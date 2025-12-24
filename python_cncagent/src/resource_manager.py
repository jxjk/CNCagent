"""
资源管理器
统一管理文件句柄、图像数据等资源
"""
import logging
import gc
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Any, Optional
import fitz  # PyMuPDF
import cv2
import numpy as np


class ResourceManager:
    """
    资源管理器类
    统一管理各种资源的生命周期
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.opened_resources = []
    
    @contextmanager
    def pdf_document(self, pdf_path: str) -> Generator[fitz.Document, None, None]:
        """
        PDF文档资源管理器
        
        Args:
            pdf_path: PDF文件路径
            
        Yields:
            fitz.Document: PDF文档对象
        """
        doc = None
        try:
            doc = fitz.open(pdf_path)
            self.opened_resources.append(f"PDF: {pdf_path}")
            yield doc
        except Exception as e:
            self.logger.error(f"打开PDF文档失败 {pdf_path}: {e}")
            raise
        finally:
            if doc:
                doc.close()
                if f"PDF: {pdf_path}" in self.opened_resources:
                    self.opened_resources.remove(f"PDF: {pdf_path}")
    
    @contextmanager
    def image_file(self, image_path: str) -> Generator[np.ndarray, None, None]:
        """
        图像文件资源管理器
        
        Args:
            image_path: 图像文件路径
            
        Yields:
            np.ndarray: 图像数组
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图像文件: {image_path}")
            
            self.opened_resources.append(f"Image: {image_path}")
            yield image
        except Exception as e:
            self.logger.error(f"读取图像文件失败 {image_path}: {e}")
            raise
        finally:
            if f"Image: {image_path}" in self.opened_resources:
                self.opened_resources.remove(f"Image: {image_path}")
    
    @contextmanager
    def temporary_array(self, array: np.ndarray) -> Generator[np.ndarray, None, None]:
        """
        临时数组资源管理器
        
        Args:
            array: NumPy数组
            
        Yields:
            np.ndarray: 输入的数组
        """
        try:
            yield array
        finally:
            # 在某些情况下强制垃圾回收
            gc.collect()
    
    def cleanup_all(self):
        """
        清理所有未释放的资源
        """
        if self.opened_resources:
            self.logger.warning(f"发现未释放的资源: {self.opened_resources}")
            # 尝试清理
            self.opened_resources.clear()
            gc.collect()
    
    def get_active_resources(self) -> list:
        """
        获取当前活跃的资源列表
        
        Returns:
            list: 活跃资源列表
        """
        return self.opened_resources.copy()


# 创建全局资源管理器实例
resource_manager = ResourceManager()


# 便捷函数
@contextmanager
def managed_pdf_document(pdf_path: str) -> Generator[fitz.Document, None, None]:
    """便捷的PDF文档管理函数"""
    with resource_manager.pdf_document(pdf_path) as doc:
        yield doc


@contextmanager
def managed_image_file(image_path: str) -> Generator[np.ndarray, None, None]:
    """便捷的图像文件管理函数"""
    with resource_manager.image_file(image_path) as img:
        yield img