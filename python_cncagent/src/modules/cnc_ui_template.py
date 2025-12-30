"""
CNC Agent Web UI 模板
重构UI界面，以大模型为技术框架，支持2D图纸、3D图纸、描述词输入和NC程序输出
"""
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNC Agent - AI驱动的智能NC编程平台</title>
    <style>
        :root {
            --primary-color: #3498db;
            --secondary-color: #2c3e50;
            --success-color: #27ae60;
            --warning-color: #f39c12;
            --danger-color: #e74c3c;
            --light-bg: #f8f9fa;
            --dark-bg: #2c3e50;
            --border-radius: 8px;
            --box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: var(--dark-bg);
            color: white;
            padding: 1rem;
            text-align: center;
            border-radius: var(--border-radius);
            margin-bottom: 20px;
            box-shadow: var(--box-shadow);
        }
        
        h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        
        .subtitle {
            font-size: 1.1rem;
            opacity: 0.9;
        }
        
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        
        .input-section, .output-section {
            background: white;
            padding: 20px;
            border-radius: var(--border-radius);
            box-shadow: var(--box-shadow);
        }
        
        .section-title {
            font-size: 1.3rem;
            color: var(--secondary-color);
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--primary-color);
        }
        
        .form-group {
            margin-bottom: 15px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: var(--secondary-color);
        }
        
        .optional-label {
            opacity: 0.7;
            font-size: 0.9em;
            font-weight: normal;
        }
        
        input[type="file"], input[type="text"], input[type="number"], textarea, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: var(--border-radius);
            font-size: 16px;
            box-sizing: border-box;
            transition: border-color 0.3s;
        }
        
        input[type="file"] {
            padding: 8px;
        }
        
        input:focus, textarea:focus, select:focus {
            outline: none;
            border-color: var(--primary-color);
            box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
        }
        
        textarea {
            height: 120px;
            resize: vertical;
        }
        
        .file-input-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }
        
        .file-input-container {
            flex: 1;
            min-width: 250px;
        }
        
        .btn {
            display: inline-block;
            background: var(--primary-color);
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: var(--border-radius);
            cursor: pointer;
            font-size: 16px;
            font-weight: bold;
            transition: all 0.3s;
            text-align: center;
            text-decoration: none;
        }
        
        .btn:hover {
            background: #2980b9;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
        }
        
        .btn:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .btn-success {
            background: var(--success-color);
        }
        
        .btn-success:hover {
            background: #219653;
        }
        
        .btn-warning {
            background: var(--warning-color);
        }
        
        .btn-warning:hover {
            background: #e67e22;
        }
        
        .btn-danger {
            background: var(--danger-color);
        }
        
        .btn-danger:hover {
            background: #c0392b;
        }
        
        .btn-group {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .result {
            margin-top: 20px;
            padding: 15px;
            background: var(--light-bg);
            border-radius: var(--border-radius);
            border-left: 4px solid var(--primary-color);
        }
        
        .result h3 {
            margin-top: 0;
            color: var(--secondary-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .nc-code {
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 15px;
            border-radius: var(--border-radius);
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
            max-height: 400px;
            overflow-y: auto;
            margin: 10px 0;
            border: 1px solid #444;
        }
        
        .error {
            color: var(--danger-color);
            background: #fadbd8;
            padding: 15px;
            border-radius: var(--border-radius);
            margin-top: 15px;
            border-left: 4px solid var(--danger-color);
        }
        
        .success {
            color: var(--success-color);
            background: #d5f4e6;
            padding: 15px;
            border-radius: var(--border-radius);
            margin-top: 15px;
            border-left: 4px solid var(--success-color);
        }
        
        .loading {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            padding: 10px 15px;
            background: #e8f4fc;
            border-radius: var(--border-radius);
        }
        
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid #3498db;
            border-top: 2px solid transparent;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .instructions {
            background: #e8f4fc;
            padding: 15px;
            border-radius: var(--border-radius);
            margin-bottom: 20px;
            border-left: 4px solid var(--primary-color);
        }
        
        .instructions h3 {
            margin-top: 0;
            color: var(--secondary-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .instructions ul {
            margin: 10px 0 0 20px;
            padding: 0;
        }
        
        .instructions li {
            margin-bottom: 8px;
        }
        
        .file-preview {
            margin-top: 10px;
            padding: 10px;
            background: #f0f8ff;
            border-radius: var(--border-radius);
            border: 1px dashed #3498db;
        }
        
        .file-preview p {
            margin: 0;
            font-size: 0.9em;
            color: #555;
        }
        
        .api-info {
            background: #fff3cd;
            padding: 10px;
            border-radius: var(--border-radius);
            margin-top: 10px;
            font-size: 0.9em;
            border-left: 4px solid var(--warning-color);
        }
        
        .api-status {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-top: 5px;
        }
        
        .status-indicator {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
        }
        
        .status-active {
            background: var(--success-color);
        }
        
        .status-inactive {
            background: var(--danger-color);
        }
        
        .download-btn {
            margin-top: 10px;
            display: inline-block;
        }
        
        footer {
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9rem;
            margin-top: 20px;
        }
        
        .advanced-options {
            background: #f9f9f9;
            padding: 15px;
            border-radius: var(--border-radius);
            margin-top: 15px;
            border: 1px solid #eee;
        }
        
        .advanced-toggle {
            cursor: pointer;
            color: var(--primary-color);
            font-weight: bold;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .ai-powered {
            background: linear-gradient(45deg, #3498db, #2c3e50);
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 10px;
            vertical-align: middle;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>CNC Agent - AI驱动的智能NC编程平台</h1>
            <div class="subtitle">基于大语言模型的2D/3D图纸到NC程序转换系统</div>
        </header>
        
        <div class="instructions">
            <h3>使用说明</h3>
            <ul>
                <li><strong>2D图纸</strong>：支持PDF、JPG、PNG等格式，用于提取几何特征</li>
                <li><strong>3D模型</strong>：支持STL、STEP、IGES、OBJ等格式，用于精确几何分析</li>
                <li><strong>加工描述</strong>：详细描述加工要求（如：请加工φ22沉孔，深度20mm）</li>
                <li><strong>AI处理</strong>：系统将结合图纸、模型和描述生成NC程序</li>
                <li><span class="ai-powered">AI驱动</span> 使用大语言模型进行智能分析和程序生成</li>
            </ul>
        </div>
        
        <form id="cncForm" enctype="multipart/form-data">
            <div class="main-content">
                <div class="input-section">
                    <h2 class="section-title">输入信息</h2>
                    
                    <div class="form-group">
                        <label for="pdfFile">2D图纸文件 (可选)</label>
                        <div class="optional-label">支持PDF、JPG、PNG、BMP等格式</div>
                        <input type="file" id="pdfFile" name="pdf" accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff">
                        <div id="pdfPreview" class="file-preview" style="display: none;"></div>
                    </div>
                    
                    <div class="form-group">
                        <label for="model3DFile">3D模型文件 (可选)</label>
                        <div class="optional-label">支持STL、STEP、IGES、OBJ等格式</div>
                        <input type="file" id="model3DFile" name="model_3d" accept=".stl,.step,.stp,.igs,.iges,.obj,.ply">
                        <div id="model3DPreview" class="file-preview" style="display: none;"></div>
                    </div>
                    
                    <div class="form-group">
                        <label for="description">加工描述 <span style="color: red;">*</span></label>
                        <div class="optional-label">请详细描述加工要求（如：请加工φ22沉孔，深度20mm，使用铣削加工）</div>
                        <textarea id="description" name="description" placeholder="例如：请加工一个直径10mm的孔，深度5mm，使用铣削加工" required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="material">材料类型</label>
                        <select id="material" name="material">
                            <option value="Aluminum">铝 (Aluminum)</option>
                            <option value="Steel">钢 (Steel)</option>
                            <option value="Stainless Steel">不锈钢 (Stainless Steel)</option>
                            <option value="Brass">黄铜 (Brass)</option>
                            <option value="Plastic">塑料 (Plastic)</option>
                            <option value="Cast Iron">铸铁 (Cast Iron)</option>
                            <option value="Titanium">钛 (Titanium)</option>
                            <option value="Other">其他</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="scale">图纸比例 (可选)</label>
                        <input type="number" id="scale" name="scale" value="1.0" min="0.001" max="100" step="0.1">
                    </div>
                    
                    <div class="advanced-options">
                        <div class="advanced-toggle" onclick="toggleAdvancedOptions()">
                            高级选项
                            <span id="advancedIndicator">+</span>
                        </div>
                        <div id="advancedContent" style="display: none;">
                            <div class="form-group">
                                <label for="precision">精度要求</label>
                                <select id="precision" name="precision">
                                    <option value="General">一般 (General)</option>
                                    <option value="High">高精度 (High)</option>
                                    <option value="Ultra">超精密 (Ultra)</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="coordinateStrategy">坐标策略</label>
                                <select id="coordinateStrategy" name="coordinate_strategy">
                                    <option value="highest_y">最高Y点 (highest_y)</option>
                                    <option value="lowest_y">最低Y点 (lowest_y)</option>
                                    <option value="leftmost_x">最左X点 (leftmost_x)</option>
                                    <option value="rightmost_x">最右X点 (rightmost_x)</option>
                                    <option value="center">中心点 (center)</option>
                                    <option value="geometric_center">几何中心 (geometric_center)</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div class="api-info">
                        <strong>AI模型配置</strong>
                        <div class="api-status">
                            <span class="status-indicator status-active"></span>
                            <span>AI模型已就绪</span>
                        </div>
                        <div style="font-size: 0.85em; margin-top: 5px;">
                            系统将使用大语言模型智能分析图纸和描述，生成高质量NC程序
                        </div>
                    </div>
                    
                    <div class="btn-group">
                        <button type="submit" id="submitBtn" class="btn">
                            生成NC程序
                            <span id="submitSpinner" class="spinner" style="display: none;"></span>
                        </button>
                        <button type="button" class="btn btn-warning" onclick="resetForm()">重置</button>
                    </div>
                </div>
                
                <div class="output-section">
                    <h2 class="section-title">输出结果</h2>
                    
                    <div id="result">
                        <div class="instructions">
                            <h3>操作提示</h3>
                            <ul>
                                <li>上传2D图纸或3D模型文件</li>
                                <li>详细描述加工要求</li>
                                <li>点击"生成NC程序"按钮</li>
                                <li>查看生成的NC代码并下载</li>
                            </ul>
                        </div>
                        
                        <div id="apiStatus" class="api-info">
                            <strong>AI模型状态</strong>
                            <div class="api-status">
                                <span class="status-indicator status-active"></span>
                                <span>大语言模型服务在线</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </form>
        
        <footer>
            <p>CNC Agent - AI驱动的智能NC编程平台 | 基于大语言模型技术</p>
            <p>AI存在幻觉，生成的NC需要加强人工复核。建议在实际加工前进行仿真验证。</p>
        </footer>
    </div>

    <script>
        // 文件预览功能
        document.getElementById('pdfFile').addEventListener('change', function(e) {
            const file = e.target.files[0];
            const preview = document.getElementById('pdfPreview');
            
            if (file) {
                preview.innerHTML = '<p>📁 ' + file.name + ' (' + formatFileSize(file.size) + ')</p>';
                preview.style.display = 'block';
            } else {
                preview.style.display = 'none';
            }
        });
        
        document.getElementById('model3DFile').addEventListener('change', function(e) {
            const file = e.target.files[0];
            const preview = document.getElementById('model3DPreview');
            
            if (file) {
                preview.innerHTML = '<p>📦 ' + file.name + ' (' + formatFileSize(file.size) + ')</p>';
                preview.style.display = 'block';
            } else {
                preview.style.display = 'none';
            }
        });
        
        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        // 高级选项切换
        function toggleAdvancedOptions() {
            const content = document.getElementById('advancedContent');
            const indicator = document.getElementById('advancedIndicator');
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                indicator.textContent = '−';
            } else {
                content.style.display = 'none';
                indicator.textContent = '+';
            }
        }
        
        // 表单重置
        function resetForm() {
            document.getElementById('cncForm').reset();
            document.getElementById('pdfPreview').style.display = 'none';
            document.getElementById('model3DPreview').style.display = 'none';
            document.getElementById('result').innerHTML = `
                <div class="instructions">
                    <h3>💡 操作提示</h3>
                    <ul>
                        <li>上传2D图纸或3D模型文件</li>
                        <li>详细描述加工要求</li>
                        <li>点击"生成NC程序"按钮</li>
                        <li>查看生成的NC代码并下载</li>
                    </ul>
                </div>
                
                <div id="apiStatus" class="api-info">
                    <strong>AI模型状态</strong>
                    <div class="api-status">
                        <span class="status-indicator status-active"></span>
                        <span>大语言模型服务在线</span>
                    </div>
                </div>
            `;
        }
        
        // 主提交处理
        document.getElementById('cncForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = document.getElementById('submitBtn');
            const submitSpinner = document.getElementById('submitSpinner');
            const resultDiv = document.getElementById('result');
            
            // 验证必填字段
            const description = formData.get('description');
            if (!description || !description.trim()) {
                resultDiv.innerHTML = '<div class="error">❌ 错误: 加工描述是必填项</div>';
                return;
            }
            
            // 显示加载状态
            submitBtn.disabled = true;
            submitBtn.innerHTML = '⏳ 正在生成NC程序... <span id="submitSpinner" class="spinner" style="display: inline-block;"></span>';
            resultDiv.innerHTML = `
                <div class="loading">
                    <span class="spinner"></span>
                    <span>AI正在分析图纸和描述，生成NC程序...</span>
                </div>
            `;
            
            // 创建带超时的fetch请求
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000); // 2分钟超时
            
            try {
                const response = await fetch('/generate_nc', {
                    method: 'POST',
                    body: formData,
                    signal: controller.signal
                });
                
                clearTimeout(timeoutId); // 清除超时
                
                if (!response.ok) {
                    throw new Error(`HTTP错误! 状态: ${response.status}`);
                }
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    resultDiv.innerHTML = `
                        <div class="result">
                            <h3>✅ 生成成功 <small>(AI驱动)</small></h3>
                            <p>NC程序已生成，共 ${data.nc_program.split('\\n').length} 行代码</p>
                            <div class="nc-code">${escapeHtml(data.nc_program)}</div>
                            <a href="/download_nc/${data.nc_file_path}" class="btn btn-success download-btn" download="output.nc">
                                💾 下载NC文件
                            </a>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<div class="error">❌ 错误: ${data.error || '未知错误'}</div>`;
                }
            } catch (error) {
                clearTimeout(timeoutId); // 清除超时
                
                if (error.name === 'AbortError') {
                    resultDiv.innerHTML = '<div class="error">❌ 请求超时: AI处理时间过长，请稍后重试或检查API密钥配置</div>';
                } else {
                    resultDiv.innerHTML = `<div class="error">❌ 请求失败: ${error.message}</div>`;
                }
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '🚀 生成NC程序 <span id="submitSpinner" class="spinner" style="display: none;"></span>';
            }
        });
        
        // HTML转义函数
        function escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
'''