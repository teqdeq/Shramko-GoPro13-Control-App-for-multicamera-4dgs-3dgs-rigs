import requests
import logging
from datetime import datetime
from goprolist_and_start_usb import discover_gopro_devices
import json

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def get_camera_file_list():
    """Получение полного списка файлов с камер"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Находим камеры
    devices = discover_gopro_devices()
    if not devices:
        logger.error("No GoPro devices found")
        return
    
    all_files = {}
    
    # Для каждой камеры
    for device in devices:
        ip = device["ip"]
        serial_number = device["name"].split("._gopro-web._tcp.local.")[0]
        logger.info(f"\nProcessing camera {serial_number} ({ip})")
        
        try:
            # Получаем список файлов через API
            url = f"http://{ip}:8080/gp/gpMediaList"
            response = requests.get(url, timeout=5)
            
            if response.status_code != 200:
                logger.error(f"Error getting media list: {response.status_code}")
                logger.error(f"Response: {response.text}")
                continue
            
            data = response.json()
            logger.info(f"Raw media list response: {data}")
            
            # Инициализируем структуру для этой камеры
            all_files[serial_number] = {
                'ip': ip,
                'files': [],
                'sequences': {},  # Для хранения последовательностей
                'groups': {}      # Для хранения групп
            }
            
            # Обрабатываем каждую директорию
            for directory in data.get('media', []):
                dir_name = directory.get('d', '')  # Полный путь директории (DCIM/100GOPRO)
                logger.info(f"\nProcessing directory: {dir_name}")
                
                # Обрабатываем каждый файл
                for file in directory.get('fs', []):
                    file_name = file.get('n', '').upper()
                    creation_time = datetime.fromtimestamp(int(file.get('cre', 0)))
                    size = int(file.get('s', 0))
                    group_id = file.get('g')
                    
                    logger.info(f"Found file: {file_name}")
                    logger.info(f"  Size: {size}")
                    logger.info(f"  Created: {creation_time}")
                    logger.info(f"  Group: {group_id}")
                    logger.info(f"  Raw data: {file}")
                    
                    # Определяем тип файла
                    if file_name.endswith('.MP4'):
                        file_type = 'MP4'
                    elif file_name.endswith('.JPG'):
                        file_type = 'JPG'
                    else:
                        continue
                    
                    # Информация о последовательности
                    sequence_info = None
                    if 'b' in file and 'l' in file:
                        sequence_info = {
                            'start': int(file['b']),
                            'end': int(file['l']),
                            'type': file.get('t')  # 'b' для burst
                        }
                        
                        # Генерируем все файлы в последовательности
                        if file_type == 'JPG':
                            base_name = file_name[:-7]  # Удаляем номер и расширение
                            for i in range(sequence_info['start'], sequence_info['end'] + 1):
                                seq_file_name = f"{base_name}{i:04d}.JPG"
                                
                                # Создаем запись для каждого файла в последовательности
                                seq_file_info = {
                                    'name': seq_file_name,
                                    'folder': dir_name,
                                    'size': size,  # Используем размер основного файла
                                    'time': creation_time,
                                    'type': file_type,
                                    'group_id': group_id,
                                    'sequence_info': sequence_info,
                                    'is_sequence_member': True
                                }
                                
                                # Проверяем, не добавили ли мы уже этот файл
                                if not any(f['name'] == seq_file_name for f in all_files[serial_number]['files']):
                                    all_files[serial_number]['files'].append(seq_file_info)
                                    
                                    # Если файл часть группы, добавляем в группы
                                    if group_id:
                                        if group_id not in all_files[serial_number]['groups']:
                                            all_files[serial_number]['groups'][group_id] = []
                                        all_files[serial_number]['groups'][group_id].append(seq_file_info)
                                    
                                    # Добавляем в последовательность
                                    seq_key = f"{sequence_info['start']}-{sequence_info['end']}"
                                    if seq_key not in all_files[serial_number]['sequences']:
                                        all_files[serial_number]['sequences'][seq_key] = []
                                    all_files[serial_number]['sequences'][seq_key].append(seq_file_info)
                    
                    # Добавляем основной файл, если он не часть последовательности
                    if not sequence_info or file_type == 'MP4':
                        file_info = {
                            'name': file_name,
                            'folder': dir_name,
                            'size': size,
                            'time': creation_time,
                            'type': file_type,
                            'group_id': group_id,
                            'sequence_info': sequence_info,
                            'is_sequence_member': False
                        }
                        
                        # Проверяем, не добавили ли мы уже этот файл
                        if not any(f['name'] == file_name for f in all_files[serial_number]['files']):
                            all_files[serial_number]['files'].append(file_info)
                            
                            # Если файл часть группы, добавляем в группы
                            if group_id:
                                if group_id not in all_files[serial_number]['groups']:
                                    all_files[serial_number]['groups'][group_id] = []
                                all_files[serial_number]['groups'][group_id].append(file_info)
            
            # Выводим статистику
            logger.info(f"\nStatistics for camera {serial_number}:")
            logger.info(f"Total files: {len(all_files[serial_number]['files'])}")
            logger.info(f"Groups found: {len(all_files[serial_number]['groups'])}")
            logger.info(f"Sequences found: {len(all_files[serial_number]['sequences'])}")
            
            # Выводим детали по группам
            for group_id, files in all_files[serial_number]['groups'].items():
                logger.info(f"\nGroup {group_id}:")
                for f in files:
                    logger.info(f"  - {f['name']} ({f['type']})")
            
            # Выводим детали по последовательностям
            for seq_key, files in all_files[serial_number]['sequences'].items():
                logger.info(f"\nSequence {seq_key}:")
                for f in files:
                    logger.info(f"  - {f['name']} ({f['type']})")
            
        except Exception as e:
            logger.error(f"Error processing camera {serial_number}: {e}")
    
    # Сохраняем результаты в файл для анализа
    try:
        with open('camera_files.json', 'w') as f:
            json.dump(all_files, f, indent=2, default=str)
        logger.info("\nResults saved to camera_files.json")
    except Exception as e:
        logger.error(f"Error saving results: {e}")
    
    return all_files

if __name__ == "__main__":
    get_camera_file_list() 