import ButtonVariables
import Constants
import Root
import ScreenOverlay
import Text
import UndoRedo


# Windows: pyinstaller --onefile --windowed --icon=AutoClicker.ico --add-data "AutoClicker.ico;." --add-data "Presets;Presets" AutoClicker_main.py
# Ubuntu: pyinstaller --onefile --windowed --icon=AutoClicker.ico --add-data "AutoClicker.ico:." --add-data "Presets:Presets" AutoClicker_main.py
# sudo apt-get install xclip for Ubuntu



ScreenOverlay.create_overlay(Root.window)

ButtonVariables.create_button.pack(pady=10)
ButtonVariables.delete_button.pack(pady=10)

ButtonVariables.rearrange_button.pack(pady=10)

Root.start_button.pack(pady=10)
ButtonVariables.always_on_top_button.pack(pady=10)

ButtonVariables.close_button.pack(pady=10)

Root.window.mainloop()
