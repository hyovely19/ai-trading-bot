@echo off
chcp 65001 > nul
echo ===========================================
echo 🤖 백그라운드에서 실행중인 봇을 종료합니다...
echo ===========================================

:: (ai_quant_manager.py를 포함한 python 프로세스만 찾아서 안전하게 종료)
wmic process where "name='python.exe' and commandline like '%%ai_quant_manager.py%%'" call terminate >nul 2>&1

echo.
echo ✅ 봇이 완전히 종료되었습니다! 창을 닫으셔도 됩니다.
pause > nul
