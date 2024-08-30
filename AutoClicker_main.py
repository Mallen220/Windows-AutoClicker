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

# pyinstaller --onefile --windowed --icon=AutoClicker.ico --add-data "AutoClicker.ico;." --add-data "Presets;Presets" AutoClicker_main.py


# Global lists to store events and their timings
events = []
timing_data = []
click_type = []  # Double, Right, Left, Copy, Paste, Middle, Scroll
press_count = []

undo_stack = []  # Stack to store undo actions
redo_stack = []  # Stack to store redo actions
max_undo_redo = 25  # Limit to the number of undo/redo actions
is_running = False
always_on_top = False  # Keep track of the "always on top" state
overlay_active = True  # Overlay state
is_text_mode = False
delay_between_rounds = 500  # Default delay in milliseconds

embedded_events = []

# Determine the path to the icon and presets directory
if getattr(sys, "frozen", False):
    program_icon = os.path.join(sys._MEIPASS, "AutoClicker.ico")
else:
    program_icon = "AutoClicker.ico"

presets_dir = "Presets"
if not os.path.exists(presets_dir):
    os.makedirs(presets_dir)

# Special key mappings
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
def modify_event(index, new_event, new_timing, new_click_type, new_press_count):
    if 0 <= index < len(events):
        events[index] = new_event
        timing_data[index] = new_timing
        click_type[index] = new_click_type
        press_count[index] = new_press_count
        save_events()
        print(f"Event {index + 1} modified: {new_event}, Delay: {new_timing}ms")


# Function to save events back to the internal structure
def save_events():
    global embedded_events
    embedded_events = []
    for i, event in enumerate(events):
        if isinstance(event, tuple):
            embedded_events.append(
                {
                    "type": "click",
                    "position": event,
                    "Button": click_type[i],
                    "Count": press_count[i],
                    "delay": timing_data[i],
                }
            )
        elif isinstance(event, str):
            embedded_events.append(
                {"type": "text", "content": event, "delay": timing_data[i]}
            )


# Load embedded events into the global events list
def load_embedded_events():
    global events, timing_data
    for event in embedded_events:
        if event["type"] == "click":
            events.append((event["position"]))
            click_type.append((event["Button"]))
            press_count.append((event["Count"]))
        elif event["type"] == "text":
            events.append(event["content"])
        timing_data.append(event["delay"])


# Function to create an overlay window for event numbers
def create_overlay():
    overlay = tk.Toplevel(root)
    overlay.iconbitmap(program_icon)
    overlay.attributes("-alpha", 0.5)  # Semi-transparent window
    overlay.attributes("-topmost", True)  # Always on top
    overlay.geometry(
        f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0"
    )  # Fullscreen
    overlay.overrideredirect(True)  # No title bar
    overlay.attributes("-transparentcolor", overlay["bg"])  # Transparent background
    overlay.label_dict = {}  # Store labels for each event
    return overlay


# Function to create an event
def create_event():
    global is_text_mode
    if keyboard.is_pressed("ctrl"):
        # Enter text input mode
        if not is_text_mode:
            is_text_mode = True
            open_text_input()
        else:
            stop_text_input()
    else:
        if is_text_mode:
            return  # Prevent creating a mouse event while in text mode
        print("Waiting for 'space' key press to create the event...")
        keyboard.wait("space")
        x, y = pyautogui.position()
        events.append((x, y))
        click_type.append("left")
        press_count.append(1)
        timing_data.append(100)  # Default wait time in milliseconds
        print(f"Event created at position: ({x}, {y})")

        # Push the event to the undo stack
        add_to_undo_stack(("create", (x, y)))

        # Clear the redo stack since a new action occurred
        redo_stack.clear()
        update_event_overlays()

        update_event_overlays()


# Function to stop text input mode and close the input window
def stop_text_input():
    if input_window:
        save_text()  # Save and close text input when user clicks "Create Event" again


# Function to delete the newest event
def delete_newest_event():
    if events:
        deleted_event = events.pop()
        click_type.pop()
        press_count.pop()
        timing_data.pop()
        print(f"Deleted event at position: {deleted_event}")

        # Clear the redo stack
        redo_stack.clear()
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
            # Undo creation (delete the event)
            if event in events:
                index = events.index(event)
                events.pop(index)
                timing_data.pop(index)
                print(f"Undid creation of event at position: {event}")
                add_to_redo_stack(
                    ("create", event)
                )  # Push the inverse action to redo stack
        elif action_type == "delete":
            # Undo deletion (recreate the event)
            events.append(event)
            timing_data.append(100)  # Default wait time
            print(f"Undid deletion of event at position: {event}")
            add_to_redo_stack(("delete", event))
        update_event_overlays()
    else:
        print("No actions to undo.")


# Redo the last undone action
def redo():
    if redo_stack:
        action = redo_stack.pop()
        action_type, event = action
        if action_type == "create":
            # Redo creation (recreate the event)
            events.append(event)
            click_type.append("left")
            press_count.append(1)
            timing_data.append(100)  # Default wait time
            print(f"Redid creation of event at position: {event}")
            add_to_undo_stack(("create", event))
        elif action_type == "delete":
            # Redo deletion (delete the event)
            if event in events:
                index = events.index(event)
                events.pop(index)
                click_type.pop()
                press_count.pop()
                timing_data.pop(index)
                print(f"Redid deletion of event at position: {event}")
                add_to_undo_stack(("delete", event))
        update_event_overlays()
    else:
        print("No actions to redo.")


# Add an action to the undo stack and maintain a maximum of 5 actions
def add_to_undo_stack(action):
    undo_stack.append(action)
    if len(undo_stack) > max_undo_redo:
        undo_stack.pop(0)  # Remove the oldest action if over the limit


# Add an action to the redo stack and maintain a maximum of 5 actions
def add_to_redo_stack(action):
    redo_stack.append(action)
    if len(redo_stack) > max_undo_redo:
        redo_stack.pop(0)


# Function to update overlays for all events
def update_event_overlays():
    save_events()
    for label in overlay.label_dict.values():
        label.destroy()
    for event_num, event in enumerate(events, 1):
        if isinstance(event, tuple):
            x, y = event
            create_event_overlay(event_num, x, y)
        elif isinstance(event, str):
            x, y = pyautogui.position()
            create_event_overlay(event_num, x, y)


# Function to toggle "always on top"
def toggle_always_on_top():
    global always_on_top
    always_on_top = not always_on_top
    root.attributes("-topmost", always_on_top)
    always_on_top_button.config(
        text="Always on Top: ON" if always_on_top else "Always on Top: OFF"
    )


# Function to create an event number overlay
def create_event_overlay(event_num, x, y):
    if overlay_active:
        if isinstance(events[event_num - 1], str):
            return
        try:
            label_color = "purple" if isinstance(events[event_num], str) else "red"
        except:
            label_color = "red"
        label = tk.Label(
            overlay, text=str(event_num), fg=label_color, font=("Arial", 24)
        )
        label.place(x=x, y=y)
        overlay.label_dict[event_num] = label


# Function to open a text input window with multiline support
def open_text_input():
    global input_window, text_box, instant_type_var
    input_window = Toplevel(root)
    input_window.iconbitmap(program_icon)
    input_window.title("Enter Text")
    input_window.geometry("500x250")
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
    save_button = tk.Button(input_window, text="Save Text", command=save_text)
    save_button.pack(pady=5)


# Function to save text from the input box and close the window
def save_text():
    global is_text_mode
    user_text = text_box.get("1.0", tk.END).strip()  # Get text input (multiline)
    if user_text:
        events.append(user_text)
        # Use instant typing or regular typing speed based on the checkbox
        interval = (
            0 if instant_type_var.get() else 100
        )  # Instant typing if checked, else default interval
        timing_data.append(interval)
        print(f"Text event created: {user_text}")
    input_window.destroy()
    is_text_mode = False  # Reset text mode flag
    print("Text input mode exited.")


# Function to save the current settings as a preset
def save_preset(name=None):
    # If no name is provided, prompt the user
    if not name:
        name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")

    # If still no name is provided, exit the function
    if not name:
        print("No name provided, preset save canceled.")
        return

    # Create the file path for the preset
    preset_path = os.path.join(presets_dir, f"{name}.txt")

    # Save the new preset
    with open(preset_path, "w") as f:
        f.write(f"- {name}\n")
        f.write(f"Delay: {delay_between_rounds}\n")
        i = 0
        for event, timing in zip(events, timing_data):
            if isinstance(event, tuple):
                f.write(
                    f"{event}\t{timing}\t{str(click_type[i])}\t{int(press_count[i])}\n"
                )
            elif isinstance(event, str):
                f.write(f"{event}\t{timing}\n")
            i = i + 1
        f.write("\n")

    print(f"Preset '{name}' saved.")


# Function to rearrange events and adjust timings
def rearrange_events():
    rearrange_window = Toplevel(root)
    rearrange_window.iconbitmap(program_icon)
    rearrange_window.title("Rearrange Events")
    rearrange_window.geometry("500x700")
    event_listbox = Listbox(rearrange_window, selectmode=SINGLE, width=40, height=10)
    event_listbox.pack(pady=10)
    for i, event in enumerate(events):
        event_listbox.insert(END, f"Event {i + 1}: {event}")

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
        events[selected_idx], events[selected_idx - 1] = (
            events[selected_idx - 1],
            events[selected_idx],
        )
        press_count[selected_idx], press_count[selected_idx - 1] = (
            press_count[selected_idx - 1],
            press_count[selected_idx],
        )
        click_type[selected_idx], click_type[selected_idx - 1] = (
            click_type[selected_idx - 1],
            click_type[selected_idx],
        )
        timing_data[selected_idx], timing_data[selected_idx - 1] = (
            timing_data[selected_idx - 1],
            timing_data[selected_idx],
        )
        update_listbox()
        event_listbox.select_set(selected_idx - 1)
        update_event_overlays()

    def move_down():
        selected_idx = event_listbox.curselection()
        if not selected_idx or selected_idx[0] == len(events) - 1:
            return
        selected_idx = selected_idx[0]
        events[selected_idx], events[selected_idx + 1] = (
            events[selected_idx + 1],
            events[selected_idx],
        )
        click_type[selected_idx], click_type[selected_idx + 1] = (
            click_type[selected_idx + 1],
            click_type[selected_idx],
        )
        press_count[selected_idx], press_count[selected_idx + 1] = (
            press_count[selected_idx + 1],
            press_count[selected_idx],
        )
        timing_data[selected_idx], timing_data[selected_idx + 1] = (
            timing_data[selected_idx + 1],
            timing_data[selected_idx],
        )
        update_listbox()
        event_listbox.select_set(selected_idx + 1)
        update_event_overlays()

    def update_listbox():
        event_listbox.delete(0, END)
        for i, event in enumerate(events):
            event_listbox.insert(END, f"Event {i + 1}: {event}")

    # Function to randomize all event times
    def randomize_all_times():
        for i in range(len(timing_data)):
            timing_data[i] = random.randint(50, 1000)
            print(f"Randomized timing for Event {i + 1}: {timing_data[i]} ms")
        update_event_overlays()

    def open_detailed_window(idx):
        detailed_event_window = Toplevel(rearrange_window)
        detailed_event_window.iconbitmap(program_icon)
        detailed_event_window.title(f"Set Timeout for Event {idx + 1}")
        timeout_label = tk.Label(detailed_event_window, text="Timeout? (ms)")
        timeout_label.pack(pady=5)
        timeout_entry = tk.Entry(detailed_event_window)
        timeout_entry.pack(pady=5)
        timeout_entry.insert(0, str(timing_data[idx]))

        # Create a label for each question
        press_count_label = tk.Label(
            detailed_event_window, text="How many times to click:"
        )
        press_count_label.pack(pady=5)
        press_count_entry = tk.Entry(detailed_event_window)
        press_count_entry.pack(pady=5)

        options = ["left", "middle", "right"]
        clicked = tk.StringVar()
        clicked.set("left")

        click_type_label = tk.Label(detailed_event_window, text="Type of Mouse Click")
        click_type_label.pack(pady=5)
        click_type_entry = tk.OptionMenu(detailed_event_window, clicked, *options)
        click_type_entry.pack(pady=5)

        def save_details():
            new_timeout = timeout_entry.get()

            try:
                new_press_count = int(press_count_entry.get())
            except ValueError:
                new_press_count = 1

            try:
                timing_data[idx] = int(new_timeout)
                press_count[idx] = int(new_press_count)
                click_type[idx] = clicked.get()
                print(f"Updated timing for Event {idx + 1}: {new_timeout} ms")
                print(f"Updated Press Count for Event {idx + 1}: {new_press_count}")
                print(f"Updated Click Type for Event {idx + 1}: {clicked.get()}")
                update_listbox()
                detailed_event_window.destroy()
            except ValueError:
                print("Please enter a valid number for the detailed window.")

            # Function to randomize timing for a specific event

        def randomize_event_time(idx):
            timing_data[idx] = random.randint(50, 1000)
            print(f"Randomized timing for Event {idx + 1}: {timing_data[idx]} ms")
            update_event_overlays()
            detailed_event_window.destroy()

        # Randomize Time Button
        randomize_button = tk.Button(
            detailed_event_window,
            text="Randomize Time",
            command=lambda: randomize_event_time(idx),
        )
        randomize_button.pack(pady=5)

        save_button = tk.Button(
            detailed_event_window, text="Save", command=save_details
        )
        save_button.pack(pady=10)

    def delete_all_events():
        global events, timing_data, click_type, press_count, embedded_events
        events = []
        timing_data = []
        click_type = []
        press_count = []
        embedded_events = []
        update_event_overlays()
        update_listbox()

    delete_all_events = tk.Button(
        rearrange_window,
        text="Delete All Events (Can't Undo)",
        command=delete_all_events,
    )
    delete_all_events.pack(pady=5)

    # Button to randomize all event times
    randomize_all_button = tk.Button(
        rearrange_window,
        text="Randomize All Times (Override Instant Type)",
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
            listbox.insert(END, preset[:-4])  # Display file name without '.txt'

            # Function to upload a preset

        def upload_preset():
            file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
            if file_path:
                file_name = os.path.basename(file_path)
                new_file_path = os.path.join(presets_dir, file_name)
                if not os.path.exists(new_file_path):
                    os.rename(
                        file_path, new_file_path
                    )  # Move the file to the presets directory
                    print(f"Preset from {file_path} uploaded successfully.")
                else:
                    print(f"Preset already exists: {file_name}")
                load_window.destroy()

        def load_selected():
            global events, delay_between_rounds
            selected_preset = listbox.curselection()
            if selected_preset:
                events = []
                preset_name = listbox.get(selected_preset)  # Get the selected file name
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
                                if len(event_data) >= 4:
                                    event, timing, temp_click_type, temp_press_count = (
                                        event_data[:4]
                                    )
                                    if event.startswith("("):
                                        x, y = map(int, event.strip("()").split(","))
                                        events.append((x, y))
                                        click_type.append(temp_click_type)
                                        press_count.append(temp_press_count)
                                    else:
                                        events.append(event)
                                    timing_data.append(int(timing))
                update_event_overlays()
                load_window.destroy()
                rearrange_window.destroy()

        def delete_selected():
            global events
            selected_preset = listbox.curselection()
            if selected_preset:
                preset_name = listbox.get(selected_preset)
                preset_path = os.path.join(presets_dir, f"{preset_name}.txt")
                if os.path.exists(preset_path):
                    os.remove(preset_path)
                    print(f"Deleted preset: {preset_name}")
                    listbox.delete(selected_preset)
                    events = []
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


# Function to start the program
def start_program():
    global is_running
    is_running = True
    start_button.config(text="Stop Program", command=stop_program)
    print("Program started!")

    def run_events():
        while is_running:
            for i, event in enumerate(events):
                if not is_running:
                    break
                if isinstance(event, tuple):
                    x, y = event
                    temp_click_type = click_type[i]
                    temp_press_count = press_count[i]
                    pyautogui.click(
                        x, y, button=str(temp_click_type), clicks=int(temp_press_count)
                    )
                    print(
                        f"Clicked {temp_click_type} {temp_press_count} time(s) at position: ({x}, {y})"
                    )
                    time.sleep(timing_data[i] / 1000)
                elif isinstance(event, str):
                    if timing_data[i] == 0:
                        pyperclip.copy(event)
                        pyautogui.hotkey("ctrl", "v")
                    else:
                        type_text(event, timing_data[i] / 1000)
                    print(f"Typed text: {event}")
            time.sleep(delay_between_rounds / 1000)  # Use the adjustable delay

    thread = threading.Thread(target=run_events)
    thread.start()

    # Monitor for space key press to stop the program
    monitor_space_key()


# Function to simulate typing text with pyautogui.press() for finer control
def type_text(text, interval):
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
        time.sleep(interval)  # Control the interval between key presses


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
    # Create the directory if it doesn't exist
    if not os.path.exists(presets_dir):
        os.makedirs(presets_dir)

    # Create the file path for the preset to be deleted
    file_path = os.path.join(presets_dir, f"{name}.txt")

    # Attempt to delete the file
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Preset '{name}' deleted successfully.")
        else:
            print(f"Preset '{name}' not found.")
    except Exception as e:
        print(f"Error deleting preset '{name}': {e}")


# Function to update the "Last save" preset
def update_last_save_preset():
    # Create the directory if it doesn't exist
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

    # Update the "Last save" preset in the presets file
    update_last_save_preset()

    print("Closing program.")
    root.quit()


# Create the main window
root = tk.Tk()
root.title("Event Controller")

root.iconbitmap(program_icon)  # Set the window icon

root.attributes("-alpha", 0.85)  # Semi-transparent

# Set window size
root.geometry("225x325")


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
root.bind("<Control-Z>", lambda event: undo())  # For Windows case-sensitivity
root.bind("<Control-Shift-Z>", lambda event: redo())

# Overlay window for event numbers
overlay = create_overlay()

# Create buttons
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
