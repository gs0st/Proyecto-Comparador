@echo off
REM Genera dist\Comparador-Linac.exe  (requiere Python 3.10+ instalado y en el PATH)
python -m venv .venv || goto :err
call .venv\Scripts\activate.bat || goto :err
python -m pip install --upgrade pip || goto :err
pip install -r requirements.txt pyinstaller || goto :err
python tests\run_tests.py || goto :err
pyinstaller --noconfirm comparador.spec || goto :err
xcopy /E /I /Y ejemplos dist\ejemplos >nul
copy /Y LEEME.md dist\LEEME.md >nul
echo.
echo Listo: dist\Comparador-Linac.exe
exit /b 0
:err
echo.
echo Fallo la construccion. Revise el mensaje de arriba.
exit /b 1
