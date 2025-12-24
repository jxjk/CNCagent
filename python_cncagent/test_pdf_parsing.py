"""
PDF解析模块的集成测试
测试PDF到图像转换、OCR识别等功能
"""
import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from src.modules.pdf_parsing_process import (
    pdf_to_images, preprocess_image, ocr_image, extract_text_from_pdf
)

class TestPDFParsingIntegration(unittest.TestCase):
    
    def setUp(self):
        """测试前准备"""
        # 创建临时目录用于测试
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """测试后清理"""
        # 清理临时文件
        temp_files = ['temp_ocr.png']
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    @patch('fitz.open')
    def test_pdf_to_images_success(self, mock_fitz_open):
        """测试PDF转图像功能成功情况"""
        # 创建模拟的PDF文档和页面
        mock_page = MagicMock()
        mock_page.get_pixmap.return_value = MagicMock(
            width=800,
            height=600,
            samples=b'\x00' * (800 * 600 * 3)  # 模拟RGB图像数据
        )
        
        mock_document = MagicMock()
        mock_document.__len__.return_value = 1
        mock_document.__getitem__.return_value = mock_page
        
        mock_fitz_open.return_value = mock_document
        
        # 测试PDF转图像
        result = pdf_to_images("test.pdf", dpi=150)
        
        # 验证结果
        self.assertEqual(len(result), 1)
        mock_fitz_open.assert_called_once_with("test.pdf")
    
    @patch('fitz.open')
    def test_pdf_to_images_with_multiple_pages(self, mock_fitz_open):
        """测试PDF转图像功能处理多页PDF"""
        # 创建模拟的多页PDF文档
        mock_pages = [MagicMock(), MagicMock()]
        for mock_page in mock_pages:
            mock_page.get_pixmap.return_value = MagicMock(
                width=800,
                height=600,
                samples=b'\x00' * (800 * 600 * 3)
            )
        
        mock_document = MagicMock()
        mock_document.__len__.return_value = 2
        mock_document.__getitem__.side_effect = mock_pages
        
        mock_fitz_open.return_value = mock_document
        
        # 测试多页PDF转图像
        result = pdf_to_images("test.pdf", dpi=150)
        
        # 应该返回2个图像
        self.assertEqual(len(result), 2)
    
    def test_preprocess_image(self):
        """测试图像预处理功能"""
        from PIL import Image
        import numpy as np
        
        # 创建一个简单的测试图像
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # 执行预处理
        processed_image = preprocess_image(test_image)
        
        # 验证图像已转换为灰度图
        self.assertEqual(processed_image.mode, 'L')
        self.assertEqual(processed_image.size, (100, 100))
    
    @patch('pytesseract.image_to_string')
    @patch('os.remove')
    def test_ocr_image_success(self, mock_remove, mock_ocr):
        """测试OCR图像识别成功情况"""
        from PIL import Image
        
        # 创建一个测试图像
        test_image = Image.new('RGB', (100, 100), color='white')
        mock_ocr.return_value = "测试文本"
        
        # 执行OCR
        result = ocr_image(test_image, lang='chi_sim+eng')
        
        # 验证OCR被调用
        self.assertEqual(result, "测试文本")
        mock_ocr.assert_called_once()
        mock_remove.assert_called_once_with("temp_ocr.png")
    
    @patch('pytesseract.image_to_string')
    @patch('os.remove')
    def test_ocr_image_with_exception(self, mock_remove, mock_ocr):
        """测试OCR图像识别异常情况"""
        from PIL import Image
        
        # 模拟OCR异常
        mock_ocr.side_effect = Exception("OCR Error")
        
        test_image = Image.new('RGB', (100, 100), color='white')
        
        # 执行OCR，应该返回空字符串
        result = ocr_image(test_image, lang='chi_sim+eng')
        
        # 验证返回空字符串
        self.assertEqual(result, "")
        mock_remove.assert_called_once_with("temp_ocr.png")
    
    @patch('fitz.open')
    def test_extract_text_from_pdf_success(self, mock_fitz_open):
        """测试从PDF直接提取文本功能"""
        mock_page = MagicMock()
        mock_page.get_text.return_value = "测试PDF文本内容"
        
        mock_document = MagicMock()
        mock_document.__len__.return_value = 1
        mock_document.__getitem__.return_value = mock_page
        
        mock_fitz_open.return_value = mock_document
        
        # 测试文本提取
        result = extract_text_from_pdf("test.pdf")
        
        # 验证结果
        self.assertEqual(result, "测试PDF文本内容")
        mock_fitz_open.assert_called_once_with("test.pdf")


class TestPDFParsingEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    @patch('fitz.open')
    def test_pdf_to_images_empty_pdf(self, mock_fitz_open):
        """测试空PDF文档"""
        mock_document = MagicMock()
        mock_document.__len__.return_value = 0  # 空PDF
        
        mock_fitz_open.return_value = mock_document
        
        # 测试空PDF转图像
        result = pdf_to_images("empty.pdf", dpi=150)
        
        # 验证返回空列表
        self.assertEqual(result, [])
    
    def test_preprocess_image_different_modes(self):
        """测试不同图像模式的预处理"""
        from PIL import Image
        
        # 测试RGB模式
        rgb_image = Image.new('RGB', (50, 50), color='blue')
        result_rgb = preprocess_image(rgb_image)
        self.assertEqual(result_rgb.mode, 'L')
        
        # 测试RGBA模式
        rgba_image = Image.new('RGBA', (50, 50), color='blue')
        result_rgba = preprocess_image(rgba_image)
        self.assertEqual(result_rgba.mode, 'L')
    
    @patch('pytesseract.image_to_string')
    @patch('os.remove')
    def test_ocr_image_no_text_found(self, mock_remove, mock_ocr):
        """测试OCR未识别到文本的情况"""
        from PIL import Image
        
        # 模拟OCR返回空字符串
        mock_ocr.return_value = ""
        
        test_image = Image.new('RGB', (100, 100), color='white')
        
        result = ocr_image(test_image, lang='chi_sim+eng')
        
        self.assertEqual(result, "")
    
    @patch('pytesseract.pytesseract.tesseract_cmd', r'invalid/path/tesseract.exe')
    @patch('os.remove')
    def test_ocr_image_tesseract_not_found(self, mock_remove):
        """测试Tesseract未找到的情况"""
        from PIL import Image
        import pytesseract
        
        test_image = Image.new('RGB', (100, 100), color='white')
        
        # 这将引发TesseractNotFoundError，但我们已经捕获了异常
        try:
            result = ocr_image(test_image, lang='chi_sim+eng')
            self.assertEqual(result, "")
        except pytesseract.TesseractNotFoundError:
            # 如果Tesseract未找到，返回空字符串
            self.assertEqual(ocr_image(test_image, lang='chi_sim+eng'), "")


if __name__ == '__main__':
    unittest.main()