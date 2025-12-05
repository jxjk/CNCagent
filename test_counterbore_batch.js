const axios = require('axios');
const fs = require('fs');
const path = require('path');

// 沉头孔批量加工测试 - 验证程序是否能正确识别两个相同沉孔并按最佳实践进行加工
async function testCounterboreBatchProcessing() {
  console.log('=== 沉头孔批量加工功能测试 ===');
  console.log('目标：验证程序是否能正确识别两个相同沉孔特征并按NC编程最佳实践进行加工');
  console.log('验证重点：是否在一次换刀过程中依次加工两个孔，以节省换刀时间');
  
  // 定义可能的端口
  const PORTS = [3000, 3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009];
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
  async function waitForState(targetState, timeout = 30000) {
    const startTime = Date.now();
    while (Date.now() - startTime < timeout) {
      try {
        const stateRes = await axios.get(`${BASE_URL}/api/state`);
        const currentState = stateRes.data.currentState;
        console.log(`当前状态: ${currentState}, 目标状态: ${targetState}`);
        if (currentState === targetState) {
          return true;
        }
        await new Promise(resolve => setTimeout(resolve, 2000)); // 增加等待时间
      } catch (error) {
        console.log('获取状态失败:', error.message);
        await new Promise(resolve => setTimeout(resolve, 2000));
      }
    }
    return false;
  }

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
    
    // 查找PDF文件
    const files = fs.readdirSync('./');
    const pdfFiles = files.filter(file => path.extname(file).toLowerCase() === '.pdf');
    
    if (pdfFiles.length > 0) {
      const pdfFile = pdfFiles[0];
      console.log(`找到PDF文件: ${pdfFile}`);
      
      console.log('正在导入PDF图纸...');
      const importRes = await axios.post(`${BASE_URL}/api/project/import`, {
        filePath: `./${pdfFile}`
      });
      console.log('图纸导入请求已发送，响应:', importRes.data);
      
      console.log('等待解析完成 (状态变为 ready)...');
      const isReady = await waitForState('ready', 45000); // 增加超时时间
      if (!isReady) {
        console.log('等待状态变为ready超时');
        const currentState = await axios.get(`${BASE_URL}/api/state`);
        console.log('当前最终状态:', currentState.data.currentState);
        return;
      }
    } else {
      console.log('当前目录下没有找到PDF文件，将继续测试');
    }
    
    console.log('状态已就绪，开始测试两个相同沉头孔的识别和批量加工...');
    
    // 测试用例1：验证沉头孔特征类型是否可用
    console.log('=== 测试用例1：验证沉头孔特征类型 ===');
    try {
      const featureTypesRes = await axios.get(`${BASE_URL}/api/feature/types`);
      if (featureTypesRes.data && Array.isArray(featureTypesRes.data.types)) {
        const hasCounterbore = featureTypesRes.data.types.includes('counterbore');
        console.log(`沉头孔特征类型是否可用: ${hasCounterbore ? '是' : '否'}`);
        if (!hasCounterbore) {
          console.log('警告：系统中未找到沉头孔特征类型');
        }
      } else {
        console.log('无法获取特征类型列表');
      }
    } catch (e) {
      console.log('获取特征类型失败:', e.message);
    }
    
    // 测试用例2：选择并定义两个相同参数的沉头孔特征
    console.log('=== 测试用例2：选择并定义两个相同参数的沉头孔 ===');
    const holePositions = [
      { x: -20, y: -5, id: 'hole1', description: '第一个目标孔' },
      { x: -80, y: -5, id: 'hole2', description: '第二个目标孔' }
    ];
    
    const features = [];
    let successCount = 0;
    
    for (const pos of holePositions) {
      console.log(`${pos.description} - 选择孔位置 ${pos.id} (X=${pos.x}, Y=${pos.y})...`);
      try {
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
            
            console.log(`设置 ${pos.id} 特征类型为沉头孔...`);
            const typeRes = await axios.post(`${BASE_URL}/api/feature/type`, {
              featureId: defineRes.data.feature.id,
              featureType: 'counterbore'
            });
            console.log(`${pos.id} 特征类型设置完成:`, typeRes.data.success ? '成功' : '失败');
            
            // 设置相同的参数以确保它们会被识别为相同特征
            if (typeRes.data.success) {
              const paramRes = await axios.post(`${BASE_URL}/api/feature/parameters`, {
                featureId: defineRes.data.feature.id,
                parameters: {
                  diameter: 5.5,
                  depth: 14,
                  drawingDepth: 10,
                  counterboreDiameter: 9,
                  counterboreDepth: 5.5,
                  useCounterbore: true
                }
              });
              console.log(`${pos.id} 特征参数设置完成:`, paramRes.data.success ? '成功' : '失败');
              
              features.push(defineRes.data.feature);
              successCount++;
            }
          } else {
            console.log(`${pos.id} 特征定义失败:`, defineRes.data.error);
          }
        } else {
          console.log(`${pos.id} 特征选择失败`);
        }
      } catch (e) {
        console.log(`${pos.id} 特征选择/定义失败:`, e.message);
      }
    }
    
    console.log(`成功定义的特征数量: ${successCount}/2`);
    
    // 测试用例3：生成G代码并验证批量加工
    console.log('=== 测试用例3：生成沉头孔批量加工G代码 ===');
    try {
      const gcodeRes = await axios.post(`${BASE_URL}/api/gcode/generate`);
      
      if (gcodeRes.data.success && gcodeRes.data.gCodeBlocks) {
        console.log('G代码生成成功');
        
        // 检查G代码块
        const gCodeBlocks = gcodeRes.data.gCodeBlocks;
        console.log(`生成的G代码块数量: ${gCodeBlocks.length}`);
        
        let fullGCode = '';
        let gCodeByBlock = [];
        for (const block of gCodeBlocks) {
          let blockCode = '';
          if (block.code && Array.isArray(block.code)) {
            for (const line of block.code) {
              blockCode += line + '\n';
            }
            blockCode += '\n';
          }
          fullGCode += blockCode;
          gCodeByBlock.push({
            id: block.id,
            type: block.type,
            featureType: block.featureType,
            isBatchOperation: block.isBatchOperation,
            batchSize: block.batchSize,
            code: blockCode
          });
        }
        
        // 检查G代码是否包含两个孔的加工指令
        const hasFirstHole = fullGCode.includes('X-20.0') || fullGCode.includes('X-20') || fullGCode.includes('X-20.000');
        const hasSecondHole = fullGCode.includes('X-80.0') || fullGCode.includes('X-80') || fullGCode.includes('X-80.000');
        const hasBothHoles = hasFirstHole && hasSecondHole;
        
        console.log(`是否包含第一个孔(-20, -5)的加工指令: ${hasFirstHole ? '是' : '否'}`);
        console.log(`是否包含第二个孔(-80, -5)的加工指令: ${hasSecondHole ? '是' : '否'}`);
        console.log(`是否包含两个孔的加工指令: ${hasBothHoles ? '是' : '否'}`);
        
        // 检查是否包含沉头孔加工工艺
        const hasCounterboreProcess = fullGCode.toLowerCase().includes('counterbore') || 
                                     fullGCode.toLowerCase().includes('沉孔') ||
                                     fullGCode.includes('T03') || // 沉头刀
                                     fullGCode.includes('G82');  // 沉孔循环
        console.log(`是否包含沉头孔加工工艺: ${hasCounterboreProcess ? '是' : '否'}`);
        
        // 检查是否包含点孔、钻孔、沉孔工艺
        const hasSpotDrilling = fullGCode.toLowerCase().includes('点孔') || fullGCode.includes('T01');
        const hasDrilling = fullGCode.toLowerCase().includes('钻孔') || fullGCode.includes('T02');
        const hasCounterboring = fullGCode.toLowerCase().includes('沉孔') || fullGCode.includes('T03');
        
        console.log(`是否包含点孔工艺: ${hasSpotDrilling ? '是' : '否'}`);
        console.log(`是否包含钻孔工艺: ${hasDrilling ? '是' : '否'}`);
        console.log(`是否包含沉孔工艺: ${hasCounterboring ? '是' : '否'}`);
        
        // 检查批量加工的关键指标
        let batchProcessingDetected = false;
        let totalHoleOperations = 0;
        let toolChanges = 0;
        
        for (const line of fullGCode.split('\n')) {
          if (line.includes('T0') && line.includes('M06')) {
            toolChanges++;
          }
          if (line.includes('G0 X-20.0') || line.includes('G0 X-80.0')) {
            totalHoleOperations++;
          }
        }
        
        console.log(`总换刀次数: ${toolChanges}`);
        console.log(`孔定位操作数: ${totalHoleOperations}`);
        
        // 检查批量加工特征
        let batchBlocks = gCodeByBlock.filter(block => block.isBatchOperation);
        console.log(`检测到的批量操作块数量: ${batchBlocks.length}`);
        
        if (batchBlocks.length > 0) {
          console.log('批量操作详情:');
          batchBlocks.forEach((block, idx) => {
            console.log(`  批量块${idx + 1}: 类型=${block.featureType}, 大小=${block.batchSize}`);
            console.log(`    代码片段: ${block.code.substring(0, 200)}...`);
          });
        }
        
        // 关键验证：是否按NC最佳实践进行批量加工
        // 理想情况下，对于两个相同特征，应该在一次换刀过程中加工两个孔
        const optimalToolChanges = 3; // 点孔T01 + 钻孔T02 + 沉孔T03 = 3次换刀，而不是6次
        const hasOptimalToolChanges = toolChanges <= optimalToolChanges;
        
        console.log(`是否符合NC最佳实践(≤${optimalToolChanges}次换刀): ${hasOptimalToolChanges ? '是' : '否'}`);
        
        // 保存生成的G代码到测试输出文件
        const testOutput = `; 沉头孔批量加工测试输出
; 生成时间: ${new Date().toISOString()}
; 测试结果: ${hasBothHoles && hasCounterboreProcess && hasOptimalToolChanges ? '通过' : '未通过'}
; 成功定义的特征数: ${successCount}/2
; 包含第一个孔: ${hasFirstHole ? '是' : '否'}
; 包含第二个孔: ${hasSecondHole ? '是' : '否'}
; 包含沉头孔工艺: ${hasCounterboreProcess ? '是' : '否'}
; 包含点孔工艺: ${hasSpotDrilling ? '是' : '否'}
; 包含钻孔工艺: ${hasDrilling ? '是' : '否'}
; 包含沉孔工艺: ${hasCounterboring ? '是' : '否'}
; 总换刀次数: ${toolChanges} (最佳实践应≤${optimalToolChanges})
; 批量操作块数量: ${batchBlocks.length}
; 符合NC最佳实践: ${hasOptimalToolChanges ? '是' : '否'}

${fullGCode}`;

        fs.writeFileSync('./test_batch_counterbore.nc', testOutput);
        console.log('测试输出已保存到 test_batch_counterbore.nc');
        
        // 测试结果总结
        console.log('\n=== 测试结果总结 ===');
        console.log(`特征定义成功率: ${successCount}/2 (${successCount * 50}%)`);
        console.log(`G代码生成: ${gcodeRes.data.success ? '成功' : '失败'}`);
        console.log(`双孔识别: ${hasBothHoles ? '成功' : '失败'}`);
        console.log(`沉头孔工艺: ${hasCounterboreProcess ? '包含' : '缺失'}`);
        console.log(`完整工艺流程: ${hasSpotDrilling && hasDrilling && hasCounterboring ? '完整' : '不完整'}`);
        console.log(`批量加工检测: ${batchBlocks.length > 0 ? '检测到' : '未检测到'}`);
        console.log(`NC最佳实践遵循: ${hasOptimalToolChanges ? '是' : '否'}`);
        
        const overallResult = successCount >= 1 && hasBothHoles && hasCounterboreProcess && hasOptimalToolChanges;
        console.log(`总体测试结果: ${overallResult ? '通过' : '未通过'}`);
        
        return {
          successCount,
          hasBothHoles,
          hasCounterboreProcess,
          hasSpotDrilling,
          hasDrilling,
          hasCounterboring,
          toolChanges,
          optimalToolChanges,
          hasOptimalToolChanges,
          batchBlocksCount: batchBlocks.length,
          overallResult
        };
      } else {
        console.log('G代码生成失败:', gcodeRes.data.error);
        
        // 生成标准测试输出
        const testOutput = `; 沉头孔批量加工测试输出
; 生成时间: ${new Date().toISOString()}
; 测试结果: 未通过 - G代码生成失败
; 成功定义的特征数: ${successCount}/2
; G代码生成状态: 失败

G代码生成失败，详细错误信息: ${gcodeRes.data.error || '未知错误'}`;

        fs.writeFileSync('./test_batch_counterbore.nc', testOutput);
        console.log('测试输出已保存到 test_batch_counterbore.nc');
        
        return {
          successCount,
          hasBothHoles: false,
          hasCounterboreProcess: false,
          hasSpotDrilling: false,
          hasDrilling: false,
          hasCounterboring: false,
          toolChanges: 0,
          optimalToolChanges: 3,
          hasOptimalToolChanges: false,
          batchBlocksCount: 0,
          overallResult: false
        };
      }
    } catch (e) {
      console.log('G代码生成过程中出现错误:', e.message);
      
      // 生成标准测试输出
      const testOutput = `; 沉头孔批量加工测试输出
; 生成时间: ${new Date().toISOString()}
; 测试结果: 未通过 - G代码生成异常
; 成功定义的特征数: ${successCount}/2
; 异常信息: ${e.message}`;

      fs.writeFileSync('./test_batch_counterbore.nc', testOutput);
      console.log('测试输出已保存到 test_batch_counterbore.nc');
      
      return {
        successCount,
        hasBothHoles: false,
        hasCounterboreProcess: false,
        hasSpotDrilling: false,
        hasDrilling: false,
        hasCounterboring: false,
        toolChanges: 0,
        optimalToolChanges: 3,
        hasOptimalToolChanges: false,
        batchBlocksCount: 0,
        overallResult: false
      };
    }
  } catch (error) {
    console.log('测试过程中出现错误:', error.message);
    if (error.response) {
      console.log(`API请求失败，状态码: ${error.response.status}`);
      console.log('错误信息:', error.response.data);
    } else if (error.code === 'ECONNRESET' || error.code === 'ECONNABORTED') {
      console.log('连接被重置或中止，可能是服务器处理时间过长');
    } else if (error.code === 'ECONNREFUSED') {
      console.log('无法连接到CNCagent服务器，请确保服务器正在运行');
    }
    
    return {
      successCount: 0,
      hasBothHoles: false,
      hasCounterboreProcess: false,
      hasSpotDrilling: false,
      hasDrilling: false,
      hasCounterboring: false,
      toolChanges: 0,
      optimalToolChanges: 3,
      hasOptimalToolChanges: false,
      batchBlocksCount: 0,
      overallResult: false
    };
  }
}

// 执行测试
testCounterboreBatchProcessing()
  .then(results => {
    console.log('\n=== 最终测试报告 ===');
    console.log(`测试执行时间: ${new Date().toISOString()}`);
    console.log(`特征定义成功率: ${results.successCount}/2`);
    console.log(`双孔识别: ${results.hasBothHoles ? '通过' : '失败'}`);
    console.log(`沉头孔工艺: ${results.hasCounterboreProcess ? '通过' : '失败'}`);
    console.log(`点孔工艺: ${results.hasSpotDrilling ? '通过' : '失败'}`);
    console.log(`钻孔工艺: ${results.hasDrilling ? '通过' : '失败'}`);
    console.log(`沉孔工艺: ${results.hasCounterboring ? '通过' : '失败'}`);
    console.log(`批量加工检测: ${results.batchBlocksCount > 0 ? '通过' : '失败'}`);
    console.log(`NC最佳实践遵循: ${results.hasOptimalToolChanges ? '通过' : '失败'}`);
    console.log(`总体结果: ${results.overallResult ? '通过' : '未通过'}`);
    
    // 根据测试结果写入测试报告
    const report = `# 沉头孔批量加工功能测试报告

## 测试概要
- 测试时间: ${new Date().toISOString()}
- 测试目标: 验证CNCagent程序是否能正确识别和批量处理两个相同沉头孔
- 测试位置: 第一个孔(X-20, Y-5)，第二个孔(X-80, Y-5)
- NC最佳实践要求: 在一次换刀过程中依次加工两个孔，以节省换刀时间

## 测试结果
- 特征定义成功率: ${results.successCount}/2
- 双孔识别: ${results.hasBothHoles ? '通过' : '失败'}
- 沉头孔工艺: ${results.hasCounterboreProcess ? '通过' : '失败'}
- 点孔工艺: ${results.hasSpotDrilling ? '通过' : '失败'}
- 钻孔工艺: ${results.hasDrilling ? '通过' : '失败'}
- 沉孔工艺: ${results.hasCounterboring ? '通过' : '失败'}
- 批量加工检测: ${results.batchBlocksCount > 0 ? '通过' : '失败'}
- NC最佳实践遵循: ${results.hasOptimalToolChanges ? '通过' : '失败'}
- 总体结果: ${results.overallResult ? '通过' : '未通过'}

## 详细分析
- 总换刀次数: ${results.toolChanges} (最佳实践应≤${results.optimalToolChanges})
- 检测到批量操作块: ${results.batchBlocksCount} 个
- 是否符合NC最佳实践: ${results.hasOptimalToolChanges ? '是' : '否'}

## 测试结论
${results.overallResult ? 
'程序能够正确识别两个相同沉头孔特征，并按照NC编程最佳实践，在一次换刀过程中依次加工两个孔，有效节省了换刀时间。' : 
results.hasBothHoles && !results.hasOptimalToolChanges ? 
'程序能够正确识别两个相同沉头孔特征，但未按照NC编程最佳实践进行批量加工，可能存在不必要的换刀操作。' :
'程序在识别或处理两个相同沉头孔方面存在问题，需要进一步修复。'}

## 详细说明
1. 特征定义成功率: ${results.successCount >= 2 ? '高' : results.successCount >= 1 ? '中等' : '低'}
2. 双孔识别能力: ${results.hasBothHoles ? '具备' : '缺失'}
3. 沉头孔加工能力: ${results.hasCounterboreProcess ? '具备' : '缺失'}
4. 工艺完整性: ${results.hasSpotDrilling && results.hasDrilling && results.hasCounterboring ? '完整' : '不完整'}
5. 批量加工能力: ${results.batchBlocksCount > 0 ? '具备' : '缺失'}
6. NC最佳实践遵循: ${results.hasOptimalToolChanges ? '符合' : '不符合'}

## 建议
${results.overallResult ? 
'当前修复已成功解决双沉头孔识别和批量处理问题，符合NC编程最佳实践，可以投入生产使用。' : 
'需要进一步检查和修复沉头孔识别和批量处理逻辑，确保能够正确识别相同特征并按最佳实践进行加工，减少不必要的换刀操作。'}
`;

    fs.writeFileSync('./FINAL_TEST_REPORT.md', report);
    console.log('详细测试报告已保存到 FINAL_TEST_REPORT.md');
    
    // 更新todo状态
    console.log('\n=== 更新测试状态 ===');
    console.log('已完成沉头孔批量加工功能测试');
  })
  .catch(error => {
    console.error('测试执行失败:', error);
  });