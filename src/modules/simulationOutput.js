// src/modules/simulationOutput.js
// 模拟输出模块

const { validateGCodeSafety, detectCollisions } = require('./validation');

// 启动模拟
function startSimulation(gCodeBlocks) {
  if (!Array.isArray(gCodeBlocks)) {
    throw new Error('G代码块列表无效');
  }

  // 模拟处理时间
  const startTime = Date.now();
  
  // 模拟执行G代码
  const simulationResults = {
    id: 'sim_' + Date.now().toString(36) + Math.random().toString(36).substr(2, 5),
    status: 'completed',
    startTime: new Date(),
    endTime: null,
    executionTime: 0,
    totalCommands: gCodeBlocks.length,
    processedCommands: 0,
    progress: 0,
    toolPaths: [],
    collisionChecks: [],
    materialRemoval: 0,
    estimatedTime: 0,
    warnings: [],
    errors: [],
    statistics: {
      totalPathLength: 0,
      totalCuttingTime: 0,
      totalAirTime: 0,
      rapidMoves: 0,
      feedMoves: 0,
      spindleHours: 0
    }
  };

    // 模拟处理每个G代码块
  for (let i = 0; i < gCodeBlocks.length; i++) {
    const block = gCodeBlocks[i];
    
    // 模拟处理时间
    const processingTime = Math.random() * 50 + 10; // 10-60ms per block
    simulationResults.processedCommands++;
    simulationResults.progress = Math.round((i + 1) / gCodeBlocks.length * 100);
    
    // 生成工具路径（简化的模拟）
    if (block.type === 'feature_operation') {
      const toolPath = generateToolPath(block);
      if (toolPath) {
        simulationResults.toolPaths.push(toolPath);
        
        // 累计统计信息
        simulationResults.statistics.totalPathLength += toolPath.length;
        simulationResults.statistics.totalCuttingTime += toolPath.cuttingTime;
        simulationResults.statistics.totalAirTime += toolPath.airTime;
        simulationResults.statistics.rapidMoves += toolPath.rapidMoves;
        simulationResults.statistics.feedMoves += toolPath.feedMoves;
        
        // 计算主轴运行时间（基于进给移动时间）
        if (toolPath.spindleSpeed > 0) {
          simulationResults.statistics.spindleHours += toolPath.cuttingTime / 3600; // 转换为小时
        }
      }
    }
    
    // 进行安全和碰撞验证
    if (block.code && Array.isArray(block.code)) {
      const safetyValidation = validateGCodeSafety(block.code);
      if (safetyValidation.errors.length > 0) {
        simulationResults.errors.push(...safetyValidation.errors);
      }
      if (safetyValidation.warnings.length > 0) {
        simulationResults.warnings.push(...safetyValidation.warnings);
      }
      
      // 进行碰撞检测
      const collisionResult = detectCollisions(block.code);
      if (collisionResult.hasCollisions) {
        simulationResults.collisionChecks.push({
          blockId: block.id,
          collisions: collisionResult.collisions,
          timestamp: new Date()
        });
      }
    }
    
    // 检查潜在问题
    const issues = checkForIssues(block);
    if (issues.warnings.length > 0) {
      simulationResults.warnings.push(...issues.warnings);
    }
    if (issues.errors.length > 0) {
      simulationResults.errors.push(...issues.errors);
    }
    
    // 模拟延迟
    const now = Date.now();
    if (now - startTime > 100) {  // 如果处理时间过长，模拟进度
      break;
    }
  }

  simulationResults.endTime = new Date();
  simulationResults.executionTime = simulationResults.endTime - simulationResults.startTime;
  simulationResults.estimatedTime = simulationResults.totalCuttingTime + simulationResults.totalAirTime;

  // 计算材料移除量（基于路径长度和切削参数的模拟）
  // 这里使用简化的模拟，实际应用中需要更复杂的模型
  const avgPathLength = simulationResults.statistics.totalPathLength / Math.max(simulationResults.toolPaths.length, 1);
  simulationResults.materialRemoval = avgPathLength * 0.5; // 简化的材料移除计算

  // 计算总体效率指标
  simulationResults.efficiencyMetrics = {
    pathOptimizationRatio: simulationResults.statistics.totalPathLength / (simulationResults.statistics.rapidMoves + simulationResults.statistics.feedMoves || 1),
    airToCutRatio: simulationResults.statistics.totalAirTime / (simulationResults.statistics.totalCuttingTime || 1),
    averageFeedRate: simulationResults.statistics.totalPathLength / (simulationResults.statistics.totalCuttingTime || 1)
  };

  return simulationResults;
}

// 生成详细的工具路径
function generateToolPath(gCodeBlock) {
  if (!gCodeBlock || !gCodeBlock.code || !Array.isArray(gCodeBlock.code)) {
    return null;
  }

  // 初始化工具路径对象
  const path = {
    id: 'path_' + gCodeBlock.id,
    featureId: gCodeBlock.featureId,
    featureType: gCodeBlock.featureType,
    commands: gCodeBlock.code.length,
    start: { x: 0, y: 0, z: 0 },
    end: { x: 0, y: 0, z: 0 },
    length: 0,
    estimatedTime: 0,
    tool: gCodeBlock.parameters?.recommendedTool || 'default_tool',
    spindleSpeed: gCodeBlock.parameters?.spindleSpeed || 0,
    feedRate: gCodeBlock.parameters?.feedRate || 0,
    operations: [],
    rapidMoves: 0,
    feedMoves: 0,
    cuttingTime: 0,
    airTime: 0
  };

  // 当前位置
  let currentPosition = { x: 0, y: 0, z: 0 };
  let currentFeedRate = 0;
  let currentSpindleSpeed = 0;
  let totalCuttingTime = 0;
  let totalAirTime = 0;

  // 解析G代码
  for (const line of gCodeBlock.code) {
    // 跳过注释和空行
    if (!line || line.trim().startsWith(';')) continue;

    // 解析坐标
    const xMatch = line.match(/X\s*(-?\d+\.?\d*)/i);
    const yMatch = line.match(/Y\s*(-?\d+\.?\d*)/i);
    const zMatch = line.match(/Z\s*(-?\d+\.?\d*)/i);
    const fMatch = line.match(/F\s*(\d+\.?\d*)/i);
    const sMatch = line.match(/S\s*(\d+\.?\d*)/i);

    // 检查G代码类型
    const isRapid = line.includes('G0') || line.includes('G00');
    const isFeed = line.includes('G1') || line.includes('G01');
    const isArcCW = line.includes('G2') || line.includes('G02');
    const isArcCCW = line.includes('G3') || line.includes('G03');

    // 更新当前参数
    if (fMatch) currentFeedRate = parseFloat(fMatch[1]);
    if (sMatch) currentSpindleSpeed = parseFloat(sMatch[1]);

    // 如果有坐标变化，记录操作
    if (xMatch || yMatch || zMatch) {
      // 保存当前位置作为起点
      const previousPosition = { ...currentPosition };

      // 更新当前位置
      if (xMatch) currentPosition.x = parseFloat(xMatch[1]);
      if (yMatch) currentPosition.y = parseFloat(yMatch[1]);
      if (zMatch) currentPosition.z = parseFloat(zMatch[1]);

      // 计算移动距离
      const dx = currentPosition.x - previousPosition.x;
      const dy = currentPosition.y - previousPosition.y;
      const dz = currentPosition.z - previousPosition.z;
      const distance = Math.sqrt(dx * dx + dy * dy + dz * dz);

      // 计算移动时间
      let moveTime = 0;
      if (isRapid) {
        // 快速移动时间估算（假设快速移动速度为5000 mm/min）
        moveTime = distance / 5000 * 60; // 转换为秒
        path.rapidMoves++;
      } else if (isFeed || isArcCW || isArcCCW) {
        // 进给移动时间
        if (currentFeedRate > 0) {
          moveTime = distance / currentFeedRate * 60; // 转换为秒
          totalCuttingTime += moveTime;
        }
        path.feedMoves++;
      }

      // 记录操作
      const operation = {
        command: line.trim(),
        start: { ...previousPosition },
        end: { ...currentPosition },
        distance: distance,
        moveTime: moveTime,
        feedRate: currentFeedRate,
        spindleSpeed: currentSpindleSpeed,
        type: isRapid ? 'rapid' : isFeed ? 'linear_feed' : isArcCW ? 'arc_cw' : isArcCCW ? 'arc_ccw' : 'other'
      };

      path.operations.push(operation);

      // 累计总长度
      path.length += distance;

      // 累计时间
      if (isRapid) {
        totalAirTime += moveTime;
      }
    }
  }

  // 设置起始和结束位置
  if (path.operations.length > 0) {
    path.start = { ...path.operations[0].start };
    path.end = { ...path.operations[path.operations.length - 1].end };
  }

  // 计算总时间
  path.cuttingTime = totalCuttingTime;
  path.airTime = totalAirTime;
  path.estimatedTime = totalCuttingTime + totalAirTime;

  return path;
}

// 检查潜在问题
function checkForIssues(gCodeBlock) {
  const issues = {
    warnings: [],
    errors: []
  };

  if (!gCodeBlock || !gCodeBlock.code || !Array.isArray(gCodeBlock.code)) {
    issues.errors.push('G代码块格式无效');
    return issues;
  }

  for (const line of gCodeBlock.code) {
    // 检查潜在的错误
    if (line.includes('G91') && !line.includes('G90')) {
      issues.warnings.push('使用增量模式可能影响后续操作');
    }
    
    if (line.includes('G54') || line.includes('G55') || line.includes('G56')) {
      issues.warnings.push('使用工件坐标系，请确保已设置正确');
    }
    
    // 检查过高的进给率
    const fMatch = line.match(/F(\d+)/);
    if (fMatch) {
      const feedRate = parseInt(fMatch[1]);
      if (feedRate > 2000) {
        issues.warnings.push(`进给率 ${feedRate} 可能过高`);
      }
    }
    
    // 检查过大的移动距离
    const xMatch = line.match(/X(-?\d+\.?\d*)/);
    const yMatch = line.match(/Y(-?\d+\.?\d*)/);
    const zMatch = line.match(/Z(-?\d+\.?\d*)/);
    
    if (xMatch && Math.abs(parseFloat(xMatch[1])) > 1000) {
      issues.warnings.push(`X轴移动距离过大: ${xMatch[1]}`);
    }
    if (yMatch && Math.abs(parseFloat(yMatch[1])) > 1000) {
      issues.warnings.push(`Y轴移动距离过大: ${yMatch[1]}`);
    }
    if (zMatch && Math.abs(parseFloat(zMatch[1])) > 500) {
      issues.warnings.push(`Z轴移动距离过大: ${zMatch[1]}`);
    }
  }

  return issues;
}

// 变量驱动模拟
function variableDrivenSimulation(gCodeBlocks, variableValues) {
  if (!Array.isArray(gCodeBlocks)) {
    throw new Error('G代码块列表无效');
  }

  if (!variableValues || typeof variableValues !== 'object') {
    throw new Error('变量值参数无效');
  }

  // 创建G代码的副本以进行变量替换
  const modifiedBlocks = gCodeBlocks.map(block => {
    if (block.code && Array.isArray(block.code)) {
      const modifiedCode = block.code.map(line => {
        let modifiedLine = line;
        
        // 替换宏变量（格式为 #1, #2, #3 等）
        for (const [varName, value] of Object.entries(variableValues)) {
          // 在实际应用中，这里会根据具体的变量映射进行替换
          // 简化的模拟：查找并替换变量引用
          const regex = new RegExp(`\\${varName}\\|#{${varName}}|@${varName}`, 'g');
          modifiedLine = modifiedLine.replace(regex, value.toString());
        }
        
        return modifiedLine;
      });
      
      return {
        ...block,
        code: modifiedCode
      };
    }
    return block;
  });

  // 执行修改后的G代码的模拟
  return startSimulation(modifiedBlocks);
}

// 导出代码
function exportCode(gCodeBlocks, outputPath) {
  if (!Array.isArray(gCodeBlocks)) {
    throw new Error('G代码块列表无效');
  }

  // 验证输出路径
  if (outputPath && typeof outputPath === 'string') {
    const path = require('path');
    const fs = require('fs');
    
    // 确保输出目录存在
    const dir = path.dirname(outputPath);
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
    
    // 生成完整的G代码字符串
    let fullCode = '';
    fullCode += '; CNCagent Generated G-Code\n';
    fullCode += '; Generated on: ' + new Date().toISOString() + '\n';
    fullCode += '\n';
    
    for (const block of gCodeBlocks) {
      if (block.code && Array.isArray(block.code)) {
        fullCode += `; Block: ${block.id || 'unknown'}\n`;
        for (const line of block.code) {
          fullCode += line + '\n';
        }
        fullCode += '\n';
      }
    }
    
    // 写入文件
    fs.writeFileSync(outputPath, fullCode);
    
    return {
      success: true,
      outputPath: outputPath,
      fileSize: Buffer.byteLength(fullCode),
      lineCount: fullCode.split('\n').length
    };
  } else {
    // 如果没有提供输出路径，返回G代码字符串
    let fullCode = '';
    for (const block of gCodeBlocks) {
      if (block.code && Array.isArray(block.code)) {
        for (const line of block.code) {
          fullCode += line + '\n';
        }
      }
    }
    
    return {
      success: true,
      gCode: fullCode,
      lineCount: fullCode.split('\n').length
    };
  }
}

module.exports = {
  startSimulation,
  variableDrivenSimulation,
  exportCode
};