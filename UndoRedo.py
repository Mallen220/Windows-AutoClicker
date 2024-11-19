import Constants
import ScreenOverlay

# Undo the last action
def undo():
    if Constants.undo_stack:
        action = Constants.undo_stack.pop()
        action_type, event = action

        if action_type == "create":
            if event in Constants.embedded_events:
                index = Constants.embedded_events.index(event)
                Constants.embedded_events.pop(index)
                print(f"Undid creation of event at position: {event['position']}")
                add_to_redo_stack(("create", event))

        elif action_type == "delete":
            Constants.embedded_events.append(event)
            Constants.embedded_events.sort(key=lambda e: e.get("position", (0, 0)))
            print(f"Undid deletion of event at position: {event['position']}")
            add_to_redo_stack(("create", event))

        ScreenOverlay.update_event_overlays()
    else:
        print("No actions to undo.")

def add_to_undo_stack(action):
    Constants.undo_stack.append(action)
    if len(Constants.undo_stack) > Constants.max_undo_redo:
        Constants.undo_stack.pop(0)

# Redo the last undone action
def redo():
    if Constants.redo_stack:

        action = Constants.redo_stack.pop()
        action_type, event = action

        if action_type == "create":
            Constants.embedded_events.append(event)
            Constants.embedded_events.sort(key=lambda e: e.get("position", (0, 0)))
            print(f"Redid creation of event at position: {event['position']}")
            add_to_undo_stack(("create", event))

        elif action_type == "delete":
            if event in Constants.embedded_events:
                index = Constants.embedded_events.index(event)
                Constants.embedded_events.pop(index)
                print(f"Redid deletion of event at position: {event['position']}")
                add_to_undo_stack(("delete", event))
    else:
        print("No actions to redo.")
    ScreenOverlay.update_event_overlays()


def add_to_redo_stack(action):
    Constants.redo_stack.append(action)
    if len(Constants.redo_stack) > Constants.max_undo_redo:
        Constants.redo_stack.pop(0)