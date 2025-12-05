// 测试原始的CNCStateManager在修复后的行为
const { CNCStateManager } = require('../src/index.js');

describe('修复后的CNCStateManager测试', () => {
  let stateManager;

  beforeEach(() => {
    stateManager = new CNCStateManager();
  });

  test('handleImport方法应该等待异步解析完成后再返回', async () => {
    // 创建一个临时PDF文件用于测试
    const fs = require('fs');
    const path = require('path');
    const tempPdfPath = path.join(__dirname, 'temp_test_file.pdf');
    
    // 创建一个简单的PDF文件
    fs.writeFileSync(tempPdfPath, '%PDF-1.4\n%����\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000103 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n149\n%%EOF');

    try {
      // 检查初始状态
      expect(stateManager.state).toBe('waiting_import');

      // 调用handleImport，这应该等待解析完成后再返回
      const result = await stateManager.handleImport(tempPdfPath);

      // 验证导入成功
      expect(result.success).toBe(true);
      expect(result.project).toBeDefined();

      // 验证状态在返回时已经是'ready'，这意味着异步解析已完成
      expect(stateManager.state).toBe('ready');

      // 验证状态转换历史中包含正确的状态
      const history = stateManager.stateHistory;
      expect(history).toContain('drawing_loaded');
      expect(history).toContain('processing');
      expect(history).toContain('ready');
      
      // 确保'processing'在'ready'之前
      const processingIndex = history.indexOf('processing');
      const readyIndex = history.indexOf('ready');
      expect(processingIndex).toBeLessThan(readyIndex);
    } finally {
      // 清理临时文件
      if (fs.existsSync(tempPdfPath)) {
        fs.unlinkSync(tempPdfPath);
      }
    }
  });

  test('在解析完成前不应允许特征选择', async () => {
    const fs = require('fs');
    const path = require('path');
    const tempPdfPath = path.join(__dirname, 'temp_test_file2.pdf');
    
    // 创建一个简单的PDF文件
    fs.writeFileSync(tempPdfPath, '%PDF-1.4\n%����\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000053 00000 n \n0000000103 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n149\n%%EOF');

    try {
      // 在导入完成前尝试选择特征 - 应该失败
      const selectionBeforeImport = stateManager.handleFeatureSelection(30, 30);
      expect(selectionBeforeImport.success).toBe(false);
      expect(selectionBeforeImport.error).toContain('不允许选择特征');

      // 导入文件
      await stateManager.handleImport(tempPdfPath);

      // 现在应该允许选择特征（即使没有找到实际的几何元素）
      // 验证不会因为状态错误而失败
      const selectionAfterImport = stateManager.handleFeatureSelection(30, 30);
      // 特征选择可能返回null（如果没有找到匹配的元素）或一个对象
      // 但不应该返回一个带有状态错误的对象
      if (selectionAfterImport && typeof selectionAfterImport === 'object' && selectionAfterImport.success === false) {
        // 如果返回错误，它不应该是因为状态问题
        expect(selectionAfterImport.error).not.toContain('不允许选择特征');
      }
      // selectionAfterImport 可能是 null 或有效的选择对象
      expect(selectionAfterImport).toBeDefined();
    } finally {
      if (fs.existsSync(tempPdfPath)) {
        fs.unlinkSync(tempPdfPath);
      }
    }
  });
});