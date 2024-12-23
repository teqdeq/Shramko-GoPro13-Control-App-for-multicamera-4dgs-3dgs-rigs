import os
import sys
import shutil
from pathlib import Path
import subprocess
import pkg_resources

def get_project_root() -> Path:
    """Получить корневой каталог проекта"""
    return Path(__file__).parent

def get_build_dir() -> Path:
    """Получить каталог для сборки"""
    return get_project_root().parent / 'build_env'

def clean_build_dir() -> None:
    """Очистка каталога сборки"""
    build_dir = get_build_dir()
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)

def copy_project_files() -> None:
    """Копирование файлов проекта в каталог сборки"""
    src_dir = get_project_root()
    build_dir = get_build_dir()
    
    # Копируем все .py файлы
    for py_file in src_dir.glob('*.py'):
        shutil.copy2(py_file, build_dir)
    
    # Копируем каталог с иконками
    ico_dir = src_dir / 'ico'
    if ico_dir.exists():
        shutil.copytree(ico_dir, build_dir / 'ico')

def create_spec_file() -> None:
    """Создание spec файла для PyInstaller"""
    build_dir = get_build_dir()
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{build_dir / "Gopro_Gui_interfase_Pyqt5.py"}'],
    pathex=[r'{build_dir}'],
    binaries=[],
    datas=[
        (r'{build_dir / "ico"}', 'ico'),
    ],
    hiddenimports=[
        'zeroconf._utils.ipaddress',
        'zeroconf._services.info',
        'zeroconf._core',
        'zeroconf._engine',
        'zeroconf._listener',
        'zeroconf._handlers',
        'zeroconf._handlers.answers',
        'zeroconf._handlers.browser',
        'zeroconf._handlers.cache',
        'zeroconf._handlers.incoming',
        'zeroconf._handlers.outgoing',
        'zeroconf._handlers.query',
        'zeroconf._handlers.record_manager',
        'zeroconf._updates',
        'zeroconf._services.browser',
        'zeroconf._services.registry',
        'zeroconf._services.info',
        'zeroconf._utils',
        'zeroconf._utils.name',
        'zeroconf._utils.time',
        'zeroconf._utils.net',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='GoPro_Control',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{build_dir / "ico/icon.ico"}',
)
'''
    
    spec_file = build_dir / 'GoPro_Control.spec'
    spec_file.write_text(spec_content, encoding='utf-8')

def build_exe() -> None:
    """Сборка exe файла"""
    build_dir = get_build_dir()
    spec_file = build_dir / 'GoPro_Control.spec'
    
    # Запуск PyInstaller
    subprocess.run([
        'pyinstaller',
        '--clean',
        '--workpath', str(build_dir / 'build'),
        '--distpath', str(build_dir / 'dist'),
        str(spec_file)
    ], check=True)

def main() -> int:
    """Основная функция сборки"""
    try:
        print("Начало сборки приложения...")
        
        # Очистка каталога сборки
        print("Очистка каталога сборки...")
        clean_build_dir()
        
        # Копирование файлов
        print("Копирование файлов проекта...")
        copy_project_files()
        
        # Создание spec файла
        print("Создание spec файла...")
        create_spec_file()
        
        # Сборка exe
        print("Сборка exe файла...")
        build_exe()
        
        print("Сборка успешно завершена!")
        return 0
        
    except Exception as e:
        print(f"Ошибка при сборке: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 