@echo off
rem WenQuest CAD launcher (installer build): set conda env paths ourselves instead of pixi, then start FreeCAD.exe
setlocal
set "WQ=%~dp0"
set "CONDA_PREFIX=%WQ%env"
set "PATH=%CONDA_PREFIX%;%CONDA_PREFIX%\Library\mingw-w64\bin;%CONDA_PREFIX%\Library\usr\bin;%CONDA_PREFIX%\Library\bin;%CONDA_PREFIX%\Scripts;%CONDA_PREFIX%\bin;%PATH%"
set "PYTHONHOME=%CONDA_PREFIX%"
set "PYTHONUTF8=1"
rem 11-22: Qt plugins by path (qt6.conf is made relative by relocate.ps1; this is a second safety net)
set "QT_PLUGIN_PATH=%CONDA_PREFIX%\Library\lib\qt6\plugins"
if exist "%CONDA_PREFIX%\Library\bin\ccx.exe" set "FAP_CCX=%CONDA_PREFIX%\Library\bin\ccx.exe"
if exist "%CONDA_PREFIX%\etc\conda\activate.d" for %%f in ("%CONDA_PREFIX%\etc\conda\activate.d\*.bat") do call "%%f" >nul 2>&1
if /i "%~1"=="--cmd" goto cmdline
start "" "%CONDA_PREFIX%\Library\bin\FreeCAD.exe" %*
goto :eof
:cmdline
shift
"%CONDA_PREFIX%\Library\bin\FreeCADCmd.exe" %1 %2 %3 %4 %5 %6 %7 %8 %9
