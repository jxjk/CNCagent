// src/index.js
// 主应用入口和状态管理

const express = require('express');
const rateLimit = require('express-rate-limit'); // 防止请求泛洪
const { 
  Project, 
  initializeProject, 
  clearWorkspace, 
  handleDrawingImport 
} = require('./modules/projectInitialization');
const { 
  pdfParsingProcess 
} = require('./modules/subprocesses/pdfParsingProcess');
const { 
  selectFeature, 
  startFeatureDefinition, 
  selectFeatureType, 
  associateMacroVariable 
} = require('./modules/featureDefinition');
const { 
  triggerGCodeGeneration 
} = require('./modules/gCodeGeneration');
const { 
  startSimulation, 
  variableDrivenSimulation, 
  exportCode 
} = require('./modules/simulationOutput');

class CNCStateManager {
  constructor() {
    this.state = 'waiting_import'; // 等待导入
    this.project = null;
    this.selectedFeature = null; // 保持兼容性
    this.selectedFeatures = []; // 新增：支持多个特征选择
    this.stateHistory = ['waiting_import']; // 状态历史，用于回溯
    this.maxStateHistory = 10; // 最大状态历史记录数
  }

  // 状态转换方法
  setState(newState) {
    if (!newState || typeof newState !== 'string') {
      console.error('无效的状态值');
      return;
    }
    
    const validStates = [
      'waiting_import', 'drawing_loaded', 'processing', 'ready', 
      'feature_selected', 'defining_feature', 'code_generated', 
      'simulation_running', 'code_exported', 'error'
    ];
    
    if (!validStates.includes(newState)) {
      console.error(`无效的状态: ${newState}`);
      return;
    }
    
    console.log(`状态从 ${this.state} 转换到 ${newState}`);
    this.state = newState;
    
    // 更新状态历史
    this.stateHistory.push(newState);
    if (this.stateHistory.length > this.maxStateHistory) {
      this.stateHistory.shift();
    }
  }

  // 获取允许的状态转换
  getAllowedTransitions() {
    const transitions = {
      'waiting_import': ['drawing_loaded', 'error'],
      'drawing_loaded': ['processing', 'error'],
      'processing': ['ready', 'error'],
      'ready': ['feature_selected', 'code_generated', 'error'],
      'feature_selected': ['defining_feature', 'ready', 'feature_selected', 'error'], // 允许保持在相同状态以选择更多特征
      'defining_feature': ['ready', 'code_generated', 'feature_selected', 'error'], // 允许返回到特征选择状态
      'code_generated': ['simulation_running', 'code_exported', 'error'],
      'simulation_running': ['code_generated', 'code_exported', 'error'],
      'code_exported': ['waiting_import'],
      'error': ['waiting_import']
    };
    
    return transitions[this.state] || [];
  }

  // 开始新项目
  startNewProject() {
    try {
      clearWorkspace();
      this.project = initializeProject();
      this.selectedFeature = null;
      this.selectedFeatures = []; // 重置多个特征选择
      this.setState('waiting_import');
      console.log('新项目已初始化');
      return { success: true };
    } catch (error) {
      console.error('初始化新项目失败:', error);
      this.setState('error');
      return { success: false, error: error.message };
    }
  }

    // 处理图纸导入
  async handleImport(filePath) {
    try {
      // 输入验证
      if (!filePath || typeof filePath !== 'string') {
        throw new Error('文件路径无效');
      }
      
      this.project = await handleDrawingImport(filePath);
      this.setState('drawing_loaded');
      
      // 等待PDF解析流程完成
      await this.processDrawing();
      
      return { success: true, project: this.project };
    } catch (error) {
      console.error('图纸导入失败:', error);
      this.setState('error');
      return { success: false, error: error.message };
    }
  }

  // 处理图纸解析
  async processDrawing() {
    try {
      if (!this.project || !this.project.filePath) {
        throw new Error('项目或项目文件路径无效');
      }
      
      console.log('开始解析图纸...');
      this.setState('processing');
      
      const parsingResult = await pdfParsingProcess(this.project.filePath);
      
      // 更新项目数据
      this.project.drawingInfo = parsingResult.drawingInfo;
      this.project.geometryElements = parsingResult.geometryElements;
      this.project.dimensions = parsingResult.dimensions;
      this.project.tolerances = parsingResult.tolerances || []; // 形位公差
      this.project.surfaceFinishes = parsingResult.surfaceFinishes || []; // 表面光洁度
      this.project.updatedAt = new Date();
      
      this.setState('ready');
      console.log('图纸解析完成');
      return { success: true, parsingResult };
    } catch (error) {
      console.error('图纸解析失败:', error);
      this.setState('error');
      return { success: false, error: error.message };
    }
  }

  // 用户选择特征
  handleFeatureSelection(x, y) {
    try {
      // 输入验证
      if (typeof x !== 'number' || typeof y !== 'number') {
        throw new Error('坐标参数必须是数字');
      }
      
      // 现在允许在 'ready' 和 'feature_selected' 状态下选择特征
      if (this.state !== 'ready' && this.state !== 'feature_selected') {
        throw new Error(`当前状态 ${this.state} 不允许选择特征，需要 'ready' 或 'feature_selected' 状态`);
      }

      if (!this.project) {
        throw new Error('项目未初始化');
      }

      const selection = selectFeature(this.project, x, y);
      if (selection && selection.element) {
        // 如果找到了确切的元素，添加到选中的特征列表中
        this.selectedFeature = selection; // 保持向后兼容
        // 检查是否已经选择过这个元素，避免重复添加
        const existingIndex = this.selectedFeatures.findIndex(f => f.element && f.element.id === selection.element.id);
        if (existingIndex === -1) {
          this.selectedFeatures.push(selection);
        } else {
          // 如果已存在，则更新该元素
          this.selectedFeatures[existingIndex] = selection;
        }
        // 保持在 feature_selected 状态，允许选择多个特征
        this.setState('feature_selected');
        return {
          ...selection,
          selectedFeaturesCount: this.selectedFeatures.length // 返回当前选中的特征总数
        };
      } else {
        // 如果没有找到确切的元素，但有目标坐标，也添加到选中的特征列表中
        // 创建一个虚拟选择对象并更新状态
        const virtualSelection = {
          element: null,
          coordinates: { x, y },
          timestamp: new Date(),
          message: '未找到匹配的几何元素，但已记录目标坐标',
          success: true
        };
        this.selectedFeature = virtualSelection; // 保持向后兼容
        this.selectedFeatures.push(virtualSelection); // 添加到多选列表
        // 保持在 feature_selected 状态，允许选择多个特征
        this.setState('feature_selected');
        return {
          ...virtualSelection,
          selectedFeaturesCount: this.selectedFeatures.length // 返回当前选中的特征总数
        };
      }
    } catch (error) {
      console.error('选择特征时出错:', error);
      return { success: false, error: error.message };
    }
  }

  // 启动特征定义（为当前选中的单个特征创建定义）
  startFeatureDefinition() {
    try {
      if (this.state !== 'feature_selected') {
        throw new Error(`当前状态 ${this.state} 不允许启动特征定义，需要 'feature_selected' 状态`);
      }
      
      if (!this.selectedFeature) {
        throw new Error('没有选中的特征');
      }

      if (!this.project) {
        throw new Error('项目未初始化');
      }

      // 如果没有找到确切的元素，但有目标坐标，创建一个虚拟元素
      let elementToUse = this.selectedFeature.element;
      if (!elementToUse) {
        // 创建虚拟圆元素用于指定坐标处的孔
        elementToUse = {
          id: `virtual_circle_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
          type: 'circle',
          center: this.selectedFeature.coordinates,
          radius: 2.75, // 默认半径对应5.5mm直径
          text: `Target hole at X${this.selectedFeature.coordinates.x}, Y${this.selectedFeature.coordinates.y}`,
          isVirtual: true // 标记为虚拟元素
        };
        
        // 添加到项目的几何元素中
        if (!Array.isArray(this.project.geometryElements)) {
          this.project.geometryElements = [];
        }
        this.project.geometryElements.push(elementToUse);
      }
      
      const feature = startFeatureDefinition(
        this.project, 
        elementToUse, 
        this.selectedFeature.dimensions || []
      );
      
      if (feature) {
        this.project.features.push(feature);
        this.project.updatedAt = new Date();
        this.setState('defining_feature');
        return feature;
      }
      
      return null;
    } catch (error) {
      console.error('启动特征定义时出错:', error);
      return { success: false, error: error.message };
    }
  }

    // 批量启动特征定义（为所有选中的特征创建定义）
  startFeatureDefinitionBatch() {
    try {
      if (this.state !== 'feature_selected') {
        throw new Error(`当前状态 ${this.state} 不允许启动特征定义，需要 'feature_selected' 状态`);
      }

      if (this.selectedFeatures.length === 0) {
        throw new Error('没有选中的特征');
      }

      if (!this.project) {
        throw new Error('项目未初始化');
      }

      const createdFeatures = [];

      for (const selectedFeature of this.selectedFeatures) {
        let elementToUse = selectedFeature.element;
        if (!elementToUse) {
          // 创建虚拟圆元素用于指定坐标处的孔
          elementToUse = {
            id: `virtual_circle_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
            type: 'circle',
            center: selectedFeature.coordinates,
            radius: 2.75, // 默认半径对应5.5mm直径
            text: `Target hole at X${selectedFeature.coordinates.x}, Y${selectedFeature.coordinates.y}`,
            isVirtual: true // 标记为虚拟元素
          };
          
          // 添加到项目的几何元素中
          if (!Array.isArray(this.project.geometryElements)) {
            this.project.geometryElements = [];
          }
          this.project.geometryElements.push(elementToUse);
        }

        const feature = startFeatureDefinition(
          this.project, 
          elementToUse, 
          selectedFeature.dimensions || []
        );

        if (feature) {
          this.project.features.push(feature);
          createdFeatures.push(feature);
        }
      }

      if (createdFeatures.length > 0) {
        this.project.updatedAt = new Date();
        this.setState('defining_feature');
        return createdFeatures;
      }

      return [];
    } catch (error) {
      console.error('批量启动特征定义时出错:', error);
      return { success: false, error: error.message };
    }
  }

  // 清空已选择的特征
  clearSelectedFeatures() {
    this.selectedFeature = null;
    this.selectedFeatures = [];
    // 如果当前状态是 feature_selected，则回到 ready 状态
    if (this.state === 'feature_selected') {
      this.setState('ready');
    }
  }

  // 从已选择的特征中移除指定的特征
  removeSelectedFeature(featureIndex) {
    if (featureIndex >= 0 && featureIndex < this.selectedFeatures.length) {
      this.selectedFeatures.splice(featureIndex, 1);
      // 如果移除了所有特征，更新状态
      if (this.selectedFeatures.length === 0) {
        this.selectedFeature = null;
        if (this.state === 'feature_selected') {
          this.setState('ready');
        }
      } else {
        // 否则，更新当前选中的特征为列表中的最后一个
        this.selectedFeature = this.selectedFeatures[this.selectedFeatures.length - 1];
      }
    }
  }

  // 选择特征类型
  selectFeatureType(featureId, featureType) {
    try {
      // 输入验证
      if (!featureId || typeof featureId !== 'string') {
        throw new Error('特征ID无效');
      }
      
      if (!featureType || typeof featureType !== 'string') {
        throw new Error('特征类型无效');
      }

      if (!this.project || !Array.isArray(this.project.features)) {
        throw new Error('项目或项目特征列表无效');
      }
      
      const feature = this.project.features.find(f => f.id === featureId);
      if (feature) {
        selectFeatureType(feature, featureType);
        this.project.updatedAt = new Date();
        return feature;
      }
      
      throw new Error(`未找到ID为 ${featureId} 的特征`);
    } catch (error) {
      console.error('选择特征类型时出错:', error);
      return { success: false, error: error.message };
    }
  }

  // 关联宏变量
  associateMacroVariable(featureId, dimensionId, variableName) {
    try {
      // 输入验证
      if (!featureId || typeof featureId !== 'string') {
        throw new Error('特征ID无效');
      }
      
      if (!dimensionId || typeof dimensionId !== 'string') {
        throw new Error('尺寸ID无效');
      }
      
      if (!variableName || typeof variableName !== 'string') {
        throw new Error('变量名无效');
      }

      if (!this.project || !Array.isArray(this.project.features)) {
        throw new Error('项目或项目特征列表无效');
      }
      
      const feature = this.project.features.find(f => f.id === featureId);
      if (feature) {
        associateMacroVariable(feature, dimensionId, variableName);
        this.project.updatedAt = new Date();
        return feature;
      }
      
      throw new Error(`未找到ID为 ${featureId} 的特征`);
    } catch (error) {
      console.error('关联宏变量时出错:', error);
      return { success: false, error: error.message };
    }
  }

  // 生成G代码
  generateGCode() {
    try {
      if (this.state !== 'ready' && this.state !== 'defining_feature') {
        throw new Error(`当前状态 ${this.state} 不允许生成G代码`);
      }
      
      if (!this.project) {
        throw new Error('项目未初始化');
      }
      
      this.project.gCodeBlocks = triggerGCodeGeneration(this.project);
      
      // 验证生成的G代码
      const { validateGCodeBlocks, validateGCodeSyntax, validateGCodeSafety, detectCollisions } = require('./modules/validation');
      const gCodeValidation = validateGCodeBlocks(this.project.gCodeBlocks);
      if (gCodeValidation.errors.length > 0) {
        console.error('G代码验证失败:', gCodeValidation.errors);
        this.setState('error');
        return { success: false, error: `G代码验证失败: ${gCodeValidation.errors.join('; ')}` };
      }
      
      // 对每块G代码进行语法验证和安全验证
      let hasCollisionRisk = false;
      for (const block of this.project.gCodeBlocks) {
        if (Array.isArray(block.code)) {
          const syntaxValidation = validateGCodeSyntax(block.code);
          if (syntaxValidation.errors.length > 0) {
            console.error(`G代码块 ${block.id} 语法验证失败:`, syntaxValidation.errors);
          }
          
          const safetyValidation = validateGCodeSafety(block.code);
          if (safetyValidation.errors.length > 0) {
            console.error(`G代码块 ${block.id} 安全验证失败:`, safetyValidation.errors);
          }
          
          // 进行碰撞检测
          const collisionDetection = detectCollisions(block.code);
          if (collisionDetection.hasCollisions) {
            hasCollisionRisk = true;
            console.error(`G代码块 ${block.id} 碰撞检测失败:`, collisionDetection.collisions);
            // 添加碰撞风险信息到项目
            if (!this.project.collisionWarnings) this.project.collisionWarnings = [];
            this.project.collisionWarnings.push({
              blockId: block.id,
              collisions: collisionDetection.collisions,
              timestamp: new Date()
            });
          }
        }
      }
      
      this.project.updatedAt = new Date();
      this.setState('code_generated');
      console.log('G代码生成和验证完成');
      
      // 如果有碰撞风险，可以设置特殊状态或添加警告
      if (hasCollisionRisk) {
        console.warn('生成的G代码存在碰撞风险，请仔细检查后再运行');
      }
      
      return this.project.gCodeBlocks;
    } catch (error) {
      console.error('生成G代码时出错:', error);
      this.setState('error');
      return { success: false, error: error.message };
    }
  }

  // 启动模拟
  runSimulation() {
    try {
      if (this.state !== 'code_generated') {
        throw new Error(`当前状态 ${this.state} 不允许启动模拟，需要 'code_generated' 状态`);
      }
      
      if (!this.project || !Array.isArray(this.project.gCodeBlocks)) {
        throw new Error('项目或G代码块列表无效');
      }
      
      const simulationResults = startSimulation(this.project.gCodeBlocks);
      this.setState('simulation_running');
      return simulationResults;
    } catch (error) {
      console.error('运行模拟时出错:', error);
      this.setState('error');
      return { success: false, error: error.message };
    }
  }

  // 变量驱动模拟
  runVariableDrivenSimulation(variableValues) {
    try {
      if (this.state !== 'code_generated' && this.state !== 'simulation_running') {
        throw new Error(`当前状态 ${this.state} 不允许运行变量驱动模拟`);
      }
      
      if (!this.project || !Array.isArray(this.project.gCodeBlocks)) {
        throw new Error('项目或G代码块列表无效');
      }
      
      const simulationResults = variableDrivenSimulation(this.project.gCodeBlocks, variableValues);
      console.log('变量驱动模拟完成');
      return simulationResults;
    } catch (error) {
      console.error('运行变量驱动模拟时出错:', error);
      return { success: false, error: error.message };
    }
  }

  // 导出代码
  exportCode(outputPath) {
    try {
      if (this.state !== 'code_generated') {
        throw new Error(`当前状态 ${this.state} 不允许导出代码，需要 'code_generated' 状态`);
      }
      
      if (!this.project || !Array.isArray(this.project.gCodeBlocks)) {
        throw new Error('项目或G代码块列表无效');
      }
      
      const gCode = exportCode(this.project.gCodeBlocks, outputPath);
      this.setState('code_exported');
      console.log('代码导出完成');
      return gCode;
    } catch (error) {
      console.error('导出代码时出错:', error);
      this.setState('error');
      return { success: false, error: error.message };
    }
  }
  
    // 获取当前状态信息
  getStateInfo() {
    return {
      currentState: this.state,
      allowedTransitions: this.getAllowedTransitions(),
      stateHistory: [...this.stateHistory],
      projectExists: !!this.project,
      featureSelected: !!this.selectedFeature,
      selectedFeatureCount: this.selectedFeatures.length, // 返回选中特征的数量
      selectedFeatures: this.selectedFeatures // 返回选中的特征列表
    };
  }
}

// 创建状态管理器实例
const cncStateManager = new CNCStateManager();

// 创建Express应用
const app = express();
const PORT = process.env.PORT || 3000;

// 安全中间件
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15分钟
  max: 100, // 限制每个IP 15分钟内最多100个请求
  message: '请求过于频繁，请稍后再试'
});

app.use(limiter);
app.use(express.json({ 
  limit: '10mb' // 限制请求体大小
}));
app.use(express.static('public'));

// 输入验证中间件
function validateInput(req, res, next) {
  // 验证所有输入参数
  if (req.body) {
    // 检查是否包含潜在的恶意代码
    const bodyStr = JSON.stringify(req.body);
    const dangerousPatterns = [
      /<script/i,
      /javascript:/i,
      /vbscript:/i,
      /on\w+\s*=/i,
      /<iframe/i,
      /<object/i,
      /<embed/i
    ];
    
    for (const pattern of dangerousPatterns) {
      if (pattern.test(bodyStr)) {
        return res.status(400).json({ 
          success: false, 
          error: '请求包含潜在的恶意内容' 
        });
      }
    }
  }
  
  next();
}

app.use(validateInput);

// API路由
app.post('/api/project/new', (req, res) => {
  try {
    const result = cncStateManager.startNewProject();
    res.json({ ...result, state: cncStateManager.state });
  } catch (error) {
    console.error('创建新项目时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/project/import', async (req, res) => {
  try {
    const { filePath } = req.body;
    if (!filePath) {
      return res.status(400).json({ success: false, error: '缺少文件路径' });
    }
    
    const result = await cncStateManager.handleImport(filePath);
    res.json({ ...result, state: cncStateManager.state });
  } catch (error) {
    console.error('导入项目时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/feature/select', (req, res) => {
  try {
    const { x, y } = req.body;
    if (typeof x !== 'number' || typeof y !== 'number') {
      return res.status(400).json({ success: false, error: '坐标必须是数字' });
    }
    
    const selection = cncStateManager.handleFeatureSelection(x, y);
    if (selection && selection.hasOwnProperty('success') && selection.success === false) {
      return res.status(400).json(selection);
    }
    // 总是返回成功，但包含selection信息，让客户端决定如何处理
    // 如果找到了元素，success为true；如果没有找到元素但记录了坐标，也视为部分成功
    const hasValidElement = selection && selection.element;
    res.json({ success: true, selection, hasElement: hasValidElement });
  } catch (error) {
    console.error('选择特征时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/feature/define', (req, res) => {
  try {
    const { batch } = req.body; // 检查是否请求批量处理
    let result;
    if (batch) {
      result = cncStateManager.startFeatureDefinitionBatch();
      if (result && result.success === false) {
        return res.status(400).json(result);
      }
      res.json({ success: Array.isArray(result), features: result });
    } else {
      result = cncStateManager.startFeatureDefinition();
      if (result && result.success === false) {
        return res.status(400).json(result);
      }
      res.json({ success: !!result, feature: result });
    }
  } catch (error) {
    console.error('定义特征时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/feature/type', (req, res) => {
  try {
    const { featureId, featureType } = req.body;
    if (!featureId || !featureType) {
      return res.status(400).json({ success: false, error: '缺少必要参数' });
    }
    
    const result = cncStateManager.selectFeatureType(featureId, featureType);
    if (result && result.success === false) {
      return res.status(400).json(result);
    }
    res.json({ success: !!result, feature: result });
  } catch (error) {
    console.error('选择特征类型时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/feature/variable', (req, res) => {
  try {
    const { featureId, dimensionId, variableName } = req.body;
    if (!featureId || !dimensionId || !variableName) {
      return res.status(400).json({ success: false, error: '缺少必要参数' });
    }
    
    const result = cncStateManager.associateMacroVariable(featureId, dimensionId, variableName);
    if (result && result.success === false) {
      return res.status(400).json(result);
    }
    res.json({ success: !!result, feature: result });
  } catch (error) {
    console.error('关联宏变量时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/gcode/generate', (req, res) => {
  try {
    const result = cncStateManager.generateGCode();
    if (result && result.success === false) {
      return res.status(400).json(result);
    }
    res.json({ success: !!result, gCodeBlocks: result });
  } catch (error) {
    console.error('生成G代码时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/simulation/start', (req, res) => {
  try {
    const results = cncStateManager.runSimulation();
    if (results && results.success === false) {
      return res.status(400).json(results);
    }
    res.json({ success: !!results, results });
  } catch (error) {
    console.error('运行模拟时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/simulation/variable', (req, res) => {
  try {
    const { variableValues } = req.body;
    if (!variableValues) {
      return res.status(400).json({ success: false, error: '缺少变量值' });
    }
    
    const results = cncStateManager.runVariableDrivenSimulation(variableValues);
    if (results && results.success === false) {
      return res.status(400).json(results);
    }
    res.json({ success: !!results, results });
  } catch (error) {
    console.error('运行变量驱动模拟时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.post('/api/gcode/export', (req, res) => {
  try {
    const { outputPath } = req.body;
    const gCode = cncStateManager.exportCode(outputPath);
    if (gCode && gCode.success === false) {
      return res.status(400).json(gCode);
    }
    res.json({ success: !!gCode, gCode });
  } catch (error) {
    console.error('导出代码时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

app.get('/api/state', (req, res) => {
  try {
    const stateInfo = cncStateManager.getStateInfo();
    res.json(stateInfo);
  } catch (error) {
    console.error('获取状态时出错:', error);
    res.status(500).json({ success: false, error: error.message });
  }
});

// 错误处理中间件
app.use((error, req, res, next) => {
  console.error('服务器错误:', error);
  res.status(500).json({ 
    success: false, 
    error: '服务器内部错误' 
  });
});

// 404中间件
app.use('*', (req, res) => {
  res.status(404).json({ 
    success: false, 
    error: 'API端点不存在' 
  });
});

// 只有在直接运行此文件时才启动服务器
if (require.main === module) {
  // 启动服务器
  let currentPort = PORT;
  let maxRetries = 10; // 尝试最多10个端口
  let attempt = 0;
  
  function startServer(port) {
    attempt++;
    console.log(`尝试启动服务器在端口 ${port} (尝试 ${attempt}/${maxRetries + 1})`);
    const server = app.listen(port, () => {
      console.log(`CNCagent 服务器运行在端口 ${port}`);
      console.log('状态管理器已初始化，当前状态:', cncStateManager.state);
    });

    // 处理端口被占用的情况
    server.on('error', (err) => {
      if (err.code === 'EADDRINUSE') {
        if (attempt < maxRetries) {
          const newPort = port + 1;
          console.log(`端口 ${port} 已被占用，尝试使用端口 ${newPort}`);
          setTimeout(() => {
            startServer(newPort);
          }, 1000);
        } else {
          console.error(`已尝试 ${maxRetries} 个端口，都被占用，无法启动服务器:`);
          console.error(err);
        }
      } else {
        console.error('服务器启动错误:', err);
      }
    });
  }

  startServer(currentPort);
}

module.exports = { CNCStateManager };