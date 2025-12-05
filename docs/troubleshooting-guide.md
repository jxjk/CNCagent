# CNCagent 故障排除指南

## 目录
1. [常见问题](#常见问题)
2. [错误代码详解](#错误代码详解)
3. [性能问题](#性能问题)
4. [API问题](#api问题)
5. [安全问题](#安全问题)
6. [部署问题](#部署问题)
7. [故障诊断工具](#故障诊断工具)

## 常见问题

### 1. 应用无法启动

**症状**: 
- 控制台显示错误信息
- 无法访问 `http://localhost:3000`

**可能原因及解决方案**:

**Node.js版本不兼容**
- 检查Node.js版本: `node --version`
- 确保版本为v16.0或更高
- 如需更新，请下载并安装最新版本的Node.js

**端口被占用**
- 错误信息: `Error: listen EADDRINUSE: address already in use :::3000`
- 解决方案:
  ```bash
  # 检查端口占用情况
  # Windows
  netstat -ano | findstr :3000
  # macOS/Linux
  lsof -i :3000
  
  # 更改端口启动
  PORT=3001 npm start
  ```

**依赖安装不完整**
- 错误信息: `Error: Cannot find module`
- 解决方案:
  ```bash
  # 清理并重新安装依赖
  rm -rf node_modules package-lock.json
  npm install
  ```

### 2. 图纸导入失败

**症状**:
- API返回错误信息
- 解析状态停留在 `processing`

**可能原因及解决方案**:

**文件格式不支持**
- 确保文件格式为: PDF, DXF, SVG, DWG, STEP, IGES
- 检查文件扩展名是否正确

**文件路径问题**
- 确保文件路径为绝对路径
- 检查文件是否存在且有读取权限
- Windows路径使用双反斜杠或正斜杠:
  ```json
  {
    "filePath": "C:\\path\\to\\drawing.pdf"
  }
  ```

**文件损坏**
- 尝试用相应软件打开文件确认文件完整性
- 重新保存文件

### 3. 特征选择失败

**症状**:
- 选择坐标后返回 `success: false`
- 无法进入 `feature_selected` 状态

**可能原因及解决方案**:

**坐标不准确**
- 确保坐标在几何元素附近（容差为5像素）
- 检查图纸坐标系统是否正确

**几何元素无法识别**
- 确保元素类型被支持（line, circle, rectangle等）
- 检查元素数据格式是否正确

### 4. G代码生成问题

**症状**:
- 生成的G代码不完整
- G代码无法在数控机床上运行

**可能原因及解决方案**:

**特征定义不完整**
- 确保所有特征都有正确的类型
- 检查特征参数是否合理

**参数设置不当**
- 验证进给率、安全高度等参数
- 检查刀具参数是否符合机床要求

## 错误代码详解

### HTTP错误代码

| 代码 | 含义 | 解决方案 |
|------|------|----------|
| 400 | 请求参数错误 | 检查请求体格式和参数值 |
| 404 | API端点不存在 | 检查URL路径是否正确 |
| 429 | 请求频率超限 | 等待15分钟重置或调整请求频率 |
| 500 | 服务器内部错误 | 查看控制台日志，检查系统资源 |

### 应用错误代码

| 错误类型 | 说明 | 解决方案 |
|----------|------|----------|
| Invalid input | 输入参数无效 | 验证参数类型和格式 |
| Missing required parameter | 缺少必要参数 | 检查请求体是否包含所有必需字段 |
| File does not exist | 文件不存在 | 验证文件路径和权限 |
| Unsupported file format | 不支持的文件格式 | 使用支持的格式 |
| Invalid state transition | 无效的状态转换 | 检查当前状态是否允许该操作 |
| Feature not found | 未找到特征 | 验证特征ID和坐标 |

### 状态转换错误

| 当前状态 | 尝试转换 | 问题 | 解决方案 |
|----------|----------|------|----------|
| waiting_import | feature_selected | 未导入图纸 | 先导入图纸文件 |
| drawing_loaded | feature_selected | 未完成解析 | 等待解析完成 |
| ready | code_generated | 未定义特征 | 先选择和定义特征 |
| code_generated | simulation_running | G代码为空 | 重新生成G代码 |

## 性能问题

### 1. 响应缓慢

**可能原因**:
- 处理大型图纸文件
- 系统资源不足
- 网络延迟

**解决方案**:
```bash
# 检查系统资源使用情况
# Windows
tasklist /fi "imagename eq node.exe"
# macOS/Linux
top -p $(pgrep -f "node.*index.js")
```

- 增加Node.js内存限制: `node --max-old-space-size=4096 src/index.js`
- 分批处理大型文件
- 优化系统资源分配

### 2. 内存使用过高

**症状**:
- 应用占用大量内存
- 系统变慢

**解决方案**:
- 定期清理workspace目录
- 监控内存使用情况
- 重启应用释放内存

### 3. 文件处理缓慢

**优化建议**:
- 预先压缩大型图纸文件
- 使用SSD存储
- 优化网络连接

## API问题

### 1. 请求限制问题

**问题**: API请求被拒绝，返回 "请求过于频繁，请稍后再试"

**解决方案**:
- 检查请求频率是否超过100次/15分钟
- 实现请求队列机制
- 调整express-rate-limit配置

### 2. CORS问题

**问题**: 浏览器中跨域请求失败

**解决方案**:
- 在服务器端配置CORS中间件
- 或确保前端和后端在同一域下运行

### 3. 请求体大小限制

**问题**: 上传大文件时返回413错误

**解决方案**:
- 当前限制为10MB，如需调整可在src/index.js中修改:
  ```javascript
  app.use(express.json({ limit: '20mb' })); // 调整限制
  ```

## 安全问题

### 1. 输入验证问题

**问题**: 恶意输入导致的安全漏洞

**防护措施**:
- 所有输入都会经过验证
- XSS防护已启用
- 文件类型验证
- 路径遍历防护

### 2. 文件上传安全

**防护措施**:
- 仅支持特定CAD格式
- 文件路径验证
- 文件内容检查

## 部署问题

### 1. 生产环境部署

**常见问题及解决方案**:

**权限问题**
- 确保运行用户有足够权限
- 检查工作目录权限

**端口访问**
- 确保防火墙允许相应端口
- 检查安全组设置（云环境）

**进程管理**
- 使用PM2等进程管理器
- 配置开机自启

### 2. Docker部署

如果使用Docker部署，请确保:

**Dockerfile示例**:
```dockerfile
FROM node:16-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
```

**常见Docker问题**:
- 确保卷挂载正确
- 检查网络配置
- 验证端口映射

## 故障诊断工具

### 1. 日志分析

**应用日志**:
- 查看控制台输出
- 检查状态转换日志
- 记录错误信息

**系统日志**:
- Windows事件查看器
- Linux系统日志 (`/var/log/`)

### 2. 状态检查脚本

创建一个简单的诊断脚本 `diagnose.js`:

```javascript
const axios = require('axios');

async function diagnose() {
  console.log('开始诊断 CNCagent 服务...');
  
  try {
    // 检查服务是否运行
    const response = await axios.get('http://localhost:3000/api/state');
    console.log('✓ 服务运行正常');
    console.log('当前状态:', response.data.currentState);
    console.log('项目存在:', response.data.projectExists);
    console.log('特征选择:', response.data.featureSelected);
    
    // 检查API可用性
    const newProject = await axios.post('http://localhost:3000/api/project/new');
    console.log('✓ API接口可用');
    console.log('新项目创建状态:', newProject.data.success);
    
  } catch (error) {
    console.log('✗ 服务诊断失败:', error.message);
    if (error.response) {
      console.log('状态码:', error.response.status);
      console.log('响应:', error.response.data);
    }
  }
}

diagnose();
```

### 3. 系统资源监控

**内存和CPU监控**:
```bash
# 检查Node进程资源使用
ps aux | grep node

# 检查端口占用
netstat -tulpn | grep :3000

# 检查磁盘空间
df -h
```

### 4. 网络连接测试

```bash
# 测试本地连接
curl -v http://localhost:3000/api/state

# 测试API响应
curl -X POST http://localhost:3000/api/project/new \
  -H "Content-Type: application/json" \
  -d "{}"
```

## 预防措施

### 1. 定期维护
- 定期更新依赖包
- 清理工作目录
- 备份重要数据
- 监控系统性能

### 2. 监控设置
- 设置日志轮转
- 监控API响应时间
- 跟踪错误率
- 监控资源使用

### 3. 安全更新
- 定期检查安全漏洞
- 更新到最新版本
- 审查访问日志
- 验证输入数据

## 联系支持

如果遇到无法解决的问题:

1. 检查完整的错误日志
2. 确认版本信息
3. 提供复现步骤
4. 联系系统管理员或开发团队