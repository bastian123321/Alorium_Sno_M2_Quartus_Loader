@echo off
rem Loads a .rpd into the application slot (image 1) of a Sno M2 through Alorium's xlr8reconfig.
rem Usage: flash.bat COM3 path\to\design.rpd
rem The board must be running something that answers the loader: Alorium's image or its factory
rem image (your design reaches that with the factory_escape hold). Close the Arduino Serial Monitor first.
rem The "Was not able to handshake" message AFTER "Loading image 1 and resetting xlr8" is normal:
rem it only means the new design is not an Alorium image and cannot report a version.
if "%~2"=="" (
  echo Usage: %~nx0 COMx design.rpd
  exit /b 1
)
set TOOL=
for /d %%D in ("%LOCALAPPDATA%\Arduino15\packages\alorium\tools\xlr8reconfig\*") do set TOOL=%%D
if "%TOOL%"=="" (
  echo xlr8reconfig not found. Install the Alorium XLR8 boards package in the Arduino IDE first.
  exit /b 1
)
"%TOOL%\xlr8reconfig.exe" --port %1 --dir_path "%TOOL%/" --rpd_file "%~f2" --load_image 1 -v
