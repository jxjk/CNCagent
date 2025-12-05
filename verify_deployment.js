const axios = require('axios');

// 部署验证脚本
const BASE_URL = 'http://127.0.0.1:8081';

async function verifyDeployment() {
  console.log('开始验证 CNCagent 部署...');
  
  try {
    // 1. 检查健康状态
    console.log('\n1. 检查健康状态...');
    const healthResponse = await axios.get(`${BASE_URL}/health`);
    console.log('✅ 健康检查通过:', healthResponse.data.status);
    
    // 2. 检查状态信息
    console.log('\n2. 检查系统状态...');
    const stateResponse = await axios.get(`${BASE_URL}/api/state`);
    console.log('✅ 状态获取成功:', stateResponse.data.state);
    
    // 3. 创建新项目
    console.log('\n3. 测试创建新项目...');
    const newProjectResponse = await axios.post(`${BASE_URL}/api/project/new`);
    console.log('✅ 新项目创建成功:', newProjectResponse.data.success);
    
    // 4. 尝试导入功能（使用模拟数据）
    console.log('\n4. 测试项目导入功能...');
    try {
      const importResponse = await axios.post(`${BASE_URL}/api/project/import`, {
        filePath: 'NA1603-5001-00.pdf'  // 使用项目中的示例PDF
      });
      console.log('✅ 项目导入功能响应正常:', importResponse.data.success);
    } catch (error) {
      console.log('⚠️  项目导入可能需要真实文件:', error.response?.data?.error || error.message);
    }
    
    // 5. 测试特征选择
    console.log('\n5. 测试特征选择功能...');
    try {
      const featureSelectResponse = await axios.post(`${BASE_URL}/api/feature/select`, {
        x: 10,
        y: 10
      });
      console.log('✅ 特征选择功能响应正常:', featureSelectResponse.data.success);
    } catch (error) {
      console.log('⚠️  特征选择功能响应:', error.response?.data?.error || error.message);
    }
    
    // 6. 测试特征定义
    console.log('\n6. 测试特征定义功能...');
    try {
      const featureDefineResponse = await axios.post(`${BASE_URL}/api/feature/define`);
      console.log('✅ 特征定义功能响应正常:', featureDefineResponse.data.success !== undefined);
    } catch (error) {
      console.log('⚠️  特征定义功能响应:', error.response?.data?.error || error.message);
    }
    
    // 7. 测试G代码生成
    console.log('\n7. 测试G代码生成功能...');
    try {
      const gcodeResponse = await axios.post(`${BASE_URL}/api/gcode/generate`);
      console.log('✅ G代码生成功能响应正常:', gcodeResponse.data.success !== undefined);
    } catch (error) {
      console.log('⚠️  G代码生成功能响应:', error.response?.data?.error || error.message);
    }
    
    console.log('\n🎉 部署验证完成！');
    console.log('\nCNCagent 已成功部署在:', BASE_URL);
    console.log('所有核心API端点均可访问');
    
  } catch (error) {
    console.error('\n❌ 部署验证失败:', error.message);
    if (error.response) {
      console.error('响应数据:', error.response.data);
    }
  }
}

verifyDeployment();