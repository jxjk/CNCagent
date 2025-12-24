"""
Flask API服务，提供PDF到NC程序的Web接口
"""
import os
import json
from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import tempfile
from src.main import generate_nc_from_pdf


app = Flask(__name__)
CORS(app)  # 允许跨域请求


# HTML模板 - CNC Agent用户界面
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNC Agent - PDF到NC程序转换器</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }
        h1 {
            text-align: center;
            color: #2c3e50;
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #2c3e50;
        }
        input[type="file"], input[type="text"], input[type="number"], textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        textarea {
            height: 100px;
            resize: vertical;
        }
        button {
            background: #3498db;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        button:hover {
            background: #2980b9;
        }
        button:disabled {
            background: #bdc3c7;
            cursor: not-allowed;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #3498db;
        }
        .result h3 {
            margin-top: 0;
            color: #2c3e50;
        }
        .nc-code {
            background: #2c3e50;
            color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
        }
        .error {
            color: #e74c3c;
            background: #fadbd8;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .success {
            color: #27ae60;
            background: #d5f4e6;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .loading {
            text-align: center;
            padding: 20px;
        }
        .loading:after {
            content: "";
            animation: spin 1s linear infinite;
            width: 20px;
            height: 20px;
            border: 3px solid #3498db;
            border-top: 3px solid transparent;
            border-radius: 50%;
            display: inline-block;
            margin-left: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .instructions {
            background: #e8f4fc;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        .instructions h3 {
            margin-top: 0;
            color: #2980b9;
        }
        .instructions ul {
            margin-bottom: 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CNC Agent - PDF到NC程序转换器</h1>
        
        <div class="instructions">
            <h3>使用说明</h3>
            <ul>
                <li>上传包含几何图纸的PDF文件</li>
                <li>在描述框中输入加工要求（如：请加工一个直径10mm的孔，深度5mm）</li>
                <li>设置图纸比例尺（默认为1.0）</li>
                <li>点击"生成NC程序"按钮</li>
            </ul>
        </div>
        
        <form id="cncForm" enctype="multipart/form-data">
            <div class="form-group">
                <label for="pdfFile">PDF图纸文件:</label>
                <input type="file" id="pdfFile" name="pdf" accept=".pdf" required>
            </div>
            
            <div class="form-group">
                <label for="description">加工描述:</label>
                <textarea id="description" name="description" placeholder="例如：请加工一个直径10mm的孔，深度5mm，使用铣削加工" required></textarea>
            </div>
            
            <div class="form-group">
                <label for="scale">图纸比例尺 (可选):</label>
                <input type="number" id="scale" name="scale" value="1.0" min="0.001" max="100" step="0.1">
            </div>
            
            <button type="submit" id="submitBtn">生成NC程序</button>
        </form>
        
        <div id="result"></div>
    </div>

    <script>
        document.getElementById('cncForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const submitBtn = document.getElementById('submitBtn');
            const resultDiv = document.getElementById('result');
            
            // 显示加载状态
            submitBtn.disabled = true;
            submitBtn.textContent = '生成中...';
            resultDiv.innerHTML = '<div class="loading">处理中</div>';
            
            try {
                const response = await fetch('/generate_nc', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    resultDiv.innerHTML = `
                        <div class="result">
                            <h3>生成的NC程序</h3>
                            <div class="nc-code">${data.nc_program}</div>
                            <br>
                            <a href="/download_nc/${data.nc_file_path}" download="output.nc">
                                <button>下载NC文件</button>
                            </a>
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `<div class="error">错误: ${data.error || '未知错误'}</div>`;
                }
            } catch (error) {
                resultDiv.innerHTML = `<div class="error">请求失败: ${error.message}</div>`;
            } finally {
                submitBtn.disabled = false;
                submitBtn.textContent = '生成NC程序';
            }
        });
    </script>
</body>
</html>
'''


@app.route('/')
def index():
    """返回用户界面"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({"status": "healthy", "service": "CNC Agent API"})


@app.route('/generate_nc', methods=['POST'])
def generate_nc():
    """根据上传的PDF和用户描述生成NC程序"""
    try:
        # 检查请求是否包含文件和描述
        if 'pdf' not in request.files:
            return jsonify({"error": "缺少PDF文件"}), 400
        
        if 'description' not in request.form:
            return jsonify({"error": "缺少用户描述"}), 400
        
        pdf_file = request.files['pdf']
        user_description = request.form['description']
        scale = float(request.form.get('scale', 1.0))
        
        # 验证文件类型
        if not pdf_file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "文件必须是PDF格式"}), 400
        
        # 创建临时文件保存上传的PDF
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            pdf_file.save(temp_pdf.name)
            temp_pdf_path = temp_pdf.name
        
        try:
            # 生成NC程序
            nc_program = generate_nc_from_pdf(temp_pdf_path, user_description, scale)
            
            # 创建临时文件保存NC程序
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.nc') as temp_nc:
                temp_nc.write(nc_program)
                temp_nc_path = temp_nc.name
            
            # 返回NC程序内容和下载链接
            return jsonify({
                "status": "success",
                "nc_program": nc_program,
                "nc_file_path": temp_nc_path,
                "message": "NC程序生成成功"
            })
            
        finally:
            # 删除临时PDF文件
            os.unlink(temp_pdf_path)
    
    except Exception as e:
        return jsonify({"error": f"生成NC程序时发生错误: {str(e)}"}), 500


@app.route('/download_nc/<path:file_path>')
def download_nc(file_path):
    """下载生成的NC文件"""
    try:
        # 安全验证：确保文件路径在临时目录中，防止路径遍历攻击
        import tempfile
        temp_dir = tempfile.gettempdir()
        resolved_path = os.path.abspath(file_path)
        if not resolved_path.startswith(temp_dir):
            return jsonify({"error": "非法文件路径"}), 400
        
        # 验证文件是否存在且为.nc文件
        if not os.path.exists(resolved_path) or not resolved_path.endswith('.nc'):
            return jsonify({"error": "文件不存在或格式不正确"}), 400
            
        return send_file(resolved_path, as_attachment=True, download_name="output.nc")
    except Exception as e:
        return jsonify({"error": f"下载文件时发生错误: {str(e)}"}), 500


@app.route('/api/generate', methods=['POST'])
def generate_api():
    """API接口，接受JSON格式的请求"""
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "请求体必须是JSON格式"}), 400
        
        pdf_content = data.get('pdf_content')
        user_description = data.get('description')
        scale = data.get('scale', 1.0)
        
        if not pdf_content or not user_description:
            return jsonify({"error": "缺少必要的参数: pdf_content, description"}), 400
        
        # 将PDF内容写入临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            # 假设pdf_content是base64编码的PDF内容
            import base64
            pdf_bytes = base64.b64decode(pdf_content)
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name
        
        try:
            # 生成NC程序
            nc_program = generate_nc_from_pdf(temp_pdf_path, user_description, scale)
            
            return jsonify({
                "status": "success",
                "nc_program": nc_program,
                "message": "NC程序生成成功"
            })
            
        finally:
            # 删除临时PDF文件
            os.unlink(temp_pdf_path)
    
    except Exception as e:
        return jsonify({"error": f"API调用失败: {str(e)}"}), 500


if __name__ == '__main__':
    # 从环境变量获取端口，如果没有则默认使用5000
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)