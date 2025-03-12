"""
GoPro Camera Settings Description
This file contains descriptions of all camera settings and their values.
Each setting is documented with its ID, possible values, and meaning.
"""

CAMERA_SETTINGS = {
    # Video Settings
    "2": {
        "name": "Video Resolution",
        "value": 1,
        "meaning": "4K",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "100": "5.3K"
        }
    },
    
    "3": {
        "name": "Frames Per Second",
        "value": 6,
        "meaning": "50.0 fps",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the frames per second for video recording",
        "allowed_values": {
            "0": "240.0",
            "1": "120.0",
            "2": "100.0",
            "5": "60.0",
            "6": "50.0",
            "8": "30.0",
            "9": "25.0",
            "10": "24.0",
            "13": "200.0"
        }
    },
    
    "5": {
        "name": "Video Timelapse Rate",
        "value": 0,
        "meaning": "0.5 Seconds",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the interval for timelapse video",
        "allowed_values": {
            "0": "0.5 Seconds",
            "1": "1 Second",
            "2": "2 Seconds",
            "3": "5 Seconds",
            "4": "10 Seconds",
            "5": "30 Seconds",
            "6": "60 Seconds",
            "7": "2 Minutes",
            "8": "5 Minutes",
            "9": "30 Minutes",
            "10": "60 Minutes",
            "11": "3 Seconds"
        }
    },
    
    "6": {
        "name": "Video Framing",
        "value": 1,
        "meaning": "16:9",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the aspect ratio for video recording",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    
    "13": {
        "name": "Media Format",
        "value": 1,
        "meaning": "Time Lapse Video",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the media format for recording",
        "allowed_values": {
            "13": "Time Lapse Video",
            "20": "Time Lapse Photo",
            "21": "Night Lapse Photo",
            "26": "Night Lapse Video"
        }
    },
    
    "19": {
        "name": "Photo Mode",
        "value": 0,
        "meaning": "SuperPhoto",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo capture mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "24": {
        "name": "Video Bit Rate",
        "value": 0,
        "meaning": "Standard",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video bit rate",
        "allowed_values": {
            "0": "Standard",
            "1": "High",
            "2": "Low"
        }
    },
    
    "30": {
        "name": "Photo Timelapse Rate",
        "value": 110,
        "meaning": "0.5 Seconds",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the interval for timelapse photos",
        "allowed_values": {
            "11": "3 Seconds",
            "100": "60 Minutes",
            "101": "30 Minutes",
            "102": "5 Minutes",
            "103": "2 Minutes",
            "104": "60 Seconds",
            "105": "30 Seconds",
            "106": "10 Seconds",
            "107": "5 Seconds",
            "108": "2 Seconds"
        }
    },
    
    "31": {
        "name": "Photo Interval Duration",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the duration for interval photo capture",
        "allowed_values": {
            "0": "Off",
            "1": "5 Minutes",
            "2": "10 Minutes",
            "3": "15 Minutes",
            "4": "20 Minutes",
            "5": "30 Minutes",
            "6": "1 Hour",
            "7": "2 Hours",
            "8": "3 Hours",
            "9": "4 Hours",
            "10": "8 Hours"
        }
    },
    
    "32": {
        "name": "Nightlapse Rate",
        "value": 10,
        "meaning": "10 Seconds",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the interval for nightlapse photos",
        "allowed_values": {
            "1": "Auto",
            "2": "4 Seconds",
            "3": "5 Seconds",
            "4": "10 Seconds",
            "5": "15 Seconds",
            "6": "20 Seconds",
            "7": "30 Seconds",
            "8": "1 Minute",
            "9": "2 Minutes",
            "10": "5 Minutes",
            "11": "30 Minutes",
            "12": "60 Minutes"
        }
    },
    
    "37": {
        "name": "Photo Single Interval",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the single interval for photo capture",
        "allowed_values": {
            "0": "Off",
            "1": "0.5s",
            "2": "1s",
            "3": "2s",
            "4": "5s",
            "5": "10s",
            "6": "30s",
            "7": "60s"
        }
    },
    
    "41": {
        "name": "Video Resolution",
        "value": 9,
        "meaning": "1080p",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution for specific modes",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "100": "5.3K"
        }
    },
    
    "42": {
        "name": "Frame Rate",
        "value": 6,
        "meaning": "50.0",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the frame rate for specific modes",
        "allowed_values": {
            "0": "240.0",
            "1": "120.0",
            "2": "100.0",
            "5": "60.0",
            "6": "50.0",
            "8": "30.0",
            "9": "25.0",
            "10": "24.0",
            "13": "200.0"
        }
    },
    
    "43": {
        "name": "Webcam Digital Lenses",
        "value": 0,
        "meaning": "Wide",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the field of view for webcam mode",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "4": "Linear",
            "7": "Max SuperView"
        }
    },
    
    "44": {
        "name": "Video Resolution",
        "value": 9,
        "meaning": "1080p",
        "supported_cameras": ["HERO10 Black"],
        "description": "Secondary video resolution setting",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "100": "5.3K"
        }
    },
    
    "45": {
        "name": "Video Timelapse Rate",
        "value": 5,
        "meaning": "30 Seconds",
        "supported_cameras": ["HERO10 Black"],
        "description": "Secondary timelapse rate setting",
        "allowed_values": {
            "0": "0.5 Seconds",
            "1": "1 Second",
            "2": "2 Seconds",
            "3": "5 Seconds",
            "4": "10 Seconds",
            "5": "30 Seconds",
            "6": "60 Seconds",
            "7": "2 Minutes",
            "8": "5 Minutes",
            "9": "30 Minutes",
            "10": "60 Minutes"
        }
    },
    
    "47": {
        "name": "Video Lens",
        "value": 4,
        "meaning": "Linear",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the lens type for video",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock"
        }
    },
    
    "48": {
        "name": "Video Lens",
        "value": 3,
        "meaning": "Superview",
        "supported_cameras": ["HERO10 Black"],
        "description": "Alternative lens setting for video",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock"
        }
    },
    
    "54": {
        "name": "Anti-Flicker",
        "value": 1,
        "meaning": "PAL",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the anti-flicker mode",
        "allowed_values": {
            "0": "NTSC",
            "1": "PAL",
            "2": "60Hz",
            "3": "50Hz"
        }
    },
    
    "59": {
        "name": "Auto Power Down",
        "value": 0,
        "meaning": "Never",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the auto power down timer",
        "allowed_values": {
            "0": "Never",
            "1": "1 Min",
            "4": "5 Min",
            "6": "15 Min",
            "7": "30 Min"
        }
    },
    
    "60": {
        "name": "Controls",
        "value": 0,
        "meaning": "Easy",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the control mode",
        "allowed_values": {
            "0": "Easy",
            "1": "Pro"
        }
    },
    
    "61": {
        "name": "Easy Mode Speed",
        "value": 0,
        "meaning": "8X Ultra Slo-Mo",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the speed for easy mode",
        "allowed_values": {
            "0": "8X Ultra Slo-Mo",
            "1": "4X Slo-Mo",
            "2": "2X Slo-Mo",
            "3": "Real Speed",
            "4": "2X Speed Up",
            "5": "4X Speed Up",
            "6": "8X Speed Up",
            "7": "15X Speed Up",
            "8": "30X Speed Up"
        }
    },
    
    "62": {
        "name": "Easy Night Photo",
        "value": 0,
        "meaning": "Super Photo",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the night photo mode",
        "allowed_values": {
            "0": "Super Photo",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "64": {
        "name": "Photo Single Interval",
        "value": 4,
        "meaning": "2s",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the interval for single photo capture",
        "allowed_values": {
            "0": "Off",
            "1": "0.5s",
            "2": "1s",
            "3": "2s",
            "4": "5s",
            "5": "10s",
            "6": "30s",
            "7": "60s"
        }
    },
    
    "65": {
        "name": "Photo Interval Duration",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the duration for interval photos",
        "allowed_values": {
            "0": "Off",
            "1": "5 Minutes",
            "2": "10 Minutes",
            "3": "15 Minutes",
            "4": "20 Minutes",
            "5": "30 Minutes",
            "6": "1 Hour",
            "7": "2 Hours",
            "8": "3 Hours",
            "9": "4 Hours",
            "10": "8 Hours"
        }
    },
    
    "66": {
        "name": "Enable Night Photo",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Enables or disables night photo mode",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    
    "67": {
        "name": "Frame Rate",
        "value": 0,
        "meaning": "240.0",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the frame rate for specific modes",
        "allowed_values": {
            "0": "240.0",
            "1": "120.0",
            "2": "100.0",
            "5": "60.0",
            "6": "50.0",
            "8": "30.0",
            "9": "25.0",
            "10": "24.0",
            "13": "200.0"
        }
    },
    
    "75": {
        "name": "Photo Output",
        "value": 0,
        "meaning": "Standard",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo output format",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "3": "SuperPhoto"
        }
    },
    
    "76": {
        "name": "Photo Mode",
        "value": 0,
        "meaning": "SuperPhoto",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo capture mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "83": {
        "name": "GPS",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Enables or disables GPS",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    
    "84": {
        "name": "Wireless Band",
        "value": 0,
        "meaning": "2.4GHz",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the wireless band frequency",
        "allowed_values": {
            "0": "2.4GHz",
            "1": "5GHz",
            "2": "Auto"
        }
    },
    
    "85": {
        "name": "Video Bit Rate",
        "value": 0,
        "meaning": "Standard",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video bit rate mode",
        "allowed_values": {
            "0": "Standard",
            "1": "High",
            "2": "Low"
        }
    },
    
    "86": {
        "name": "Video Easy Mode",
        "value": 0,
        "meaning": "Highest Quality",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video quality in easy mode",
        "allowed_values": {
            "0": "Highest Quality",
            "1": "Standard Quality",
            "2": "Extended Battery"
        }
    },
    
    "87": {
        "name": "Profiles",
        "value": 0,
        "meaning": "Standard",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the color profile",
        "allowed_values": {
            "0": "Standard",
            "1": "Vibrant",
            "2": "Natural",
            "3": "Flat",
            "100": "Standard (Extended)"
        }
    },
    
    "88": {
        "name": "Setup Screen Saver",
        "value": 50,
        "meaning": "1 Min",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the screen saver timeout",
        "allowed_values": {
            "0": "Never",
            "1": "1 Min",
            "2": "2 Min",
            "3": "3 Min",
            "4": "5 Min"
        }
    },
    
    "91": {
        "name": "Video Framing",
        "value": 3,
        "meaning": "8:7",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video framing aspect ratio",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    
    "102": {
        "name": "Frame Rate",
        "value": 8,
        "meaning": "30.0 fps",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video frame rate",
        "allowed_values": {
            "0": "240.0",
            "1": "120.0",
            "2": "100.0",
            "5": "60.0",
            "6": "50.0",
            "8": "30.0",
            "9": "25.0",
            "10": "24.0",
            "13": "200.0"
        }
    },
    
    "103": {
        "name": "Video Lens",
        "value": 3,
        "meaning": "Superview",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video lens type",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock"
        }
    },
    
    "105": {
        "name": "Photo Lens",
        "value": 0,
        "meaning": "Wide",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo lens type",
        "allowed_values": {
            "19": "Narrow",
            "100": "Max SuperView",
            "101": "Wide",
            "102": "Linear"
        }
    },
    
    "106": {
        "name": "Photo Output",
        "value": 1,
        "meaning": "Raw",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo output format",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    
    "111": {
        "name": "Video Aspect Ratio",
        "value": 0,
        "meaning": "4:3",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video aspect ratio",
        "allowed_values": {
            "0": "4:3",
            "1": "16:9",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    
    "112": {
        "name": "Setup Language",
        "value": 255,
        "meaning": "System Default",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the interface language",
        "allowed_values": {
            "0": "English",
            "1": "Chinese",
            "2": "Japanese",
            "3": "Korean",
            "4": "Spanish",
            "5": "French",
            "6": "German",
            "7": "Italian",
            "8": "Portuguese",
            "9": "Russian",
            "255": "System Default"
        }
    },
    
    "114": {
        "name": "Framing",
        "value": 1,
        "meaning": "Vertical",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the capture framing",
        "allowed_values": {
            "0": "Horizontal",
            "1": "Vertical"
        }
    },
    
    "115": {
        "name": "Lapse Mode",
        "value": 0,
        "meaning": "TimeWarp",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the timelapse mode",
        "allowed_values": {
            "0": "TimeWarp",
            "1": "Time Lapse",
            "2": "Night Lapse"
        }
    },
    
    "116": {
        "name": "Multi Shot Aspect Ratio",
        "value": 2,
        "meaning": "Not documented for HERO10",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the multi-shot aspect ratio",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    
    "117": {
        "name": "Multi Shot Framing",
        "value": 1,
        "meaning": "16:9",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the multi-shot framing",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    
    "118": {
        "name": "Star Trails Length",
        "value": 4,
        "meaning": "Not documented for HERO10",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the star trails capture length",
        "allowed_values": {
            "0": "15 Minutes",
            "1": "30 Minutes",
            "2": "1 Hour",
            "3": "2 Hours",
            "4": "4 Hours"
        }
    },
    
    "121": {
        "name": "Video Lens",
        "value": 3,
        "meaning": "Superview",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video lens type",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock",
            "11": "Max HyperView",
            "12": "Ultra SuperView",
            "13": "Ultra Wide",
            "104": "Ultra HyperView"
        }
    },
    
    "122": {
        "name": "Photo Lens",
        "value": 0,
        "meaning": "Wide",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo lens type",
        "allowed_values": {
            "0": "Wide 12 MP",
            "10": "Linear 12 MP",
            "19": "Narrow",
            "27": "Wide 23 MP",
            "28": "Linear 13 MP",
            "31": "Wide 27 MP",
            "32": "Linear 27 MP",
            "41": "Ultra Wide 12 MP",
            "100": "Max SuperView",
            "101": "Wide",
            "102": "Linear"
        }
    },
    
    "123": {
        "name": "Time Lapse Digital Lenses",
        "value": 0,
        "meaning": "Wide",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the timelapse lens type",
        "allowed_values": {
            "19": "Narrow",
            "31": "Wide 27 MP",
            "32": "Linear 27 MP",
            "100": "Max SuperView",
            "101": "Wide",
            "102": "Linear"
        }
    },
    
    "124": {
        "name": "Photo Output",
        "value": 100,
        "meaning": "SuperPhoto",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo output mode",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    
    "125": {
        "name": "Photo Output",
        "value": 0,
        "meaning": "Standard",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo output format",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "3": "SuperPhoto"
        }
    },
    
    "126": {
        "name": "System Video Mode",
        "value": 0,
        "meaning": "Highest Quality",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the system video mode",
        "allowed_values": {
            "0": "Highest Quality",
            "1": "Extended Battery",
            "2": "Standard Quality"
        }
    },
    
    "128": {
        "name": "Media Format",
        "value": 12,
        "meaning": "Time Lapse Video",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the media format",
        "allowed_values": {
            "12": "Time Lapse Video (Legacy)",
            "13": "Time Lapse Video",
            "20": "Time Lapse Photo",
            "21": "Night Lapse Photo",
            "26": "Night Lapse Video"
        }
    },
    
    "129": {
        "name": "Video Framing",
        "value": 2,
        "meaning": "Full Frame",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video framing",
        "allowed_values": {
            "0": "16:9",
            "1": "4:3",
            "2": "Full Frame",
            "3": "8:7"
        }
    },
    
    "130": {
        "name": "Video Resolution",
        "value": 105,
        "meaning": "5.3K",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "105": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    
    "131": {
        "name": "Video Lens",
        "value": 3,
        "meaning": "Superview",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video lens type",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock",
            "11": "Max HyperView",
            "12": "Ultra SuperView",
            "13": "Ultra Wide",
            "104": "Ultra HyperView"
        }
    },
    
    "132": {
        "name": "Media Format",
        "value": 12,
        "meaning": "Time Lapse Video",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the media format",
        "allowed_values": {
            "13": "Time Lapse Video",
            "20": "Time Lapse Photo",
            "21": "Night Lapse Photo",
            "26": "Night Lapse Video"
        }
    },
    
    "134": {
        "name": "Anti-Flicker",
        "value": 3,
        "meaning": "50Hz",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the anti-flicker mode",
        "allowed_values": {
            "0": "NTSC",
            "1": "PAL",
            "2": "60Hz",
            "3": "50Hz"
        }
    },
    
    "135": {
        "name": "Hypersmooth",
        "value": 100,
        "meaning": "Standard",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video stabilization mode",
        "allowed_values": {
            "0": "Off",
            "1": "Low",
            "2": "High",
            "3": "Boost",
            "4": "Auto Boost",
            "100": "Standard"
        }
    },
    
    "139": {
        "name": "Hypersmooth",
        "value": 3,
        "meaning": "Boost",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the enhanced stabilization mode",
        "allowed_values": {
            "0": "Off",
            "1": "On",
            "2": "High",
            "3": "Boost",
            "4": "Auto Boost"
        }
    },
    
    "144": {
        "name": "Video Resolution",
        "value": 12,
        "meaning": "720p",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    
    "145": {
        "name": "Photo Mode",
        "value": 0,
        "meaning": "SuperPhoto",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "146": {
        "name": "Photo Output",
        "value": 0,
        "meaning": "Standard",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo output format",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    
    "147": {
        "name": "Enable Night Photo",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Enables or disables night photo mode",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    
    "148": {
        "name": "Video Bit Rate",
        "value": 100,
        "meaning": "High",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video bit rate",
        "allowed_values": {
            "0": "Standard",
            "1": "High",
            "100": "High"
        }
    },
    
    "149": {
        "name": "Video Lens",
        "value": 2,
        "meaning": "Narrow",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video lens type",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock",
            "11": "Max HyperView",
            "12": "Ultra SuperView",
            "13": "Ultra Wide",
            "104": "Ultra HyperView"
        }
    },
    
    "153": {
        "name": "Video Resolution",
        "value": 100,
        "meaning": "5.3K",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    
    "154": {
        "name": "Video Lens",
        "value": 3,
        "meaning": "Superview",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video lens type",
        "allowed_values": {
            "0": "Wide",
            "2": "Narrow",
            "3": "Superview",
            "4": "Linear",
            "7": "Max SuperView",
            "8": "Linear + Horizon Leveling",
            "9": "HyperView",
            "10": "Linear + Horizon Lock",
            "11": "Max HyperView",
            "12": "Ultra SuperView",
            "13": "Ultra Wide",
            "104": "Ultra HyperView"
        }
    },
    
    "155": {
        "name": "Photo Mode",
        "value": 0,
        "meaning": "SuperPhoto",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "156": {
        "name": "Video Resolution",
        "value": 100,
        "meaning": "5.3K",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    
    "157": {
        "name": "Video Resolution",
        "value": 100,
        "meaning": "5.3K",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    
    "158": {
        "name": "Controls",
        "value": 1,
        "meaning": "Pro",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the control mode",
        "allowed_values": {
            "0": "Easy",
            "1": "Pro"
        }
    },
    
    "159": {
        "name": "Easy Night Photo",
        "value": 0,
        "meaning": "Super Photo",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the night photo mode",
        "allowed_values": {
            "0": "Super Photo",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "160": {
        "name": "Enable Night Photo",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Enables or disables night photo mode",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    
    "161": {
        "name": "Photo Output",
        "value": 100,
        "meaning": "SuperPhoto",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo output mode",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    
    "162": {
        "name": "Max Lens",
        "value": 0,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Enables or disables Max Lens Mod",
        "allowed_values": {
            "0": "Off",
            "1": "On"
        }
    },
    
    "163": {
        "name": "Photo Output",
        "value": 1,
        "meaning": "Raw",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo output format",
        "allowed_values": {
            "0": "Standard",
            "1": "Raw",
            "2": "HDR",
            "100": "SuperPhoto"
        }
    },
    
    "164": {
        "name": "Video Resolution",
        "value": 100,
        "meaning": "5.3K",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video resolution",
        "allowed_values": {
            "1": "4K",
            "4": "2.7K",
            "9": "1080p",
            "12": "720p",
            "18": "4K 4:3",
            "25": "5K 4:3",
            "26": "5.3K 8:7",
            "27": "5.3K 4:3",
            "28": "4K 8:7",
            "37": "4K 1:1",
            "38": "900",
            "100": "5.3K",
            "107": "5.3K 8:7 V2",
            "108": "4K 8:7 V2",
            "109": "4K 9:16 V2",
            "110": "1080 9:16 V2",
            "111": "2.7K 4:3 V2"
        }
    },
    
    "165": {
        "name": "Photo Mode",
        "value": 0,
        "meaning": "SuperPhoto",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the photo mode",
        "allowed_values": {
            "0": "SuperPhoto",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "166": {
        "name": "Easy Night Photo",
        "value": 0,
        "meaning": "Super Photo",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the night photo mode",
        "allowed_values": {
            "0": "Super Photo",
            "1": "HDR",
            "2": "Standard",
            "3": "Raw"
        }
    },
    
    "167": {
        "name": "HindSight",
        "value": 4,
        "meaning": "Off",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the HindSight recording mode",
        "allowed_values": {
            "2": "15 Seconds",
            "3": "30 Seconds",
            "4": "Off"
        }
    },
    
    "168": {
        "name": "Wireless Band",
        "value": 0,
        "meaning": "2.4GHz",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the wireless band frequency",
        "allowed_values": {
            "0": "2.4GHz",
            "1": "5GHz",
            "2": "Auto"
        }
    },
    
    "169": {
        "name": "Controls",
        "value": 1,
        "meaning": "Pro",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the control mode",
        "allowed_values": {
            "0": "Easy",
            "1": "Pro"
        }
    },
    
    "173": {
        "name": "Video Performance Mode",
        "value": 0,
        "meaning": "Maximum Video Performance",
        "supported_cameras": ["HERO10 Black"],
        "description": "Sets the video performance mode",
        "allowed_values": {
            "0": "Maximum Video Performance",
            "1": "Extended Battery",
            "2": "Tripod / Stationary Video"
        }
    }
}

# All settings have been documented 