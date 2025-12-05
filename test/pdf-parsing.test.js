// test/pdf-parsing.test.js
// PDF解析功能测试

const fs = require('fs');
const path = require('path');
const { pdfParsingProcess } = require('../src/modules/subprocesses/pdfParsingProcess');

describe('PDF解析功能测试', () => {
  let tempPdfPath;

  beforeAll(() => {
    // 使用已创建的CAD图纸PDF文件
    tempPdfPath = path.join(__dirname, 'test_cad_drawing.pdf');
  });

  afterAll(() => {
    // 清理临时文件
    if (fs.existsSync(tempPdfPath)) {
      fs.unlinkSync(tempPdfPath);
    }
  });

  test('应正确解析PDF文件', async () => {
    const result = await pdfParsingProcess(tempPdfPath);
    
    expect(result).toBeDefined();
    expect(result.drawingInfo).toBeDefined();
    expect(result.geometryElements).toBeDefined();
    expect(result.dimensions).toBeDefined();
    expect(result.parsingTime).toBeDefined();
    
    // 验证drawingInfo结构
    expect(result.drawingInfo.fileName).toBe('test_cad_drawing.pdf');
    expect(result.drawingInfo.filePath).toBe(tempPdfPath);
    expect(result.drawingInfo.fileType).toBe('.pdf');
    expect(result.drawingInfo.parsedAt).toBeInstanceOf(Date);
    expect(result.drawingInfo.pageCount).toBe(1);
    expect(result.drawingInfo.dimensions).toBeDefined();
    
    // 验证geometryElements结构
    expect(Array.isArray(result.geometryElements)).toBe(true);
    expect(result.geometryElements.length).toBeGreaterThan(0);
    
    // 验证dimensions结构
    expect(Array.isArray(result.dimensions)).toBe(true);
    // dimensions数组可能为空，因为简单的PDF可能不包含尺寸信息
    // 但结构应该正确
  });

  test('应为PDF文件返回正确的几何元素', async () => {
    const result = await pdfParsingProcess(tempPdfPath);
    
    // 验证PDF文件应包含几何元素和尺寸信息
    expect(Array.isArray(result.geometryElements)).toBe(true);
    expect(Array.isArray(result.dimensions)).toBe(true);
    
    // 验证几何元素的结构
    if (result.geometryElements.length > 0) {
      const firstElement = result.geometryElements[0];
      expect(firstElement.id).toBeDefined();
      expect(firstElement.type).toBeDefined();
    }
    
    // 验证尺寸信息的结构
    if (result.dimensions.length > 0) {
      const firstDimension = result.dimensions[0];
      expect(firstDimension.id).toBeDefined();
      expect(firstDimension.type).toBeDefined();
      expect(firstDimension.value).toBeDefined();
      expect(typeof firstDimension.value).toBe('number');
    }
  });

  test('应为非PDF文件返回不同的几何元素', async () => {
    // 创建一个临时的非PDF文件
    const tempTxtPath = path.join(__dirname, 'test_parsing.txt');
    fs.writeFileSync(tempTxtPath, 'dummy text content for testing');
    
    try {
      const result = await pdfParsingProcess(tempTxtPath);
      
      // 验证非PDF文件的处理
      expect(result).toBeDefined();
      expect(result.drawingInfo.fileName).toBe('test_parsing.txt');
      expect(result.drawingInfo.fileType).toBe('.txt');
      
      // 非PDF文件应该返回简化数据
      expect(Array.isArray(result.geometryElements)).toBe(true);
      expect(result.geometryElements.length).toBe(1);
      expect(result.geometryElements[0].type).toBe('rectangle');
      
      expect(Array.isArray(result.dimensions)).toBe(true);
      expect(result.dimensions.length).toBe(2);
    } finally {
      if (fs.existsSync(tempTxtPath)) {
        fs.unlinkSync(tempTxtPath);
      }
    }
  });

  test('应正确处理无效的文件路径', async () => {
    // 测试null值
    await expect(pdfParsingProcess(null)).rejects.toThrow('文件路径无效');
    
    // 测试数字
    await expect(pdfParsingProcess(123)).rejects.toThrow('文件路径无效');
    
    // 测试对象
    await expect(pdfParsingProcess({})).rejects.toThrow('文件路径无效');
  });

  test('应正确处理不存在的文件', async () => {
    await expect(pdfParsingProcess('nonexistent.pdf')).rejects.toThrow('文件不存在');
  });

  test('应正确处理空字符串路径', async () => {
    await expect(pdfParsingProcess('')).rejects.toThrow('文件路径无效');
  });

  test('应异步处理并返回解析结果', async () => {
    const startTime = Date.now();
    const result = await pdfParsingProcess(tempPdfPath);
    const endTime = Date.now();
    
    // 验证异步处理 - 移除时间限制，因为PDF解析速度取决于实际处理时间
    // expect(endTime - startTime).toBeGreaterThanOrEqual(100); // 至少等待100ms的模拟延迟
    
    // 验证结果
    expect(result).toBeDefined();
    expect(result.drawingInfo).toBeDefined();
    expect(result.geometryElements).toBeDefined();
    expect(result.dimensions).toBeDefined();
    expect(result.parsingTime).toBeDefined();
  });

  test('应正确处理特殊字符文件名', async () => {
    const specialPath = path.join(__dirname, 'test_测试_文件.pdf');
    fs.writeFileSync(specialPath, '%PDF-1.4\n%����\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000103 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n149\n%%EOF');
    
    try {
      const result = await pdfParsingProcess(specialPath);
      
      expect(result.drawingInfo.fileName).toBe('test_测试_文件.pdf');
      expect(result.drawingInfo.filePath).toBe(specialPath);
    } finally {
      if (fs.existsSync(specialPath)) {
        fs.unlinkSync(specialPath);
      }
    }
  });
});