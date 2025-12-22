"""
PDF解析和图像预处理模块
负责将PDF转换为图像，并对图像进行预处理以提高OCR和特征识别的准确性
"""
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import numpy as np
import os


def pdf_to_images(pdf_path, dpi=150):  # 降低DPI以兼容性更好
    """
    将PDF转换为高分辨率图像列表
    
    Args:
        pdf_path (str): PDF文件路径
        dpi (int): 输出图像的DPI，默认150
    
    Returns:
        list: PIL图像对象列表
    """
    pdf_document = fitz.open(pdf_path)
    images = []
    
    # 计算缩放矩阵，提高分辨率
    zoom = dpi / 72  # 72是默认DPI
    matrix = fitz.Matrix(zoom, zoom)
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        # 渲染为高分辨率图像
        pix = page.get_pixmap(matrix=matrix)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)
    
    pdf_document.close()
    return images


def preprocess_image(image):
    """
    对图像进行预处理以提高OCR准确性
    注意：当前环境中没有OpenCV，使用PIL进行基本预处理
    
    Args:
        image (PIL.Image): 输入图像
    
    Returns:
        PIL.Image: 预处理后的图像
    """
    # 转换为灰度图
    gray_img = image.convert('L')
    
    return gray_img


def ocr_image(image, lang='chi_sim+eng'):
    """
    对图像进行OCR识别
    
    Args:
        image (PIL.Image): 输入图像
        lang (str): OCR语言，默认中英文
    
    Returns:
        str: 识别出的文本
    """
    # 预处理图像
    processed_img = preprocess_image(image)
    
    # 临时保存图像用于OCR
    temp_path = "temp_ocr.png"
    processed_img.save(temp_path)
    
    try:
        # OCR识别
        text = pytesseract.image_to_string(Image.open(temp_path), lang=lang)
        return text
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)


def extract_text_from_pdf(pdf_path):
    """
    从PDF直接提取文本（如果PDF包含可选择的文本）
    
    Args:
        pdf_path (str): PDF文件路径
    
    Returns:
        str: 提取的文本
    """
    pdf_document = fitz.open(pdf_path)
    all_text = ""
    
    for page_num in range(len(pdf_document)):
        page = pdf_document[page_num]
        all_text += page.get_text()
    
    pdf_document.close()
    return all_text