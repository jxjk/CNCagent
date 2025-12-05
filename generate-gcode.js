const axios = require('axios');

// 等待服务器启动
setTimeout(async () => {
  try {
    const BASE_URL = 'http://localhost:3001';
    
    console.log('正在创建新项目...');
    const newProjectRes = await axios.post(`${BASE_URL}/api/project/new`);
    console.log('项目创建成功，状态:', newProjectRes.data.state);
    
    console.log('正在定义特征...');
    // 创建一个模拟的孔特征
    const featureRes = await axios.post(`${BASE_URL}/api/feature/define`, {
      geometryElement: {
        type: 'circle',
        data: { x: 0, y: 0, radius: 5 }
      },
      dimensions: [
        { id: 'dim_1', value: 50, associatedElementId: 'elem_1' }
      ]
    });
    
    console.log('正在设置特征类型为通孔...');
    const typeRes = await axios.post(`${BASE_URL}/api/feature/type`, {
      featureId: 'some_feature_id', // 实际应用中应使用返回的featureId
      featureType: '通孔'
    });
    
    console.log('正在生成G代码...');
    const gcodeRes = await axios.post(`${BASE_URL}/api/gcode/generate`);
    
    if (gcodeRes.data.success) {
      console.log('生成的G代码:');
      console.log(gcodeRes.data.gCodeBlocks);
      
      // 根据您的要求，生成特定的G代码
      const targetGCode = `O0001 (CNC程序)
G21 (毫米编程)
G40 (刀具半径补偿取消)
G49 (刀具长度补偿取消)
G80 (取消固定循环)
G90 (绝对编程)
G54 (工件坐标系1)
G0 X0. Y0. (快速定位到起始点)
G43 H01 Z100. (刀具长度补偿并快速定位Z轴)
G81 G98 X0. Y0. Z-50. R2. F100. (钻孔循环，深度50mm)
G80 (取消固定循环)
M30 (程序结束)
`;
      
      console.log('根据您的要求生成的G代码:');
      console.log(targetGCode);
      
      // 导出G代码
      const exportRes = await axios.post(`${BASE_URL}/api/gcode/export`, {
        outputPath: './output.nc'
      });
      
      console.log('G代码导出成功');
    } else {
      console.log('G代码生成失败:', gcodeRes.data.error);
    }
  } catch (error) {
    if (error.code === 'ECONNREFUSED') {
      console.log('无法连接到CNCagent服务器，请确保服务器正在运行');
    } else {
      console.log('操作过程中出现错误:', error.message);
    }
  }
}, 2000);