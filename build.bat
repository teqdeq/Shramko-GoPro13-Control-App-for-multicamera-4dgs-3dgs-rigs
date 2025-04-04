@echo off
cd /d "%~dp0"

REM Clean up the previous build
if exist "build_env" rmdir /s /q build_env

REM Create directories if they do not exist
mkdir build_env
mkdir build_env\data
mkdir build_env\logs

REM Copy necessary files
copy icon.ico build_env\
copy camera_cache.json build_env\data\
xcopy /E /I ico build_env\ico

REM Build the application
pyinstaller --workpath build_env\build --distpath build_env\dist status_of_cameras_GUI.spec

REM Copy additional files to the directory with the built application
copy goprolist_usb_activate_time_sync_record.py build_env\dist\status_of_cameras_GUI\
copy stop_record.py build_env\dist\status_of_cameras_GUI\
copy prime_camera_sn.py build_env\dist\status_of_cameras_GUI\
copy goprolist_and_start_usb.py build_env\dist\status_of_cameras_GUI\
copy utils.py build_env\dist\status_of_cameras_GUI\
copy date_time_sync.py build_env\dist\status_of_cameras_GUI\
copy set_preset_0.py build_env\dist\status_of_cameras_GUI\
copy set_video_mode.py build_env\dist\status_of_cameras_GUI\
copy read_and_write_all_settings_from_prime_to_other.py build_env\dist\status_of_cameras_GUI\

REM Create necessary directories in the built application
mkdir build_env\dist\status_of_cameras_GUI\data
mkdir build_env\dist\status_of_cameras_GUI\logs

echo Build complete!
pause