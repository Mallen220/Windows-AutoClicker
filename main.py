import tkinter as tk
from tkinter import Toplevel, Listbox, END, SINGLE
import pyautogui
import time
import threading
import random
import keyboard

# Global list to store events (as positions)
events = []
timing_data = []  # List to store timing data (in milliseconds)
is_running = False
always_on_top = False  # Keep track of the "always on top" state
overlay_active = True  # Overlay state
is_text_mode = False
event_count = 0  # To track consecutive event creations
max_event_count = 4  # Limit for consecutive event creation without pressing 'z'


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


def create_event():
    global is_text_mode, event_count
    if event_count >= max_event_count:
        print("You need to press 'z' before creating more events.")
        return

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
        event_count = 0  # Reset the event counter after pressing 'z'

        # Create a mouse click event at the current mouse position
        x, y = pyautogui.position()
        events.append((x, y))
        timing_data.append(100)  # Default wait time in milliseconds
        print(f"Event created at position: ({x}, {y})")

        # Update overlays for all events after creating a new one
        update_event_overlays()

    event_count += 1  # Increment the event count

# Function to stop text input mode and close the input window
def stop_text_input():
    if input_window:
        save_text()  # Save and close text input when user clicks "Create Event" again


# Function to delete the newest event
def delete_newest_event():
    if events:
        events.pop()
        print("Deleted the newest event.")
    else:
        print("No events to delete.")

# Function to update overlays for all events
def update_event_overlays():
    # Clear all existing overlays
    for label in overlay.label_dict.values():
        label.destroy()

    # Recreate overlays for all events with the correct color
    for event_num, event in enumerate(events, 1):
        if isinstance(event, tuple):  # Mouse click event
            x, y = event
            create_event_overlay(event_num, x, y)
        elif isinstance(event, str):  # Text event
            # For text events, just create an overlay at the position of the last mouse event
            # or use default coordinates (optional: adjust how you want text events shown)
            x, y = pyautogui.position()  # Default to current position for now
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
            label_color = "purple"  # Text event
        else:
            label_color = "red"  # Mouse click event

        label = tk.Label(overlay, text=str(event_num), fg=label_color, font=("Arial", 24))
        label.place(x=x, y=y)
        overlay.label_dict[event_num] = label


# Function to open a text input window with multiline support
def open_text_input():
    global input_window, text_box
    input_window = Toplevel(root)
    input_window.title("Enter Text")
    input_window.geometry("300x200")

    label = tk.Label(input_window, text="Enter text to simulate (Press 'Enter' for new line):")
    label.pack(pady=5)

    # Create a text box for multiline input
    text_box = tk.Text(input_window, width=40, height=5)
    text_box.pack(pady=5)
    text_box.focus()

    # Button to save and close the text input box (this will be triggered manually)
    save_button = tk.Button(input_window, text="Save Text", command=save_text)
    save_button.pack(pady=5)


# Function to save text from the input box and close the window
def save_text():
    global is_text_mode
    user_text = text_box.get("1.0", tk.END).strip()  # Get text input (multiline)
    if user_text:
        events.append(user_text)
        timing_data.append(100)  # Default typing speed (100 ms per character)
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
        timing_data[selected_idx], timing_data[selected_idx - 1] = timing_data[selected_idx - 1], timing_data[selected_idx]
        update_listbox()
        event_listbox.select_set(selected_idx - 1)
        update_event_overlays()  # Update event overlays after moving

    def move_down():
        selected_idx = event_listbox.curselection()
        if not selected_idx or selected_idx[0] == len(events) - 1:
            return
        selected_idx = selected_idx[0]
        events[selected_idx], events[selected_idx + 1] = events[selected_idx + 1], events[selected_idx]
        timing_data[selected_idx], timing_data[selected_idx + 1] = timing_data[selected_idx + 1], timing_data[selected_idx]
        update_listbox()
        event_listbox.select_set(selected_idx + 1)
        update_event_overlays()  # Update event overlays after moving

    def update_listbox():
        event_listbox.delete(0, END)
        for i, event in enumerate(events):
            event_listbox.insert(END, f"Event {i + 1}: {event}")

    def open_timeout_window(idx):
        # Open a window to ask for the timeout (in ms)
        timeout_window = Toplevel(rearrange_window)
        timeout_window.title(f"Set Timeout for Event {idx + 1}")

        label = tk.Label(timeout_window, text="Timeout? (ms)")
        label.pack(pady=5)

        timeout_entry = tk.Entry(timeout_window)
        timeout_entry.pack(pady=5)
        timeout_entry.insert(0, str(timing_data[idx]))  # Set the current timing data as default

        def save_timeout():
            new_timeout = timeout_entry.get()
            try:
                timing_data[idx] = int(new_timeout)  # Update the timing data
                print(f"Updated timing for Event {idx + 1}: {new_timeout} ms")
                update_listbox()  # Refresh the listbox after updating timing
                timeout_window.destroy()  # Close the window
            except ValueError:
                print("Please enter a valid number for the timeout.")

        save_button = tk.Button(timeout_window, text="Save", command=save_timeout)
        save_button.pack(pady=10)

    # Bind double-click event to open timeout window
    def on_double_click(event):
        selected_idx = event_listbox.curselection()
        if selected_idx:
            open_timeout_window(selected_idx[0])

    event_listbox.bind("<Double-Button-1>", on_double_click)

    move_up_button = tk.Button(rearrange_window, text="Move Up", command=move_up)
    move_up_button.pack(pady=5)

    move_down_button = tk.Button(rearrange_window, text="Move Down", command=move_down)
    move_down_button.pack(pady=5)

    close_button = tk.Button(rearrange_window, text="Close", command=rearrange_window.destroy)
    close_button.pack(pady=10)


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
                if isinstance(event, tuple):  # Mouse click event
                    x, y = event
                    pyautogui.click(x, y)
                    print(f"Clicked at position: ({x}, {y})")
                    time.sleep(timing_data[i] / 1000)  # Wait based on timing data
                elif isinstance(event, str):  # Keyboard input event
                    type_text(event, timing_data[i] / 1000)  # Use the new function for finer control
                    print(f"Typed text: {event}")
            time.sleep(0.5)  # Delay between rounds

    thread = threading.Thread(target=run_events)
    thread.start()

    # Monitor for space key press to stop the program
    monitor_space_key()

# Function to simulate typing text with pyautogui.press() for finer control
def type_text(text, interval):
    for char in text:
        if char == ' ':
            pyautogui.press('space')
        elif char == '\n':
            pyautogui.press('enter')
        else:
            pyautogui.press(char)
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


# GUI Setup
root = tk.Tk()
root.title("Event Controller")

# Set window transparency
root.attributes("-alpha", 0.85)  # Semi-transparent
root.geometry("300x600")

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





