@echo off
echo Creating build environment...

set BUILD_DIR=C:\!AndriiShramko\inventions\SDKGOPROShramko\build_env
set SOURCE_DIR=C:\!AndriiShramko\inventions\SDKGOPROShramko\GoProControl\api\v2\v38

:: Create directories
mkdir "%BUILD_DIR%" 2>nul
mkdir "%BUILD_DIR%\data" 2>nul
mkdir "%BUILD_DIR%\logs" 2>nul

:: Copy all necessary files
echo Copying files...
copy "%SOURCE_DIR%\status_of_cameras_GUI.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\status_of_cameras_GUI.spec" "%BUILD_DIR%"
copy "%SOURCE_DIR%\utils.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\goprolist_usb_activate_time_sync_record.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\stop_record.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\goprolist_and_start_usb.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\prime_camera_sn.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\camera_cache.json" "%BUILD_DIR%\data"
copy "%SOURCE_DIR%\icon.ico" "%BUILD_DIR%"
xcopy /E /I "%SOURCE_DIR%\ico" "%BUILD_DIR%\ico"

:: Copy other dependent files
copy "%SOURCE_DIR%\read_and_write_all_settings_from_prime_to_other.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\copy_to_pc_and_scene_sorting.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\copy_to_pc.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\Turn_Off_Cameras.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\format_sd.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\sync_and_record.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\date_time_sync.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\camera_orientation_lock.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\set_preset_0.py" "%BUILD_DIR%"
copy "%SOURCE_DIR%\set_video_mode.py" "%BUILD_DIR%"

:: Copy requirements.txt
copy "%SOURCE_DIR%\requirements.txt" "%BUILD_DIR%"

echo Build environment prepared