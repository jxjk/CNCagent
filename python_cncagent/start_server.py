"""
Flask API服务，提供PDF到NC程序的Web接口

使用方法:
  python start_server.py        # 启动Web服务器 (默认端口5000)
  PORT=8080 python start_server.py  # 使用环境变量指定端口

统一启动器 (推荐):
  python start_unified.py web   # 仅启动Web服务器
  python start_unified.py       # 同时启动GUI和Web服务器
"""
import os

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # 如果没有安装dotenv则跳过

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
    <title>CNC Agent - 2D/3D图纸到NC程序转换器</title>
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
            max-width: 1200px;
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
        .file-input-group {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            align-items: center;
        }
        .file-input-container {
            flex: 1;
            min-width: 200px;
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
        .optional-field {
            opacity: 0.7;
            font-size: 0.9em;
        }
        .flex-container {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
        }
        .flex-item {
            flex: 1;
            min-width: 300px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>CNC Agent - 2D/3D图纸到NC程序转换器</h1>
        
        <div class="instructions">
            <h3>使用说明</h3>
            <ul>
                <li>同时支持上传2D图纸（PDF、图片）和3D模型（STL、STEP等）</li>
                <li>在描述框中输入加工要求（如：请加工一个直径10mm的孔，深度5mm）</li>
                <li>2D图纸和3D模型均为可选，但至少需要提供加工描述</li>
                <li>点击"生成NC程序"按钮</li>
            </ul>
        </div>
        
        <form id="cncForm" enctype="multipart/form-data">
            <div class="flex-container">
                <div class="flex-item">
                    <div class="form-group">
                        <label for="pdfFile">2D图纸文件 (可选):</label>
                        <div class="optional-field">支持PDF、JPG、PNG等格式</div>
                        <input type="file" id="pdfFile" name="pdf" accept=".pdf,.jpg,.jpeg,.png,.bmp,.tiff">
                    </div>
                    
                    <div class="form-group">
                        <label for="model3DFile">3D模型文件 (可选):</label>
                        <div class="optional-field">支持STL、STEP、IGES、OBJ等格式</div>
                        <input type="file" id="model3DFile" name="model_3d" accept=".stl,.step,.stp,.igs,.iges,.obj,.ply">
                    </div>
                </div>
                
                <div class="flex-item">
                    <div class="form-group">
                        <label for="description">加工描述 (必填):</label>
                        <textarea id="description" name="description" placeholder="例如：请加工一个直径10mm的孔，深度5mm，使用铣削加工" required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="scale">图纸比例尺 (可选):</label>
                        <input type="number" id="scale" name="scale" value="1.0" min="0.001" max="100" step="0.1">
                    </div>
                </div>
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
            
            // 检查是否至少提供了描述
            const description = formData.get('description');
            if (!description || !description.trim()) {
                resultDiv.innerHTML = '<div class="error">错误: 加工描述是必填项</div>';
                return;
            }
            
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
    """根据上传的2D/3D文件和用户描述生成NC程序"""
    try:
        # 检查是否提供了用户描述（这是必须的）
        if 'description' not in request.form:
            return jsonify({"error": "缺少用户描述"}), 400
        
        # 获取用户描述并确保正确处理中文字符
        user_description = request.form['description']
        if isinstance(user_description, bytes):
            user_description = user_description.decode('utf-8')
        
        # 获取比例尺
        scale = float(request.form.get('scale', 1.0))
        
        # 初始化文件路径
        pdf_path = None
        model_3d_path = None
        
        # 处理2D文件（PDF或图像）
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file.filename != '':  # 如果文件名不为空
                # 验证文件类型
                allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
                file_ext = os.path.splitext(pdf_file.filename.lower())[1]
                if file_ext not in allowed_extensions:
                    return jsonify({"error": f"不支持的2D文件格式: {file_ext}。支持的格式: {', '.join(allowed_extensions)}"}), 400
                
                # 创建临时文件保存上传的2D文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                    pdf_file.save(temp_file.name)
                    pdf_path = temp_file.name
        
        # 处理3D模型文件
        if 'model_3d' in request.files:
            model_3d_file = request.files['model_3d']
            if model_3d_file.filename != '':  # 如果文件名不为空
                # 验证3D模型文件类型
                allowed_extensions = {'.stl', '.step', '.stp', '.igs', '.iges', '.obj', '.ply', '.off', '.gltf', '.glb'}
                file_ext = os.path.splitext(model_3d_file.filename.lower())[1]
                if file_ext not in allowed_extensions:
                    return jsonify({"error": f"不支持的3D模型格式: {file_ext}。支持的格式: {', '.join(allowed_extensions)}"}), 400
                
                # 创建临时文件保存上传的3D模型
                with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
                    model_3d_file.save(temp_file.name)
                    model_3d_path = temp_file.name
        
        # 检查是否至少提供了2D文件、3D文件或用户描述中的信息
        if not pdf_path and not model_3d_path:
            # 如果没有提供任何图纸文件，只用用户描述
            if not user_description.strip():
                return jsonify({"error": "必须提供2D图纸、3D模型或加工描述之一"}), 400
        
        try:
            # 从环境变量获取API配置
            import os
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
            model = os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'deepseek-chat'))
            
            # 生成NC程序 - 使用main模块中的函数
            from src.main import generate_nc_from_pdf
            
            nc_program = generate_nc_from_pdf(
                pdf_path=pdf_path,  # 可能为None
                user_description=user_description,
                scale=scale,
                model_3d_path=model_3d_path,  # 可能为None
                api_key=api_key,
                model=model
            )
            
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
            # 删除临时文件
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)
            if model_3d_path and os.path.exists(model_3d_path):
                os.unlink(model_3d_path)
    
    except Exception as e:
        # 确保临时文件被清理
        if 'pdf_path' in locals() and pdf_path and os.path.exists(pdf_path):
            try:
                os.unlink(pdf_path)
            except:
                pass
        if 'model_3d_path' in locals() and model_3d_path and os.path.exists(model_3d_path):
            try:
                os.unlink(model_3d_path)
            except:
                pass
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
        # 确保用户描述正确处理中文字符
        if isinstance(user_description, bytes):
            user_description = user_description.decode('utf-8')
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
            # 从环境变量获取API配置
            import os
            api_key = os.getenv('DEEPSEEK_API_KEY') or os.getenv('OPENAI_API_KEY')
            model = os.getenv('DEEPSEEK_MODEL', os.getenv('OPENAI_MODEL', 'deepseek-chat'))
            
            # 生成NC程序
            nc_program = generate_nc_from_pdf(
                user_description=user_description,
                pdf_path=temp_pdf_path,
                scale=scale,
                api_key=api_key,
                model=model
            )
            
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