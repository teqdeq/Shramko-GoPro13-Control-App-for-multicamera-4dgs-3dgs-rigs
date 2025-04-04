# Copyright (c) 2024 Andrii Shramko
# Contact: zmei116@gmail.com
# LinkedIn: https://www.linkedin.com/in/andrii-shramko/
# Tags: #ShramkoVR #ShramkoCamera #ShramkoSoft
# License: This code is free to use for non-commercial projects.
# For commercial use, please contact Andrii Shramko at the above email or LinkedIn.

import os
import sys
import requests
import logging
from datetime import datetime
from pathlib import Path
from goprolist_and_start_usb import discover_gopro_devices
from prime_camera_sn import serial_number as prime_camera_sn
from utils import get_app_root, setup_logging, check_dependencies

def create_folder_structure_and_copy_files(destination_root, scene_time_threshold=5):
    """
    Copying and sorting files from cameras
    """
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        check_dependencies()
        
        destination_root = Path(destination_root)
        
        # Checking write permissions
        if not os.access(str(destination_root), os.W_OK):
            logger.error(f"No write access to destination directory: {destination_root}")
            return
            
        # Step 1: Collecting file information from cameras
        logger.info("Collecting files information from cameras...")
        devices = discover_gopro_devices()
        if not devices:
            logger.error("No GoPro devices found")
            return
            
        files_info = collect_files_info(devices)
        
        # Step 2: Checking existing files
        logger.info("Checking existing files...")
        existing_files = check_existing_files(destination_root, files_info)
        
        # Step 3: Grouping files into scenes
        logger.info("Calculating scene ranges...")
        scenes = calculate_scene_time_ranges(files_info, scene_time_threshold)
        
        # Adding detailed statistics for each scene
        for scene_idx, scene in enumerate(scenes, 1):
            mp4_files = sum(1 for f in scene['files'] if f['name'].upper().endswith('.MP4'))
            jpg_files = sum(1 for f in scene['files'] if f['name'].upper().endswith('.JPG'))
            logger.info(f"\nScene {scene_idx} statistics:")
            logger.info(f"Total files in scene: {len(scene['files'])}")
            logger.info(f"MP4 files: {mp4_files}")
            logger.info(f"JPG files: {jpg_files}")
        
        # Step 4: Creating folder structure
        logger.info("Creating scene folders...")
        scene_folders = create_scene_folders(destination_root, scenes)
        
        # Step 5: Copying files
        copied_files = []
        failed_files = []
        
        for scene_folder in scene_folders:
            logger.info(f"Processing scene: {scene_folder['name']}")
            
            for file in scene_folder['files']:
                # Let's use prefixed_name
                dest_filename = f"{file['camera']}_{file['name']}"
                
                # Let's define the destination folder depending on the file type
                if file['type'] == 'JPG' and scene_folder.get('jpg_folder'):
                    dest_folder = scene_folder['jpg_folder']
                elif file['type'] == 'GPR' and scene_folder.get('gpr_folder'):
                    dest_folder = scene_folder['gpr_folder']
                else:  # MP4 and other files remain in the scene root
                    dest_folder = scene_folder['folder']
                
                dest_path = dest_folder / dest_filename
                
                logger.info(f"Processing {file['type']} file: {dest_filename}")
                
                # Check the existing file taking the prefix into account
                if dest_path.exists():
                    actual_size = dest_path.stat().st_size
                    # Check that this file is indeed from this camera
                    if dest_path.name.startswith(f"{file['camera']}_"):
                        if actual_size == file['size']:
                            logger.info(f"File already exists with correct size: {dest_filename}")
                            copied_files.append({'camera': file['camera'], 'file': file['name'], 'type': file['type']})
                            continue
                        else:
                            logger.warning(f"Size mismatch for {dest_filename}, re-copying")
                            dest_path.unlink()
                    else:
                        # If the file exists but is from another camera, skip deletion
                        logger.info(f"Found file with same name but different camera, keeping both: {dest_filename}")
                
                try:
                    logger.info(f"Copying {dest_filename}...")
                    
                    # Creating URL taking into account the camera's folder structure
                    source_url = f"http://{files_info[file['camera']]['ip']}:8080/videos/DCIM/{file['folder']}/{file['name']}"
                    
                    # Checking file availability before copying
                    check_response = requests.head(source_url, timeout=5)
                    if check_response.status_code != 200:
                        raise Exception(f"File not accessible. Status code: {check_response.status_code}")
                    
                    success = copy_file_with_verification(
                        source_url, 
                        dest_path, 
                        file['size']
                    )
                    
                    if success:
                        copied_files.append({'camera': file['camera'], 'file': file['name'], 'type': file['type']})
                        logger.info(f"Successfully copied {file['type']} file: {dest_filename}")
                    else:
                        failed_files.append({
                            'camera': file['camera'],
                            'file': file['name'],
                            'type': file['type'],
                            'reason': 'Copy verification failed'
                        })
                        
                except Exception as e:
                    logger.error(f"Error copying {file['name']}: {e}")
                    failed_files.append({
                        'camera': file['camera'],
                        'file': file['name'],
                        'type': file['type'],
                        'reason': str(e)
                    })
        
        # After copying files, add copy statistics
        for scene_idx, scene_folder in enumerate(scene_folders, 1):
            scene_files = scene_folder['files']
            copied_in_scene = len([f for f in copied_files if any(sf['name'] == f['file'] for sf in scene_files)])
            failed_in_scene = len([f for f in failed_files if any(sf['name'] == f['file'] for sf in scene_files)])
            logger.info(f"\nScene {scene_idx} copy results:")
            logger.info(f"Successfully copied: {copied_in_scene}")
            logger.info(f"Failed to copy: {failed_in_scene}")
            logger.info(f"Already existed: {len(scene_files) - copied_in_scene - failed_in_scene}")
        
        # Step 6: Checking results
        verification_results = verify_all_files_copied(files_info, copied_files, failed_files)
        
        # Step 7: Saving the operation log
        log_copy_operation(destination_root, verification_results)
        
        # Returning results for GUI
        return {
            'status': 'success' if not failed_files else 'incomplete',
            'verification': verification_results,
            'copied': {
                'total': len(copied_files),
                'mp4': len([f for f in copied_files if f['type'] == 'MP4']),
                'jpg': len([f for f in copied_files if f['type'] == 'JPG']),
                'gpr': len([f for f in copied_files if f['type'] == 'GPR'])
            },
            'failed': {
                'total': len(failed_files),
                'mp4': len([f for f in failed_files if f['type'] == 'MP4']),
                'jpg': len([f for f in failed_files if f['type'] == 'JPG']),
                'gpr': len([f for f in failed_files if f['type'] == 'GPR'])
            },
            'total_scenes': len(scene_folders)
        }

    except Exception as e:
        logger.error(f"Unexpected error during copy operation: {e}", exc_info=True)
        if getattr(sys, 'frozen', False):
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Critical)
            msg.setText("Error during file copying")
            msg.setInformativeText(str(e))
            msg.setWindowTitle("Error")
            msg.exec_()
        raise

def verify_all_files_copied(files_info, copied_files, failed_files):
    """Verify that all files were copied"""
    verification_results = {}
    
    for serial_number, info in files_info.items():
        if 'error' in info:
            verification_results[serial_number] = {
                'status': 'ERROR',
                'reason': info['error'],
                'missing_files': []
            }
            continue
        
        # Checking each file
        missing_files = []
        for file_info in info['files']:
            # Checking the copy taking into account camera_id
            file_copied = any(
                cf['camera'] == serial_number and cf['file'] == file_info['name']
                for cf in copied_files
            )
            file_failed = any(
                ff['camera'] == serial_number and ff['file'] == file_info['name']
                for ff in failed_files
            )
            
            if not file_copied and not file_failed:
                missing_files.append(f"{serial_number}_{file_info['name']}")  # Adding prefix for clarity
        
        verification_results[serial_number] = {
            'status': 'OK' if not missing_files else 'INCOMPLETE',
            'total_files': info['total_files'],
            'copied_files': len([cf for cf in copied_files if cf['camera'] == serial_number]),
            'failed_files': len([ff for ff in failed_files if ff['camera'] == serial_number]),
            'missing_files': missing_files
        }
    
    # Outputting verification results
    print("\nVerification Results:")
    print("=" * 50)
    for serial_number, result in verification_results.items():
        print(f"\nCamera {serial_number}:")
        print(f"Status: {result['status']}")
        if result['status'] == 'ERROR':
            print(f"Error: {result['reason']}")
        else:
            print(f"Total files: {result.get('total_files', 0)}")
            print(f"Copied files: {result.get('copied_files', 0)}")
            print(f"Failed files: {result.get('failed_files', 0)}")
            if result.get('missing_files'):
                print("Missing files:")
                for file in result['missing_files']:
                    print(f"  - {file}")
    
    return verification_results

def calculate_scene_time_ranges(files_info, scene_time_threshold=5):
    """Calculate time ranges for scenes"""
    all_files = []
    for serial_number, info in files_info.items():
        if 'error' not in info:
            for file_info in info['files']:
                all_files.append({
                    'camera': serial_number,
                    'time': file_info['time'],
                    'name': file_info['name'],
                    'folder': file_info['folder'],
                    'size': file_info['size'],
                    'type': file_info['type']
                })
    
    # Sorting files by time
    all_files.sort(key=lambda x: x['time'])
    
    # Grouping files into scenes
    scenes = []
    current_scene = []
    
    for i, file in enumerate(all_files):
        if not current_scene:
            current_scene = [file]
        else:
            # Checking the time difference and belonging to the same scene
            time_diff = abs((file['time'] - current_scene[0]['time']).total_seconds())
            
            # Files belong to the same scene if:
            # 1. The time difference is less than the threshold
            # 2. Files are from different cameras
            if time_diff <= scene_time_threshold and not any(
                cf['camera'] == file['camera'] for cf in current_scene
            ):
                current_scene.append(file)
            else:
                if len(current_scene) > 0:
                    # Counting the number of files of each type in the scene
                    scene_stats = {
                        'files': current_scene,
                        'file_counts': {'MP4': 0, 'JPG': 0, 'GPR': 0},
                        'has_jpg': False,
                        'has_gpr': False,
                        'start_time': current_scene[0]['time'],
                        'end_time': current_scene[-1]['time']
                    }
                    
                    for scene_file in current_scene:
                        file_type = scene_file['type']
                        scene_stats['file_counts'][file_type] += 1
                        if file_type == 'JPG':
                            scene_stats['has_jpg'] = True
                        elif file_type == 'GPR':
                            scene_stats['has_gpr'] = True
                    
                    scenes.append(scene_stats)
                current_scene = [file]
    
    # Adding the last scene
    if current_scene:
        scene_stats = {
            'files': current_scene,
            'file_counts': {'MP4': 0, 'JPG': 0, 'GPR': 0},
            'has_jpg': False,
            'has_gpr': False,
            'start_time': current_scene[0]['time'],
            'end_time': current_scene[-1]['time']
        }
        
        for scene_file in current_scene:
            file_type = scene_file['type']
            scene_stats['file_counts'][file_type] += 1
            if file_type == 'JPG':
                scene_stats['has_jpg'] = True
            elif file_type == 'GPR':
                scene_stats['has_gpr'] = True
        
        scenes.append(scene_stats)
    
    return scenes

def create_scene_folders(destination_root, scenes):
    """Creating folder structure for scenes"""
    scene_folders = []
    used_timestamps = set()  # For tracking already used timestamps
    
    for scene_index, scene in enumerate(scenes, 1):
        # Using the shooting time from the main camera or the first available camera
        prime_file = next(
            (f for f in scene['files'] if f['camera'] == prime_camera_sn),
            scene['files'][0]
        )
        
        scene_timestamp = prime_file['time'].strftime("%Y_%m_%d_%H_%M_%S")
        
        # Checking the uniqueness of the timestamp
        if scene_timestamp in used_timestamps:
            continue
        
        used_timestamps.add(scene_timestamp)
        scene_folder_name = f"scene{scene_index:02d}_{scene_timestamp}"
        scene_folder = destination_root / scene_folder_name
        
        try:
            scene_folder.mkdir(exist_ok=True)
            logging.info(f"Created scene folder: {scene_folder}")
            
            # Creating subfolders if there are corresponding files
            jpg_folder = None
            gpr_folder = None
            
            if scene['has_jpg'] and scene['file_counts']['JPG'] > 0:
                jpg_folder = scene_folder / 'JPG'
                jpg_folder.mkdir(exist_ok=True)
                logging.info(f"Created JPG folder in scene {scene_index}: {jpg_folder}")
                
            if scene['has_gpr'] and scene['file_counts']['GPR'] > 0:
                gpr_folder = scene_folder / 'GPR'
                gpr_folder.mkdir(exist_ok=True)
                logging.info(f"Created GPR folder in scene {scene_index}: {gpr_folder}")
            
            scene_folders.append({
                'folder': scene_folder,
                'jpg_folder': jpg_folder,
                'gpr_folder': gpr_folder,
                'files': scene['files'],
                'name': scene_folder_name,
                'timestamp': scene_timestamp,
                'has_jpg': scene['has_jpg'],
                'has_gpr': scene['has_gpr'],
                'file_counts': scene['file_counts']
            })
            
            logging.info(f"Scene {scene_index} structure:")
            logging.info(f"  Total files: {sum(scene['file_counts'].values())}")
            for file_type, count in scene['file_counts'].items():
                if count > 0:
                    logging.info(f"  {file_type} files: {count}")
                    
        except Exception as e:
            logging.error(f"Error creating scene folder {scene_folder_name}: {e}")
            continue
    
    return scene_folders

def log_copy_operation(destination_root, verification_results):
    """Save the log of the copy operation"""
    log_file = destination_root / 'copy_log.txt'
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"\nCopy Operation Log - {timestamp}\n")
        f.write("=" * 50 + "\n")
        
        total_stats = {'MP4': 0, 'JPG': 0, 'GPR': 0}
        
        for serial_number, result in verification_results.items():
            f.write(f"\nCamera {serial_number}:\n")
            f.write(f"Status: {result['status']}\n")
            
            if result['status'] == 'ERROR':
                f.write(f"Error: {result['reason']}\n")
            else:
                f.write(f"Total files: {result.get('total_files', 0)}\n")
                
                # Writing statistics by file types
                for file_type in ['MP4', 'JPG', 'GPR']:
                    count = len([f for f in result.get('copied_files', []) if f['type'] == file_type])
                    if count > 0:
                        f.write(f"{file_type} files copied: {count}\n")
                        total_stats[file_type] += count
                
                if result.get('failed_files'):
                    f.write("Failed files:\n")
                    for file in result['failed_files']:
                        f.write(f"  - {file['name']} ({file['type']}): {file.get('reason', 'Unknown error')}\n")
        
        # Writing overall statistics
        f.write("\nTotal Statistics:\n")
        f.write("-" * 20 + "\n")
        for file_type, count in total_stats.items():
            if count > 0:
                f.write(f"Total {file_type} files: {count}\n")
        
        f.write("\n" + "=" * 50 + "\n")

def collect_files_info(devices):
    """Collect information about files on all cameras"""
    files_info = {}
    
    for device in devices:
        ip = device["ip"]
        serial_number = device["name"].split("._gopro-web._tcp.local.")[0]
        
        try:
            # Using the documented endpoint /gopro/media/list
            media_url = f"http://{ip}:8080/gopro/media/list"
            response = requests.get(media_url, timeout=10)
            response.raise_for_status()
            
            media_list = response.json().get("media", [])
            files_info[serial_number] = {
                'ip': ip,
                'total_files': 0,
                'files': [],
                'size': 0,
                'has_jpg': False,
                'has_gpr': False,
                'file_counts': {'MP4': 0, 'JPG': 0, 'GPR': 0}
            }
            
            # First, collect all JPG files with the RAW flag
            raw_jpgs = set()
            for media in media_list:
                for file in media.get("fs", []):
                    file_name = file.get("n", "").upper()
                    if file_name.endswith('.JPG') and bool(file.get("raw")):
                        raw_jpgs.add(file_name)
            
            # Now processing all files
            for media in media_list:
                for file in media.get("fs", []):
                    file_name = file.get("n", "").upper()
                    
                    # Determining the file type
                    if file_name.endswith('.MP4'):
                        file_type = 'MP4'
                    elif file_name.endswith('.JPG'):
                        file_type = 'JPG'
                        files_info[serial_number]['has_jpg'] = True
                    elif file_name.endswith('.GPR'):
                        file_type = 'GPR'
                        files_info[serial_number]['has_gpr'] = True
                    else:
                        continue  # Skipping unknown file types
                    
                    # Incrementing the counter for this file type
                    files_info[serial_number]['file_counts'][file_type] += 1
                    
                    # Adding file information
                    file_info = {
                        'name': file.get("n"),  # Keeping the original name
                        'folder': media.get("d"),
                        'size': int(file.get("s", "0")),
                        'time': datetime.fromtimestamp(int(file.get("cre"))),
                        'type': file_type,
                        'camera_id': serial_number,  # Adding camera_id
                        'has_gpr': file_name in raw_jpgs if file_type == 'JPG' else False
                    }
                    files_info[serial_number]['files'].append(file_info)
                    files_info[serial_number]['total_files'] += 1
                    files_info[serial_number]['size'] += file_info['size']
                    
                    # If this is a JPG with the RAW flag, add the corresponding GPR file
                    if file_type == 'JPG' and file_name in raw_jpgs:
                        gpr_name = file_name.replace('.JPG', '.GPR')
                        gpr_info = {
                            'name': gpr_name,
                            'folder': media.get("d"),
                            'size': int(file.get("s", "0")),  # Using the same size
                            'time': datetime.fromtimestamp(int(file.get("cre"))),
                            'type': 'GPR'
                        }
                        files_info[serial_number]['files'].append(gpr_info)
                        files_info[serial_number]['total_files'] += 1
                        files_info[serial_number]['size'] += gpr_info['size']
                        files_info[serial_number]['has_gpr'] = True
                        files_info[serial_number]['file_counts']['GPR'] += 1
            
            logging.info(f"Camera {serial_number}: found {files_info[serial_number]['total_files']} files")
            logging.info(f"Total size: {files_info[serial_number]['size'] / (1024*1024):.2f} MB")
            
            # Logging information about file types
            for file_type, count in files_info[serial_number]['file_counts'].items():
                if count > 0:
                    logging.info(f"Camera {serial_number}: {count} {file_type} files")
            
        except Exception as e:
            logging.error(f"Error collecting files from camera {serial_number}: {e}")
            files_info[serial_number] = {'error': str(e)}
    
    return files_info

def check_existing_files(destination_root, files_info):
    """Checking existing files in the target directories"""
    existing_files = {}
    
    for serial_number, info in files_info.items():
        if 'error' in info:
            continue
            
        existing_files[serial_number] = []
        
        # Searching for files in all subdirectories
        for root, _, files in os.walk(destination_root):
            for file_info in info['files']:
                # Creating a file name with the serial_number prefix
                file_name = f"{serial_number}_{file_info['name']}"
                if file_name in files:
                    file_path = os.path.join(root, file_name)
                    actual_size = os.path.getsize(file_path)
                    
                    # Checking size consistency
                    if actual_size == file_info['size']:
                        existing_files[serial_number].append({
                            'name': file_name,
                            'path': file_path,
                            'size': actual_size,
                            'verified': True
                        })
                        logging.info(f"Found existing file with matching size: {file_name}")
                    else:
                        logging.warning(f"Found file {file_name} but size mismatch: expected {file_info['size']}, got {actual_size}")
                        try:
                            # Removing the file with the wrong size
                            os.remove(file_path)
                            logging.info(f"Removed file with incorrect size: {file_name}")
                        except Exception as e:
                            logging.error(f"Failed to remove file {file_name}: {e}")
    
    return existing_files

def copy_file_with_verification(source_url, dest_path, expected_size):
    """Copying file with size verification"""
    try:
        # Checking file availability and getting the actual size
        head_response = requests.head(source_url, timeout=5)
        if head_response.status_code != 200:
            raise Exception(f"File not accessible. Status code: {head_response.status_code}")
        
        # Получаем реальный размер файла с камеры
        total_size = int(head_response.headers.get('content-length', 0))
        if total_size == 0:
            raise Exception("Content-Length header is missing or zero")
        
        # Getting the actual file size from the camera
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copying file
        downloaded_size = 0
        with requests.get(source_url, stream=True, timeout=30) as response:
            response.raise_for_status()
            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size > 0:
                            progress = (downloaded_size / total_size) * 100
                            if progress % 5 < 1:
                                logging.info(f"Download progress for {dest_path.name}: {progress:.1f}%")
        
        # Checking the size of the copied file
        actual_size = os.path.getsize(dest_path)
        if actual_size != total_size:
            logging.error(f"Size mismatch after download for {dest_path.name}: expected from camera {total_size}, got {actual_size}")
            if os.path.exists(dest_path):
                os.remove(dest_path)
            return False
        
        logging.info(f"Successfully copied and verified: {dest_path.name} ({actual_size} bytes)")
        return True
        
    except Exception as e:
        logging.error(f"Error copying {source_url} to {dest_path}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python copy_to_pc_and_scene_sorting.py <destination_root>")
        sys.exit(1)
    
    destination = sys.argv[1]
    create_folder_structure_and_copy_files(destination)
