import pyautogui
import Constants
import UndoRedo
import ScreenOverlay
import KeyTracker


# Function to modify an event
def modify_event(
        index,
        new_event,
        new_timing,
        new_click_type=None,
        new_press_count=None,
        new_random_time=None,
):
    if 0 <= index < len(Constants.embedded_events):
        if isinstance(Constants.embedded_events[index], dict):
            if "type" in Constants.embedded_events[index]:
                if Constants.embedded_events[index]["type"] == "click":
                    Constants.embedded_events[index]["position"] = new_event
                    Constants.embedded_events[index]["delay"] = new_timing
                    if new_click_type is not None:
                        Constants.embedded_events[index]["click_type"] = new_click_type
                    if new_random_time is not None:
                        Constants.embedded_events[index]["random_time"] = new_random_time
                    else:
                        Constants.embedded_events[index]["random_time"] = False
                    if new_press_count is not None:
                        Constants.embedded_events[index]["press_count"] = new_press_count
                elif Constants.embedded_events[index]["type"] == "text":
                    Constants.embedded_events[index]["content"] = new_event
                    Constants.embedded_events[index]["delay"] = new_timing
        print(f"Event {index + 1} modified: {new_event}, Delay: {new_timing}ms")


# Function to create an event
def create_event():
    import Text
    import DetailedWindow
    if KeyTracker.is_pressed("ctrl_l") or KeyTracker.is_pressed("ctrl_r") or KeyTracker.is_pressed("ctrl"):
        if not Constants.is_text_mode:
            Constants.is_text_mode = True
            Text.open_text_input()
        else:
            Text.stop_text_input()
    elif KeyTracker.is_pressed("w"):
        new_event = Constants.embedded_events.append(
            {
                "type": "wait",
                "delay": 100,
                "random_time": False,
            }
        )
        DetailedWindow.open_detailed_window(len(Constants.embedded_events) - 1)
    elif KeyTracker.is_pressed("shift"):
        print("Waiting for 'space' key press to create the scroll event...")
        KeyTracker.wait_for_key("space")
        x, y = pyautogui.position()

        new_event = Constants.embedded_events.append(
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
        KeyTracker.wait_for_key("space")
        x, y = pyautogui.position()

        new_event = Constants.embedded_events.append(
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
    UndoRedo.add_to_undo_stack(("create", new_event))

    Constants.redo_stack.clear()
    ScreenOverlay.update_event_overlays()

def delete_event(idx=None):
    import listbox
    if idx is None:
        idx = len(Constants.embedded_events) - 1
    if Constants.embedded_events:
        deleted_event = Constants.embedded_events.pop(idx)
        UndoRedo.add_to_undo_stack(("delete", deleted_event))
        print(f"Deleted event at position: {deleted_event}")
        ScreenOverlay.update_event_overlays()
        listbox.update_listbox()
        print("Deleted the newest event.")
    else:
        print("No events to delete.")

def delete_all_events():
    for i in range(len(Constants.embedded_events)):
        delete_event()

def randomize_all_times():
    for i in range(len(Constants.embedded_events)):
        Constants.embedded_events[i]["random_time"] = True
        print(f"Randomized timing for Event {i + 1}: True")
    ScreenOverlay.update_event_overlays()

def move_selected_event(idx=None):
    if idx is None:
        idx = len(Constants.embedded_events) - 1
    print("Waiting for 'space' key press to move the event...")
    KeyTracker.wait_for_key("space")
    x, y = pyautogui.position()
    if Constants.embedded_events[idx]["type"] == "click":
        Constants.embedded_events[idx] = {
            "type": "click",
            "position": (x, y),
            "click_type": Constants.embedded_events[idx]["click_type"],
            "press_count": Constants.embedded_events[idx]["press_count"],
            "delay": Constants.embedded_events[idx]["delay"],
        }
    elif Constants.embedded_events[idx]["type"] == "scroll":
        Constants.embedded_events[idx] = {
            "type": "scroll",
            "position": (x, y),
            "press_count": Constants.embedded_events[idx]["press_count"],
            "delay": Constants.embedded_events[idx]["delay"],
        }
    ScreenOverlay.update_event_overlays()