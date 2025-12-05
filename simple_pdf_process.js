const path = require('path');
const { pdfParsingProcess } = require('./src/modules/subprocesses/pdfParsingProcess');

async function simpleProcessPDF() {
  try {
    console.log('开始处理PDF文件...');
    
    // 直接调用PDF解析
    const pdfFilePath = path.join(__dirname, 'NA1603-5001-00.pdf');
    console.log(`解析PDF文件: ${pdfFilePath}`);
    
    const result = await pdfParsingProcess(pdfFilePath);
    console.log('PDF解析完成');
    console.log('图纸信息:', result.drawingInfo);
    console.log('几何元素数量:', result.geometryElements.length);
    console.log('尺寸数量:', result.dimensions.length);
    
    // 显示视角信息
    if (result.drawingInfo.viewOrientation) {
      console.log('图纸视角方向:', result.drawingInfo.viewOrientation);
    }
    
    // 寻找圆形特征（孔）
    const circles = result.geometryElements.filter(element => 
      element.type === 'circle' && element.center
    );
    
    console.log(`找到 ${circles.length} 个圆形特征`);
    
    // 显示圆形特征信息
    circles.forEach((circle, index) => {
      console.log(`圆形 ${index + 1}: 中心(${circle.center.x}, ${circle.center.y}), 半径: ${circle.radius || circle.radiusX || 'N/A'}`);
    });
    
    console.log('PDF解析任务完成！');
  } catch (error) {
    console.error('处理过程中出现错误:', error.message);
    console.error('堆栈:', error.stack);
  }
}

simpleProcessPDF();