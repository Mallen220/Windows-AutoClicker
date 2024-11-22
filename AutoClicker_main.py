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

Root.create_button.pack(pady=10)
Root.delete_button.pack(pady=10)

Root.rearrange_button.pack(pady=10)

Root.start_button.pack(pady=10)
Root.always_on_top_button.pack(pady=10)

Root.close_button.pack(pady=10)

Root.window.mainloop()
