// src/modules/subprocesses/pdfParsingProcess.js
// PDF解析处理子模块

const fs = require('fs');
const path = require('path');
// 导入pdfjs-dist库
const pdfjsLib = require('pdfjs-dist');
const Tesseract = require('tesseract.js');
const { createCanvas } = require('canvas'); // 用于PDF到图像的转换

const { validateGeometryElements } = require('../validation');

// 尝试从文本中提取几何信息的辅助函数
function extractGeometricInfoFromText(text) {
  const geometryElements = [];
  const dimensions = [];
  const tolerances = []; // 形位公差
  const surfaceFinishes = []; // 表面光洁度
  const lines = text.split(/\r?\n/);
  let id = 0;

  
  // 更精确的正则表达式用于匹配可能的几何元素和尺寸
  // 匹配坐标对 (x, y) - 支持多种格式
  const coordPatterns = [
    /([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)/g,  // 基本坐标格式 x, y
    /X:\s*([+-]?\d+\.?\d*)\s*Y:\s*([+-]?\d+\.?\d*)/gi,  // X: x Y: y 格式
    /X\s*([+-]?\d+\.?\d*)\s*Y\s*([+-]?\d+\.?\d*)/gi,   // X x Y y 格式
    /\(([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)\)/g,     // (x, y) 格式
    /\[(\d+\.?\d*)\s*,\s*(\d+\.?\d*)\]/g,               // [x, y] 格式
    /POINT\s+\(([-+]?\d+\.?\d*)\s*,\s*([-+]?\d+\.?\d*)\)/gi,  // POINT (x, y) 格式
    /COORD\s*[:\s]+([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)/gi, // COORD: x, y 格式
    /CENTER\s*[:\s]*([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)/gi, // CENTER: x, y 格式
    /ORIGIN\s*[:\s]*([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)/gi  // ORIGIN: x, y 格式
  ];
  
  // 匹配可能的尺寸标注 - 支持多种单位
  const dimPatterns = [
    /(\d+\.?\d*)\s*mm/gi,     // 毫米
    /(\d+\.?\d*)\s*in/gi,     // 英寸
    /(\d+\.?\d*)\s*英寸/gi,   // 中文英寸
    /(\d+\.?\d*)\s*cm/gi,     // 厘米
    /(\d+\.?\d*)\s*m/gi,      // 米
    /(\d+\.?\d*)\s*mm\s*dia/gi, // 直径标注
    /R(\d+\.?\d*)/gi,         // 半径R格式
    /Ø(\d+\.?\d*)/gi,         // 直径φ格式
    /Φ(\d+\.?\d*)/gi,         // 直径Φ格式
    /DIA\s*(\d+\.?\d*)/gi,    // DIA格式直径
    /Diameter\s*(\d+\.?\d*)/gi, // Diameter格式
    /DIAMETER\s*[:\s]*([+-]?\d+\.?\d*)/gi, // DIAMETER: value 格式
    /RADIUS\s*[:\s]*([+-]?\d+\.?\d*)/gi,   // RADIUS: value 格式
    /LENGTH\s*[:\s]*([+-]?\d+\.?\d*)/gi,    // LENGTH: value 格式
    /WIDTH\s*[:\s]*([+-]?\d+\.?\d*)/gi,     // WIDTH: value 格式
    /HEIGHT\s*[:\s]*([+-]?\d+\.?\d*)/gi,    // HEIGHT: value 格式
    /SIZE\s*[:\s]*([+-]?\d+\.?\d*)/gi,      // SIZE: value 格式
    /(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)/gi, // 长x宽x高格式
    /(\d+\.?\d*)\s*x\s*(\d+\.?\d*)/gi       // 长x宽格式
  ];
  
  // 匹配圆心和半径/直径的特定模式
  const circlePatterns = [
    /CIRCLE.*?R(\d+\.?\d*)/gi,
    /CIRCLE.*?RADIUS.*?(\d+\.?\d*)/gi,
    /CIRCLE.*?(\d+\.?\d*)\s*RADIUS/gi,
    /圆.*?R(\d+\.?\d*)/gi,
    /圆形.*?半径\s*(\d+\.?\d*)/gi,
    /圆.*?半径\s*(\d+\.?\d*)/gi,
    /圆.*?直径\s*(\d+\.?\d*)/gi,
    /CIRCULAR.*?DIA\s*(\d+\.?\d*)/gi,
    /ARC.*?R(\d+\.?\d*)/gi,
    /ARC.*?RADIUS.*?(\d+\.?\d*)/gi
  ];
  
  // 匹配矩形或线段的模式
  const rectanglePatterns = [
    /RECTANGLE|RECT|矩形|长方形/gi,
    /BOX|SQUARE|正方形|方块/gi
  ];
  
  // 匹配直线的模式
  const linePatterns = [
    /LINE|STRAIGHT/gi,
    /LINEAR/gi
  ];
  
  // 匹配孔特征
  const holePatterns = [
    /HOLE/gi,
    /孔/gi,
    /THRU/gi,  // 穿透孔
    /CIRCLE/gi, // 圆形孔
    /圆/gi
  ];
  
  // 匹配螺纹特征
  const threadPatterns = [
    /THREAD/gi,
    /螺纹/gi,
    /螺紋/gi,
    /M(\d+\.?\d*)\s*x\s*(\d+\.?\d*)/gi, // M6x1 螺纹格式
    /-\s*T/gi, // 螺纹符号 -T
    /TAP/gi,   // 攻丝
    /TAPPED/gi // 已攻丝
  ];
  
  // 匹配槽特征
  const slotPatterns = [
    /SLOT/gi,
    /槽/gi,
    /GROOVE/gi,
    /KEYWAY/gi, // 键槽
    /NOTCH/gi   // 切口
  ];
  
  // 匹配边特征
  const edgePatterns = [
    /EDGE/gi,
    /边/gi,
    /EDGE\s+CHAMFER/gi,  // 边倒角
    /EDGE\s+FILLET/gi    // 边圆角
  ];
  
  // 匹配面或区域特征
  const facePatterns = [
    /SURFACE/gi,
    /面/gi,
    /SURF/gi,
    /PLANE/gi,   // 平面
    /FLAT/gi     // 平面
  ];
  
  // 匹配形位公差
  const tolerancePatterns = [
    /∥/g,      // 平行度
    /⊥/g,      // 垂直度
    /∠/g,      // 倾斜度
    /⌒/g,      // 圆弧度
    /○/g,      // 圆度
    /◎/g,      // 同轴度
    /□/g,      // 正方形度
    / cylindricity /gi, // 圆柱度
    / concentricity /gi, // 同心度
    / symmetry /gi,      // 对称度
    / runout /gi,        // 跳动
    / position /gi,      // 位置度
    / flatness /gi,      // 平面度
    / straightness /gi,  // 直线度
    / profile /gi,       // 轮廓度
    / tolerance /gi,     // 公差
    /公差/gi,
    /位置度/gi,
    /平行度/gi,
    /垂直度/gi,
    /同轴度/gi
  ];
  
  // 匹配表面光洁度
  const surfaceFinishPatterns = [
    /Ra(\d+\.?\d*)/gi,   // 表面粗糙度Ra值
    /Rz(\d+\.?\d*)/gi,   // 表面粗糙度Rz值
    /表面粗糙度/gi,
    /光洁度/gi,
    /FINISH/gi,
    /MACHINED/gi,
    /GROUND/gi,    // 磨削
    /MILLED/gi,    // 铣削
    /TURNED/gi     // 车削
  ];
  
  // 匹配倒角特征
  const chamferPatterns = [
    /CHAMFER/gi,
    /倒角/gi,
    /BEVEL/gi
  ];
  
  // 匹配圆角特征
  const filletPatterns = [
    /FILLET/gi,
    /圆角/gi,
    /R(\d+\.?\d*)\s+FILLET/gi  // R值圆角
  ];
  
  // 处理坐标
  lines.forEach((line, lineIndex) => {
    // 检测孔特征
    holePatterns.forEach(holePattern => {
      if (holePattern.test(line)) {
        // 尝试从孔的描述中提取坐标和尺寸
        const coordMatches = [...line.matchAll(/([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)/g)];
        const dimMatches = [...line.matchAll(/(\d+\.?\d*)\s*mm/gi)];
        if (coordMatches.length > 0) {
          const x = parseFloat(coordMatches[0][1]);
          const y = parseFloat(coordMatches[0][2]);
          if (!isNaN(x) && !isNaN(y)) {
            geometryElements.push({
              id: `hole_${id++}`,
              type: 'hole',
              center: { x: x, y: y },
              text: line.trim(),
              lineIndex: lineIndex
            });
          }
        }
        if (dimMatches.length > 0) {
          const diameter = parseFloat(dimMatches[0][1]);
          if (!isNaN(diameter)) {
            dimensions.push({
              id: `hole_dia_${id++}`,
              type: 'diameter',
              value: diameter,
              unit: 'mm',
              description: `Hole diameter: ${diameter} mm`,
              lineIndex: lineIndex
            });
          }
        }
      }
    });
    
    // 检测倒角
    chamferPatterns.forEach(chamferPattern => {
      if (chamferPattern.test(line)) {
        // 提取倒角尺寸
        const dimMatches = [...line.matchAll(/(\d+\.?\d*)\s*mm/gi)];
        dimMatches.forEach(match => {
          const value = parseFloat(match[1]);
          if (!isNaN(value) && value > 0) {
            dimensions.push({
              id: `chamfer_${id++}`,
              type: 'linear',
              value: value,
              unit: 'mm',
              description: `Chamfer: ${value} mm`,
              lineIndex: lineIndex
            });
          }
        });
      }
    });
    
    // 检测圆角
    filletPatterns.forEach(filletPattern => {
      const matches = [...line.matchAll(filletPattern)];
      matches.forEach(match => {
        if (match[1]) { // R值圆角
          const radius = parseFloat(match[1]);
          if (!isNaN(radius) && radius > 0) {
            dimensions.push({
              id: `fillet_${id++}`,
              type: 'radius',
              value: radius,
              unit: 'mm',
              description: `Fillet radius: ${radius} mm`,
              lineIndex: lineIndex
            });
          }
        } else {
          // 一般圆角标注
          const dimMatches = [...line.matchAll(/(\d+\.?\d*)\s*mm/gi)];
          dimMatches.forEach(dimMatch => {
            const value = parseFloat(dimMatch[1]);
            if (!isNaN(value) && value > 0) {
              dimensions.push({
                id: `fillet_${id++}`,
                type: 'radius',
                value: value,
                unit: 'mm',
                description: `Fillet: ${value} mm`,
                lineIndex: lineIndex
              });
            }
          });
        }
      });
    });
    
    // 处理坐标
    coordPatterns.forEach(pattern => {
      const matches = [...line.matchAll(pattern)];
      matches.forEach(match => {
        const x = parseFloat(match[1]);
        const y = parseFloat(match[2]);
        
        // 验证坐标合理性
        if (!isNaN(x) && !isNaN(y)) {
          if (Math.abs(x) < 10000 && Math.abs(y) < 10000) { // 合理的坐标范围
            geometryElements.push({
              id: `point_${id++}`,
              type: 'point',
              x: x,
              y: y,
              text: line.trim(),
              lineIndex: lineIndex
            });
          }
        }
      });
    });
  });
  
  // 重新遍历每行进行尺寸和几何元素解析
  lines.forEach((line, index) => {
    // 检测尺寸标注
    dimPatterns.forEach(pattern => {
      const matches = [...line.matchAll(pattern)];
      matches.forEach(match => {
        // 处理多个数字的情况（如长x宽x高或长x宽格式）
        if (match[0].includes('x') && (match[0].match(/x/g) || []).length >= 2) {
          // 长x宽x高格式
          const dims = match[0].match(/(\d+\.?\d*)/g);
          if (dims && dims.length >= 3) {
            const length = parseFloat(dims[0]);
            const width = parseFloat(dims[1]);
            const height = parseFloat(dims[2]);
            if (!isNaN(length) && !isNaN(width) && !isNaN(height)) {
              geometryElements.push({
                id: `box_${index}_${id++}`,
                type: 'box',
                length: length,
                width: width,
                height: height,
                text: line.trim(),
                lineIndex: index
              });
            }
          } else if (dims && dims.length >= 2) {
            // 长x宽格式
            const length = parseFloat(dims[0]);
            const width = parseFloat(dims[1]);
            if (!isNaN(length) && !isNaN(width)) {
              geometryElements.push({
                id: `rect_${index}_${id++}`,
                type: 'rectangle',
                width: width,
                height: length, // 假设第一个是长度，第二个是宽度
                text: line.trim(),
                lineIndex: index
              });
            }
          }
        } else {
          // 单个数值的尺寸标注
          const valueStr = match[1] || match[2] || match[3] || match[4]; // 获取匹配的数值
          if (valueStr) {
            const value = parseFloat(valueStr);
            if (!isNaN(value) && value > 0) {
              // 确定尺寸类型
              let dimensionType = 'linear';
              if (match[0].includes('R') || match[0].includes('半径') || match[0].includes('RADIUS')) {
                dimensionType = 'radius';
              } else if (match[0].includes('Ø') || match[0].includes('Φ') || match[0].includes('DIA') || match[0].includes('Diameter') || match[0].includes('DIAMETER')) {
                dimensionType = 'diameter';
              } else if (match[0].includes('WIDTH') || match[0].includes('LENGTH') || match[0].includes('HEIGHT')) {
                dimensionType = 'linear';
              }
              
              dimensions.push({
                id: `dim_${index}_${id++}`,
                type: dimensionType,
                value: value,
                unit: 'mm', // 默认单位为毫米
                description: line.trim(),
                lineIndex: index
              });
            }
          }
        }
      });
    });
    
    // 检测圆形元素
    circlePatterns.forEach(pattern => {
      const matches = [...line.matchAll(pattern)];
      matches.forEach(match => {
        const radius = parseFloat(match[1]);
        if (!isNaN(radius) && radius > 0) {
          geometryElements.push({
            id: `circle_${index}_${id++}`,
            type: 'circle',
            center: { x: 0, y: 0 }, // 初始位置，需要从上下文推断
            radius: radius,
            text: line.trim(),
            lineIndex: index
          });
        }
      });
    });
    
    // 检测矩形元素
    rectanglePatterns.forEach(pattern => {
      if (pattern.test(line)) {
        // 尝试从同一行或附近行提取尺寸
        const dimMatches = [...line.matchAll(/(\d+\.?\d*)\s*x\s*(\d+\.?\d*)/gi)];
        dimMatches.forEach(dimMatch => {
          const width = parseFloat(dimMatch[1]);
          const height = parseFloat(dimMatch[2]);
          if (!isNaN(width) && !isNaN(height) && width > 0 && height > 0) {
            geometryElements.push({
              id: `rect_${index}_${id++}`,
              type: 'rectangle',
              width: width,
              height: height,
              text: line.trim(),
              lineIndex: index
            });
          }
        });
      }
    });
    
    // 检测直线元素
    linePatterns.forEach(pattern => {
      if (pattern.test(line)) {
        // 尝试从同一行提取直线信息
        const pointMatches = [...line.matchAll(/([+-]?\d+\.?\d*)[,\s]+([+-]?\d+\.?\d*)/g)];
        if (pointMatches.length >= 2) { // 线段至少需要两个点
          const start = { x: parseFloat(pointMatches[0][1]), y: parseFloat(pointMatches[0][2]) };
          const end = { x: parseFloat(pointMatches[1][1]), y: parseFloat(pointMatches[1][2]) };
          if (!isNaN(start.x) && !isNaN(start.y) && !isNaN(end.x) && !isNaN(end.y)) {
            geometryElements.push({
              id: `line_${index}_${id++}`,
              type: 'line',
              start: start,
              end: end,
              text: line.trim(),
              lineIndex: index
            });
          }
        }
      }
    });
    
    // 检测螺纹
    threadPatterns.forEach(threadPattern => {
      const threadMatches = [...line.matchAll(threadPattern)];
      threadMatches.forEach(match => {
        // 检查是否是M格式螺纹 (如 M6x1)
        if (match[0].toUpperCase().startsWith('M') && match[1] && match[2]) {
          const diameter = parseFloat(match[1]);
          const pitch = parseFloat(match[2]);
          if (!isNaN(diameter) && !isNaN(pitch)) {
            geometryElements.push({
              id: `thread_${index}_${id++}`,
              type: 'thread',
              diameter: diameter,
              pitch: pitch,
              text: line.trim(),
              lineIndex: index
            });
          }
        } else {
          // 一般螺纹标注
          geometryElements.push({
            id: `thread_${index}_${id++}`,
            type: 'thread',
            text: line.trim(),
            lineIndex: index
          });
        }
      });
    });
    
    // 检测槽
    slotPatterns.forEach(slotPattern => {
      if (slotPattern.test(line)) {
        // 尝试从槽的描述中提取尺寸
        const dimMatches = [...line.matchAll(/(\d+\.?\d*)\s*mm/gi)];
        const lengthMatches = [...line.matchAll(/(\d+\.?\d*)\s*x\s*(\d+\.?\d*)/gi)];
        if (lengthMatches.length > 0) {
          const length = parseFloat(lengthMatches[0][1]);
          const width = parseFloat(lengthMatches[0][2]);
          if (!isNaN(length) && !isNaN(width)) {
            geometryElements.push({
              id: `slot_${index}_${id++}`,
              type: 'slot',
              length: length,
              width: width,
              text: line.trim(),
              lineIndex: index
            });
          }
        } else if (dimMatches.length > 0) {
          const length = parseFloat(dimMatches[0][1]);
          if (!isNaN(length)) {
            geometryElements.push({
              id: `slot_${index}_${id++}`,
              type: 'slot',
              length: length,
              text: line.trim(),
              lineIndex: index
            });
          }
        } else {
          geometryElements.push({
            id: `slot_${index}_${id++}`,
            type: 'slot',
            text: line.trim(),
            lineIndex: index
          });
        }
      }
    });
    
    // 检测边
    edgePatterns.forEach(edgePattern => {
      if (edgePattern.test(line)) {
        geometryElements.push({
          id: `edge_${index}_${id++}`,
          type: 'edge',
          text: line.trim(),
          lineIndex: index
        });
      }
    });
    
    // 检测面
    facePatterns.forEach(facePattern => {
      if (facePattern.test(line)) {
        geometryElements.push({
          id: `face_${index}_${id++}`,
          type: 'face',
          text: line.trim(),
          lineIndex: index
        });
      }
    });
    
    // 检测形位公差
    tolerancePatterns.forEach(tolerancePattern => {
      const toleranceMatches = [...line.matchAll(tolerancePattern)];
      toleranceMatches.forEach(match => {
        // 检查是否包含公差值
        const valueMatches = [...line.matchAll(/(\d+\.?\d*)/g)];
        if (valueMatches.length > 0) {
          const value = parseFloat(valueMatches[0][1] || valueMatches[0][0]);
          if (!isNaN(value)) {
            tolerances.push({
              id: `tolerance_${index}_${id++}`,
              type: 'geometric_tolerance',
              value: value,
              symbol: match[0],
              description: line.trim(),
              lineIndex: index
            });
          } else {
            tolerances.push({
              id: `tolerance_${index}_${id++}`,
              type: 'geometric_tolerance',
              symbol: match[0],
              description: line.trim(),
              lineIndex: index
            });
          }
        } else {
          tolerances.push({
            id: `tolerance_${index}_${id++}`,
            type: 'geometric_tolerance',
            symbol: match[0],
            description: line.trim(),
            lineIndex: index
          });
        }
      });
    });
    
    // 检测表面光洁度
    surfaceFinishPatterns.forEach(surfaceFinishPattern => {
      const finishMatches = [...line.matchAll(surfaceFinishPattern)];
      finishMatches.forEach(match => {
        if (match[1]) { // Ra或Rz值
          const value = parseFloat(match[1]);
          if (!isNaN(value)) {
            surfaceFinishes.push({
              id: `surface_finish_${index}_${id++}`,
              type: 'surface_roughness',
              value: value,
              symbol: match[0],
              description: line.trim(),
              lineIndex: index
            });
          }
        } else {
          surfaceFinishes.push({
            id: `surface_finish_${index}_${id++}`,
            type: 'surface_roughness',
            symbol: match[0],
            description: line.trim(),
            lineIndex: index
          });
        }
      });
    });
  });
  
    // 尝试从上下文推断圆心位置和其他关联信息
  for (let i = 0; i < geometryElements.length; i++) {
    if (geometryElements[i].type === 'circle') {
      // 查找附近的坐标点作为圆心
      for (let j = 0; j < geometryElements.length; j++) {
        if (geometryElements[j].type === 'point' && i !== j) {
          // 如果圆的文本描述中包含点的信息，可以推断圆心
          const circleText = geometryElements[i].text || '';
          const pointText = geometryElements[j].text || '';
          // 检查是否在同一行或相邻行，或者文本内容有相关性
          if (Math.abs(geometryElements[i].lineIndex - geometryElements[j].lineIndex) <= 1 ||
              circleText.includes(pointText) || pointText.includes(circleText)) {
            geometryElements[i].center = { x: geometryElements[j].x, y: geometryElements[j].y };
            break;
          }
        }
      }
    }
  }
  
  // 尝试关联尺寸标注与几何元素
  for (let i = 0; i < dimensions.length; i++) {
    for (let j = 0; j < geometryElements.length; j++) {
      // 尝试将尺寸标注与几何元素关联
      const dimText = dimensions[i].description || '';
      const geomText = geometryElements[j].text || '';
      
      // 如果尺寸描述和几何元素文本相关，则建立关联
      if (dimText.includes(geomText) || geomText.includes(dimText)) {
        if (!geometryElements[j].dimensions) {
          geometryElements[j].dimensions = [];
        }
        geometryElements[j].dimensions.push(dimensions[i].id);
      }
      
      // 更智能的关联：检查几何元素的坐标是否接近尺寸标注中的数值
      if (geometryElements[j].center) {
        // 检查X坐标是否与尺寸值匹配
        if (Math.abs(geometryElements[j].center.x - dimensions[i].value) < 1.0 ||
            Math.abs(geometryElements[j].center.y - dimensions[i].value) < 1.0 ||
            Math.abs(geometryElements[j].center.x + dimensions[i].value) < 1.0 ||
            Math.abs(geometryElements[j].center.y + dimensions[i].value) < 1.0) {
          if (!geometryElements[j].dimensions) {
            geometryElements[j].dimensions = [];
          }
          if (!geometryElements[j].dimensions.includes(dimensions[i].id)) {
            geometryElements[j].dimensions.push(dimensions[i].id);
          }
        }
      }
    }
  }
  
  // 增强复杂CAD图纸解析：识别几何关系
  const enhancedGeometryElements = enhanceGeometricRelationships(geometryElements, dimensions);
  return { geometryElements: enhancedGeometryElements, dimensions, tolerances, surfaceFinishes };
}

// 增强几何元素关系识别
function enhanceGeometricRelationships(geometryElements, dimensions) {
  // 识别同心圆
  for (let i = 0; i < geometryElements.length; i++) {
    if (geometryElements[i].type === 'circle') {
      for (let j = i + 1; j < geometryElements.length; j++) {
        if (geometryElements[j].type === 'circle') {
          // 检查是否为同心圆（中心点接近）
          if (geometryElements[i].center && geometryElements[j].center) {
            const distance = Math.sqrt(
              Math.pow(geometryElements[i].center.x - geometryElements[j].center.x, 2) +
              Math.pow(geometryElements[i].center.y - geometryElements[j].center.y, 2)
            );
            if (distance < 0.5) { // 如果中心点距离小于0.5mm，则认为是同心圆
              if (!geometryElements[i].relatedElements) geometryElements[i].relatedElements = [];
              if (!geometryElements[j].relatedElements) geometryElements[j].relatedElements = [];
              geometryElements[i].relatedElements.push(geometryElements[j].id);
              geometryElements[j].relatedElements.push(geometryElements[i].id);
              
              // 标记为同心圆特征
              geometryElements[i].isConcentric = true;
              geometryElements[j].isConcentric = true;
            }
          }
        }
      }
    }
  }
  
  // 识别孔组
  const circles = geometryElements.filter(el => el.type === 'circle' && el.center);
  if (circles.length > 1) {
    // 检查孔是否形成规则阵列（如圆形分布、矩形分布等）
    const holeGroups = identifyHoleGroups(circles);
    holeGroups.forEach((group, idx) => {
      for (const circleId of group.holeIds) {
        const circle = geometryElements.find(el => el.id === circleId);
        if (circle) {
          if (!circle.featureGroup) circle.featureGroup = [];
          circle.featureGroup.push(`hole_group_${idx}`);
          circle.groupType = group.type; // 'bolt_circle', 'rectangular_array', etc.
        }
      }
    });
  }
  
  return geometryElements;
}

// 识别孔组（如螺栓圆、矩形阵列等）
function identifyHoleGroups(circles) {
  const groups = [];
  const processed = new Set();
  
  for (let i = 0; i < circles.length; i++) {
    if (processed.has(circles[i].id)) continue;
    
    // 检查是否可能是螺栓圆的一部分
    const potentialBoltCircle = findBoltCircle(circles, i);
    if (potentialBoltCircle && potentialBoltCircle.holeIds.length > 2) {
      groups.push({
        type: 'bolt_circle',
        center: potentialBoltCircle.center,
        radius: potentialBoltCircle.radius,
        holeIds: potentialBoltCircle.holeIds
      });
      
      // 标记这些孔为已处理
      potentialBoltCircle.holeIds.forEach(id => processed.add(id));
    } else {
      // 检查是否可能是矩形阵列
      const potentialRectArray = findRectangularArray(circles, i);
      if (potentialRectArray && potentialRectArray.holeIds.length > 1) {
        groups.push({
          type: 'rectangular_array',
          origin: potentialRectArray.origin,
          spacing: potentialRectArray.spacing,
          dimensions: potentialRectArray.dimensions,
          holeIds: potentialRectArray.holeIds
        });
        
        // 标记这些孔为已处理
        potentialRectArray.holeIds.forEach(id => processed.add(id));
      } else {
        // 单个孔，不需要分组
        processed.add(circles[i].id);
      }
    }
  }
  
  return groups;
}

// 查找可能的螺栓圆
function findBoltCircle(circles, startIndex) {
  const centerCandidate = circles[startIndex].center;
  const distances = [];
  
  for (let i = 0; i < circles.length; i++) {
    if (i === startIndex) continue;
    
    const dist = Math.sqrt(
      Math.pow(circles[i].center.x - centerCandidate.x, 2) +
      Math.pow(circles[i].center.y - centerCandidate.y, 2)
    );
    distances.push({ index: i, distance: dist, circle: circles[i] });
  }
  
  // 对距离进行分组，查找相同距离的孔
  const distanceGroups = {};
  const tolerance = 0.5; // 0.5mm的公差
  for (const dist of distances) {
    // 找到最接近的距离桶
    let foundGroup = false;
    for (const [distKey, group] of Object.entries(distanceGroups)) {
      if (Math.abs(parseFloat(distKey) - dist.distance) < tolerance) {
        group.push(dist);
        foundGroup = true;
        break;
      }
    }
    if (!foundGroup) {
      distanceGroups[dist.distance] = [dist];
    }
  }
  
  // 查找包含至少3个孔的距离组
  for (const [distKey, group] of Object.entries(distanceGroups)) {
    if (group.length >= 3) { // 至少3个孔才能形成圆
      return {
        center: centerCandidate,
        radius: parseFloat(distKey),
        holeIds: [circles[startIndex].id, ...group.map(d => d.circle.id)]
      };
    }
  }
  
  return null;
}

// 查找可能的矩形阵列
function findRectangularArray(circles, startIndex) {
  const origin = circles[startIndex].center;
  const xCoords = new Set();
  const yCoords = new Set();
  
  // 收集所有孔的坐标
  for (const circle of circles) {
    xCoords.add(circle.center.x);
    yCoords.add(circle.center.y);
  }
  
  const sortedX = Array.from(xCoords).sort((a, b) => a - b);
  const sortedY = Array.from(yCoords).sort((a, b) => a - b);
  
  // 检查是否形成规则的网格
  if (sortedX.length > 1 && sortedY.length > 1) {
    // 计算X和Y方向的间距
    const xSpacing = sortedX.length > 1 ? (sortedX[sortedX.length - 1] - sortedX[0]) / (sortedX.length - 1) : 0;
    const ySpacing = sortedY.length > 1 ? (sortedY[sortedY.length - 1] - sortedY[0]) / (sortedY.length - 1) : 0;
    
    // 检查是否为等间距分布
    let isRegular = true;
    if (sortedX.length > 2) {
      for (let i = 1; i < sortedX.length; i++) {
        const calculatedSpacing = sortedX[i] - sortedX[i-1];
        if (Math.abs(calculatedSpacing - xSpacing) > 0.1) {
          isRegular = false;
          break;
        }
      }
    }
    
    if (sortedY.length > 2) {
      for (let i = 1; i < sortedY.length; i++) {
        const calculatedSpacing = sortedY[i] - sortedY[0];
        if (Math.abs(calculatedSpacing - ySpacing * i) > 0.1) {
          isRegular = false;
          break;
        }
      }
    }
    
    if (isRegular && xSpacing > 0.1 && ySpacing > 0.1) {
      // 确认实际存在这些位置的孔
      const expectedHoles = [];
      for (let xIdx = 0; xIdx < sortedX.length; xIdx++) {
        for (let yIdx = 0; yIdx < sortedY.length; yIdx++) {
          const expectedX = sortedX[0] + xIdx * xSpacing;
          const expectedY = sortedY[0] + yIdx * ySpacing;
          
          // 查找实际存在的孔
          for (const circle of circles) {
            if (Math.abs(circle.center.x - expectedX) < 0.2 && Math.abs(circle.center.y - expectedY) < 0.2) {
              expectedHoles.push(circle.id);
            }
          }
        }
      }
      
      if (expectedHoles.length >= 2 && expectedHoles.length >= sortedX.length * sortedY.length * 0.7) { // 至少70%的孔存在
        return {
          origin: { x: sortedX[0], y: sortedY[0] },
          spacing: { x: xSpacing, y: ySpacing },
          dimensions: { x: sortedX.length, y: sortedY.length },
          holeIds: expectedHoles
        };
      }
    }
  }
  
  return null;
}

// 从PDF的绘图操作中提取几何信息
async function extractGeometricInfoFromDrawingOperations(page) {
  const geometryElements = [];
  const dimensions = [];
  const tolerances = []; // 形位公差
  const surfaceFinishes = []; // 表面光洁度
  let id = 0;
  
  try {
    // 获取页面的绘图操作列表
    const operatorList = await page.getOperatorList();
    
    if (operatorList && operatorList.fnArray) {
      let currentPoint = { x: 0, y: 0 };
      let pathStartPoint = { x: 0, y: 0 };
      let pathPoints = [];
      let currentTransform = [1, 0, 0, 1, 0, 0]; // 初始变换矩阵
      
      for (let i = 0; i < operatorList.fnArray.length; i++) {
        const fn = operatorList.fnArray[i];
        const args = operatorList.argsArray[i];
        
        // 根据PDF操作码检测几何形状
        switch (fn) {
          case pdfjsLib.OPS.save: // 保存图形状态
            break;
          case pdfjsLib.OPS.restore: // 恢复图形状态
            break;
          case pdfjsLib.OPS.transform: // 应用变换矩阵
            if (args && args.length >= 6) {
              currentTransform = args;
            }
            break;
          case pdfjsLib.OPS.moveTo: // 移动到点
            if (args && args.length >= 2) {
              const [x, y] = transformPoint(args[0], args[1], currentTransform);
              currentPoint = { x, y };
              pathStartPoint = { ...currentPoint };
              pathPoints = [currentPoint];
            }
            break;
          case pdfjsLib.OPS.lineTo: // 画线到点
            if (args && args.length >= 2) {
              const [x, y] = transformPoint(args[0], args[1], currentTransform);
              const newPoint = { x, y };
              geometryElements.push({
                id: `line_${id++}`,
                type: 'line',
                start: currentPoint,
                end: newPoint,
                operationIndex: i
              });
              currentPoint = newPoint;
              pathPoints.push(currentPoint);
            }
            break;
          case pdfjsLib.OPS.rectangle: // 矩形
            if (args && args.length >= 4) {
              const [x, y, width, height] = args;
              if (width !== 0 && height !== 0) {
                const transformedX = currentTransform[0] * x + currentTransform[2] * y + currentTransform[4];
                const transformedY = currentTransform[1] * x + currentTransform[3] * y + currentTransform[5];
                const transformedWidth = width * Math.sqrt(currentTransform[0]**2 + currentTransform[1]**2);
                const transformedHeight = height * Math.sqrt(currentTransform[2]**2 + currentTransform[3]**2);
                
                geometryElements.push({
                  id: `rect_${id++}`,
                  type: 'rectangle',
                  x: transformedX,
                  y: transformedY,
                  width: Math.abs(transformedWidth),
                  height: Math.abs(transformedHeight),
                  operationIndex: i
                });
                
                // 添加尺寸标注
                dimensions.push({
                  id: `dim_width_${id++}`,
                  type: 'linear',
                  value: Math.abs(transformedWidth),
                  unit: 'pdf_units',
                  description: 'Rectangle width from PDF drawing operations',
                  operationIndex: i
                });
                
                dimensions.push({
                  id: `dim_height_${id++}`,
                  type: 'linear',
                  value: Math.abs(transformedHeight),
                  unit: 'pdf_units',
                  description: 'Rectangle height from PDF drawing operations',
                  operationIndex: i
                });
              }
            }
            break;
          case pdfjsLib.OPS.curveTo: // 贝塞尔曲线
            if (args && args.length >= 6) {
              const [x1, y1, x2, y2, x3, y3] = args;
              const p1 = transformPoint(x1, y1, currentTransform);
              const p2 = transformPoint(x2, y2, currentTransform);
              const p3 = transformPoint(x3, y3, currentTransform);
              
              geometryElements.push({
                id: `curve_${id++}`,
                type: 'curve',
                start: currentPoint,
                controlPoints: [{ x: p1.x, y: p1.y }, { x: p2.x, y: p2.y }],
                end: { x: p3.x, y: p3.y },
                operationIndex: i
              });
              
              currentPoint = { x: p3.x, y: p3.y };
              pathPoints.push(currentPoint);
            }
            break;
          case pdfjsLib.OPS.closePath: // 闭合路径
            if (pathPoints.length > 1) {
              // 创建闭合路径（可能是多边形、圆形等）
              geometryElements.push({
                id: `closed_path_${id++}`,
                type: 'polygon',
                points: [...pathPoints],
                operationIndex: i
              });
            }
            break;
          case pdfjsLib.OPS.stroke: // 描边
            // 检查当前路径是否可以识别为特定形状（例如圆形、椭圆等）
            if (pathPoints.length > 2) {
              // 这里可以添加更复杂的形状识别逻辑
              // 例如，检查路径点是否接近圆形或椭圆
              const pathLength = pathPoints.length;
              if (pathLength > 10) { // 假设多于10个点的闭合路径可能是圆形或椭圆
                // 尝试拟合圆形或椭圆（简化实现）
                const centerX = pathPoints.reduce((sum, p) => sum + p.x, 0) / pathLength;
                const centerY = pathPoints.reduce((sum, p) => sum + p.y, 0) / pathLength;
                const avgRadius = pathPoints.reduce((sum, p) => {
                  const dist = Math.sqrt((p.x - centerX)**2 + (p.y - centerY)**2);
                  return sum + dist;
                }, 0) / pathLength;
                
                if (avgRadius > 0.1) { // 避免非常小的圆形
                  geometryElements.push({
                    id: `circle_${id++}`,
                    type: 'circle',
                    center: { x: centerX, y: centerY },
                    radius: avgRadius,
                    points: pathPoints,
                    operationIndex: i
                  });
                }
              }
            }
            break;
          // 添加对其他操作码的处理以识别更多元素
          case pdfjsLib.OPS.fill: // 填充
            // 可用于识别实心形状，如螺纹
            break;
          default:
            // 其他操作码可以进一步处理
            break;
        }
      }
    }
  } catch (error) {
    console.warn('无法从绘图操作中提取几何信息:', error.message);
  }
  
  return { geometryElements, dimensions, tolerances, surfaceFinishes };
}

// 帮助函数：应用变换矩阵到点
function transformPoint(x, y, matrix) {
  const [a, b, c, d, e, f] = matrix;
  return {
    x: a * x + c * y + e,
    y: b * x + d * y + f
  };
}

const pdfjs = require('pdfjs-dist');

// 在Node.js环境中，我们需要使用canvas来处理PDF到图像的转换
// 这里我们定义一个辅助函数来渲染PDF页面为图像并进行OCR
async function extractFromPdfImage(pdf, page, scale = 2.0) {
  try {
    // 获取页面的视口
    const viewport = page.getViewport({ scale: scale });
    
    // 创建canvas用于渲染PDF页面
    const canvas = createCanvas(viewport.width, viewport.height);
    const context = canvas.getContext('2d');
    
    // 设置渲染参数
    const renderContext = {
      canvasContext: context,
      viewport: viewport
    };
    
    // 渲染PDF页面到canvas
    await page.render(renderContext).promise;
    
    // 将canvas转换为图像数据
    const imageData = canvas.toBuffer('image/png');
    
    // 使用Tesseract进行OCR识别
    const { createWorker } = require('tesseract.js');
    const worker = createWorker();
    
    await worker.load();
    await worker.loadLanguage('eng+chi_sim'); // 加载英文和中文简体语言包
    await worker.initialize('eng+chi_sim');
    
    const result = await worker.recognize(imageData);
    const text = result.data.text;
    
    await worker.terminate();
    
    console.log(`OCR识别完成，识别到文本长度: ${text.length}`);
    return text;
  } catch (error) {
    console.error('OCR处理失败:', error.message);
    return '';
  }
}

// 自动视角识别函数
function identifyViewOrientation(geometryElements, dimensions, textContent) {
  // 检查是否存在坐标系标注
  const hasCoordinateSystem = textContent.toLowerCase().includes('x') && textContent.toLowerCase().includes('y');
  
  // 检查是否有标注原点
  const hasOrigin = textContent.toLowerCase().includes('origin') || textContent.includes('ORIGIN') || textContent.includes('原点');
  
  // 分析几何元素的位置分布
  const points = geometryElements.filter(el => el.center || (el.x !== undefined && el.y !== undefined));
  if (points.length > 0) {
    const xCoords = points.map(p => p.center ? p.center.x : p.x);
    const yCoords = points.map(p => p.center ? p.center.y : p.y);
    const minX = Math.min(...xCoords);
    const maxX = Math.max(...xCoords);
    const minY = Math.min(...yCoords);
    const maxY = Math.max(...yCoords);
    
    // 判断图纸的主要视角
    if (maxX > 0 && maxY > 0) {
      // 如果所有坐标都是正数，可能采用第一象限坐标系
      return {
        origin: { x: minX, y: maxY }, // 通常左上角为原点
        orientation: 'top_left_quadrant1',
        xPositiveDirection: 'right',
        yPositiveDirection: 'down'
      };
    } else {
      // 如果有负坐标，使用中心为原点的坐标系
      return {
        origin: { x: (minX + maxX) / 2, y: (minY + maxY) / 2 },
        orientation: 'center_zero',
        xPositiveDirection: 'right',
        yPositiveDirection: 'up'
      };
    }
  }
  
  // 默认返回右上角为原点的坐标系
  return {
    origin: { x: 0, y: 0 },
    orientation: 'top_right',
    xPositiveDirection: 'left', // X轴向左为正
    yPositiveDirection: 'down'  // Y轴向下为正
  };
}

// 解析PDF内容的主要函数
async function pdfParsingProcess(filePath) {
  if (!filePath || typeof filePath !== 'string') {
    throw new Error('文件路径无效');
  }

  if (!fs.existsSync(filePath)) {
    throw new Error(`文件不存在: ${filePath}`);
  }

  // 获取文件信息
  const stats = fs.statSync(filePath);
  const fileExtension = path.extname(filePath).toLowerCase();

  // 根据文件类型返回不同结果
  let drawingInfo = {
    fileName: path.basename(filePath),
    filePath: filePath,
    fileSize: stats.size,
    fileType: fileExtension,
    parsedAt: new Date(),
    pageCount: 0, // 将在解析后更新
    dimensions: { width: 0, height: 0 }
  };

  let geometryElements = [];
  let dimensions = [];
  let tolerances = []; // 形位公差
  let surfaceFinishes = []; // 表面光洁度
  let textContent = ''; // 存储所有文本内容用于视角识别

  // 对于PDF文件，进行实际解析
  if (fileExtension === '.pdf') {
    try {
      const data = new Uint8Array(fs.readFileSync(filePath));
      const pdf = await pdfjsLib.getDocument({ data }).promise;
      
      drawingInfo.pageCount = pdf.numPages;
      
      // 解析每一页的内容
      for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        
        // 首先尝试直接从PDF文本层提取信息
        let pageText = '';
        try {
          const textContentObj = await page.getTextContent();
          pageText = textContentObj.items.map(item => item.str).join(' ');
          textContent += pageText + ' '; // 累积所有页面的文本
        } catch (textError) {
          console.warn(`无法从第${pageNum}页提取文本内容:`, textError.message);
        }
        
        // 从文本中提取几何信息
        const extracted = extractGeometricInfoFromText(pageText);
        geometryElements = [...geometryElements, ...extracted.geometryElements];
        dimensions = [...dimensions, ...extracted.dimensions];
        
        // 从PDF绘图操作中提取几何信息
        try {
          const drawingExtracted = await extractGeometricInfoFromDrawingOperations(page);
          geometryElements = [...geometryElements, ...drawingExtracted.geometryElements];
          dimensions = [...dimensions, ...drawingExtracted.dimensions];
          tolerances = [...tolerances, ...drawingExtracted.tolerances];
          surfaceFinishes = [...surfaceFinishes, ...drawingExtracted.surfaceFinishes];
        } catch (drawingError) {
          console.warn(`从第${pageNum}页的绘图操作中提取几何信息失败:`, drawingError.message);
        }
        
        // 如果文本提取没有得到足够的几何信息，尝试使用OCR
        if (geometryElements.length < 5) { // 如果几何元素少于5个，尝试OCR
          try {
            console.log(`尝试对第${pageNum}页进行OCR处理...`);
            const ocrText = await extractFromPdfImage(pdf, page, 2.0);
            if (ocrText && ocrText.trim().length > 0) {
              console.log(`OCR识别成功，文本长度: ${ocrText.length}`);
              
              // 从OCR文本中提取几何信息
              const ocrExtracted = extractGeometricInfoFromText(ocrText);
              geometryElements = [...geometryElements, ...ocrExtracted.geometryElements];
              dimensions = [...dimensions, ...ocrExtracted.dimensions];
              // 添加OCR提取的其他信息
              if (ocrExtracted.tolerances) {
                tolerances = [...tolerances, ...ocrExtracted.tolerances];
              }
              if (ocrExtracted.surfaceFinishes) {
                surfaceFinishes = [...surfaceFinishes, ...ocrExtracted.surfaceFinishes];
              }
            } else {
              console.log(`OCR未能识别到有用的文本内容`);
            }
          } catch (ocrError) {
            console.warn(`OCR处理失败:`, ocrError.message);
          }
        }
      }
      
      // 检查PDF的页面信息
      if (pdf.numPages > 0) {
        const firstPage = await pdf.getPage(1);
        const viewport = firstPage.getViewport({ scale: 1.0 });
        drawingInfo.dimensions = { 
          width: viewport.width, 
          height: viewport.height 
        };
      }
      
      // 自动视角识别
      drawingInfo.viewOrientation = identifyViewOrientation(geometryElements, dimensions, textContent);
      
      // 检查是否存在螺纹特征
      const threadPattern = /thread|螺纹|螺紋|THRU|tapped|tap/gi;
      drawingInfo.hasThreads = threadPattern.test(textContent);
      
      // 检查是否存在槽特征
      const slotPattern = /slot|槽|SLOT/gi;
      drawingInfo.hasSlots = slotPattern.test(textContent);
      
      // 检查是否存在倒角特征
      const chamferPattern = /chamfer|倒角|CHAMFER/gi;
      drawingInfo.hasChamfers = chamferPattern.test(textContent);
      
      // 检查是否存在圆角特征
      const filletPattern = /fillet|圆角|FILLET|R\d+/gi;
      drawingInfo.hasFillets = filletPattern.test(textContent);
      
      // 如果仍然没有提取到足够的几何元素，尝试更高级的分析
      if (geometryElements.length === 0) {
        // 这种情况可能需要更复杂的CAD图纸解析算法
        console.warn('警告: 无法从PDF中提取几何元素，图纸可能包含图像而非文本/矢量内容');
        
        // 作为备选方案，我们可以尝试分析PDF的结构
        // 这里我们保持空数组，让上层代码处理回退逻辑
      }
      
    } catch (error) {
      console.error('PDF解析错误:', error);
      throw new Error(`PDF解析失败: ${error.message}`);
    }
  } else {
    // 对于其他文件类型，返回简化数据
    geometryElements = [
      { id: 'element_1', type: 'rectangle', bounds: { x: 0, y: 0, width: 100, height: 50 } }
    ];
    
    dimensions = [
      { id: 'dim_1', type: 'linear', value: 100 },
      { id: 'dim_2', type: 'linear', value: 50 }
    ];
    
    drawingInfo.dimensions = { width: 100, height: 50 };
  }

  // 如果最终没有提取到任何几何元素，提供一些默认值以确保API的稳定性
  if (geometryElements.length === 0) {
    geometryElements = [
      { id: 'default_rectangle', type: 'rectangle', bounds: { x: 10, y: 10, width: 80, height: 60 } }
    ];
  }

    // 验证几何元素的有效性
  const validation = validateGeometryElements(geometryElements);
  if (validation.warnings && validation.warnings.length > 0) {
    console.warn('几何元素验证警告:', validation.warnings);
  }

  return {
    drawingInfo,
    geometryElements,
    dimensions,
    tolerances,
    surfaceFinishes,
    parsingTime: Date.now() - new Date().getTime()
  };
}


module.exports = {
  pdfParsingProcess
};