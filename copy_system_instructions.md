# Instructions for Implementing the File Copy System from GoPro Cameras

## 1. System Structure

### 1.1 Main Components
- `CopyManager` - the main class for managing copying
- `FileStatistics` - class for collecting statistics
- `CopyProgressWidget` - widget for displaying progress
- Logging system

### 1.2 Auxiliary Classes
- `FileInfo` - information about a file
- `SceneInfo` - information about a scene (group of files)
- `CopyStatistics` - copy statistics

## 2. Copy Process

### 2.1 Preparation for Copying
1. Get the list of cameras from `camera_cache.json`
2. For each camera:
   - Request the list of files via the API (`/gopro/media/list`)
   - Create `FileInfo` objects for each file
   - Check the availability of the camera

### 2.2 Grouping Files into Scenes
1. Sort files by creation time
2. Group files into scenes:
   - Interval between files <= 5 minutes = one scene
   - Create a new scene if the interval is exceeded
3. For each scene:
   - Create a unique name based on the time
   - Calculate the total size of the files
   - Create a directory for the scene

### 2.3 Copying Process
1. For each scene:
   - Create a directory for the scene
   - For each file in the scene:
     * Check if the file exists
     * Verify the size if the file exists
     * Copy the file while tracking progress
     * Verify the copied file

### 2.4 Copy Verification
1. Check the file size before and after copying
2. Check the availability of the file on the camera
3. Check write permissions for the destination directory
4. Check available disk space

## 3. Logging System

### 3.1 Logging Levels
- DEBUG: detailed information for debugging
- INFO: main copy operations
- WARNING: non-critical issues
- ERROR: critical errors
- CRITICAL: fatal errors

### 3.2 What to Log
1. Start/end of copying
2. Status of each file:
   - Start of copying
   - Copy progress
   - Completion of copying
   - Copy errors
3. Statistics:
   - Total number of files
   - File sizes
   - Copying time
   - Copying speed
4. Errors:
   - Camera unavailability
   - Read/write errors
   - Verification errors

### 3.3 Log Format
```
[TIMESTAMP] [LEVEL] [MODULE] Message
Additional information in multiple lines
```

## 4. Error Handling

### 4.1 Types of Errors
1. Connection errors:
   - Camera unavailable
   - Network issues
2. File system errors:
   - Insufficient space
   - No write permissions
   - File is locked
3. Data errors:
   - Incorrect file size
   - Verification error
4. Camera API errors:
   - Invalid response
   - Timeout

### 4.2 Error Handling
1. For each type of error:
   - Log the details
   - Update the file status
   - Notify the user
2. Recovery strategies:
   - Retry for network errors
   - Skip problematic files
   - Allow resuming from the point of failure

## 5. Progress Display

### 5.1 Information to Display
1. Overall progress:
   - Percentage completed
   - Remaining time
   - Copying speed
2. Scene progress:
   - Scene name
   - Number of files
   - Copying status
3. File progress:
   - File name
   - Size
   - Status
   - Percentage completed
4. Statistics:
   - Total files
   - Copied
   - Skipped
   - Errors

### 5.2 GUI Updates
1. Use Qt signals:
   - `progress_updated`
   - `status_updated`
   - `error_occurred`
2. Update frequency:
   - Progress: every 100ms
   - Statistics: every second
   - Errors: immediately

## 6. Optimization

### 6.1 Performance
1. Multithreaded copying:
   - Use `ThreadPoolExecutor` for parallel copying
   - Limit the number of threads
2. Buffer size:
   - Optimal `chunk_size`
   - Memory management
3. Caching:
   - Cache the file list
   - Cache statistics

### 6.2 Reliability
1. Recovery mechanism:
   - Save the copy state
   - Allow resuming interrupted copying
2. Integrity checks:
   - Verify file sizes
   - Check file availability
3. Exception handling:
   - Properly close threads
   - Release resources

## 7. Testing

### 7.1 Unit Tests
1. Test components:
   - `CopyManager`
   - `FileStatistics`
   - Logging
2. Test scenarios:
   - Successful copying
   - Error handling
   - Copy cancellation

### 7.2 Integration Tests
1. Interaction with cameras
2. File system operations
3. GUI updates

### 7.3 Test Scenarios
1. Copying large files
2. Interrupting copying
3. Losing connection to the camera
4. Running out of disk space