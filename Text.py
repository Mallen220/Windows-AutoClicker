import time
import Constants
import Root
import tkinter as tk
from tkinter import END, Toplevel
import pyautogui


# Function to stop text input mode and close the input window
def stop_text_input(idx=None):
    if input_window:
        if idx is None:
            save_text()
        else:
            save_text(idx)

def open_text_input(idx=None):
    global input_window, text_box, instant_type_var
    input_window = Toplevel(Root.window)
    Constants.icon_per_os(input_window)
    input_window.title("Enter Text")
    if idx is None:
        input_window.geometry("500x350")
    else:
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
    if idx is None:
        save_button = tk.Button(input_window, text="Save Text", command=save_text)
    else:
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

def set_text_input(text):
    text_box.delete(1.0, END)
    text_box.insert(END, text)
    save_text()

# Function to save text from the input box and close the window
def save_text(idx=None, is_random_time=None):
    try:
        text = text_box.get("1.0", tk.END).strip()
        if text:
            if idx is None:
                event_data = {
                    "type": "text",
                    "content": text,
                    "delay": 0 if instant_type_var.get() else 100,
                    "random_time": False,
                }
                Constants.embedded_events.append(event_data)
            else:
                event_data = {
                    "type": "text",
                    "content": text,
                    "delay": 0 if instant_type_var.get() else 100,
                    "random_time": is_random_time,
                }
                Constants.embedded_events[idx] = event_data
            print(f"Text event created: {text}")
    except Exception as e:
        print(e)
        print(
            "An Error has occurred while saving text (Maybe bad text?). No text will be saved and the menu will be closed."
        )
    input_window.destroy()
    Constants.is_text_mode = False
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
                    (key for key in Constants.special_keys if special_key.startswith(key)), None
                )
                if next_special_key:
                    pyautogui.press(Constants.special_keys[next_special_key])
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