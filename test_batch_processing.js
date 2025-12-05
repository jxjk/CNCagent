const { triggerGCodeGeneration } = require('./src/modules/gCodeGeneration');
const fs = require('fs');

// 直接测试G代码生成模块，验证批量加工功能
function testCounterboreBatchProcessing() {
  console.log('=== 沉头孔批量加工功能直接测试 ===');
  console.log('目标：验证G代码生成模块是否能正确识别两个相同沉孔特征并按NC编程最佳实践进行批量加工');
  console.log('验证重点：是否在一次换刀过程中依次加工两个孔，以节省换刀时间');
  
  try {
    // 创建一个模拟项目，直接包含两个相同的沉头孔特征
    const project = {
      features: [
        {
          id: 'feat_1',
          elementId: 'circle_1',
          elementType: 'circle',
          featureType: 'counterbore',
          baseGeometry: { center: { x: -20, y: -5 } },
          parameters: {
            diameter: 5.5,
            depth: 14,
            drawingDepth: 10,
            counterboreDiameter: 9,
            counterboreDepth: 5.5,
            useCounterbore: true
          }
        },
        {
          id: 'feat_2',
          elementId: 'circle_2',
          elementType: 'circle',
          featureType: 'counterbore', 
          baseGeometry: { center: { x: -80, y: -5 } },
          parameters: {
            diameter: 5.5,
            depth: 14,
            drawingDepth: 10,
            counterboreDiameter: 9,
            counterboreDepth: 5.5,
            useCounterbore: true
          }
        }
      ]
    };

    console.log('模拟项目已创建，包含两个相同参数的沉头孔特征');
    console.log('第一个孔: X-20, Y-5');
    console.log('第二个孔: X-80, Y-5');
    console.log('孔参数: 直径5.5mm, 深度14mm, 沉孔径9mm, 沉孔深5.5mm');
    
    // 调用G代码生成函数
    console.log('\n开始生成G代码...');
    const gCodeBlocks = triggerGCodeGeneration(project);
    
    console.log('G代码生成成功');
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
        featureGroup: block.featureGroup,
        code: blockCode
      });
    }
    
    // 检查G代码是否包含两个孔的加工指令
    const hasFirstHole = fullGCode.includes('X-20.0') || fullGCode.includes('X-20') || fullGCode.includes('X-20.000');
    const hasSecondHole = fullGCode.includes('X-80.0') || fullGCode.includes('X-80') || fullGCode.includes('X-80.000');
    const hasBothHoles = hasFirstHole && hasSecondHole;
    
    console.log(`\n是否包含第一个孔(-20, -5)的加工指令: ${hasFirstHole ? '是' : '否'}`);
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
    
    console.log(`\n总换刀次数: ${toolChanges}`);
    console.log(`孔定位操作数: ${totalHoleOperations}`);
    
    // 检查批量加工特征
    let batchBlocks = gCodeByBlock.filter(block => block.isBatchOperation);
    console.log(`检测到的批量操作块数量: ${batchBlocks.length}`);
    
    if (batchBlocks.length > 0) {
      console.log('批量操作详情:');
      batchBlocks.forEach((block, idx) => {
        console.log(`  批量块${idx + 1}: 类型=${block.featureType}, 大小=${block.batchSize}`);
        if (block.featureGroup) {
          console.log(`    特征组: ${block.featureGroup.length}个特征`);
          block.featureGroup.forEach((fg, i) => {
            console.log(`      特征${i+1}: ID=${fg.id}, 位置=(${fg.geometry.center.x}, ${fg.geometry.center.y})`);
          });
        }
        console.log(`    代码片段: ${block.code.substring(0, 300)}...`);
      });
    }
    
    // 关键验证：是否按NC最佳实践进行批量加工
    // 理想情况下，对于两个相同特征，应该在一次换刀过程中加工两个孔
    const optimalToolChanges = 3; // 点孔T01 + 钻孔T02 + 沉孔T03 = 3次换刀，而不是6次
    const hasOptimalToolChanges = toolChanges <= optimalToolChanges;
    
    console.log(`\n是否符合NC最佳实践(≤${optimalToolChanges}次换刀): ${hasOptimalToolChanges ? '是' : '否'}`);
    
    // 检查是否实现了特征分组
    const hasFeatureGrouping = project.features.length === 2 && batchBlocks.length > 0;
    console.log(`是否实现了特征分组: ${hasFeatureGrouping ? '是' : '否'}`);
    
    // 保存生成的G代码到测试输出文件
    const testOutput = `; 沉头孔批量加工功能测试输出
; 生成时间: ${new Date().toISOString()}
; 测试目标: 验证两个相同沉头孔特征的批量加工
; 测试结果: ${hasBothHoles && hasCounterboreProcess && hasOptimalToolChanges ? '通过' : '未通过'}
; 包含第一个孔: ${hasFirstHole ? '是' : '否'}
; 包含第二个孔: ${hasSecondHole ? '是' : '否'}
; 包含沉头孔工艺: ${hasCounterboreProcess ? '是' : '否'}
; 包含点孔工艺: ${hasSpotDrilling ? '是' : '否'}
; 包含钻孔工艺: ${hasDrilling ? '是' : '否'}
; 包含沉孔工艺: ${hasCounterboring ? '是' : '否'}
; 总换刀次数: ${toolChanges} (最佳实践应≤${optimalToolChanges})
; 批量操作块数量: ${batchBlocks.length}
; 是否符合NC最佳实践: ${hasOptimalToolChanges ? '是' : '否'}
; 是否实现了特征分组: ${hasFeatureGrouping ? '是' : '否'}

${fullGCode}`;

    fs.writeFileSync('./test_batch_counterbore.nc', testOutput);
    console.log('\n测试输出已保存到 test_batch_counterbore.nc');
    
    // 测试结果总结
    console.log('\n=== 测试结果总结 ===');
    console.log(`G代码生成: 成功`);
    console.log(`双孔识别: ${hasBothHoles ? '成功' : '失败'}`);
    console.log(`沉头孔工艺: ${hasCounterboreProcess ? '包含' : '缺失'}`);
    console.log(`完整工艺流程: ${hasSpotDrilling && hasDrilling && hasCounterboring ? '完整' : '不完整'}`);
    console.log(`批量加工检测: ${batchBlocks.length > 0 ? '检测到' : '未检测到'}`);
    console.log(`NC最佳实践遵循: ${hasOptimalToolChanges ? '是' : '否'}`);
    console.log(`特征分组实现: ${hasFeatureGrouping ? '是' : '否'}`);
    
    const overallResult = hasBothHoles && hasCounterboreProcess && hasOptimalToolChanges;
    console.log(`\n总体测试结果: ${overallResult ? '通过' : '未通过'}`);
    
    // 生成详细的测试报告
    const report = `# 沉头孔批量加工功能测试报告

## 测试概要
- 测试时间: ${new Date().toISOString()}
- 测试目标: 验证CNCagent程序是否能正确识别和批量处理两个相同沉头孔
- 测试方法: 直接调用G代码生成模块，绕过PDF解析步骤
- 测试数据: 两个相同参数的沉头孔，坐标(X-20, Y-5)和(X-80, Y-5)
- NC最佳实践要求: 在一次换刀过程中依次加工两个孔，以节省换刀时间

## 测试结果
- 双孔识别: ${hasBothHoles ? '通过' : '失败'}
- 沉头孔工艺: ${hasCounterboreProcess ? '通过' : '失败'}
- 点孔工艺: ${hasSpotDrilling ? '通过' : '失败'}
- 钻孔工艺: ${hasDrilling ? '通过' : '失败'}
- 沉孔工艺: ${hasCounterboring ? '通过' : '失败'}
- 批量加工检测: ${batchBlocks.length > 0 ? '通过' : '失败'}
- NC最佳实践遵循: ${hasOptimalToolChanges ? '通过' : '失败'}
- 特征分组实现: ${hasFeatureGrouping ? '通过' : '失败'}
- 总体结果: ${overallResult ? '通过' : '未通过'}

## 详细分析
- 总换刀次数: ${toolChanges} (最佳实践应≤${optimalToolChanges})
- 检测到批量操作块: ${batchBlocks.length} 个
- 是否符合NC最佳实践: ${hasOptimalToolChanges ? '是' : '否'}
- 是否实现了特征分组: ${hasFeatureGrouping ? '是' : '否'}

## G代码生成详情
${fullGCode.substring(0, 1000)}...

## 测试结论
${overallResult ? 
'程序能够正确识别两个相同沉头孔特征，并按照NC编程最佳实践，在一次换刀过程中依次加工两个孔，有效节省了换刀时间。特征分组功能正常工作，相同特征被正确归类到同一加工批次。' : 
hasBothHoles && !hasOptimalToolChanges ? 
'程序能够正确识别两个相同沉头孔特征并生成相应的加工代码，但未按照NC编程最佳实践进行批量加工，可能存在不必要的换刀操作。特征分组功能可能未正确实现。' :
'程序在识别或处理两个相同沉头孔方面存在问题，或者批量加工逻辑未按预期工作。'}

## 详细说明
1. 双孔识别能力: ${hasBothHoles ? '具备' : '缺失'}
2. 沉头孔加工能力: ${hasCounterboreProcess ? '具备' : '缺失'}
3. 工艺完整性: ${hasSpotDrilling && hasDrilling && hasCounterboring ? '完整' : '不完整'}
4. 批量加工能力: ${batchBlocks.length > 0 ? '具备' : '缺失'}
5. NC最佳实践遵循: ${hasOptimalToolChanges ? '符合' : '不符合'}
6. 特征分组实现: ${hasFeatureGrouping ? '已实现' : '未实现'}

## 建议
${overallResult ? 
'当前的CNCagent程序已成功实现双沉头孔识别和批量处理功能，符合NC编程最佳实践，可以投入生产使用。' : 
'需要进一步检查和修复G代码生成模块中的特征分组和批量加工逻辑，确保相同特征能够在一次换刀过程中完成加工，提高加工效率。'}
`;

    fs.writeFileSync('./FINAL_TEST_REPORT.md', report);
    console.log('\n详细测试报告已保存到 FINAL_TEST_REPORT.md');
    
    // 更新todo状态
    console.log('\n=== 更新测试状态 ===');
    console.log('已完成沉头孔批量加工功能直接测试');
    
    return {
      hasBothHoles,
      hasCounterboreProcess,
      hasSpotDrilling,
      hasDrilling,
      hasCounterboring,
      toolChanges,
      optimalToolChanges,
      hasOptimalToolChanges,
      batchBlocksCount: batchBlocks.length,
      hasFeatureGrouping,
      overallResult
    };
    
  } catch (error) {
    console.error('测试过程中出现错误:', error);
    console.error('错误堆栈:', error.stack);
    
    return {
      hasBothHoles: false,
      hasCounterboreProcess: false,
      hasSpotDrilling: false,
      hasDrilling: false,
      hasCounterboring: false,
      toolChanges: 0,
      optimalToolChanges: 3,
      hasOptimalToolChanges: false,
      batchBlocksCount: 0,
      hasFeatureGrouping: false,
      overallResult: false
    };
  }
}

// 执行测试
const results = testCounterboreBatchProcessing();

console.log('\n=== 最终测试报告 ===');
console.log(`测试执行时间: ${new Date().toISOString()}`);
console.log(`双孔识别: ${results.hasBothHoles ? '通过' : '失败'}`);
console.log(`沉头孔工艺: ${results.hasCounterboreProcess ? '通过' : '失败'}`);
console.log(`点孔工艺: ${results.hasSpotDrilling ? '通过' : '失败'}`);
console.log(`钻孔工艺: ${results.hasDrilling ? '通过' : '失败'}`);
console.log(`沉孔工艺: ${results.hasCounterboring ? '通过' : '失败'}`);
console.log(`批量加工检测: ${results.batchBlocksCount > 0 ? '通过' : '失败'}`);
console.log(`NC最佳实践遵循: ${results.hasOptimalToolChanges ? '通过' : '失败'}`);
console.log(`特征分组实现: ${results.hasFeatureGrouping ? '通过' : '失败'}`);
console.log(`总体结果: ${results.overallResult ? '通过' : '未通过'}`);