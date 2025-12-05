const path = require('path');
const { CNCStateManager } = require('./src/index');

// 创建CNC状态管理器实例
const cncManager = new CNCStateManager();

async function processPDF() {
  try {
    console.log('开始处理PDF文件...');
    
    // 步骤1: 创建新项目
    console.log('创建新项目...');
    const newProjectResult = cncManager.startNewProject();
    if (!newProjectResult.success) {
      throw new Error(`创建新项目失败: ${newProjectResult.error}`);
    }
    console.log('新项目创建成功');
    
    // 步骤2: 导入PDF文件
    const pdfFilePath = path.join(__dirname, 'NA1603-5001-00.pdf');
    console.log(`导入PDF文件: ${pdfFilePath}`);
    const importResult = await cncManager.handleImport(pdfFilePath);
    if (!importResult.success) {
      throw new Error(`导入PDF文件失败: ${importResult.error}`);
    }
    console.log('PDF文件导入成功');
    
    // 检查解析结果
    console.log('图纸解析完成，特征数量:', cncManager.project.geometryElements.length);
    
    // 步骤3: 选择要加工的2个沉头孔
    // 假设图纸中有特定位置的孔（根据之前的实现，通常是x=-20,y=-5和x=-80,y=-5）
    console.log('选择要加工的2个沉头孔...');
    
    // 选择2个特定坐标点的孔
    const targetPoints = [
      { x: -20, y: -5, id: 1 },
      { x: -80, y: -5, id: 2 }
    ];
    
    for (const point of targetPoints) {
      console.log(`选择第${point.id}个孔: 坐标(${point.x}, ${point.y})`);
      
      // 选择特征
      const selection = cncManager.handleFeatureSelection(point.x, point.y);
      if (selection && selection.hasOwnProperty('success') && selection.success !== false) {
        console.log(`第${point.id}个孔选择成功`);
      } else {
        console.log(`第${point.id}个孔选择失败，但会继续创建虚拟孔特征`);
      }
      
      // 开始特征定义
      const feature = cncManager.startFeatureDefinition();
      if (feature && feature.id) {
        console.log(`第${point.id}个孔特征定义成功，ID: ${feature.id}`);
        
        // 设置特征类型为沉头孔
        const updatedFeature = cncManager.selectFeatureType(feature.id, 'counterbore');
        if (updatedFeature) {
          console.log(`第${point.id}个孔设置为沉头孔类型`);
        } else {
          console.log(`第${point.id}个孔设置沉头孔类型失败`);
        }
      } else {
        console.log(`第${point.id}个孔特征定义失败`);
      }
    }
    
    // 步骤4: 生成G代码
    console.log('生成G代码...');
    const gCodeBlocks = cncManager.generateGCode();
    if (!gCodeBlocks || (gCodeBlocks.hasOwnProperty('success') && gCodeBlocks.success === false)) {
      throw new Error('G代码生成失败');
    }
    console.log('G代码生成成功');
    
    // 步骤5: 导出NC程序
    const outputFilePath = path.join(__dirname, 'output.nc');
    console.log(`导出NC程序到: ${outputFilePath}`);
    const exportResult = cncManager.exportCode(outputFilePath);
    if (!exportResult || (exportResult.hasOwnProperty('success') && exportResult.success === false)) {
      throw new Error('NC程序导出失败');
    }
    console.log('NC程序导出成功');
    
    // 显示生成的部分G代码
    if (Array.isArray(gCodeBlocks)) {
      console.log('\n生成的G代码预览:');
      // 只显示程序开头和沉头孔加工部分
      for (const block of gCodeBlocks) {
        if (block.type === 'program_control' && block.id === 'program_start') {
          console.log('\n--- 程序开始 ---');
          block.code.forEach(line => console.log(line));
        } else if (block.featureType === 'counterbore') {
          console.log('\n--- 沉头孔加工 ---');
          block.code.forEach(line => console.log(line));
        }
      }
    }
    
    console.log('\n处理完成！NC程序已保存到 output.nc');
  } catch (error) {
    console.error('处理过程中出现错误:', error.message);
    console.error('堆栈:', error.stack);
    process.exit(1);
  }
}

// 运行处理
processPDF();