# CNCagent 模块详细说明

## 1. 项目初始化模块 (projectInitialization.js)

### 概述
项目初始化模块负责创建和管理项目实例，处理新项目的创建、工作区清理以及图纸导入功能。

### 核心组件

#### Project 类
```javascript
class Project {
  constructor() {
    this.id = generateId();                    // 项目唯一标识符
    this.name = 'New Project';                 // 项目名称
    this.filePath = null;                      // 源文件路径
    this.drawingInfo = null;                   // 图纸信息
    this.geometryElements = [];                // 几何元素数组
    this.dimensions = [];                      // 尺寸数组
    this.features = [];                        // 特征数组
    this.gCodeBlocks = [];                     // G代码块数组
    this.createdAt = new Date();               // 创建时间
    this.updatedAt = new Date();               // 更新时间
    this.workspacePath = null;                 // 工作区路径
  }
}
```

#### 核心函数

**initializeProject(projectName)**
- **功能**: 初始化新项目
- **参数**: projectName (可选，默认为 'New Project')
- **返回**: Project 实例
- **说明**: 创建新的Project实例并创建对应的工作区目录

**clearWorkspace()**
- **功能**: 清理所有工作区文件
- **参数**: 无
- **返回**: 无
- **说明**: 删除workspace目录下的所有项目文件夹

**handleDrawingImport(filePath)**
- **功能**: 处理图纸文件导入
- **参数**: filePath (文件路径)
- **返回**: Project 实例
- **说明**: 验证文件格式并创建项目实例

### 2. 图纸解析模块 (subprocesses/pdfParsingProcess.js)

### 概述
图纸解析模块负责解析各种CAD格式文件，提取几何元素和尺寸信息。

#### 核心函数

**pdfParsingProcess(filePath)**
- **功能**: 解析PDF等格式文件
- **参数**: filePath (文件路径)
- **返回**: 解析结果对象
- **说明**: 
  - 验证文件存在性
  - 使用pdfjs-dist库进行实际PDF解析
  - 从PDF文本层提取几何信息（坐标、尺寸、半径等）
  - 使用正则表达式模式匹配识别几何元素
  - 返回包含drawingInfo, geometryElements, dimensions的对象
  - 对于图像型CAD图纸，提供回退机制

### 3. 特征定义模块 (featureDefinition.js)

### 概述
特征定义模块负责识别和定义CAD图纸中的几何特征，支持特征选择、类型定义和宏变量关联。

#### 核心函数

**selectFeature(project, x, y)**
- **功能**: 根据坐标选择几何特征
- **参数**: 
  - project: 项目对象
  - x, y: 坐标位置
- **返回**: 选择的特征对象或null
- **说明**: 
  - 使用容差机制选择附近的几何元素
  - 支持线、圆、矩形等多种几何类型
  - 返回包含元素、坐标和时间戳的对象

**startFeatureDefinition(project, element, dimensions)**
- **功能**: 开始定义选中的特征
- **参数**: 
  - project: 项目对象
  - element: 几何元素
  - dimensions: 尺寸信息
- **返回**: 特征定义对象
- **说明**: 
  - 创建特征对象
  - 设置基本属性
  - 初始化参数

**selectFeatureType(feature, featureType)**
- **功能**: 为特征指定类型
- **参数**: 
  - feature: 特征对象
  - featureType: 特征类型
- **返回**: 无
- **说明**: 
  - 验证特征类型有效性
  - 设置默认参数
  - 支持的类型：hole, pocket, boss, slot, chamfer, fillet, extrude, cut

**associateMacroVariable(feature, dimensionId, variableName)**
- **功能**: 将宏变量关联到特征尺寸
- **参数**: 
  - feature: 特征对象
  - dimensionId: 尺寸ID
  - variableName: 变量名
- **返回**: 无
- **说明**: 
  - 验证变量名格式
  - 建立尺寸到变量的映射

### 4. G代码生成模块 (gCodeGeneration.js)

### 概述
G代码生成模块根据定义的特征生成相应的G代码，包含程序控制代码和特征特定的加工指令。

#### 核心函数

**triggerGCodeGeneration(project)**
- **功能**: 触发G代码生成
- **参数**: project (项目对象)
- **返回**: G代码块数组
- **说明**: 
  - 为每个特征生成G代码
  - 添加程序开始和结束代码
  - 返回完整的G代码块数组

**generateFeatureGCode(feature)**
- **功能**: 为特定特征生成G代码
- **参数**: feature (特征对象)
- **返回**: G代码块对象
- **说明**: 根据特征类型调用相应的生成函数

**generateHoleGCode(feature)**
- **功能**: 生成孔加工的G代码
- **参数**: feature (孔特征)
- **返回**: G代码行数组
- **说明**: 生成钻孔操作的G代码序列

**generatePocketGCode(feature)**
- **功能**: 生成口袋加工的G代码
- **参数**: feature (口袋特征)
- **返回**: G代码行数组
- **说明**: 生成铣削口袋的G代码序列

**generateSlotGCode(feature)**
- **功能**: 生成槽加工的G代码
- **参数**: feature (槽特征)
- **返回**: G代码行数组
- **说明**: 生成铣削槽的G代码序列

**generateChamferGCode(feature)**
- **功能**: 生成倒角加工的G代码
- **参数**: feature (倒角特征)
- **返回**: G代码行数组
- **说明**: 生成倒角操作的G代码序列

**generateFilletGCode(feature)**
- **功能**: 生成圆角加工的G代码
- **参数**: feature (圆角特征)
- **返回**: G代码行数组
- **说明**: 生成圆角操作的G代码序列

### 5. 模拟输出模块 (simulationOutput.js)

### 概述
模拟输出模块负责G代码的模拟执行、工具路径生成、问题检测和代码导出功能。

#### 核心函数

**startSimulation(gCodeBlocks)**
- **功能**: 启动G代码模拟执行
- **参数**: gCodeBlocks (G代码块数组)
- **返回**: 模拟结果对象
- **说明**: 
  - 模拟执行G代码序列
  - 生成工具路径
  - 检测潜在问题
  - 返回包含执行时间、警告和错误的详细结果

**generateToolPath(gCodeBlock)**
- **功能**: 为G代码块生成工具路径
- **参数**: gCodeBlock (G代码块)
- **返回**: 工具路径对象
- **说明**: 
  - 解析G代码中的坐标指令
  - 生成路径点序列
  - 计算路径长度和时间

**checkForIssues(gCodeBlock)**
- **功能**: 检查G代码中的潜在问题
- **参数**: gCodeBlock (G代码块)
- **返回**: 问题对象（包含警告和错误）
- **说明**: 
  - 检查过高的进给率
  - 检查过大的移动距离
  - 检查坐标系使用问题

**variableDrivenSimulation(gCodeBlocks, variableValues)**
- **功能**: 基于变量值的模拟执行
- **参数**: 
  - gCodeBlocks (G代码块数组)
  - variableValues (变量值对象)
- **返回**: 模拟结果对象
- **说明**: 
  - 替换G代码中的宏变量
  - 执行修改后的G代码模拟

**exportCode(gCodeBlocks, outputPath)**
- **功能**: 导出G代码到文件
- **参数**: 
  - gCodeBlocks (G代码块数组)
  - outputPath (输出路径，可选)
- **返回**: 导出结果对象
- **说明**: 
  - 生成完整的G代码字符串
  - 如果提供路径则写入文件
  - 返回文件信息

## 模块间交互关系

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  项目初始化     │───►│  图纸解析       │───►│  特征定义       │
│  (project      │    │  (pdfParsing   │    │  (feature      │
│   initialization│    │   process)     │    │   definition)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                       │
                              ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  G代码生成      │◄───│  状态管理器     │───►│  模拟输出       │
│  (gCode        │    │  (CNCState     │    │  (simulation   │
│   generation)   │    │   Manager)     │    │   output)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### 数据流向

1. **项目初始化** → **状态管理器**: 提供项目实例
2. **图纸解析** → **项目**: 填充几何元素和尺寸
3. **特征定义** → **项目**: 添加特征定义
4. **G代码生成** ← **项目**: 读取特征信息生成代码
5. **模拟输出** ← **G代码**: 执行模拟和导出

## 错误处理机制

每个模块都实现了输入验证和错误处理：

- 参数类型检查
- 无效值验证
- 异步操作错误捕获
- 状态转换合法性验证
- 文件操作异常处理

## 扩展性设计

- 模块间松耦合设计
- 函数式编程接口
- 可扩展的特征类型系统
- 插件式G代码生成器
- 统一的数据格式定义