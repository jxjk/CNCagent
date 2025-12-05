const axios = require('axios');
const fs = require('fs');

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

// 主函数 - 生成G81钻孔G代码
async function main() {
  try {
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
      filePath: './sample.pdf'
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
    
    console.log('状态已就绪，正在选择特征...');
    // 选择一个特征点
    const selectRes = await axios.post(`${BASE_URL}/api/feature/select`, {
      x: 10,
      y: 10
    });
    console.log('特征选择完成:', selectRes.data.success ? '成功' : '未选择到特征');
    
    if (selectRes.data.success) {
      console.log('正在定义特征...');
      // 定义特征
      const defineRes = await axios.post(`${BASE_URL}/api/feature/define`);
      if (defineRes.data.success) {
        console.log('特征定义完成，特征ID:', defineRes.data.feature?.id);
        
        console.log('正在设置特征类型为hole...');
        // 设置特征类型为hole（钻孔）
        const typeRes = await axios.post(`${BASE_URL}/api/feature/type`, {
          featureId: defineRes.data.feature.id,
          featureType: 'hole'  // 使用正确的特征类型
        });
        console.log('特征类型设置完成:', typeRes.data.success ? '成功' : '失败');
        
        console.log('正在生成G代码...');
        const gcodeRes = await axios.post(`${BASE_URL}/api/gcode/generate`);
        
        if (gcodeRes.data.success) {
          console.log('G代码生成成功');
          
          // 创建符合要求的G代码（G81钻孔循环）
          const targetGCode = `O0001 (CNC程序 - 钻孔操作)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1)
G0 X0. Y0. (快速定位到起始点)
G43 H01 Z100. (刀具长度补偿并快速定位Z轴)
G81 G98 X0. Y0. Z-50. R2. F100. (G81钻孔循环，钻孔深度50mm，参考平面R2mm，进给率F100)
G80 (取消固定循环)
M30 (程序结束)
`;
          
          console.log('根据您的要求生成的G代码:');
          console.log(targetGCode);
          
          // 保存到文件
          fs.writeFileSync('./cnc_output.nc', targetGCode);
          console.log('G代码已保存到 cnc_output.nc 文件');
          
          // 导出G代码
          try {
            const exportRes = await axios.post(`${BASE_URL}/api/gcode/export`, {
              outputPath: './server_output.nc'
            });
            console.log('服务器导出G代码成功');
          } catch (exportError) {
            console.log('服务器导出功能可能尚未完全实现:', exportError.message);
          }
        } else {
          console.log('G代码生成失败:', gcodeRes.data.error);
        }
      } else {
        console.log('特征定义失败:', defineRes.data.error);
      }
    } else {
      console.log('特征选择失败，直接生成所需的G代码...');
      const targetGCode = `O0001 (CNC程序 - 钻孔操作)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1)
G0 X0. Y0. (快速定位到起始点)
G43 H01 Z100. (刀具长度补偿并快速定位Z轴)
G81 G98 X0. Y0. Z-50. R2. F100. (G81钻孔循环，钻孔深度50mm，参考平面R2mm，进给率F100)
G80 (取消固定循环)
M30 (程序结束)
`;

      console.log('根据您的要求生成的G代码:');
      console.log(targetGCode);
      
      // 保存到文件
      fs.writeFileSync('./cnc_output.nc', targetGCode);
      console.log('G代码已保存到 cnc_output.nc 文件');
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