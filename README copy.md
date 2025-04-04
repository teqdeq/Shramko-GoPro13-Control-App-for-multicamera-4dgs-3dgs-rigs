# Shramko GoPro Control App

**Developed by Andrii Shramko**
* **Email**: [zmei116@gmail.com](mailto:zmei116@gmail.com)
* **LinkedIn**: [Andrii Shramko](https://www.linkedin.com/in/andrii-shramko/)
* **GitHub Repository**: [https://github.com/AndriiShramko/Shramko_GoPro_Control_App](https://github.com/AndriiShramko/Shramko_GoPro_Control_App)

**Tags**: #ShramkoVR #ShramkoCamera #ShramkoSoft

---

**⚠️ Disclaimer:**
> Please note: Much of the initial code documentation was generated with assistance from AI tools (like ChatGPT). While functional on the author's setup for managing GoPro Hero 10/13 cameras, some documentation details might contain inaccuracies or "hallucinations." The core functionality has been tested, but users should review the code and documentation critically. The primary goal was to create a working tool for synchronous multi-camera control in a scanner rig.

---

## Overview

**Shramko GoPro Control App** is a powerful software solution designed for synchronizing and managing multiple GoPro cameras (tested primarily on **GoPro Hero 13**, with potential compatibility for **Hero 10-12**) via USB. The application is capable of controlling a large number of cameras (potentially up to 1000, though tested with smaller arrays), allowing users to start/stop recording, adjust settings, synchronize time, and download files—all from a central interface or via scripts.

This tool is ideal for projects requiring multi-camera setups, such as **virtual reality studios**, **3D scanning rigs**, **advertising shoots**, **music videos**, or **film productions**. It simplifies the management of large GoPro arrays, enabling synchronized footage capture with ease.

## Demo Videos

* [![Video 1: GoPro Control App Demo](https://img.youtube.com/vi/YOUR_VIDEO_ID_1/0.jpg)](http://www.youtube.com/watch?v=YOUR_VIDEO_ID_1) *(Replace YOUR_VIDEO_ID_1 with actual ID)*
* [![Video 2: GoPro Control Features](https://img.youtube.com/vi/YOUR_VIDEO_ID_2/0.jpg)](http://www.youtube.com/watch?v=YOUR_VIDEO_ID_2) *(Replace YOUR_VIDEO_ID_2 with actual ID)*
* [![Video 3: GoPro Multi-Camera Setup](https://img.youtube.com/vi/YOUR_VIDEO_ID_3/0.jpg)](http://www.youtube.com/watch?v=YOUR_VIDEO_ID_3) *(Replace YOUR_VIDEO_ID_3 with actual ID)*

*(Note: The original image links were placeholders. Please replace the video IDs above with the actual YouTube video IDs from your links.)*

## Key Features

* **Multi-Camera USB Control**: Connect and manage multiple GoPro cameras simultaneously via USB.
* **Synchronized Recording**: Start and stop recording on all connected cameras at the same time.
* **Centralized Settings Management**:
    * Copy settings (ISO, shutter speed, white balance, etc.) from a designated "prime" camera to all others.
    * Set specific video modes or presets across all cameras.
* **Time Synchronization**: Ensure all cameras share the same system time (UTC based) for accurate alignment in post-production.
* **Automated File Management**:
    * Download media files from all cameras to a PC.
    * Automatically organize downloaded files into session-based folders ("scenes") with camera identifiers.
* **SD Card Management**: Format SD cards on all connected cameras remotely.
* **Camera Status Monitoring**: View the status (recording, battery, storage, etc.) of connected cameras (CLI and GUI options).
* **Power Control**: Turn off all connected cameras remotely.
* **Graphical User Interfaces (GUI)**: Includes PyQt5-based interfaces (`Gopro_Gui_interfase_Pyqt5.py`, `status_of_cameras_GUI.py`) for easier control and monitoring.
* **Modular Scripting**: Core functions are broken down into individual Python scripts for flexibility and automation.

## Requirements

* **Operating System**: Windows 10 or later (Primary development environment)
* **Python Version**: Python 3.11 or newer recommended.
* **Hardware**:
    * GoPro Cameras (Tested on Hero 13, potentially compatible with Hero 10, 11, 12 - User verification needed).
    * USB Hub(s) capable of handling the required number of cameras.
    * Reliable USB cables for each camera.
* **Dependencies**: All Python dependencies are listed in `requirements.txt`.

## Installation

1.  **Clone the Repository**:
    ```sh
    git clone [https://github.com/AndriiShramko/Shramko_GoPro_Control_App.git](https://github.com/AndriiShramko/Shramko_GoPro_Control_App.git)
    cd Shramko_GoPro_Control_App
    ```

2.  **Set Up a Virtual Environment** (Recommended):
    ```sh
    python -m venv venv
    ```
    Activate the environment:
    * Windows: `venv\Scripts\activate`
    * macOS/Linux: `source venv/bin/activate`

3.  **Install Dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4.  **GoPro USB Communication**: Ensure your system has the necessary drivers and permissions to communicate with GoPro cameras via USB. You might need to follow specific setup instructions for enabling GoPro USB API communication depending on your OS and camera firmware.

## Usage

### Running the GUI Applications

Two main GUI applications are available:

1.  **Main Control Interface**: Provides comprehensive control over cameras (connect, record, settings, download, format).
    ```sh
    python Gopro_Gui_interfase_Pyqt5.py
    ```
2.  **Status Monitoring Interface**: Focuses on displaying the real-time status of connected cameras.
    ```sh
    python status_of_cameras_GUI.py
    ```

### Using the GUI (`Gopro_Gui_interfase_Pyqt5.py`)

1.  **Connect Cameras**: Connect your GoPro cameras via USB and power them on.
2.  **Launch the GUI**: Run `python Gopro_Gui_interfase_Pyqt5.py`.
3.  **Establish Connection**: Use the "Connect to Cameras" button (or similar) to detect and initialize communication.
4.  **Control Options**:
    * **Copy Settings**: Select "Copy Settings from Prime Camera" to synchronize settings. (Ensure `prime_camera_sn.py` is configured).
    * **Record**: Use the "Record" button to start/stop recording simultaneously.
    * **Set Preset**: Apply a specific camera preset.
    * **Turn Off**: Power down all connected cameras.
    * **Download & Format Tab**:
        * Download files from all cameras. Files will be sorted by session/scene if using the appropriate function.
        * Format SD cards on all cameras.

### Running Individual Scripts (for Automation/CLI)

The core functionalities are available as standalone scripts. This is useful for automation or command-line workflows.

**Recommended Workflow:**

1.  **Detect & Prepare Cameras**:
    ```bash
    python goprolist_and_start_usb.py
    ```
    * This discovers cameras, enables USB control, and creates/updates `camera_cache.json`.

2.  **(Optional) Synchronize Time**:
    ```bash
    python date_time_sync.py
    ```

3.  **(Optional) Synchronize Settings**:
    * First, ensure `prime_camera_sn.py` contains the serial number of your reference camera.
    * Then run:
    ```bash
    python read_and_write_all_settings_from_prime_to_other.py
    ```

4.  **Start Recording**:
    * To sync time and start recording in one step:
        ```bash
        python sync_and_record.py
        ```
    * Or, to just start recording (assuming time/settings are already synced):
        ```bash
        python recording.py
        ```

5.  **Stop Recording**:
    ```bash
    python stop_record.py
    ```

6.  **Download Files**:
    * To download and sort by scene:
        ```bash
        python copy_to_pc_and_scene_sorting.py
        ```
    * To download into basic camera-specific folders:
        ```bash
        python copy_to_pc.py
        ```

7.  **(Optional) Format SD Cards**:
    * **Use with caution - this deletes all data!**
    ```bash
    python format_sd.py
    ```

8.  **(Optional) Turn Off Cameras**:
    ```bash
    python Turn_Off_Cameras.py
    ```

## Project Architecture & File Descriptions

The application uses a modular design, with scripts dedicated to specific tasks. Communication between scripts often relies on the `camera_cache.json` file, which stores information about detected cameras.

### Key Files and Modules

* **`camera_cache.json`**: Stores cached data (IP, name, status) about connected cameras, speeding up subsequent operations.
* **`prime_camera_sn.py`**: Contains the serial number of the "primary" camera used as a reference for copying settings. **You need to edit this file.**
* **`utils.py`**: Contains common utility functions used by multiple scripts (likely).

### GUI Modules

* **`Gopro_Gui_interfase_Pyqt5.py`**: Main PyQt5-based graphical user interface for full application control.
* **`status_of_cameras_GUI.py`**: PyQt5-based GUI specifically for monitoring the real-time status of connected cameras.
* **`Gopro_Gui_Interface.py`**: An earlier or alternative GUI version (potentially less feature-rich).
* **`icon.ico` / `ico/`**: Icon files used by the GUI applications.

### Core Control & Management Scripts

* **`goprolist_and_start_usb.py`**:
    * **Purpose**: Detects connected GoPros via USB, enables USB control mode on them, and saves their details to `camera_cache.json`. **This is usually the first script to run.**
* **`goprolist_usb_activate_time_sync.py`**:
    * **Purpose**: Combines camera discovery/USB activation with time synchronization (`date_time_sync.py`).
* **`date_time_sync.py`**:
    * **Purpose**: Synchronizes the system clock (UTC) of the host PC with all connected cameras listed in `camera_cache.json`. Crucial for multi-cam alignment.
* **`read_and_write_all_settings_from_prime_to_other.py`**:
    * **Purpose**: Reads all settings from the primary camera (defined in `prime_camera_sn.py`) and applies them to all other connected cameras. Ensures consistent setup. Relies on `set_video_mode.py` (likely for setting specific modes as part of the process).
* **`set_video_mode.py`**:
    * **Purpose**: Sets a specific video mode (resolution, frame rate, FOV) on connected cameras. Used by the settings sync script.
* **`set_preset_0.py`**:
    * **Purpose**: Applies a specific predefined camera preset (Preset 0 in this case) to all connected cameras.

### Recording Scripts

* **`recording.py`**:
    * **Purpose**: Sends the command to start video recording on all cameras listed in `camera_cache.json`. Attempts to ensure cameras are in video mode first.
* **`stop_record.py`**:
    * **Purpose**: Sends the command to stop video recording on all connected cameras simultaneously.
* **`sync_and_record.py`**:
    * **Purpose**: A convenience script that first runs time synchronization (`date_time_sync.py`) and then immediately starts recording (`recording.py`).
* **`goprolist_usb_activate_time_sync_record.py`**:
    * **Purpose**: A comprehensive script likely combining discovery, USB activation, time sync, and starting recording.

### File Management Scripts

* **`copy_to_pc.py`**:
    * **Purpose**: Downloads media files from all connected cameras to the PC, typically organizing them into folders based on camera serial number/identifier.
* **`copy_to_pc_and_scene_sorting.py`**:
    * **Purpose**: Downloads media files and sorts them into a structured hierarchy based on "scenes" (recording sessions) and camera identifiers. Creates folders like `destination_root/sceneXX_timestamp/camera_serial_file.MP4`. Relies on `copy_to_pc.py` and `prime_camera_sn.py` (potentially to identify the primary camera for session naming).
* **`format_sd.py`**:
    * **Purpose**: Sends a command to format the SD cards on all connected cameras. **Warning: Deletes all data.**

### Status & Utility Scripts

* **`status_of_cameras.py`**:
    * **Purpose**: Command-line script to retrieve and display the current status (recording state, battery, etc.) of connected cameras.
* **`Turn_Off_Cameras.py`**:
    * **Purpose**: Sends a command to power off all connected cameras.
* **`camera_orientation_lock.py`**:
    * **Purpose**: Locks the screen orientation on connected cameras.
* **`sleep.py`**:
    * **Purpose**: A simple utility to introduce delays, likely used within other scripts to allow time for camera operations to complete.

### Dependency Interaction Example (Connecting Cameras)

Gopro_Gui_interfase_Pyqt5.py (or script execution)└── Calls: goprolist_usb_activate_time_sync.py├── Uses: goprolist_and_start_usb.py (for discovery & USB enable)│   └── Writes/Reads: camera_cache.json└── Uses: date_time_sync.py (for time sync)└── Reads: camera_cache.json*(See original input for more detailed dependency chains for other actions like recording, copying settings, etc.)*

### File Sorting Structure (Example)

When using `copy_to_pc_and_scene_sorting.py`, files are organized under a chosen destination root directory:

destination_root/├── scene01_2024_03_21_15_30_45/│   ├── ABC123_GX010001.MP4  (File from camera with serial ABC123)│   ├── DEF456_GX010001.MP4  (File from camera DEF456)│   └── XYZ789_GX010001.MP4  (File from camera XYZ789)├── scene02_2024_03_21_15_35_12/│   ├── ABC123_GX010002.MP4│   ├── DEF456_GX010002.MP4│   └── XYZ789_GX010002.MP4└── ... more scenes
## Building Executables (`.exe`)

You can build standalone Windows executables using **PyInstaller**. This bundles the application and its dependencies, so users don't need to install Python.

1.  **Install PyInstaller**:
    ```sh
    pip install pyinstaller
    ```

2.  **Navigate to Project Directory**:
    ```sh
    cd path/to/Shramko_GoPro_Control_App
    ```

3.  **Build the Main GUI**:
    ```sh
    pyinstaller --onefile --windowed --icon=icon.ico Gopro_Gui_interfase_Pyqt5.py
    ```
    * `--onefile`: Creates a single `.exe` file.
    * `--windowed` (or `--noconsole`): Prevents the console window from appearing when running the GUI.
    * `--icon=icon.ico`: Sets the application icon.

4.  **Build the Status GUI**:
    ```sh
    pyinstaller --onefile --windowed --icon=icon.ico status_of_cameras_GUI.py
    ```

5.  **Locate Executable**: The `.exe` files will be created in the `dist` subfolder.

6.  **Distribution**: Distribute the `.exe` file. Ensure any necessary external files (like `camera_cache.json` if needed persistently, or `prime_camera_sn.py` if not embedded) are included alongside the executable if required by your specific build configuration.

7.  **Troubleshooting Builds**: If the `.exe` fails (e.g., `ModuleNotFoundError`), you might need to explicitly tell PyInstaller about hidden imports using the `--hidden-import=module_name` flag during the build command. Check the PyInstaller output and documentation for details. The original notes mention potentially needing `--hidden-import=zeroconf` or `zeroconf._utils.ipaddress`.

## FAQ and Troubleshooting

* **Cameras Not Detected?**
    * Check USB connections and power. Ensure cameras are in a compatible USB mode.
    * Verify USB drivers are installed correctly.
    * Run `goprolist_and_start_usb.py` manually and check its output and `camera_cache.json`.
    * Ensure no other software is conflicting with GoPro USB communication.
* **Recording Fails on Some Cameras?**
    * Check SD card space and status (is it full or corrupted?).
    * Check battery levels.
    * Ensure cameras are in video mode.
    * Run `goprolist_usb_activate_time_sync_record.py` or individual sync/record scripts and check logs for errors.
* **Settings Sync Not Working?**
    * Verify the serial number in `prime_camera_sn.py` is correct and matches a connected camera.
    * Check logs from `read_and_write_all_settings_from_prime_to_other.py` for specific setting errors.
* **`.exe` File Fails to Run?**
    * See the "Building Executables" section regarding `--hidden-import`.
    * Test the `.exe` on a clean machine (without Python installed) to ensure all dependencies were bundled.
* **Git "LF will be replaced by CRLF" Warnings?**
    * This is a line-ending warning common on Windows. Configure Git to handle line endings automatically: `git config --global core.autocrlf true`.
* **Firmware Updates?**
    * This application does **not** handle GoPro firmware updates. Please use GoPro's official methods.

## Use Cases

* **Virtual Reality / 3D Scanning**: Capture synchronized footage from multiple angles for photogrammetry or volumetric video.
* **Music Videos / Performances**: Record performances from various viewpoints simultaneously for dynamic editing.
* **Advertising / Product Shoots**: Create immersive or multi-perspective showcases of products.
* **Sports / Event Coverage**: Film live events from different locations with synchronized timecodes.
* **Scientific Research / Documentation**: Record experiments or processes requiring synchronized multi-camera observation.

## GoPro HERO13 USB Monitor Tool

Included in the project (or potentially as a related tool) is a GUI specifically for monitoring GoPro HERO13 status via USB.

* **Purpose**: Provides a real-time view of camera status (recording state, battery, storage, temperature, etc.).
* **Limitations**: HERO13 only, USB connection required, monitoring only (no control).
* **Launch**:
    * As script: `gopro_monitor` (if installed via `setup.py`)
    * As module: `python -m status_monitoring.main` (adjust path if needed)
* **Installation**: Requires separate installation steps if packaged independently (check for `setup.py` or specific instructions in its directory). `pip install -e .` suggests it might be installable as an editable package.

## Contribution

Contributions are welcome!

1.  **Reporting Issues**: Use the [GitHub Issues](https://github.com/AndriiShramko/Shramko_GoPro_Control_App/issues) tab to report bugs or suggest features. Provide detailed descriptions and steps to reproduce.
2.  **Pull Requests**:
    * Fork the repository.
    * Create a new branch for your changes (`git checkout -b feature/your-feature-name`).
    * Make your changes and commit them (`git commit -m "Add feature X"`).
    * Push the branch to your fork (`git push origin feature/your-feature-name`).
    * Open a Pull Request on the main repository, clearly describing your changes.
3.  **Code Style**: Follow PEP 8 guidelines. Consider using tools like `black` or `flake8`. Add comments for complex logic.
4.  **Community**: Be respectful and constructive in discussions.

## License

This software is provided free for **non-commercial use**.

For **commercial licensing**, please contact Andrii Shramko:
* **Email**: [zmei116@gmail.com](mailto:zmei116@gmail.com)
* **LinkedIn**: [Andrii Shramko](https://www.linkedin.com/in/andrii-shramko/)
