@echo off

SET DEEPSEEK_API_KEY=sk-ca4d0ccb91b9470c99af938dcdbe88db
SET DEEPSEEK_MODEL=deepseek-chat
SET DEEPSEEK_API_BASE=https://api.deepseek.com


cd python_cncagent
python start_unified.py both-beautified

pause