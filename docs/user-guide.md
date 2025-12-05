# CNCagent 用户操作指南

## 目录
1. [快速开始](#快速开始)
2. [系统要求](#系统要求)
3. [安装与启动](#安装与启动)
4. [工作流程](#工作流程)
5. [功能详解](#功能详解)
6. [常见操作](#常见操作)
7. [最佳实践](#最佳实践)

## 快速开始

CNCagent是一个自动化CNC编程工具，可以将CAD图纸转换为G代码。以下是快速开始的步骤：

1. **启动应用**
   ```bash
   npm start
   ```
   应用将运行在 `http://localhost:3000`

2. **创建项目**
   ```bash
   curl -X POST http://localhost:3000/api/project/new
   ```

3. **导入图纸**
   ```bash
   curl -X POST http://localhost:3000/api/project/import \
     -H "Content-Type: application/json" \
     -d '{"filePath": "/path/to/your/drawing.pdf"}'
   ```

4. **选择并定义特征**
   ```bash
   curl -X POST http://localhost:3000/api/feature/select \
     -H "Content-Type: application/json" \
     -d '{"x": 100, "y": 200}'
   ```

5. **生成G代码**
   ```bash
   curl -X POST http://localhost:3000/api/gcode/generate
   ```

## 系统要求

### 硬件要求
- CPU: 双核 2.0 GHz 或更高
- 内存: 4 GB RAM（推荐 8 GB）
- 存储: 至少 500 MB 可用空间
- 图形: 支持 OpenGL 2.0+（用于模拟功能）

### 软件要求
- Node.js v16.0 或更高版本
- 操作系统: Windows 10+, macOS 10.14+, 或 Linux (Ubuntu 18.04+)

## 安装与启动

### 1. 克隆或下载项目
```bash
git clone <project-repository-url>
# 或直接下载项目压缩包
```

### 2. 安装依赖
```bash
cd CNCagent
npm install
```

### 3. 启动应用
```bash
# 生产模式
npm start

# 开发模式（带自动重载）
npm run dev
```

### 4. 验证安装
打开浏览器访问 `http://localhost:3000/api/state`，应返回当前状态信息。

## 工作流程

CNCagent的工作流程分为以下几个步骤：

```
[开始] → [创建项目] → [导入图纸] → [解析图纸] → [选择特征] → [定义特征] → [生成G代码] → [模拟验证] → [导出代码]
```

### 1. 创建项目
- 初始化新的工作区
- 准备项目相关的临时文件

### 2. 导入图纸
- 支持格式: PDF, DXF, SVG, DWG, STEP, IGES
- 自动解析几何元素和尺寸

### 3. 解析图纸
- 提取线条、圆形、矩形等几何元素
- 识别尺寸标注

### 4. 选择特征
- 通过坐标选择图纸上的几何元素
- 准备进行特征定义

### 5. 定义特征
- 指定特征类型（孔、口袋、槽等）
- 设置加工参数

### 6. 生成G代码
- 根据特征定义生成相应的G代码
- 优化刀具路径

### 7. 模拟验证
- 模拟G代码执行
- 检查潜在问题

### 8. 导出代码
- 生成标准G代码文件
- 适用于数控机床

## 功能详解

### 项目管理

#### 创建新项目
- **API端点**: `POST /api/project/new`
- **功能**: 初始化一个新的CNC编程项目
- **参数**: 
  - `projectName` (可选): 项目名称
- **说明**: 每个项目都有独立的工作空间，建议每个CAD图纸使用单独的项目

#### 导入图纸
- **API端点**: `POST /api/project/import`
- **功能**: 导入CAD图纸文件
- **参数**: 
  - `filePath` (必需): 图纸文件的完整路径
- **支持格式**: PDF, DXF, SVG, DWG, STEP, IGES
- **说明**: 
  - 文件必须存在且格式正确
  - 系统会自动解析几何元素和尺寸

### 特征识别与定义

#### 选择特征
- **API端点**: `POST /api/feature/select`
- **功能**: 在图纸上选择一个几何特征
- **参数**: 
  - `x` (必需): X坐标
  - `y` (必需): Y坐标
- **说明**: 
  - 使用容差机制选择最近的几何元素
  - 支持线、圆、矩形等多种几何类型
  - 选择成功后可进行特征定义

#### 定义特征
- **API端点**: `POST /api/feature/define`
- **功能**: 开始定义选中的特征
- **说明**: 
  - 自动创建特征定义对象
  - 准备设置特征类型和参数

#### 设置特征类型
- **API端点**: `POST /api/feature/type`
- **功能**: 为特征指定加工类型
- **参数**: 
  - `featureId` (必需): 特征ID
  - `featureType` (必需): 特征类型
- **支持的类型**:
  - `hole`: 钻孔特征
  - `pocket`: 口袋铣削特征
  - `boss`: 凸台特征
  - `slot`: 槽特征
  - `chamfer`: 倒角特征
  - `fillet`: 圆角特征
  - `extrude`: 拉伸特征
  - `cut`: 切割特征

#### 关联宏变量
- **API端点**: `POST /api/feature/variable`
- **功能**: 将宏变量关联到特征尺寸
- **参数**: 
  - `featureId` (必需): 特征ID
  - `dimensionId` (必需): 尺寸ID
  - `variableName` (必需): 变量名
- **说明**: 
  - 变量名需符合编程命名规范
  - 支持参数化编程

### G代码生成

#### 生成G代码
- **API端点**: `POST /api/gcode/generate`
- **功能**: 根据定义的特征生成G代码
- **说明**: 
  - 自动生成程序开头和结尾代码
  - 包含安全高度设置
  - 优化刀具路径

### 模拟与验证

#### 启动模拟
- **API端点**: `POST /api/simulation/start`
- **功能**: 模拟G代码执行过程
- **说明**: 
  - 生成工具路径可视化
  - 检测潜在碰撞
  - 估算加工时间

#### 变量驱动模拟
- **API端点**: `POST /api/simulation/variable`
- **功能**: 使用特定变量值进行模拟
- **参数**: 
  - `variableValues`: 包含变量名和值的对象
- **说明**: 
  - 验证不同参数下的加工效果
  - 支持参数优化

### 代码导出

#### 导出G代码
- **API端点**: `POST /api/gcode/export`
- **功能**: 将G代码导出为文件
- **参数**: 
  - `outputPath` (可选): 输出文件路径
- **说明**: 
  - 默认返回G代码文本
  - 指定路径则保存为文件

## 常见操作

### 1. 完整的编程流程示例

```bash
# 1. 创建新项目
curl -X POST http://localhost:3000/api/project/new \
  -H "Content-Type: application/json" \
  -d '{"projectName": "My Part"}'

# 2. 导入图纸
curl -X POST http://localhost:3000/api/project/import \
  -H "Content-Type: application/json" \
  -d '{"filePath": "/path/to/part.pdf"}'

# 3. 等待图纸解析完成（可以查询状态）
curl -X GET http://localhost:3000/api/state

# 4. 选择特征（假设在坐标(30, 30)有一个圆）
curl -X POST http://localhost:3000/api/feature/select \
  -H "Content-Type: application/json" \
  -d '{"x": 30, "y": 30}'

# 5. 定义特征
curl -X POST http://localhost:3000/api/feature/define

# 6. 设置特征类型为孔
curl -X POST http://localhost:3000/api/feature/type \
  -H "Content-Type: application/json" \
  -d '{"featureId": "feat_abc123", "featureType": "hole"}'

# 7. 生成G代码
curl -X POST http://localhost:3000/api/gcode/generate

# 8. 模拟验证
curl -X POST http://localhost:3000/api/simulation/start

# 9. 导出代码
curl -X POST http://localhost:3000/api/gcode/export \
  -H "Content-Type: application/json" \
  -d '{"outputPath": "/output/part.nc"}'
```

### 2. 参数化编程示例

```bash
# 1. 关联宏变量
curl -X POST http://localhost:3000/api/feature/variable \
  -H "Content-Type: application/json" \
  -d '{
    "featureId": "feat_abc123", 
    "dimensionId": "dim_1", 
    "variableName": "HOLE_DIAMETER"
  }'

# 2. 使用不同参数进行模拟
curl -X POST http://localhost:3000/api/simulation/variable \
  -H "Content-Type: application/json" \
  -d '{
    "HOLE_DIAMETER": 10,
    "HOLE_DEPTH": 20
  }'
```

### 3. 状态检查

```bash
# 检查当前应用状态
curl -X GET http://localhost:3000/api/state

# 响应示例
{
  "currentState": "ready",
  "allowedTransitions": ["feature_selected", "code_generated", "error"],
  "stateHistory": ["waiting_import", "drawing_loaded", "processing", "ready"],
  "projectExists": true,
  "featureSelected": false
}
```

## 最佳实践

### 1. 图纸准备
- 使用标准的CAD格式（PDF, DXF等）
- 确保几何元素清晰可识别
- 标注所有重要尺寸
- 保持图纸比例准确

### 2. 特征识别
- 在几何元素中心附近选择特征
- 使用足够大的容差值
- 验证选择的特征是否正确

### 3. 参数设置
- 根据材料选择合适的进给率
- 设置适当的安全高度
- 考虑刀具尺寸限制

### 4. 模拟验证
- 始终在实际加工前进行模拟
- 检查工具路径是否合理
- 验证加工时间是否符合预期

### 5. 代码导出
- 选择合适的数控系统格式
- 检查生成的G代码是否符合机床要求
- 保留原始项目文件便于修改

### 6. 性能优化
- 分批处理大型图纸
- 定期清理工作区
- 使用SSD存储提高I/O性能

### 7. 错误处理
- 检查API响应中的错误信息
- 验证状态转换的合法性
- 保持日志用于故障排除

## 安全注意事项

- 验证所有文件路径，防止路径遍历攻击
- 检查上传文件格式
- 监控系统资源使用情况
- 定期备份重要项目文件