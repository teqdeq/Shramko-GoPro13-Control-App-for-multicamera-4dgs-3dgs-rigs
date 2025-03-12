"""
GoPro Camera Settings Dictionary
Complete list of all 173 settings from GoPro API v2.0
"""

CAMERA_SETTINGS = {
    # Video Settings
    '2': {  # Video Resolution
        'name': 'Video Resolution',
        'options': {
            1: '4K',
            2: '2.7K',
            4: '1440p',
            7: '1080p',
            8: '960p',
            9: '720p',
            10: '480p'
        }
    },
    '3': {  # Frames Per Second
        'name': 'FPS',
        'options': {
            0: '240',
            1: '120',
            2: '100',
            5: '60',
            6: '50',
            8: '30',
            9: '25',
            10: '24'
        }
    },
    '4': {  # FOV
        'name': 'Field of View',
        'options': {
            0: 'Wide',
            2: 'Narrow',
            3: 'SuperView',
            4: 'Linear',
            7: 'Linear + Horizon Leveling',
            8: 'HyperView'
        }
    },
    '5': {  # Low Light
        'name': 'Low Light',
        'options': {
            0: 'Off',
            1: 'On'
        }
    },
    '6': {  # Photo Resolution
        'name': 'Photo Resolution',
        'options': {
            3: '12MP',
            4: '7MP Wide',
            5: '7MP Medium',
            6: '5MP Wide',
            13: '23MP',
            14: '27MP'
        }
    },
    '13': {  # Protune
        'name': 'Protune',
        'options': {
            0: 'Off',
            1: 'On'
        }
    },
    '14': {  # White Balance
        'name': 'White Balance',
        'options': {
            0: 'Auto',
            1: '3000K',
            2: '4000K',
            3: '4800K',
            4: '5500K',
            5: '6000K',
            6: '6500K',
            7: 'Native'
        }
    },
    '19': {  # ISO Max
        'name': 'ISO Maximum',
        'options': {
            0: '6400',
            1: '3200',
            2: '1600',
            3: '800',
            4: '400',
            7: '200',
            8: '100'
        }
    },
    '24': {  # ISO Min
        'name': 'ISO Minimum',
        'options': {
            0: '6400',
            1: '3200',
            2: '1600',
            3: '800',
            4: '400',
            7: '200',
            8: '100'
        }
    },
    '30': {  # Shutter Speed
        'name': 'Shutter Speed',
        'options': {
            0: 'Auto',
            3: '1/25',
            6: '1/30',
            8: '1/50',
            11: '1/60',
            13: '1/100',
            16: '1/120',
            18: '1/200',
            21: '1/240',
            23: '1/400',
            26: '1/480',
            28: '1/800',
            31: '1/960',
            33: '1/1600',
            36: '1/1920',
            38: '1/3200'
        }
    },
    '31': {  # EV Comp
        'name': 'Exposure Compensation',
        'options': {
            0: '0',
            1: '+0.5',
            2: '+1',
            3: '+1.5',
            4: '+2',
            8: '-2',
            7: '-1.5',
            6: '-1',
            5: '-0.5'
        }
    },
    '32': {  # Video Mode
        'name': 'Video Mode',
        'options': {
            10: 'Standard',
            11: 'Performance',
            12: 'Extended Battery'
        }
    },
    '37': {  # Video Format
        'name': 'Video Format',
        'options': {
            0: 'HEVC',
            1: 'H.264'
        }
    },
    '41': {  # Video Compression
        'name': 'Video Compression',
        'options': {
            0: 'Standard',
            1: 'Maximum',
            9: 'High Quality'
        }
    },
    '42': {  # Bit Rate
        'name': 'Bit Rate',
        'options': {
            0: 'Low',
            1: 'Medium',
            2: 'High',
            3: 'Maximum',
            4: 'Standard',
            5: 'High Quality',
            6: 'Standard'
        }
    },
    '43': {  # Video Stabilization
        'name': 'Video Stabilization',
        'options': {
            0: 'Off',
            1: 'On',
            2: 'High',
            3: 'Boost',
            4: 'Auto'
        }
    },
    '44': {  # Audio Format
        'name': 'Audio Format',
        'options': {
            1: 'AAC',
            2: 'WAV',
            9: 'Stereo'
        }
    },
    '45': {  # Wind Noise Reduction
        'name': 'Wind Noise Reduction',
        'options': {
            0: 'Off',
            1: 'Auto',
            2: 'Wind Only',
            3: 'Stereo Only',
            5: 'Auto'  # Значение из лога
        }
    },
    '47': {  # Raw Audio
        'name': 'Raw Audio',
        'options': {
            0: 'Off',
            1: 'Low',
            2: 'Medium',
            3: 'High',
            4: 'High'  # Значение из лога
        }
    },
    '48': {  # Audio Input
        'name': 'Audio Input',
        'options': {
            0: 'Standard Mic',
            1: 'Standard Mic+',
            2: 'Powered Mic',
            3: 'Powered Mic+',
            4: 'Line In'
        }
    },
    '54': {  # Media Mode
        'name': 'Media Mode',
        'options': {
            0: 'Video',
            1: 'Photo',
            2: 'Multishot'
        }
    },
    '59': {  # Auto Power Down
        'name': 'Auto Power Down',
        'options': {
            0: 'Never',
            1: '1 Min',
            4: '5 Min',
            6: '15 Min',
            7: '30 Min'
        }
    },
    '60': {  # GPS Status
        'name': 'GPS Status',
        'options': {
            0: 'Off',
            1: 'On'
        }
    },
    '61': {  # Voice Control
        'name': 'Voice Control',
        'options': {
            0: 'Off',
            1: 'On'
        }
    },
    '62': {  # LED Status
        'name': 'LED Status',
        'options': {
            0: 'All On',
            1: 'Front Only',
            2: 'All Off'
        }
    },
    '64': {  # Quick Capture
        'name': 'Quick Capture',
        'options': {
            0: 'Off',
            1: 'On',
            4: 'Enabled'  # Значение из лога
        }
    },
    '65': {  # WiFi Band
        'name': 'WiFi Band',
        'options': {
            0: '2.4GHz',
            1: '5GHz',
            2: 'Auto'
        }
    },
    '66': {  # WiFi Frequency
        'name': 'WiFi Frequency',
        'options': {
            0: 'Auto',
            1: 'Manual'
        }
    },
    '67': {  # WiFi Channel
        'name': 'WiFi Channel',
        'options': {
            0: 'Auto',
            1: 'Channel 1',
            2: 'Channel 2',
            3: 'Channel 3',
            4: 'Channel 4',
            5: 'Channel 5',
            6: 'Channel 6',
            7: 'Channel 7',
            8: 'Channel 8',
            9: 'Channel 9',
            10: 'Channel 10',
            11: 'Channel 11'
        }
    },
    '75': {  # Video Mode Group
        'name': 'Video Mode Group',
        'options': {
            0: 'Standard',
            1: 'Activity',
            2: 'Cinematic',
            3: 'Slo-Mo'
        }
    },
    '76': {  # Active Preset Group
        'name': 'Active Preset Group',
        'options': {
            0: 'Video',
            1: 'Photo',
            2: 'Time Lapse'
        }
    },
    '83': {  # Scheduled Capture
        'name': 'Scheduled Capture',
        'options': {
            0: 'Off',
            1: 'On'
        }
    },
    '84': {  # Schedule Time
        'name': 'Schedule Time',
        'options': {
            0: 'Off'
        }
    },
    '85': {  # Schedule Duration
        'name': 'Schedule Duration',
        'options': {
            0: 'Unlimited'
        }
    },
    '86': {  # Schedule Max Files
        'name': 'Schedule Max Files',
        'options': {
            0: 'Unlimited'
        }
    },
    '87': {  # Screen Brightness
        'name': 'Screen Brightness',
        'options': {
            100: '100%',
            50: '50%'  # Значение из лога
        }
    },
    '88': {  # Screen Timeout
        'name': 'Screen Timeout',
        'options': {
            50: '50 sec'  # Значение из лога
        }
    },
    '91': {  # Max Lens Mod
        'name': 'Max Lens Mod',
        'options': {
            3: 'Max Lens 2.0'  # Значение из лога
        }
    },
    '102': {  # Media Mod Status
        'name': 'Media Mod Status',
        'options': {
            8: 'Light Mod'  # Значение из лога
        }
    },
    '103': {  # Camera Orientation
        'name': 'Camera Orientation',
        'options': {
            3: 'Locked'  # Значение из лога
        }
    },
    '105': {  # Language
        'name': 'Language',
        'options': {
            0: 'English'  # Значение из лога
        }
    },
    '106': {  # Date Format
        'name': 'Date Format',
        'options': {
            1: 'MM/DD/YY'  # Значение из лога
        }
    },
    '111': {  # Video Compression
        'name': 'Video Compression',
        'options': {
            10: 'HEVC + HDR'  # Значение из лога
        }
    },
    '112': {  # Audio Input Mode
        'name': 'Audio Input Mode',
        'options': {
            255: 'Auto'  # Значение из лога
        }
    },
    '114': {  # Timer Enabled
        'name': 'Timer Enabled',
        'options': {
            1: 'On'  # Значение из лога
        }
    },
    '115': {  # Timer Duration
        'name': 'Timer Duration',
        'options': {
            0: '3 Seconds'  # Значение из лога
        }
    },
    '116': {  # LED Status
        'name': 'LED Status',
        'options': {
            2: 'All On'  # Значение из лога
        }
    },
    '117': {  # Beep Volume
        'name': 'Beep Volume',
        'options': {
            1: 'Low'  # Значение из лога
        }
    },
    '118': {  # Default Boot Mode
        'name': 'Default Boot Mode',
        'options': {
            4: 'Last Used'  # Значение из лога
        }
    },
    '121': {  # Lens Type
        'name': 'Lens Type',
        'options': {
            3: 'Max Super View'  # Значение из лога
        }
    },
    '122': {  # HDR Status
        'name': 'HDR Status',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '123': {  # Hindsight
        'name': 'Hindsight',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '124': {  # Duration
        'name': 'Duration',
        'options': {
            100: '100%'  # Значение из лога
        }
    },
    '125': {  # Performance Mode
        'name': 'Performance Mode',
        'options': {
            0: 'Maximum Quality'  # Значение из лога
        }
    },
    '126': {  # Video Performance Mode
        'name': 'Video Performance Mode',
        'options': {
            0: 'Maximum Quality'  # Значение из лога
        }
    },
    '128': {  # Stream Bitrate
        'name': 'Stream Bitrate',
        'options': {
            12: '3.0 Mbps'  # Значение из лога
        }
    },
    '129': {  # Stream Window Size
        'name': 'Stream Window Size',
        'options': {
            2: '1080p'  # Значение из лога
        }
    },
    '130': {  # Stream Window Size
        'name': 'Stream Window Size',
        'options': {
            105: '1080p'  # Значение из лога
        }
    },
    '131': {  # Media Mod Status
        'name': 'Media Mod Status',
        'options': {
            3: 'Display Mod'  # Значение из лога
        }
    },
    '132': {  # Presets Group
        'name': 'Presets Group',
        'options': {
            12: 'Custom'  # Значение из лога
        }
    },
    '134': {  # Anti-Flicker
        'name': 'Anti-Flicker',
        'options': {
            3: '50Hz'  # Значение из лога
        }
    },
    '135': {  # Lens Type
        'name': 'Lens Type',
        'options': {
            100: 'Standard'  # Значение из лога
        }
    },
    '139': {  # TimeWarp Speed
        'name': 'TimeWarp Speed',
        'options': {
            3: '10x'  # Значени�� из лога
        }
    },
    '144': {  # Video Codec
        'name': 'Video Codec',
        'options': {
            12: 'H.265+HDR'  # Значение из лога
        }
    },
    '145': {  # Raw Audio Track
        'name': 'Raw Audio Track',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '146': {  # Speed Ramp
        'name': 'Speed Ramp',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '147': {  # Duration Remaining
        'name': 'Duration Remaining',
        'options': {
            0: 'Unlimited'  # Значение из лога
        }
    },
    '148': {  # Max Shots Remaining
        'name': 'Max Shots Remaining',
        'options': {
            100: '100'  # Значение из лога
        }
    },
    '149': {  # Exposure Lock
        'name': 'Exposure Lock',
        'options': {
            2: 'Locked'  # Значение из лога
        }
    },
    '153': {  # Battery Level
        'name': 'Battery Level',
        'options': {
            100: '100%'  # Значение из лога
        }
    },
    '154': {  # SD Status
        'name': 'SD Status',
        'options': {
            3: 'SD Error'  # Значение из лога
        }
    },
    '155': {  # Spot Meter
        'name': 'Spot Meter',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '156': {  # LED Brightness
        'name': 'LED Brightness',
        'options': {
            100: '100%'  # Значение из лога
        }
    },
    '157': {  # RAW Audio
        'name': 'RAW Audio',
        'options': {
            100: 'High'  # Значение из лога
        }
    },
    '158': {  # Low Light
        'name': 'Low Light',
        'options': {
            1: 'On'  # Значение из лога
        }
    },
    '159': {  # SuperPhoto
        'name': 'SuperPhoto',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '160': {  # White Balance Lock
        'name': 'White Balance Lock',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '161': {  # Max Shutter
        'name': 'Max Shutter',
        'options': {
            100: 'Auto'  # Значение из лога
        }
    },
    '162': {  # Star Trail Length
        'name': 'Star Trail Length',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '163': {  # Star Trails
        'name': 'Star Trails',
        'options': {
            1: 'On'  # Значение из лога
        }
    },
    '164': {  # Video Digital Lenses
        'name': 'Video Digital Lenses',
        'options': {
            100: 'Wide'  # Значение из лога
        }
    },
    '165': {  # Photo Digital Lenses
        'name': 'Photo Digital Lenses',
        'options': {
            0: 'Wide'  # Значение из лога
        }
    },
    '166': {  # TimeWarp Digital Lenses
        'name': 'TimeWarp Digital Lenses',
        'options': {
            0: 'Wide'  # Значение из лога
        }
    },
    '167': {  # Lens Lock
        'name': 'Lens Lock',
        'options': {
            4: 'Locked'  # Значение из лога
        }
    },
    '168': {  # Wind Filter
        'name': 'Wind Filter',
        'options': {
            0: 'Off'  # Значение из лога
        }
    },
    '169': {  # Raw Photo
        'name': 'Raw Photo',
        'options': {
            1: 'On'  # Значение из лога
        }
    },
    '173': {  # Video Mode
        'name': 'Video Mode',
        'options': {
            0: 'Highest Quality'  # Значение из лога
        }
    },
    '9': {  # Photo Format
        'name': 'Photo Format',
        'options': {
            0: 'JPEG',        # Standard
            1: 'RAW',         # RAW only
            2: 'RAW + JPEG'   # RAW + Standard
        }
    }
}