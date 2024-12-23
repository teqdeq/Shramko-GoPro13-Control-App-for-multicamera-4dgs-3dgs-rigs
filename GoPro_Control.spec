# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['Gopro_Gui_interfase_Pyqt5.py'],
    pathex=[],
    binaries=[],
    datas=[('data', 'data'), ('utils.py', '.'), ('goprolist_and_start_usb.py', '.'), ('date_time_sync.py', '.'), ('recording.py', '.'), ('stop_record.py', '.'), ('set_preset_0.py', '.'), ('read_and_write_all_settings_from_prime_to_other.py', '.'), ('format_sd.py', '.'), ('Turn_Off_Cameras.py', '.'), ('copy_to_pc_and_scene_sorting.py', '.'), ('prime_camera_sn.py', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='GoPro_Control',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='GoPro_Control',
)
