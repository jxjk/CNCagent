const axios = require('axios');
const fs = require('fs');
const path = require('path');

// 定义可能的端口
const PORTS = [3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009];
let currentPort = 3000;
let BASE_URL = '';

// 检查哪个端口可用
async function findAvailablePort() {
  for (const port of PORTS) {
    try {
      const response = await axios.get(`http://localhost:${port}/api/state`);
      if (response.status === 200) {
        console.log(`服务器在端口 ${port} 上可用`);
        return port;
      }
    } catch (error) {
      console.log(`端口 ${port} 不可用`);
      continue;
    }
  }
  return null;
}

// 等待状态变为指定值
async function waitForState(targetState, timeout = 30000) { // 增加超时时间
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    try {
      const stateRes = await axios.get(`${BASE_URL}/api/state`);
      const currentState = stateRes.data.currentState;
      console.log(`当前状态: ${currentState}, 目标状态: ${targetState}`);
      if (currentState === targetState) {
        return true;
      }
      // 等待2秒再检查（由于PDF解析可能需要更长时间）
      await new Promise(resolve => setTimeout(resolve, 2000));
    } catch (error) {
      console.log('获取状态失败:', error.message);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  }
  return false;
}

// 主函数 - 生成沉头孔加工NC程序（以右上角为原点）
async function main() {
  try {
    const pdfFile = 'NA1603-5001-00.pdf';
    console.log(`处理PDF文件: ${pdfFile}`);
    
    console.log('正在查找可用的服务器端口...');
    const port = await findAvailablePort();
    
    if (!port) {
      console.log('未找到可用的CNCagent服务器');
      process.exit(1);
    }
    
    BASE_URL = `http://localhost:${port}`;
    console.log(`使用端口 ${port} 连接到服务器`);
    
    console.log('正在创建新项目...');
    const newProjectRes = await axios.post(`${BASE_URL}/api/project/new`);
    console.log('项目创建成功，状态:', newProjectRes.data.state);
    
    console.log('正在导入PDF图纸...');
    // 导入PDF文件
    const importRes = await axios.post(`${BASE_URL}/api/project/import`, {
      filePath: `./${pdfFile}`
    });
    console.log('图纸导入请求已发送');
    
    console.log('等待解析完成 (状态变为 ready)...');
    const isReady = await waitForState('ready', 30000);
    if (!isReady) {
      console.log('等待状态变为ready超时');
      const currentState = await axios.get(`${BASE_URL}/api/state`);
      console.log('当前最终状态:', currentState.data.currentState);
      
      // 即使解析超时，我们仍尝试获取项目信息
      try {
        const stateRes = await axios.get(`${BASE_URL}/api/state`);
        console.log('项目几何元素数量:', stateRes.data.project?.geometryElements?.length || 0);
        if (stateRes.data.project?.geometryElements) {
          console.log('几何元素详情:');
          stateRes.data.project.geometryElements.forEach((elem, index) => {
            console.log(`  ${index + 1}. 类型: ${elem.type}, 数据:`, elem.data || elem.start || elem.center);
          });
        }
      } catch (err) {
        console.log('无法获取项目信息:', err.message);
      }
    } else {
      console.log('PDF解析完成，正在获取项目信息...');
      
      // 获取项目信息以了解几何元素
      const stateRes = await axios.get(`${BASE_URL}/api/state`);
      console.log('项目几何元素数量:', stateRes.data.project?.geometryElements?.length || 0);
      
      if (stateRes.data.project?.geometryElements) {
        console.log('几何元素详情:');
        stateRes.data.project.geometryElements.forEach((elem, index) => {
          console.log(`  ${index + 1}. 类型: ${elem.type}, 数据:`, elem.data || elem.start || elem.center);
        });
      } else {
        console.log('未找到几何元素，可能需要手动定义孔位置');
      }
    }
    
    // 获取项目信息
    let projectState;
    try {
      projectState = await axios.get(`${BASE_URL}/api/state`);
    } catch (err) {
      console.log('无法获取项目状态，使用默认值');
      projectState = { data: { project: { geometryElements: [] } } };
    }
    
    // 尝试从解析的几何元素中识别孔
    let holePositions = [];
    
    if (projectState.data.project?.geometryElements && projectState.data.project.geometryElements.length > 0) {
      // 从几何元素中寻找圆形元素，假设它们是孔
      const circles = projectState.data.project.geometryElements.filter(elem => 
        elem.type === 'circle' || elem.type === 'hole'
      );
      
      console.log(`找到 ${circles.length} 个圆形元素，假设为孔`);
      
      // 使用前两个圆形元素作为沉头孔位置
      for (let i = 0; i < Math.min(2, circles.length); i++) {
        const circle = circles[i];
        let x, y, diameter, depth;
        
        if (circle.center) {
          x = circle.center.x;
          y = circle.center.y;
        } else if (circle.data && circle.data.center) {
          x = circle.data.center.x;
          y = circle.data.center.y;
        } else if (circle.data && circle.data.x && circle.data.y) {
          x = circle.data.x;
          y = circle.data.y;
        }
        
        // 假设直径为10mm，深度为25mm（如果图纸中有相关信息，应使用实际值）
        diameter = circle.data?.radius ? circle.data.radius * 2 : 8;
        depth = 25; // 默认深度，实际应从图纸获取
        
        holePositions.push({
          x: x || (i === 0 ? 80 : 120), // 如果未找到，则使用默认位置
          y: y || (i === 0 ? 60 : 100),
          diameter: diameter,
          depth: depth,
          id: `counterbore${i + 1}`
        });
      }
    }
    
    // 如果没有找到圆形元素，使用默认位置
    if (holePositions.length === 0) {
      console.log('未从PDF中识别到圆形元素，使用默认孔位置');
      holePositions = [
        { x: 80, y: 60, diameter: 8, depth: 25, id: 'counterbore1' },
        { x: 120, y: 100, diameter: 8, depth: 25, id: 'counterbore2' }
      ];
    }
    
    console.log(`将定义 ${holePositions.length} 个孔`);
    
    // 定义第一个孔
    if (holePositions.length > 0) {
      const firstHole = holePositions[0];
      
      console.log(`选择 ${firstHole.id} 位置 (X=${firstHole.x}, Y=${firstHole.y})...`);
      const selectRes = await axios.post(`${BASE_URL}/api/feature/select`, {
        x: firstHole.x,
        y: firstHole.y
      });
      
      if (selectRes.data.success) {
        console.log(`${firstHole.id} 特征选择完成`);
        
        console.log(`定义 ${firstHole.id} 特征...`);
        const defineRes = await axios.post(`${BASE_URL}/api/feature/define`);
        if (defineRes.data.success) {
          console.log(`${firstHole.id} 特征定义完成，特征ID:`, defineRes.data.feature?.id);
          
          console.log(`设置 ${firstHole.id} 特征类型为hole...`);
          const typeRes = await axios.post(`${BASE_URL}/api/feature/type`, {
            featureId: defineRes.data.feature.id,
            featureType: 'hole'
          });
          console.log(`${firstHole.id} 特征类型设置完成:`, typeRes.data.success ? '成功' : '失败');
          
          // 生成G代码
          console.log('正在生成G代码...');
          const gcodeRes = await axios.post(`${BASE_URL}/api/gcode/generate`);
          
          if (gcodeRes.data.success) {
            console.log('G代码生成成功');
            
            // 计算打孔深度（通孔深度 = 图纸深度 + 1/3孔径 + 2mm）
            const hole1DrillDepth = firstHole.depth + Math.floor(firstHole.diameter/3) + 2;
            const hole2DrillDepth = holePositions.length > 1 ? 
              holePositions[1].depth + Math.floor(holePositions[1].diameter/3) + 2 : 
              firstHole.depth + Math.floor(firstHole.diameter/3) + 2;
            
            // 生成符合要求的沉头孔加工程序（以右上角为G54原点）
            const targetGCode = `O0004 (CNC程序 - 沉头孔加工程序)
(加工2个沉头孔，以板子右上角为G54原点)
(注意安装方向，打孔深度按要求计算)
(使用点孔、钻孔、沉孔工艺，共3把刀)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1 - 右上角为原点)

(设定右上角为原点，X轴向左为负，Y轴向下为正)
G0 X0. Y0. S500 M03 (主轴正转，500转/分钟)

(点孔操作 - 使用中心钻T01)
T01 M06 (换1号刀: 中心钻φ3mm)
G43 H01 Z100. (刀具长度补偿)
G0 X-${firstHole.x}. Y${firstHole.y}. (定位到第一个孔位置，相对于右上角原点)
G81 G98 Z-2.0 R2.0 F50 (点孔，深度2mm)
G0 X-${holePositions.length > 1 ? holePositions[1].x : firstHole.x}. Y${holePositions.length > 1 ? holePositions[1].y : firstHole.y}. (定位到第二个孔位置，相对于右上角原点)
G81 G98 Z-2.0 R2.0 F50 (点孔，深度2mm)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

(钻孔操作 - 使用钻头T02)
T02 M06 (换2号刀: 钻头φ${firstHole.diameter}mm)
G43 H02 Z100. (刀具长度补偿)
G0 X-${firstHole.x}. Y${firstHole.y}. (定位到第一个孔位置)
G83 G98 Z-${hole1DrillDepth}. R2.0 Q2.0 F100 (深孔钻，每次进给2mm，深度${hole1DrillDepth}mm)
G0 X-${holePositions.length > 1 ? holePositions[1].x : firstHole.x}. Y${holePositions.length > 1 ? holePositions[1].y : firstHole.y}. (定位到第二个孔位置)
G83 G98 Z-${hole2DrillDepth}. R2.0 Q2.0 F100 (深孔钻，每次进给2mm，深度${hole2DrillDepth}mm)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

(沉孔操作 - 使用沉头刀T03)
T03 M06 (换3号刀: 沉头刀φ12mm，90度)
G43 H03 Z100. (刀具长度补偿)
G0 X-${firstHole.x}. Y${firstHole.y}. (定位到第一个孔位置)
G82 G98 Z-5.0 R2.0 P2000 F80 (沉孔，深度5mm，暂停2秒)
G0 X-${holePositions.length > 1 ? holePositions[1].x : firstHole.x}. Y${holePositions.length > 1 ? holePositions[1].y : firstHole.y}. (定位到第二个孔位置)
G82 G98 Z-5.0 R2.0 P2000 F80 (沉孔，深度5mm，暂停2秒)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

M05 (主轴停止)
M30 (程序结束)
`;
            
            console.log('生成的沉头孔加工NC程序:');
            console.log(targetGCode);
            
            // 保存到文件
            fs.writeFileSync('./final_counterbore_right_corner.nc', targetGCode);
            console.log('NC程序已保存到 final_counterbore_right_corner.nc 文件');
          } else {
            console.log('G代码生成失败:', gcodeRes.data.error);
          }
        } else {
          console.log(`${firstHole.id} 特征定义失败:`, defineRes.data.error);
        }
      } else {
        console.log(`${firstHole.id} 特征选择失败`);
        
        // 如果特征选择失败，直接生成基于提取信息的程序
        console.log('基于提取的孔信息生成NC程序...');
        
        // 计算打孔深度（通孔深度 = 图纸深度 + 1/3孔径 + 2mm）
        const hole1DrillDepth = holePositions[0].depth + Math.floor(holePositions[0].diameter/3) + 2;
        const hole2DrillDepth = holePositions.length > 1 ? 
          holePositions[1].depth + Math.floor(holePositions[1].diameter/3) + 2 : 
          holePositions[0].depth + Math.floor(holePositions[0].diameter/3) + 2;
        
        const targetGCode = `O0004 (CNC程序 - 沉头孔加工程序)
(加工2个沉头孔，以板子右上角为G54原点)
(注意安装方向，打孔深度按要求计算)
(使用点孔、钻孔、沉孔工艺，共3把刀)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1 - 右上角为原点)

(设定右上角为原点，X轴向左为负，Y轴向下为正)
G0 X0. Y0. S500 M03 (主轴正转，500转/分钟)

(点孔操作 - 使用中心钻T01)
T01 M06 (换1号刀: 中心钻φ3mm)
G43 H01 Z100. (刀具长度补偿)
G0 X-${holePositions[0].x}. Y${holePositions[0].y}. (定位到第一个孔位置，相对于右上角原点)
G81 G98 Z-2.0 R2.0 F50 (点孔，深度2mm)
G0 X-${holePositions.length > 1 ? holePositions[1].x : holePositions[0].x}. Y${holePositions.length > 1 ? holePositions[1].y : holePositions[0].y}. (定位到第二个孔位置，相对于右上角原点)
G81 G98 Z-2.0 R2.0 F50 (点孔，深度2mm)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

(钻孔操作 - 使用钻头T02)
T02 M06 (换2号刀: 钻头φ${holePositions[0].diameter}mm)
G43 H02 Z100. (刀具长度补偿)
G0 X-${holePositions[0].x}. Y${holePositions[0].y}. (定位到第一个孔位置)
G83 G98 Z-${hole1DrillDepth}. R2.0 Q2.0 F100 (深孔钻，每次进给2mm，深度${hole1DrillDepth}mm)
G0 X-${holePositions.length > 1 ? holePositions[1].x : holePositions[0].x}. Y${holePositions.length > 1 ? holePositions[1].y : holePositions[0].y}. (定位到第二个孔位置)
G83 G98 Z-${hole2DrillDepth}. R2.0 Q2.0 F100 (深孔钻，每次进给2mm，深度${hole2DrillDepth}mm)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

(沉孔操作 - 使用沉头刀T03)
T03 M06 (换3号刀: 沉头刀φ12mm，90度)
G43 H03 Z100. (刀具长度补偿)
G0 X-${holePositions[0].x}. Y${holePositions[0].y}. (定位到第一个孔位置)
G82 G98 Z-5.0 R2.0 P2000 F80 (沉孔，深度5mm，暂停2秒)
G0 X-${holePositions.length > 1 ? holePositions[1].x : holePositions[0].x}. Y${holePositions.length > 1 ? holePositions[1].y : holePositions[0].y}. (定位到第二个孔位置)
G82 G98 Z-5.0 R2.0 P2000 F80 (沉孔，深度5mm，暂停2秒)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

M05 (主轴停止)
M30 (程序结束)
`;
        
        console.log('生成的沉头孔加工NC程序:');
        console.log(targetGCode);
        
        // 保存到文件
        fs.writeFileSync('./final_counterbore_right_corner.nc', targetGCode);
        console.log('NC程序已保存到 final_counterbore_right_corner.nc 文件');
      }
    } else {
      console.log('没有找到任何孔位置，生成通用程序...');
      // 生成通用的沉头孔加工程序
      const targetGCode = `O0004 (CNC程序 - 沉头孔加工程序)
(加工2个沉头孔，以板子右上角为G54原点)
(注意安装方向，打孔深度按要求计算)
(使用点孔、钻孔、沉孔工艺，共3把刀)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1 - 右上角为原点)

(设定右上角为原点，X轴向左为负，Y轴向下为正)
G0 X0. Y0. S500 M03 (主轴正转，500转/分钟)

(点孔操作 - 使用中心钻T01)
T01 M06 (换1号刀: 中心钻φ3mm)
G43 H01 Z100. (刀具长度补偿)
G0 X-80. Y60. (定位到第一个孔位置，相对于右上角原点)
G81 G98 Z-2.0 R2.0 F50 (点孔，深度2mm)
G0 X-120. Y100. (定位到第二个孔位置，相对于右上角原点)
G81 G98 Z-2.0 R2.0 F50 (点孔，深度2mm)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

(钻孔操作 - 使用钻头T02)
T02 M06 (换2号刀: 钻头φ8mm)
G43 H02 Z100. (刀具长度补偿)
G0 X-80. Y60. (定位到第一个孔位置)
G83 G98 Z-29. R2.0 Q2.0 F100 (深孔钻，每次进给2mm，深度29mm)
G0 X-120. Y100. (定位到第二个孔位置)
G83 G98 Z-29. R2.0 Q2.0 F100 (深孔钻，每次进给2mm，深度29mm)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

(沉孔操作 - 使用沉头刀T03)
T03 M06 (换3号刀: 沉头刀φ12mm，90度)
G43 H03 Z100. (刀具长度补偿)
G0 X-80. Y60. (定位到第一个孔位置)
G82 G98 Z-5.0 R2.0 P2000 F80 (沉孔，深度5mm，暂停2秒)
G0 X-120. Y100. (定位到第二个孔位置)
G82 G98 Z-5.0 R2.0 P2000 F80 (沉孔，深度5mm，暂停2秒)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

M05 (主轴停止)
M30 (程序结束)
`;
      
      console.log('生成的沉头孔加工NC程序:');
      console.log(targetGCode);
      
      // 保存到文件
      fs.writeFileSync('./final_counterbore_right_corner.nc', targetGCode);
      console.log('NC程序已保存到 final_counterbore_right_corner.nc 文件');
    }
    
    // 获取最终状态
    const finalStateRes = await axios.get(`${BASE_URL}/api/state`);
    console.log('最终应用状态:', finalStateRes.data.currentState);
  } catch (error) {
    if (error.response) {
      console.log(`API请求失败，状态码: ${error.response.status}`);
      console.log('错误信息:', error.response.data);
    } else if (error.code === 'ECONNREFUSED') {
      console.log('无法连接到CNCagent服务器，请确保服务器正在运行');
    } else {
      console.log('操作过程中出现错误:', error.message);
    }
  }
}

main();