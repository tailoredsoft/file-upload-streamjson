@echo off
if "%1"=="" goto :usage
if "%1"=="?" goto :usage
if "%2"=="" goto :usage
python file_uploader.py %1 %2 -f -t -v -n
goto done


:usage
echo USAGE
echo    uploadpy script.py serialport
echo.
echo      Where 
echo         script.py  : Script file to upload as text
echo         serialport : serial port name to use
echo.
echo      Example
echo         uploadpy myapp.py COM24

:done

