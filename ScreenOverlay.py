from screeninfo import get_monitors
import Constants
import pyautogui
import tkinter as tk


# Function to create an overlay window for event numbers
def create_overlay(root):
    if not Constants.is_windows_os():
        return
    global overlay_windows
    overlay_windows = []

    # Create an overlay window for each monitor
    for monitor in get_monitors():
        overlay = tk.Toplevel(root)
        Constants.icon_per_os(overlay)

        # Set the geometry according to the monitor size and position
        overlay.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        overlay.overrideredirect(True)  # Remove window decorations (top bar, borders)
        if Constants.is_windows_os():
            overlay.attributes("-transparentcolor", overlay["bg"])

        # Allow adding visible text or widgets
        overlay.label_dict = {}
        overlay.monitor = monitor
        overlay_windows.append(overlay)


# Function to update overlays for all events
def update_event_overlays():
    global overlay_windows

    for overlay in overlay_windows:
        for label in overlay.label_dict.values():
            label.destroy()

    for event_num, event in enumerate(Constants.embedded_events, 1):
        if event["type"] == "click" or event["type"] == "scroll":
            x, y = event["position"]
            create_event_overlay(event_num, x, y)
        elif event["type"] == "text" or event["type"] == "wait":
            x, y = pyautogui.position()
            create_event_overlay(event_num, x, y)


# Function to determine which monitor the event was created on
def get_monitor_for_position(x, y):
    monitors = get_monitors()
    for monitor in monitors:
        if (
                monitor.x <= x < monitor.x + monitor.width
                and monitor.y <= y < monitor.y + monitor.height
        ):
            return monitor
    return monitors[0]  # Fallback to the main monitor if not found


# Function to create an event number overlay on the correct monitor
def create_event_overlay(event_num, x, y):
    event = Constants.embedded_events[event_num - 1]

    if event["type"] == "text" or event["type"] == "wait":
        return

    # Determine the label color based on the event type
    if event["type"] == "click":
        label_color = "red"
    elif event["type"] == "scroll":
        label_color = "green"
    else:
        try:
            if Constants.embedded_events[event_num]["type"] == "text":
                label_color = "purple"
        except Exception as e:
            print(e)
        try:
            if Constants.embedded_events[event_num]["type"] == "wait":
                label_color = "yellow"
        except Exception as e:
            print(e)

    # Find the monitor where this event should be displayed
    monitor = get_monitor_for_position(x, y)

    # Find the corresponding overlay window for this monitor
    for overlay in overlay_windows:
        if overlay.monitor == monitor:
            # Adjust position relative to the monitor's top-left corner
            adjusted_x = x - monitor.x
            adjusted_y = y - monitor.y

            # Create a label for the event number
            label = tk.Label(
                overlay, text=str(event_num), fg=label_color, font=("Arial", 24)
            )
            label.place(x=adjusted_x, y=adjusted_y)

            # Store the label in the overlay's label dictionary
            overlay.label_dict[event_num] = label
            break