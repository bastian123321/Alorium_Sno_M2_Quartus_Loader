@echo off
rem Puts one of Alorium's Sno M2 images back into the application slot.
rem Usage: restore_alorium.bat COM3 [16 | 32 | 64 | r3195]
rem   16 (default), 32, 64 = the r3317 image for that FPGA clock; r3195 = the older 16 MHz image.
rem The board must be running the factory image (hold the factory_escape button combination).
set TOOL=
for /d %%D in ("%LOCALAPPDATA%\Arduino15\packages\alorium\tools\xlr8reconfig\*") do set TOOL=%%D
set IMGDIR=
for /d %%D in ("%LOCALAPPDATA%\Arduino15\packages\alorium\hardware\avr\*") do set IMGDIR=%%D\fpga_images
if "%TOOL%"=="" (
  echo xlr8reconfig not found. Install the Alorium XLR8 boards package in the Arduino IDE first.
  exit /b 1
)
set IMG=%IMGDIR%\snom2_c16_oDefault_u16__x0F_p0_q6_n15_s12_f1__svn3317.rpd
if "%2"=="32" set IMG=%IMGDIR%\snom2_c32_oDefault_u16__x0F_p0_q6_n15_s12_f1__svn3317.rpd
if "%2"=="64" set IMG=%IMGDIR%\snom2_c64_oDefault_u16__x0F_p0_q6_n15_s12_f1__svn3317.rpd
if "%2"=="r3195" set IMG=%IMGDIR%\snom2_c16_oDefault_u16_x0F_svn3195.rpd
echo Image: %IMG%
"%TOOL%\xlr8reconfig.exe" --port %1 --dir_path "%TOOL%/" --rpd_file "%IMG%" --load_image 1 -v
