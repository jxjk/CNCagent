// test/integration.test.js
// 集成测试 - 测试模块间的交互

const { Project, initializeProject, clearWorkspace, handleDrawingImport } = require('../src/modules/projectInitialization');
const { pdfParsingProcess } = require('../src/modules/subprocesses/pdfParsingProcess');
const { selectFeature, startFeatureDefinition, selectFeatureType, associateMacroVariable } = require('../src/modules/featureDefinition');
const { triggerGCodeGeneration } = require('../src/modules/gCodeGeneration');
const { startSimulation, variableDrivenSimulation, exportCode } = require('../src/modules/simulationOutput');

describe('集成测试 - 完整工作流程', () => {
  let project;
  let tempFilePath;

  beforeAll(() => {
    // 创建临时测试文件 - 使用有效的PDF结构
    const fs = require('fs');
    const path = require('path');
    tempFilePath = path.join(__dirname, 'integration_test.pdf');
    const validPdfContent = `%PDF-1.5
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
/Length 200
>>
stream
BT
/F1 12 Tf
100 700 Td
(Integration Test Drawing) Tj
100 650 Td
(Rectangle: 100 x 50 mm) Tj
100 600 Td
(Circle: R25 mm) Tj
100 550 Td
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
0000000321 00000 n 
trailer
<<
/Size 6
/Root 1 0 R
/Info null
>>
startxref
400
%%EOF`;
    fs.writeFileSync(tempFilePath, validPdfContent);
  });

  afterAll(() => {
    // 清理临时测试文件
    const fs = require('fs');
    if (fs.existsSync(tempFilePath)) {
      fs.unlinkSync(tempFilePath);
    }
    clearWorkspace();
  });

  beforeEach(() => {
    clearWorkspace();
  });

  test('应能够完成从项目初始化到G代码导出的完整流程', async () => {
    // 1. 初始化项目
    project = initializeProject('Integration Test Project');
    expect(project).toBeDefined();
    expect(project.name).toBe('Integration Test Project');

    // 2. 导入图纸
    project = await handleDrawingImport(tempFilePath);
    expect(project.filePath).toBe(tempFilePath);

    // 3. 解析图纸
    const parsingResult = await pdfParsingProcess(project.filePath);
    expect(parsingResult).toBeDefined();
    expect(Array.isArray(parsingResult.geometryElements)).toBe(true);

    // 更新项目数据
    project.drawingInfo = parsingResult.drawingInfo;
    project.geometryElements = parsingResult.geometryElements;
    project.dimensions = parsingResult.dimensions;

    // 4. 选择特征
    if (project.geometryElements.length > 0) {
      const selectedFeature = selectFeature(project, 30, 30); // 假设有一个元素在该位置
      if (selectedFeature) {
        // 5. 开始特征定义
        const feature = startFeatureDefinition(project, selectedFeature.element, project.dimensions);
        expect(feature).toBeDefined();
        
        // 6. 选择特征类型
        selectFeatureType(feature, 'hole');
        expect(feature.featureType).toBe('hole');

        // 7. 关联宏变量
        associateMacroVariable(feature, 'dim_1', 'HOLE_DIAMETER');
        expect(feature.macroVariables.dim_1).toBe('HOLE_DIAMETER');

        // 将特征添加到项目中
        if (!Array.isArray(project.features)) {
          project.features = [];
        }
        project.features.push(feature);
      }
    }

    // 8. 生成G代码
    const gCodeBlocks = triggerGCodeGeneration(project);
    expect(gCodeBlocks).toBeDefined();
    expect(Array.isArray(gCodeBlocks)).toBe(true);
    expect(gCodeBlocks.length).toBeGreaterThan(0);

    // 9. 更新项目G代码
    project.gCodeBlocks = gCodeBlocks;

    // 10. 运行模拟
    const simulationResults = startSimulation(project.gCodeBlocks);
    expect(simulationResults).toBeDefined();
    expect(simulationResults.status).toBe('completed');

    // 11. 运行变量驱动模拟
    const variableValues = { HOLE_DIAMETER: 15 };
    const variableSimulationResults = variableDrivenSimulation(project.gCodeBlocks, variableValues);
    expect(variableSimulationResults).toBeDefined();
    expect(variableSimulationResults.status).toBe('completed');

    // 12. 导出代码
    const exportResult = exportCode(project.gCodeBlocks);
    expect(exportResult).toBeDefined();
    expect(exportResult.success).toBe(true);
    expect(exportResult.gCode).toBeDefined();
  });

  test('应验证模块间数据传递的一致性', async () => {
    // 初始化项目
    project = initializeProject('Data Consistency Test');
    expect(project).toBeDefined();

    // 导入图纸
    project = await handleDrawingImport(tempFilePath);
    expect(project.filePath).toBe(tempFilePath);

    // 解析图纸
    const parsingResult = await pdfParsingProcess(project.filePath);
    expect(parsingResult).toBeDefined();
    
    // 验证解析结果被正确传递到项目
    project.drawingInfo = parsingResult.drawingInfo;
    project.geometryElements = parsingResult.geometryElements;
    project.dimensions = parsingResult.dimensions;
    
    expect(project.drawingInfo).toEqual(parsingResult.drawingInfo);
    expect(project.geometryElements).toEqual(parsingResult.geometryElements);
    expect(project.dimensions).toEqual(parsingResult.dimensions);

    // 选择特征并验证
    if (project.geometryElements.length > 0) {
      const selectedFeature = selectFeature(project, 30, 30);
      if (selectedFeature) {
        // 验证特征定义与选择的元素一致
        const feature = startFeatureDefinition(project, selectedFeature.element, project.dimensions);
        expect(feature.baseGeometry).toEqual(selectedFeature.element);
        
        // 添加到项目特征列表
        if (!Array.isArray(project.features)) {
          project.features = [];
        }
        project.features.push(feature);
      }
    }

    // 验证G代码生成使用了正确的特征数据
    const gCodeBlocks = triggerGCodeGeneration(project);
    expect(gCodeBlocks).toBeDefined();
    
    // 验证模拟使用了正确的G代码
    const simulationResults = startSimulation(gCodeBlocks);
    expect(simulationResults.totalCommands).toBe(gCodeBlocks.length);
  });

  test('应验证错误处理在模块间的传递', () => {
    // 测试无效输入的错误传递
    expect(() => {
      selectFeature(null, 10, 10);
    }).toThrow('项目参数无效');

    expect(() => {
      startFeatureDefinition(null, {}, []);
    }).toThrow('项目参数无效');

    expect(() => {
      selectFeatureType(null, 'hole');
    }).toThrow('特征参数无效');

    expect(() => {
      associateMacroVariable(null, 'dim_1', 'VAR');
    }).toThrow('特征参数无效');
  });

  test('应验证项目状态在各模块操作后的正确性', async () => {
    // 初始化
    project = initializeProject('State Test Project');
    expect(project).toBeDefined();
    expect(project.features).toEqual([]);
    expect(project.gCodeBlocks).toEqual([]);

    // 解析图纸
    const parsingResult = await pdfParsingProcess(tempFilePath);
    project.drawingInfo = parsingResult.drawingInfo;
    project.geometryElements = parsingResult.geometryElements;
    project.dimensions = parsingResult.dimensions;
    
    expect(project.geometryElements).toBeDefined();
    expect(project.dimensions).toBeDefined();

    // 创建特征
    if (project.geometryElements.length > 0) {
      const selectedFeature = selectFeature(project, 30, 30);
      if (selectedFeature) {
        const feature = startFeatureDefinition(project, selectedFeature.element, project.dimensions);
        selectFeatureType(feature, 'pocket');
        associateMacroVariable(feature, 'dim_1', 'POCKET_WIDTH');
        
        // 添加到项目
        if (!Array.isArray(project.features)) {
          project.features = [];
        }
        project.features.push(feature);
      }
    }

    // 验证特征已添加到项目
    expect(Array.isArray(project.features)).toBe(true);
    if (project.features.length > 0) {
      expect(project.features[0].featureType).toBe('pocket');
      expect(project.features[0].macroVariables.dim_1).toBe('POCKET_WIDTH');
    }

    // 验证G代码生成
    const gCodeBlocks = triggerGCodeGeneration(project);
    project.gCodeBlocks = gCodeBlocks;
    expect(Array.isArray(project.gCodeBlocks)).toBe(true);
    expect(project.gCodeBlocks.length).toBeGreaterThan(0);
  });
});