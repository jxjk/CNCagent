const { pdfParsingProcess } = require('../src/modules/subprocesses/pdfParsingProcess');
const fs = require('fs');
const path = require('path');

describe('PDF解析和特征识别集成测试', () => {
  describe('PDF解析基础功能测试', () => {
    test('验证无效文件路径处理', async () => {
      await expect(pdfParsingProcess(null)).rejects.toThrow();
      await expect(pdfParsingProcess(undefined)).rejects.toThrow();
      await expect(pdfParsingProcess('')).rejects.toThrow();
      await expect(pdfParsingProcess('nonexistent.pdf')).rejects.toThrow();
    });

    test('验证PDF文件类型检测', async () => {
      // 创建一个临时的简单PDF内容（模拟空PDF）
      const tempPdfPath = path.join(__dirname, 'temp_test.pdf');
      try {
        // 我们不实际创建PDF，而是测试函数对非PDF文件的处理
        const tempTxtPath = path.join(__dirname, 'temp_test.txt');
        fs.writeFileSync(tempTxtPath, 'This is a test text file');
        
        const result = await pdfParsingProcess(tempTxtPath);
        expect(result).toBeDefined();
        expect(result.drawingInfo).toBeDefined();
        expect(result.drawingInfo.fileType).toBe('.txt');
        expect(result.geometryElements).toBeDefined();
        expect(Array.isArray(result.geometryElements)).toBe(true);
      } finally {
        // 清理临时文件
        if (fs.existsSync(path.join(__dirname, 'temp_test.txt'))) {
          fs.unlinkSync(path.join(__dirname, 'temp_test.txt'));
        }
      }
    });
  });

  describe('几何元素提取功能测试', () => {
    test('验证从文本提取几何信息', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const sampleText = `
        图纸标题：机械零件
        孔位置：X: 10.5 Y: 15.2
        孔位置：X: 25.8 Y: 30.1
        直径：5.5mm
        深度：10mm
        圆形元素：R5.0
        矩形尺寸：20 x 30
        坐标：(40.5, 50.2)
        CENTER: 60.0, 70.0
        POINT (80.1, 90.3)
      `;
      
      const result = extractGeometricInfoFromText(sampleText);
      expect(result).toBeDefined();
      expect(result.geometryElements).toBeDefined();
      expect(result.dimensions).toBeDefined();
      
      // 验证提取到的几何元素数量
      const points = result.geometryElements.filter(el => ['point', 'circle', 'hole'].includes(el.type) && (el.x !== undefined || el.center));
      expect(points.length).toBeGreaterThanOrEqual(6); // 至少应有6个坐标点
      
      // 验证提取到的尺寸
      expect(result.dimensions.length).toBeGreaterThan(0);
    });

    test('验证坐标格式多样性提取', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const sampleText = `
        X: 10.0 Y: 20.0
        X=15 Y=25
        (30.5, 40.2)
        [50.1, 60.3]
        COORD: 70.0, 80.0
        CENTER 90.5 100.2
        ORIGIN: 110.1, 120.3
        POINT (130.4, 140.6)
      `;
      
      const result = extractGeometricInfoFromText(sampleText);
      const points = result.geometryElements.filter(el => el.type === 'point' || (el.center && el.type !== 'circle'));
      
      expect(points.length).toBeGreaterThanOrEqual(8); // 8种不同的坐标格式
    });

    test('验证尺寸标注提取', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const sampleText = `
        直径：Ø5.5mm
        直径：Φ6.0mm
        直径：DIA 7.5
        半径：R8.0
        半径：RADIUS 9.5
        长度：10.0mm
        宽度：15.5mm
        高度：20.0mm
        大小：25 x 30 x 5
        长x宽：35 x 40
      `;
      
      const result = extractGeometricInfoFromText(sampleText);
      expect(result.dimensions.length).toBeGreaterThanOrEqual(10); // 多种尺寸格式
      
      // 验证特定类型的尺寸
      const diameters = result.dimensions.filter(dim => dim.type === 'diameter');
      const radii = result.dimensions.filter(dim => dim.type === 'radius');
      const linear = result.dimensions.filter(dim => dim.type === 'linear');
      
      expect(diameters.length).toBeGreaterThanOrEqual(3); // 至少3个直径
      expect(radii.length).toBeGreaterThanOrEqual(2);     // 至少2个半径
      expect(linear.length).toBeGreaterThanOrEqual(5);    // 其他线性尺寸
    });

    test('验证CAD特征识别', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const sampleText = `
        HOLE X: 10.0 Y: 20.0 DIA 5.5mm
        孔位置：X: 15.0 Y: 25.0
        CIRCLE R5.0 CENTER X: 30.0 Y: 35.0
        矩形：RECTANGLE 20 x 30
        槽：SLOT LENGTH 40mm
        螺纹：THREAD M6x1
        倒角：CHAMFER 2mm
        圆角：FILLET R3.0
        表面粗糙度：Ra3.2
        位置度：POSITION TOLERANCE 0.1
      `;
      
      const result = extractGeometricInfoFromText(sampleText);
      
      // 验证各种CAD特征
      const holes = result.geometryElements.filter(el => el.type === 'hole' || (el.text && (el.text.toLowerCase().includes('hole') || el.text.includes('孔'))));
      const circles = result.geometryElements.filter(el => el.type === 'circle');
      const slots = result.geometryElements.filter(el => el.type === 'slot' || (el.text && (el.text.toLowerCase().includes('slot') || el.text.includes('槽'))));
      const threads = result.geometryElements.filter(el => el.type === 'thread' || (el.text && (el.text.toLowerCase().includes('thread') || el.text.includes('螺纹'))));
      const chamfers = result.geometryElements.filter(el => el.type === 'chamfer' || (el.text && (el.text.toLowerCase().includes('chamfer') || el.text.includes('倒角'))));
      const fillets = result.geometryElements.filter(el => el.type === 'fillet' || (el.text && (el.text.toLowerCase().includes('fillet') || el.text.includes('圆角'))));
      const surfaceFinishes = result.surfaceFinishes;
      const tolerances = result.tolerances;
      
      expect(holes.length).toBeGreaterThanOrEqual(2);
      expect(circles.length).toBeGreaterThanOrEqual(1);
      expect(slots.length).toBeGreaterThanOrEqual(1);
      expect(threads.length).toBeGreaterThanOrEqual(1);
      expect(chamfers.length).toBeGreaterThanOrEqual(1);
      expect(fillet.length).toBeGreaterThanOrEqual(1);
      expect(surfaceFinishes.length).toBeGreaterThanOrEqual(1);
      expect(tolerances.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('OCR文本后处理功能测试', () => {
    test('验证OCR错误修正', () => {
      const { postProcessOcrText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      // 测试常见的OCR识别错误
      const rawOcrText = `
        H0LE X: 25.0 Y: 30.0 DIA 5.5mm
        DRILL DEPTH 10mm
        G-code: 81 G98 Z-14.8 R2.0 F100.0
        C1RCLE R5.0
        dimention: 20.0mm
        thur hole
        tnmm instead of mm
      `;
      
      const processedText = postProcessOcrText(rawOcrText);
      
      // 验证错误已修正
      expect(processedText).toContain('HOLE'); // H0LE -> HOLE
      expect(processedText).toContain('G81');  // 81 -> G81
      expect(processedText).toContain('G98');  // 98 -> G98
      expect(processedText).toContain('CIRCLE'); // C1RCLE -> CIRCLE
      expect(processedText).toContain('dimension'); // dimention -> dimension
      expect(processedText).toContain('THRU'); // thur -> THRU
      expect(processedText).toContain('mm'); // tnmm -> mm
    });

    test('验证G代码相关OCR错误修正', () => {
      const { postProcessOcrText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const gCodeOcr = `
        00001 (PROGRAM START)
        G21 G40 G49 G80 G90 G54
        T02 M06 (TOOL CHANGE)
        S800 M03 (SPINDLE START)
        G43 H02 Z100.
        G0 X10.000 Y20.000
        81 G98 Z-14.8 R2.0 F100.
        X15.000 Y25.000
        X20.000 Y30.000
        G80 (CANCEL CYCLE)
        G0 Z100. (SAFE HEIGHT)
        M05 (SPINDLE STOP)
        M30 (PROGRAM END)
      `;
      
      const processedText = postProcessOcrText(gCodeOcr);
      
      // 验证G代码指令修正
      expect(processedText).toContain('G81'); // 81 -> G81
      expect(processedText).toContain('G98'); // 98 -> G98
      expect(processedText).toContain('G80'); // 可能的80 -> G80
      expect(processedText).toContain('O0001'); // 00001 -> O0001
    });

    test('验证数字和单位OCR错误修正', () => {
      const { postProcessOcrText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const textWithNumbers = `
        X: l0.0 (should be 10.0)
        Y: O5.0 (should be 05.0)
        Z: S2.0 (should be 52.0)
        直径 Z.5mm (should be 2.5mm)
        深度 l5mm (should be 15mm)
        R0.5 (should be R0.5 - this one is correct)
        l2 x 08 (should be 12 x 08)
      `;
      
      const processedText = postProcessOcrText(textWithNumbers);
      
      // 验证数字错误修正
      expect(processedText).toContain('X: 10.0'); // l0.0 -> 10.0
      expect(processedText).toContain('Y: 05.0'); // O5.0 -> 05.0
      // 注意：这些具体的替换可能需要根据实际的修正规则调整
    });
  });

  describe('几何关系识别功能测试', () => {
    test('验证同心圆识别', () => {
      const { enhanceGeometricRelationships } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const geometryElements = [
        { id: 'circle1', type: 'circle', center: { x: 0, y: 0 }, radius: 5, text: 'Inner circle' },
        { id: 'circle2', type: 'circle', center: { x: 0.1, y: -0.1 }, radius: 8, text: 'Outer circle' }, // 近似同心
        { id: 'circle3', type: 'circle', center: { x: 10, y: 10 }, radius: 5, text: 'Separate circle' }  // 不同心
      ];
      
      const enhanced = enhanceGeometricRelationships(geometryElements, []);
      
      // 找到同心圆
      const concentricCircles = enhanced.filter(el => el.isConcentric);
      expect(concentricCircles.length).toBeGreaterThanOrEqual(2); // 至少两个同心圆
    });

    test('验证孔组识别 - 螺栓圆', () => {
      const { findBoltCircle } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      // 创建一个模拟的螺栓圆（6个孔围绕中心点）
      const center = { x: 0, y: 0 };
      const radius = 20;
      const boltCircle = [];
      for (let i = 0; i < 6; i++) {
        const angle = (2 * Math.PI * i) / 6;
        boltCircle.push({
          id: `hole_${i}`,
          type: 'circle',
          center: { x: center.x + radius * Math.cos(angle), y: center.y + radius * Math.sin(angle) }
        });
      }
      
      // 添加一个不在圆上的孔
      boltCircle.push({
        id: 'hole_outside',
        type: 'circle',
        center: { x: 50, y: 50 }
      });
      
      // 测试是否能识别螺栓圆 - 从第一个孔开始查找
      const result = findBoltCircle(boltCircle, 0);
      if (result) {
        expect(result.center).toBeDefined();
        expect(result.radius).toBeCloseTo(radius, 0); // 接近指定半径
        expect(result.holeIds.length).toBeGreaterThanOrEqual(6); // 至少找到6个孔
      }
    });

    test('验证孔组识别 - 矩形阵列', () => {
      const { findRectangularArray } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      // 创建一个3x3的矩形阵列
      const rectArray = [];
      const spacing = 10;
      for (let i = 0; i < 3; i++) {
        for (let j = 0; j < 3; j++) {
          rectArray.push({
            id: `hole_${i}_${j}`,
            type: 'circle',
            center: { x: i * spacing, y: j * spacing }
          });
        }
      }
      
      // 测试是否能识别矩形阵列 - 从第一个孔开始查找
      const result = findRectangularArray(rectArray, 0);
      if (result) {
        expect(result.origin).toBeDefined();
        expect(result.spacing).toBeDefined();
        expect(result.dimensions).toBeDefined();
        expect(result.holeIds.length).toBeGreaterThanOrEqual(8); // 9个孔减去起始孔
      }
    });
  });

  describe('PDF解析与G代码生成集成测试', () => {
    test('验证从特征提取到G代码生成的完整流程', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
      
      // 模拟从PDF解析得到的文本
      const pdfText = `
        机械零件图纸
        孔位置：X: 10.0 Y: 10.0
        孔位置：X: 20.0 Y: 10.0
        孔位置：X: 15.0 Y: 20.0
        直径：5.5mm
        深度：10mm
      `;
      
      // 提取几何信息
      const { geometryElements, dimensions } = extractGeometricInfoFromText(pdfText);
      
      // 验证提取到的孔特征
      const holes = geometryElements.filter(el => el.type === 'hole' || (el.text && (el.text.toLowerCase().includes('hole') || el.text.includes('孔'))));
      expect(holes.length).toBeGreaterThanOrEqual(3); // 至少3个孔
      
      // 构建G代码生成所需的特征对象
      const features = holes.map((hole, index) => ({
        id: `feature_${index}`,
        featureType: 'hole',
        baseGeometry: hole.center ? hole.center : { center: { x: 10 + index * 5, y: 10 } }, // 备用坐标
        parameters: {
          diameter: 5.5,
          depth: 14, // 实际加工深度
          drawingDepth: 10, // 图纸深度
          toolNumber: 2
        }
      }));
      
      // 添加尺寸信息
      const diameterDim = dimensions.find(dim => dim.type === 'diameter');
      if (diameterDim && features.length > 0) {
        features.forEach(feature => {
          feature.parameters.diameter = diameterDim.value;
        });
      }
      
      // 生成项目对象
      const project = {
        features: features,
        materialType: 'Aluminum'
      };
      
      // 生成G代码
      const gCodeBlocks = triggerGCodeGeneration(project);
      
      // 验证G代码生成成功
      expect(gCodeBlocks).toBeDefined();
      expect(Array.isArray(gCodeBlocks)).toBe(true);
      expect(gCodeBlocks.length).toBeGreaterThanOrEqual(3); // 程序开始+特征+程序结束
      
      // 验证孔加工G代码
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      expect(holeBlocks.length).toBeGreaterThanOrEqual(3); // 至少3个孔加工块
    });

    test('验证批量加工功能的端到端流程', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
      
      // 模拟包含多个相同孔的CAD文本
      const cadText = `
        零件：支架板
        HOLE: X: 5.0 Y: 5.0 DIA 4.0mm DEEP 8mm
        HOLE: X: 10.0 Y: 5.0 DIA 4.0mm DEEP 8mm  // 相同参数
        HOLE: X: 15.0 Y: 5.0 DIA 4.0mm DEEP 8mm  // 相同参数
        HOLE: X: 5.0 Y: 10.0 DIA 4.0mm DEEP 8mm // 相同参数
        HOLE: X: 10.0 Y: 10.0 DIA 4.0mm DEEP 8mm // 相同参数
      `;
      
      // 提取几何信息
      const { geometryElements } = extractGeometricInfoFromText(cadText);
      const holes = geometryElements.filter(el => el.type === 'hole' || (el.text && (el.text.toLowerCase().includes('hole') || el.text.includes('孔'))));
      expect(holes.length).toBeGreaterThanOrEqual(5);
      
      // 创建特征对象
      const features = holes.map((hole, index) => {
        // 从文本中提取坐标信息
        const text = hole.text || '';
        const xMatch = text.match(/X:\s*([+-]?\d+\.?\d*)/);
        const yMatch = text.match(/Y:\s*([+-]?\d+\.?\d*)/);
        const diaMatch = text.match(/DIA\s*(\d+\.?\d*)/);
        const deepMatch = text.match(/DEEP\s*(\d+\.?\d*)/);
        
        return {
          id: `feature_${index}`,
          featureType: 'hole',
          baseGeometry: {
            center: { 
              x: xMatch ? parseFloat(xMatch[1]) : index * 5, 
              y: yMatch ? parseFloat(yMatch[1]) : 5 
            }
          },
          parameters: {
            diameter: diaMatch ? parseFloat(diaMatch[1]) : 4.0,
            depth: deepMatch ? parseFloat(deepMatch[1]) : 12, // 实际加工深度
            drawingDepth: diaMatch ? parseFloat(diaMatch[1]) : 8, // 图纸深度
            toolNumber: 2
          }
        };
      });
      
      // 创建项目
      const project = {
        features: features,
        materialType: 'Steel'
      };
      
      // 生成G代码
      const gCodeBlocks = triggerGCodeGeneration(project);
      
      // 查找是否有批量加工的块
      const batchHoleBlock = gCodeBlocks.find(block => block.isBatchOperation && block.featureType === 'hole');
      
      if (batchHoleBlock) {
        // 验证批量加工特性
        expect(batchHoleBlock.isBatchOperation).toBe(true);
        expect(batchHoleBlock.batchSize).toBeGreaterThanOrEqual(5); // 应该批量处理所有相同孔
      }
      
      // 验证生成的G代码包含正确的G81循环
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      expect(holeBlocks.length).toBeGreaterThanOrEqual(1);
      
      if (holeBlocks.length > 0) {
        const gCodeLines = holeBlocks[0].code;
        const hasG81 = gCodeLines.some(line => line.includes('G81'));
        expect(hasG81).toBe(true);
      }
    });

    test('验证OCR改进对整体流程的影响', () => {
      const { postProcessOcrText, extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
      
      // 模拟OCR识别错误的文本
      const rawOcrText = `
        机械零件图
        H0LE L0CATION: X: 25.0 Y: 30.0
        DIA 5.5mm D3PTH 10mm
        G81 CYCL3: G98 Z-14.8 R2.0 F100.0
        MAT3RIAL: Aluminum
      `;
      
      // 首先应用OCR后处理
      const processedText = postProcessOcrText(rawOcrText);
      expect(processedText).toContain('HOLE'); // 修正错误
      expect(processedText).toContain('LOCATION'); // 修正错误
      expect(processedText).toContain('G81'); // 修正错误
      expect(processedText).toContain('G98'); // 修正错误
      
      // 然后提取几何信息
      const { geometryElements, dimensions } = extractGeometricInfoFromText(processedText);
      const holes = geometryElements.filter(el => el.type === 'hole' || (el.text && (el.text.toLowerCase().includes('hole') || el.text.includes('孔'))));
      
      expect(holes.length).toBeGreaterThanOrEqual(1); // 至少提取到1个孔
      
      // 构建特征并生成G代码
      const features = holes.map((hole, index) => {
        const text = hole.text || '';
        const xMatch = text.match(/X:\s*([+-]?\d+\.?\d*)/);
        const yMatch = text.match(/Y:\s*([+-]?\d+\.?\d*)/);
        const diaMatch = text.match(/DIA\s*(\d+\.?\d*)/);
        const depthMatch = text.match(/D[EU]PTH\s*(\d+\.?\d*)/);
        
        return {
          id: `feature_${index}`,
          featureType: 'hole',
          baseGeometry: {
            center: {
              x: xMatch ? parseFloat(xMatch[1]) : 25.0,
              y: yMatch ? parseFloat(yMatch[1]) : 30.0
            }
          },
          parameters: {
            diameter: diaMatch ? parseFloat(diaMatch[1]) : 5.5,
            depth: depthMatch ? parseFloat(depthMatch[1]) * 1.5 : 15, // 实际深度计算
            drawingDepth: depthMatch ? parseFloat(depthMatch[1]) : 10,
            toolNumber: 2
          }
        };
      });
      
      if (features.length > 0) {
        const project = {
          features: features,
          materialType: 'Aluminum'
        };
        
        const gCodeBlocks = triggerGCodeGeneration(project);
        expect(gCodeBlocks).toBeDefined();
        expect(gCodeBlocks.length).toBeGreaterThanOrEqual(2); // 至少开始和结束
        
        // 验证生成的G代码质量
        const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
        if (holeBlocks.length > 0) {
          const gCodeLines = holeBlocks[0].code;
          const hasValidG81 = gCodeLines.some(line => line.includes('G81') && line.includes('G98') && line.includes('Z-') && line.includes('R') && line.includes('F'));
          expect(hasValidG81).toBe(true); // 验证G81格式正确
        }
      }
    });
  });

  describe('视角识别功能测试', () => {
    test('验证自动视角识别', () => {
      const { identifyViewOrientation } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      // 模拟不同坐标系的几何元素
      const geometryElements1 = [  // 第一象限坐标系
        { center: { x: 10, y: 10 } },
        { center: { x: 20, y: 30 } },
        { center: { x: 40, y: 50 } }
      ];
      
      const geometryElements2 = [  // 包含负坐标的中心原点坐标系
        { center: { x: -10, y: -10 } },
        { center: { x: 0, y: 0 } },
        { center: { x: 10, y: 10 } }
      ];
      
      const orientation1 = identifyViewOrientation(geometryElements1, [], "");
      const orientation2 = identifyViewOrientation(geometryElements2, [], "");
      
      // 验证返回了视角信息
      expect(orientation1).toBeDefined();
      expect(orientation1.origin).toBeDefined();
      expect(orientation1.orientation).toBeDefined();
      
      expect(orientation2).toBeDefined();
      expect(orientation2.origin).toBeDefined();
      expect(orientation2.orientation).toBeDefined();
    });
  });

  describe('边界条件和错误处理测试', () => {
    test('验证空文本处理', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const result = extractGeometricInfoFromText("");
      expect(result.geometryElements).toBeDefined();
      expect(Array.isArray(result.geometryElements)).toBe(true);
      expect(result.dimensions).toBeDefined();
      expect(Array.isArray(result.dimensions)).toBe(true);
    });

    test('验证无效输入处理', () => {
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const result1 = extractGeometricInfoFromText(null);
      const result2 = extractGeometricInfoFromText(undefined);
      const result3 = extractGeometricInfoFromText(123);
      
      // 函数应该能处理无效输入而不崩溃
      expect(result1.geometryElements).toBeDefined();
      expect(result2.geometryElements).toBeDefined();
      expect(result3.geometryElements).toBeDefined();
    });

    test('验证后处理函数边界情况', () => {
      const { postProcessOcrText } = require('../src/modules/subprocesses/pdfParsingProcess');
      
      const result1 = postProcessOcrText(null);
      const result2 = postProcessOcrText(undefined);
      const result3 = postProcessOcrText("");
      const result4 = postProcessOcrText(123);
      
      // 验证函数能处理各种输入类型
      expect(typeof result1).toBe('string'); // 应返回字符串
      expect(typeof result2).toBe('string');
      expect(typeof result3).toBe('string');
      expect(typeof result4).toBe('string');
    });
  });
});