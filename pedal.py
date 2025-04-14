import subprocess
import signal
import sys
import os
from evdev import InputDevice, categorize, ecodes

DEVICE_PATH = '/dev/input/by-id/usb-OLYMPUS_IMAGING_CORP._HID_FootSwitch_RS_Series-event-mouse'  # Change this to your device link, run ls -l /dev/input/by-id/ in the terminal, and then add it after '/dev/input/by-id/'

# CHANGE THE NUMBERS (272, 273, 274) to the code given in SYN_REPORT in evtest
BUTTON_MAP = {
    272: ['workspace_left'],       # Left pedal → workspace left
    273: ['workspace_right'],       # Right pedal → workspace right
    274: ['open_terminal'],  # Middle button → Open terminal
}

try:
    device = InputDevice(DEVICE_PATH)
except FileNotFoundError:
    print(f"Device not found: {DEVICE_PATH}")
    sys.exit(1)

def cleanup_and_exit(signum=None, frame=None):
    print("Cleaning up and exiting...")
    try:
        device.ungrab()
    except Exception:
        pass
    sys.exit(0)

if "HYPRLAND_INSTANCE_SIGNATURE" not in os.environ:
    hypr_sock_dir = "/tmp/hypr"
    for entry in os.listdir(hypr_sock_dir):
        full_path = os.path.join(hypr_sock_dir, entry)
        if "main" in entry:
            os.environ["HYPRLAND_INSTANCE_SIGNATURE"] = full_path
            break

# Register signal handlers for graceful shutdown
for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
    signal.signal(sig, cleanup_and_exit)

print(f"Listening on {device.name} ({DEVICE_PATH})...")

# Tells the kernel that only this script receives events from the device. This is to stop it from being treated as a mouse, and to stop middle-click pasting in most linux desktops. You can optionally delete this line, but that means that the device will be treated as a mouse, e.g. left button will send LMB, etc.
try:
    device.grab()
except OSError as e:
    print(f"Failed to grab device: {e}")

try:
    for event in device.read_loop():
        if event.type == ecodes.EV_KEY and event.value == 1:  # Key down
            keycode = event.code
            if keycode in BUTTON_MAP:
                action = BUTTON_MAP[keycode]
                print(f"Sending: {action[0]}")

                if action[0] == 'workspace_left':
                    subprocess.run(["hyprctl", "dispatch", "workspace", "-1"])
                elif action[0] == 'workspace_right':
                    subprocess.run(["hyprctl", "dispatch", "workspace", "+1"])
                elif action[0] == 'open_terminal':
                    subprocess.run(["hyprctl", "dispatch", "exec", "alacritty"])
except Exception as e:
    print(f"Error: {e}")
finally:
    cleanup_and_exit()