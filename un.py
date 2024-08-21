import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
import pyautogui
import pyperclip
import time
import keyboard

# Import the functions to test from the main module
from main import (
    create_event, stop_text_input, delete_newest_event, update_event_overlays,
    toggle_always_on_top, create_event_overlay, open_text_input, save_text,
    rearrange_events, start_program, type_text, stop_program, monitor_space_key,
    close_and_save, create_overlay, events, timing_data, is_running, always_on_top, overlay_active,
    is_text_mode, preset_file
)


class TestEventController(unittest.TestCase):

    def setUp(self):
        """Set up the environment for testing"""
        # This function will run before every test
        self.root = tk.Tk()  # Create a Tkinter root window
        self.overlay = create_overlay()  # Create overlay window

    def tearDown(self):
        """Clean up after each test"""
        self.root.destroy()
        self.overlay.destroy()

    @patch('keyboard.is_pressed')
    @patch('pyautogui.position', return_value=(100, 200))
    def test_create_event(self, mock_position, mock_is_pressed):
        mock_is_pressed.return_value = False  # Simulate not pressing 'ctrl'
        create_event()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0], (100, 200))
        self.assertEqual(timing_data[0], 100)

    @patch('tkinter.Toplevel')
    def test_stop_text_input(self, mock_toplevel):
        global input_window
        input_window = MagicMock()
        stop_text_input()
        input_window.destroy.assert_called_once()

    def test_delete_newest_event(self):
        events.append((100, 200))
        timing_data.append(100)
        delete_newest_event()
        self.assertEqual(len(events), 0)
        self.assertEqual(len(timing_data), 0)

    def test_toggle_always_on_top(self):
        global always_on_top
        toggle_always_on_top()
        self.assertTrue(always_on_top)
        toggle_always_on_top()
        self.assertFalse(always_on_top)

    @patch('pyautogui.click')
    @patch('time.sleep', return_value=None)  # Mock sleep to speed up tests
    def test_start_program(self, mock_sleep, mock_click):
        global is_running
        start_program()
        self.assertTrue(is_running)
        # Simulate stopping the program
        stop_program()
        self.assertFalse(is_running)

    @patch('pyautogui.press')
    @patch('time.sleep', return_value=None)
    def test_type_text(self, mock_sleep, mock_press):
        type_text('hello world', 0.1)
        expected_calls = [
            unittest.mock.call('h'),
            unittest.mock.call('e'),
            unittest.mock.call('l'),
            unittest.mock.call('l'),
            unittest.mock.call('o'),
            unittest.mock.call('space'),
            unittest.mock.call('w'),
            unittest.mock.call('o'),
            unittest.mock.call('r'),
            unittest.mock.call('l'),
            unittest.mock.call('d')
        ]
        mock_press.assert_has_calls(expected_calls)

    @patch('pyautogui.hotkey')
    @patch('pyperclip.copy')
    def test_type_text_with_clipboard(self, mock_copy, mock_hotkey):
        global timing_data
        events.append('sample text')
        timing_data.append(0)
        type_text('sample text', 0)
        mock_copy.assert_called_with('sample text')
        mock_hotkey.assert_called_with('ctrl', 'v')

    @patch('keyboard.is_pressed', return_value=False)
    @patch('time.sleep', return_value=None)
    def test_monitor_space_key(self, mock_sleep, mock_is_pressed):
        monitor_space_key()
        # Simulate pressing the space key
        mock_is_pressed.return_value = True
        stop_program()
        self.assertFalse(is_running)

    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    def test_close_and_save(self, mock_open):
        events.append((100, 200))
        timing_data.append(100)
        close_and_save()
        mock_open.assert_called_once_with("events.txt", "w")
        handle = mock_open()
        handle.write.assert_called_once_with("(100, 200)\n")

if __name__ == '__main__':
    unittest.main()
