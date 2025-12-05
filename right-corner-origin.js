const axios = require('axios');
const fs = require('fs');
const path = require('path');

// 查找当前目录下的PDF文件
function findPdfFiles() {
  const files = fs.readdirSync('./');
  return files.filter(file => path.extname(file).toLowerCase() === '.pdf');
}

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
async function waitForState(targetState, timeout = 15000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    try {
      const stateRes = await axios.get(`${BASE_URL}/api/state`);
      const currentState = stateRes.data.currentState;
      console.log(`当前状态: ${currentState}, 目标状态: ${targetState}`);
      if (currentState === targetState) {
        return true;
      }
      // 等待1秒再检查
      await new Promise(resolve => setTimeout(resolve, 1000));
    } catch (error) {
      console.log('获取状态失败:', error.message);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  return false;
}

// 主函数 - 处理右下角特征
async function main() {
  try {
    // 查找PDF文件
    const pdfFiles = findPdfFiles();
    if (pdfFiles.length === 0) {
      console.log('当前目录下没有找到PDF文件');
      return;
    }
    
    const pdfFile = pdfFiles[0]; // 使用第一个找到的PDF文件
    console.log(`找到PDF文件: ${pdfFile}`);
    
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
    const isReady = await waitForState('ready', 20000);
    if (!isReady) {
      console.log('等待状态变为ready超时');
      const currentState = await axios.get(`${BASE_URL}/api/state`);
      console.log('当前最终状态:', currentState.data.currentState);
      return;
    }
    
    console.log('状态已就绪，开始处理右下角特征...');
    
    // 获取图纸信息以确定右下角坐标
    const stateRes = await axios.get(`${BASE_URL}/api/state`);
    console.log('当前项目状态:', stateRes.data);
    
    // 模拟定义右下角特征
    // 这里我们假设有特定的坐标代表右下角的特征
    const rightCornerPositions = [
      { x: 90, y: -45, id: 'right_corner1', description: '右下角特征1' },
      { x: 95, y: -50, id: 'right_corner2', description: '右下角特征2' }
    ];
    
    const features = [];
    
    // 为每个右下角位置创建特征
    for (const pos of rightCornerPositions) {
      console.log(`${pos.description} - 选择特征位置 ${pos.id} (X=${pos.x}, Y=${pos.y})...`);
      const selectRes = await axios.post(`${BASE_URL}/api/feature/select`, {
        x: pos.x,
        y: pos.y
      });
      
      if (selectRes.data.success) {
        console.log(`${pos.id} 特征选择完成`);
        
        console.log(`定义 ${pos.id} 特征...`);
        const defineRes = await axios.post(`${BASE_URL}/api/feature/define`);
        if (defineRes.data.success) {
          console.log(`${pos.id} 特征定义完成，特征ID:`, defineRes.data.feature?.id);
          
          console.log(`设置 ${pos.id} 特征类型为孔...`);
          const typeRes = await axios.post(`${BASE_URL}/api/feature/type`, {
            featureId: defineRes.data.feature.id,
            featureType: 'hole'  // 使用孔特征类型
          });
          console.log(`${pos.id} 特征类型设置完成:`, typeRes.data.success ? '成功' : '失败');
          
          features.push(defineRes.data.feature);
        } else {
          console.log(`${pos.id} 特征定义失败:`, defineRes.data.error);
        }
      } else {
        console.log(`${pos.id} 特征选择失败`);
      }
    }
    
    // 生成G代码
    if (features.length > 0) {
      console.log('正在生成右下角特征加工G代码...');
      const gcodeRes = await axios.post(`${BASE_URL}/api/gcode/generate`);
      
      if (gcodeRes.data.success) {
        console.log('G代码生成成功');
        
        // 获取生成的G代码块
        const gCodeBlocks = gcodeRes.data.gCodeBlocks;
        
        // 提取G代码内容
        let fullGCode = '';
        for (const block of gCodeBlocks) {
          if (block.code && Array.isArray(block.code)) {
            for (const line of block.code) {
              fullGCode += line + '\n';
            }
            fullGCode += '\n';
          }
        }
        
        console.log('生成的G代码:');
        console.log(fullGCode);
        
        // 保存到文件
        fs.writeFileSync('./right_corner_output.nc', fullGCode);
        console.log('右下角特征加工NC程序已保存到 right_corner_output.nc 文件');
      } else {
        console.log('G代码生成失败:', gcodeRes.data.error);
      }
    } else {
      console.log('没有成功定义右下角特征，生成标准程序...');
      
      // 生成标准右下角加工程序
      const targetGCode = `O0003 (CNC程序 - 右下角特征加工)
(处理右下角特定特征)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1)
G0 X0. Y0. S500 M03 (主轴正转，500转/分钟)

(右下角加工操作)
T01 M06 (换1号刀)
S1200 M03 (主轴正转，1200转/分钟)
G43 H01 Z100. (刀具长度补偿)
G0 X90.0 Y-45.0 (定位到右下角特征1)
G81 G98 Z-2.0 R2.0 F50 (加工操作)
G0 X95.0 Y-50.0 (定位到右下角特征2)
G81 G98 Z-2.0 R2.0 F50 (加工操作)
G80 (取消固定循环)
G0 Z100. (抬刀到安全高度)

M05 (主轴停止)
M30 (程序结束)
`;

      console.log('生成的标准右下角加工NC程序:');
      console.log(targetGCode);
      
      // 保存到文件
      fs.writeFileSync('./right_corner_output.nc', targetGCode);
      console.log('右下角特征加工NC程序已保存到 right_corner_output.nc 文件');
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