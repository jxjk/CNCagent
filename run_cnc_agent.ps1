# 设置DeepSeek API密钥环境变量
$env:DEEPSEEK_API_KEY="sk-b306662b71a04f16a1eccfa2c63aef3f"

# 设置模型名称
$env:DEEPSEEK_MODEL="deepseek-chat"

Write-Host "已设置DEEPSEEK_API_KEY环境变量"
Write-Host "正在启动CNC Agent..."

# 运行CNC Agent
Set-Location python_cncagent
python src/main.py @args