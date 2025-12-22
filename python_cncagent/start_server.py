"""
Flask API服务，提供PDF到NC程序的Web接口
"""
import os
import json
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import tempfile
from src.main import generate_nc_from_pdf


app = Flask(__name__)
CORS(app)  # 允许跨域请求


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
        return send_file(file_path, as_attachment=True, download_name="output.nc")
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