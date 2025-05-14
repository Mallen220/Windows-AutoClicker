import ast
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import END, filedialog, Listbox, simpledialog, SINGLE, Toplevel, Variable

from pynput import keyboard
import pyautogui
import pyperclip
from screeninfo import get_monitors

import Constants

# Windows: pyinstaller --onefile --windowed --icon=AutoClicker.ico --add-data "AutoClicker.ico;." --add-data "Presets;Presets" AutoClicker_main.py
# Ubuntu: pyinstaller --onefile --windowed --icon=AutoClicker.ico --add-data "AutoClicker.ico:." --add-data "Presets:Presets" AutoClicker_main.py
# sudo apt-get install xclip for Ubuntu


#####################################################
# Constant Variables
#####################################################

undo_stack = []
redo_stack = []
max_undo_redo = 200  # Limit to the number of undo/redo actions
overlay_windows = []
is_running = False
always_on_top = False
overlay_active = True
is_text_mode = False
delay_between_rounds = 500  # Default delay in milliseconds
min_random_time = 50
max_random_time = 4000

presets_dir = "Presets"
special_keys = Constants.special_keys
pressed_keys = set()
CTRL_KEY = "command" if os.name == "Darwin" or os.name == "posix" else "ctrl"


embedded_events = []

#####################################################
# Header, OS, and Icon
#####################################################


if os.name == "nt":
    isWindows = True
    if getattr(sys, "frozen", False):
        program_icon = os.path.join(sys._MEIPASS, "AutoClicker.ico")
    else:
        program_icon = "AutoClicker.ico"
else:
    isWindows = False
    program_icon = "AutoClicker.ico"  # Change the extension if needed

if not os.path.exists(presets_dir):
    os.makedirs(presets_dir)


def icon_per_os(window):
    if isWindows:
        window.iconbitmap(program_icon)
    else:
        print("No Linux Icon!")
        # window.iconphoto(False, tk.PhotoImage(file=program_icon))


#####################################################
# Keyboard Listener
#####################################################


def on_press(key):
    """Callback for when a key is pressed"""
    try:
        # Add the pressed key to the set
        pressed_keys.add(key.char if hasattr(key, "char") else key)
    except AttributeError:
        pressed_keys.add(key)


def on_release(key):
    """Callback for when a key is released"""
    try:
        # Remove the released key from the set
        pressed_keys.remove(key.char if hasattr(key, "char") else key)
    except KeyError:
        pass


def is_pressed(key):
    """Check if a specific key is currently being pressed and return a boolean."""
    # Handle single character keys (e.g., 'a', 'b', '1', etc.)
    if len(key) == 1:
        key_obj = keyboard.KeyCode(char=key)
    else:
        try:
            # Handle special keys like 'esc', 'shift', etc.
            key_obj = getattr(keyboard.Key, key.lower())
        except AttributeError:
            raise ValueError(f"Invalid key: {key}")

    # Check if the key is in the pressed_keys set
    return key_obj in pressed_keys


def wait_for_key(key):
    """Wait until a specific key is pressed"""
    while not is_pressed(key):
        pass


#####################################################
# Overlay Control TODO: There appears to be a duplicate method. Check.
#####################################################


# Function to create an overlay window for event numbers
def create_overlay():
    if not isWindows:
        return
    global overlay_windows
    overlay_windows = []

    # Create an overlay window for each monitor
    for monitor in get_monitors():
        overlay = tk.Toplevel(root)
        icon_per_os(overlay)

        # Set the geometry according to the monitor size and position
        overlay.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        overlay.overrideredirect(True)  # Remove window decorations (top bar, borders)
        overlay.attributes("-transparentcolor", overlay["bg"])

        # Allow adding visible text or widgets
        overlay.label_dict = {}
        overlay.monitor = monitor
        overlay_windows.append(overlay)


# Function to create an event number overlay on the correct monitor
def create_event_overlay(event_num, x, y):
    if overlay_active:
        event = embedded_events[event_num - 1]

        if event["type"] == "text" or event["type"] == "wait":
            return

        # Determine the label color based on the event type
        if event["type"] == "click":
            label_color = "red"
        elif event["type"] == "scroll":
            label_color = "green"
        else:
            try:
                if embedded_events[event_num]["type"] == "text":
                    label_color = "purple"
            except Exception as e:
                print(e)
            try:
                if embedded_events[event_num]["type"] == "wait":
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


# Function to update overlays for all events
def update_event_overlays():
    if not isWindows:
        return
    global overlay_windows

    for overlay in overlay_windows:
        for label in overlay.label_dict.values():
            label.destroy()

    for event_num, event in enumerate(embedded_events, 1):
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


#####################################################
# Event Control
#####################################################


# # Function to modify an event TODO: Modify to save details and delete event. Then create a new event in place. Update rearrange window details after.
def modify_event(new_event, idx=None):
    if 0 <= idx < len(embedded_events):
        original_type = embedded_events[idx]["type"]
        original_type = embedded_events[idx]["type"]
        print(f"Event {idx + 1} modified: {new_event}")


def save_details(
    idx, new_timeout, new_random_time, new_press_count=-1, new_click_type="left"
):
    try:
        if (
            embedded_events[idx]["type"] == "scroll"
            or embedded_events[idx]["type"] == "click"
        ):
            if new_press_count == -1:
                if embedded_events[idx]["type"] == "scroll":
                    new_press_count = 300
                else:
                    new_press_count = 1

            try:
                embedded_events[idx]["delay"] = int(new_timeout)
                embedded_events[idx]["press_count"] = new_press_count
                embedded_events[idx]["click_type"] = new_click_type
                embedded_events[idx]["random_time"] = new_random_time
                print(f"Updated details of Event {idx + 1}: {embedded_events[idx]}")

            except ValueError:
                print("Please enter a valid number for the detailed window.")
        elif embedded_events[idx]["type"] == "wait":
            try:
                embedded_events[idx]["delay"] = int(new_timeout)
                embedded_events[idx]["random_time"] = new_random_time
                print(f"Updated details of Event {idx + 1}: {embedded_events[idx]}")
            except ValueError:
                print("Please enter a valid number for the detailed window.")
    except Exception as e:
        print(
            "Wow! An error occurred. Are there no events? embedded_events[idx] is likely out of range. "
        )
    update_listbox()


def move_selected_event(idx=None):
    print("Waiting for 'space' key press to move the event...")
    wait_for_key("space")
    x, y = pyautogui.position()
    if idx is None:
        idx = len(embedded_events)  ##TODO: Test if this should be +1 or not
    if (
        embedded_events[idx]["type"] == "click"
        or embedded_events[idx]["type"] == "scroll"
    ):
        embedded_events[idx]["position"] = (x, y)
    update_event_overlays()


# Function to create an event
def create_event():  ##TODO: Rewrite to be several new buttons.
    global is_text_mode
    x, y = pyautogui.position()
    if is_pressed("ctrl_l") or is_pressed("ctrl_r") or is_pressed("ctrl"):
        if not is_text_mode:
            is_text_mode = True
            open_text_input()
        else:
            save_text()

    if is_pressed("w"):
        new_event = embedded_events.append(
            {
                "type": "wait",
                "delay": 100,
                "random_time": False,
            }
        )
        open_detailed_window(len(embedded_events) - 1)
    elif is_pressed("shift"):
        print("Waiting for 'space' key press to create the scroll event...")
        wait_for_key("space")

        new_event = embedded_events.append(
            {
                "type": "scroll",
                "position": (x, y),
                "press_count": 300,
                "delay": 100,
                "random_time": False,
            }
        )
    else:
        print("Waiting for 'space' key press to create the event...")
        wait_for_key("space")

        new_event = embedded_events.append(
            {
                "type": "click",
                "position": (x, y),
                "click_type": "left",
                "press_count": 1,
                "delay": 100,
                "random_time": False,
            }
        )
        print(f"Event created at position: ({x}, {y})")

    add_to_undo_stack(("create", new_event))
    update_event_overlays()


# Function to delete the newest event
def delete_event(idx=None):
    if embedded_events:
        if idx is None:
            deleted_event = embedded_events.pop()
        else:
            deleted_event = embedded_events[idx]

        add_to_undo_stack(("create", deleted_event))
        print(f"Deleted event at position: {deleted_event}")
        update_event_overlays()
        return True
    else:
        print("No events to delete.")
        return False


def save_delay(new_delay):
    global delay_between_rounds
    try:
        delay_between_rounds = new_delay
        print(f"Updated delay between rounds: {delay_between_rounds} ms")
    except ValueError:
        print("Please enter a valid number for the delay.")


def modify_event_order(
    original_event_idx, shift_amount
):  # -1 is down one, +1 is up one.
    # selected_idx = event_listbox.curselection()
    if (
        not original_event_idx
        or (original_event_idx[0] == 0 and shift_amount < 0)
        or (
            original_event_idx[0] == len(embedded_events) + shift_amount
            and shift_amount > 0
        )
    ):
        return
    selected_idx = original_event_idx[0]
    embedded_events[selected_idx], embedded_events[selected_idx + shift_amount] = (
        embedded_events[selected_idx + shift_amount],
        embedded_events[selected_idx],
    )
    update_listbox()
    event_listbox.select_set(selected_idx - 1)
    update_event_overlays()


#####################################################
# Text logic
#####################################################


def open_text_input(idx=None):
    global input_window, text_box, instant_type_var
    input_window = Toplevel(root)
    icon_per_os(input_window)
    input_window.title("Enter Text")

    input_window.geometry("500x400")
    label = tk.Label(
        input_window, text="Enter text to simulate (Press 'Enter' for new line):"
    )
    label.pack(pady=5)
    text_box = tk.Text(input_window, width=40, height=5)
    text_box.pack(pady=5)
    text_box.focus()
    instant_type_var = tk.BooleanVar()
    instant_type_check = tk.Checkbutton(
        input_window, text="Instant Type", variable=instant_type_var
    )

    instant_type_check.pack(pady=5)
    copy_button = tk.Button(
        input_window,
        text="Set to copy selection",
        command=lambda: set_text_input("Copy"),
    )
    copy_button.pack(pady=5)
    paste_button = tk.Button(
        input_window,
        text="Set to paste at cursor",
        command=lambda: set_text_input("Paste"),
    )
    paste_button.pack(pady=5)

    random_time_var = tk.BooleanVar()
    random_time_check = tk.Checkbutton(
        input_window, text="Random time", variable=random_time_var
    )
    random_time_check.pack(pady=5)

    save_button = tk.Button(
        input_window,
        text="Save Text",
        command=lambda: save_text(idx, random_time_var.get()),
    )
    save_button.pack(pady=5)


# For system set inputs
def set_text_input(text):
    text_box.delete(1.0, END)
    text_box.insert(END, text)
    save_text()


# Function to save text from the input box and close the window
def save_text(idx=None, is_random_time=False):
    global is_text_mode
    if not input_window:
        return

    try:
        text = text_box.get("1.0", tk.END).strip()
        if text:
            event_data = {
                "type": "text",
                "content": text,
                "delay": 0 if instant_type_var.get() else 100,
                "random_time": is_random_time,
            }
            if idx is None:
                embedded_events.append(event_data)
            else:
                embedded_events[idx] = event_data
            print(f"Text event created: {text}")
    except Exception as e:
        print(e)
        print(
            "An Error has occurred while saving text (Maybe bad text?). No text will be saved and the menu will be closed."
        )
    input_window.destroy()
    is_text_mode = False
    print("Text input mode exited.")


def type_text(text, delay):
    i = 0
    while i < len(text):
        char = text[i]
        if char == "\\":
            i += 1
            if i < len(text):
                special_key = text[i:]
                next_special_key = next(
                    (key for key in special_keys if special_key.startswith(key)), None
                )
                if next_special_key:
                    pyautogui.press(special_keys[next_special_key])
                    i += len(next_special_key) - 1
                else:
                    pyautogui.press(char)
        elif char == " ":
            pyautogui.press("space")
        elif char == "\n":
            pyautogui.press("enter")
        else:
            pyautogui.press(char)
        i += 1
        time.sleep(delay)


#####################################################
# Presets
#####################################################


# Function to save the current settings as a preset
def save_preset(name=None):
    if not name:
        name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")

    if not name:
        print("No name provided, preset save canceled.")
        return

    preset_path = os.path.join(presets_dir, f"{name}.txt")

    # Save the new preset
    with open(preset_path, "w") as f:
        f.write(f"- {name}\n")
        f.write(f"Delay: {delay_between_rounds}\n")
        for event_data in embedded_events:
            f.write(f"{str(event_data)}\n")
        f.write("\n")

    print(f"Preset '{name}' saved.")


def load_selected(selected_preset):  # listbox.curselection()
    global embedded_events, delay_between_rounds
    if selected_preset:
        embedded_events = []
        preset_name = event_listbox.get(selected_preset)
        preset_path = os.path.join(presets_dir, f"{preset_name}.txt")

        try:
            with open(preset_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("- "):
                        continue
                    elif line.startswith("Delay: "):
                        delay_between_rounds = int(line.split(":")[1].strip())
                    else:
                        try:
                            event_data = ast.literal_eval(line)
                            if "position" in event_data:
                                event_data["position"] = tuple(
                                    map(int, event_data["position"])
                                )

                            embedded_events.append(event_data)
                        except (ValueError, SyntaxError) as e:
                            print(f"Error loading event: {e}")
                            continue
        except FileNotFoundError:
            print(f"Preset file '{preset_name}' not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        update_event_overlays()


# Function to delete a preset file from the "Presets" directory
def delete_preset(name):
    if not os.path.exists(presets_dir):
        os.makedirs(presets_dir)

    file_path = os.path.join(presets_dir, f"{name}.txt")

    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Preset '{name}' deleted successfully.")
        else:
            print(f"Preset '{name}' not found.")
    except Exception as e:
        print(f"Error deleting preset '{name}': {e}")


def update_last_save_preset():
    if not os.path.exists(presets_dir):
        os.makedirs(presets_dir)

    # Check if the last_save.txt exists and if it does, update it
    try:
        save_preset("last_save")
    except Exception as e:
        print(f"Error updating last saved preset: {e}")


#####################################################
# Undo / Redo #TODO: FIXME
#####################################################


# Undo the last action
def undo():
    if undo_stack:
        action = undo_stack.pop()
        action_type, event = action

        if action_type == "create":
            if event in embedded_events:
                index = embedded_events.index(event)
                embedded_events.pop(index)
                print(f"Undid creation of event at position: {event['position']}")
                add_to_redo_stack(("create", event))

        elif action_type == "delete":
            embedded_events.append(event)
            embedded_events.sort(key=lambda e: e.get("position", (0, 0)))
            print(f"Undid deletion of event at position: {event['position']}")
            add_to_redo_stack(("create", event))

        update_event_overlays()
    else:
        print("No actions to undo.")


# Redo the last undone action
def redo():
    if redo_stack:
        print(redo_stack)

        action = redo_stack.pop()
        action_type, event = action

        if action_type == "create":
            embedded_events.append(event)
            embedded_events.sort(key=lambda e: e.get("position", (0, 0)))
            print(f"Redid creation of event at position: {event['position']}")
            add_to_undo_stack(("create", event))

        elif action_type == "delete":
            if event in embedded_events:
                index = embedded_events.index(event)
                embedded_events.pop(index)
                print(f"Redid deletion of event at position: {event['position']}")
                add_to_undo_stack(("delete", event))
    else:
        print("No actions to redo.")
    update_event_overlays()


def add_to_undo_stack(action):
    undo_stack.append(action)
    if len(undo_stack) > max_undo_redo:
        undo_stack.pop(0)


def add_to_redo_stack(action):
    redo_stack.append(action)
    if len(redo_stack) > max_undo_redo:
        redo_stack.pop(0)


#####################################################
# GUI's
#####################################################


def open_detailed_window(idx, rearrange_window=None):
    if (
        embedded_events[idx]["type"] == "click"
        or embedded_events[idx]["type"] == "scroll"
        or embedded_events[idx]["type"] == "wait"
    ):
        if rearrange_window is None:
            detailed_event_window = Toplevel(root)
        else:
            detailed_event_window = Toplevel(rearrange_window)
        icon_per_os(detailed_event_window)
        detailed_event_window.title(f"Set Timeout for Event {idx + 1}")

        timeout_label = tk.Label(detailed_event_window, text="Timeout? (ms)")
        timeout_label.pack(pady=5)
        timeout_entry = tk.Entry(detailed_event_window)
        timeout_entry.pack(pady=5)
        timeout_entry.insert(0, str(embedded_events[idx]["delay"]))

        if not embedded_events[idx]["type"] == "wait":
            press_count_label = tk.Label(
                detailed_event_window, text="How many times to click:"
            )
            press_count_label.pack(pady=5)
            press_count_entry = tk.Entry(detailed_event_window)
            press_count_entry.pack(pady=5)
            press_count_entry.insert(0, str(embedded_events[idx].get("press_count", 1)))

            options = ["left", "middle", "right"]
            clicked = tk.StringVar()
            clicked.set(embedded_events[idx].get("click_type", "left"))

            click_type_label = tk.Label(
                detailed_event_window, text="Type of Mouse Click"
            )
            click_type_label.pack(pady=5)
            click_type_entry = tk.OptionMenu(detailed_event_window, clicked, *options)
            click_type_entry.pack(pady=5)

        random_time_var = tk.BooleanVar()
        random_time_check = tk.Checkbutton(
            detailed_event_window, text="Random time", variable=random_time_var
        )
        random_time_check.pack(pady=5)

        delete_selected_event = tk.Button(
            detailed_event_window,
            text="Delete Event",
            command=lambda: delete_event(idx),
        )
        delete_selected_event.pack(pady=10)

        if not embedded_events[idx]["type"] == "wait":
            move_event = tk.Button(
                detailed_event_window,
                text="Move Event",
                command=move_selected_event,
            )
            move_event.pack(pady=10)

        save_button = tk.Button(  ##TODO: Test
            detailed_event_window,
            text="Save",
            command=lambda: (
                save_details(
                    idx,
                    timeout_entry.get(),
                    random_time_var.get(),
                    int(press_count_entry.get()),
                    click_type_entry.getvar(),
                ),
                detailed_event_window.destroy(),
            ),
        )
        save_button.pack(pady=10)
    elif embedded_events[idx]["type"] == "text":
        global is_text_mode
        if not is_text_mode:
            is_text_mode = True
            open_text_input(idx)
        else:
            save_text()

        while rearrange_window is not None:
            rearrange_window.destroy()


# Function to toggle "always on top"
def toggle_always_on_top():
    global always_on_top
    always_on_top = not always_on_top
    root.attributes("-topmost", always_on_top)
    always_on_top_button.config(
        text="Always on Top: ON" if always_on_top else "Always on Top: OFF"
    )


def update_listbox():
    try:
        event_listbox.delete(0, END)
        for i, event_data in enumerate(embedded_events):
            try:
                if event_data["type"] == "click" or event_data["type"] == "scroll":
                    event_listbox.insert(
                        END, f"Event {i + 1}: {event_data['position']}"
                    )
                elif event_data["type"] == "text":
                    event_listbox.insert(END, f"Event {i + 1}: {event_data['content']}")
                elif event_data["type"] == "wait":
                    event_listbox.insert(
                        END, f"Event {i + 1}: Wait {event_data['delay'] / 1000} s"
                    )
            except Exception:
                event_listbox.insert(END, f"Event {i + 1}: error loading event data")
    except Exception:
        print("Listbox does not exist. Failed to updated listbox. Exiting...")


# Function to rearrange events and adjust timings
def rearrange_events():
    global embedded_events, delay_between_rounds
    rearrange_window = Toplevel(root)
    icon_per_os(rearrange_window)
    rearrange_window.title("Rearrange Events")
    rearrange_window.geometry("500x700")
    event_listbox = Listbox(rearrange_window, selectmode=SINGLE, width=40, height=10)
    event_listbox.pack(pady=10)

    for i, event_data in enumerate(embedded_events):
        if event_data["type"] == "click" or event_data["type"] == "scroll":
            event_listbox.insert(END, f"Event {i + 1}: {event_data['position']}")
        elif event_data["type"] == "text":
            event_listbox.insert(END, f"Event {i + 1}: {event_data['content']}")
        elif event_data["type"] == "wait":
            event_listbox.insert(END, f"Event {i + 1}: Wait {event_data['delay']} ms")

    delay_label = tk.Label(rearrange_window, text="Delay Between Rounds (ms):")
    delay_label.pack(pady=5)
    delay_entry = tk.Entry(rearrange_window)
    delay_entry.pack(pady=5)
    delay_entry.insert(0, str(delay_between_rounds))

    save_delay_button = tk.Button(
        rearrange_window,
        text="Save Delay",
        command=lambda: save_delay(int(delay_entry.get())),
    )
    save_delay_button.pack(pady=5)

    def randomize_all_times():
        for i in range(len(embedded_events)):
            embedded_events[i]["random_time"] = True
            print(f"Randomized timing for Event {i + 1}: True")
        update_event_overlays()

    def delete_all_events():
        global embedded_events
        embedded_events = []
        update_event_overlays()
        update_listbox()

    delete_all_events_button = tk.Button(
        rearrange_window,
        text="Delete All Events (Can't Undo)",
        command=delete_all_events,
    )
    delete_all_events_button.pack(pady=5)

    randomize_all_button = tk.Button(
        rearrange_window,
        text="Randomize All Times",
        command=randomize_all_times,
    )
    randomize_all_button.pack(pady=5)

    # Function to load a selected preset
    def load_preset():
        global embedded_events, delay_between_rounds, event_listbox
        load_window = Toplevel(root)
        icon_per_os(load_window)
        load_window.title("Load Preset")
        load_window.geometry("300x500")
        event_listbox = Listbox(load_window, width=40, height=15)
        event_listbox.pack(pady=10)

        # List all .txt files in the presets directory
        presets = [f for f in os.listdir(presets_dir) if f.endswith(".txt")]
        for preset in presets:
            event_listbox.insert(END, preset[:-4])

        def upload_preset():
            file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if file_path:
                file_name = os.path.basename(file_path)
                new_file_path = os.path.join(presets_dir, file_name)
                if not os.path.exists(new_file_path):
                    os.rename(file_path, new_file_path)
                    print(f"Preset from {file_path} uploaded successfully.")
                else:
                    print(f"Preset already exists: {file_name}")
                load_window.destroy()

        def delete_selected_preset():
            global embedded_events
            selected_preset = event_listbox.curselection()
            if selected_preset:
                preset_name = event_listbox.get(selected_preset)
                preset_path = os.path.join(presets_dir, f"{preset_name}.txt")
                if os.path.exists(preset_path):
                    os.remove(preset_path)
                    print(f"Deleted preset: {preset_name}")
                    event_listbox.delete(selected_preset)
                    embedded_events = []
                    update_event_overlays()

        load_button = tk.Button(
            load_window,
            text="Load Selected Preset",
            command=lambda: (
                load_selected(event_listbox.curselection()),
                load_window.destroy(),
                rearrange_window.destroy(),
            ),
        )
        load_button.pack(pady=10)

        upload_button = tk.Button(
            load_window, text="Upload Preset", command=upload_preset
        )
        upload_button.pack(pady=10)

        delete_button = tk.Button(
            load_window, text="Delete Selected Preset", command=delete_selected_preset
        )
        delete_button.pack(pady=10)

    def on_double_click(useless):
        selected_idx = event_listbox.curselection()
        if selected_idx:
            open_detailed_window(selected_idx[0])

    event_listbox.bind("<Double-Button-1>", on_double_click)

    move_up_button = tk.Button(
        rearrange_window,
        text="Move Up",
        command=lambda: modify_event_order(event_listbox.curselection(), -1),
    )
    move_up_button.pack(pady=5)

    move_down_button = tk.Button(
        rearrange_window,
        text="Move Down",
        command=lambda: modify_event_order(event_listbox.curselection(), 1),
    )
    move_down_button.pack(pady=5)

    save_preset_button = tk.Button(
        rearrange_window, text="Save Preset", command=save_preset
    )
    save_preset_button.pack(pady=5)

    load_preset_button = tk.Button(
        rearrange_window, text="Load Preset", command=load_preset
    )
    load_preset_button.pack(pady=5)

    close_button = tk.Button(
        rearrange_window, text="Close", command=rearrange_window.destroy
    )
    close_button.pack(pady=10)


#####################################################
# Start / Stop Program
#####################################################


def start_program():
    global is_running
    is_running = True
    start_button.config(text="Stop Program", command=stop_program)
    print("Program started!")

    def sleep_appropriately(event):
        delay = (
            random_time_in_range(min_random_time, max_random_time)
            if event["random_time"]
            else event["delay"] / 1000
        )
        time.sleep(delay)

    def run_events():
        while is_running:
            for event in embedded_events:
                if not is_running:
                    break

                event_type = event["type"]

                if event_type in ("click", "scroll"):
                    x, y = event["position"]
                    press_count = event["press_count"]

                    if event_type == "click":
                        pyautogui.click(
                            x,
                            y,
                            button=str(event["click_type"]),
                            clicks=int(press_count),
                        )
                        print(
                            f"Clicked {event['click_type']} {press_count} time(s) at position: ({x}, {y})"
                        )
                    else:  # scroll
                        pyautogui.scroll(press_count, x=x, y=y)
                        print(f"Scrolled {press_count} time(s) at position: ({x}, {y})")

                    sleep_appropriately(event)

                elif event_type == "text":
                    content = event["content"]

                    hotkey_map = {
                        "Copy": [CTRL_KEY, "c"],
                        "Paste": [CTRL_KEY, "v"],
                        "Print": [CTRL_KEY, "p"],
                        "Control Right Arrow": [CTRL_KEY, "right"],
                    }

                    if content in hotkey_map:
                        pyautogui.hotkey(*hotkey_map[content])
                    elif event["delay"] == 0:
                        pyperclip.copy(content)
                        pyautogui.hotkey(CTRL_KEY, "v")
                    else:
                        delay = (
                            random_time_in_range(min_random_time, max_random_time)
                            if event["random_time"]
                            else event["delay"] / 1000
                        )
                        type_text(content, delay)

                    print(f"Typed text: {content}")

                elif event_type == "wait":
                    delay = event["delay"] / 1000
                    print(f"Waiting: {delay} s")
                    time.sleep(delay)

            time.sleep(random_time_in_range(400, 3000) / 1000)

    threading.Thread(target=run_events).start()
    monitor_space_key()


# Function to stop the program
def stop_program():
    global is_running
    is_running = False
    start_button.config(text="Start Program", command=start_program)
    print("Program stopped!")


# Function to close and save the events and update the "Last save" preset
def close_and_save():
    print("Updating 'Last save' preset...")

    update_last_save_preset()

    print("Closing program.")
    root.quit()


#####################################################
# Util's
#####################################################


def random_time_in_range(min_time=None, max_time=None):
    if min_time is None:
        min_time = min_random_time
    if max_time is None:
        max_time = max_random_time

    return random.randint(min_time, max_time) / 1000


# Function to monitor the space key to stop the program
def monitor_space_key():
    def stop_on_space_key():
        while is_running:
            if is_pressed("space"):
                stop_program()

    thread = threading.Thread(target=stop_on_space_key)
    thread.start()


root = tk.Tk()
root.title("Event Controller")
icon_per_os(root)
root.attributes("-alpha", 0.85)
root.geometry("225x350")


# Function to enable dragging the window by clicking anywhere
def on_drag_start(event):
    root._drag_data = {"x": event.x, "y": event.y}


def on_drag_motion(event):
    delta_x = event.x - root._drag_data["x"]
    delta_y = event.y - root._drag_data["y"]
    new_x = root.winfo_x() + delta_x
    new_y = root.winfo_y() + delta_y
    root.geometry(f"+{new_x}+{new_y}")


root.bind("<Button-1>", on_drag_start)
root.bind("<B1-Motion>", on_drag_motion)
root.bind("<Control-z>", lambda event: undo())
root.bind("<Control-Z>", lambda event: undo())
root.bind("<Control-Shift-Z>", lambda event: redo())

if isWindows:  # TODO: Make it work on Ubuntu and MacOS.
    create_overlay()

create_button = tk.Button(root, text="Create Event", command=create_event)
create_button.pack(pady=10)

delete_button = tk.Button(root, text="Delete Newest Event", command=delete_event)
delete_button.pack(pady=10)

rearrange_button = tk.Button(root, text="Rearrange Events", command=rearrange_events)
rearrange_button.pack(pady=10)

start_button = tk.Button(root, text="Start Program", command=start_program)
start_button.pack(pady=10)

always_on_top_button = tk.Button(
    root, text="Always on Top: Off", command=toggle_always_on_top
)
always_on_top_button.pack(pady=10)

close_button = tk.Button(root, text="Close & Save", command=close_and_save)
close_button.pack(pady=10)

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

root.mainloop()
