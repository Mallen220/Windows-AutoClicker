import Constants
import pyautogui
import tkinter as tk
from tkinter import END, filedialog, Listbox, simpledialog, SINGLE, Toplevel
import EventFunctions
import Root
import ScreenOverlay
import KeyTracker
import Text
import RearrangeEventsWindow

def open_detailed_window(idx=None):
    import listbox
    if idx is None:
        idx = listbox.event_listbox.curselection()[0]
    if (
            Constants.embedded_events[idx]["type"] == "click"
            or Constants.embedded_events[idx]["type"] == "scroll"
            or Constants.embedded_events[idx]["type"] == "wait"
    ):
        if RearrangeEventsWindow.rearrange_window is None:
            detailed_event_window = Toplevel(Root.window)
        else:
            detailed_event_window = Toplevel(RearrangeEventsWindow.rearrange_window)
        Constants.icon_per_os(detailed_event_window)
        detailed_event_window.title(f"Set Timeout for Event {idx + 1}")

        timeout_label = tk.Label(detailed_event_window, text="Timeout? (ms)")
        timeout_label.pack(pady=5)
        timeout_entry = tk.Entry(detailed_event_window)
        timeout_entry.pack(pady=5)
        timeout_entry.insert(0, str(Constants.embedded_events[idx]["delay"]))

        if not Constants.embedded_events[idx]["type"] == "wait":
            press_count_label = tk.Label(
                detailed_event_window, text="How many times to click:"
            )
            press_count_label.pack(pady=5)
            press_count_entry = tk.Entry(detailed_event_window)
            press_count_entry.pack(pady=5)
            press_count_entry.insert(0, str(Constants.embedded_events[idx].get("press_count", 1)))

            options = ["left", "middle", "right"]
            clicked = tk.StringVar()
            clicked.set(Constants.embedded_events[idx].get("click_type", "left"))

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

        delete_event = tk.Button(
            detailed_event_window,
            text="Delete Event",
            command=EventFunctions.delete_event(idx),
        )
        delete_event.pack(pady=10)

        if not Constants.embedded_events[idx]["type"] == "wait":

            move_event = tk.Button(
                detailed_event_window,
                text="Move Event",
                command=Root.move_selected_event(),
            )
            move_event.pack(pady=10)

        def save_details():
            new_timeout = timeout_entry.get()
            try:
                if (
                        Constants.embedded_events[idx]["type"] == "scroll"
                        or Constants.embedded_events[idx]["type"] == "click"
                ):
                    try:
                        new_press_count = int(press_count_entry.get())
                    except ValueError:
                        if Constants.embedded_events[idx]["type"] == "scroll":
                            new_press_count = 300
                        else:
                            new_press_count = 1

                    try:
                        Constants.embedded_events[idx]["delay"] = int(new_timeout)
                        Constants.embedded_events[idx]["press_count"] = new_press_count
                        Constants.embedded_events[idx]["click_type"] = clicked.get()
                        Constants.embedded_events[idx]["random_time"] = random_time_var.get()
                        print(f"Updated details of Event {idx + 1}: {Constants.embedded_events[idx]}")

                        Constants.update_listbox()
                        detailed_event_window.destroy()
                    except ValueError:
                        print("Please enter a valid number for the detailed window.")
                elif Constants.embedded_events[idx]["type"] == "wait":
                    try:
                        Constants.embedded_events[idx]["delay"] = int(new_timeout)
                        Constants.embedded_events[idx]["random_time"] = random_time_var.get()
                        print(f"Updated details of Event {idx + 1}: {Constants.embedded_events[idx]}")

                        Constants.update_listbox()
                        detailed_event_window.destroy()
                    except ValueError:
                        print("Please enter a valid number for the detailed window.")
            except Exception as e:
                print(
                    "Wow! An error occurred. Are there no events? Constants.embedded_events[idx] is likely out of range. ")
                Constants.update_listbox()
                detailed_event_window.destroy()

        save_button = tk.Button(
            detailed_event_window, text="Save", command=save_details
        )
        save_button.pack(pady=10)
    elif Constants.embedded_events[idx]["type"] == "text":
        global is_text_mode
        if not is_text_mode:
            is_text_mode = True
            Text.open_text_input(idx)
        else:
            Text.stop_text_input()

        if RearrangeEventsWindow.rearrange_window is not None:
            RearrangeEventsWindow.rearrange_window.destroy()
