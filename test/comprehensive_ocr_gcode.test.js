const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
const { pdfParsingProcess } = require('../src/modules/subprocesses/pdfParsingProcess');
const fs = require('fs');
const path = require('path');

describe('OCR识别功能和钻孔固定循环G代码生成综合测试', () => {
  describe('OCR识别功能改进验证', () => {
    test('验证OCR文本后处理功能', () => {
      // 测试OCR后处理函数
      const ocrText = "H0LE X10.0 Y20.0 DIA 5.5mm Z-14.0 81 G98 Z-14.8 R2.0 F100.";
      const processedText = require('../src/modules/subprocesses/pdfParsingProcess').postProcessOcrText(ocrText);
      
      // 验证OCR错误修正
      expect(processedText).toContain('HOLE');  // H0LE -> HOLE
      expect(processedText).toContain('G81');   // 81 -> G81
      expect(processedText).toContain('G98');   // 98 -> G98
    });

    test('验证坐标和尺寸提取功能', () => {
      const sampleText = `
        X: 10.5 Y: 15.2
        HOLE位置 X: 25.0 Y: 30.0
        直径 5.5mm 深度 14mm
        R10.5
        10 x 20 x 5 长x宽x高
      `;
      
      const { geometryElements, dimensions } = require('../src/modules/subprocesses/pdfParsingProcess').extractGeometricInfoFromText(sampleText);
      
      // 验证坐标提取
      const points = geometryElements.filter(el => el.type === 'point');
      expect(points.length).toBeGreaterThanOrEqual(2);
      
      // 验证尺寸提取
      expect(dimensions.length).toBeGreaterThan(0);
      const diameters = dimensions.filter(dim => dim.type === 'diameter');
      expect(diameters.length).toBeGreaterThanOrEqual(1);
    });

    test('验证多语言OCR支持', () => {
      const sampleText = `
        孔位置 X: 30.0 Y: 40.0
        直径 6.0mm
        深度 12mm
        HOLE X: 50.0 Y: 60.0
        DIA 7.0mm
      `;
      
      const { geometryElements } = require('../src/modules/subprocesses/pdfParsingProcess').extractGeometricInfoFromText(sampleText);
      const holes = geometryElements.filter(el => el.type === 'hole' || el.text.toLowerCase().includes('hole') || el.text.includes('孔'));
      
      expect(holes.length).toBeGreaterThanOrEqual(2);
    });

    test('验证几何元素关系识别', () => {
      const geometryElements = [
        { id: 'circle1', type: 'circle', center: { x: 0, y: 0 }, radius: 5 },
        { id: 'circle2', type: 'circle', center: { x: 0, y: 0 }, radius: 8 }, // 同心圆
        { id: 'circle3', type: 'circle', center: { x: 10, y: 10 }, radius: 5 }
      ];
      
      const { enhanceGeometricRelationships } = require('../src/modules/subprocesses/pdfParsingProcess');
      const enhancedElements = enhanceGeometricRelationships(geometryElements, []);
      
      // 验证同心圆识别
      const concentricCircles = enhancedElements.filter(el => el.isConcentric);
      expect(concentricCircles.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('钻孔固定循环G代码格式验证', () => {
    test('验证标准钻孔固定循环G81格式', () => {
      // 创建一个孔特征进行测试
      const project = {
        features: [{
          id: 'hole1',
          featureType: 'hole',
          baseGeometry: {
            center: { x: 10.0, y: 20.0 }
          },
          parameters: {
            diameter: 5.5,
            depth: 14,
            drawingDepth: 10,
            toolNumber: 2
          }
        }]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeGCode = gCodeBlocks.find(block => block.featureType === 'hole');
      const gCodeLines = holeGCode.code;
      
      // 验证G81固定循环格式
      const g81Line = gCodeLines.find(line => line.includes('G81'));
      expect(g81Line).toBeDefined();
      expect(g81Line).toContain('G81');
      expect(g81Line).toContain('G98');  // 验证包含G98（返回初始平面）
      expect(g81Line).toContain('Z-');   // 验证包含Z轴深度
      expect(g81Line).toContain('R');    // 验证包含R参考平面
      expect(g81Line).toContain('F');    // 验证包含进给率
    });

    test('验证批量钻孔固定循环格式', () => {
      // 创建多个相同参数的孔特征进行批量加工测试
      const project = {
        features: [
          {
            id: 'hole1',
            featureType: 'hole',
            baseGeometry: {
              center: { x: 10.0, y: 20.0 }
            },
            parameters: {
              diameter: 5.5,
              depth: 14,
              drawingDepth: 10,
              toolNumber: 2
            }
          },
          {
            id: 'hole2',
            featureType: 'hole',
            baseGeometry: {
              center: { x: 15.0, y: 25.0 }
            },
            parameters: {
              diameter: 5.5,  // 相同参数，用于批量加工
              depth: 14,
              drawingDepth: 10,
              toolNumber: 2
            }
          },
          {
            id: 'hole3',
            featureType: 'hole',
            baseGeometry: {
              center: { x: 20.0, y: 30.0 }
            },
            parameters: {
              diameter: 5.5,  // 相同参数，用于批量加工
              depth: 14,
              drawingDepth: 10,
              toolNumber: 2
            }
          }
        ]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const batchHoleBlock = gCodeBlocks.find(block => block.isBatchOperation && block.featureType === 'hole');
      
      expect(batchHoleBlock).toBeDefined();
      expect(batchHoleBlock.isBatchOperation).toBe(true);
      expect(batchHoleBlock.batchSize).toBe(3);
      
      const gCodeLines = batchHoleBlock.code;
      
      // 验证批量加工的G81循环格式
      const g81Lines = gCodeLines.filter(line => line.includes('G81'));
      expect(g81Lines.length).toBe(1);  // 应该只有一个G81启动指令
      
      // 验证后续孔的X、Y坐标指定
      const coordinateLines = gCodeLines.filter(line => 
        (line.includes('X') && line.includes('Y')) && !line.includes('G0 X') // 排除G0定位指令
      );
      expect(coordinateLines.length).toBeGreaterThanOrEqual(2);  // 至少有2个额外的孔定位
    });

    test('验证深孔钻G83循环格式', () => {
      const project = {
        features: [{
          id: 'deepHole1',
          featureType: 'hole',
          baseGeometry: {
            center: { x: 30.0, y: 40.0 }
          },
          parameters: {
            diameter: 6.0,
            depth: 25,  // 深孔
            drawingDepth: 20,
            toolNumber: 2
          }
        }]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeGCode = gCodeBlocks.find(block => block.featureType === 'hole');
      const gCodeLines = holeGCode.code;
      
      // 对于较深的孔，应使用G83循环
      const g83Line = gCodeLines.find(line => line.includes('G83'));
      expect(g83Line).toBeDefined();
      expect(g83Line).toContain('G83');
      expect(g83Line).toContain('Q');  // G83应包含Q参数（每次进给深度）
    });

    test('验证沉头孔加工循环序列', () => {
      const project = {
        features: [{
          id: 'counterbore1',
          featureType: 'counterbore',
          baseGeometry: {
            center: { x: 25.0, y: 35.0 }
          },
          parameters: {
            diameter: 5.5,
            depth: 14,
            counterboreDiameter: 9.0,
            counterboreDepth: 5.5,
            drawingDepth: 10,
            useCounterbore: true
          }
        }]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const cbGCode = gCodeBlocks.find(block => block.featureType === 'counterbore');
      const gCodeLines = cbGCode.code;
      
      // 验证加工序列：点孔 -> 钻孔 -> 沉孔
      const t01Lines = gCodeLines.filter(line => line.includes('T01')); // 中心钻
      const t02Lines = gCodeLines.filter(line => line.includes('T02')); // 钻头
      const t03Lines = gCodeLines.filter(line => line.includes('T03')); // 沉头刀
      
      expect(t01Lines.length).toBeGreaterThanOrEqual(1);
      expect(t02Lines.length).toBeGreaterThanOrEqual(1);
      expect(t03Lines.length).toBeGreaterThanOrEqual(1);  // 如果useCounterbore为true，应有T03
      
      // 验证G81点孔循环
      const g81Lines = gCodeLines.filter(line => line.includes('G81'));
      expect(g81Lines.length).toBeGreaterThanOrEqual(1);
      
      // 验证G83钻孔循环
      const g83Lines = gCodeLines.filter(line => line.includes('G83'));
      expect(g83Lines.length).toBeGreaterThanOrEqual(1);
      
      // 验证G82沉孔循环
      const g82Lines = gCodeLines.filter(line => line.includes('G82'));
      expect(g82Lines.length).toBeGreaterThanOrEqual(1);
    });

    test('验证批量沉头孔加工循环序列', () => {
      const project = {
        features: [
          {
            id: 'counterbore1',
            featureType: 'counterbore',
            baseGeometry: {
              center: { x: 25.0, y: 35.0 }
            },
            parameters: {
              diameter: 5.5,
              depth: 14,
              counterboreDiameter: 9.0,
              counterboreDepth: 5.5,
              drawingDepth: 10,
              useCounterbore: true
            }
          },
          {
            id: 'counterbore2',
            featureType: 'counterbore',
            baseGeometry: {
              center: { x: 30.0, y: 40.0 }
            },
            parameters: {
              diameter: 5.5,  // 相同参数，用于批量加工
              depth: 14,
              counterboreDiameter: 9.0,
              counterboreDepth: 5.5,
              drawingDepth: 10,
              useCounterbore: true
            }
          }
        ]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const batchCbBlock = gCodeBlocks.find(block => block.isBatchOperation && block.featureType === 'counterbore');
      
      expect(batchCbBlock).toBeDefined();
      expect(batchCbBlock.isBatchOperation).toBe(true);
      expect(batchCbBlock.batchSize).toBe(2);
    });

    test('验证G代码安全性', () => {
      const project = {
        features: [{
          id: 'hole1',
          featureType: 'hole',
          baseGeometry: {
            center: { x: 10.0, y: 20.0 }
          },
          parameters: {
            diameter: 5.5,
            depth: 14,
            drawingDepth: 10,
            toolNumber: 2
          }
        }]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeGCode = gCodeBlocks.find(block => block.featureType === 'hole');
      
      // 验证G代码块结构
      expect(holeGCode).toBeDefined();
      expect(Array.isArray(holeGCode.code)).toBe(true);
      expect(holeGCode.code.length).toBeGreaterThan(0);
      
      // 验证关键安全指令
      const gCodeLines = holeGCode.code;
      const hasG80 = gCodeLines.some(line => line.includes('G80'));  // 固定循环取消
      const hasSafetyZ = gCodeLines.some(line => line.includes('G0 Z100'));  // 安全高度
      const hasSpindleControl = gCodeLines.some(line => line.includes('M03') || line.includes('M05'));  // 主轴控制
      
      expect(hasG80).toBe(true);
      expect(hasSafetyZ).toBe(true);
      expect(hasSpindleControl).toBe(true);
    });

    test('验证一次装刀连续加工多个孔功能', () => {
      // 创建多个相同刀具需求的孔，验证是否能实现一次装刀连续加工
      const project = {
        features: [
          {
            id: 'hole1',
            featureType: 'hole',
            baseGeometry: {
              center: { x: 10.0, y: 10.0 }
            },
            parameters: {
              diameter: 5.0,
              depth: 12,
              drawingDepth: 10,
              toolNumber: 2  // 使用钻头T02
            }
          },
          {
            id: 'hole2',
            featureType: 'hole',
            baseGeometry: {
              center: { x: 20.0, y: 10.0 }
            },
            parameters: {
              diameter: 5.0,  // 相同直径
              depth: 12,      // 相同深度
              drawingDepth: 10,
              toolNumber: 2   // 相同刀具
            }
          },
          {
            id: 'hole3',
            featureType: 'hole',
            baseGeometry: {
              center: { x: 15.0, y: 20.0 }
            },
            parameters: {
              diameter: 5.0,  // 相同直径
              depth: 12,      // 相同深度
              drawingDepth: 10,
              toolNumber: 2   // 相同刀具
            }
          }
        ]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      
      // 查找孔加工相关的G代码块
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      
      // 验证是否生成了批量加工块
      const batchHoleBlock = gCodeBlocks.find(block => block.isBatchOperation && block.featureType === 'hole');
      expect(batchHoleBlock).toBeDefined();
      expect(batchHoleBlock.batchSize).toBe(3);  // 应该批量处理3个孔
      
      const gCodeLines = batchHoleBlock.code;
      
      // 验证只换一次刀具
      const toolChangeLines = gCodeLines.filter(line => line.includes('M06'));
      expect(toolChangeLines.length).toBe(1);  // 只换一次刀
      
      // 验证G81循环后有多个X、Y坐标移动
      const coordinateMoves = gCodeLines.filter(line => 
        line.trim().startsWith('X') && line.includes('Y') && !line.includes('G0 X')
      );
      expect(coordinateMoves.length).toBe(2);  // 3个孔需要2次额外的坐标移动
    });
  });

  describe('PDF解析与G代码生成集成测试', () => {
    test('验证从PDF解析到G代码生成的完整流程', async () => {
      // 创建一个模拟的简单CAD文本内容
      const mockPdfContent = `
        图纸信息：机械零件
        孔位置：X: 10.0, Y: 20.0
        孔位置：X: 15.0, Y: 25.0
        孔位置：X: 20.0, Y: 30.0
        直径：5.5mm
        深度：10mm
        材料：Aluminum
      `;
      
      // 模拟从文本内容提取几何元素
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      const { geometryElements, dimensions } = extractGeometricInfoFromText(mockPdfContent);
      
      // 验证提取的几何元素
      const holes = geometryElements.filter(el => el.type === 'hole' || (el.text && (el.text.toLowerCase().includes('hole') || el.text.includes('孔'))));
      expect(holes.length).toBeGreaterThanOrEqual(3);
      
      // 构建项目对象用于G代码生成
      const features = holes.map((hole, index) => ({
        id: `feature_${index}`,
        featureType: 'hole',
        baseGeometry: hole.center ? hole.center : { center: { x: parseFloat(hole.text.match(/X:\s*([+-]?\d+\.?\d*)/)?.[1] || 0), y: parseFloat(hole.text.match(/Y:\s*([+-]?\d+\.?\d*)/)?.[1] || 0) }},
        parameters: {
          diameter: 5.5,
          depth: 14,
          drawingDepth: 10,
          toolNumber: 2
        }
      }));
      
      const project = {
        features: features,
        materialType: 'Aluminum'
      };
      
      // 生成G代码
      const gCodeBlocks = triggerGCodeGeneration(project);
      
      // 验证G代码生成成功
      expect(gCodeBlocks).toBeDefined();
      expect(Array.isArray(gCodeBlocks)).toBe(true);
      expect(gCodeBlocks.length).toBeGreaterThan(0);
      
      // 验证存在孔加工代码
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      expect(holeBlocks.length).toBeGreaterThanOrEqual(1);
    }, 10000); // 增加超时时间

    test('验证OCR改进对G代码生成的影响', () => {
      // 测试OCR后处理对最终G代码质量的影响
      const rawOcrText = `
        H0LE X: 25.0 Y: 30.0 DIA 5.5mm DEEP 10mm
        DRILL DEPTH Z-14.8
        G81 CYCLE WITh G98 R2.0 F100.
      `;
      
      // 使用OCR后处理函数
      const { postProcessOcrText } = require('../src/modules/subprocesses/pdfParsingProcess');
      const processedText = postProcessOcrText(rawOcrText);
      
      // 验证处理后的文本更适合几何元素提取
      expect(processedText).toContain('HOLE');  // 修复了 "H0LE" -> "HOLE"
      expect(processedText).toContain('G81');   // 修复了 "G81 CYCLE" 中的可能问题
      expect(processedText).toContain('G98');   // 修复了 "G98" 格式
      
      // 从处理后的文本提取几何信息
      const { extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      const { geometryElements, dimensions } = extractGeometricInfoFromText(processedText);
      
      // 验证提取的几何元素
      const holes = geometryElements.filter(el => el.type === 'hole' || (el.text && (el.text.toLowerCase().includes('hole') || el.text.includes('孔'))));
      expect(holes.length).toBeGreaterThanOrEqual(1);
    });
  });

  describe('边界条件和错误处理测试', () => {
    test('验证空项目处理', () => {
      const project = { features: [] };
      expect(() => triggerGCodeGeneration(project)).not.toThrow();
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      // 应该至少有程序开始和结束代码
      expect(gCodeBlocks.length).toBeGreaterThanOrEqual(2);
    });

    test('验证无效特征处理', () => {
      const project = {
        features: [null, undefined, { invalid: 'feature' }]
      };
      
      expect(() => triggerGCodeGeneration(project)).not.toThrow();
    });

    test('验证G代码格式边界值', () => {
      // 测试极小和极大的坐标值
      const extremeProject = {
        features: [{
          id: 'extremeHole',
          featureType: 'hole',
          baseGeometry: {
            center: { x: 9999.999, y: 9999.999 }  // 极大值
          },
          parameters: {
            diameter: 0.1,  // 极小直径
            depth: 0.1,     // 极小深度
            drawingDepth: 0.1,
            toolNumber: 1
          }
        }]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(extremeProject);
      const holeGCode = gCodeBlocks.find(block => block.featureType === 'hole');
      
      expect(holeGCode).toBeDefined();
      const gCodeLines = holeGCode.code;
      const positioningLine = gCodeLines.find(line => line.includes('G0 X') && line.includes('Y'));
      expect(positioningLine).toBeDefined();
    });
  });
});