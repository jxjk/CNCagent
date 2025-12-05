// 简化版服务器启动脚本，用于测试部署
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// 简单的健康检查路由
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// 基本的API路由
app.get('/api/test', (req, res) => {
  res.json({ message: 'CNCagent API is running', status: 'ready' });
});

// 项目创建API
app.post('/api/project/new', (req, res) => {
  try {
    // 模拟项目创建
    const project = {
      id: 'test-project-' + Date.now(),
      name: 'Test Project',
      status: 'created',
      timestamp: new Date().toISOString()
    };
    res.json({ success: true, project });
  } catch (error) {
    res.status(500).json({ success: false, error: error.message });
  }
});

// 启动服务器
app.listen(PORT, '127.0.0.1', () => {
  console.log(`测试服务器运行在端口 ${PORT}`);
  console.log(`健康检查地址: http://127.0.0.1:${PORT}/health`);
  console.log(`API测试地址: http://127.0.0.1:${PORT}/api/test`);
});