import requests
import logging
from datetime import datetime
from goprolist_and_start_usb import discover_gopro_devices
import json
import re

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def validate_gopro_filename(filename):
    """Проверка формата имени файла GoPro согласно документации"""
    photo_pattern = r'^GP[A-Z]{2}\d{4}\.(JPG)$'
    video_pattern = r'^GX\d{6}\.(MP4)$'
    return bool(re.match(photo_pattern, filename) or re.match(video_pattern, filename))

def generate_group_filename(group_letters, sequence_number, is_video=False):
    """Генерация имени файла по формату из документации"""
    if is_video:
        return f"GX{sequence_number:06d}.MP4"
    else:
        return f"GP{group_letters}{sequence_number:04d}.JPG"

def get_file_type_description(type_code):
    """Получение описания типа группы файлов согласно документации GoPro"""
    type_mapping = {
        # Официальные ID из документации GoPro
        12: 'video',
        13: 'time_lapse_video',
        15: 'looping',
        16: 'single_photo',
        18: 'night_photo',
        19: 'burst_photo',
        20: 'time_lapse_photo',
        21: 'night_lapse_photo',
        24: 'time_warp_video',
        25: 'live_burst',
        26: 'night_lapse_video'
    }
    
    # Пытаемся преобразовать строковый код в число
    try:
        if isinstance(type_code, str) and type_code.isdigit():
            type_code = int(type_code)
    except (ValueError, TypeError):
        pass
        
    return type_mapping.get(type_code, 'unknown')

def get_camera_file_list():
    """Получение полного списка файлов с камер"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    devices = discover_gopro_devices()
    if not devices:
        logger.error("No GoPro devices found")
        return
    
    all_files = {}
    
    for device in devices:
        ip = device["ip"]
        serial_number = device["name"].split("._gopro-web._tcp.local.")[0]
        logger.info(f"\nProcessing camera {serial_number} ({ip})")
        
        try:
            # Проверка статуса камеры перед запросом
            status_url = f"http://{ip}:8080/gp/gpControl/status"
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code != 200:
                logger.error(f"Camera {serial_number} not ready: {status_response.status_code}")
                continue
                
            url = f"http://{ip}:8080/gp/gpMediaList"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Error getting media list: {response.status_code}")
                logger.error(f"Response: {response.text}")
                continue
            
            data = response.json()
            logger.info(f"Raw media list response: {data}")
            
            all_files[serial_number] = {
                'ip': ip,
                'files': [],
                'sequences': {},
                'groups': {},
                'group_types': {}
            }
            
            for directory in data.get('media', []):
                dir_name = directory.get('d', '')
                logger.info(f"\nProcessing directory: {dir_name}")
                
                for file in directory.get('fs', []):
                    try:
                        file_name = file.get('n', '').upper()
                        
                        # Проверяем валидность имени файла
                        if not validate_gopro_filename(file_name):
                            logger.warning(f"Invalid filename format: {file_name}")
                            continue
                        
                        creation_time = datetime.fromtimestamp(int(file.get('cre', 0)))
                        size = int(file.get('s', 0))
                        group_id = file.get('g')
                        
                        # Получаем и преобразуем тип файла
                        type_code = file.get('t')
                        if isinstance(type_code, str) and type_code.isdigit():
                            type_code = int(type_code)
                        
                        logger.info(f"Found file: {file_name}")
                        logger.info(f"  Size: {size}")
                        logger.info(f"  Created: {creation_time}")
                        logger.info(f"  Group: {group_id}")
                        logger.info(f"  Type: {get_file_type_description(type_code)}")
                        logger.info(f"  Raw data: {file}")
                        
                        # Определяем тип файла
                        is_video = file_name.startswith('GX')
                        file_type = 'MP4' if is_video else 'JPG'
                        
                        # Обработка групповых файлов
                        if 'b' in file and 'l' in file:
                            start_num = int(file['b'])
                            end_num = int(file['l'])
                            missing_numbers = file.get('m', [])
                            
                            # Получаем буквенный код группы из имени файла
                            group_letters = file_name[2:4] if not is_video else None
                            
                            # Генерируем список всех файлов в группе
                            for i in range(start_num, end_num + 1):
                                # Пропускаем удаленные файлы
                                if str(i) in missing_numbers:
                                    continue
                                    
                                group_file_name = generate_group_filename(
                                    group_letters, 
                                    i, 
                                    is_video
                                )
                                
                                file_info = {
                                    'name': group_file_name,
                                    'folder': dir_name,
                                    'size': size,
                                    'time': creation_time,
                                    'type': file_type,
                                    'group_id': group_id,
                                    'group_type': get_file_type_description(type_code),
                                    'sequence_number': i,
                                    'is_group_member': True,
                                    'is_video': is_video
                                }
                                
                                # Добавляем файл в соответствующие структуры
                                all_files[serial_number]['files'].append(file_info)
                                
                                if group_id:
                                    if group_id not in all_files[serial_number]['groups']:
                                        all_files[serial_number]['groups'][group_id] = []
                                        all_files[serial_number]['group_types'][group_id] = type_code
                                    all_files[serial_number]['groups'][group_id].append(file_info)
                        
                        # Обработка одиночных файлов
                        else:
                            file_info = {
                                'name': file_name,
                                'folder': dir_name,
                                'size': size,
                                'time': creation_time,
                                'type': file_type,
                                'group_id': None,
                                'is_group_member': False,
                                'is_video': is_video
                            }
                            all_files[serial_number]['files'].append(file_info)
                            
                    except Exception as e:
                        logger.error(f"Error processing file {file_name}: {e}")
                        continue
            
            # Выводим статистику
            logger.info(f"\nStatistics for camera {serial_number}:")
            logger.info(f"Total files: {len(all_files[serial_number]['files'])}")
            logger.info(f"Groups found: {len(all_files[serial_number]['groups'])}")
            
            # Выводим информацию о группах
            for group_id, files in all_files[serial_number]['groups'].items():
                type_id = all_files[serial_number]['group_types'].get(group_id)
                logger.info(f"\nGroup {group_id} ({get_file_type_description(type_id)}):")
                for f in files:
                    logger.info(f"  - {f['name']} ({f['type']})")
            
        except Exception as e:
            logger.error(f"Error processing camera {serial_number}: {e}")
    
    # Сохраняем результаты
    try:
        with open('camera_files.json', 'w') as f:
            json.dump(all_files, f, indent=2, default=str)
        logger.info("\nResults saved to camera_files.json")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    return all_files

if __name__ == "__main__":
    get_camera_file_list() 