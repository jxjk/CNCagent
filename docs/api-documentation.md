# CNCagent API 文档

## 概述

CNCagent提供RESTful API接口，用于控制CNC编程工作流程。所有API端点都以`/api/`为前缀，返回JSON格式的响应。

### 基础信息
- **基础URL**: `http://localhost:3000/api/` (默认端口)
- **内容类型**: `application/json`
- **请求限制**: 每15分钟最多100个请求

### 响应格式

成功响应格式:
```json
{
  "success": true,
  "data": { /* 具体数据 */ }
}
```

错误响应格式:
```json
{
  "success": false,
  "error": "错误信息"
}
```

## 状态管理

### 获取当前状态
```
GET /api/state
```

获取当前应用状态信息。

#### 参数
- 无

#### 响应示例
```json
{
  "currentState": "waiting_import",
  "allowedTransitions": ["drawing_loaded", "error"],
  "stateHistory": ["waiting_import"],
  "projectExists": false,
  "featureSelected": false
}
```

#### 响应字段
- `currentState`: 当前状态 (waiting_import, drawing_loaded, processing, ready, feature_selected, defining_feature, code_generated, simulation_running, code_exported, error)
- `allowedTransitions`: 允许的状态转换
- `stateHistory`: 状态转换历史
- `projectExists`: 是否存在项目
- `featureSelected`: 是否已选择特征

## 项目管理

### 创建新项目
```
POST /api/project/new
```

初始化一个新项目。

#### 请求体
```json
{
  "projectName": "可选的项目名称"
}
```

#### 响应示例
```json
{
  "success": true,
  "state": "waiting_import"
}
```

### 导入图纸
```
POST /api/project/import
```

导入CAD图纸文件。

#### 请求体
```json
{
  "filePath": "图纸文件的完整路径"
}
```

#### 请求体字段
- `filePath` (必需): 支持的文件格式包括 .pdf, .dxf, .svg, .dwg, .step, .iges

#### 响应示例
```json
{
  "success": true,
  "project": {
    "id": "proj_123abc",
    "name": "文件名",
    "filePath": "文件路径",
    "drawingInfo": null,
    "geometryElements": [],
    "dimensions": [],
    "features": [],
    "gCodeBlocks": [],
    "createdAt": "2023-01-01T00:00:00.000Z",
    "updatedAt": "2023-01-01T00:00:00.000Z",
    "workspacePath": "工作区路径"
  }
}
```

## 特征处理

### 选择特征
```
POST /api/feature/select
```

在图纸上选择一个几何特征。

#### 请求体
```json
{
  "x": 100,
  "y": 200
}
```

#### 请求体字段
- `x` (必需): X坐标 (数字)
- `y` (必需): Y坐标 (数字)

#### 响应示例
```json
{
  "success": true,
  "selection": {
    "element": {
      "id": "line_1",
      "type": "line",
      "start": { "x": 10, "y": 10 },
      "end": { "x": 50, "y": 10 }
    },
    "coordinates": { "x": 100, "y": 200 },
    "timestamp": "2023-01-01T00:00:00.000Z"
  }
}
```

### 定义特征
```
POST /api/feature/define
```

开始定义选中的特征。

#### 请求体
- 无

#### 响应示例
```json
{
  "success": true,
  "feature": {
    "id": "feat_abc123",
    "elementId": "line_1",
    "elementType": "line",
    "baseGeometry": { ... },
    "featureType": null,
    "dimensions": [],
    "macroVariables": {},
    "parameters": {},
    "createdAt": "2023-01-01T00:00:00.000Z",
    "updatedAt": "2023-01-01T00:00:00.000Z"
  }
}
```

### 设置特征类型
```
POST /api/feature/type
```

为特征指定类型。

#### 请求体
```json
{
  "featureId": "feat_abc123",
  "featureType": "hole"
}
```

#### 请求体字段
- `featureId` (必需): 特征ID
- `featureType` (必需): 特征类型 (hole, pocket, boss, slot, chamfer, fillet, extrude, cut)

#### 响应示例
```json
{
  "success": true,
  "feature": {
    "id": "feat_abc123",
    "featureType": "hole",
    "parameters": {
      "diameter": 10,
      "depth": 20,
      "type": "through",
      "finish": "standard"
    }
  }
}
```

### 关联宏变量
```
POST /api/feature/variable
```

将宏变量关联到特征的特定尺寸。

#### 请求体
```json
{
  "featureId": "feat_abc123",
  "dimensionId": "dim_1",
  "variableName": "HOLE_DIAMETER"
}
```

#### 请求体字段
- `featureId` (必需): 特征ID
- `dimensionId` (必需): 尺寸ID
- `variableName` (必需): 变量名 (符合JavaScript变量命名规范)

#### 响应示例
```json
{
  "success": true,
  "feature": {
    "id": "feat_abc123",
    "macroVariables": {
      "dim_1": "HOLE_DIAMETER"
    }
  }
}
```

## G代码生成

### 生成G代码
```
POST /api/gcode/generate
```

根据定义的特征生成G代码。

#### 请求体
- 无

#### 响应示例
```json
{
  "success": true,
  "gCodeBlocks": [
    {
      "id": "program_start",
      "type": "program_control",
      "code": [
        "G21 ; 设置单位为毫米",
        "G90 ; 设置绝对位置模式",
        ...
      ],
      "featureId": null,
      "createdAt": "2023-01-01T00:00:00.000Z"
    },
    {
      "id": "gcode_feat_abc123",
      "type": "feature_operation",
      "code": [
        "; 生成孔 - 直径: 10, 深度: 20",
        "G43 H1 ; 刀具长度补偿",
        ...
      ],
      "featureId": "feat_abc123",
      "featureType": "hole",
      "parameters": { ... },
      "createdAt": "2023-01-01T00:00:00.000Z"
    }
  ]
}
```

### 导出G代码
```
POST /api/gcode/export
```

将生成的G代码导出到文件。

#### 请求体
```json
{
  "outputPath": "输出文件路径"
}
```

#### 请求体字段
- `outputPath` (可选): 输出文件的完整路径

#### 响应示例
```json
{
  "success": true,
  "gCode": {
    "success": true,
    "outputPath": "C:/output/program.nc",
    "fileSize": 2048,
    "lineCount": 25
  }
}
```

## 模拟功能

### 启动模拟
```
POST /api/simulation/start
```

启动G代码执行模拟。

#### 请求体
- 无

#### 响应示例
```json
{
  "success": true,
  "results": {
    "id": "sim_xyz789",
    "status": "completed",
    "startTime": "2023-01-01T00:00:00.000Z",
    "endTime": "2023-01-01T00:00:01.000Z",
    "executionTime": 1000,
    "totalCommands": 15,
    "processedCommands": 15,
    "progress": 100,
    "toolPaths": [ ... ],
    "collisionChecks": [],
    "materialRemoval": 75.5,
    "estimatedTime": 1000,
    "warnings": [],
    "errors": []
  }
}
```

### 变量驱动模拟
```
POST /api/simulation/variable
```

使用特定变量值执行模拟。

#### 请求体
```json
{
  "variableValues": {
    "HOLE_DIAMETER": 15,
    "HOLE_DEPTH": 25
  }
}
```

#### 请求体字段
- `variableValues` (必需): 包含变量名和值的对象

#### 响应示例
```json
{
  "success": true,
  "results": {
    "id": "sim_abc123",
    "status": "completed",
    "executionTime": 1200,
    "toolPaths": [ ... ],
    "materialRemoval": 85.2,
    "warnings": [],
    "errors": []
  }
}
```

## 错误代码

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | Invalid input | 输入参数无效 |
| 400 | Missing required parameter | 缺少必要参数 |
| 400 | Request contains malicious content | 请求包含潜在恶意内容 |
| 404 | API endpoint does not exist | API端点不存在 |
| 500 | Server internal error | 服务器内部错误 |
| 500 | Project initialization failed | 项目初始化失败 |
| 500 | Drawing import failed | 图纸导入失败 |
| 500 | Feature selection failed | 特征选择失败 |
| 500 | G-code generation failed | G代码生成失败 |

## 安全注意事项

- 所有输入都会经过验证，防止XSS攻击
- 实现了请求频率限制
- 文件路径验证防止路径遍历攻击
- 参数类型验证防止类型错误

## 使用示例

### JavaScript/Fetch 示例
```javascript
// 创建新项目
fetch('http://localhost:3000/api/project/new', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ projectName: 'My Project' })
})
.then(response => response.json())
.then(data => console.log(data));

// 导入图纸
fetch('http://localhost:3000/api/project/import', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ 
    filePath: 'C:/drawings/part.pdf' 
  })
})
.then(response => response.json())
.then(data => console.log(data));

// 选择特征
fetch('http://localhost:3000/api/feature/select', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ x: 100, y: 200 })
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL 示例
```bash
# 获取当前状态
curl -X GET http://localhost:3000/api/state

# 创建新项目
curl -X POST http://localhost:3000/api/project/new \
  -H "Content-Type: application/json" \
  -d '{"projectName": "Test Project"}'

# 导入图纸
curl -X POST http://localhost:3000/api/project/import \
  -H "Content-Type: application/json" \
  -d '{"filePath": "/path/to/drawing.pdf"}'

# 选择特征
curl -X POST http://localhost:3000/api/feature/select \
  -H "Content-Type: application/json" \
  -d '{"x": 100, "y": 200}'

# 生成G代码
curl -X POST http://localhost:3000/api/gcode/generate \
  -H "Content-Type: application/json"
```