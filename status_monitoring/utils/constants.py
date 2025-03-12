from enum import Enum

# Camera Settings IDs
class SettingID:
    RESOLUTION = 2
    FPS = 3
    LENS_TYPE = 91
    ISO_MIN = 102
    ISO_MAX = 103
    WHITE_BALANCE = 115
    DIGITAL_LENS = 121
    HYPERSMOOTH = 135
    INTERVAL = 30
    CURRENT_MODE = 144
    PERFORMANCE_MODE = 173
    SYSTEM_MODE = 126
    MEDIA_FORMAT = 128

# Camera Modes
class CameraMode(Enum):
    VIDEO = "video"
    PHOTO = "photo"
    TIMELAPSE = "timelapse"
    WEBCAM = "webcam"

# Status Codes
class StatusCode(Enum):
    SUCCESS = 200
    INVALID_VALUE = 403
    SETTING_CONFLICT = 409
    CAMERA_ERROR = 500

# Preview Settings
class PreviewSettings:
    MIN_QUALITY = 1
    MAX_QUALITY = 100
    DEFAULT_QUALITY = 50
    MIN_REFRESH_RATE = 1
    MAX_REFRESH_RATE = 30
    DEFAULT_REFRESH_RATE = 15

# Grid Settings
class GridSettings:
    MIN_CARD_WIDTH = 200
    MAX_CARD_WIDTH = 500
    DEFAULT_CARD_WIDTH = 300
    MIN_SPACING = 5
    MAX_SPACING = 20
    DEFAULT_SPACING = 10

# Update Intervals (ms)
class UpdateInterval:
    STATUS = 1000
    PREVIEW = 100
    BATTERY = 30000
    STORAGE = 60000
    TEMPERATURE = 30000
    CONNECTION = 5000

# Temperature Thresholds (°C)
class TemperatureThreshold:
    WARNING = 45
    CRITICAL = 50

# Storage Thresholds (%)
class StorageThreshold:
    WARNING = 25
    CRITICAL = 10

# Battery Thresholds (%)
class BatteryThreshold:
    WARNING = 50
    CRITICAL = 20

# Connection Settings
class ConnectionSettings:
    MAX_RETRIES = 3
    RETRY_DELAY = 1000
    TIMEOUT = 5000
    KEEP_ALIVE_INTERVAL = 30000

# File Paths
class FilePath:
    CONFIG = "config.json"
    LOGS = "logs"
    CACHE = "cache"

# UI Constants
class UIConstants:
    WINDOW_TITLE = "GoPro Cameras Status Monitor"
    MIN_WINDOW_WIDTH = 800
    MIN_WINDOW_HEIGHT = 600
    TOOLBAR_HEIGHT = 40
    STATUS_BAR_HEIGHT = 20
    DIALOG_MIN_WIDTH = 600
    DIALOG_MIN_HEIGHT = 800

# Error Messages
class ErrorMessage:
    CONNECTION_FAILED = "Failed to connect to camera"
    INVALID_SETTING = "Invalid setting value"
    SETTING_CONFLICT = "Setting conflict detected"
    CAMERA_BUSY = "Camera is busy"
    STORAGE_FULL = "Storage is full"
    TEMPERATURE_HIGH = "Camera temperature too high"
    BATTERY_LOW = "Battery level critical"
    USB_ERROR = "USB connection error"
    PREVIEW_ERROR = "Preview stream error"
    CONFIG_ERROR = "Configuration error"
    LOG_ERROR = "Logging error"

# Success Messages
class SuccessMessage:
    CONNECTED = "Connected to camera"
    SETTING_UPDATED = "Setting updated successfully"
    PREVIEW_STARTED = "Preview stream started"
    PREVIEW_STOPPED = "Preview stream stopped"
    CONFIG_SAVED = "Configuration saved"
    LOG_CLEANED = "Old logs cleaned up" 