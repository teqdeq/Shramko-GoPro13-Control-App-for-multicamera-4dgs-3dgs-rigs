from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
import asyncio
import aiohttp
import logging
from read_and_write_all_settings_from_prime_to_other_v02 import (
    USB_HEADERS, DELAYS, group_settings_by_priority, logger
)

@dataclass
class CameraResult:
    """Результат применения настроек к камере"""
    camera_ip: str
    success: bool
    settings_applied: Dict[str, bool]
    error_message: Optional[str] = None

class CameraSettingsManager:
    def __init__(self, max_concurrent_cameras: int = 50):
        self.semaphore = asyncio.Semaphore(max_concurrent_cameras)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def init_session(self):
        """Инициализация HTTP сессии"""
        if not self.session:
            self.session = aiohttp.ClientSession(headers=USB_HEADERS)

    async def close_session(self):
        """Закрытие HTTP сессии"""
        if self.session:
            await self.session.close()
            self.session = None
            
    async def verify_setting_async(self, camera_ip: str, setting_id: str, expected_value: Any) -> bool:
        """Асинхронная проверка применения настройки"""
        try:
            url = f"http://{camera_ip}:8080/gp/gpControl/status"
            async with self.session.get(url) as response:
                if response.status == 200:
                    status = await response.json()
                    current_value = status.get('settings', {}).get(setting_id)
                    return current_value == expected_value
                return False
        except Exception as e:
            logger.error(f"Failed to verify setting: {e}")
            return False

    async def apply_setting_async(
        self, 
        camera_ip: str, 
        setting_id: str, 
        value: Any,
        progress_callback: Callable
    ) -> bool:
        """Асинхронное применение одной настройки"""
        try:
            url = f"http://{camera_ip}:8080/gp/gpControl/setting/{setting_id}/{value}"
            async with self.session.get(url) as response:
                if response.status == 200:
                    # Проверяем применение настройки
                    if await self.verify_setting_async(camera_ip, setting_id, value):
                        progress_callback("log", f"✅ Camera {camera_ip}: Set {setting_id}={value}")
                        return True
                    else:
                        progress_callback("log", f"⚠️ Camera {camera_ip}: Setting {setting_id}={value} verification failed")
                        return False
                else:
                    progress_callback("log", f"❌ Camera {camera_ip}: Failed to set {setting_id}={value} (Status: {response.status})")
                    return False
        except Exception as e:
            progress_callback("log", f"❌ Camera {camera_ip}: Error setting {setting_id}={value}: {str(e)}")
            return False

    async def apply_settings_to_camera(
        self, 
        camera_ip: str, 
        settings: Dict[str, Any],
        progress_callback: Callable
    ) -> CameraResult:
        """Применение всех настроек к одной камере"""
        async with self.semaphore:
            try:
                result = CameraResult(
                    camera_ip=camera_ip,
                    success=True,
                    settings_applied={}
                )

                # Группируем настройки по приоритетам
                grouped_settings = group_settings_by_priority(settings)
                
                # Применяем настройки по группам
                for priority_group in ['system', 'core', 'features', 'optional']:
                    if priority_group not in grouped_settings:
                        continue
                        
                    progress_callback("log", f"\nCamera {camera_ip}: Applying {priority_group} settings...")
                    
                    for setting_id, value in grouped_settings[priority_group].items():
                        success = await self.apply_setting_async(camera_ip, setting_id, value, progress_callback)
                        result.settings_applied[setting_id] = success
                        
                        if not success:
                            result.success = False
                        
                        # Применяем задержки
                        if priority_group == 'system':
                            await asyncio.sleep(DELAYS['mode'])
                        else:
                            await asyncio.sleep(DELAYS['standard'])
                
                return result
                
            except Exception as e:
                error_msg = f"Error applying settings to camera {camera_ip}: {str(e)}"
                logger.error(error_msg)
                return CameraResult(
                    camera_ip=camera_ip,
                    success=False,
                    settings_applied={},
                    error_message=error_msg
                )

    async def apply_settings_to_all_cameras(
        self,
        cameras: List[Dict[str, str]],
        settings: Dict[str, Any],
        progress_callback: Callable
    ) -> List[CameraResult]:
        """Асинхронное применение настроек ко всем камерам"""
        await self.init_session()
        try:
            tasks = []
            for camera in cameras:
                task = self.apply_settings_to_camera(
                    camera_ip=camera['ip'],
                    settings=settings,
                    progress_callback=progress_callback
                )
                tasks.append(task)
            
            return await asyncio.gather(*tasks)
            
        finally:
            await self.close_session()

    @classmethod
    def apply_settings_sync(
        cls,
        cameras: List[Dict[str, str]],
        settings: Dict[str, Any],
        progress_callback: Callable
    ) -> List[CameraResult]:
        """Синхронная обертка для асинхронного применения настроек"""
        async def _run():
            manager = cls()
            return await manager.apply_settings_to_all_cameras(cameras, settings, progress_callback)
            
        return asyncio.run(_run()) 