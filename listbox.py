from tkinter import END, filedialog, Listbox, simpledialog, SINGLE, Toplevel
import Constants

# Listbox
event_listbox = Listbox(None, selectmode=SINGLE, width=40, height=10)

def initialize_listbox(parent_window):
    global event_listbox
    event_listbox = Listbox(parent_window, selectmode=SINGLE, width=40, height=10)
    event_listbox.bind("<Double-Button-1>", on_double_click)

def on_double_click(event):
    import RearrangeEventsWindow
    RearrangeEventsWindow.on_double_click(event)

def update_listbox():
    try:
        event_listbox.delete(0, END)
        for i, event_data in enumerate(Constants.embedded_events):
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
        print("Listbox does not exist. Failed to update listbox. Exiting...")