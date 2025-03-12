import requests
import logging
from pathlib import Path
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_file_size_from_camera(camera_ip: str, file_name: str) -> int:
    """Получение размера файла с камеры через HEAD запрос"""
    try:
        # Пробуем разные пути к файлу
        paths = [
            f"http://{camera_ip}:8080/videos/DCIM/100GOPRO/{file_name}",
            f"http://{camera_ip}:8080/videos/DCIM/{file_name}"
        ]
        
        for url in paths:
            try:
                head_response = requests.head(url, timeout=5)
                if head_response.status_code == 200:
                    size = int(head_response.headers.get('content-length', 0))
                    logger.info(f"Got file size from camera for {file_name}: {size} bytes (via HEAD request to {url})")
                    return size
            except Exception as e:
                logger.debug(f"Failed to get size from {url}: {e}")
                continue
                
        logger.warning(f"Failed to get file size from camera for {file_name} using all paths")
        return 0
        
    except Exception as e:
        logger.error(f"Error getting file size from camera: {e}")
        return 0

def get_file_size_from_media_list(camera_ip: str, file_name: str) -> int:
    """Получение размера файла из списка медиа"""
    try:
        # Получаем список медиа
        url = f"http://{camera_ip}:8080/gp/gpMediaList"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        
        media_list = response.json().get('media', [])
        
        # Ищем файл в списке
        for directory in media_list:
            for file in directory.get('fs', []):
                if file.get('n', '').upper() == file_name.upper():
                    size = int(file.get('s', 0))
                    logger.info(f"Got file size from media list for {file_name}: {size} bytes")
                    return size
                    
        logger.warning(f"File {file_name} not found in media list")
        return 0
        
    except Exception as e:
        logger.error(f"Error getting file size from media list: {e}")
        return 0

def get_local_file_size(file_path: Path) -> int:
    """Получение размера локального файла"""
    try:
        if file_path.exists():
            size = file_path.stat().st_size
            logger.info(f"Local file size for {file_path.name}: {size} bytes")
            return size
        logger.warning(f"Local file {file_path} does not exist")
        return 0
    except Exception as e:
        logger.error(f"Error getting local file size: {e}")
        return 0

def download_file(camera_ip: str, file_name: str, target_dir: Path) -> bool:
    """Загрузка файла с камеры"""
    try:
        url = f"http://{camera_ip}:8080/videos/DCIM/100GOPRO/{file_name}"
        target_path = target_dir / file_name
        
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    
        logger.info(f"Successfully downloaded {file_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error downloading file: {e}")
        return False

def test_file_size_measurement(camera_ip: str, file_name: str, target_dir: Path):
    """Тестирование измерения размера файла"""
    logger.info(f"\nTesting file size measurement for {file_name}")
    logger.info("-" * 50)
    
    # 1. Получаем размер из списка медиа
    media_list_size = get_file_size_from_media_list(camera_ip, file_name)
    logger.info(f"Size from media list: {media_list_size} bytes")
    
    # 2. Получаем размер через HEAD запрос
    head_size = get_file_size_from_camera(camera_ip, file_name)
    logger.info(f"Size from HEAD request: {head_size} bytes")
    
    # 3. Загружаем файл и проверяем его размер
    if download_file(camera_ip, file_name, target_dir):
        local_size = get_local_file_size(target_dir / file_name)
        logger.info(f"Size of downloaded file: {local_size} bytes")
        
        # Сравниваем размеры
        logger.info("\nSize comparison:")
        logger.info(f"Media list vs HEAD: {'Match' if media_list_size == head_size else 'Mismatch'}")
        logger.info(f"Media list vs Local: {'Match' if media_list_size == local_size else 'Mismatch'}")
        logger.info(f"HEAD vs Local: {'Match' if head_size == local_size else 'Mismatch'}")
        
        if head_size != local_size:
            logger.warning("HEAD request size doesn't match downloaded file size!")
        if media_list_size != local_size:
            logger.warning("Media list size doesn't match downloaded file size!")
    else:
        logger.error("Failed to download file for size comparison")

def main():
    # Параметры теста
    camera_ip = "172.29.189.51"  # Измените на IP вашей камеры
    test_files = ["GPAA0177.JPG", "GX010188.MP4"]  # Тестируем фото и видео
    target_dir = Path("test_downloads")
    
    # Создаем директорию для тестов
    target_dir.mkdir(exist_ok=True)
    
    # Тестируем каждый файл
    for file_name in test_files:
        test_file_size_measurement(camera_ip, file_name, target_dir)
        logger.info("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main() 