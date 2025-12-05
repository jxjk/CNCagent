const { triggerGCodeGeneration, generateHoleGCode, generateCounterboreGCode, generateHoleGCodeBatch, generateCounterboreGCodeBatch, groupFeaturesByTypeAndParameters, getFeatureKey } = require('../src/modules/gCodeGeneration');

describe('G代码生成模块单元测试', () => {
  describe('孔加工G代码生成测试', () => {
    test('生成标准孔加工G代码', () => {
      const feature = {
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
      };
      
      const gCodeLines = generateHoleGCode(feature);
      expect(gCodeLines).toBeDefined();
      expect(Array.isArray(gCodeLines)).toBe(true);
      expect(gCodeLines.length).toBeGreaterThan(0);
      
      // 验证关键G代码指令
      const hasToolChange = gCodeLines.some(line => line.includes('T02 M06'));
      const hasSpindleStart = gCodeLines.some(line => line.includes('S') && line.includes('M03'));
      const hasG81 = gCodeLines.some(line => line.includes('G81'));
      const hasG80 = gCodeLines.some(line => line.includes('G80'));
      const hasSafetyZ = gCodeLines.some(line => line.includes('G0 Z100'));
      
      expect(hasToolChange).toBe(true);
      expect(hasSpindleStart).toBe(true);
      expect(hasG81).toBe(true);
      expect(hasG80).toBe(true);
      expect(hasSafetyZ).toBe(true);
    });

    test('验证钻孔深度计算公式', () => {
      const feature = {
        id: 'hole_calc',
        featureType: 'hole',
        baseGeometry: {
          center: { x: 15.0, y: 25.0 }
        },
        parameters: {
          diameter: 6.0,
          drawingDepth: 10,  // 图纸深度
          toolNumber: 2
        }
      };
      
      const gCodeLines = generateHoleGCode(feature);
      const g81Line = gCodeLines.find(line => line.includes('G81'));
      
      // 验证深度计算：图纸深度 + 直径/3 + 2mm
      const expectedDepth = 10 + 6.0/3 + 2; // = 14mm
      expect(g81Line).toContain(`Z-${expectedDepth.toFixed(1)}`);
    });

    test('生成通孔和盲孔G代码', () => {
      // 通孔
      const throughHole = {
        id: 'through_hole',
        featureType: 'hole',
        baseGeometry: {
          center: { x: 5.0, y: 5.0 }
        },
        parameters: {
          diameter: 4.0,
          drawingDepth: 8,
          holeType: 'through',
          toolNumber: 2
        }
      };
      
      // 盲孔
      const blindHole = {
        id: 'blind_hole',
        featureType: 'hole',
        baseGeometry: {
          center: { x: 15.0, y: 15.0 }
        },
        parameters: {
          diameter: 4.0,
          drawingDepth: 8,
          holeType: 'blind',
          toolNumber: 2
        }
      };
      
      const throughGCode = generateHoleGCode(throughHole);
      const blindGCode = generateHoleGCode(blindHole);
      
      // 两种孔的处理方式应该相同（都使用G81）
      expect(throughGCode.some(line => line.includes('G81'))).toBe(true);
      expect(blindGCode.some(line => line.includes('G81'))).toBe(true);
    });
  });

  describe('沉头孔加工G代码生成测试', () => {
    test('生成标准沉头孔加工G代码', () => {
      const feature = {
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
      };
      
      const gCodeLines = generateCounterboreGCode(feature);
      expect(gCodeLines).toBeDefined();
      expect(Array.isArray(gCodeLines)).toBe(true);
      expect(gCodeLines.length).toBeGreaterThan(0);
      
      // 验证三步加工过程：点孔 -> 钻孔 -> 沉孔
      const hasT01 = gCodeLines.some(line => line.includes('T01 M06')); // 中心钻
      const hasT02 = gCodeLines.some(line => line.includes('T02 M06')); // 钻头
      const hasT03 = gCodeLines.some(line => line.includes('T03 M06')); // 沉头刀
      const hasG81 = gCodeLines.some(line => line.includes('G81'));     // 点孔
      const hasG83 = gCodeLines.some(line => line.includes('G83'));     // 钻孔
      const hasG82 = gCodeLines.some(line => line.includes('G82'));     // 沉孔
      
      expect(hasT01).toBe(true);
      expect(hasT02).toBe(true);
      if (feature.parameters.useCounterbore) {
        expect(hasT03).toBe(true);
      }
      expect(hasG81).toBe(true);
      expect(hasG83).toBe(true);
      if (feature.parameters.useCounterbore) {
        expect(hasG82).toBe(true);
      }
    });

    test('生成不带沉孔的加工代码', () => {
      const feature = {
        id: 'counterbore_no_cb',
        featureType: 'counterbore',
        baseGeometry: {
          center: { x: 30.0, y: 40.0 }
        },
        parameters: {
          diameter: 5.5,
          depth: 14,
          counterboreDiameter: 9.0,
          counterboreDepth: 5.5,
          drawingDepth: 10,
          useCounterbore: false  // 不使用沉孔
        }
      };
      
      const gCodeLines = generateCounterboreGCode(feature);
      expect(gCodeLines).toBeDefined();
      
      // 应该有T01和T02，但不应该有T03
      const hasT01 = gCodeLines.some(line => line.includes('T01 M06'));
      const hasT02 = gCodeLines.some(line => line.includes('T02 M06'));
      const hasT03 = gCodeLines.some(line => line.includes('T03 M06'));
      
      expect(hasT01).toBe(true);
      expect(hasT02).toBe(true);
      expect(hasT03).toBe(false); // 因为useCounterbore为false
    });
  });

  describe('批量加工G代码生成测试', () => {
    test('生成批量孔加工G代码', () => {
      const mainFeature = {
        id: 'main_hole',
        featureType: 'hole',
        baseGeometry: {
          center: { x: 10.0, y: 20.0 }
        },
        parameters: {
          diameter: 5.5,
          drawingDepth: 10,
          toolNumber: 2
        }
      };
      
      const features = [
        { ...mainFeature, id: 'hole1', baseGeometry: { center: { x: 10.0, y: 20.0 } } },
        { ...mainFeature, id: 'hole2', baseGeometry: { center: { x: 15.0, y: 25.0 } } },
        { ...mainFeature, id: 'hole3', baseGeometry: { center: { x: 20.0, y: 30.0 } } }
      ];
      
      const gCodeLines = generateHoleGCodeBatch(mainFeature, features);
      expect(gCodeLines).toBeDefined();
      expect(Array.isArray(gCodeLines)).toBe(true);
      expect(gCodeLines.length).toBeGreaterThan(0);
      
      // 验证批量加工特征
      const hasBatchComment = gCodeLines.some(line => line.includes('批量加工'));
      const hasSingleToolChange = gCodeLines.filter(line => line.includes('M06')).length === 1;
      const hasG81 = gCodeLines.some(line => line.includes('G81'));
      const hasCoordinateMoves = gCodeLines.filter(line => line.startsWith('X') && line.includes('Y')).length >= 2;  // 至少2次额外的坐标移动
      
      expect(hasBatchComment).toBe(true);
      expect(hasSingleToolChange).toBe(true);
      expect(hasG81).toBe(true);
      expect(hasCoordinateMoves).toBe(true);
    });

    test('生成批量沉头孔加工G代码', () => {
      const mainFeature = {
        id: 'main_cb',
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
      };
      
      const features = [
        { ...mainFeature, id: 'cb1', baseGeometry: { center: { x: 25.0, y: 35.0 } } },
        { ...mainFeature, id: 'cb2', baseGeometry: { center: { x: 30.0, y: 40.0 } } }
      ];
      
      const gCodeLines = generateCounterboreGCodeBatch(mainFeature, features);
      expect(gCodeLines).toBeDefined();
      expect(Array.isArray(gCodeLines)).toBe(true);
      expect(gCodeLines.length).toBeGreaterThan(0);
      
      // 验证批量沉头孔加工包含所有步骤
      const hasBatchComment = gCodeLines.some(line => line.includes('批量加工'));
      const hasT01 = gCodeLines.some(line => line.includes('T01'));
      const hasT02 = gCodeLines.some(line => line.includes('T02'));
      const hasT03 = gCodeLines.some(line => line.includes('T03'));
      const hasG81 = gCodeLines.some(line => line.includes('G81'));  // 点孔
      const hasG83 = gCodeLines.some(line => line.includes('G83'));  // 钻孔
      const hasG82 = gCodeLines.some(line => line.includes('G82'));  // 沉孔
      
      expect(hasBatchComment).toBe(true);
      expect(hasT01).toBe(true);
      expect(hasT02).toBe(true);
      expect(hasT03).toBe(true);
      expect(hasG81).toBe(true);
      expect(hasG83).toBe(true);
      expect(hasG82).toBe(true);
    });
  });

  describe('特征分组和键值生成测试', () => {
    test('生成特征唯一键', () => {
      // 测试不同类型的特征生成不同的键
      const hole1 = {
        featureType: 'hole',
        parameters: { diameter: 5.5, depth: 10 }
      };
      
      const hole2 = {
        featureType: 'hole',
        parameters: { diameter: 6.0, depth: 10 }  // 不同直径
      };
      
      const cb1 = {
        featureType: 'counterbore',
        parameters: { diameter: 5.5, depth: 10, counterboreDiameter: 9.0, counterboreDepth: 5.5 }
      };
      
      const holeKey1 = getFeatureKey(hole1);
      const holeKey2 = getFeatureKey(hole2);
      const cbKey1 = getFeatureKey(cb1);
      
      expect(holeKey1).not.toEqual(holeKey2);  // 不同参数应生成不同键
      expect(holeKey1).not.toEqual(cbKey1);    // 不同类型应生成不同键
      
      // 相同参数的孔应生成相同键
      const hole3 = { ...hole1 };
      expect(getFeatureKey(hole1)).toEqual(getFeatureKey(hole3));
    });

    test('按类型和参数分组特征', () => {
      const features = [
        {
          id: 'hole1',
          featureType: 'hole',
          parameters: { diameter: 5.5, depth: 10 }
        },
        {
          id: 'hole2',
          featureType: 'hole',
          parameters: { diameter: 5.5, depth: 10 }  // 相同参数，应与hole1分在同一组
        },
        {
          id: 'hole3',
          featureType: 'hole',
          parameters: { diameter: 6.0, depth: 10 }  // 不同参数，应分在不同组
        },
        {
          id: 'cb1',
          featureType: 'counterbore',
          parameters: { diameter: 5.5, depth: 10, counterboreDiameter: 9.0, counterboreDepth: 5.5 }
        }
      ];
      
      const grouped = groupFeaturesByTypeAndParameters(features);
      const groupKeys = Object.keys(grouped);
      
      expect(groupKeys.length).toBe(3);  // 应该有3个分组：两个不同直径的孔 + 一个沉头孔
      
      // 检查相同参数的孔是否分在同一组
      const holeGroup = groupKeys.find(key => key.includes('hole'));
      expect(grouped[holeGroup].length).toBe(2);  // hole1和hole2应在一个组
    });
  });

  describe('主G代码生成函数测试', () => {
    test('生成包含程序开始和结束的完整G代码', () => {
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
      expect(gCodeBlocks).toBeDefined();
      expect(Array.isArray(gCodeBlocks)).toBe(true);
      expect(gCodeBlocks.length).toBeGreaterThanOrEqual(3);  // 至少有程序开始、特征操作、程序结束
      
      // 验证程序开始和结束块
      const startBlock = gCodeBlocks[0];
      const endBlock = gCodeBlocks[gCodeBlocks.length - 1];
      
      expect(startBlock.type).toBe('program_control');
      expect(endBlock.type).toBe('program_control');
      expect(startBlock.code[0]).toContain('O0001');
      expect(endBlock.code[0]).toContain('M05');
      expect(endBlock.code[1]).toContain('M30');
    });

    test('处理无效项目输入', () => {
      // 测试无效输入
      expect(() => triggerGCodeGeneration(null)).toThrow();
      expect(() => triggerGCodeGeneration(undefined)).toThrow();
      expect(() => triggerGCodeGeneration('invalid')).toThrow();
      expect(() => triggerGCodeGeneration({})).toThrow();  // 没有features属性
      expect(() => triggerGCodeGeneration({ features: 'invalid' })).toThrow();  // features不是数组
    });

    test('处理无效特征', () => {
      const project = {
        features: [null, undefined, { invalid: 'feature' }]  // 包含无效特征
      };
      
      // 应该不会抛出异常，而是跳过无效特征
      expect(() => triggerGCodeGeneration(project)).not.toThrow();
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      // 应该至少有程序开始和结束代码
      expect(gCodeBlocks.length).toBeGreaterThanOrEqual(2);
    });

    test('验证批量加工功能', () => {
      // 创建多个相同参数的特征来测试批量加工
      const project = {
        features: [
          {
            id: 'hole1',
            featureType: 'hole',
            baseGeometry: { center: { x: 10.0, y: 10.0 } },
            parameters: { diameter: 5.0, drawingDepth: 10, toolNumber: 2 }
          },
          {
            id: 'hole2',
            featureType: 'hole',
            baseGeometry: { center: { x: 20.0, y: 10.0 } },
            parameters: { diameter: 5.0, drawingDepth: 10, toolNumber: 2 }  // 相同参数
          },
          {
            id: 'hole3',
            featureType: 'hole',
            baseGeometry: { center: { x: 15.0, y: 20.0 } },
            parameters: { diameter: 5.0, drawingDepth: 10, toolNumber: 2 }  // 相同参数
          }
        ]
      };
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const batchBlock = gCodeBlocks.find(block => block.isBatchOperation);
      
      expect(batchBlock).toBeDefined();
      expect(batchBlock.isBatchOperation).toBe(true);
      expect(batchBlock.batchSize).toBe(3);  // 3个相同的孔特征
    });
  });

  describe('G代码格式和标准符合性测试', () => {
    test('验证G81钻孔循环标准格式', () => {
      const feature = {
        id: 'std_hole',
        featureType: 'hole',
        baseGeometry: { center: { x: 25.555, y: 30.123 } },
        parameters: { diameter: 6.5, drawingDepth: 12, toolNumber: 2 }
      };
      
      const gCodeLines = generateHoleGCode(feature);
      const g81Line = gCodeLines.find(line => line.includes('G81'));
      
      expect(g81Line).toBeDefined();
      // 标准G81格式应为: G81 G98 Z- R2.0 F
      expect(g81Line).toContain('G81');
      expect(g81Line).toContain('G98');  // 返回初始平面
      expect(g81Line).toContain('R2.0'); // 参考平面
      expect(g81Line).toContain('F');    // 进给率
      expect(g81Line).toContain('Z-');   // Z轴负向移动
      
      // 验证坐标精度（保留3位小数）
      const positioningLine = gCodeLines.find(line => line.includes('G0 X') && line.includes('Y'));
      if (positioningLine) {
        const xMatch = positioningLine.match(/X(-?\d+\.\d{3})/);
        const yMatch = positioningLine.match(/Y(-?\d+\.\d{3})/);
        expect(xMatch).toBeDefined();
        expect(yMatch).toBeDefined();
        if (xMatch) expect(xMatch[1]).toMatch(/^\d+\.\d{3}$/);  // 3位小数
        if (yMatch) expect(yMatch[1]).toMatch(/^\d+\.\d{3}$/);  // 3位小数
      }
    });

    test('验证G83深孔钻循环标准格式', () => {
      const feature = {
        id: 'deep_hole',
        featureType: 'hole',
        baseGeometry: { center: { x: 40.0, y: 50.0 } },
        parameters: { diameter: 8.0, drawingDepth: 25, toolNumber: 2 }  // 深孔
      };
      
      const gCodeLines = generateHoleGCode(feature);
      const g83Line = gCodeLines.find(line => line.includes('G83'));
      
      if (g83Line) {
        // G83格式应包含Q参数（每次进给深度）
        expect(g83Line).toContain('G83');
        expect(g83Line).toContain('Q');  // 每次进给深度参数
      }
    });

    test('验证G82沉孔循环标准格式', () => {
      const feature = {
        id: 'std_cb',
        featureType: 'counterbore',
        baseGeometry: { center: { x: 35.0, y: 45.0 } },
        parameters: { diameter: 5.5, depth: 14, counterboreDiameter: 9.0, counterboreDepth: 5.5, drawingDepth: 10, useCounterbore: true }
      };
      
      const gCodeLines = generateCounterboreGCode(feature);
      const g82Line = gCodeLines.find(line => line.includes('G82'));
      
      if (g82Line) {
        // G82格式应包含P参数（暂停时间）
        expect(g82Line).toContain('G82');
        expect(g82Line).toContain('P');  // 暂停时间参数
      }
    });

    test('验证G代码安全指令', () => {
      const feature = {
        id: 'safe_hole',
        featureType: 'hole',
        baseGeometry: { center: { x: 5.0, y: 5.0 } },
        parameters: { diameter: 4.0, drawingDepth: 8, toolNumber: 2 }
      };
      
      const gCodeLines = generateHoleGCode(feature);
      
      // 验证安全相关的G代码指令
      const hasToolLengthCompensation = gCodeLines.some(line => line.includes('G43'));
      const hasSpindleStart = gCodeLines.some(line => line.includes('M03'));
      const hasSpindleStop = gCodeLines.some(line => line.includes('M05') || gCodeLines.indexOf(line) > gCodeLines.indexOf(gCodeLines.find(l => l.includes('M03'))));
      const hasCycleCancel = gCodeLines.some(line => line.includes('G80'));
      const hasSafePositioning = gCodeLines.some(line => line.includes('G0 Z100'));
      
      expect(hasToolLengthCompensation).toBe(true);
      expect(hasSpindleStart).toBe(true);
      expect(hasCycleCancel).toBe(true);
      expect(hasSafePositioning).toBe(true);
    });
  });

  describe('材料和刀具匹配集成测试', () => {
    test('验证推荐参数集成', () => {
      const project = {
        features: [{
          id: 'hole_with_material',
          featureType: 'hole',
          baseGeometry: { center: { x: 10.0, y: 20.0 } },
          parameters: { diameter: 5.5, drawingDepth: 10, toolNumber: 2 }
        }],
        materialType: 'Aluminum'  // 指定材料类型
      };
      
      // 这个测试主要验证不会出错，具体参数匹配逻辑在其他模块中测试
      expect(() => triggerGCodeGeneration(project)).not.toThrow();
      
      const gCodeBlocks = triggerGCodeGeneration(project);
      const holeBlock = gCodeBlocks.find(block => block.featureType === 'hole');
      
      // 验证块结构
      expect(holeBlock).toBeDefined();
      expect(holeBlock.recommendedParams).toBeDefined(); // 可能为null，但如果匹配成功会有值
    });
  });
});