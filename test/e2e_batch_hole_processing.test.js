const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
const { pdfParsingProcess } = require('../src/modules/subprocesses/pdfParsingProcess');
const fs = require('fs');
const path = require('path');

describe('端到端测试：验证一次装刀连续加工多个孔功能', () => {
  describe('批量孔加工功能验证', () => {
    test('验证相同参数孔的批量加工实现', () => {
      // 创建具有相同加工参数的多个孔
      const project = {
        features: [
          {
            id: 'hole_1',
            featureType: 'hole',
            baseGeometry: { center: { x: 10.000, y: 10.000 } },
            parameters: {
              diameter: 5.5,
              drawingDepth: 10,
              toolNumber: 2,  // 使用钻头T02
              materialType: 'Aluminum'
            }
          },
          {
            id: 'hole_2',
            featureType: 'hole',
            baseGeometry: { center: { x: 20.000, y: 10.000 } },
            parameters: {
              diameter: 5.5,  // 相同直径
              drawingDepth: 10, // 相同深度
              toolNumber: 2,    // 相同刀具
              materialType: 'Aluminum'
            }
          },
          {
            id: 'hole_3',
            featureType: 'hole',
            baseGeometry: { center: { x: 15.000, y: 20.000 } },
            parameters: {
              diameter: 5.5,  // 相同直径
              drawingDepth: 10, // 相同深度
              toolNumber: 2,    // 相同刀具
              materialType: 'Aluminum'
            }
          },
          {
            id: 'hole_4',
            featureType: 'hole',
            baseGeometry: { center: { x: 25.000, y: 20.000 } },
            parameters: {
              diameter: 5.5,  // 相同直径
              drawingDepth: 10, // 相同深度
              toolNumber: 2,    // 相同刀具
              materialType: 'Aluminum'
            }
          }
        ],
        materialType: 'Aluminum'
      };

      const gCodeBlocks = triggerGCodeGeneration(project);
      
      // 查找批量加工的块
      const batchHoleBlock = gCodeBlocks.find(block => block.isBatchOperation && block.featureType === 'hole');
      
      expect(batchHoleBlock).toBeDefined();
      expect(batchHoleBlock.isBatchOperation).toBe(true);
      expect(batchHoleBlock.batchSize).toBe(4); // 应该批量处理4个孔
      
      const gCodeLines = batchHoleBlock.code;
      
      // 验证批量加工的关键特征
      // 1. 只换一次刀具
      const toolChanges = gCodeLines.filter(line => line.includes('M06'));
      expect(toolChanges.length).toBe(1);
      
      // 2. 使用G81固定循环
      const g81Line = gCodeLines.find(line => line.includes('G81 G98'));
      expect(g81Line).toBeDefined();
      expect(g81Line).toContain('G81');
      expect(g81Line).toContain('G98');  // 返回初始平面
      expect(g81Line).toContain('Z-');   // Z轴深度
      expect(g81Line).toContain('R');    // 参考平面
      expect(g81Line).toContain('F');    // 进给率
      
      // 3. 首先移动到第一个孔位置
      const firstMove = gCodeLines.find(line => line.includes('G0 X') && line.includes('Y'));
      expect(firstMove).toBeDefined();
      expect(firstMove).toContain('X10.000');
      expect(firstMove).toContain('Y10.000');
      
      // 4. 在G81循环后有多个X、Y坐标移动（连续加工其他孔）
      const subsequentMoves = gCodeLines.filter(line => 
        line.trim().startsWith('X') && line.includes('Y') && !line.includes('G0 X')
      );
      expect(subsequentMoves.length).toBe(3); // 4个孔需要3次额外的坐标移动
      
      // 验证后续移动包含正确的坐标
      expect(subsequentMoves.some(move => move.includes('X20.000') && move.includes('Y10.000'))).toBe(true);
      expect(subsequentMoves.some(move => move.includes('X15.000') && move.includes('Y20.000'))).toBe(true);
      expect(subsequentMoves.some(move => move.includes('X25.000') && move.includes('Y20.000'))).toBe(true);
      
      // 5. 循环结束后取消固定循环
      const hasG80 = gCodeLines.some(line => line.includes('G80'));
      expect(hasG80).toBe(true);
    });

    test('验证不同参数孔的独立加工', () => {
      // 创建具有不同加工参数的孔（应分别加工）
      const project = {
        features: [
          {
            id: 'hole_1_different',
            featureType: 'hole',
            baseGeometry: { center: { x: 5.000, y: 5.000 } },
            parameters: {
              diameter: 4.0,   // 不同直径
              drawingDepth: 8,
              toolNumber: 2,
              materialType: 'Aluminum'
            }
          },
          {
            id: 'hole_2_different',
            featureType: 'hole',
            baseGeometry: { center: { x: 10.000, y: 5.000 } },
            parameters: {
              diameter: 6.0,   // 不同直径
              drawingDepth: 12, // 不同深度
              toolNumber: 2,    // 相同刀具
              materialType: 'Aluminum'
            }
          },
          {
            id: 'hole_3_same',
            featureType: 'hole',
            baseGeometry: { center: { x: 15.000, y: 5.000 } },
            parameters: {
              diameter: 6.0,   // 与hole_2相同
              drawingDepth: 12, // 与hole_2相同
              toolNumber: 2,    // 相同刀具
              materialType: 'Aluminum'
            }
          }
        ],
        materialType: 'Aluminum'
      };

      const gCodeBlocks = triggerGCodeGeneration(project);
      
      // 应该有两个加工块：1个单独加工的孔 + 1个批量加工2个孔
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      expect(holeBlocks.length).toBe(2); // 一个单独加工，一个批量加工两个
      
      // 检查是否有批量加工块
      const batchBlock = holeBlocks.find(block => block.isBatchOperation);
      const singleBlock = holeBlocks.find(block => !block.isBatchOperation);
      
      expect(batchBlock).toBeDefined();
      expect(singleBlock).toBeDefined();
      expect(batchBlock.batchSize).toBe(2); // 2个相同参数的孔
    });

    test('验证批量沉头孔加工', () => {
      // 创建多个相同参数的沉头孔
      const project = {
        features: [
          {
            id: 'cb_1',
            featureType: 'counterbore',
            baseGeometry: { center: { x: 25.000, y: 35.000 } },
            parameters: {
              diameter: 5.5,
              depth: 14,
              counterboreDiameter: 9.0,
              counterboreDepth: 5.5,
              drawingDepth: 10,
              useCounterbore: true,
              toolNumber: 2  // 实际钻孔用T02
            }
          },
          {
            id: 'cb_2',
            featureType: 'counterbore',
            baseGeometry: { center: { x: 35.000, y: 35.000 } },
            parameters: {
              diameter: 5.5,  // 相同参数
              depth: 14,
              counterboreDiameter: 9.0,
              counterboreDepth: 5.5,
              drawingDepth: 10,
              useCounterbore: true,
              toolNumber: 2
            }
          }
        ],
        materialType: 'Aluminum'
      };

      const gCodeBlocks = triggerGCodeGeneration(project);
      const batchCbBlock = gCodeBlocks.find(block => block.isBatchOperation && block.featureType === 'counterbore');
      
      expect(batchCbBlock).toBeDefined();
      expect(batchCbBlock.isBatchOperation).toBe(true);
      expect(batchCbBlock.batchSize).toBe(2); // 2个相同沉头孔
      
      const gCodeLines = batchCbBlock.code;
      
      // 验证批量沉头孔加工的特征
      // 1. 每种刀具只换一次
      const t01Count = gCodeLines.filter(line => line.includes('T01 M06')).length;
      const t02Count = gCodeLines.filter(line => line.includes('T02 M06')).length;
      const t03Count = gCodeLines.filter(line => line.includes('T03 M06')).length;
      
      expect(t01Count).toBe(1); // 点孔刀具T01只换一次
      expect(t02Count).toBe(1); // 钻孔刀具T02只换一次
      expect(t03Count).toBe(1); // 沉孔刀具T03只换一次
      
      // 2. 每个加工步骤都使用批量循环
      // 点孔批量加工
      const g81Lines = gCodeLines.filter(line => line.includes('G81 G98'));
      expect(g81Lines.length).toBeGreaterThanOrEqual(1); // 至少一个G81启动
      
      // 钻孔批量加工 (G83)
      const g83Lines = gCodeLines.filter(line => line.includes('G83 G98'));
      expect(g83Lines.length).toBeGreaterThanOrEqual(1); // 至少一个G83启动
      
      // 沉孔批量加工 (G82)
      const g82Lines = gCodeLines.filter(line => line.includes('G82 G98'));
      expect(g82Lines.length).toBeGreaterThanOrEqual(1); // 至少一个G82启动
    });
  });

  describe('标准G代码格式验证', () => {
    test('验证G81钻孔循环的标准格式', () => {
      const project = {
        features: [{
          id: 'std_hole',
          featureType: 'hole',
          baseGeometry: { center: { x: 10.000, y: 20.000 } },
          parameters: {
            diameter: 5.5,
            drawingDepth: 10,
            toolNumber: 2
          }
        }]
      };

      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeBlock = gCodeBlocks.find(block => block.featureType === 'hole');
      const gCodeLines = holeBlock.code;
      
      // 查找G81行并验证其格式
      const g81Line = gCodeLines.find(line => line.includes('G81'));
      expect(g81Line).toBeDefined();
      
      // 标准G81格式: G81 G98 Z- R2.0 Fxxx
      // 验证包含所有必要元素
      expect(g81Line).toContain('G81');  // G81指令
      expect(g81Line).toContain('G98');  // 返回初始平面模式
      expect(g81Line).toMatch(/Z-[\d.]+/);  // Z轴负向移动（具体深度值）
      expect(g81Line).toContain('R2.0'); // 参考平面
      expect(g81Line).toMatch(/F\d+/);   // 进给率
    });

    test('验证坐标精度和格式', () => {
      const project = {
        features: [{
          id: 'precision_hole',
          featureType: 'hole',
          baseGeometry: { center: { x: 25.12345, y: 30.56789 } },  // 高精度坐标
          parameters: {
            diameter: 6.5,
            drawingDepth: 15,
            toolNumber: 2
          }
        }]
      };

      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeBlock = gCodeBlocks.find(block => block.featureType === 'hole');
      const gCodeLines = holeBlock.code;
      
      // 查找定位指令并验证坐标精度
      const positioningLine = gCodeLines.find(line => line.includes('G0 X') && line.includes('Y'));
      expect(positioningLine).toBeDefined();
      
      // 验证坐标保留3位小数
      const xMatch = positioningLine.match(/X(-?\d+\.\d{3})/);
      const yMatch = positioningLine.match(/Y(-?\d+\.\d{3})/);
      
      expect(xMatch).toBeDefined();
      expect(yMatch).toBeDefined();
      
      if (xMatch) expect(xMatch[1]).toMatch(/^\d+\.\d{3}$/);  // X坐标3位小数
      if (yMatch) expect(yMatch[1]).toMatch(/^\d+\.\d{3}$/);  // Y坐标3位小数
    });

    test('验证安全和规范指令', () => {
      const project = {
        features: [{
          id: 'safe_hole',
          featureType: 'hole',
          baseGeometry: { center: { x: 5.000, y: 5.000 } },
          parameters: {
            diameter: 4.0,
            drawingDepth: 8,
            toolNumber: 2
          }
        }]
      };

      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeBlock = gCodeBlocks.find(block => block.featureType === 'hole');
      const gCodeLines = holeBlock.code;
      
      // 验证安全相关指令
      const hasToolLengthComp = gCodeLines.some(line => line.includes('G43 H02'));
      const hasSpindleStart = gCodeLines.some(line => line.includes('S') && line.includes('M03'));
      const hasSpindleStop = gCodeLines.some(line => line.includes('M05'));
      const hasCycleCancel = gCodeLines.some(line => line.includes('G80'));
      const hasSafeHeight = gCodeLines.some(line => line.includes('G0 Z100.'));
      const hasProgramStart = gCodeBlocks[0].code.includes('O0001');
      const hasProgramEnd = gCodeBlocks[gCodeBlocks.length - 1].code.includes('M30');
      
      expect(hasToolLengthComp).toBe(true);
      expect(hasSpindleStart).toBe(true);
      expect(hasCycleCancel).toBe(true);
      expect(hasSafeHeight).toBe(true);
      expect(hasProgramStart).toBe(true);
      expect(hasProgramEnd).toBe(true);
    });
  });

  describe('实际PDF解析到G代码生成端到端测试', () => {
    test('模拟完整工作流程：PDF解析 -> 特征提取 -> G代码生成', async () => {
      // 由于我们没有实际的PDF文件，我们将模拟从PDF解析得到的特征数据
      // 这个测试主要验证整个数据流是否正确传递
      
      // 模拟从PDF解析中得到的几何元素
      const mockGeometryElements = [
        { id: 'hole1', type: 'hole', center: { x: 10.000, y: 10.000 }, text: 'HOLE X: 10.0 Y: 10.0 DIA 5.5' },
        { id: 'hole2', type: 'hole', center: { x: 20.000, y: 10.000 }, text: 'HOLE X: 20.0 Y: 10.0 DIA 5.5' },
        { id: 'hole3', type: 'hole', center: { x: 15.000, y: 20.000 }, text: 'HOLE X: 15.0 Y: 20.0 DIA 5.5' }
      ];
      
      const mockDimensions = [
        { id: 'dim1', type: 'diameter', value: 5.5, unit: 'mm', description: 'Hole diameter 5.5mm' }
      ];
      
      // 将几何元素转换为G代码生成所需的特征格式
      const features = mockGeometryElements.map((geom, index) => ({
        id: `feature_${index}`,
        featureType: geom.type || 'hole',  // 默认为hole
        baseGeometry: geom,
        parameters: {
          diameter: 5.5,  // 从尺寸中获取或默认
          depth: 14,      // 实际加工深度
          drawingDepth: 10, // 图纸深度
          toolNumber: 2   // 使用钻头T02
        }
      }));
      
      const project = {
        features: features,
        materialType: 'Aluminum'
      };
      
      // 生成G代码
      const gCodeBlocks = triggerGCodeGeneration(project);
      
      // 验证生成结果
      expect(gCodeBlocks).toBeDefined();
      expect(Array.isArray(gCodeBlocks)).toBe(true);
      expect(gCodeBlocks.length).toBeGreaterThan(2); // 至少有程序开始和结束
      
      // 验证特征处理
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      expect(holeBlocks.length).toBeGreaterThanOrEqual(3); // 至少3个孔
      
      // 检查是否有批量加工
      const batchBlock = gCodeBlocks.find(block => block.isBatchOperation);
      if (batchBlock) {
        expect(batchBlock.batchSize).toBeGreaterThanOrEqual(3); // 3个相同参数的孔
        expect(batchBlock.isBatchOperation).toBe(true);
      }
    });

    test('验证OCR改进对端到端流程的影响', () => {
      const { postProcessOcrText, extractGeometricInfoFromText } = require('../src/modules/subprocesses/pdfParsingProcess');
      const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
      
      // 模拟包含OCR错误的文本（在实际PDF解析中可能出现）
      const rawTextFromOcr = `
        机械零件图纸
        H0LE P0SITI0N: X: 10.000 Y: 10.000 DIA: 5.5tnm
        H0LE P0SITI0N: X: 20.000 Y: 10.000 DIA: 5.5tnm  // 相同参数，可批量
        H0LE P0SITI0N: X: 15.000 Y: 20.000 DIA: 5.5tnm  // 相同参数，可批量
        MATL: Aluminum
        DRILL DEPTH: 10mm
        G-code: 81 G98 Z-14.8 R2.0 F100.0
      `;
      
      // 1. 应用OCR后处理改进
      const processedText = postProcessOcrText(rawTextFromOcr);
      expect(processedText).toContain('HOLE');  // 修正 "H0LE"
      expect(processedText).toContain('POSITION'); // 修正 "P0SITI0N" 
      expect(processedText).toContain('mm'); // 修正 "tnm" to "mm"
      expect(processedText).toContain('G81'); // 修正 "81" to "G81"
      expect(processedText).toContain('G98'); // 修正 "98" to "G98"
      
      // 2. 从处理后的文本提取几何信息
      const { geometryElements, dimensions } = extractGeometricInfoFromText(processedText);
      const holes = geometryElements.filter(el => el.type === 'hole' || (el.text && (el.text.toLowerCase().includes('hole') || el.text.includes('孔'))));
      expect(holes.length).toBeGreaterThanOrEqual(3); // 应提取到3个孔
      
      // 3. 转换为特征格式
      const features = holes.map((hole, index) => {
        const text = hole.text || '';
        const xMatch = text.match(/X:\s*(\d+\.\d+)/);
        const yMatch = text.match(/Y:\s*(\d+\.\d+)/);
        const diaMatch = text.match(/DIA[:\s]*(\d+\.\d+)/);
        
        return {
          id: `ocr_feature_${index}`,
          featureType: 'hole',
          baseGeometry: {
            center: {
              x: xMatch ? parseFloat(xMatch[1]) : hole.center?.x || index * 10,
              y: yMatch ? parseFloat(yMatch[1]) : hole.center?.y || 10
            }
          },
          parameters: {
            diameter: diaMatch ? parseFloat(diaMatch[1]) : 5.5,
            depth: 14, // 实际加工深度
            drawingDepth: 10, // 图纸深度
            toolNumber: 2
          }
        };
      });
      
      // 4. 生成G代码
      const project = {
        features: features,
        materialType: 'Aluminum'
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      expect(gCodeBlocks).toBeDefined();
      expect(gCodeBlocks.length).toBeGreaterThanOrEqual(3); // 至少开始+特征+结束
      
      // 5. 验证批量加工是否正确实现
      const batchBlock = gCodeBlocks.find(block => block.isBatchOperation && block.featureType === 'hole');
      if (batchBlock) {
        expect(batchBlock.batchSize).toBeGreaterThanOrEqual(3); // OCR改进后应能正确识别批量加工
        expect(batchBlock.isBatchOperation).toBe(true);
      }
      
      // 6. 验证G代码格式正确性
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      if (holeBlocks.length > 0) {
        const gCodeLines = holeBlocks[0].code;
        const hasProperG81 = gCodeLines.some(line => line.includes('G81') && line.includes('G98') && line.includes('Z-') && line.includes('R') && line.includes('F'));
        expect(hasProperG81).toBe(true);
      }
    });
  });

  describe('性能和边界条件测试', () => {
    test('验证大量相同孔的批量处理', () => {
      // 创建10个相同参数的孔
      const features = [];
      for (let i = 0; i < 10; i++) {
        features.push({
          id: `hole_${i}`,
          featureType: 'hole',
          baseGeometry: { center: { x: 10 + i * 2, y: 10 } }, // 不同位置但相同加工参数
          parameters: {
            diameter: 5.0,
            drawingDepth: 8,
            toolNumber: 2
          }
        });
      }
      
      const project = {
        features: features,
        materialType: 'Aluminum'
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const batchBlock = gCodeBlocks.find(block => block.isBatchOperation);
      
      // 验证所有10个孔都被批量处理
      expect(batchBlock).toBeDefined();
      if (batchBlock) {
        expect(batchBlock.batchSize).toBe(10);
        expect(batchBlock.isBatchOperation).toBe(true);
      }
    });

    test('验证不同加工参数的正确分组', () => {
      const project = {
        features: [
          // 3个相同参数的孔 - 组1
          { id: 'h1', featureType: 'hole', baseGeometry: { center: { x: 1, y: 1 } }, parameters: { diameter: 5.0, toolNumber: 2 } },
          { id: 'h2', featureType: 'hole', baseGeometry: { center: { x: 2, y: 1 } }, parameters: { diameter: 5.0, toolNumber: 2 } },
          { id: 'h3', featureType: 'hole', baseGeometry: { center: { x: 3, y: 1 } }, parameters: { diameter: 5.0, toolNumber: 2 } },
          // 2个相同参数的孔 - 组2
          { id: 'h4', featureType: 'hole', baseGeometry: { center: { x: 1, y: 2 } }, parameters: { diameter: 6.0, toolNumber: 2 } },
          { id: 'h5', featureType: 'hole', baseGeometry: { center: { x: 2, y: 2 } }, parameters: { diameter: 6.0, toolNumber: 2 } },
          // 1个单独的孔 - 组3
          { id: 'h6', featureType: 'hole', baseGeometry: { center: { x: 1, y: 3 } }, parameters: { diameter: 5.0, toolNumber: 1 } } // 不同刀具
        ],
        materialType: 'Aluminum'
      };

      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      
      // 应该有3个处理块：组1批量(3个) + 组2批量(2个) + 组3单独(1个)
      expect(holeBlocks.length).toBe(3);
      
      const batchBlocks = holeBlocks.filter(block => block.isBatchOperation);
      const singleBlocks = holeBlocks.filter(block => !block.isBatchOperation);
      
      expect(batchBlocks.length).toBe(2);  // 两个批量处理块
      expect(singleBlocks.length).toBe(1); // 一个单独处理块
      
      // 验证批量大小
      const batchSizes = batchBlocks.map(block => block.batchSize);
      expect(batchSizes).toContain(3); // 第一组
      expect(batchSizes).toContain(2); // 第二组
      expect(singleBlocks[0].isBatchOperation).toBeFalsy(); // 第三组是单独处理
    });

    test('验证钻孔深度计算准确性', () => {
      const testCases = [
        { drawingDepth: 10, diameter: 5.5, expectedActual: 13.8 }, // 10 + 5.5/3 + 2 = 13.8
        { drawingDepth: 8, diameter: 6.0, expectedActual: 12.0 },  // 8 + 6.0/3 + 2 = 12.0
        { drawingDepth: 15, diameter: 4.5, expectedActual: 18.5 }  // 15 + 4.5/3 + 2 = 18.5
      ];
      
      testCases.forEach((testCase, index) => {
        const project = {
          features: [{
            id: `depth_test_${index}`,
            featureType: 'hole',
            baseGeometry: { center: { x: 10, y: 10 } },
            parameters: {
              diameter: testCase.diameter,
              drawingDepth: testCase.drawingDepth,
              toolNumber: 2
            }
          }],
          materialType: 'Aluminum'
        };
        
        const gCodeBlocks = triggerGCodeGeneration(project);
        const holeBlock = gCodeBlocks.find(block => block.featureType === 'hole');
        const gCodeLines = holeBlock.code;
        
        const g81Line = gCodeLines.find(line => line.includes('G81'));
        expect(g81Line).toBeDefined();
        expect(g81Line).toContain(`Z-${testCase.expectedActual}`);
      });
    });
  });

  describe('实际应用场景验证', () => {
    test('验证法兰盘多孔加工场景', () => {
      // 模拟法兰盘上多个螺栓孔的加工
      const boltCircle = [];
      const center = { x: 50, y: 50 };
      const radius = 30;
      const numBolts = 6;
      
      for (let i = 0; i < numBolts; i++) {
        const angle = (2 * Math.PI * i) / numBolts;
        const x = center.x + radius * Math.cos(angle);
        const y = center.y + radius * Math.sin(angle);
        
        boltCircle.push({
          id: `bolt_${i}`,
          featureType: 'hole',
          baseGeometry: { center: { x: parseFloat(x.toFixed(3)), y: parseFloat(y.toFixed(3)) } },
          parameters: {
            diameter: 8.5,  // M8螺栓孔
            drawingDepth: 15,
            toolNumber: 2   // 钻头
          }
        });
      }
      
      const project = {
        features: boltCircle,
        materialType: 'Steel'
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const batchBlock = gCodeBlocks.find(block => block.isBatchOperation);
      
      // 验证所有6个螺栓孔都被批量处理
      expect(batchBlock).toBeDefined();
      if (batchBlock) {
        expect(batchBlock.batchSize).toBe(6);
        expect(batchBlock.isBatchOperation).toBe(true);
      }
      
      // 验证G代码质量
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      if (holeBlocks.length > 0) {
        const gCodeLines = holeBlocks[0].code;
        const hasProperFormat = gCodeLines.some(line => line.includes('G81') && line.includes('G98') && line.includes('Z-') && line.includes('R2.0') && line.includes('F'));
        expect(hasProperFormat).toBe(true);
      }
    });

    test('验证多层板加工场景', () => {
      // 模拟需要不同深度的多层板钻孔
      const project = {
        features: [
          // 第一层孔 - 浅孔
          { id: 'layer1_1', featureType: 'hole', baseGeometry: { center: { x: 10, y: 10 } }, parameters: { diameter: 4.0, drawingDepth: 5, toolNumber: 2 } },
          { id: 'layer1_2', featureType: 'hole', baseGeometry: { center: { x: 20, y: 10 } }, parameters: { diameter: 4.0, drawingDepth: 5, toolNumber: 2 } },
          // 第二层孔 - 深孔
          { id: 'layer2_1', featureType: 'hole', baseGeometry: { center: { x: 10, y: 20 } }, parameters: { diameter: 4.0, drawingDepth: 15, toolNumber: 2 } },
          { id: 'layer2_2', featureType: 'hole', baseGeometry: { center: { x: 20, y: 20 } }, parameters: { diameter: 4.0, drawingDepth: 15, toolNumber: 2 } }
        ],
        materialType: 'PCB'
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeBlocks = gCodeBlocks.filter(block => block.featureType === 'hole');
      
      // 应该有2个批量块（相同深度的孔分为一组）
      expect(holeBlocks.length).toBe(2);
      
      // 每个组内应该批量处理2个孔
      const batchBlocks = holeBlocks.filter(block => block.isBatchOperation);
      batchBlocks.forEach(block => {
        expect(block.batchSize).toBe(2);
        expect(block.isBatchOperation).toBe(true);
      });
    });
  });
});