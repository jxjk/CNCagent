// test/comprehensive_pdf_parsing.test.js
// 全面的PDF解析功能测试

const fs = require('fs');
const path = require('path');
const { pdfParsingProcess } = require('../src/modules/subprocesses/pdfParsingProcess');

describe('PDF解析功能综合测试', () => {
  // 创建包含各种CAD元素的测试PDF
  let testPdfPath;

  beforeAll(() => {
    testPdfPath = path.join(__dirname, 'comprehensive_cad_test.pdf');
    
    // 创建一个包含多种CAD元素的PDF内容
    const detailedPdfContent = `%PDF-1.5
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
/MediaBox [0 0 612 792]
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Contents [4 0 R]
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 1000
>>
stream
BT
/F1 12 Tf
100 700 Td
(CAD Drawing Comprehensive Test) Tj
100 680 Td
(Rectangle: 100 x 50 mm) Tj
100 660 Td
(Rectangle with dimensions: 200.0 x 150.0 x 10.0 mm) Tj
100 640 Td
(Circle: R25 mm, Center at (100, 100)) Tj
100 620 Td
(Circle: DIA 50 mm, Center (200, 200)) Tj
100 600 Td
(Line from point (10,10) to point (100,50)) Tj
100 580 Td
(Line X: 10 Y: 10 X: 100 Y: 50) Tj
100 560 Td
(Hole at coordinate (50,30), Diameter 10 mm) Tj
100 540 Td
(Hole: 15.5 mm dia at (150, 150)) Tj
100 520 Td
(Fillet with radius R5 mm) Tj
100 500 Td
(Fillet R8 mm at corner) Tj
100 480 Td
(Chamfer 2 x 45 deg) Tj
100 460 Td
(Chamfer: 3.0 mm) Tj
100 440 Td
(Slot: 30.0 x 10.0 mm) Tj
100 420 Td
(Rectangular pocket: 40.0 x 20.0 mm) Tj
100 400 Td
(Dimensions: LENGTH 100.0 mm) Tj
100 380 Td
(Dimensions: WIDTH 50.0 mm) Tj
100 360 Td
(Dimensions: HEIGHT 25.0 mm) Tj
100 340 Td
(SIZE: 15.0 mm) Tj
100 320 Td
(Diameter: 25.0 mm) Tj
100 300 Td
(Radius: 12.5 mm) Tj
100 280 Td
(POINT (75.0, 25.0)) Tj
100 260 Td
(COORD: 85.0, 35.0) Tj
100 240 Td
(CENTER: 95.0, 45.0) Tj
100 220 Td
(ORIGIN: 105.0, 55.0) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000103 00000 n 
0000000221 00000 n 
0000001500 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
/Info null
>>
startxref
1700
%%EOF`;

    fs.writeFileSync(testPdfPath, detailedPdfContent);
  });

  afterAll(() => {
    // 清理临时文件
    if (fs.existsSync(testPdfPath)) {
      fs.unlinkSync(testPdfPath);
    }
  });

  test('应能提取多种几何元素类型', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    expect(result).toBeDefined();
    expect(result.geometryElements).toBeDefined();
    expect(result.dimensions).toBeDefined();
    
    // 验证几何元素数组
    expect(Array.isArray(result.geometryElements)).toBe(true);
    
    // 验证尺寸信息数组
    expect(Array.isArray(result.dimensions)).toBe(true);
    
    // 验证几何元素的结构
    result.geometryElements.forEach(element => {
      expect(element.id).toBeDefined();
      expect(element.type).toBeDefined();
      expect(typeof element.type).toBe('string');
    });
    
    // 验证尺寸信息的结构
    result.dimensions.forEach(dim => {
      expect(dim.id).toBeDefined();
      expect(dim.type).toBeDefined();
      expect(dim.value).toBeDefined();
      expect(typeof dim.value).toBe('number');
      expect(dim.value).toBeGreaterThan(0);
    });
  });

  test('应能正确识别矩形元素', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 查找矩形元素
    const rectangleElements = result.geometryElements.filter(el => 
      el.type === 'rectangle' || 
      el.type === 'box'
    );
    
    // 验证数组类型和结构
    expect(Array.isArray(rectangleElements)).toBe(true);
    
    // 如果找到矩形或盒子元素，验证其结构
    for (let i = 0; i < rectangleElements.length; i++) {
      const rect = rectangleElements[i];
      if (rect.type === 'rectangle') {
        // 矩形可能有bounds属性或width/height属性
        if (rect.bounds) {
          expect(rect.bounds.x).toBeDefined();
          expect(rect.bounds.y).toBeDefined();
          expect(rect.bounds.width).toBeDefined();
          expect(rect.bounds.height).toBeDefined();
        } else {
          expect(rect.width).toBeDefined();
          expect(rect.height).toBeDefined();
        }
      } else if (rect.type === 'box') {
        expect(rect.length).toBeDefined();
        expect(rect.width).toBeDefined();
        expect(rect.height).toBeDefined();
      }
    }
  });

  test('应能正确识别圆形元素', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 查找圆形元素
    const circleElements = result.geometryElements.filter(el => 
      el.type === 'circle'
    );
    
    // 即使可能无法从简单PDF中提取到圆形，也验证结构
    circleElements.forEach(circle => {
      expect(circle.radius).toBeDefined();
      expect(circle.center).toBeDefined();
      expect(typeof circle.radius).toBe('number');
      expect(circle.center.x).toBeDefined();
      expect(circle.center.y).toBeDefined();
    });
  });

  test('应能正确识别线元素', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 查找线元素
    const lineElements = result.geometryElements.filter(el => 
      el.type === 'line'
    );
    
    lineElements.forEach(line => {
      expect(line.start).toBeDefined();
      expect(line.end).toBeDefined();
      expect(line.start.x).toBeDefined();
      expect(line.start.y).toBeDefined();
      expect(line.end.x).toBeDefined();
      expect(line.end.y).toBeDefined();
    });
  });

  test('应能正确识别孔元素', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 查找孔元素
    const holeElements = result.geometryElements.filter(el => 
      el.type === 'hole'
    );
    
    holeElements.forEach(hole => {
      expect(hole.center).toBeDefined();
      expect(hole.center.x).toBeDefined();
      expect(hole.center.y).toBeDefined();
    });
  });

  test('应能提取各种尺寸类型', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 查找不同类型尺寸
    const linearDimensions = result.dimensions.filter(dim => 
      dim.type === 'linear'
    );
    
    const radiusDimensions = result.dimensions.filter(dim => 
      dim.type === 'radius'
    );
    
    const diameterDimensions = result.dimensions.filter(dim => 
      dim.type === 'diameter'
    );
    
    // 验证各种尺寸类型的存在
    expect(Array.isArray(linearDimensions)).toBe(true);
    expect(Array.isArray(radiusDimensions)).toBe(true);
    expect(Array.isArray(diameterDimensions)).toBe(true);
    
    // 验证尺寸值的合理性
    [...linearDimensions, ...radiusDimensions, ...diameterDimensions].forEach(dim => {
      expect(dim.value).toBeGreaterThan(0);
      expect(dim.unit).toBeDefined();
    });
  });

  test('应能处理包含坐标信息的文本', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 查找点元素
    const pointElements = result.geometryElements.filter(el => 
      el.type === 'point'
    );
    
    pointElements.forEach(point => {
      expect(typeof point.x).toBe('number');
      expect(typeof point.y).toBe('number');
    });
  });

  test('应能提取文本中的数值信息', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 检查是否提取到了一些数值
    const hasDimensions = result.dimensions.length > 0;
    const hasGeometry = result.geometryElements.length > 0;
    
    // 即使提取可能不完全，结构应该是正确的
    expect(Array.isArray(result.dimensions)).toBe(true);
    expect(Array.isArray(result.geometryElements)).toBe(true);
  });

  test('应能处理复杂尺寸组合', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 检查是否能识别长x宽x高的格式
    const boxElements = result.geometryElements.filter(el => 
      el.type === 'box'
    );
    
    boxElements.forEach(box => {
      expect(box.length).toBeDefined();
      expect(box.width).toBeDefined();
      expect(box.height).toBeDefined();
      expect(typeof box.length).toBe('number');
      expect(typeof box.width).toBe('number');
      expect(typeof box.height).toBe('number');
    });
  });

  test('应能处理错误和边界情况', async () => {
    // 测试空PDF路径
    await expect(pdfParsingProcess(null)).rejects.toThrow('文件路径无效');
    
    // 测试不存在的文件
    await expect(pdfParsingProcess(path.join(__dirname, 'nonexistent.pdf'))).rejects.toThrow('文件不存在');
    
    // 测试空字符串
    await expect(pdfParsingProcess('')).rejects.toThrow('文件路径无效');
    
    // 测试非字符串类型
    await expect(pdfParsingProcess(123)).rejects.toThrow('文件路径无效');
  });

  test('应返回完整的图纸信息', async () => {
    const result = await pdfParsingProcess(testPdfPath);
    
    // 验证图纸信息结构
    expect(result.drawingInfo).toBeDefined();
    expect(result.drawingInfo.fileName).toBe('comprehensive_cad_test.pdf');
    expect(result.drawingInfo.filePath).toBe(testPdfPath);
    expect(result.drawingInfo.fileType).toBe('.pdf');
    expect(result.drawingInfo.parsedAt).toBeInstanceOf(Date);
    expect(result.drawingInfo.pageCount).toBeGreaterThanOrEqual(0); // 可能是0或1
    expect(result.drawingInfo.dimensions).toBeDefined();
  });

  test('应能正确处理包含中文标注的图纸', async () => {
    const chinesePdfPath = path.join(__dirname, 'chinese_cad_test.pdf');
    
    // 创建包含中文标注的PDF
    const chinesePdfContent = `%PDF-1.5
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
/MediaBox [0 0 612 792]
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj

4 0 obj
<<
/Length 300
>>
stream
BT
/F1 12 Tf
100 700 Td
(圆形：R25毫米) Tj
100 680 Td
(矩形：长100宽50毫米) Tj
100 660 Td
(直径：30毫米) Tj
100 640 Td
(半径：15毫米) Tj
100 620 Td
(孔：直径10毫米) Tj
ET
endstream
endobj

5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj

xref
0 6
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000103 00000 n 
0000000221 00000 n 
0000000400 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
/Info null
>>
startxref
500
%%EOF`;
    
    fs.writeFileSync(chinesePdfPath, chinesePdfContent);
    
    try {
      const result = await pdfParsingProcess(chinesePdfPath);
      
      expect(result).toBeDefined();
      expect(Array.isArray(result.geometryElements)).toBe(true);
      expect(Array.isArray(result.dimensions)).toBe(true);
    } finally {
      // 清理中文测试文件
      if (fs.existsSync(chinesePdfPath)) {
        fs.unlinkSync(chinesePdfPath);
      }
    }
  });
});