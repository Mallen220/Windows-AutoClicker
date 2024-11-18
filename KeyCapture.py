import tkinter as tk
from pynput import keyboard
import threading


class KeyCapture:
    def __init__(self, root):
        self.root = root
        self.root.title("Key Capture")
        self.root.geometry("400x200")

        self.label = tk.Label(root, text="Press any keys...  (Enter to close)", font=("Arial", 16))
        self.label.pack(pady=20)

        self.current_keys = set()
        self.sticky_keys = set()
        self.all_released = True

        self.listener = keyboard.Listener(on_press=self.on_key_press, on_release=self.on_key_release)
        self.listener.start()

        self.root.bind('<Return>', self.on_enter)

    def on_key_press(self, key):
        """Handle key press event to update current keys and label display."""
        self.all_released = False

        try:
            if key.char not in self.current_keys:
                self.current_keys.add(key.char)
        except AttributeError:
            if key not in self.current_keys and key != keyboard.Key.enter:
                self.current_keys.add(key)

        if key != keyboard.Key.enter:
            self.sticky_keys = self.current_keys.copy()
        self.update_label()

    def on_key_release(self, key):
        """Handle key release event and check if all keys have been released."""
        try:
            if key.char in self.current_keys:
                self.current_keys.remove(key.char)
        except AttributeError:
            if key in self.current_keys:
                self.current_keys.remove(key)

        if not self.current_keys:
            self.all_released = True

    def update_label(self):
        """Update the label with the current sticky keys."""
        keys_str = " + ".join(self.get_key_name(key) for key in self.sticky_keys)
        self.label.config(text=keys_str)

    def get_key_name(self, key):
        """Get the string representation of a key."""
        if isinstance(key, keyboard.Key):
            return key.name
        else:
            return key

    def on_enter(self, event):
        """Stop capturing keys and return the pressed keys if Enter is pressed alone."""
        if len(self.current_keys) == 0:
            self.listener.stop()
            self.root.destroy()
            self.root.quit()


def start_key_capture():
    root = tk.Tk()
    app = KeyCapture(root)
    root.mainloop()
    return app.sticky_keys


# Example usage
if __name__ == "__main__":
    pressed_keys = start_key_capture()
    print("Captured keys:", pressed_keys)