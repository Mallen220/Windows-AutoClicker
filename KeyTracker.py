from pynput import keyboard


pressed_keys = set()

def on_press(key):
    """Callback for when a key is pressed"""
    try:
        # Add the pressed key to the set
        pressed_keys.add(key.char if hasattr(key, 'char') else key)
    except AttributeError:
        pressed_keys.add(key)


def on_release(key):
    """Callback for when a key is released"""
    try:
        # Remove the released key from the set
        pressed_keys.remove(key.char if hasattr(key, 'char') else key)
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


keyboard.Listener(on_press=on_press, on_release=on_release).start() #Starts listening when program is running