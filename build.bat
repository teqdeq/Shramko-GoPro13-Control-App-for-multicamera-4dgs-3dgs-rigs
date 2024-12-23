@echo off
cd /d "%~dp0"

rem Очищаем предыдущую сборку
if exist "build_env" rmdir /s /q build_env

rem Создаем каталоги если их нет
mkdir build_env
mkdir build_env\data
mkdir build_env\logs

rem Копируем необходимые файлы
copy icon.ico build_env\
copy camera_cache.json build_env\data\
xcopy /E /I ico build_env\ico

rem Собираем приложение
pyinstaller --workpath build_env\build --distpath build_env\dist status_of_cameras_GUI.spec

rem Копируем дополнительные файлы в каталог с собранным приложением
copy goprolist_usb_activate_time_sync_record.py build_env\dist\status_of_cameras_GUI\
copy stop_record.py build_env\dist\status_of_cameras_GUI\
copy prime_camera_sn.py build_env\dist\status_of_cameras_GUI\
copy goprolist_and_start_usb.py build_env\dist\status_of_cameras_GUI\
copy utils.py build_env\dist\status_of_cameras_GUI\
copy date_time_sync.py build_env\dist\status_of_cameras_GUI\
copy set_preset_0.py build_env\dist\status_of_cameras_GUI\
copy set_video_mode.py build_env\dist\status_of_cameras_GUI\
copy read_and_write_all_settings_from_prime_to_other.py build_env\dist\status_of_cameras_GUI\

rem Создаем необходимые директории в собранном приложении
mkdir build_env\dist\status_of_cameras_GUI\data
mkdir build_env\dist\status_of_cameras_GUI\logs

echo Build complete!
pause