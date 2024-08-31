# Windows AutoClicker Program README

## Overview

The **AutoClicker Program** is a versatile automation tool that allows users to create and manage a sequence of mouse clicks and keyboard events. This program offers a user-friendly interface to add, modify, and delete events, as well as the ability to save and load event presets. The program supports various automation features, such as click events, text typing, and adjustable time delays between events. The program also includes an overlay window that displays numbered labels at the event locations for easier visualization.

---

## Features

- **Event Creation**: Capture mouse click events or keyboard text inputs by pressing `Space`. Supports both instant and delayed text inputs.
- **Text Input Mode**: Use `Ctrl` when creating an event to switch into text input mode and simulate typing text with optional instant typing.
- **Overlay Window**: Displays numbered markers for event locations on the screen. The overlay window can be toggled and moved.
- **Event Modification**: Modify the timing or position of previously added events.
- **Preset Management**: Save and load event sequences as presets for future use. Presets can be uploaded from external files and deleted.
- **Rearrange Events**: Adjust the order of events and modify event delays.
- **Always-on-Top Toggle**: Keep the main window on top of other windows.
- **Adjustable Delay Between Rounds**: Set delays between entire rounds of event sequences.

---

## Usage

### Initial Setup
- **Event Overlay**: A semi-transparent window will appear showing event numbers as markers at their locations.
- **Always on Top**: The application can be set to always stay on top using the toggle button.
- **Adding Events**:  
  - **Mouse Click Events**: Press `Space` to capture the current mouse cursor position as a click event.  
  - **Text Input Events**: Press `Ctrl` when creating an event to switch to text input mode, type the desired text, and press "Save Text" to add the text event.  
  - **Modify Event Delays**: Open the rearrange window, double-click an event, and modify its delay (in milliseconds).

### Buttons and Functions

#### Main Buttons:
- **Create Event**: Press to add a mouse click event at the current mouse cursor position. Text input is created when `Ctrl` is pressed when creating an event.
- **Delete Newest Event**: Deletes the most recently added event.
- **Rearrange Events**: Opens a new window that allows you to change the order of events, adjust timing delays, and save/load presets.
- **Always on Top**: Toggles the window’s ability to remain on top of other windows.
- **Save Preset**: Saves the current event list and timing as a named preset.
- **Load Preset**: Loads a saved preset of events, replacing the current event list.

#### Inside Rearrange Events:
- **Move Up**: Moves the selected event up in the list.
- **Move Down**: Moves the selected event down in the list.
- **Save Delay**: Saves the set delay between rounds of events (in milliseconds).
- **Load Preset**: Opens a dialog to load a preset from disk.
- **Upload Preset**: Allows you to upload a preset file from your computer.
- **Delete Preset**: Deletes a selected preset.
- **Double-Click Event**: Modify the timing for a selected event by double-clicking on it.
  
---

## Allowed Keyboard Input (Text Input Mode)

- **Text**: You can input text for typing events.
- **Special Keys**: The following special keys can be used in text input if they are preceded by a "\\": 

'\t', '\n', '\r', ' ', '!', '"', '#', '$', '%', '&', "'", '(',
')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7',
'8', '9', ':', ';', '<', '=', '>', '?', '@', '[', '\\', ']', '^', '_', '`',
'a', 'b', 'c', 'd', 'e','f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o',
'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~',
'accept', 'add', 'alt', 'altleft', 'altright', 'apps', 'backspace',
'browserback', 'browserfavorites', 'browserforward', 'browserhome',
'browserrefresh', 'browsersearch', 'browserstop', 'capslock', 'clear',
'convert', 'ctrl', 'ctrlleft', 'ctrlright', 'decimal', 'del', 'delete',
'divide', 'down', 'end', 'enter', 'esc', 'escape', 'execute', 'f1', 'f10',
'f11', 'f12', 'f13', 'f14', 'f15', 'f16', 'f17', 'f18', 'f19', 'f2', 'f20',
'f21', 'f22', 'f23', 'f24', 'f3', 'f4', 'f5', 'f6', 'f7', 'f8', 'f9',
'final', 'fn', 'hanguel', 'hangul', 'hanja', 'help', 'home', 'insert', 'junja',
'kana', 'kanji', 'launchapp1', 'launchapp2', 'launchmail',
'launchmediaselect', 'left', 'modechange', 'multiply', 'nexttrack',
'nonconvert', 'num0', 'num1', 'num2', 'num3', 'num4', 'num5', 'num6',
'num7', 'num8', 'num9', 'numlock', 'pagedown', 'pageup', 'pause', 'pgdn',
'pgup', 'playpause', 'prevtrack', 'print', 'printscreen', 'prntscrn',
'prtsc', 'prtscr', 'return', 'right', 'scrolllock', 'select', 'separator',
'shift', 'shiftleft', 'shiftright', 'sleep', 'space', 'stop', 'subtract', 'tab',
'up', 'volumedown', 'volumemute', 'volumeup', 'win', 'winleft', 'winright', 'yen',
'command', 'option', 'optionleft', 'optionright'

---

## Example Flow

1. **Start Program**: Open the AutoClicker application.
2. **Create Events**: Press `Space` to capture the mouse position as an event. Press `Ctrl` when creating an event to enter text input mode and add typing events.
3. **View Events**: Numbered labels will appear on the screen showing event positions.
4. **Modify Events**: Open the rearrange window, move events up or down, and adjust delays.
5. **Save Preset**: Save the sequence of events as a preset for future use.
6. **Load Preset**: Load a preset to quickly repeat previously created events.

---

## TODO List

1. **Improve error handling when entering incorrect input in text input mode**.
2. **Optimize event overlay for large screens and 2 screens**.
3. **Enable conditional events (e.g., click only if a certain condition is met)**.
4. **Provide an option for automatic screen recording during event sequences**.
5. **Add hotkey customization for more flexible controls**.
