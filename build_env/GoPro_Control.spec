# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\build_env\\data', 'data')]
binaries = [('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\utils.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\goprolist_and_start_usb.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\date_time_sync.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\recording.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\stop_record.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\set_preset_0.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\read_and_write_all_settings_from_prime_to_other.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\format_sd.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\Turn_Off_Cameras.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\copy_to_pc_and_scene_sorting.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\prime_camera_sn.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\status_of_cameras.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\goprolist_usb_activate_time_sync.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\goprolist_usb_activate_time_sync_record.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\set_video_mode.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\camera_orientation_lock.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\sync_and_record.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\sleep.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\copy_to_pc.py', '.'), ('C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\ico', 'ico')]
hiddenimports = []
tmp_ret = collect_all('zeroconf')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['..\\Gopro_Gui_interfase_Pyqt5.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name='GoPro_Control',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir='.',
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['C:\\!AndriiShramko\\inventions\\SDKGOPROShramko\\GoProControl\\api\\v2\\v39\\icon.ico'],
)
