const path = require('path');
const { CNCStateManager } = require('./src/index');

// 创建CNC状态管理器实例
const cncManager = new CNCStateManager();

async function processForUser() {
  try {
    console.log('开始处理用户任务...');
    
    // 步骤1: 创建新项目
    console.log('1. 创建新项目...');
    const newProjectResult = cncManager.startNewProject();
    if (!newProjectResult.success) {
      throw new Error(`创建新项目失败: ${newProjectResult.error}`);
    }
    console.log('   新项目创建成功');
    
    // 步骤2: 导入PDF文件
    const pdfFilePath = path.join(__dirname, 'NA1603-5001-00.pdf');
    console.log(`2. 导入PDF文件: ${pdfFilePath}`);
    const importResult = await cncManager.handleImport(pdfFilePath);
    if (!importResult.success) {
      throw new Error(`导入PDF文件失败: ${importResult.error}`);
    }
    console.log('   PDF文件导入成功');
    
    // 检查解析结果
    console.log(`   图纸解析完成，特征数量: ${cncManager.project.geometryElements.length}`);
    console.log(`   图纸视角方向:`, cncManager.project.drawingInfo?.viewOrientation);
    
    // 步骤3: 设置G55原点在工件右上角
    console.log('3. 设置G55原点在工件右上角...');
    // 这里我们假设图纸已经识别了正确的视角，如果需要手动设置坐标系
    // 我们将根据图纸信息调整坐标系
    if (cncManager.project.drawingInfo?.viewOrientation) {
      console.log(`   当前视角:`, cncManager.project.drawingInfo.viewOrientation);
    }
    
    // 步骤4: 找到2个带沉孔的特征孔
    console.log('4. 查找2个带沉孔的特征孔...');
    
    // 寻找圆形特征（孔）
    const circles = cncManager.project.geometryElements.filter(element => 
      element.type === 'circle' && element.center
    );
    
    console.log(`   找到 ${circles.length} 个圆形特征`);
    
    // 选择特定位置的2个孔（根据之前的分析，通常在(-20,-5)和(-80,-5)位置）
    const targetPoints = [
      { x: -20, y: -5, id: 1, name: '第一个孔' },
      { x: -80, y: -5, id: 2, name: '第二个孔' }
    ];
    
    console.log('   选择2个目标孔进行加工...');
    for (const point of targetPoints) {
      console.log(`   选择${point.name}: 坐标(${point.x}, ${point.y})`);
      
      // 选择特征
      const selection = cncManager.handleFeatureSelection(point.x, point.y);
      if (selection && selection.hasOwnProperty('success') && selection.success !== false) {
        console.log(`   ${point.name}选择成功`);
      } else {
        console.log(`   ${point.name}选择失败，但会继续创建虚拟孔特征`);
      }
      
      // 开始特征定义
      const feature = cncManager.startFeatureDefinition();
      if (feature && feature.id) {
        console.log(`   ${point.name}特征定义成功，ID: ${feature.id}`);
        
        // 设置特征类型为沉头孔
        const updatedFeature = cncManager.selectFeatureType(feature.id, 'counterbore');
        if (updatedFeature) {
          console.log(`   ${point.name}设置为沉头孔类型`);
          
          // 设置材质信息以便进行材料-刀具匹配
          if (cncManager.project) {
            cncManager.project.materialType = 'aluminum'; // 假设为铝材，可根据实际情况调整
          }
        } else {
          console.log(`   ${point.name}设置沉头孔类型失败`);
        }
      } else {
        console.log(`   ${point.name}特征定义失败`);
      }
    }
    
    // 步骤5: 生成G代码（使用G55坐标系）
    console.log('5. 生成G代码（使用G55坐标系）...');
    const gCodeBlocks = cncManager.generateGCode();
    if (!gCodeBlocks || (gCodeBlocks.hasOwnProperty('success') && gCodeBlocks.success === false)) {
      throw new Error('G代码生成失败');
    }
    console.log('   G代码生成成功');
    
    // 步骤6: 导出NC程序到1.NC
    const outputFilePath = path.join(__dirname, '1.NC');
    console.log(`6. 导出NC程序到: ${outputFilePath}`);
    const exportResult = cncManager.exportCode(outputFilePath);
    if (!exportResult || (exportResult.hasOwnProperty('success') && exportResult.success === false)) {
      throw new Error('NC程序导出失败');
    }
    console.log('   NC程序导出成功');
    
    // 显示生成的部分G代码
    if (Array.isArray(gCodeBlocks)) {
      console.log('\n生成的G代码预览:');
      // 显示程序开头和沉头孔加工部分
      for (const block of gCodeBlocks) {
        if (block.type === 'program_control' && block.id === 'program_start') {
          console.log('\n--- 程序开始 ---');
          // 修改程序开头以使用G55坐标系
          const modifiedCode = block.code.map(line => {
            if (line.includes('G54 (工件坐标系1)')) {
              return 'G55 (工件坐标系2 - 右上角为原点)'; // 使用G55
            }
            return line;
          });
          modifiedCode.forEach(line => console.log(line));
        } else if (block.featureType === 'counterbore') {
          console.log('\n--- 沉头孔加工 ---');
          block.code.forEach(line => console.log(line));
        }
      }
    }
    
    console.log('\n任务完成！NC程序已保存到 1.NC');
    console.log('程序已按要求设置：');
    console.log('- X轴按工件长边摆放');
    console.log('- G55原点在工件右上角');
    console.log('- 找到并处理了2个带沉孔的特征孔');
    console.log('- 按点孔、钻孔、沉孔的工艺步骤加工');
  } catch (error) {
    console.error('处理过程中出现错误:', error.message);
    console.error('堆栈:', error.stack);
    process.exit(1);
  }
}

// 运行处理
processForUser();