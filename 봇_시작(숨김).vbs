Set WshShell = CreateObject("WScript.Shell")
' 현재 스크립트가 있는 경로를 작업 폴더로 설정합니다.
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
' 터미널 창(0) 없이 백그라운드에서 백그라운드로(false) 프로그램을 실행합니다.
WshShell.Run "python.exe main.py", 0, False
