import Constants
import tkinter as tk


# Function to enable dragging the window by clicking anywhere
def on_drag_start(event):
    window._drag_data = {"x": event.x, "y": event.y}

def on_drag_motion(event):
    delta_x = event.x - window._drag_data["x"]
    delta_y = event.y - window._drag_data["y"]
    new_x = window.winfo_x() + delta_x
    new_y = window.winfo_y() + delta_y
    window.geometry(f"+{new_x}+{new_y}")

# Function to close and save the events and update the "Last save" preset
def close_and_save():
    import Presets
    print("Updating 'Last save' preset...")

    Presets.update_last_save_preset()

    print("Closing program.")
    window.quit()

# Function to toggle "always on top"
def toggle_always_on_top():
    Constants.always_on_top = not Constants.always_on_top
    window.attributes("-topmost", Constants.always_on_top)
    always_on_top_button.config(
        text="Always on Top: ON" if Constants.always_on_top else "Always on Top: OFF"
    )


window = tk.Tk()
window.title("Event Controller")
Constants.icon_per_os(window)
window.attributes("-alpha", 0.85)
window.geometry("225x350")

window.bind("<Button-1>", on_drag_start)
window.bind("<B1-Motion>", on_drag_motion)
# window.bind("<Control-z>", lambda event: UndoRedo.undo())
# window.bind("<Control-Z>", lambda event: UndoRedo.undo())
# window.bind("<Control-Shift-Z>", lambda event: UndoRedo.redo())

import RuntimeFunctions
import EventFunctions
start_button = tk.Button(window, text="Start Program", command=RuntimeFunctions.start_program())

always_on_top_button = tk.Button(window, text="Always on Top: Off", command=toggle_always_on_top)
close_button = tk.Button(window, text="Close & Save", command=close_and_save)
create_button = tk.Button(window, text="Create Event", command=EventFunctions.create_event)
delete_button = tk.Button(window, text="Delete Newest Event", command=EventFunctions.delete_event)
import RearrangeEventsWindow
rearrange_button = tk.Button(window, text="Rearrange Events", command=RearrangeEventsWindow.create_rearrange_window) #RearrangeEventsWindow