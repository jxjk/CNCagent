// src/modules/validation.js
// CNC加工验证和错误处理模块

// 验证G代码块的有效性
function validateGCodeBlocks(gCodeBlocks) {
  if (!Array.isArray(gCodeBlocks)) {
    throw new Error('G代码块必须是数组');
  }

  const errors = [];
  const warnings = [];

  for (let i = 0; i < gCodeBlocks.length; i++) {
    const block = gCodeBlocks[i];
    
    if (!block || typeof block !== 'object') {
      errors.push(`G代码块 ${i} 无效: 不是对象`);
      continue;
    }

    if (!block.id || typeof block.id !== 'string') {
      errors.push(`G代码块 ${i} 无效: 缺少有效的ID`);
    }

    if (!Array.isArray(block.code)) {
      errors.push(`G代码块 ${i} 无效: 代码不是数组`);
      continue;
    }

    // 检查代码行
    for (let j = 0; j < block.code.length; j++) {
      const line = block.code[j];
      if (typeof line !== 'string') {
        errors.push(`G代码块 ${i} 行 ${j} 无效: 代码行不是字符串`);
      }
    }

    // 检查是否存在危险的G代码指令
    for (let j = 0; j < block.code.length; j++) {
      const line = block.code[j];
      if (line.toUpperCase().includes('M30') && j !== block.code.length - 1) {
        warnings.push(`G代码块 ${i}: 程序结束指令M30不在最后`);
      }
    }
  }

  return { errors, warnings };
}

// 验证特征参数的有效性
function validateFeatureParameters(feature) {
  if (!feature || typeof feature !== 'object') {
    return { valid: false, errors: ['特征参数无效'] };
  }

  const errors = [];

  if (!feature.featureType) {
    errors.push('缺少特征类型');
  }

  if (!feature.parameters || typeof feature.parameters !== 'object') {
    errors.push('缺少特征参数或参数格式无效');
  } else {
    const params = feature.parameters;

    switch (feature.featureType) {
      case 'hole':
      case 'counterbore':
        if (typeof params.diameter === 'number' && params.diameter <= 0) {
          errors.push('孔径必须大于0');
        }
        if (typeof params.depth === 'number' && params.depth <= 0) {
          errors.push('深度必须大于0');
        }
        break;
      case 'pocket':
        if (typeof params.width === 'number' && params.width <= 0) {
          errors.push('宽度必须大于0');
        }
        if (typeof params.length === 'number' && params.length <= 0) {
          errors.push('长度必须大于0');
        }
        if (typeof params.depth === 'number' && params.depth <= 0) {
          errors.push('深度必须大于0');
        }
        break;
      case 'thread':
        if (typeof params.diameter === 'number' && params.diameter <= 0) {
          errors.push('螺纹直径必须大于0');
        }
        if (typeof params.pitch === 'number' && params.pitch <= 0) {
          errors.push('螺距必须大于0');
        }
        break;
      default:
        break;
    }
  }

  return { valid: errors.length === 0, errors };
}

// 验证几何元素的有效性
function validateGeometryElements(geometryElements) {
  if (!Array.isArray(geometryElements)) {
    return { valid: false, errors: ['几何元素必须是数组'] };
  }

  const errors = [];
  const warnings = [];

  for (let i = 0; i < geometryElements.length; i++) {
    const element = geometryElements[i];

    if (!element || typeof element !== 'object') {
      errors.push(`几何元素 ${i} 无效: 不是对象`);
      continue;
    }

    if (!element.type) {
      errors.push(`几何元素 ${i} 无效: 缺少类型`);
    }

    // 验证特定类型的几何元素
    switch (element.type) {
      case 'circle':
        if (!element.center || typeof element.center !== 'object') {
          errors.push(`圆形元素 ${i} 无效: 缺少中心点`);
        } else {
          if (typeof element.center.x !== 'number') {
            errors.push(`圆形元素 ${i} 无效: 中心点X坐标不是数字`);
          }
          if (typeof element.center.y !== 'number') {
            errors.push(`圆形元素 ${i} 无效: 中心点Y坐标不是数字`);
          }
        }
        if (typeof element.radius === 'number' && element.radius <= 0) {
          errors.push(`圆形元素 ${i} 无效: 半径必须大于0`);
        }
        break;
      case 'line':
        if (!element.start || typeof element.start !== 'object') {
          errors.push(`线元素 ${i} 无效: 缺少起点`);
        } else {
          if (typeof element.start.x !== 'number') {
            errors.push(`线元素 ${i} 无效: 起点X坐标不是数字`);
          }
          if (typeof element.start.y !== 'number') {
            errors.push(`线元素 ${i} 无效: 起点Y坐标不是数字`);
          }
        }
        if (!element.end || typeof element.end !== 'object') {
          errors.push(`线元素 ${i} 无效: 缺少终点`);
        } else {
          if (typeof element.end.x !== 'number') {
            errors.push(`线元素 ${i} 无效: 终点X坐标不是数字`);
          }
          if (typeof element.end.y !== 'number') {
            errors.push(`线元素 ${i} 无效: 终点Y坐标不是数字`);
          }
        }
        break;
      case 'rectangle':
        if (typeof element.width === 'number' && element.width <= 0) {
          errors.push(`矩形元素 ${i} 无效: 宽度必须大于0`);
        }
        if (typeof element.height === 'number' && element.height <= 0) {
          errors.push(`矩形元素 ${i} 无效: 高度必须大于0`);
        }
        break;
      case 'thread':
        if (typeof element.diameter === 'number' && element.diameter <= 0) {
          errors.push(`螺纹元素 ${i} 无效: 直径必须大于0`);
        }
        if (typeof element.pitch === 'number' && element.pitch <= 0) {
          errors.push(`螺纹元素 ${i} 无效: 螺距必须大于0`);
        }
        break;
      default:
        warnings.push(`未知的几何元素类型: ${element.type}`);
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

// 验证加工参数的合理性
function validateMachiningParameters(features) {
  if (!Array.isArray(features)) {
    return { valid: false, errors: ['特征列表必须是数组'] };
  }

  const errors = [];
  const warnings = [];

  for (let i = 0; i < features.length; i++) {
    const feature = features[i];
    
    if (!feature || typeof feature !== 'object') {
      continue;
    }

    // 检查加工参数是否合理
    if (feature.parameters) {
      const params = feature.parameters;

      // 检查进给率
      if (typeof params.feedRate === 'number') {
        if (params.feedRate <= 0) {
          errors.push(`特征 ${i} 的进给率必须大于0`);
        } else if (params.feedRate > 2000) {
          warnings.push(`特征 ${i} 的进给率(${params.feedRate})可能过高`);
        }
      }

      // 检查主轴转速
      if (typeof params.spindleSpeed === 'number') {
        if (params.spindleSpeed <= 0) {
          errors.push(`特征 ${i} 的主轴转速必须大于0`);
        } else if (params.spindleSpeed > 10000) {
          warnings.push(`特征 ${i} 的主轴转速(${params.spindleSpeed})可能过高`);
        }
      }

      // 检查深度参数
      if (typeof params.depth === 'number' && params.depth <= 0) {
        errors.push(`特征 ${i} 的深度必须大于0`);
      }
    }
  }

  return { valid: errors.length === 0, errors, warnings };
}

// 验证G代码语法
function validateGCodeSyntax(gCodeLines) {
  if (!Array.isArray(gCodeLines)) {
    return { valid: false, errors: ['G代码行必须是数组'] };
  }

  const errors = [];
  const warnings = [];
  const gCodes = new Set();
  const mCodes = new Set();

  for (let i = 0; i < gCodeLines.length; i++) {
    const line = gCodeLines[i];
    if (typeof line !== 'string') {
      continue;
    }

    // 提取G代码和M代码
    const gMatches = line.match(/G(\d+\.?\d*)/gi);
    if (gMatches) {
      gMatches.forEach(g => {
        gCodes.add(g.toUpperCase());
      });
    }

    const mMatches = line.match(/M(\d+\.?\d*)/gi);
    if (mMatches) {
      mMatches.forEach(m => {
        mCodes.add(m.toUpperCase());
      });
    }

    // 检查语法错误
    if (line.startsWith('G') && !line.match(/^G\d+(\.\d+)?/)) {
      warnings.push(`G代码行 ${i}: G代码格式可能不正确 - "${line}"`);
    }

    if (line.startsWith('M') && !line.match(/^M\d+(\.\d+)?/)) {
      warnings.push(`G代码行 ${i}: M代码格式可能不正确 - "${line}"`);
    }

    // 检查常见的错误模式
    if (line.includes('G0') && line.includes('F')) {
      warnings.push(`G代码行 ${i}: G00快速移动不应包含进给率F - "${line}"`);
    }
  }

  return { valid: errors.length === 0, errors, warnings, gCodes: Array.from(gCodes), mCodes: Array.from(mCodes) };
}

// 验证G代码的运动安全性和逻辑性
function validateGCodeSafety(gCodeLines) {
  if (!Array.isArray(gCodeLines)) {
    return { valid: false, errors: ['G代码行必须是数组'] };
  }

  const errors = [];
  const warnings = [];
  let currentX = 0, currentY = 0, currentZ = 0;
  let currentFeedRate = 0;
  let isRapidMove = false;
  let isModalGCode = {};
  
  for (let i = 0; i < gCodeLines.length; i++) {
    const line = gCodeLines[i].toUpperCase().trim();
    if (!line || line.startsWith(';')) { // 跳过注释行
      continue;
    }

    // 解析坐标值
    const xMatch = line.match(/X\s*(-?\d+\.?\d*)/i);
    const yMatch = line.match(/Y\s*(-?\d+\.?\d*)/i);
    const zMatch = line.match(/Z\s*(-?\d+\.?\d*)/i);
    const fMatch = line.match(/F\s*(\d+\.?\d*)/i);
    
    // 检查G代码
    const gMatches = line.match(/G\s*(\d+\.?\d*)/g);
    if (gMatches) {
      gMatches.forEach(g => {
        const gCode = g.replace(/\s/g, ''); // 移除空格
        const gNum = parseFloat(gCode.substring(1));
        switch(gNum) {
          case 0: // 快速移动
            isRapidMove = true;
            break;
          case 1: // 直线插补
            isRapidMove = false;
            break;
          case 2: // 顺时针圆弧插补
          case 3: // 逆时针圆弧插补
            isRapidMove = false;
            break;
          case 17: // XY平面
          case 18: // XZ平面
          case 19: // YZ平面
            break;
          case 20: // 英制单位
            warnings.push(`G代码行 ${i}: 使用英制单位可能与系统设置冲突`);
            break;
          case 21: // 公制单位
            // 这是推荐的单位
            break;
          case 90: // 绝对坐标
            isModalGCode.absolute = true;
            break;
          case 91: // 增量坐标
            isModalGCode.absolute = false;
            break;
        }
      });
    }

    // 检查坐标值的合理性
    if (xMatch) {
      const xVal = parseFloat(xMatch[1]);
      if (Math.abs(xVal) > 1000) { // 假设最大工作范围为1000mm
        errors.push(`G代码行 ${i}: X坐标值${xVal}超出安全范围`);
      } else {
        currentX = xVal;
      }
    }
    if (yMatch) {
      const yVal = parseFloat(yMatch[1]);
      if (Math.abs(yVal) > 1000) {
        errors.push(`G代码行 ${i}: Y坐标值${yVal}超出安全范围`);
      } else {
        currentY = yVal;
      }
    }
    if (zMatch) {
      const zVal = parseFloat(zMatch[1]);
      if (zVal > 200 || zVal < -200) { // 假设Z轴范围为-200到200mm
        errors.push(`G代码行 ${i}: Z坐标值${zVal}超出安全范围`);
      } else {
        currentZ = zVal;
      }
    }

    // 检查进给率
    if (fMatch) {
      const fVal = parseFloat(fMatch[1]);
      if (fVal <= 0) {
        errors.push(`G代码行 ${i}: 进给率F必须大于0`);
      } else if (fVal > 5000) {
        warnings.push(`G代码行 ${i}: 进给率F${fVal}可能过高`);
      } else {
        currentFeedRate = fVal;
      }
    }

    // 检查非移动G代码后直接移动的情况
    if (line.includes('M03') && i < gCodeLines.length - 1) {
      // 检查主轴启动后是否合理设置了参数
      if (currentFeedRate === 0) {
        warnings.push(`G代码行 ${i}: 主轴启动后应设置合适的进给率`);
      }
    }
  }

  return { valid: errors.length === 0, errors, warnings, finalPosition: { x: currentX, y: currentY, z: currentZ } };
}

// 碰撞检测算法
function detectCollisions(gCodeLines, workpieceDimensions = { x: 200, y: 200, z: 100 }, toolDiameter = 6) {
  if (!Array.isArray(gCodeLines)) {
    return { hasCollisions: true, errors: ['G代码行必须是数组'] };
  }

  const collisions = [];
  let currentX = 0, currentY = 0, currentZ = 0; // 当前工具位置
  let previousX = 0, previousY = 0, previousZ = 0; // 前一位置
  let isRapidMove = false; // 是否为快速移动
  let isCutting = false; // 是否在切削

  // 工件边界
  const workpieceBounds = {
    minX: -workpieceDimensions.x / 2,
    maxX: workpieceDimensions.x / 2,
    minY: -workpieceDimensions.y / 2,
    maxY: workpieceDimensions.y / 2,
    minZ: 0, // 假设工件顶部为Z=0
    maxZ: workpieceDimensions.z
  };

  // 刀具半径
  const toolRadius = toolDiameter / 2;

  for (let i = 0; i < gCodeLines.length; i++) {
    const line = gCodeLines[i].toUpperCase().trim();
    if (!line || line.startsWith(';')) { // 跳过注释行
      continue;
    }

    // 保存当前位置作为前一位置
    previousX = currentX;
    previousY = currentY;
    previousZ = currentZ;

    // 检查G代码
    const gMatches = line.match(/G\s*(\d+\.?\d*)/g);
    if (gMatches) {
      gMatches.forEach(g => {
        const gNum = parseFloat(g.replace(/\s/g, '').substring(1));
        switch(gNum) {
          case 0: // 快速移动
            isRapidMove = true;
            isCutting = false;
            break;
          case 1: // 直线插补
            isRapidMove = false;
            isCutting = true;
            break;
          case 2: // 顺时针圆弧插补
          case 3: // 逆时针圆弧插补
            isRapidMove = false;
            isCutting = true;
            break;
        }
      });
    }

    // 解析坐标值
    const xMatch = line.match(/X\s*(-?\d+\.?\d*)/i);
    const yMatch = line.match(/Y\s*(-?\d+\.?\d*)/i);
    const zMatch = line.match(/Z\s*(-?\d+\.?\d*)/i);
    
    if (xMatch) currentX = parseFloat(xMatch[1]);
    if (yMatch) currentY = parseFloat(yMatch[1]);
    if (zMatch) currentZ = parseFloat(zMatch[1]);

    // 检查是否在工件边界内
    if (isCutting) {
      // 检查当前位置是否在工件边界内
      if (currentX < workpieceBounds.minX || currentX > workpieceBounds.maxX ||
          currentY < workpieceBounds.minY || currentY > workpieceBounds.maxY ||
          currentZ < workpieceBounds.minZ - toolRadius || currentZ > workpieceBounds.maxZ + toolRadius) {
        collisions.push({
          type: 'boundary_violation',
          description: `在G代码行 ${i}，刀具位置 (${currentX}, ${currentY}, ${currentZ}) 超出工件边界`,
          line: i,
          position: { x: currentX, y: currentY, z: currentZ }
        });
      }

      // 检查快速移动时的安全高度
      if (isRapidMove && currentZ < workpieceBounds.maxZ - 5) { // 假设安全高度为工件顶部上方5mm
        collisions.push({
          type: 'rapid_move_collision',
          description: `在G代码行 ${i}，快速移动高度(${currentZ})过低，可能与工件碰撞`,
          line: i,
          position: { x: currentX, y: currentY, z: currentZ }
        });
      }

      // 检查刀具与工件的潜在碰撞
      // 通过检查移动路径是否穿过工件内部
      if (isRapidMove) {
        // 对于快速移动，检查路径是否穿过工件
        const pathCheck = checkPathCollision(previousX, previousY, previousZ, currentX, currentY, currentZ, workpieceBounds, toolRadius);
        if (pathCheck.collision) {
          collisions.push({
            type: 'rapid_path_collision',
            description: `在G代码行 ${i}，快速移动路径从(${previousX}, ${previousY}, ${previousZ})到(${currentX}, ${currentY}, ${currentZ})可能与工件碰撞`,
            line: i,
            start: { x: previousX, y: previousY, z: previousZ },
            end: { x: currentX, y: currentY, z: currentZ }
          });
        }
      }
    }

    // 检查Z轴极限位置
    if (currentZ < -50) { // 假设Z轴下限为-50mm
      collisions.push({
        type: 'z_limit_exceeded',
        description: `在G代码行 ${i}，Z轴位置(${currentZ})超出下限，可能导致刀具与工作台碰撞`,
        line: i,
        position: { x: currentX, y: currentY, z: currentZ }
      });
    }

    // 检查是否在安全起始位置
    if (i === 0 && isCutting && currentZ > -5) { // 如果第一个指令就是切削且不在安全高度
      collisions.push({
        type: 'unsafe_start',
        description: `在G代码行 ${i}，起始位置(${currentX}, ${currentY}, ${currentZ})不安全，应先移动到安全高度再开始切削`,
        line: i,
        position: { x: currentX, y: currentY, z: currentZ }
      });
    }
  }

  return { hasCollisions: collisions.length > 0, collisions, workpieceBounds, toolRadius };
}

// 辅助函数：检查移动路径是否与工件碰撞
function checkPathCollision(startX, startY, startZ, endX, endY, endZ, workpieceBounds, toolRadius) {
  // 简化的路径碰撞检测
  // 这里使用线性插值检查路径上的几个点
  const steps = 10; // 将路径分为10个点进行检查
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const x = startX + (endX - startX) * t;
    const y = startY + (endY - startY) * t;
    const z = startZ + (endZ - startZ) * t;

    // 检查该点是否在工件内部（考虑刀具半径）
    if (x >= workpieceBounds.minX - toolRadius && x <= workpieceBounds.maxX + toolRadius &&
        y >= workpieceBounds.minY - toolRadius && y <= workpieceBounds.maxY + toolRadius &&
        z >= workpieceBounds.minZ - toolRadius && z <= workpieceBounds.maxZ + toolRadius) {
      return { collision: true, point: { x, y, z } };
    }
  }

  return { collision: false };
}

module.exports = {
  validateGCodeBlocks,
  validateFeatureParameters,
  validateGeometryElements,
  validateMachiningParameters,
  validateGCodeSyntax,
  validateGCodeSafety,
  detectCollisions
};