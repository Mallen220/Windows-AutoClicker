#####################################################
# Undo / Redo #TODO: Please note that this code is deprecated and will be removed in the future. It is not currently or actively maintained or supported.
#####################################################

undo_stack = []
redo_stack = []
max_undo_redo = 200  # Limit to the number of undo/redo actions

# Undo the last action
def undo():
    if undo_stack:
        action = undo_stack.pop()
        action_type, event = action

        if action_type == "create":
            if event in embedded_events:
                index = embedded_events.index(event)
                embedded_events.pop(index)
                print(f"Undid creation of event at position: {event['position']}")
                add_to_redo_stack(("create", event))

        elif action_type == "delete":
            embedded_events.append(event)
            embedded_events.sort(key=lambda e: e.get("position", (0, 0)))
            print(f"Undid deletion of event at position: {event['position']}")
            add_to_redo_stack(("create", event))

        update_event_overlays()
    else:
        print("No actions to undo.")


# Redo the last undone action
def redo():
    if redo_stack:
        print(redo_stack)

        action = redo_stack.pop()
        action_type, event = action

        if action_type == "create":
            embedded_events.append(event)
            embedded_events.sort(key=lambda e: e.get("position", (0, 0)))
            print(f"Redid creation of event at position: {event['position']}")
            add_to_undo_stack(("create", event))

        elif action_type == "delete":
            if event in embedded_events:
                index = embedded_events.index(event)
                embedded_events.pop(index)
                print(f"Redid deletion of event at position: {event['position']}")
                add_to_undo_stack(("delete", event))
    else:
        print("No actions to redo.")
    update_event_overlays()


def add_to_undo_stack(action):
    undo_stack.append(action)
    if len(undo_stack) > max_undo_redo:
        undo_stack.pop(0)


def add_to_redo_stack(action):
    redo_stack.append(action)
    if len(redo_stack) > max_undo_redo:
        redo_stack.pop(0)


root.bind("<Control-z>", lambda event: undo())
root.bind("<Control-Z>", lambda event: undo())
root.bind("<Control-Shift-Z>", lambda event: redo())