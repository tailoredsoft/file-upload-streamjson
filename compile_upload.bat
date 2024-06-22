@echo off
if "%1"=="" goto usage
if "%1"=="?" goto usage
if exist "%1" goto no_ext
if "%2"=="" goto no_port

echo ======================================================================
echo Formatting FFS, compiling and downloading %1.py ...
echo.
if not exist "%1.py" goto not_exist
python mp_loader.py %1.py %2 -f %3 %4 %5 %6 %7 %8 %9  
echo.
echo Done
echo ======================================================================
goto done

:not_exist
echo FAIL: File %1.py does not exist
echo .
goto :end

:no_ext
echo FAIL: Remove .py extension from appname in the command line
echo .
goto :end

:no_port
echo FAIL: Serial port name not specified
echo .
goto :end

:usage
echo USAGE
echo    compile_upload appname serialport
echo.
echo.     Do not supply the .py extension as it is added automatically
echo.     by this batch file to create the compiled file with .mpy extension
echo.
echo WHERE
echo   appname   : Application name WITHOUT the .py extension
echo   serialport: Serial port to use to upload.
echo.
echo Example:  upload appname COM42
echo.
goto end

:done

:end
