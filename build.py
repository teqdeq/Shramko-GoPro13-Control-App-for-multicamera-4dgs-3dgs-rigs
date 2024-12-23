import PyInstaller.__main__
import os
import shutil
from pathlib import Path

def prepare_build_env():
    """Подготовка окружения для сборки"""
    # Получаем абсолютные пути
    current_dir = Path.cwd()
    build_env = current_dir / 'build_env'
    
    # Создаем структуру каталогов с абсолютными путями
    build_dirs = [
        build_env,
        build_env / 'build',
        build_env / 'dist',
        build_env / 'data',
    ]
    
    for dir_path in build_dirs:
        dir_path.mkdir(exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Копируем необходимые файлы с проверкой путей
    data_src = current_dir / 'data'
    data_dst = build_env / 'data'
    
    if data_src.exists():
        if data_dst.exists():
            shutil.rmtree(data_dst)
        shutil.copytree(data_src, data_dst)
        print(f"Copied data from {data_src} to {data_dst}")
    else:
        print(f"Warning: Source data directory not found at {data_src}")

def clean_dist():
    """Очистка папок dist и build"""
    for dir_name in ['build_env/dist', 'build_env/build']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)

def create_portable_exe():
    """Создание портативного exe-файла"""
    # Подготавливаем окружение
    prepare_build_env()
    
    # Получаем абсолютные пути
    current_dir = Path.cwd()
    build_env = current_dir / 'build_env'
    data_dir = build_env / 'data'
    
    # Проверяем и копируем иконку
    icon_path = current_dir / 'icon.ico'
    if not icon_path.exists():
        icon_path = current_dir / 'ico' / 'icon.ico'
    if not icon_path.exists():
        print("Warning: Icon file not found, using default")
        icon_arg = []
    else:
        icon_arg = [f'--icon={str(icon_path)}']
    
    # Формируем список файлов для добавления
    files_to_add = [
        'utils.py',
        'goprolist_and_start_usb.py',
        'date_time_sync.py',
        'recording.py',
        'stop_record.py',
        'set_preset_0.py',
        'read_and_write_all_settings_from_prime_to_other.py',
        'format_sd.py',
        'Turn_Off_Cameras.py',
        'copy_to_pc_and_scene_sorting.py',
        'prime_camera_sn.py',
        'status_of_cameras.py',
        'goprolist_usb_activate_time_sync.py',
        'goprolist_usb_activate_time_sync_record.py',
        'set_video_mode.py',
        'camera_orientation_lock.py',
        'sync_and_record.py',
        'sleep.py',
        'copy_to_pc.py',
    ]
    
    # Формируем параметры для PyInstaller
    pyinstaller_args = [
        'Gopro_Gui_interfase_Pyqt5.py',
        '--name=GoPro_Control',
        '--onefile',
        '--windowed',
        '--runtime-tmpdir=.',
        '--collect-all=zeroconf',
    ]
    
    # Добавляем data директорию
    if data_dir.exists():
        pyinstaller_args.append(f'--add-data={str(data_dir)};data')
    else:
        print("Creating empty data directory...")
        data_dir.mkdir(exist_ok=True)
        pyinstaller_args.append(f'--add-data={str(data_dir)};data')
    
    # Добавляем иконку если она есть
    pyinstaller_args.extend(icon_arg)
    
    # Добавляем файлы с абсолютными путями
    for file in files_to_add:
        file_path = current_dir / file
        if file_path.exists():
            pyinstaller_args.append(f'--add-binary={str(file_path)};.')
        else:
            print(f"Warning: File not found: {file_path}")
    
    # Добавляем каталог с иконками
    ico_dir = current_dir / 'ico'
    if ico_dir.exists():
        pyinstaller_args.append(f'--add-binary={str(ico_dir)};ico')
    
    # Добавляем остальные параметры
    pyinstaller_args.extend([
        '--clean',
        '--noconfirm',
        '--log-level=INFO',
        f'--workpath={str(build_env / "build")}',
        f'--distpath={str(build_env / "dist")}',
        f'--specpath={str(build_env)}'
    ])
    
    # Запускаем PyInstaller
    PyInstaller.__main__.run(pyinstaller_args)

def main():
    try:
        print("Cleaning previous builds...")
        clean_dist()
        
        print("Creating portable exe...")
        create_portable_exe()
        
        print("Build completed successfully!")
        print("Executable can be found in: build_env/dist/GoPro_Control.exe")
        
    except Exception as e:
        print(f"Error during build: {e}")
        return 1
    return 0

if __name__ == "__main__":
    exit(main()) 