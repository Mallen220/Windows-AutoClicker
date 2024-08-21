import tkinter as tk
from tkinter import Toplevel, Listbox, END, SINGLE, simpledialog
import pyautogui
import pyperclip
import time
import threading
import keyboard
# Global list to store events (as positions)
events = []
timing_data = []  # List to store timing data (in milliseconds)
is_running = False
always_on_top = False  # Keep track of the "always on top" state
overlay_active = True  # Overlay state
is_text_mode = False
preset_file = "presets.txt"  # File to store presets

# Special key mappings
special_keys = {
    't': 't', 'r': 'r', 'accept': 'accept', 'add': 'add', 'alt': 'alt', 'altleft': 'altleft', 'altright': 'altright',
    'apps': 'apps', 'backspace': 'backspace', 'browserback': 'browserback', 'browserfavorites': 'browserfavorites',
    'browserforward': 'browserforward', 'browserhome': 'browserhome', 'browserrefresh': 'browserrefresh',
    'browsersearch': 'browsersearch', 'browserstop': 'browserstop', 'capslock': 'capslock', 'clear': 'clear',
    'convert': 'convert', 'ctrl': 'ctrl', 'ctrlleft': 'ctrlleft', 'ctrlright': 'ctrlright', 'decimal': 'decimal',
    'del': 'del', 'delete': 'delete', 'divide': 'divide', 'down': 'down', 'end': 'end', 'enter': 'enter',
    'esc': 'esc', 'escape': 'escape', 'execute': 'execute', 'f1': 'f1', 'f10': 'f10', 'f11': 'f11', 'f12': 'f12',
    'f13': 'f13', 'f14': 'f14', 'f15': 'f15', 'f16': 'f16', 'f17': 'f17', 'f18': 'f18', 'f19': 'f19', 'f2': 'f2',
    'f20': 'f20', 'f21': 'f21', 'f22': 'f22', 'f23': 'f23', 'f24': 'f24', 'f3': 'f3', 'f4': 'f4', 'f5': 'f5',
    'f6': 'f6', 'f7': 'f7', 'f8': 'f8', 'f9': 'f9', 'final': 'final', 'fn': 'fn', 'hanguel': 'hanguel',
    'hangul': 'hangul', 'hanja': 'hanja', 'help': 'help', 'home': 'home', 'insert': 'insert', 'junja': 'junja',
    'kana': 'kana', 'kanji': 'kanji', 'launchapp1': 'launchapp1', 'launchapp2': 'launchapp2', 'launchmail': 'launchmail',
    'launchmediaselect': 'launchmediaselect', 'left': 'left', 'modechange': 'modechange', 'multiply': 'multiply',
    'nexttrack': 'nexttrack', 'nonconvert': 'nonconvert', 'num0': 'num0', 'num1': 'num1', 'num2': 'num2',
    'num3': 'num3', 'num4': 'num4', 'num5': 'num5', 'num6': 'num6', 'num7': 'num7', 'num8': 'num8', 'num9': 'num9',
    'numlock': 'numlock', 'pagedown': 'pagedown', 'pageup': 'pageup', 'pause': 'pause', 'pgdn': 'pgdn',
    'pgup': 'pgup', 'playpause': 'playpause', 'prevtrack': 'prevtrack', 'print': 'print', 'printscreen': 'printscreen',
    'prntscrn': 'prntscrn', 'prtsc': 'prtsc', 'prtscr': 'prtscr', 'return': 'return', 'right': 'right',
    'scrolllock': 'scrolllock', 'select': 'select', 'separator': 'separator', 'shift': 'shift', 'shiftleft': 'shiftleft',
    'shiftright': 'shiftright', 'sleep': 'sleep', 'space': 'space', 'stop': 'stop', 'subtract': 'subtract',
    'tab': 'tab', 'up': 'up', 'volumedown': 'volumedown', 'volumemute': 'volumemute', 'volumeup': 'volumeup',
    'win': 'win', 'winleft': 'winleft', 'winright': 'winright', 'yen': 'yen', 'command': 'command',
    'option': 'option', 'optionleft': 'optionleft', 'optionright': 'optionright'
}


# Function to create an overlay window for event numbers
def create_overlay():
    overlay = tk.Toplevel(root)
    overlay.attributes("-alpha", 0.5)  # Semi-transparent window
    overlay.attributes("-topmost", True)  # Always on top
    overlay.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}+0+0")  # Fullscreen
    overlay.overrideredirect(True)  # No title bar
    overlay.attributes("-transparentcolor", overlay["bg"])  # Transparent background
    overlay.label_dict = {}  # Store labels for each event
    return overlay


# Function to create an event
def create_event():
    global is_text_mode
    if keyboard.is_pressed('ctrl'):
        # Enter text input mode
        if not is_text_mode:
            is_text_mode = True
            open_text_input()
        else:
            stop_text_input()
    else:
        if is_text_mode:
            return  # Prevent creating a mouse event while in text mode
        print("Waiting for 'Z' key press to create the event...")
        keyboard.wait('z')
        x, y = pyautogui.position()
        events.append((x, y))
        timing_data.append(100)  # Default wait time in milliseconds
        print(f"Event created at position: ({x}, {y})")
        update_event_overlays()


# Function to stop text input mode and close the input window
def stop_text_input():
    if input_window:
        save_text()  # Save and close text input when user clicks "Create Event" again

# Function to delete the newest event
def delete_newest_event():
    if events:
        events.pop()
        timing_data.pop()
        update_event_overlays()
        print("Deleted the newest event.")
    else:
        print("No events to delete.")


# Function to update overlays for all events
def update_event_overlays():
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
    always_on_top_button.config(text="Always on Top: ON" if always_on_top else "Always on Top: OFF")


# Function to create an event number overlay
def create_event_overlay(event_num, x, y):
    if overlay_active:
        if isinstance(events[event_num - 1], str):
            return
        try:
            label_color = "purple" if isinstance(events[event_num], str) else "red"
        except:
            label_color = "red"
        label = tk.Label(overlay, text=str(event_num), fg=label_color, font=("Arial", 24))
        label.place(x=x, y=y)
        overlay.label_dict[event_num] = label


# Function to open a text input window with multiline support
def open_text_input():
    global input_window, text_box, instant_type_var
    input_window = Toplevel(root)
    input_window.title("Enter Text")
    input_window.geometry("500x250")
    label = tk.Label(input_window, text="Enter text to simulate (Press 'Enter' for new line):")
    label.pack(pady=5)
    text_box = tk.Text(input_window, width=40, height=5)
    text_box.pack(pady=5)
    text_box.focus()
    instant_type_var = tk.BooleanVar()
    instant_type_check = tk.Checkbutton(input_window, text="Instant Type", variable=instant_type_var)
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
        interval = 0 if instant_type_var.get() else 100  # Instant typing if checked, else default interval
        timing_data.append(interval)
        print(f"Text event created: {user_text}")
    input_window.destroy()
    is_text_mode = False  # Reset text mode flag
    print("Text input mode exited.")

# Function to rearrange events and adjust timings
def rearrange_events():
    rearrange_window = Toplevel(root)
    rearrange_window.title("Rearrange Events")
    rearrange_window.geometry("600x600")
    event_listbox = Listbox(rearrange_window, selectmode=SINGLE, width=40, height=10)
    event_listbox.pack(pady=10)
    for i, event in enumerate(events):
        event_listbox.insert(END, f"Event {i + 1}: {event}")

    def move_up():
        selected_idx = event_listbox.curselection()
        if not selected_idx or selected_idx[0] == 0:
            return
        selected_idx = selected_idx[0]
        events[selected_idx], events[selected_idx - 1] = events[selected_idx - 1], events[selected_idx]
        timing_data[selected_idx], timing_data[selected_idx - 1] = timing_data[selected_idx - 1], timing_data[
            selected_idx]
        update_listbox()
        event_listbox.select_set(selected_idx - 1)
        update_event_overlays()

    def move_down():
        selected_idx = event_listbox.curselection()
        if not selected_idx or selected_idx[0] == len(events) - 1:
            return
        selected_idx = selected_idx[0]
        events[selected_idx], events[selected_idx + 1] = events[selected_idx + 1], events[selected_idx]
        timing_data[selected_idx], timing_data[selected_idx + 1] = timing_data[selected_idx + 1], timing_data[
            selected_idx]
        update_listbox()
        event_listbox.select_set(selected_idx + 1)
        update_event_overlays()

    def update_listbox():
        event_listbox.delete(0, END)
        for i, event in enumerate(events):
            event_listbox.insert(END, f"Event {i + 1}: {event}")

    def open_timeout_window(idx):
        timeout_window = Toplevel(rearrange_window)
        timeout_window.title(f"Set Timeout for Event {idx + 1}")
        label = tk.Label(timeout_window, text="Timeout? (ms)")
        label.pack(pady=5)
        timeout_entry = tk.Entry(timeout_window)
        timeout_entry.pack(pady=5)
        timeout_entry.insert(0, str(timing_data[idx]))

        def save_timeout():
            new_timeout = timeout_entry.get()
            try:
                timing_data[idx] = int(new_timeout)
                print(f"Updated timing for Event {idx + 1}: {new_timeout} ms")
                update_listbox()
                timeout_window.destroy()
            except ValueError:
                print("Please enter a valid number for the timeout.")

        save_button = tk.Button(timeout_window, text="Save", command=save_timeout)
        save_button.pack(pady=10)

    # Function to save current settings as a preset
    def save_preset():
        preset_name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")
        if preset_name:
            with open(preset_file, 'a') as f:
                f.write(f"- {preset_name}\n")
                for event, timing in zip(events, timing_data):
                    f.write(f"{event}\t{timing}\n")
                f.write("\n")
            print(f"Preset '{preset_name}' saved.")

    # Function to load a selected preset
    def load_preset():
        load_window = Toplevel(root)
        load_window.title("Load Preset")
        load_window.geometry("300x400")
        listbox = Listbox(load_window, width=40, height=15)
        listbox.pack(pady=10)
        try:
            with open(preset_file, 'r') as f:
                lines = f.readlines()
                presets = [line.strip() for line in lines if line.strip() and not line.startswith('\t') and line.startswith('- ')]
                for preset in presets:
                    listbox.insert(END, preset)
        except FileNotFoundError:
            print("No preset file found.")

        def load_selected():
            global events
            selected_preset = listbox.curselection()
            if selected_preset:
                events = []
                preset_name = listbox.get(selected_preset)
                print(f"Loading preset: {preset_name}")
                with open(preset_file, 'r') as f:
                    lines = f.readlines()
                    loading = False
                    for line in lines:
                        if line.strip() == preset_name:
                            loading = True
                            continue
                        if loading and not line.strip():
                            break
                        if loading:
                            event_data = line.split('\t')
                            if len(event_data) == 2:
                                event, timing = event_data
                                if event.startswith('('):
                                    x, y = map(int, event.strip('()').split(','))
                                    events.append((x, y))
                                else:
                                    events.append(event)
                                timing_data.append(int(timing))
                update_event_overlays()
                load_window.destroy()
                rearrange_window.destroy()

        load_button = tk.Button(load_window, text="Load Selected Preset", command=load_selected)
        load_button.pack(pady=10)

    def on_double_click(event):
        selected_idx = event_listbox.curselection()
        if selected_idx:
            open_timeout_window(selected_idx[0])

    event_listbox.bind("<Double-Button-1>", on_double_click)

    move_up_button = tk.Button(rearrange_window, text="Move Up", command=move_up)
    move_up_button.pack(pady=5)

    move_down_button = tk.Button(rearrange_window, text="Move Down", command=move_down)
    move_down_button.pack(pady=5)

    save_preset_button = tk.Button(rearrange_window, text="Save Preset", command=save_preset)
    save_preset_button.pack(pady=5)

    load_preset_button = tk.Button(rearrange_window, text="Load Preset", command=load_preset)
    load_preset_button.pack(pady=5)

    close_button = tk.Button(rearrange_window, text="Close", command=rearrange_window.destroy)
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
                    pyautogui.click(x, y)
                    print(f"Clicked at position: ({x}, {y})")
                    time.sleep(timing_data[i] / 1000)
                elif isinstance(event, str):
                    if timing_data[i] == 0:
                        pyperclip.copy(event)
                        pyautogui.hotkey('ctrl', 'v')
                    else:
                        type_text(event, timing_data[i] / 1000)
                    print(f"Typed text: {event}")
            time.sleep(0.5)  # Delay between rounds

    thread = threading.Thread(target=run_events)
    thread.start()

    # Monitor for space key press to stop the program
    monitor_space_key()

# Function to simulate typing text with pyautogui.press() for finer control
def type_text(text, interval):
    i = 0
    while i < len(text):
        char = text[i]
        if char == '\\':
            i += 1
            if i < len(text):
                special_key = text[i:]
                next_special_key = next((key for key in special_keys if special_key.startswith(key)), None)
                if next_special_key:
                    pyautogui.press(special_keys[next_special_key])
                    i += len(next_special_key) - 1
                else:
                    pyautogui.press(char)
        elif char == ' ':
            pyautogui.press('space')
        elif char == '\n':
            pyautogui.press('enter')
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
            if keyboard.is_pressed('space'):
                stop_program()

    thread = threading.Thread(target=stop_on_space_key)
    thread.start()

# Function to close and save the events
def close_and_save():
    with open("events.txt", "w") as f:
        for event in events:
            f.write(f"{event}\n")
    print("Events saved. Closing program.")
    root.quit()

# Create the main window
root = tk.Tk()
root.title("Event Controller")

root.attributes("-alpha", 0.85)  # Semi-transparent

# Set window size
root.geometry("225x325")

# Function to enable dragging the window by clicking anywhere
def on_drag_start(event):
    root._drag_data = {'x': event.x, 'y': event.y}

def on_drag_motion(event):
    delta_x = event.x - root._drag_data['x']
    delta_y = event.y - root._drag_data['y']
    new_x = root.winfo_x() + delta_x
    new_y = root.winfo_y() + delta_y
    root.geometry(f"+{new_x}+{new_y}")

root.bind("<Button-1>", on_drag_start)
root.bind("<B1-Motion>", on_drag_motion)

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

always_on_top_button = tk.Button(root, text="Always on Top: Off", command=toggle_always_on_top)
always_on_top_button.pack(pady=10)

close_button = tk.Button(root, text="Close & Save", command=close_and_save)
close_button.pack(pady=10)

root.mainloop()