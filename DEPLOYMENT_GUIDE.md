# CNCagent 部署指南

## 系统要求
- Node.js 16.x 或更高版本
- npm 包管理器
- Windows/Linux/macOS 操作系统

## 安装步骤

1. **克隆或下载源代码**
   ```bash
   git clone <repository-url>
   # 或者直接下载ZIP文件并解压
   ```

2. **安装依赖包**
   ```bash
   cd CNCagent
   npm install
   ```

3. **验证安装**
   ```bash
   npm test
   # 或运行特定测试
   node -e "const { CNCStateManager } = require('./src/index'); console.log('CNCagent loaded successfully');"
   ```

## 功能特性

### 1. PDF读取与解析能力
- 支持PDF格式的CAD图纸读取
- 高级OCR功能，可识别图像中的文字和几何元素
- 智能解析算法，提取几何信息

### 2. 图纸视图视角识别
- 自动识别图纸坐标系统
- 智能判断原点位置和方向
- 支持多种坐标系标准

### 3. 几何元素识别
- **孔识别**: 智能识别各类孔特征，包括定位坐标和尺寸
- **螺纹识别**: 识别内外螺纹、螺纹规格和深度
- **槽识别**: 矩形槽、键槽、T型槽等
- **边识别**: 直线边、弧形边等
- **面区域识别**: 矩形面、圆形面等

### 4. 尺寸标注识别
- 标注位置尺寸
- 特征尺寸提取
- 光洁度识别
- 形状位置公差识别

### 5. 加工工艺规划
- 自动规划加工顺序
- 优化刀具路径
- 支持多种加工工艺（钻孔、铣削、攻丝等）

### 6. 材料-刀具智能匹配
- 支持多种材料类型（钢、不锈钢、铝、铜、塑料、钛合金）
- 智能推荐刀具和加工参数
- 根据材料特性优化转速和进给

### 7. G代码生成与验证
- 生成标准G代码
- 语法验证
- 安全性验证
- 碰撞检测算法

### 8. 碰撞检测算法
- 工件边界检测
- 安全高度验证
- 路径碰撞检测

### 9. OCR功能
- 集成Tesseract.js进行光学字符识别
- 从图像中提取几何信息

### 10. 复杂CAD图纸解析
- 识别几何关系
- 处理同心圆、孔组
- 检测螺栓圆、矩形阵列

### 11. 加工仿真功能
- 工具路径模拟
- 加工时间估算
- 变量驱动模拟

## 运行应用

### 启动服务
```bash
npm start
```

### API端点
- `POST /api/project/new` - 创建新项目
- `POST /api/project/import` - 导入图纸文件
- `POST /api/feature/select` - 选择特征
- `POST /api/feature/define` - 定义特征
- `POST /api/gcode/generate` - 生成G代码
- `POST /api/simulation/start` - 启动仿真
- `POST /api/gcode/export` - 导出代码
- `GET /api/state` - 获取当前状态

### 使用示例
```javascript
const { CNCStateManager } = require('./src/index');
const stateManager = new CNCStateManager();

// 创建新项目
stateManager.startNewProject();

// 导入图纸 (需要实现PDF解析)
// stateManager.handleImport('path/to/drawing.pdf');

// 选择特征
// stateManager.handleFeatureSelection(x, y);

// 定义特征
// stateManager.startFeatureDefinition();

// 生成G代码
// stateManager.generateGCode();

// 运行仿真
// stateManager.runSimulation();

// 导出代码
// stateManager.exportCode('output.nc');
```

## 配置选项

### 端口配置
默认端口为3000，如果被占用会自动尝试+1端口直到找到可用端口。

### 安全配置
- 请求频率限制：15分钟内最多100个请求
- 输入验证：防止恶意代码注入
- 文件上传限制：10MB

## 维护和故障排除

### 常见问题
1. **端口被占用** - 服务会自动尝试下一个端口
2. **PDF解析失败** - 检查文件格式和权限
3. **依赖包错误** - 重新运行 `npm install`

### 日志记录
系统会在控制台输出详细的状态转换和错误信息。

## 许可证
MIT License

## 版本历史
- 1.0.0 - 初始版本，包含完整的CNC加工功能链