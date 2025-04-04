import requests
import time

# Configuration parameters
camera_ip = "172.29.143.51"  # Example camera IP (replace with the actual IP)
port = 8080

# URLs for commands
power_down_url = f"http://{camera_ip}:{port}/gopro/camera/setting?setting=59&option=6"  # Set sleep mode in 15 minutes
keep_alive_url = f"http://{camera_ip}:{port}/gopro/camera/keep_alive"
start_recording_url = f"http://{camera_ip}:{port}/gopro/camera/shutter/start"

# Put the camera into sleep mode
response = requests.get(power_down_url)
if response.status_code == 200:
    print("The camera is set to sleep mode in 15 minutes.")
else:
    print("Error while trying to set sleep mode.")

# Send keep-alive signals to prevent the camera from fully shutting down
for _ in range(4):
    time.sleep(1)  # Send keep-alive every second to keep the camera active
    response = requests.get(keep_alive_url)
    if response.status_code == 200:
        print("Keep-alive command sent successfully.")
    else:
        print("Error while sending keep-alive command.")

# Wait for 4 seconds before starting recording
print("Waiting 4 seconds before starting recording...")
time.sleep(4)

# Start recording on the camera
response = requests.get(start_recording_url)
if response.status_code == 200:
    print("Recording started successfully.")
else:
    print("Error while trying to start recording.")
