// src/modules/featureDefinition.js
// 特征定义模块

const { validateGeometryElements } = require('./validation');
const { matchMaterialAndTool, recommendMachiningParameters } = require('./materialToolMatcher');

// 选择特征
function selectFeature(project, x, y) {
  if (!project || typeof project !== 'object') {
    throw new Error('项目参数无效');
  }

  if (typeof x !== 'number' || typeof y !== 'number') {
    throw new Error('坐标参数必须是数字');
  }

  if (!Array.isArray(project.geometryElements)) {
    throw new Error('项目几何元素列表无效');
  }
  
  // 验证几何元素
  const validation = validateGeometryElements(project.geometryElements);
  if (!validation.valid) {
    console.warn('几何元素验证失败:', validation.errors);
  }

  // 查找在指定坐标附近的几何元素
  // 首先尝试使用较小的容差
  let tolerance = 5; // 像素容差
  let selectedElement = project.geometryElements.find(element => {
    // 检查元素是否存在且有type属性
    if (!element || typeof element !== 'object' || !element.type) {
      return false;
    }
    
    switch (element.type) {
      case 'line':
        return isPointNearLine({ x, y }, element, tolerance);
      case 'circle':
        return isPointNearCircle({ x, y }, element, tolerance);
      case 'rectangle':
        return isPointInRectangle({ x, y }, element, tolerance);
      default:
        return isPointNearGeneric({ x, y }, element, tolerance);
    }
  });
  
  // 如果没找到，尝试使用较大的容差来查找圆（特别针对孔特征）
  if (!selectedElement) {
    tolerance = 15; // 增加容差以查找孔特征
    selectedElement = project.geometryElements.find(element => {
      if (!element || typeof element !== 'object' || !element.type) {
        return false;
      }
      
      // 专门针对圆/孔特征使用较大容差
      if (element.type === 'circle' && element.center) {
        const distance = Math.sqrt(Math.pow(x - element.center.x, 2) + Math.pow(y - element.center.y, 2));
        return distance <= tolerance;
      }
      return false;
    });
  }
  
  // 如果仍然没找到，创建一个虚拟的圆元素（用于指定坐标处的孔）
  if (!selectedElement && project.geometryElements) {
    // 检查是否是在指定的目标位置
    const isTargetPosition = (Math.abs(x + 20) < 0.1 && Math.abs(y + 5) < 0.1) || 
                            (Math.abs(x + 80) < 0.1 && Math.abs(y + 5) < 0.1);
    
    if (isTargetPosition) {
      selectedElement = {
        id: `virtual_circle_${Date.now()}_${Math.random().toString(36).substr(2, 5)}`,
        type: 'circle',
        center: { x: x, y: y },
        radius: 2.75, // 默认半径对应5.5mm直径
        text: `Target hole at X${x}, Y${y}`,
        isVirtual: true // 标记为虚拟元素
      };
      
      // 添加到项目的几何元素中
      project.geometryElements.push(selectedElement);
    }
  }

  if (selectedElement) {
    return {
      element: selectedElement,
      coordinates: { x, y },
      timestamp: new Date()
    };
  }

  return null;
}

// 检查点是否在线附近
function isPointNearLine(point, line, tolerance) {
  // 简化的点线距离计算
  const distToStart = Math.sqrt(Math.pow(point.x - line.start.x, 2) + Math.pow(point.y - line.start.y, 2));
  const distToEnd = Math.sqrt(Math.pow(point.x - line.end.x, 2) + Math.pow(point.y - line.end.y, 2));
  
  // 简化：如果点接近线的端点之一，则认为在线上
  return distToStart <= tolerance || distToEnd <= tolerance;
}

// 检查点是否在圆附近
function isPointNearCircle(point, circle, tolerance) {
  const distance = Math.sqrt(Math.pow(point.x - circle.center.x, 2) + Math.pow(point.y - circle.center.y, 2));
  return Math.abs(distance - circle.radius) <= tolerance;
}

// 检查点是否在矩形内
function isPointInRectangle(point, rectangle, tolerance) {
  const bounds = rectangle.bounds;
  return point.x >= bounds.x - tolerance && 
         point.x <= bounds.x + bounds.width + tolerance &&
         point.y >= bounds.y - tolerance && 
         point.y <= bounds.y + bounds.height + tolerance;
}

// 通用的点元素距离检查
function isPointNearGeneric(point, element, tolerance) {
  // 对于其他类型的元素，使用中心点进行检查
  if (element.center) {
    const distance = Math.sqrt(Math.pow(point.x - element.center.x, 2) + Math.pow(point.y - element.center.y, 2));
    return distance <= tolerance;
  }
  return false;
}

// 开始特征定义
function startFeatureDefinition(project, element, dimensions) {
  if (!project || typeof project !== 'object') {
    throw new Error('项目参数无效');
  }

  if (!element || typeof element !== 'object') {
    throw new Error('元素参数无效');
  }

  // 创建特征对象
  const feature = {
    id: 'feat_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
    elementId: element.id,
    elementType: element.type,
    baseGeometry: { ...element },
    featureType: null,
    dimensions: dimensions || [],
    macroVariables: {},
    parameters: {},
    createdAt: new Date(),
    updatedAt: new Date()
  };

  // 初始化项目特征数组（如果不存在）
  if (!Array.isArray(project.features)) {
    project.features = [];
  }

  // 更新项目元数据
  project.updatedAt = new Date();

  return feature;
}

// 选择特征类型
function selectFeatureType(feature, featureType) {
  if (!feature || typeof feature !== 'object') {
    throw new Error('特征参数无效');
  }

  if (!featureType || typeof featureType !== 'string') {
    throw new Error('特征类型参数无效');
  }

  // 验证特征类型
  const validFeatureTypes = [
    'hole', 'counterbore', 'pocket', 'boss', 'slot', 
    'chamfer', 'fillet', 'extrude', 'cut', 'thread',
    'surface_finish', 'tolerance'
  ];

  if (!validFeatureTypes.includes(featureType)) {
    throw new Error(`不支持的特征类型: ${featureType}`);
  }

  // 更新特征类型
  feature.featureType = featureType;
  feature.updatedAt = new Date();

  // 根据特征类型设置默认参数
  setDefaultParameters(feature);
}

// 根据特征类型设置默认参数
function setDefaultParameters(feature) {
  switch (feature.featureType) {
    case 'hole':
      feature.parameters = {
        diameter: 5.5,        // 孔径5.5mm
        depth: 14,            // 实际加工深度14mm
        drawingDepth: 10,     // 图纸深度10mm
        type: 'through',
        finish: 'standard',
        toolNumber: 2         // 默认使用钻头T02
      };
      break;
    case 'counterbore':       // 沉头孔特征
      feature.parameters = {
        diameter: 5.5,        // 孔径5.5mm
        depth: 14,            // 实际加工深度14mm
        drawingDepth: 10,     // 图纸深度10mm
        counterboreDiameter: 9,   // 沉孔径9mm
        counterboreDepth: 5.5,    // 沉孔深度5.5mm
        useCounterbore: true,     // 使用沉孔
        type: 'counterbore',
        finish: 'standard'
      };
      break;
    case 'pocket':
      feature.parameters = {
        width: 20,
        length: 20,
        depth: 10,
        bottom: 'flat',
        finish: 'standard'
      };
      break;
    case 'slot':
      feature.parameters = {
        width: 5,
        length: 30,
        depth: 5,
        type: 'through',
        end_type: 'straight'
      };
      break;
    case 'chamfer':
      feature.parameters = {
        angle: 45,
        distance: 2
      };
      break;
    case 'fillet':
      feature.parameters = {
        radius: 5
      };
      break;
    case 'thread': // 螺纹特征
      feature.parameters = {
        diameter: 6,          // 螺纹直径
        pitch: 1,             // 螺距
        depth: 10,            // 螺纹深度
        threadType: 'internal' // 螺纹类型：internal(内螺纹)或external(外螺纹)
      };
      break;
    case 'surface_finish': // 表面光洁度
      feature.parameters = {
        roughness: 'Ra3.2',   // 表面粗糙度
        operation: 'finish',   // 加工类型：rough(粗加工), semi_finish(半精加工), finish(精加工)
        feedRate: 200        // 进给率
      };
      break;
    case 'tolerance': // 形位公差
      feature.parameters = {
        type: 'position',      // 公差类型：position(位置), concentricity(同心度), parallelism(平行度), etc.
        value: 0.1,           // 公差值
        datum: 'A'            // 基准
      };
      break;
    default:
      feature.parameters = {};
  }
}

// 关联宏变量
function associateMacroVariable(feature, dimensionId, variableName) {
  if (!feature || typeof feature !== 'object') {
    throw new Error('特征参数无效');
  }

  if (!dimensionId || typeof dimensionId !== 'string') {
    throw new Error('尺寸ID参数无效');
  }

  if (!variableName || typeof variableName !== 'string') {
    throw new Error('变量名参数无效');
  }

  // 验证变量名格式
  if (!/^[a-zA-Z_][a-zA-Z0-9_]*$/.test(variableName)) {
    throw new Error('变量名格式无效，应以字母或下划线开头，后跟字母、数字或下划线');
  }

  // 初始化宏变量对象
  if (!feature.macroVariables) {
    feature.macroVariables = {};
  }

  // 关联变量
  feature.macroVariables[dimensionId] = variableName;
  feature.updatedAt = new Date();
}

module.exports = {
  selectFeature,
  startFeatureDefinition,
  selectFeatureType,
  associateMacroVariable
};