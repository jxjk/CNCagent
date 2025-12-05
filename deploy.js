// CNCagent 部署脚本 - 使用指定端口
const { CNCStateManager } = require('./src/index');

// 创建状态管理器实例
const cncStateManager = new CNCStateManager();

// 启动服务器
const express = require('express');
const rateLimit = require('express-rate-limit');
const app = express();
const PORT = 8081; // 使用一个明确未被占用的端口

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

// API路由（从index.js复制）
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
    res.json({ success: true, selection, hasElement: !!(selection && selection.element) });
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

// 健康检查端点
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'CNCagent',
    timestamp: new Date().toISOString(),
    state: cncStateManager.state
  });
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

// 启动服务器
const server = app.listen(PORT, '127.0.0.1', () => {
  console.log(`=======================================================`);
  console.log(`CNCagent 部署成功!`);
  console.log(`服务器运行在: http://127.0.0.1:${PORT}`);
  console.log(`健康检查: http://127.0.0.1:${PORT}/health`);
  console.log(`API文档: http://127.0.0.1:${PORT}/api/state`);
  console.log(`当前状态: ${cncStateManager.state}`);
  console.log(`=======================================================`);
});

// 处理服务器错误
server.on('error', (err) => {
  console.error('服务器启动错误:', err);
  if (err.code === 'EADDRINUSE') {
    console.error(`端口 ${PORT} 已被占用，请尝试其他端口`);
  }
});