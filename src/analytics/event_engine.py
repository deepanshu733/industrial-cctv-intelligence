class EventEngine:

    def __init__(self):
        self.events = []
        self.vehicle_states = {}


    # 1. Check whether vehicle state has changed

    def check_event(
        self,
        track_id,
        class_name,
        direction,
        status
    ):

        current_state = {
            "direction": direction,
            "status": status
        }


        # First time seeing this vehicle

        if track_id not in self.vehicle_states:

            self.vehicle_states[track_id] = current_state

            return None


        previous_state = self.vehicle_states[track_id]


        # Check whether direction or status changed

        if (
            previous_state["direction"] != direction
            or previous_state["status"] != status
        ):

            event = {
                "vehicle_id": track_id,
                "vehicle_class": class_name,
                "previous_direction": previous_state["direction"],
                "direction": direction,
                "previous_status": previous_state["status"],
                "status": status
            }


            self.events.append(event)

            self.vehicle_states[track_id] = current_state

            return event


        # No meaningful change

        return None


    # 2. Get all events

    def get_events(self):

        return self.events


    # 3. Clear all events

    def clear_events(self):

        self.events.clear()