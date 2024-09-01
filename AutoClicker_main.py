import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import END, filedialog, Listbox, simpledialog, SINGLE, Toplevel

import keyboard
import pyautogui
import pyperclip
from screeninfo import get_monitors

# pyinstaller --onefile --windowed --icon=AutoClicker.ico --add-data "AutoClicker.ico;." --add-data "Presets;Presets" AutoClicker_main.py

undo_stack = []
redo_stack = []
max_undo_redo = 25  # Limit to the number of undo/redo actions
overlay_windows = []
is_running = False
always_on_top = False
overlay_active = True
is_text_mode = False
delay_between_rounds = 500  # Default delay in milliseconds
min_random_time = 50
max_random_time = 4000

embedded_events = []

# Determine the path to the icon and presets directory
if getattr(sys, "frozen", False):
    program_icon = os.path.join(sys._MEIPASS, "AutoClicker.ico")
else:
    program_icon = "AutoClicker.ico"

presets_dir = "Presets"
if not os.path.exists(presets_dir):
    os.makedirs(presets_dir)

special_keys = {
    "t": "t",
    "r": "r",
    "accept": "accept",
    "add": "add",
    "alt": "alt",
    "altleft": "altleft",
    "altright": "altright",
    "apps": "apps",
    "backspace": "backspace",
    "browserback": "browserback",
    "browserfavorites": "browserfavorites",
    "browserforward": "browserforward",
    "browserhome": "browserhome",
    "browserrefresh": "browserrefresh",
    "browsersearch": "browsersearch",
    "browserstop": "browserstop",
    "capslock": "capslock",
    "clear": "clear",
    "convert": "convert",
    "ctrl": "ctrl",
    "ctrlleft": "ctrlleft",
    "ctrlright": "ctrlright",
    "decimal": "decimal",
    "del": "del",
    "delete": "delete",
    "divide": "divide",
    "down": "down",
    "end": "end",
    "enter": "enter",
    "esc": "esc",
    "escape": "escape",
    "execute": "execute",
    "f1": "f1",
    "f10": "f10",
    "f11": "f11",
    "f12": "f12",
    "f13": "f13",
    "f14": "f14",
    "f15": "f15",
    "f16": "f16",
    "f17": "f17",
    "f18": "f18",
    "f19": "f19",
    "f2": "f2",
    "f20": "f20",
    "f21": "f21",
    "f22": "f22",
    "f23": "f23",
    "f24": "f24",
    "f3": "f3",
    "f4": "f4",
    "f5": "f5",
    "f6": "f6",
    "f7": "f7",
    "f8": "f8",
    "f9": "f9",
    "final": "final",
    "fn": "fn",
    "hanguel": "hanguel",
    "hangul": "hangul",
    "hanja": "hanja",
    "help": "help",
    "home": "home",
    "insert": "insert",
    "junja": "junja",
    "kana": "kana",
    "kanji": "kanji",
    "launchapp1": "launchapp1",
    "launchapp2": "launchapp2",
    "launchmail": "launchmail",
    "launchmediaselect": "launchmediaselect",
    "left": "left",
    "modechange": "modechange",
    "multiply": "multiply",
    "nexttrack": "nexttrack",
    "nonconvert": "nonconvert",
    "num0": "num0",
    "num1": "num1",
    "num2": "num2",
    "num3": "num3",
    "num4": "num4",
    "num5": "num5",
    "num6": "num6",
    "num7": "num7",
    "num8": "num8",
    "num9": "num9",
    "numlock": "numlock",
    "pagedown": "pagedown",
    "pageup": "pageup",
    "pause": "pause",
    "pgdn": "pgdn",
    "pgup": "pgup",
    "playpause": "playpause",
    "prevtrack": "prevtrack",
    "print": "print",
    "printscreen": "printscreen",
    "prntscrn": "prntscrn",
    "prtsc": "prtsc",
    "prtscr": "prtscr",
    "return": "return",
    "right": "right",
    "scrolllock": "scrolllock",
    "select": "select",
    "separator": "separator",
    "shift": "shift",
    "shiftleft": "shiftleft",
    "shiftright": "shiftright",
    "sleep": "sleep",
    "space": "space",
    "stop": "stop",
    "subtract": "subtract",
    "tab": "tab",
    "up": "up",
    "volumedown": "volumedown",
    "volumemute": "volumemute",
    "volumeup": "volumeup",
    "win": "win",
    "winleft": "winleft",
    "winright": "winright",
    "yen": "yen",
    "command": "command",
    "option": "option",
    "optionleft": "optionleft",
    "optionright": "optionright",
}


# Function to modify an event
def modify_event(
    index,
    new_event,
    new_timing,
    new_click_type=None,
    new_press_count=None,
    new_random_time=None,
):
    if 0 <= index < len(embedded_events):
        if isinstance(embedded_events[index], dict):
            if "type" in embedded_events[index]:
                if embedded_events[index]["type"] == "click":
                    embedded_events[index]["position"] = new_event
                    embedded_events[index]["delay"] = new_timing
                    if new_click_type is not None:
                        embedded_events[index]["click_type"] = new_click_type
                    if new_random_time is not None:
                        embedded_events[index]["random_time"] = new_random_time
                    else:
                        embedded_events[index]["random_time"] = False
                    if new_press_count is not None:
                        embedded_events[index]["press_count"] = new_press_count
                elif embedded_events[index]["type"] == "text":
                    embedded_events[index]["content"] = new_event
                    embedded_events[index]["delay"] = new_timing
        print(f"Event {index + 1} modified: {new_event}, Delay: {new_timing}ms")


# Function to create an overlay window for event numbers
def create_overlay():
    global overlay_windows
    overlay_windows = []

    # Create an overlay window for each monitor
    for monitor in get_monitors():
        overlay = tk.Toplevel(root)
        overlay.iconbitmap(program_icon)
        overlay.attributes("-alpha", 0.5)
        overlay.attributes("-topmost", True)

        # Set the geometry according to the monitor size and position
        overlay.geometry(f"{monitor.width}x{monitor.height}+{monitor.x}+{monitor.y}")
        overlay.overrideredirect(True)
        overlay.attributes("-transparentcolor", overlay["bg"])

        overlay.label_dict = {}
        overlay.monitor = monitor
        overlay_windows.append(overlay)


# Function to update overlays for all events
def update_event_overlays():
    global overlay_windows

    for overlay in overlay_windows:
        for label in overlay.label_dict.values():
            label.destroy()

    for event_num, event in enumerate(embedded_events, 1):
        if event["type"] == "click" or event["type"] == "scroll":
            x, y = event["position"]
            create_event_overlay(event_num, x, y)
        elif event["type"] == "text":
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
    if overlay_active:
        event = embedded_events[event_num - 1]

        if event["type"] == "text":
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


# Function to create an event
def create_event():
    global is_text_mode
    if keyboard.is_pressed("ctrl"):
        if not is_text_mode:
            is_text_mode = True
            open_text_input()
        else:
            stop_text_input()
    else:
        if keyboard.is_pressed("shift"):
            print("Waiting for 'space' key press to create the scroll event...")
            keyboard.wait("space")
            x, y = pyautogui.position()

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
            keyboard.wait("space")
            x, y = pyautogui.position()

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

        redo_stack.clear()
        update_event_overlays()


# Function to stop text input mode and close the input window
def stop_text_input():
    if input_window:
        save_text()


# Function to delete the newest event
def delete_newest_event():
    if embedded_events:
        deleted_event = embedded_events.pop()
        add_to_undo_stack(("create", deleted_event))
        print(f"Deleted event at position: {deleted_event}")

        update_event_overlays()
        print("Deleted the newest event.")
    else:
        print("No events to delete.")


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


# Function to toggle "always on top"
def toggle_always_on_top():
    global always_on_top
    always_on_top = not always_on_top
    root.attributes("-topmost", always_on_top)
    always_on_top_button.config(
        text="Always on Top: ON" if always_on_top else "Always on Top: OFF"
    )


def open_text_input():
    global input_window, text_box, instant_type_var
    input_window = Toplevel(root)
    input_window.iconbitmap(program_icon)
    input_window.title("Enter Text")
    input_window.geometry("500x350")
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
    save_button = tk.Button(input_window, text="Save Text", command=save_text)
    save_button.pack(pady=5)


def set_text_input(text):
    text_box.delete(1.0, END)
    text_box.insert(END, text)
    save_text()


# Function to save text from the input box and close the window
def save_text():
    global is_text_mode
    try:
        text = text_box.get("1.0", tk.END).strip()
        if text:
            event_data = {
                "type": "text",
                "content": text,
                "delay": 0 if instant_type_var.get() else 100,
                "random_time": False,
            }
            embedded_events.append(event_data)
            print(f"Text event created: {text}")
    except Exception as e:
        print(e)
        print(
            "An Error has occurred while saving text (Maybe bad text?). No text will be saved and the menu will be closed."
        )
    input_window.destroy()
    is_text_mode = False
    print("Text input mode exited.")


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
            if event_data["type"] == "click":
                f.write(
                    f"{event_data['position']}\t{event_data['delay']}\t{event_data['click_type']}\t{event_data['press_count']}\t{event_data['random_time']}\n"
                )
            elif event_data["type"] == "scroll":
                f.write(
                    f"{event_data['position']}\t{event_data['delay']}\t{event_data['press_count']}\t{event_data['random_time']}\tscroll\n"
                )
            elif event_data["type"] == "text":
                f.write(
                    f"{event_data['content']}\t{event_data['delay']}\t{event_data['random_time']}\n"
                )
        f.write("\n")

    print(f"Preset '{name}' saved.")


# Function to rearrange events and adjust timings
def rearrange_events():
    global embedded_events, delay_between_rounds
    rearrange_window = Toplevel(root)
    rearrange_window.iconbitmap(program_icon)
    rearrange_window.title("Rearrange Events")
    rearrange_window.geometry("500x700")
    event_listbox = Listbox(rearrange_window, selectmode=SINGLE, width=40, height=10)
    event_listbox.pack(pady=10)

    for i, event_data in enumerate(embedded_events):
        if event_data["type"] == "click" or event_data["type"] == "scroll":
            event_listbox.insert(END, f"Event {i + 1}: {event_data['position']}")
        elif event_data["type"] == "text":
            event_listbox.insert(END, f"Event {i + 1}: {event_data['content']}")

    delay_label = tk.Label(rearrange_window, text="Delay Between Rounds (ms):")
    delay_label.pack(pady=5)
    delay_entry = tk.Entry(rearrange_window)
    delay_entry.pack(pady=5)
    delay_entry.insert(0, str(delay_between_rounds))

    def save_delay():
        global delay_between_rounds
        try:
            delay_between_rounds = int(delay_entry.get())
            print(f"Updated delay between rounds: {delay_between_rounds} ms")
        except ValueError:
            print("Please enter a valid number for the delay.")

    save_delay_button = tk.Button(
        rearrange_window, text="Save Delay", command=save_delay
    )
    save_delay_button.pack(pady=5)

    def move_up():
        selected_idx = event_listbox.curselection()
        if not selected_idx or selected_idx[0] == 0:
            return
        selected_idx = selected_idx[0]
        embedded_events[selected_idx], embedded_events[selected_idx - 1] = (
            embedded_events[selected_idx - 1],
            embedded_events[selected_idx],
        )
        update_listbox()
        event_listbox.select_set(selected_idx - 1)
        update_event_overlays()

    def move_down():
        selected_idx = event_listbox.curselection()
        if not selected_idx or selected_idx[0] == len(embedded_events) - 1:
            return
        selected_idx = selected_idx[0]
        embedded_events[selected_idx], embedded_events[selected_idx + 1] = (
            embedded_events[selected_idx + 1],
            embedded_events[selected_idx],
        )
        update_listbox()
        event_listbox.select_set(selected_idx + 1)
        update_event_overlays()

    def update_listbox():
        event_listbox.delete(0, END)
        for i, event_data in enumerate(embedded_events):
            event_listbox.insert(END, f"Event {i + 1}: {event_data['position']}")

    def randomize_all_times():
        for i in range(len(embedded_events)):
            embedded_events[i]["random_time"] = True
            print(f"Randomized timing for Event {i + 1}: True")
        update_event_overlays()

    def open_detailed_window(idx):
        detailed_event_window = Toplevel(rearrange_window)
        detailed_event_window.iconbitmap(program_icon)
        detailed_event_window.title(f"Set Timeout for Event {idx + 1}")

        timeout_label = tk.Label(detailed_event_window, text="Timeout? (ms)")
        timeout_label.pack(pady=5)
        timeout_entry = tk.Entry(detailed_event_window)
        timeout_entry.pack(pady=5)
        timeout_entry.insert(0, str(embedded_events[idx]["delay"]))

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

        click_type_label = tk.Label(detailed_event_window, text="Type of Mouse Click")
        click_type_label.pack(pady=5)
        click_type_entry = tk.OptionMenu(detailed_event_window, clicked, *options)
        click_type_entry.pack(pady=5)

        random_time_var = tk.BooleanVar()
        random_time_check = tk.Checkbutton(
            detailed_event_window, text="Random time", variable=random_time_var
        )
        random_time_check.pack(pady=5)

        def move_selected_event():
            print("Waiting for 'space' key press to move the event...")
            keyboard.wait("space")
            x, y = pyautogui.position()

            if embedded_events[idx]["type"] == "click":
                embedded_events[idx] = {
                    "type": "click",
                    "position": (x, y),
                    "click_type": embedded_events[idx]["click_type"],
                    "press_count": embedded_events[idx]["press_count"],
                    "delay": embedded_events[idx]["delay"],
                }
            elif embedded_events[idx]["type"] == "scroll":
                embedded_events[idx] = {
                    "type": "scroll",
                    "position": (x, y),
                    "press_count": embedded_events[idx]["press_count"],
                    "delay": embedded_events[idx]["delay"],
                }
            update_event_overlays()

        move_event = tk.Button(
            detailed_event_window, text="Move Event", command=move_selected_event
        )
        move_event.pack(pady=10)

        def save_details():
            new_timeout = timeout_entry.get()
            try:
                new_press_count = int(press_count_entry.get())
            except ValueError:
                if embedded_events[idx]["type"] == "scroll":
                    new_press_count = 300
                else:
                    new_press_count = 1

            try:
                embedded_events[idx]["delay"] = int(new_timeout)
                embedded_events[idx]["press_count"] = new_press_count
                embedded_events[idx]["click_type"] = clicked.get()
                embedded_events[idx]["random_time"] = random_time_var.get()
                print(f"Updated details of Event {idx + 1}: {embedded_events[idx]}")
                update_listbox()
                detailed_event_window.destroy()
            except ValueError:
                print("Please enter a valid number for the detailed window.")

        save_button = tk.Button(
            detailed_event_window, text="Save", command=save_details
        )
        save_button.pack(pady=10)

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
        load_window = Toplevel(root)
        load_window.iconbitmap(program_icon)
        load_window.title("Load Preset")
        load_window.geometry("300x500")
        listbox = Listbox(load_window, width=40, height=15)
        listbox.pack(pady=10)

        # List all .txt files in the presets directory
        presets = [f for f in os.listdir(presets_dir) if f.endswith(".txt")]
        for preset in presets:
            listbox.insert(END, preset[:-4])

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

        def load_selected():
            global embedded_events, delay_between_rounds
            selected_preset = listbox.curselection()
            if selected_preset:
                embedded_events = []
                preset_name = listbox.get(selected_preset)
                preset_path = os.path.join(presets_dir, f"{preset_name}.txt")
                with open(preset_path, "r") as f:
                    lines = f.readlines()
                    loading = False
                    for line in lines:
                        if line.strip() == f"- {preset_name}":
                            loading = True
                            continue
                        if loading and not line.strip():
                            break
                        if loading:
                            if line.startswith("Delay:"):
                                delay_between_rounds = int(line.split(":")[1].strip())
                            else:
                                event_data = line.split("\t")
                                if len(event_data) >= 5:
                                    (
                                        event,
                                        timing,
                                        temp_click_type,
                                        temp_press_count,
                                        temp_random_timing,
                                    ) = event_data[:5]
                                    if event.startswith("("):
                                        x, y = map(int, event.strip("()").split(","))
                                        embedded_events.append(
                                            {
                                                "type": "click",
                                                "position": (x, y),
                                                "click_type": temp_click_type,
                                                "press_count": int(temp_press_count),
                                                "delay": int(timing),
                                                "random_time": bool(temp_random_timing),
                                            }
                                        )
                                    elif event.endswith("scroll"):
                                        x, y = map(int, event.strip("()").split(","))
                                        embedded_events.append(
                                            {
                                                "type": "scroll",
                                                "position": (x, y),
                                                "press_count": int(temp_press_count),
                                                "delay": int(timing),
                                                "random_time": bool(temp_random_timing),
                                            }
                                        )
                                    else:
                                        embedded_events.append(
                                            {
                                                "type": "text",
                                                "content": event,
                                                "delay": int(timing),
                                                "random_time": bool(temp_random_timing),
                                            }
                                        )
                update_event_overlays()
                load_window.destroy()
                rearrange_window.destroy()

        def delete_selected():
            global embedded_events
            selected_preset = listbox.curselection()
            if selected_preset:
                preset_name = listbox.get(selected_preset)
                preset_path = os.path.join(presets_dir, f"{preset_name}.txt")
                if os.path.exists(preset_path):
                    os.remove(preset_path)
                    print(f"Deleted preset: {preset_name}")
                    listbox.delete(selected_preset)
                    embedded_events = []
                    update_event_overlays()

        load_button = tk.Button(
            load_window, text="Load Selected Preset", command=load_selected
        )
        load_button.pack(pady=10)

        upload_button = tk.Button(
            load_window, text="Upload Preset", command=upload_preset
        )
        upload_button.pack(pady=10)

        delete_button = tk.Button(
            load_window, text="Delete Selected Preset", command=delete_selected
        )
        delete_button.pack(pady=10)

    def on_double_click(useless):
        selected_idx = event_listbox.curselection()
        if selected_idx:
            open_detailed_window(selected_idx[0])

    event_listbox.bind("<Double-Button-1>", on_double_click)

    move_up_button = tk.Button(rearrange_window, text="Move Up", command=move_up)
    move_up_button.pack(pady=5)

    move_down_button = tk.Button(rearrange_window, text="Move Down", command=move_down)
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


def random_time_in_range(min_time=None, max_time=None):
    if min_time is None:
        min_time = 50
    if max_time is None:
        max_time = 4000

    return random.randint(min_time, max_time) / 1000


def start_program():
    global is_running
    is_running = True
    start_button.config(text="Stop Program", command=stop_program)
    print("Program started!")

    def run_events():
        while is_running:
            for event_data in embedded_events:
                if not is_running:
                    break
                if event_data["type"] == "click":
                    x, y = event_data["position"]
                    temp_click_type = event_data["click_type"]
                    temp_press_count = event_data["press_count"]
                    pyautogui.click(
                        x, y, button=str(temp_click_type), clicks=int(temp_press_count)
                    )
                    print(
                        f"Clicked {temp_click_type} {temp_press_count} time(s) at position: ({x}, {y})"
                    )
                    if event_data["random_time"]:
                        time.sleep(
                            random_time_in_range(min_random_time, max_random_time)
                        )
                    else:
                        time.sleep(event_data["delay"] / 1000)
                elif event_data["type"] == "scroll":
                    x, y = event_data["position"]
                    temp_press_count = event_data["press_count"]
                    pyautogui.scroll(temp_press_count, x=x, y=y)
                    print(
                        f"Scrolled {temp_press_count} time(s) at position: ({x}, {y})"
                    )
                    if event_data["random_time"]:
                        time.sleep(
                            random_time_in_range(min_random_time, max_random_time)
                        )
                    else:
                        time.sleep(event_data["delay"] / 1000)
                elif event_data["type"] == "text":
                    if event_data["content"] == "Copy":
                        pyautogui.hotkey("ctrl", "c")
                    elif event_data["content"] == "Paste":
                        pyautogui.hotkey("ctrl", "v")
                    elif event_data["delay"] == 0:
                        pyperclip.copy(event_data["content"])
                        pyautogui.hotkey("ctrl", "v")
                    else:
                        type_text(
                            event_data["content"],
                            (
                                (event_data["delay"] / 1000)
                                if not event_data["random_time"]
                                else random_time_in_range(
                                    min_random_time, max_random_time
                                )
                            ),
                        )
                    print(f"Typed text: {event_data['content']}")
            time.sleep(random_time_in_range(400, 3000) / 1000)

    thread = threading.Thread(target=run_events)
    thread.start()

    monitor_space_key()


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


# Function to stop the program
def stop_program():
    global is_running
    is_running = False
    start_button.config(text="Start Program", command=start_program)
    print("Program stopped!")


# Function to monitor the space key to stop the program
def monitor_space_key():
    def stop_on_space_key():
        while is_running:
            if keyboard.is_pressed("space"):
                stop_program()

    thread = threading.Thread(target=stop_on_space_key)
    thread.start()


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


# Function to close and save the events and update the "Last save" preset
def close_and_save():
    print("Updating 'Last save' preset...")

    update_last_save_preset()

    print("Closing program.")
    root.quit()


root = tk.Tk()
root.title("Event Controller")
root.iconbitmap(program_icon)
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

create_overlay()

create_button = tk.Button(root, text="Create Event", command=create_event)
create_button.pack(pady=10)

delete_button = tk.Button(root, text="Delete Newest Event", command=delete_newest_event)
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

root.mainloop()
