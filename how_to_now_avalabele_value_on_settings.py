import asyncio
import aiohttp
import logging
import json
from datetime import datetime
from goprolist_and_start_usb import discover_gopro_devices

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Создаем список всех ID от 1 до 200
SETTINGS_TO_CHECK = [{"id": i, "name": f"Setting ID {i}"} for i in range(1, 201)]

# Словарь для хранения результатов только с доступными значениями
valid_settings_data = {}

async def check_setting_values(session, camera_ip, setting):
    """Проверка доступных значений для настройки"""
    try:
        # Пробуем установить некорректное значение, чтобы получить список доступных
        url = f"http://{camera_ip}:8080/gopro/camera/setting?setting={setting['id']}&option=999999"
        async with session.get(url, timeout=5) as response:
            if response.status == 403:
                error_data = await response.json()
                has_valid_data = False
                setting_data = {
                    "id": setting['id'],
                    "status_code": response.status
                }

                if 'supported_options' in error_data:
                    supported_options = error_data['supported_options']
                    if supported_options:  # Проверяем, что список не пустой
                        has_valid_data = True
                        setting_data["supported_options"] = supported_options
                        logging.info(f"\nДоступные значения для Setting ID {setting['id']}:")
                        for option in supported_options:
                            logging.info(f"  {option['display_name']} (ID: {option['id']})")

                elif 'available_options' in error_data:
                    available_options = error_data['available_options']
                    if available_options:  # Проверяем, что список не пустой
                        has_valid_data = True
                        setting_data["available_options"] = available_options
                        logging.info(f"  Available options: {available_options}")

                # Сохраняем только если есть доступные значения
                if has_valid_data:
                    valid_settings_data[setting['id']] = setting_data
                    
            elif response.status == 200:
                try:
                    current_value = await response.json()
                    if current_value is not None:  # Проверяем, что значение не None
                        setting_data = {
                            "id": setting['id'],
                            "status_code": response.status,
                            "current_value": current_value
                        }
                        valid_settings_data[setting['id']] = setting_data
                        logging.info(f"\nТекущее значение для Setting ID {setting['id']}: {current_value}")
                except:
                    pass  # Пропускаем, если не удалось разобрать ответ
            
    except Exception as e:
        logging.error(f"Error checking setting ID {setting['id']}: {e}")

def save_settings_to_file(settings_data, camera_ip):
    """Сохранение настроек в файл"""
    try:
        # Создаем структуру данных с метаданными
        output_data = {
            "metadata": {
                "camera_ip": camera_ip,
                "scan_date": datetime.now().isoformat(),
                "total_valid_settings": len(settings_data)
            },
            "settings": settings_data
        }
        
        # Сохраняем в файл
        with open('all_avalable_gopro10_value_settings.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
            
        logging.info(f"\nНайдено {len(settings_data)} настроек с доступными значениями")
        logging.info("Результаты сохранены в файл: all_avalable_gopro10_value_settings.json")
        
    except Exception as e:
        logging.error(f"Error saving settings to file: {e}")

async def main_async(devices):
    """Основная асинхронная функция"""
    try:
        if not devices:
            logging.error("No cameras found")
            return
            
        async with aiohttp.ClientSession() as session:
            for device in devices:
                camera_ip = device['ip']
                logging.info(f"\nПроверка настроек для камеры {camera_ip}")
                
                # Очищаем словарь перед новым сканированием
                valid_settings_data.clear()
                
                for setting in SETTINGS_TO_CHECK:
                    await check_setting_values(session, camera_ip, setting)
                    await asyncio.sleep(0.3)  # Пауза между запросами
                
                # Сохраняем только настройки с доступными значениями
                save_settings_to_file(valid_settings_data, camera_ip)
            
    except Exception as e:
        logging.error(f"Error in main: {e}")

def main():
    """Точка входа"""
    try:
        logging.info("Starting settings check")
        
        # Ищем камеры
        devices = discover_gopro_devices()
        
        if not devices:
            logging.error("No cameras found")
            return
            
        # Запускаем проверку
        asyncio.run(main_async(devices))
        
    except KeyboardInterrupt:
        logging.info("Check stopped by user")
    except Exception as e:
        logging.error(f"Error in main: {e}", exc_info=True)

if __name__ == "__main__":
    main()