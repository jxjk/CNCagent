// 专用服务器启动脚本
const { CNCStateManager } = require('./src/index');

// 创建状态管理器实例
const cncStateManager = new CNCStateManager();

// 启动服务器
const express = require('express');
const rateLimit = require('express-rate-limit');
const app = express();
const PORT = 3001; // 使用备用端口

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

// 复制API路由（从index.js中复制）
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

// 启动服务器
let currentPort = PORT;
let maxRetries = 10; // 尝试最多10个端口
let attempt = 0;

function startServer(port) {
  attempt++;
  console.log(`尝试启动服务器在端口 ${port} (尝试 ${attempt}/${maxRetries + 1})`);
  const server = app.listen(port, () => {
    console.log(`CNCagent 服务器成功运行在端口 ${port}`);
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