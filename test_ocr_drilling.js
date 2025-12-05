const fs = require('fs');
const path = require('path');

// 测试OCR识别和钻孔固定循环G代码生成
async function testOCRAndDrillingCycle() {
  console.log('测试OCR识别和钻孔固定循环G代码生成功能...');
  
  // 1. 直接测试OCR识别功能
  console.log('\n1. 测试OCR相关功能...');
  try {
    const { extractGeometricInfoFromText, postProcessOcrText } = require('./src/modules/subprocesses/pdfParsingProcess');
    
    // 测试OCR后处理功能
    const testOcrText = "H0LE AT X100 Y100 DIAMETER 5.5mm DEPTH 10mm THRU";
    const processedText = postProcessOcrText(testOcrText);
    console.log('OCR文本后处理结果:', processedText);
    
    // 测试几何信息提取
    const geometricInfo = extractGeometricInfoFromText(processedText);
    console.log('提取的几何信息:', JSON.stringify(geometricInfo, null, 2));
    
  } catch (error) {
    console.error('OCR功能测试失败:', error.message);
  }
  
  // 2. 测试钻孔固定循环G代码生成功能
  console.log('\n2. 测试钻孔固定循环G代码生成功能...');
  try {
    const { generateHoleGCode, generateHoleGCodeBatch, generateCounterboreGCode, generateCounterboreGCodeBatch } = require('./src/modules/gCodeGeneration');
    
    // 测试单孔G代码生成（使用钻孔固定循环）
    const singleHoleFeature = {
      id: 'test_hole_1',
      featureType: 'hole',
      baseGeometry: {
        center: { x: 100, y: 100 }
      },
      parameters: {
        diameter: 5.5,
        depth: 14,
        drawingDepth: 10,
        holeType: 'through'
      }
    };
    
    const singleHoleGCode = generateHoleGCode(singleHoleFeature);
    console.log('\n单孔G代码生成结果:');
    console.log(singleHoleGCode);
    
    // 检查是否包含钻孔固定循环
    const hasDrillingCycle = singleHoleGCode.some(line => 
      line.includes('G81') || line.includes('G82') || line.includes('G83')
    );
    
    if (hasDrillingCycle) {
      console.log('✓ 单孔G代码中检测到钻孔固定循环');
    } else {
      console.log('⚠ 单孔G代码中未检测到钻孔固定循环');
    }
    
    // 测试批量孔G代码生成
    const batchHoleFeatures = [
      {
        id: 'test_hole_1',
        featureType: 'hole',
        baseGeometry: {
          center: { x: 100, y: 100 }
        },
        parameters: {
          diameter: 5.5,
          depth: 14,
          drawingDepth: 10
        }
      },
      {
        id: 'test_hole_2',
        featureType: 'hole',
        baseGeometry: {
          center: { x: 120, y: 100 }
        },
        parameters: {
          diameter: 5.5,
          depth: 14,
          drawingDepth: 10
        }
      }
    ];
    
    const batchHoleGCode = generateHoleGCodeBatch(batchHoleFeatures[0], batchHoleFeatures);
    console.log('\n批量孔G代码生成结果:');
    console.log(batchHoleGCode);
    
    // 检查批量G代码是否包含钻孔固定循环
    const hasBatchDrillingCycle = batchHoleGCode.some(line => 
      line.includes('G81') || line.includes('G82') || line.includes('G83')
    );
    
    if (hasBatchDrillingCycle) {
      console.log('✓ 批量孔G代码中检测到钻孔固定循环');
    } else {
      console.log('⚠ 批量孔G代码中未检测到钻孔固定循环');
    }
    
    // 测试沉头孔G代码生成
    const counterboreFeature = {
      id: 'test_cb_1',
      featureType: 'counterbore',
      baseGeometry: {
        center: { x: 150, y: 150 }
      },
      parameters: {
        diameter: 5.5,
        depth: 14,
        drawingDepth: 10,
        counterboreDiameter: 9,
        counterboreDepth: 5.5,
        useCounterbore: true
      }
    };
    
    const counterboreGCode = generateCounterboreGCode(counterboreFeature);
    console.log('\n沉头孔G代码生成结果:');
    console.log(counterboreGCode);
    
    // 检查沉头孔G代码是否包含固定循环
    const hasCounterboreCycles = counterboreGCode.some(line => 
      line.includes('G81') || line.includes('G82') || line.includes('G83')
    );
    
    if (hasCounterboreCycles) {
      console.log('✓ 沉头孔G代码中检测到钻孔固定循环');
    } else {
      console.log('⚠ 沉头孔G代码中未检测到钻孔固定循环');
    }
    
    console.log('\n钻孔固定循环G代码格式改进功能测试完成!');
    
  } catch (error) {
    console.error('钻孔固定循环G代码生成功能测试失败:', error.message);
    console.error(error.stack);
  }
  
  // 3. 验证G代码生成器主函数
  console.log('\n3. 验证G代码生成器主函数...');
  try {
    const { triggerGCodeGeneration } = require('./src/modules/gCodeGeneration');
    
    // 创建一个模拟项目
    const mockProject = {
      features: [
        {
          id: 'mock_hole_1',
          featureType: 'hole',
          baseGeometry: {
            center: { x: 100, y: 100 }
          },
          parameters: {
            diameter: 5.5,
            depth: 14,
            drawingDepth: 10
          }
        }
      ],
      materialType: 'steel'
    };
    
    const gCodeBlocks = triggerGCodeGeneration(mockProject);
    console.log('主G代码生成器结果:');
    console.log(`生成了 ${gCodeBlocks.length} 个G代码块`);
    
    // 检查是否包含钻孔固定循环
    let hasAnyDrillingCycle = false;
    for (const block of gCodeBlocks) {
      if (Array.isArray(block.code)) {
        const blockHasCycle = block.code.some(line => 
          line.includes('G81') || line.includes('G82') || line.includes('G83')
        );
        if (blockHasCycle) {
          hasAnyDrillingCycle = true;
          console.log(`✓ G代码块 ${block.id} 包含钻孔固定循环`);
          // 显示包含循环的行
          const drillingLines = block.code.filter(line => 
            line.includes('G81') || line.includes('G82') || line.includes('G83')
          );
          console.log('  钻孔循环行:', drillingLines);
        }
      }
    }
    
    if (hasAnyDrillingCycle) {
      console.log('✓ 主生成器成功生成了钻孔固定循环');
    } else {
      console.log('⚠ 主生成器未生成钻孔固定循环');
    }
    
  } catch (error) {
    console.error('G代码生成器主函数测试失败:', error.message);
    console.error(error.stack);
  }
  
  console.log('\n所有测试完成!');
}

// 运行测试
testOCRAndDrillingCycle();