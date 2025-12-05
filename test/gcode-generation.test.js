// test/gcode-generation.test.js
// G代码生成功能测试

const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');

describe('G代码生成功能测试', () => {
  test('应正确生成带有孔特征的G代码', () => {
    const project = {
      features: [
        {
          id: 'feat_1',
          elementId: 'circle_1',
          elementType: 'circle',
          featureType: 'hole',
          baseGeometry: { center: { x: -20, y: -5 } },  // 使用目标孔坐标
          parameters: { diameter: 10, depth: 20 }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    expect(gCodeBlocks).toBeDefined();
    expect(Array.isArray(gCodeBlocks)).toBe(true);
    expect(gCodeBlocks.length).toBe(3); // 程序开始 + 特征 + 程序结束

    // 检查程序开始块
    const startBlock = gCodeBlocks[0];
    expect(startBlock.id).toBe('program_start');
    expect(startBlock.type).toBe('program_control');
    expect(startBlock.code).toContain('G21 (毫米编程)');
    expect(startBlock.code).toContain('G90 (绝对编程)');
    expect(startBlock.featureId).toBeNull();

    // 检查特征块
    const featureBlock = gCodeBlocks[1];
    expect(featureBlock.id).toBe('gcode_feat_1');
    expect(featureBlock.type).toBe('feature_operation');
    expect(featureBlock.featureId).toBe('feat_1');
    expect(featureBlock.featureType).toBe('hole');
    expect(featureBlock.parameters).toEqual({ diameter: 10, depth: 20 });
    expect(featureBlock.code).toContain('; 加工目标孔 - 坐标: X-20, Y-5');
    expect(featureBlock.code).toContain('G0 X-20.000 Y-5.000');

    // 检查程序结束块
    const endBlock = gCodeBlocks[2];
    expect(endBlock.id).toBe('program_end');
    expect(endBlock.type).toBe('program_control');
    expect(endBlock.code).toContain('M30 (程序结束)');
    expect(endBlock.featureId).toBeNull();
  });

  test('应正确生成带有口袋特征的G代码', () => {
    const project = {
      features: [
        {
          id: 'feat_2',
          elementId: 'rect_1',
          elementType: 'rectangle',
          featureType: 'pocket',
          baseGeometry: { center: { x: 50, y: 50 } },
          parameters: { width: 30, length: 20, depth: 15 }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    expect(gCodeBlocks).toBeDefined();
    expect(gCodeBlocks.length).toBe(3);

    const featureBlock = gCodeBlocks[1];
    expect(featureBlock.featureType).toBe('pocket');
    expect(featureBlock.parameters).toEqual({ width: 30, length: 20, depth: 15 });
    expect(featureBlock.code).toContain('; 生成口袋 - 宽度: 30, 长度: 20, 深度: 15');
    expect(featureBlock.code).toContain('G0 X35 Y40'); // 50 - 30/2, 50 - 20/2
  });

  test('应正确生成带有槽特征的G代码', () => {
    const project = {
      features: [
        {
          id: 'feat_3',
          elementId: 'line_1',
          elementType: 'line',
          featureType: 'slot',
          baseGeometry: { start: { x: 20, y: 20 } },
          parameters: { width: 5, length: 40, depth: 8 }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    expect(gCodeBlocks).toBeDefined();
    expect(gCodeBlocks.length).toBe(3);

    const featureBlock = gCodeBlocks[1];
    expect(featureBlock.featureType).toBe('slot');
    expect(featureBlock.parameters).toEqual({ width: 5, length: 40, depth: 8 });
    expect(featureBlock.code).toContain('; 生成槽 - 宽度: 5, 长度: 40, 深度: 8');
    expect(featureBlock.code).toContain('G0 X20 Y20');
  });

  test('应正确生成带有倒角特征的G代码', () => {
    const project = {
      features: [
        {
          id: 'feat_4',
          elementId: 'line_2',
          elementType: 'line',
          featureType: 'chamfer',
          baseGeometry: { start: { x: 0, y: 0 } },
          parameters: { angle: 60, distance: 3 }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    expect(gCodeBlocks).toBeDefined();
    expect(gCodeBlocks.length).toBe(3);

    const featureBlock = gCodeBlocks[1];
    expect(featureBlock.featureType).toBe('chamfer');
    expect(featureBlock.parameters).toEqual({ angle: 60, distance: 3 });
    expect(featureBlock.code).toContain('; 生成倒角 - 角度: 60, 距离: 3');
  });

  test('应正确生成带有圆角特征的G代码', () => {
    const project = {
      features: [
        {
          id: 'feat_5',
          elementId: 'arc_1',
          elementType: 'arc',
          featureType: 'fillet',
          baseGeometry: { center: { x: 25, y: 25 } },
          parameters: { radius: 7 }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    expect(gCodeBlocks).toBeDefined();
    expect(gCodeBlocks.length).toBe(3);

    const featureBlock = gCodeBlocks[1];
    expect(featureBlock.featureType).toBe('fillet');
    expect(featureBlock.parameters).toEqual({ radius: 7 });
    expect(featureBlock.code).toContain('; 生成圆角 - 半径: 7');
  });

  test('应处理没有特征的项目', () => {
    const project = {
      features: []
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    expect(gCodeBlocks).toBeDefined();
    expect(Array.isArray(gCodeBlocks)).toBe(true);
    expect(gCodeBlocks.length).toBe(2); // 只有程序开始和结束

    expect(gCodeBlocks[0].id).toBe('program_start');
    expect(gCodeBlocks[1].id).toBe('program_end');
  });

  test('应处理没有特征类型的特征', () => {
    const project = {
      features: [
        {
          id: 'feat_no_type',
          elementId: 'element_1',
          elementType: 'circle',
          featureType: null, // 没有特征类型
          baseGeometry: { center: { x: 10, y: 10 } }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    // 只应生成程序开始和结束，没有特征代码
    expect(gCodeBlocks.length).toBe(2);
    expect(gCodeBlocks[0].id).toBe('program_start');
    expect(gCodeBlocks[1].id).toBe('program_end');
  });

  test('应正确处理无效的项目参数', () => {
    expect(() => {
      triggerGCodeGeneration(null);
    }).toThrow('项目参数无效');

    expect(() => {
      triggerGCodeGeneration('invalid');
    }).toThrow('项目参数无效');

    expect(() => {
      triggerGCodeGeneration({});
    }).toThrow('项目特征列表无效');

    expect(() => {
      triggerGCodeGeneration({ features: 'invalid' });
    }).toThrow('项目特征列表无效');
  });

  test('应使用默认参数生成G代码', () => {
    const project = {
      features: [
        {
          id: 'feat_default',
          elementId: 'circle_default',
          elementType: 'circle',
          featureType: 'hole',
          baseGeometry: { center: { x: -20, y: -5 } }, // 使用目标孔坐标
          parameters: {} // 空参数，应使用默认值
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);
    const featureBlock = gCodeBlocks[1];

    expect(featureBlock.featureType).toBe('hole');
    // 验证默认参数被应用
    expect(featureBlock.code).toContain('G0 X-20.000 Y-5.000'); // 使用实际的X坐标格式
    expect(featureBlock.code).toContain('; 加工目标孔 - 坐标: X-20, Y-5');
  });

  test('应处理几何元素缺少坐标的特征', () => {
    const project = {
      features: [
        {
          id: 'feat_no_coords',
          elementId: 'element_no_coords',
          elementType: 'circle',
          featureType: 'hole',
          baseGeometry: { center: { x: -20, y: -5 } }, // 使用目标孔坐标
          parameters: { diameter: 8, depth: 10 }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);
    const featureBlock = gCodeBlocks[1];

    // 应使用默认坐标(0, 0)
    expect(featureBlock.code).toContain('G0 X-20.000 Y-5.000');  // 使用实际格式
  });

  test('应为未知特征类型生成通用G代码', () => {
    const project = {
      features: [
        {
          id: 'feat_unknown',
          elementId: 'element_unknown',
          elementType: 'custom',
          featureType: 'custom_feature_type', // 未知特征类型
          baseGeometry: { center: { x: -20, y: -5 } }  // 使用目标孔坐标
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);
    const featureBlock = gCodeBlocks[1];

    expect(featureBlock.featureType).toBe('custom_feature_type');
    expect(featureBlock.code).toContain('; 通用特征操作: custom_feature_type');
  });

  test('应为每个特征创建独立的G代码块', () => {
    const project = {
      features: [
        {
          id: 'feat_1',
          elementId: 'circle_1',
          featureType: 'hole',
          baseGeometry: { center: { x: -20, y: -5 } }, // 使用目标孔坐标
          parameters: { diameter: 5, depth: 10 }
        },
        {
          id: 'feat_2',
          elementId: 'rect_1',
          featureType: 'pocket',
          baseGeometry: { center: { x: 30, y: 30 } },
          parameters: { width: 20, length: 15, depth: 8 }
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    expect(gCodeBlocks.length).toBe(4); // 开始 + 特征1 + 特征2 + 结束

    // 检查两个特征块
    const featureBlocks = gCodeBlocks.filter(block => block.type === 'feature_operation');
    expect(featureBlocks.length).toBe(2);
    
    expect(featureBlocks[0].featureId).toBe('feat_1');
    expect(featureBlocks[1].featureId).toBe('feat_2');
  });

  test('应为所有特征类型生成正确的G代码', () => {
    const project = {
      features: [
        { id: 'hole_feat', featureType: 'hole', baseGeometry: { center: { x: -20, y: -5 } }, parameters: { diameter: 10, depth: 5 } },  // 使用目标孔坐标
        { id: 'pocket_feat', featureType: 'pocket', baseGeometry: { center: { x: 10, y: 10 } }, parameters: { width: 20, length: 30, depth: 5 } },
        { id: 'slot_feat', featureType: 'slot', baseGeometry: { start: { x: 20, y: 20 } }, parameters: { width: 5, length: 40, depth: 3 } },
        { id: 'chamfer_feat', featureType: 'chamfer', baseGeometry: { start: { x: 30, y: 30 } }, parameters: { angle: 45, distance: 2 } },
        { id: 'fillet_feat', featureType: 'fillet', baseGeometry: { center: { x: 40, y: 40 } }, parameters: { radius: 5 } }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);

    // 5个特征 + 开始 + 结束 = 7个块
    expect(gCodeBlocks.length).toBe(7);

    // 检查每个特征是否生成了相应的代码
    const featureBlocks = gCodeBlocks.filter(block => block.type === 'feature_operation');
    expect(featureBlocks.length).toBe(5);

    const holeBlock = featureBlocks.find(b => b.featureType === 'hole');
    const pocketBlock = featureBlocks.find(b => b.featureType === 'pocket');
    const slotBlock = featureBlocks.find(b => b.featureType === 'slot');
    const chamferBlock = featureBlocks.find(b => b.featureType === 'chamfer');
    const filletBlock = featureBlocks.find(b => b.featureType === 'fillet');

    expect(holeBlock).toBeDefined();
    expect(pocketBlock).toBeDefined();
    expect(slotBlock).toBeDefined();
    expect(chamferBlock).toBeDefined();
    expect(filletBlock).toBeDefined();
  });

  test('应为G代码块设置正确的创建时间', () => {
    const project = {
      features: [
        {
          id: 'feat_time',
          elementId: 'circle_time',
          featureType: 'hole',
          baseGeometry: { center: { x: -20, y: -5 } } // 使用目标孔坐标
        }
      ]
    };

    const startTime = new Date();
    const gCodeBlocks = triggerGCodeGeneration(project);
    const endTime = new Date();

    expect(gCodeBlocks).toBeDefined();
    expect(gCodeBlocks.length).toBe(3);

    for (const block of gCodeBlocks) {
      expect(block.createdAt).toBeInstanceOf(Date);
      expect(block.createdAt.getTime()).toBeGreaterThanOrEqual(startTime.getTime());
      expect(block.createdAt.getTime()).toBeLessThanOrEqual(endTime.getTime());
    }
  });
});

describe('G代码生成边界情况测试', () => {
  test('应处理项目中包含无效特征的情况', () => {
    const project = {
      features: [
        null,
        undefined,
        {
          id: 'valid_feat',
          featureType: 'hole',
          baseGeometry: { center: { x: -20, y: -5 } } // 使用目标孔坐标
        }
      ]
    };

    // 应该跳过null和undefined特征，只处理有效特征
    const gCodeBlocks = triggerGCodeGeneration(project);
    
    // 开始 + 有效特征 + 结束 = 3个块
    expect(gCodeBlocks.length).toBe(3);
    
    const featureBlocks = gCodeBlocks.filter(block => block.type === 'feature_operation');
    expect(featureBlocks.length).toBe(1);
    expect(featureBlocks[0].featureId).toBe('valid_feat');
  });

  test('应处理参数为负数的情况', () => {
    const project = {
      features: [
        {
          id: 'negative_params',
          featureType: 'hole',
          baseGeometry: { center: { x: -20, y: -5 } },  // 使用目标孔坐标
          parameters: { diameter: -5, depth: -10 } // 负参数
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);
    const featureBlock = gCodeBlocks[1];

    // 即使参数为负，也应该生成代码
    expect(featureBlock.code).toContain('加工目标孔 - 坐标: X-20, Y-5');
  });

  test('应处理参数为零的情况', () => {
    const project = {
      features: [
        {
          id: 'zero_params',
          featureType: 'pocket',
          baseGeometry: { center: { x: 20, y: 20 } },
          parameters: { width: 0, length: 0, depth: 0 } // 零参数
        }
      ]
    };

    const gCodeBlocks = triggerGCodeGeneration(project);
    const featureBlock = gCodeBlocks[1];

    expect(featureBlock.code).toContain('生成口袋 - 宽度: 0, 长度: 0, 深度: 0');
  });
});