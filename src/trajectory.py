class TrajectoryManager:

    def __init__(self, max_points=50):

        self.trajectories = {}
        self.max_points = max_points


    # Update vehicle trajectory

    def update(self, track_id, center):

        if track_id not in self.trajectories:
            self.trajectories[track_id] = []

        self.trajectories[track_id].append(center)

        self.trajectories[track_id] = (
            self.trajectories[track_id][-self.max_points:]
        )


    # Calculate movement

    def get_movement(self, track_id):

        trajectory = self.trajectories.get(track_id, [])

        if len(trajectory) < 2:
            return 0, 0

        previous_x, previous_y = trajectory[-2]
        current_x, current_y = trajectory[-1]

        dx = current_x - previous_x
        dy = current_y - previous_y

        return dx, dy


    # Calculate stable direction

    def get_direction(self, track_id, points=10, threshold=5):

        trajectory = self.trajectories.get(track_id, [])

        if len(trajectory) < points:
            return "UNKNOWN"

        previous_x, previous_y = trajectory[-points]
        current_x, current_y = trajectory[-1]

        dx = current_x - previous_x
        dy = current_y - previous_y

        if abs(dx) < threshold and abs(dy) < threshold:
            return "STATIONARY"

        if abs(dx) > abs(dy):

            if dx > 0:
                return "RIGHT"

            else:
                return "LEFT"

        else:

            if dy > 0:
                return "DOWN"

            else:
                return "UP"


    # Detect whether vehicle has stopped

    def is_stopped(self, track_id, points=10, threshold=5):

        trajectory = self.trajectories.get(track_id, [])

        if len(trajectory) < points:
            return False

        previous_x, previous_y = trajectory[-points]
        current_x, current_y = trajectory[-1]

        dx = abs(current_x - previous_x)
        dy = abs(current_y - previous_y)

        if dx < threshold and dy < threshold:
            return True

        return False


    # Calculate pixel-based speed

    def get_speed(self, track_id, fps, points=10):

        trajectory = self.trajectories.get(track_id, [])

        if len(trajectory) < points:
            return 0.0

        previous_x, previous_y = trajectory[-points]
        current_x, current_y = trajectory[-1]

        dx = current_x - previous_x
        dy = current_y - previous_y

        distance_pixels = (
            (dx ** 2) +
            (dy ** 2)
        ) ** 0.5

        time_seconds = (
            points - 1
        ) / fps

        if time_seconds <= 0:
            return 0.0

        speed = (
            distance_pixels /
            time_seconds
        )

        return speed


    # Convert pixel speed to approximate km/h

    def get_speed_kmh(
        self,
        track_id,
        fps,
        meter_per_pixel,
        points=10
    ):

        pixel_speed = self.get_speed(
            track_id,
            fps,
            points
        )

        meters_per_second = (
            pixel_speed *
            meter_per_pixel
        )

        speed_kmh = (
            meters_per_second *
            3.6
        )

        return speed_kmh


    # Get complete trajectory

    def get_trajectory(self, track_id):

        return self.trajectories.get(track_id, [])