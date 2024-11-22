import Constants
import tkinter as tk
from tkinter import END, Toplevel

import DetailedWindow
import Root
import ScreenOverlay

def save_delay():
    try:
        if 'delay_entry' not in globals() and 'delay_entry' not in locals():
            delay_entry = 500
        Constants.delay_between_rounds = int(delay_entry.get())
        print(f"Updated delay between rounds: {Constants.delay_between_rounds} ms")
    except ValueError:
        print("Please enter a valid number for the delay.")

def move_up():
    import listbox
    selected_idx = listbox.event_listbox.curselection()
    if not selected_idx or selected_idx[0] == 0:
        return
    selected_idx = selected_idx[0]
    Constants.embedded_events[selected_idx], Constants.embedded_events[selected_idx - 1] = (
        Constants.embedded_events[selected_idx - 1],
        Constants.embedded_events[selected_idx],
    )
    listbox.update_listbox()
    listbox.event_listbox.select_set(selected_idx - 1)
    ScreenOverlay.update_event_overlays()

def move_down():
    import listbox
    selected_idx = listbox.event_listbox.curselection()
    if not selected_idx or selected_idx[0] == len(Constants.embedded_events) - 1:
        return
    selected_idx = selected_idx[0]
    Constants.embedded_events[selected_idx], Constants.embedded_events[selected_idx + 1] = (
        Constants.embedded_events[selected_idx + 1],
        Constants.embedded_events[selected_idx],
    )
    listbox.update_listbox()
    listbox.event_listbox.select_set(selected_idx + 1)
    ScreenOverlay.update_event_overlays()

def on_double_click(useless):
    import listbox
    selected_idx = listbox.event_listbox.curselection()
    if selected_idx:
        DetailedWindow.open_detailed_window(selected_idx[0])

def create_rearrange_window():
    # Function to rearrange events and adjust timings
    rearrange_window = Toplevel(Root.window)
    Constants.icon_per_os(rearrange_window)
    rearrange_window.title("Rearrange Events")
    rearrange_window.geometry("500x700")

    import listbox
    listbox.initialize_listbox(rearrange_window)
    rearrange_window.after(100, listbox.should_update_listbox)
    listbox.event_listbox.pack(pady=10)

    for i, event_data in enumerate(Constants.embedded_events):
        if event_data["type"] == "click" or event_data["type"] == "scroll":
            listbox.event_listbox.insert(END, f"Event {i + 1}: {event_data['position']}")
        elif event_data["type"] == "text":
            listbox.event_listbox.insert(END, f"Event {i + 1}: {event_data['content']}")
        elif event_data["type"] == "wait":
            listbox.event_listbox.insert(END, f"Event {i + 1}: Wait {event_data['delay']} ms")

    delay_label = tk.Label(rearrange_window, text="Delay Between Rounds (ms):")
    delay_label.pack(pady=5)
    delay_entry = tk.Entry(rearrange_window)
    delay_entry.pack(pady=5)
    delay_entry.insert(0, str(Constants.delay_between_rounds))

    import EventFunctions
    save_delay_button = tk.Button(rearrange_window, text="Save Delay", command=save_delay)

    save_delay_button.pack(pady=5)

    delete_all_events_button = tk.Button(
        rearrange_window,
        text="Delete All Events (Can't Undo)",
        command=EventFunctions.delete_all_events,
    )
    delete_all_events_button.pack(pady=5)


    randomize_all_button = tk.Button(
        rearrange_window,
        text="Randomize All Times",
        command=EventFunctions.randomize_all_times,
    )
    randomize_all_button.pack(pady=5)

    move_up_button = tk.Button(rearrange_window, text="Move Up", command=move_up)
    move_down_button = tk.Button(rearrange_window, text="Move Down", command=move_down)
    close_rearrange_events_button = tk.Button(rearrange_window, text="Close", command=rearrange_window.destroy)
    move_up_button.pack(pady=5)
    move_down_button.pack(pady=5)
    import Presets
    Presets.create_buttons(rearrange_window)
    close_rearrange_events_button.pack(pady=10)