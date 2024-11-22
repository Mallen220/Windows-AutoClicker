import os
import sys
import random
from tkinter import END, filedialog, Listbox, simpledialog, SINGLE, Toplevel

max_undo_redo = 25  # Final
min_random_time = 50  # Final
max_random_time = 4000  # Final
presets_dir = "Presets"  # Final
current_os = os.name  # Final
undo_stack = []
redo_stack = []
overlay_windows = []
is_running = False
always_on_top = False
is_text_mode = False
delay_between_rounds = 500
embedded_events = []
special_keys = {
    "t": "t",
    "r": "r",
    "accept": "accept",
    "add": "add",
    "alt": "alt",
    "altleft": "altleft",
    "altright": "altright",
    "apps": "apps",
    "backspace": "backspace",
    "browserback": "browserback",
    "browserfavorites": "browserfavorites",
    "browserforward": "browserforward",
    "browserhome": "browserhome",
    "browserrefresh": "browserrefresh",
    "browsersearch": "browsersearch",
    "browserstop": "browserstop",
    "capslock": "capslock",
    "clear": "clear",
    "convert": "convert",
    "ctrl": "ctrl",
    "ctrlleft": "ctrlleft",
    "ctrlright": "ctrlright",
    "decimal": "decimal",
    "del": "del",
    "delete": "delete",
    "divide": "divide",
    "down": "down",
    "end": "end",
    "enter": "enter",
    "esc": "esc",
    "escape": "escape",
    "execute": "execute",
    "f1": "f1",
    "f10": "f10",
    "f11": "f11",
    "f12": "f12",
    "f13": "f13",
    "f14": "f14",
    "f15": "f15",
    "f16": "f16",
    "f17": "f17",
    "f18": "f18",
    "f19": "f19",
    "f2": "f2",
    "f20": "f20",
    "f21": "f21",
    "f22": "f22",
    "f23": "f23",
    "f24": "f24",
    "f3": "f3",
    "f4": "f4",
    "f5": "f5",
    "f6": "f6",
    "f7": "f7",
    "f8": "f8",
    "f9": "f9",
    "final": "final",
    "fn": "fn",
    "hanguel": "hanguel",
    "hangul": "hangul",
    "hanja": "hanja",
    "help": "help",
    "home": "home",
    "insert": "insert",
    "junja": "junja",
    "kana": "kana",
    "kanji": "kanji",
    "launchapp1": "launchapp1",
    "launchapp2": "launchapp2",
    "launchmail": "launchmail",
    "launchmediaselect": "launchmediaselect",
    "left": "left",
    "modechange": "modechange",
    "multiply": "multiply",
    "nexttrack": "nexttrack",
    "nonconvert": "nonconvert",
    "num0": "num0",
    "num1": "num1",
    "num2": "num2",
    "num3": "num3",
    "num4": "num4",
    "num5": "num5",
    "num6": "num6",
    "num7": "num7",
    "num8": "num8",
    "num9": "num9",
    "numlock": "numlock",
    "pagedown": "pagedown",
    "pageup": "pageup",
    "pause": "pause",
    "pgdn": "pgdn",
    "pgup": "pgup",
    "playpause": "playpause",
    "prevtrack": "prevtrack",
    "print": "print",
    "printscreen": "printscreen",
    "prntscrn": "prntscrn",
    "prtsc": "prtsc",
    "prtscr": "prtscr",
    "return": "return",
    "right": "right",
    "scrolllock": "scrolllock",
    "select": "select",
    "separator": "separator",
    "shift": "shift",
    "shiftleft": "shiftleft",
    "shiftright": "shiftright",
    "sleep": "sleep",
    "space": "space",
    "stop": "stop",
    "subtract": "subtract",
    "tab": "tab",
    "up": "up",
    "volumedown": "volumedown",
    "volumemute": "volumemute",
    "volumeup": "volumeup",
    "win": "win",
    "winleft": "winleft",
    "winright": "winright",
    "yen": "yen",
    "command": "command",
    "option": "option",
    "optionleft": "optionleft",
    "optionright": "optionright",
}




def is_windows_os():
    if current_os == "nt":
        return True

    return False

def icon_per_os(window):
    if is_windows_os():
        if getattr(sys, "frozen", False):
            program_icon = os.path.join(sys._MEIPASS, "AutoClicker.ico")
        else:
            program_icon = "AutoClicker.ico"
        window.iconbitmap(program_icon)
    else:
        print("No Linux Icon!")

def random_time_in_range(min_time=None, max_time=None):
    if min_time is None:
        min_time = min_random_time
    if max_time is None:
        max_time = max_random_time

    return random.randint(min_time, max_time) / 1000