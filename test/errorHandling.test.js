// test\errorHandling.test.js
// 错误处理测试 - 验证错误处理机制

const { Project, initializeProject, clearWorkspace, handleDrawingImport } = require('../src/modules/projectInitialization');
const { pdfParsingProcess } = require('../src/modules/subprocesses/pdfParsingProcess');
const { selectFeature, startFeatureDefinition, selectFeatureType, associateMacroVariable } = require('../src/modules/featureDefinition');
const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
const { startSimulation, variableDrivenSimulation, exportCode } = require('../src/modules/simulationOutput');
const { CNCStateManager } = require('../src/index');

describe('错误处理测试 - 项目初始化模块', () => {
  beforeEach(() => {
    clearWorkspace();
  });

  test('应正确处理无效的项目名称', () => {
    expect(() => {
      initializeProject(null);
    }).toThrow('项目名必须是字符串');

    expect(() => {
      initializeProject(123);
    }).toThrow('项目名必须是字符串');

    expect(() => {
      initializeProject({});
    }).toThrow('项目名必须是字符串');
  });

  test('应正确处理不存在的文件导入', async () => {
    await expect(handleDrawingImport('nonexistent.pdf')).rejects.toThrow('文件不存在');
  });

  test('应正确处理无效的文件路径', async () => {
    await expect(handleDrawingImport(null)).rejects.toThrow('文件路径无效');
    await expect(handleDrawingImport(123)).rejects.toThrow('文件路径无效');
    await expect(handleDrawingImport({})).rejects.toThrow('文件路径无效');
  });

  test('应正确处理不支持的文件格式', async () => {
    // 创建一个临时的不支持的文件
    const fs = require('fs');
    const path = require('path');
    const unsupportedFilePath = path.join(__dirname, 'unsupported.xyz');
    
    fs.writeFileSync(unsupportedFilePath, 'dummy content');
    
    try {
      await expect(handleDrawingImport(unsupportedFilePath)).rejects.toThrow('不支持的文件格式');
    } finally {
      if (fs.existsSync(unsupportedFilePath)) {
        fs.unlinkSync(unsupportedFilePath);
      }
    }
  });
});

describe('错误处理测试 - PDF解析模块', () => {
  test('应正确处理无效的文件路径', async () => {
    await expect(pdfParsingProcess(null)).rejects.toThrow('文件路径无效');
    await expect(pdfParsingProcess(123)).rejects.toThrow('文件路径无效');
    await expect(pdfParsingProcess({})).rejects.toThrow('文件路径无效');
  });

  test('应正确处理不存在的文件', async () => {
    await expect(pdfParsingProcess('nonexistent.pdf')).rejects.toThrow('文件不存在');
  });
});

describe('错误处理测试 - 特征定义模块', () => {
  test('应正确处理无效的selectFeature参数', () => {
    expect(() => {
      selectFeature(null, 10, 10);
    }).toThrow('项目参数无效');

    expect(() => {
      selectFeature({}, null, 10);
    }).toThrow('坐标参数必须是数字');

    expect(() => {
      selectFeature({}, 10, null);
    }).toThrow('坐标参数必须是数字');

    expect(() => {
      selectFeature({}, 'invalid', 10);
    }).toThrow('坐标参数必须是数字');

    expect(() => {
      selectFeature({}, 10, 'invalid');
    }).toThrow('坐标参数必须是数字');
  });

  test('应正确处理无效的startFeatureDefinition参数', () => {
    expect(() => {
      startFeatureDefinition(null, {}, []);
    }).toThrow('项目参数无效');

    expect(() => {
      startFeatureDefinition({}, null, []);
    }).toThrow('元素参数无效');

    expect(() => {
      startFeatureDefinition({}, 'invalid', []);
    }).toThrow('元素参数无效');
  });

  test('应正确处理无效的selectFeatureType参数', () => {
    const feature = { id: 'test', parameters: {} };
    
    expect(() => {
      selectFeatureType(null, 'hole');
    }).toThrow('特征参数无效');

    expect(() => {
      selectFeatureType(feature, null);
    }).toThrow('特征类型参数无效');

    expect(() => {
      selectFeatureType(feature, 123);
    }).toThrow('特征类型参数无效');

    expect(() => {
      selectFeatureType(feature, 'invalid_type');
    }).toThrow('不支持的特征类型');
  });

  test('应正确处理无效的associateMacroVariable参数', () => {
    const feature = { id: 'test' };
    
    expect(() => {
      associateMacroVariable(null, 'dim1', 'VAR');
    }).toThrow('特征参数无效');

    expect(() => {
      associateMacroVariable(feature, null, 'VAR');
    }).toThrow('尺寸ID参数无效');

    expect(() => {
      associateMacroVariable(feature, 123, 'VAR');
    }).toThrow('尺寸ID参数无效');

    expect(() => {
      associateMacroVariable(feature, 'dim1', null);
    }).toThrow('变量名参数无效');

    expect(() => {
      associateMacroVariable(feature, 'dim1', 123);
    }).toThrow('变量名参数无效');

    expect(() => {
      associateMacroVariable(feature, 'dim1', '123invalid'); // 以数字开头的变量名
    }).toThrow('变量名格式无效');
  });
});

describe('错误处理测试 - G代码生成模块', () => {
  test('应正确处理无效的triggerGCodeGeneration参数', () => {
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
});

describe('错误处理测试 - 模拟输出模块', () => {
  test('应正确处理无效的startSimulation参数', () => {
    expect(() => {
      startSimulation(null);
    }).toThrow('G代码块列表无效');

    expect(() => {
      startSimulation('invalid');
    }).toThrow('G代码块列表无效');

    expect(() => {
      startSimulation({});
    }).toThrow('G代码块列表无效');
  });

  test('应正确处理无效的variableDrivenSimulation参数', () => {
    expect(() => {
      variableDrivenSimulation(null, {});
    }).toThrow('G代码块列表无效');

    expect(() => {
      variableDrivenSimulation('invalid', {});
    }).toThrow('G代码块列表无效');

    expect(() => {
      variableDrivenSimulation([], null);
    }).toThrow('变量值参数无效');

    expect(() => {
      variableDrivenSimulation([], 'invalid');
    }).toThrow('变量值参数无效');
  });

  test('应正确处理无效的exportCode参数', () => {
    expect(() => {
      exportCode(null);
    }).toThrow('G代码块列表无效');

    expect(() => {
      exportCode('invalid');
    }).toThrow('G代码块列表无效');

    expect(() => {
      exportCode({});
    }).toThrow('G代码块列表无效');
  });
});

describe('错误处理测试 - 状态管理器', () => {
  let stateManager;

  beforeEach(() => {
    stateManager = new CNCStateManager();
  });

  test('应正确处理无效的状态设置', () => {
    // 对于null和非字符串值，类会记录错误但不会抛出异常
    const originalConsoleError = console.error;
    console.error = jest.fn(); // 模拟console.error
    
    stateManager.setState(null);
    expect(console.error).toHaveBeenCalledWith('无效的状态值');
    
    stateManager.setState(123);
    expect(console.error).toHaveBeenCalledWith('无效的状态值');
    
    stateManager.setState('invalid_state');
    expect(console.error).toHaveBeenCalledWith('无效的状态: invalid_state');
    
    console.error = originalConsoleError; // 恢复原始console.error
  });

  test('应正确处理无效的项目导入', async () => {
    // 模拟console.error以避免测试中的console输出
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    const result = await stateManager.handleImport(null);
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();

    const result2 = await stateManager.handleImport(123);
    expect(result2.success).toBe(false);
    expect(result2.error).toBeDefined();
    
    console.error = originalConsoleError; // 恢复原始console.error
  });

  test('应正确处理无效的特征选择', () => {
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    const result = stateManager.handleFeatureSelection(null, 10);
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();

    const result2 = stateManager.handleFeatureSelection(10, null);
    expect(result2.success).toBe(false);
    expect(result2.error).toBeDefined();

    const result3 = stateManager.handleFeatureSelection('invalid', 10);
    expect(result3.success).toBe(false);
    expect(result3.error).toBeDefined();
    
    console.error = originalConsoleError;
  });

  test('应正确处理无效的状态转换', () => {
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    // 尝试在错误状态下执行操作
    const result = stateManager.startFeatureDefinition();
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
    expect(result.error).toContain('当前状态');
    
    console.error = originalConsoleError;
  });

  test('应正确处理无效的特征类型选择', () => {
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    const result = stateManager.selectFeatureType(null, 'hole');
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();

    const result2 = stateManager.selectFeatureType(123, 'hole');
    expect(result2.success).toBe(false);
    expect(result2.error).toBeDefined();
    
    console.error = originalConsoleError;
  });

  test('应正确处理无效的宏变量关联', () => {
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    const result = stateManager.associateMacroVariable(null, 'dim1', 'VAR');
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();

    const result2 = stateManager.associateMacroVariable(123, 'dim1', 'VAR');
    expect(result2.success).toBe(false);
    expect(result2.error).toBeDefined();
    
    console.error = originalConsoleError;
  });

  test('应正确处理无效的G代码生成', () => {
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    const result = stateManager.generateGCode();
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
    
    console.error = originalConsoleError;
  });

  test('应正确处理无效的模拟运行', () => {
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    const result = stateManager.runSimulation();
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
    
    console.error = originalConsoleError;
  });

  test('应正确处理无效的代码导出', () => {
    const originalConsoleError = console.error;
    console.error = jest.fn();
    
    const result = stateManager.exportCode();
    expect(result.success).toBe(false);
    expect(result.error).toBeDefined();
    
    console.error = originalConsoleError;
  });
});

describe('错误处理测试 - 边界情况', () => {
  test('应处理极值坐标选择', () => {
    const project = {
      geometryElements: [
        { id: 'line_1', type: 'line', start: { x: 0, y: 0 }, end: { x: 100, y: 100 } }
      ]
    };

    // 测试极大值坐标
    const result1 = selectFeature(project, Number.MAX_SAFE_INTEGER, Number.MAX_SAFE_INTEGER);
    expect(result1).toBeDefined(); // 不应抛出异常，即使找不到特征

    // 测试极小值坐标
    const result2 = selectFeature(project, Number.MIN_SAFE_INTEGER, Number.MIN_SAFE_INTEGER);
    expect(result2).toBeDefined();
  });

  test('应处理空数组输入', () => {
    const project = {
      geometryElements: []
    };

    const result = selectFeature(project, 10, 10);
    expect(result).toBeNull();
  });

  test('应处理包含无效元素的数组', () => {
    const project = {
      geometryElements: [
        null,
        undefined,
        { id: 'valid', type: 'line', start: { x: 0, y: 0 }, end: { x: 10, y: 10 } }
      ]
    };

    const result = selectFeature(project, 5, 5);
    // 应该跳过无效元素，找到有效元素
    expect(result).toBeDefined();
  });
});