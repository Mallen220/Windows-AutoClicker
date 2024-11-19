import Root
import tkinter as tk
import RuntimeFunctions
import EventFunctions
import Presets
import RearrangeEventsWindow



###Button Constants
always_on_top_button = tk.Button(Root.window, text="Always on Top: Off", command=Root.toggle_always_on_top)
close_button = tk.Button(Root.window, text="Close & Save", command=Root.close_and_save)
close_rearrange_events_button = tk.Button(RearrangeEventsWindow.rearrange_window, text="Close", command=RearrangeEventsWindow.rearrange_window.destroy)
create_button = tk.Button(Root.window, text="Create Event", command=EventFunctions.create_event)
delete_button = tk.Button(Root.window, text="Delete Newest Event", command=EventFunctions.delete_event)
rearrange_button = tk.Button(Root.window, text="Rearrange Events", command=print("not working now")) #RearrangeEventsWindow



