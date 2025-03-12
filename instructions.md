# GoPro HERO13 Settings Documentation

## USB Connection
### Basic Connection
- Open GoPro systems that utilize USB must support the Network Control Model (NCM) protocol
- Connection steps:
  1. Physically connect the camera's USB-C port to your system
  2. Send HTTP command to enable wired USB control

### Socket Address
- USB address format: 172.2X.1YZ.51:8080 
- Where XYZ are the last three digits of the camera's serial number

## Camera State
- System Busy flag is set while:
  - Loading presets
  - Changing settings
  - Formatting sdcard
- Encoding Active flag is set while capturing photo/video media

## Settings Control
### Base URL
- http://<camera_ip>:8080/gp/gpControl/setting/

### Change Setting
- PUT /setting/{setting_id}/{option_id}
Example:

### Setting Examples
PUT http://172.2X.1YZ.51:8080/gp/gpControl/setting/2/9
Changes resolution (setting_id=2) to 1080p (option_id=9)

### Response Codes
- 200: Success
- 403: Invalid value (returns list of currently supported values)
- 409: Setting conflict
- 500: Camera error

### Setting Groups and Dependencies
1. Video Settings Group:
   - 2: Resolution
   - 3: FPS
   - 91: Lens Type
   - 121: EV Comp
   - 122: Sharpness
   
2. Photo Settings Group:
   - 19: Photo Mode
   - 125: Photo Output
   - 146: Shutter Speed
   
3. Timelapse Settings Group:
   - 30: Interval
   - 32: Duration
   - 37: ISO Min
   
4. Global Settings:
   - 134: Anti-flicker
   - 135: Hypersmooth
   - 159: Auto Power Off

### HERO13 Specific Settings
Base endpoint: http://<camera_ip>:8080/gp/gpControl/

1. Single setting:
   PUT /setting/{id}/{value}

2. Multiple settings (batch):
   POST /setting
   Content-Type: application/json
   
   {
     "settings": {
       "{setting_id}": {value},
       "{setting_id}": {value}
     }
   }

### Setting Timing and Delays
1. Minimum delays between settings:
   - 100ms between individual settings
   - 250ms after mode changes
   - 500ms after Performance Mode changes
   
2. Batch Setting Best Practices:
   - Maximum 10 settings per batch
   - Wait for status.1 == 0 between batches
   - Total timeout: 5 seconds per batch

### Setting Priority Order
Priority 1 (System):
- 173: Performance Mode
- 126: System Mode
- 128: Media Format

Priority 2 (Core):
- 2: Resolution
- 3: FPS
- 91: Lens

Priority 3 (Features):
- 135: HyperSmooth
- 64: Bitrate
- 115: Color

Priority 4 (Optional):
- All other settings

### Setting Validation and Dependencies

1. Setting State Machine:
   Each setting change must follow state transitions:
   Current State -> Validate -> Apply -> Verify -> Next State

2. Setting Validation Rules:
   GET /gp/gpControl/setting/validate
   Request body:
   {
     "settings": {
       "id": value,
       ...
     }
   }
   
   Response:
   {
     "valid": true/false,
     "conflicts": [
       {
         "setting_id": id,
         "current_value": value,
         "required_value": value
       }
     ]
   }

3. Setting Dependencies Map:
   {
     "2": ["126", "173"],    // Resolution depends on System Mode and Performance Mode
     "3": ["2", "173"],      // FPS depends on Resolution and Performance Mode
     "135": ["2", "3", "173"] // HyperSmooth depends on Resolution, FPS, and Performance Mode
   }

### Setting Application Methods

1. Safe Setting Application:
   PUT /gp/gpControl/setting/safe/{id}/{value}
   - Includes automatic validation
   - Handles dependencies
   - Returns detailed error information
   
2. Force Setting Application:
   PUT /gp/gpControl/setting/force/{id}/{value}
   - Bypasses validation
   - Use with caution
   - May cause camera instability

3. Batch Setting with Validation:
   POST /gp/gpControl/setting/batch
   {
     "settings": {...},
     "validate": true,
     "resolve_conflicts": true
   }

### Error Prevention and Recovery

1. Common Error Patterns:
   - 409: Settings applied in wrong order
   - 403: Invalid setting for current mode
   - 500: Camera busy or system error

2. Recovery Sequence:
   a) On error:
      GET /gp/gpControl/setting/reset/{id}
      Resets specific setting to default
      
   b) Full reset if needed:
      POST /gp/gpControl/setting/factory_reset
      {
        "keep_network": true,
        "keep_pairing": true
      }

3. Setting Conflict Resolution:
   GET /gp/gpControl/setting/conflicts
   Returns matrix of setting conflicts

### Template and Preset Management

1. Template Operations:
   GET /gp/gpControl/setting/templates
   Returns list of available templates
   
   POST /gp/gpControl/setting/template/save
   {
     "name": "template_name",
     "settings": current_settings,
     "metadata": {
       "created": timestamp,
       "camera_model": "HERO13",
       "firmware": "H24.01.01.30.72"
     }
   }

2. Preset Management:
   GET /gp/gpControl/presets
   Returns:
   {
     "presets": [
       {
         "id": preset_id,
         "name": "preset_name",
         "settings": {...}
       }
     ]
   }

### Setting Synchronization (Multiple Cameras)

1. Primary Camera Settings Export:
   GET /gp/gpControl/setting/export
   Returns:
   {
     "timestamp": "ISO-8601",
     "camera_model": "HERO13",
     "settings_bundle": {
       "settings": {...},
       "checksums": {...}
     }
   }

2. Secondary Camera Settings Import:
   POST /gp/gpControl/setting/import
   {
     "settings_bundle": {...},
     "verify": true
   }

### USB Setting Protocol Specifics

1. USB Setting Endpoints:
   Base URL for USB: http://172.2X.1YZ.51:8080/gp/gpControl/

2. USB-Specific Headers:
   Required headers for USB communication:
   {
     "Connection": "Keep-Alive",
     "Accept": "application/json",
     "Content-Type": "application/json"
   }

3. USB Setting Performance:
   - Maximum throughput: 100 settings/second
   - Recommended batch size: 5-10 settings
   - Minimum delay between batches: 50ms

4. USB Connection Maintenance:
   GET /gp/gpControl/usb/status
   Returns:
   {
     "connection": "active|inactive",
     "bandwidth": number,
     "errors": number,
     "last_transaction": timestamp
   }

### Final Setting Validation

1. Complete Validation Sequence:
   a) Check camera status
   b) Validate settings
   c) Apply settings
   d) Verify application
   e) Save confirmation

2. Setting Documentation:
   GET /gp/gpControl/setting/info/{id}
   Returns:
   {
     "id": number,
     "name": string,
     "description": string,
     "type": "enum|range|boolean",
     "values": [...],
     "dependencies": [...],
     "firmware_requirements": {...}
   }

### Setting Health Check and Recovery Points

1. Setting Health Check:
   GET /gp/gpControl/setting/health
   Returns:
   {
     "settings_status": {
       "id": {
         "value": current_value,
         "expected": expected_value,
         "status": "ok|mismatch|error",
         "last_set": "timestamp"
       }
     }
   }

2. Setting Recovery Points:
   POST /gp/gpControl/setting/checkpoint
   Creates recovery point for current settings
   
   GET /gp/gpControl/setting/restore/{checkpoint_id}
   Restores settings from checkpoint

3. Setting Diagnostics:
   GET /gp/gpControl/setting/diagnostic
   Returns detailed setting state information:
   {
     "setting_history": [...],
     "failed_attempts": [...],
     "dependency_violations": [...]
   }

## Camera Status Monitoring via USB

### Basic Camera State Flags
From the documentation:
- System Busy flag indicates when camera is:
  - Loading presets
  - Changing settings
  - Formatting sdcard
- Encoding Active flag indicates when camera is:
  - Capturing photo/video media

### USB Connection Status
1. Connection Health Check:
   GET /gp/gpControl/usb/status
   Returns:
   ```json
   {
     "connection": "active|inactive",
     "bandwidth": number,
     "errors": number,
     "last_transaction": timestamp
   }
   ```

### Hardware Status Query
GET /gp/gpControl/query/hardware
Returns:
```json
{
  "battery_level": 75,
  "temperature": 45,
  "storage_temp": 42,
  "usb_connection": "3.0",
  "power_source": "battery"  // battery|usb|ac
}
```

### Storage Status Query
GET /gp/gpControl/query/storage/info
Returns:
```json
{
  "remaining": 1234567890,  // bytes
  "total": 12345678900,
  "used": 1234567890,
  "free_files": 1234,      // estimated remaining files
  "status": "ready"        // ready|busy|error
}
```

### File System Status
GET /gp/gpControl/query/filesystem
Returns:
```json
{
  "sd_status": "ready",      // ready|missing|error
  "fs_type": "exfat",
  "cluster_size": 32768,
  "max_file_size": 4294967296,
  "supports_large_files": true
}
```

### Last Captured File Status
GET /gp/gpControl/query/last_captured
Returns:
```json
{
  "status": 0,          // 0 = success
  "file": "GH010123.MP4",
  "timestamp": 1577836800,
  "size": 1234567890,
  "resolution": "4K",
  "duration": 120       // for videos only
}
```

### Transfer Status Monitoring
GET /gp/gpControl/query/transfer/status
Returns:
```json
{
  "active_transfers": 2,
  "queued_transfers": 5,
  "failed_transfers": 0,
  "completed_transfers": 10,
  "total_bytes_transferred": 1234567890,
  "current_transfer_speed": 1048576  // bytes/sec
}
```

### Setting Health Check Status
GET /gp/gpControl/setting/health
Returns:
```json
{
  "settings_status": {
    "id": {
      "value": current_value,
      "expected": expected_value,
      "status": "ok|mismatch|error",
      "last_set": "timestamp"
    }
  }
}
```

## Media File Operations

### Available Media Endpoints
Base URL: http://<camera_ip>:8080/gp/gpControl/

1. Media List and Info:
   - GET /media/list - Get list of all media files
   - GET /media/info/{media_file} - Get detailed file information
   - GET /media/last - Get last captured media file
   
2. File Download:
   - GET /media/download/{media_file} - Download specific media file
   - GET /media/screennail/{media_file} - Get media preview image
   - GET /media/thumbnail/{media_file} - Get media thumbnail
   
3. File Management:
   - DELETE /media/delete/all - Delete all files
   - DELETE /media/delete/{media_file} - Delete specific file
   - DELETE /media/group/{group_id} - Delete group of files

4. Additional Media Data:
   - GET /media/telemetry/{media_file} - Get file telemetry data
   - GET /media/gpmf/{media_file} - Get GPMF metadata

### Media File Data Models

1. Media List Schema:
   ```json
   {
     "media": [
       {
         "d": "DCIM/100GOPRO",  // directory
         "fs": [                 // files array
           {
             "n": "GH010123.MP4",  // filename
             "cre": "1577836800",  // creation timestamp
             "mod": "1577836800",  // modification timestamp
             "s": "1234567",       // size in bytes
             "g": "1234"           // group ID (if part of grouped media)
           }
         ]
       }
     ]
   }
   ```

2. Photo Metadata Schema:
   ```json
   {
     "w": 4000,          // width in pixels
     "h": 3000,          // height in pixels
     "raw": true/false,  // whether RAW is available
     "hdr": true/false,  // whether HDR was used
     "wdr": true/false   // whether WDR was used
   }
   ```

3. Video Metadata Schema:
   ```json
   {
     "w": 3840,          // width in pixels
     "h": 2160,          // height in pixels
     "fps": 60,          // frames per second
     "dur": 120,         // duration in seconds
     "hs": true/false,   // hypersmooth enabled
     "hdr": true/false   // HDR enabled
   }
   ```

4. Grouped Media Schema:
   ```json
   {
     "g": "1234",        // group ID
     "t": "burst",       // type (burst, timelapse, etc)
     "fs": [             // files in group
       {
         "n": "GH010123.MP4",
         "cre": "1577836800"
       }
     ]
   }
   ```

### File Download Process

1. Download Workflow:
   a) Get media list to identify files:
      GET /media/list
   
   b) For each file to download:
      - Get file info first:
        GET /media/info/{media_file}
      - Check file size and type
      - Initiate download:
        GET /media/download/{media_file}

2. Download Headers:
   Required headers for download:
   ```
   Accept-Encoding: gzip, deflate
   Connection: Keep-Alive
   ```

3. Download Response:
   - Content-Type: video/mp4, image/jpeg, etc.
   - Content-Length: file size in bytes
   - Accept-Ranges: bytes (supports partial downloads)

4. Large File Downloads:
   - Support for range requests
   - Example: 
     ```
     Range: bytes=0-1048576
     ```
   - Resume interrupted downloads
   - Parallel chunk downloads supported

5. Download Performance:
   - Maximum throughput depends on USB connection speed
   - Recommended chunk size: 1MB
   - Multiple simultaneous downloads supported
   - Keep-alive connection recommended

### USB File Transfer Specifics

1. USB Connection Requirements:
   - Network Control Model (NCM) protocol support required
   - USB 3.0 recommended for optimal transfer speeds
   - Connection must be maintained throughout transfer

2. Transfer Speed Optimization:
   - USB 3.0: Up to 640MB/s theoretical maximum
   - USB 2.0: Up to 60MB/s theoretical maximum
   - Actual speeds may vary based on:
     * Camera battery level
     * System resources
     * File fragmentation
     * USB cable quality

3. Connection Monitoring:
   - Regular status checks recommended:
     GET /gp/gpControl/usb/status
   - Monitor bandwidth and errors during transfer
   - Implement automatic reconnection if connection drops

4. Error Handling:
   - Check connection status before each file transfer
   - Implement retry mechanism for failed transfers
   - Monitor error count in status response
   - Reset connection if error threshold exceeded

5. Best Practices:
   - Use high-quality USB cable
   - Ensure camera battery level above 20%
   - Monitor camera temperature during large transfers
   - Implement transfer queue system for multiple files
   - Regular connection health checks during long transfers

### Camera States During File Transfer

1. Pre-transfer State Check:
   GET /gp/gpControl/status
   Important flags:
   - System Busy (1 = busy, 0 = ready)
   - Encoding Active (1 = recording, 0 = idle)
   - Storage Status (1 = available, 0 = full)
   
2. Transfer Blocking States:
   - Camera is recording video/capturing photo
   - System is formatting SD card
   - Camera is updating firmware
   - Battery critically low (< 10%)

3. State Monitoring During Transfer:
   - Check camera status every 5 seconds
   - Pause transfer if camera enters busy state
   - Resume transfer when camera returns to ready state
   - Monitor storage status for changes

4. Recovery States:
   - If camera disconnects: wait for "ready" state before reconnecting
   - If transfer interrupted: verify file integrity before resuming
   - If camera enters power save: wake camera and reestablish connection

5. Transfer State Management:
   - Create transfer session ID
   - Track progress for each file
   - Store resume points for large files
   - Log state changes during transfer
   - Maintain transfer queue state

### Group File Operations

1. Group Transfer Workflow:
   a) Get group information:
      GET /media/list?group=true
   
   b) Download files by group:
      - All files in burst mode
      - Time lapse sequences
      - Multi-shot series

2. Group Transfer Optimization:
   - Download files in parallel within group
   - Maintain file order sequence
   - Verify group completeness
   - Track group transfer progress

3. Group File Structure:
   - Parent directory: DCIM/100GOPRO
   - File naming convention: 
     * GH01XXXX.MP4 for video
     * GOPRXXXX.JPG for photos
     * Same XXXX for files in group

4. Group Transfer Validation:
   - Verify all files in group downloaded
   - Check group metadata integrity
   - Validate file sequence numbers
   - Confirm total group size matches

### Data Transfer Protocol

1. Transfer Packet Structure:
   ```
   [Header][Payload][Checksum]
   Header format:
   - 4 bytes: Magic number (0x47504D44)
   - 4 bytes: Payload length
   - 2 bytes: Packet sequence number
   - 2 bytes: Flags
   ```

2. Transfer Chunking:
   - Maximum packet size: 64KB
   - Chunk sequence numbering
   - Chunk acknowledgment required
   - Retry failed chunks automatically

3. Data Integrity:
   - CRC32 checksum per chunk
   - End-to-end file hash verification
   - Corrupt chunk detection and retransmission
   - File size verification after transfer

4. Transfer Resume Protocol:
   a) Store transfer state:
      - Last successful chunk
      - File offset
      - Checksum of received data
   
   b) Resume procedure:
      - Verify existing chunks
      - Request missing chunks
      - Update transfer progress
      - Validate final file

5. Transfer Optimization:
   - Adaptive chunk sizing
   - Dynamic window sizing
   - Compression for supported types
   - Bandwidth monitoring and adjustment

### File Transfer Error Handling

1. Transfer Error Codes:
   - 404: File not found
   - 409: Transfer conflict (file in use)
   - 413: File too large
   - 429: Too many concurrent transfers
   - 500: Internal camera error
   - 507: Storage full
   - 511: Network authentication required

2. Connection Error Recovery:
   a) Temporary errors (retry-able):
      - Network timeout
      - Temporary disconnection
      - Bandwidth fluctuation
      - System busy
   
   b) Fatal errors (require user intervention):
      - Storage full
      - Battery critical
      - Hardware failure
      - File corruption

3. Error Recovery Strategy:
   - Implement exponential backoff for retries
   - Maximum 3 retry attempts per chunk
   - Log all transfer errors with timestamps
   - Maintain error statistics per session
   - Notify user of unrecoverable errors

4. Data Validation Errors:
   - Checksum mismatch
   - File size mismatch
   - Incomplete chunks
   - Invalid file format
   - Corrupted metadata

5. Error Prevention:
   - Pre-transfer space verification
   - Battery level monitoring
   - Connection quality check
   - File system integrity check
   - Concurrent transfer limiting

### Network File Transfer Options

1. HTTPS Transfer Support:
   - Secure file transfer over HTTPS
   - Certificate-based authentication
   - Encrypted data transmission
   - Support for proxy servers

2. Network Transfer Headers:
   ```
   Content-Type: application/json
   Accept: application/json
   X-GoPro-Signature: [calculated hash]
   Authorization: Bearer [token]
   ```

3. Network Transfer Performance:
   - Bandwidth dependent on network conditions
   - Support for WiFi Direct connection
   - Automatic network type detection
   - Network quality monitoring

4. Network Security:
   - TLS 1.2/1.3 encryption
   - Certificate validation
   - Session token management
   - Secure key exchange

5. Network Transfer vs USB:
   Advantages:
   - No physical connection needed
   - Multiple camera support
   - Remote access capability
   
   Limitations:
   - Lower transfer speeds
   - Network dependency
   - Higher power consumption
   - Connection stability varies

### File Query and Status Operations

1. Last Captured File Query:
   GET /gp/gpControl/query/last_captured
   Returns:
   ```json
   {
     "status": 0,          // 0 = success
     "file": "GH010123.MP4",
     "timestamp": 1577836800,
     "size": 1234567,
     "resolution": "4K",
     "duration": 120       // for videos only
   }
   ```

2. Storage Status Query:
   GET /gp/gpControl/query/storage/info
   Returns:
   ```json
   {
     "remaining": 1234567890,  // bytes
     "total": 12345678900,
     "used": 1234567890,
     "free_files": 1234,      // estimated remaining files
     "status": "ready"        // ready|busy|error
   }
   ```

3. Transfer Status Query:
   GET /gp/gpControl/query/transfer/status
   Returns:
   ```json
   {
     "active_transfers": 2,
     "queued_transfers": 5,
     "failed_transfers": 0,
     "completed_transfers": 10,
     "total_bytes_transferred": 1234567890,
     "current_transfer_speed": 1048576  // bytes/sec
   }
   ```

4. File System Query:
   GET /gp/gpControl/query/filesystem
   Returns:
   ```json
   {
     "sd_status": "ready",      // ready|missing|error
     "fs_type": "exfat",
     "cluster_size": 32768,
     "max_file_size": 4294967296,
     "supports_large_files": true
   }
   ```

5. Hardware Status for Transfer:
   GET /gp/gpControl/query/hardware
   Returns:
   ```json
   {
     "battery_level": 75,
     "temperature": 45,
     "storage_temp": 42,
     "usb_connection": "3.0",
     "power_source": "battery"  // battery|usb|ac
   }
   ```

### File Metadata and Telemetry

1. GPMF Metadata Access:
   GET /media/gpmf/{media_file}
   Returns:
   ```json
   {
     "streams": [
       {
         "type": "GPS5",
         "samples": [
           {
             "lat": 12.3456,
             "lon": 78.9012,
             "alt": 100,
             "speed": 5.6,
             "timestamp": 1577836800
           }
         ]
       },
       {
         "type": "ACCL",
         "samples": [
           {
             "x": 1.2,
             "y": -0.5,
             "z": 9.8,
             "timestamp": 1577836800
           }
         ]
       }
     ]
   }
   ```

2. File Telemetry Data:
   GET /media/telemetry/{media_file}
   Returns:
   ```json
   {
     "device": {
       "model": "HERO13",
       "firmware": "H24.01.01.30.72",
       "serial": "C3341234567"
     },
     "settings": {
       "resolution": "4K",
       "fps": 60,
       "fov": "Wide",
       "stabilization": "On"
     },
     "conditions": {
       "temperature": 45,
       "battery_start": 85,
       "battery_end": 75
     }
   }
   ```

3. Metadata Download Options:
   - Raw GPMF data stream
   - Processed JSON format
   - CSV export format
   - Binary telemetry format

4. Telemetry Synchronization:
   - Timestamp alignment with video frames
   - GPS track correlation
   - Sensor data synchronization
   - Event markers in timeline

5. Metadata Transfer Optimization:
   - Selective metadata download
   - Compressed telemetry streams
   - Cached metadata access
   - Incremental updates

### USB Transfer Performance Optimization

1. Transfer Speed Factors:
   - USB Controller Mode:
     * SuperSpeed (USB 3.0): 5 Gbps
     * HighSpeed (USB 2.0): 480 Mbps
     * Must verify connection mode before transfer
   
2. Buffer Management:
   - Optimal buffer sizes:
     * Large files: 1MB buffer
     * Small files: 64KB buffer
   - Double buffering for continuous transfer
   - Memory-mapped transfers when possible
   
3. Transfer Queue Management:
   - Maximum concurrent transfers: 4
   - Queue depth per transfer: 8
   - Priority based on file type:
     * High: Small files (thumbnails, metadata)
     * Medium: Photos
     * Low: Large video files

4. Performance Monitoring:
   - Real-time throughput tracking
   - Transfer speed history
   - System resource usage
   - Temperature monitoring
   
5. Performance Optimization:
   - Disable USB power saving
   - Use direct memory access (DMA)
   - Minimize system CPU usage
   - Optimize packet sizes for file type

### USB Transfer Initialization Process

1. Connection Setup Sequence:
   a) Physical Connection:
      - Connect USB cable
      - Wait for device enumeration
      - Verify USB mode (2.0/3.0)
   
   b) Enable USB Control:
      ```
      PUT http://172.2X.1YZ.51:8080/gp/gpControl/usb/enable
      Response: 200 OK = Ready for transfer
      ```

2. Pre-transfer Checklist:
   - Verify camera firmware version
   - Check available storage space
   - Validate USB connection speed
   - Ensure sufficient battery level
   - Check camera temperature

3. Transfer Session Setup:
   a) Create transfer session:
      ```
      POST /gp/gpControl/transfer/session
      Request:
      {
        "session_id": "unique_id",
        "transfer_mode": "usb",
        "priority": "high|normal|low"
      }
      ```
   
   b) Configure transfer parameters:
      ```
      PUT /gp/gpControl/transfer/configure
      {
        "chunk_size": 1048576,
        "max_retries": 3,
        "timeout": 30,
        "verify_transfer": true
      }
      ```

4. Resource Allocation:
   - Allocate transfer buffers
   - Initialize checksum calculators
   - Prepare progress tracking
   - Setup error logging
   - Create temporary storage

5. Transfer Environment Setup:
   - Disable camera sleep mode
   - Set USB power management
   - Configure transfer timeouts
   - Initialize recovery system
   - Prepare status monitoring

### Transfer Completion and Cleanup

1. Transfer Finalization:
   a) Verify transfer completion:
      ```
      GET /gp/gpControl/transfer/status/{session_id}
      Response:
      {
        "status": "complete",
        "files_transferred": 10,
        "total_bytes": 1234567890,
        "failed_files": 0,
        "duration": 300
      }
      ```

   b) Final verification:
      - Compare checksums
      - Verify file counts
      - Check file sizes
      - Validate metadata

2. Session Cleanup:
   a) Close transfer session:
      ```
      POST /gp/gpControl/transfer/session/{session_id}/close
      {
        "cleanup_temp": true,
        "generate_report": true
      }
      ```
   
   b) Resource cleanup:
      - Free transfer buffers
      - Close file handles
      - Clear temporary storage
      - Reset transfer state

3. Post-transfer Operations:
   - Generate transfer report
   - Log transfer statistics
   - Update file indexes
   - Clean temporary files
   - Reset camera state

4. Transfer Report Generation:
   ```json
   {
     "session_summary": {
       "start_time": "2024-01-20T10:00:00Z",
       "end_time": "2024-01-20T10:05:00Z",
       "total_files": 10,
       "total_bytes": 1234567890,
       "average_speed": 4194304,
       "errors_encountered": 0
     },
     "file_details": [
       {
         "name": "GH010123.MP4",
         "size": 123456789,
         "status": "success",
         "verification": "passed"
       }
     ]
   }
   ```

5. Camera State Restoration:
   - Re-enable sleep mode
   - Restore power settings
   - Clear transfer flags
   - Reset USB connection
   - Update media list

### GPMF Metadata Status
GET /media/gpmf/{media_file}
Returns:
```json
{
  "streams": [
    {
      "type": "GPS5",
      "samples": [
        {
          "lat": 12.3456,
          "lon": 78.9012,
          "alt": 100,
          "speed": 5.6,
          "timestamp": 1577836800
        }
      ]
    },
    {
      "type": "ACCL",
      "samples": [
        {
          "x": 1.2,
          "y": -0.5,
          "z": 9.8,
          "timestamp": 1577836800
        }
      ]
    }
  ]
}
```

### File Telemetry Status
GET /media/telemetry/{media_file}
Returns:
```json
{
  "device": {
    "model": "HERO13",
    "firmware": "H24.01.01.30.72",
    "serial": "C3341234567"
  },
  "settings": {
    "resolution": "4K",
    "fps": 60,
    "fov": "Wide",
    "stabilization": "On"
  },
  "conditions": {
    "temperature": 45,
    "battery_start": 85,
    "battery_end": 75
  }
}
```

### Transfer Session Status
GET /gp/gpControl/transfer/status/{session_id}
Returns:
```json
{
  "status": "complete",
  "files_transferred": 10,
  "total_bytes": 1234567890,
  "failed_files": 0,
  "duration": 300
}
```

### Transfer Report Status
The transfer report provides a comprehensive status of the entire transfer session:
```json
{
  "session_summary": {
    "start_time": "2024-01-20T10:00:00Z",
    "end_time": "2024-01-20T10:05:00Z",
    "total_files": 10,
    "total_bytes": 1234567890,
    "average_speed": 4194304,
    "errors_encountered": 0
  },
  "file_details": [
    {
      "name": "GH010123.MP4",
      "size": 123456789,
      "status": "success",
      "verification": "passed"
    }
  ]
}
```

### Important Status Monitoring Best Practices
1. Connection Monitoring:
   - Regular status checks recommended
   - Monitor bandwidth and errors during transfer
   - Implement automatic reconnection if connection drops

2. Performance Monitoring:
   - Real-time throughput tracking
   - Transfer speed history
   - System resource usage
   - Temperature monitoring

3. Error Monitoring:
   - Monitor error count in status response
   - Reset connection if error threshold exceeded
   - Log all transfer errors with timestamps
   - Maintain error statistics per session

### HERO13 Specific Status Monitoring

### Setting Documentation Status
GET /gp/gpControl/setting/info/{id}
Returns:
```json
{
  "id": number,
  "name": string,
  "description": string,
  "type": "enum|range|boolean",
  "values": [...],
  "dependencies": [...],
  "firmware_requirements": {...}
}
```

### Setting Diagnostics Status
GET /gp/gpControl/setting/diagnostic
Returns:
```json
{
  "setting_history": [...],
  "failed_attempts": [...],
  "dependency_violations": [...]
}
```

### Setting Recovery Points
1. Create Recovery Point:
   POST /gp/gpControl/setting/checkpoint
   Creates recovery point for current settings

2. Restore from Recovery Point:
   GET /gp/gpControl/setting/restore/{checkpoint_id}
   Restores settings from checkpoint

### Complete Status Validation Sequence
1. Status Check Sequence:
   a) Check camera status
   b) Validate settings
   c) Apply settings
   d) Verify application
   e) Save confirmation

### Status Monitoring Timing Guidelines
1. Minimum Status Check Intervals:
   - 100ms between individual status checks
   - 250ms after mode changes
   - 500ms after Performance Mode changes
   
2. Batch Status Check Best Practices:
   - Maximum 10 status checks per batch
   - Wait for status.1 == 0 between batches
   - Total timeout: 5 seconds per batch

### Status Priority Order for HERO13
Priority 1 (System Status):
- 173: Performance Mode Status
- 126: System Mode Status
- 128: Media Format Status

Priority 2 (Core Status):
- 2: Resolution Status
- 3: FPS Status
- 91: Lens Status

Priority 3 (Features Status):
- 135: HyperSmooth Status
- 64: Bitrate Status
- 115: Color Status

### Webcam Status Monitoring
1. Get Webcam Status:
   GET /gp/gpControl/webcam/status
   Returns webcam operational status

2. Get Webcam Version:
   GET /gp/gpControl/webcam/version
   Returns webcam firmware version

3. Webcam Preview Status:
   GET /gp/gpControl/webcam/preview
   Returns preview stream status

### Status Monitoring Headers for HERO13
Required headers for all status monitoring requests:
```json
{
  "Connection": "Keep-Alive",
  "Accept": "application/json",
  "Content-Type": "application/json"
}
```

### Status Monitoring Best Practices for HERO13
1. System Status Monitoring:
   - Check System Busy flag before operations
   - Monitor Encoding Active flag during capture
   - Verify USB connection status regularly
   - Track battery level and temperature

2. Media Status Monitoring:
   - Monitor storage space continuously
   - Track file system status
   - Check media list updates
   - Verify transfer progress

3. Error Status Handling:
   - Monitor error counts
   - Track connection stability
   - Log status changes
   - Maintain error history

### Media List Monitoring for HERO13
1. Get Media List Status:
   GET /media/list
   Returns:
   ```json
   {
     "media": [
       {
         "d": "DCIM/100GOPRO",  // directory
         "fs": [                 // files array
           {
             "n": "GH010123.MP4",  // filename
             "cre": "1577836800",  // creation timestamp
             "mod": "1577836800",  // modification timestamp
             "s": "1234567",       // size in bytes
             "g": "1234"           // group ID (if part of grouped media)
           }
         ]
       }
     ]
   }
   ```

2. Media Info Status:
   GET /media/info/{media_file}
   Returns detailed file status information

3. Group Media Status:
   ```json
   {
     "g": "1234",        // group ID
     "t": "burst",       // type (burst, timelapse, etc)
     "fs": [             // files in group
       {
         "n": "GH010123.MP4",
         "cre": "1577836800"
       }
     ]
   }
   ```

### Preview Stream Status for HERO13
1. Start Preview Stream Status:
   GET /gp/gpControl/execute?p1=gpStream&c1=start
   Returns stream initialization status

2. Stop Preview Stream Status:
   GET /gp/gpControl/execute?p1=gpStream&c1=stop
   Returns stream termination status

3. Preview Stream Health:
   GET /gp/gpControl/status/preview
   Returns:
   ```json
   {
     "active": true/false,
     "resolution": "1080p",
     "fps": 30,
     "bitrate": 4000000,
     "codec": "h264"
   }
   ```

### Real-time Status Monitoring Guidelines for HERO13
1. Critical Status Checks:
   - System Busy flag: Every 100ms
   - Battery level: Every 30 seconds
   - Storage space: Every 60 seconds
   - Temperature: Every 30 seconds
   - USB connection: Every 5 seconds

2. Media Operation Status Checks:
   - During file transfer: Every 1 second
   - During recording: Every 2 seconds
   - During preview streaming: Every 500ms
   - Media list updates: Every 5 seconds

3. Error Status Thresholds:
   - Connection errors: Max 3 in 60 seconds
   - Transfer failures: Max 2 per file
   - Temperature warnings: Above 45°C
   - Storage warnings: Below 10% free space

### USB Connection Maintenance for HERO13
1. Connection Status Check:
   GET /gp/gpControl/usb/status
   Returns:
   ```json
   {
     "connection": "active|inactive",
     "bandwidth": number,
     "errors": number,
     "last_transaction": timestamp
   }
   ```

2. USB Performance Status:
   - Maximum throughput: 100 settings/second
   - Recommended batch size: 5-10 settings
   - Minimum delay between batches: 50ms

3. USB Connection Health:
   GET /gp/gpControl/usb/health
   Returns:
   ```json
   {
     "connection_quality": "good|degraded|poor",
     "signal_strength": number,
     "packet_loss": number,
     "latency": number
   }
   ```

### Status Validation and Recovery for HERO13
1. Setting Validation Status:
   GET /gp/gpControl/setting/validate
   Request body:
   ```json
   {
     "settings": {
       "id": value,
       ...
     }
   }
   ```
   Response:
   ```json
   {
     "valid": true/false,
     "conflicts": [
       {
         "setting_id": id,
         "current_value": value,
         "required_value": value
       }
     ]
   }
   ```

2. Status Recovery Sequence:
   a) On error:
      GET /gp/gpControl/setting/reset/{id}
      Resets specific setting to default
      
   b) Full reset if needed:
      POST /gp/gpControl/setting/factory_reset
      ```json
      {
        "keep_network": true,
        "keep_pairing": true
      }
      ```

### Status Monitoring Dependencies for HERO13
1. Setting Dependencies Map:
   ```json
   {
     "2": ["126", "173"],    // Resolution depends on System Mode and Performance Mode
     "3": ["2", "173"],      // FPS depends on Resolution and Performance Mode
     "135": ["2", "3", "173"] // HyperSmooth depends on Resolution, FPS, and Performance Mode
   }
   ```

2. Status Check Dependencies:
   - Hardware status must be checked before performance mode changes
   - System busy flag must be checked before any setting changes
   - Storage status must be checked before media operations
   - USB status must be checked before file transfers

### Status Monitoring Error Prevention for HERO13
1. Common Error Patterns:
   - 409: Status checks in wrong order
   - 403: Invalid status check for current mode
   - 500: Camera busy or system error

2. Error Prevention Best Practices:
   - Validate settings before applying changes
   - Check system status before operations
   - Monitor temperature during heavy operations
   - Track USB connection quality
   - Log all status changes
   - Implement automatic recovery procedures















