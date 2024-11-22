import Constants
import pyautogui
import time
import Text
import KeyTracker
import pyperclip
import threading


def start_program():
    global is_running
    is_running = True
    # Root.start_button.config(text="Stop Program", command=stop_program)
    print("Program started!")

    def run_events():
        while is_running:
            for event_data in Constants.embedded_events:
                if not is_running:
                    break
                if event_data["type"] == "click":
                    x, y = event_data["position"]
                    temp_click_type = event_data["click_type"]
                    temp_press_count = event_data["press_count"]
                    pyautogui.click(
                        x, y, button=str(temp_click_type), clicks=int(temp_press_count)
                    )
                    print(
                        f"Clicked {temp_click_type} {temp_press_count} time(s) at position: ({x}, {y})"
                    )
                    if event_data["random_time"]:
                        time.sleep(
                            Constants.random_time_in_range()
                        )
                    else:
                        time.sleep(event_data["delay"] / 1000)
                elif event_data["type"] == "scroll":
                    x, y = event_data["position"]
                    temp_press_count = event_data["press_count"]
                    pyautogui.scroll(temp_press_count, x=x, y=y)
                    print(
                        f"Scrolled {temp_press_count} time(s) at position: ({x}, {y})"
                    )
                    if event_data["random_time"]:
                        time.sleep(
                            Constants.random_time_in_range()
                        )
                    else:
                        time.sleep(event_data["delay"] / 1000)
                elif event_data["type"] == "text":
                    if event_data["content"] == "Copy":
                        pyautogui.hotkey("ctrl", "c")
                    elif event_data["content"] == "Paste":
                        pyautogui.hotkey("ctrl", "v")
                    elif event_data["content"] == "Control Right Arrow":
                        pyautogui.hotkey("ctrl", "right")
                    elif event_data["delay"] == 0:
                        pyperclip.copy(event_data["content"])
                        pyautogui.hotkey("ctrl", "v")
                    else:
                        Text.type_text(
                            event_data["content"],
                            (
                                (event_data["delay"] / 1000)
                                if not event_data["random_time"]
                                else Constants.random_time_in_range()
                            ),
                        )
                    print(f"Typed text: {event_data['content']}")
                elif event_data["type"] == "wait":
                    print(f"Waiting: {event_data['delay'] / 1000} s")
                    time.sleep(event_data["delay"] / 1000)

            time.sleep(Constants.random_time_in_range(400, 3000) / 1000)

    thread = threading.Thread(target=run_events)
    thread.start()

    monitor_space_key()


# Function to stop the program
def stop_program():
    import Root
    global is_running
    is_running = False
    Root.start_button.config(text="Start Program", command=start_program)
    print("Program stopped!")


# Function to monitor the space key to stop the program
def monitor_space_key():
    def stop_on_space_key():
        while is_running:
            if KeyTracker.is_pressed("space"):
                stop_program()

    thread = threading.Thread(target=stop_on_space_key)
    thread.start()