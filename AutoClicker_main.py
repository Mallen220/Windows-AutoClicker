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
from PIL import Image, ImageTk

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
CTRL_KEY = "command" if os.name == "Darwin" else "ctrl"

SCREENSHOT_DIR = "conditions"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


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
# Overlay Control
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


def save_details(
    idx, new_settings=None
):
    if new_settings is not None:
        global embedded_events

        # Basic validation
        if new_settings is None or not new_settings:
            return
        if not (0 <= idx < len(embedded_events)):
            print(f"[save_details] idx {idx} out of range")
            return

        event = embedded_events[idx]

        # Apply the updates
        for key, value in new_settings.items():
            if value is None:
                continue  # skip “no-op” entries
            event[key] = value  # add or replace

        # No need to re-assign; `event` is the same dict object,
        # but doing it explicitly avoids surprises if you ever
        # switch to an immutable structure.
        embedded_events[idx] = event
    update_listbox()


def move_selected_event(window=None, idx=None):
    print("Waiting for 'space' key press to move the event...")
    wait_for_key("space")

    x, y = pyautogui.position()
    if idx is None:
        idx = len(embedded_events) - 1
    if (
        embedded_events[idx]["type"] == "click"
        or embedded_events[idx]["type"] == "scroll"
    ):
        embedded_events[idx]["position"] = (x, y)
    update_event_overlays()

    if window is not None:
        window.destroy()


def add_event(
    event_type: str,
    *,
    grab_cursor: bool = False,
    delay: int = 100,
    random_time: bool = False,
    extra: dict | None = None,
) -> None:
    """
    Create a new event and push it to `embedded_events`.

    Parameters
    ----------
    event_type         : 'click' | 'scroll' | 'wait' | 'conditional' | …
    grab_cursor   : wait for <Space> and capture mouse (True/False)
    delay         : universal per‑event delay (ms)
    random_time   : universal random‑time flag
    extra         : dict with event‑specific fields to merge in
    """
    # ── capture position if needed ─────────────────────────────
    if grab_cursor:
        print(f"Press <Space> to capture the {event_type} position…")
        wait_for_key("space")
        x, y = pyautogui.position()
    else:
        x = y = None

    # ── assemble event dict ───────────────────────────────────
    event = {
        "type": event_type,
        "delay": delay,
        "random_time": random_time,
    }
    if grab_cursor:
        event["position"] = (x, y)
    if extra:
        event.update(extra)

    # ── commit & UI refresh ───────────────────────────────────
    embedded_events.append(event)
    add_to_undo_stack(("create", event))

    print("Event created:", event)
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


def modify_event_order(selected_tuple, shift: int) -> None:
    if not selected_tuple or shift == 0:
        return

    src_idx = selected_tuple[0]
    max_idx = len(embedded_events) - 1

    # clamp destination so it stays within [0, max_idx]
    dst_idx = max(0, min(src_idx + shift, max_idx))
    if dst_idx == src_idx:
        return  # nothing to do

    item = embedded_events.pop(src_idx)
    embedded_events.insert(dst_idx, item)

    update_listbox()
    event_listbox.select_set(dst_idx)
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

def create_text_event():
    global is_text_mode
    if not is_text_mode:
        is_text_mode = True
        open_text_input()
    else:
        save_text()
        update_event_overlays()


#####################################################
# Conditional Control
#####################################################


def open_conditional_window(idx=None):
    img_path_var = tk.StringVar()

    conditional_window = Toplevel(root)
    conditional_window.title("Conditional Logic")
    tk.Label(conditional_window, text="Kind").grid(row=0, column=0)
    kind_var = tk.StringVar(value=embedded_events[idx]["cond_kind"] if idx is not None else "if")
    tk.OptionMenu(conditional_window, kind_var, "if", "while", "if_else").grid(row=0, column=1)

    tk.Label(conditional_window, text="Jump to when true").grid(row=1, column=0)
    true_var = tk.IntVar(value=0)
    tk.Entry(conditional_window, textvariable=true_var, width=5).grid(row=1, column=1)

    tk.Label(conditional_window, text="Jump to when false").grid(row=2, column=0)
    false_var = tk.IntVar(value=-1)                # -1 → fall-through
    false_entry = tk.Entry(conditional_window, textvariable=false_var, width=5)
    false_entry.grid(row=2, column=1)

    # Disable the “false” entry except for if_else
    def toggle_false(*_):
        state = "normal" if kind_var.get() == "if_else" else "disabled"
        false_entry.configure(state=state)
    kind_var.trace_add("write", toggle_false)
    toggle_false()

    # ---------------------------------------------------------------------------
    # main routine – bound to SPACE
    # ---------------------------------------------------------------------------
    def grab_image(event=None):
        """
        Hide the GUI, capture the current active screen, present CropWindow.
        The final PNG path winds up in img_path_var.
        """
        conditional_window.withdraw()  # hide everything
        time.sleep(0.2)  # make sure it is off-screen
        full_shot = pyautogui.screenshot()  # PIL Image
        cropped_window(full_shot)  # user handles the rest

    def cropped_window(pil_img):
        def save_and_finish(pil_img):
            """
            Save the cropped PIL image, restore the main window, update img_path_var.
            """
            filename = os.path.join(
                SCREENSHOT_DIR, f"cond_{int(time.time())}.png"
            )
            pil_img.save(filename)
            conditional_window.deiconify()

            img_path_var.set(filename)

        """
        Full-size window containing the captured screen image.
        If the screenshot is larger than the main display, we shrink it
        while keeping aspect ratio.  Drag to pick a crop, release to save.
        """
        captured_window = Toplevel(root)
        captured_window.title("Drag to crop – release to save")
        captured_window.attributes("-topmost", True)

        # ------------------------------------------------------------
        # down-scale if needed so the preview fits on the current screen
        # ------------------------------------------------------------
        scr_w = captured_window.winfo_screenwidth()
        scr_h = captured_window.winfo_screenheight()
        img_w, img_h = pil_img.size

        scale = min(scr_w / img_w, scr_h / img_h, 1.0)  # never > 1
        scale = scale  # keep for later

        if scale < 1.0:
            disp_w, disp_h = int(img_w * scale), int(img_h * scale)
            display_img = pil_img.resize((disp_w, disp_h), Image.LANCZOS)
        else:
            display_img = pil_img  # no scaling

        pil_img_orig = pil_img  # full-res copy
        tk_img = ImageTk.PhotoImage(display_img)

        start_x = start_y = None
        rect_id = None

        canvas = tk.Canvas(
            captured_window,
            width=tk_img.width(),
            height=tk_img.height(),
            cursor="cross"
        )
        canvas.pack(expand=True)
        canvas.create_image(0, 0, anchor="nw", image=tk_img)

        canvas.image = tk_img
        pil_img_orig = pil_img
        scale_factor = scale
        start_x = start_y = None
        rect_id = None

        # ------------------------------------------------------------
        # mouse callbacks
        # ------------------------------------------------------------
        def _on_press(event):
            nonlocal start_x, start_y, rect_id
            start_x, start_y = event.x, event.y
            if rect_id is not None:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(
                start_x, start_y, event.x, event.y,
                outline="red", width=2
            )

        def _on_drag(event):
            nonlocal start_x, start_y, rect_id
            canvas.coords(
                rect_id,
                start_x, start_y, event.x, event.y
            )

        def _on_release(event):
            nonlocal start_x, start_y, rect_id
            # --- coords on the (possibly scaled) preview ---
            left_p, upper_p = min(start_x, event.x), min(start_y, event.y)
            right_p, lower_p = max(start_x, event.x), max(start_y, event.y)

            # ignore clicks with no drag
            if right_p - left_p < 2 or lower_p - upper_p < 2:
                captured_window.destroy()
                conditional_window.deiconify()
                return

            # --- map back to original screenshot coordinates ---
            inv = 1.0 / scale
            left_o = int(left_p * inv)
            upper_o = int(upper_p * inv)
            right_o = int(right_p * inv)
            lower_o = int(lower_p * inv)

            cropped = pil_img_orig.crop((left_o, upper_o, right_o, lower_o))
            save_and_finish(cropped)  # reuse existing helper
            captured_window.destroy()

        # ------------------------------------------------------------
        # canvas setup
        # ------------------------------------------------------------

        # mouse bindings
        canvas.bind("<Button-1>", _on_press)
        canvas.bind("<B1-Motion>", _on_drag)
        canvas.bind("<ButtonRelease-1>", _on_release)


    root.bind_all("<space>", grab_image)
    tk.Button(conditional_window, text="Capture Screen",
              command=grab_image).grid(row=3, columnspan=2)

    def save_conditional():
        cond = {
            "cond_kind": kind_var.get(),
            "image_path": embedded_events[idx]["image_path"] if (img_path_var.get() is None and idx is not None) else img_path_var.get(),
            "true_target": true_var.get(),
            "false_target": None if kind_var.get() != "if_else" else false_var.get(),
        }
        if idx is None:
            add_event("conditional", extra=cond,)
        else:
            save_details(idx, cond)
        update_listbox()
        conditional_window.destroy()
    tk.Button(conditional_window, text="Save", command=save_conditional).grid(row=4, columnspan=2)



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
        # print(embedded_events)
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
                command=lambda: (move_selected_event(detailed_event_window), update_listbox()),
            )
            move_event.pack(pady=10)

        save_button = tk.Button(
            detailed_event_window,
            text="Save",
            command=lambda: (
                save_details(
                    idx,
                    {"delay": int(timeout_entry.get()),
                     "random_time": random_time_var.get(),
                     "press_count": 1 if embedded_events[idx]["type"] == "wait" else int(press_count_entry.get()),
                     "click_type": "left" if embedded_events[idx]["type"] == "wait" else clicked.get()},
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
    elif embedded_events[idx]["type"] == "conditional":
        open_conditional_window(idx)
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
    global event_listbox
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
                elif event_data["type"] == "conditional":
                    event_listbox.insert(
                        END, f"Event {i + 1}: Conditional ({event_data['cond_kind']}) travels to {event_data['true_target']}"
                    )
            except Exception:
                event_listbox.insert(END, f"Event {i + 1}: error loading event data")
    except Exception:
        print("Listbox does not exist. Failed to updated listbox. Exiting...")


# Function to rearrange events and adjust timings
def rearrange_events():
    global embedded_events, delay_between_rounds, event_listbox
    rearrange_window = Toplevel(root)
    icon_per_os(rearrange_window)
    rearrange_window.title("Rearrange Events")
    rearrange_window.geometry("500x700")
    event_listbox = Listbox(rearrange_window, selectmode=SINGLE, width=40, height=10)
    event_listbox.pack(pady=10)

    update_listbox()

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
        global embedded_events, delay_between_rounds
        load_window = Toplevel(root)
        icon_per_os(load_window)
        load_window.title("Load Preset")
        load_window.geometry("300x500")
        preset_listbox = Listbox(load_window, width=40, height=15)
        preset_listbox.pack(pady=10)

        # List all .txt files in the presets directory
        presets = [f for f in os.listdir(presets_dir) if f.endswith(".txt")]
        for preset in presets:
            preset_listbox.insert(END, preset[:-4])

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
            selected_preset = preset_listbox.curselection()
            if selected_preset:
                preset_name = preset_listbox.get(selected_preset)
                preset_path = os.path.join(presets_dir, f"{preset_name}.txt")
                if os.path.exists(preset_path):
                    os.remove(preset_path)
                    print(f"Deleted preset: {preset_name}")
                    preset_listbox.delete(selected_preset)
                    embedded_events = []
                    update_event_overlays()

        load_button = tk.Button(
            load_window,
            text="Load Selected Preset",
            command=lambda: (
                load_selected(preset_listbox.curselection()),
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
        i = 0
        n = len(embedded_events)
        while is_running:
            event = embedded_events[i]
            if i >= n:
                i = 0

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
            elif event_type == "conditional":
                img_found = pyautogui.locateOnScreen(
                    event["image_path"], confidence=0.85, grayscale=True
                ) is not None
                if img_found is not None:
                    print(f"Condition met on screen!")

                kind = event["cond_kind"]
                if kind == "if":
                    i = event["true_target"] if img_found else i + 1
                elif kind == "if_else":
                    i = event["true_target"] if img_found else (
                        event["false_target"] if event["false_target"] >= 0 else i + 1
                    )
                elif kind == "while":
                    i = event["true_target"] if img_found else i + 1

                print("Traveling to event ", i)
                continue

        time.sleep(random_time_in_range(400, 3000) / 1000)
        i += 1

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

if isWindows:
    create_overlay()

# ──────────────────────────────────────────────────────────────
#  Root GUI: horizontal bar with C / S / W / T buttons
# ──────────────────────────────────────────────────────────────
event_bar = tk.Frame(root)
event_bar.pack(pady=10)                       # keep the rest of the layout

btn_click  = tk.Button(event_bar, text="C", width=0, command=lambda: add_event("click", grab_cursor=True, extra={"click_type": "left", "press_count": 1},))
btn_scroll = tk.Button(event_bar, text="S", width=0, command=lambda: add_event("scroll", grab_cursor=True, extra={"press_count": 300}, ))
btn_wait   = tk.Button(event_bar, text="W", width=0, command=lambda: (add_event("wait"), open_detailed_window(len(embedded_events) - 1)))
btn_text   = tk.Button(event_bar, text="T", width=0, command=create_text_event)
btn_logic   = tk.Button(event_bar, text="L", width=0, command=open_conditional_window)


for b in (btn_click, btn_scroll, btn_wait, btn_text, btn_logic):
    b.pack(side="left", padx=0)               # horizontal alignment

# ──────────────────────────────────────────────────────────────
#  Existing control buttons (unchanged)
# ──────────────────────────────────────────────────────────────
delete_button           = tk.Button(root, text="Delete Newest Event", command=delete_event)
rearrange_button        = tk.Button(root, text="Rearrange Events",    command=rearrange_events)
start_button            = tk.Button(root, text="Start Program",       command=start_program)
always_on_top_button    = tk.Button(root, text="Always on Top: Off",  command=toggle_always_on_top)
close_button            = tk.Button(root, text="Close & Save",        command=close_and_save)

for btn in (delete_button, rearrange_button, start_button,
            always_on_top_button, close_button):
    btn.pack(pady=10)                         # keep your existing vertical stack

listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

root.mainloop()
