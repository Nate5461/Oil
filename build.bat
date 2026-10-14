@echo off
rem Builds dist\oilApp.exe - run from this folder on a Windows machine with Python installed
python -m pip install -r requirements.txt || exit /b 1
python -m PyInstaller --noconfirm oilApp.spec || exit /b 1
echo.
echo Done: send dist\oilApp.exe
