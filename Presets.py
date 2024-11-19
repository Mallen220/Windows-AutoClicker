import os
import tkinter as tk
from tkinter import END, filedialog, Listbox, simpledialog, SINGLE, Toplevel
import ast
import Constants
import Root
import ScreenOverlay
import RearrangeEventsWindow


# Function to delete a preset file from the "Presets" directory
def delete_preset(name):
    if not os.path.exists(Constants.presets_dir):
        os.makedirs(Constants.presets_dir)

    file_path = os.path.join(Constants.presets_dir, f"{name}.txt")

    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Preset '{name}' deleted successfully.")
        else:
            print(f"Preset '{name}' not found.")
    except Exception as e:
        print(f"Error deleting preset '{name}': {e}")


def update_last_save_preset():
    if not os.path.exists(Constants.presets_dir):
        os.makedirs(Constants.presets_dir)

    # Check if the last_save.txt exists and if it does, update it
    try:
        save_preset("last_save")
    except Exception as e:
        print(f"Error updating last saved preset: {e}")

# Function to save the current settings as a preset
def save_preset(name=None):
    if not name:
        name = simpledialog.askstring("Save Preset", "Enter a name for this preset:")

    if not name:
        print("No name provided, preset save canceled.")
        return

    preset_path = os.path.join(Constants.presets_dir, f"{name}.txt")

    # Save the new preset
    with open(preset_path, "w") as f:
        f.write(f"- {name}\n")
        f.write(f"Delay: {Constants.delay_between_rounds}\n")
        for event_data in Constants.embedded_events:
            f.write(f"{str(event_data)}\n")
        f.write("\n")

    print(f"Preset '{name}' saved.")


def upload_preset():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        file_name = os.path.basename(file_path)
        new_file_path = os.path.join(Constants.presets_dir, file_name)
        if not os.path.exists(new_file_path):
            os.rename(file_path, new_file_path)
            print(f"Preset from {file_path} uploaded successfully.")
        else:
            print(f"Preset already exists: {file_name}")

        load_window.destroy()

def load_selected(selected_preset=None):
    if selected_preset is None:
        selected_preset = listbox.get(selected_preset)
    if selected_preset:
        Constants.embedded_events = []
        preset_name = selected_preset
        preset_path = os.path.join(Constants.presets_dir, f"{preset_name}.txt")

        try:
            with open(preset_path, "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("- "):
                        continue
                    elif line.startswith("Delay: "):
                        delay_between_rounds = int(line.split(":")[1].strip())
                    else:
                        try:
                            event_data = ast.literal_eval(line)
                            if "position" in event_data:
                                event_data["position"] = tuple(
                                    map(int, event_data["position"])
                                )

                            Constants.embedded_events.append(event_data)
                        except (ValueError, SyntaxError) as e:
                            print(f"Error loading event: {e}")
                            continue
        except FileNotFoundError:
            print(f"Preset file '{preset_name}' not found.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        ScreenOverlay.update_event_overlays()
        load_window.destroy()
        try:
            RearrangeEventsWindow.rearrange_window.destroy()
        except Exception as e:
            print(f"The rearrange_window is likely not open so cannot be closed: {e}")

def delete_selected(selected_preset=None):
    if selected_preset is None:
        selected_preset = listbox.get(selected_preset)
    if selected_preset:
        preset_name = selected_preset
        preset_path = os.path.join(Constants.presets_dir, f"{preset_name}.txt")
        if os.path.exists(preset_path):
            os.remove(preset_path)
            print(f"Deleted preset: {preset_name}")
            listbox.delete(selected_preset)
            Constants.embedded_events = []
            ScreenOverlay.update_event_overlays()

    load_button = tk.Button(
        load_window, text="Load Selected Preset", command=load_selected
    )
    load_button.pack(pady=10)

    upload_button = tk.Button(
        load_window, text="Upload Preset", command=upload_preset
    )
    upload_button.pack(pady=10)

    delete_button = tk.Button(
        load_window, text="Delete Selected Preset", command=delete_selected
    )
    delete_button.pack(pady=10)

if __name__ == "__main__":
    load_window = Toplevel(Root.window)
    Constants.icon_per_os(load_window)
    load_window.title("Load Preset")
    load_window.geometry("300x500")
    listbox = Listbox(load_window, width=40, height=15)
    listbox.pack(pady=10)

    # List all .txt files in the presets directory
    presets = [f for f in os.listdir(Constants.presets_dir) if f.endswith(".txt")]
    for preset in presets:
        listbox.insert(END, preset[:-4])
