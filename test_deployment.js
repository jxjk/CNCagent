const axios = require('axios');

async function testCNCagent() {
  const baseURL = 'http://localhost:3000';
  
  console.log('开始测试CNCagent OCR识别和G代码生成功能...');
  
  try {
    // 1. 测试获取状态
    console.log('\n1. 测试获取当前状态...');
    let response = await axios.get(`${baseURL}/api/state`);
    console.log('当前状态:', response.data);
    
    // 2. 创建新项目
    console.log('\n2. 创建新项目...');
    response = await axios.post(`${baseURL}/api/project/new`);
    console.log('创建项目结果:', response.data);
    
    // 3. 模拟导入PDF文件（使用已存在的PDF测试）
    console.log('\n3. 导入图纸文件测试...');
    try {
      response = await axios.post(`${baseURL}/api/project/import`, {
        filePath: './NA1603-5001-00.pdf'  // 使用项目中已存在的PDF文件
      });
      console.log('导入结果:', response.data);
    } catch (error) {
      console.log('导入PDF失败，可能是文件不存在或解析错误:', error.response?.data || error.message);
    }
    
    // 4. 测试选择特征
    console.log('\n4. 测试选择特征...');
    try {
      response = await axios.post(`${baseURL}/api/feature/select`, {
        x: 100,  // 测试坐标
        y: 100
      });
      console.log('选择特征结果:', response.data);
    } catch (error) {
      console.log('选择特征失败:', error.response?.data || error.message);
    }
    
    // 5. 测试定义特征
    console.log('\n5. 测试定义特征...');
    try {
      response = await axios.post(`${baseURL}/api/feature/define`);
      console.log('定义特征结果:', response.data);
    } catch (error) {
      console.log('定义特征失败:', error.response?.data || error.message);
    }
    
    // 6. 模拟添加一个孔特征来测试钻孔G代码生成
    console.log('\n6. 测试G代码生成...');
    try {
      // 获取当前状态，看看是否可以生成G代码
      response = await axios.get(`${baseURL}/api/state`);
      console.log('生成G代码前的状态:', response.data);
      
      response = await axios.post(`${baseURL}/api/gcode/generate`);
      console.log('G代码生成结果:', response.data);
      
      if (response.data.success && response.data.gCodeBlocks) {
        console.log('\nG代码生成成功!');
        
        // 查看生成的G代码是否包含钻孔固定循环
        console.log('\n查看G代码块:');
        for (const block of response.data.gCodeBlocks) {
          console.log(`\n区块类型: ${block.type}, 特征类型: ${block.featureType}`);
          if (Array.isArray(block.code)) {
            console.log('G代码片段:');
            for (let i = 0; i < Math.min(block.code.length, 10); i++) {  // 只显示前10行
              console.log(`  ${block.code[i]}`);
            }
            if (block.code.length > 10) {
              console.log(`  ... 还有 ${block.code.length - 10} 行`);
            }
            
            // 检查是否包含钻孔固定循环
            const hasDrillingCycle = block.code.some(line => 
              line.includes('G81') || line.includes('G82') || line.includes('G83')
            );
            if (hasDrillingCycle) {
              console.log('✓ 检测到钻孔固定循环 (G81/G82/G83)');
            } else {
              console.log('未检测到钻孔固定循环');
            }
          }
        }
      }
    } catch (error) {
      console.log('G代码生成失败:', error.response?.data || error.message);
    }
    
    console.log('\n测试完成!');
    
  } catch (error) {
    console.error('测试过程中出现错误:', error.message);
  }
}

// 运行测试
testCNCagent();