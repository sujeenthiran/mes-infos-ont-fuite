@echo off
chcp 65001 >nul
title Mes infos ont fuite ?
cd /d "%~dp0"

echo.
echo   ==============================================
echo      MES INFOS ONT FUITE ?   - demarrage...
echo   ==============================================
echo.

call :trouver_python
if defined PY goto lancer

echo   Python n'est pas installe sur ce PC (il est gratuit et officiel).
echo.
where winget >nul 2>&1
if errorlevel 1 goto manuel
choice /c ON /n /m "  Veux-tu que je l'installe automatiquement maintenant ? [O = oui, N = non] "
if errorlevel 2 goto manuel
echo.
echo   Installation de Python en cours (1 a 3 minutes)...
winget install -e --id Python.Python.3.12 --scope user --accept-package-agreements --accept-source-agreements
call :trouver_python
if defined PY goto lancer
echo.
echo   Python est installe. Ferme cette fenetre et relance Lancer.bat.
pause
exit /b 0

:manuel
echo.
echo   1. Va sur https://www.python.org/downloads/ et clique sur "Download Python".
echo   2. Pendant l'installation, COCHE la case "Add python.exe to PATH".
echo   3. Relance ensuite ce fichier Lancer.bat.
echo.
start "" "https://www.python.org/downloads/"
pause
exit /b 1

:lancer
%PY% mes_infos_ont_fuite.py %*
if errorlevel 1 (
  echo.
  echo   Un probleme est survenu. Lis le message ci-dessus.
  pause
)
exit /b 0

:trouver_python
set "PY="
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1 && set "PY=py -3" && goto :eof
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1 && set "PY=python" && goto :eof
for %%P in ("%LOCALAPPDATA%\Programs\Python\Launcher\py.exe" "%WINDIR%\py.exe") do (
  if exist %%P set "PY="%%~P" -3" && goto :eof
)
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do (
  if exist "%%~D\python.exe" set "PY="%%~D\python.exe"" && goto :eof
)
goto :eof
