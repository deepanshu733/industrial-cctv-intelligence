from ultralytics import YOLO

import cv2
import math
from collections import defaultdict, deque

from trajectory import TrajectoryManager
from analytics.event_engine import EventEngine
from analytics.zone_manager import ZoneManager


# ============================================================
# 1. LOAD YOLO MODEL
# ============================================================

model = YOLO("yolo11n.pt")


# ============================================================
# 2. VIDEO PATH
# ============================================================

video_path = "../videos/traffic.mov"

cap = cv2.VideoCapture(video_path)


if not cap.isOpened():

    print("ERROR: Could not open video.")

    exit()


# ============================================================
# 3. GET VIDEO FPS
# ============================================================

fps = cap.get(cv2.CAP_PROP_FPS)


if fps <= 0:

    fps = 30.0


print("Video FPS:", fps)


# ============================================================
# 4. INITIALIZE TRAJECTORY MANAGER
# ============================================================

trajectory_manager = TrajectoryManager(
    max_points=50
)


# ============================================================
# 5. INITIALIZE EVENT ENGINE
# ============================================================

event_engine = EventEngine()


# ============================================================
# 6. INITIALIZE ZONE MANAGER
# ============================================================

zone_manager = ZoneManager()


# ============================================================
# 7. SPEED SETTINGS
# ============================================================

# Temporary scene scale.
#
# This converts pixel movement into an approximate
# real-world distance.
#
# It must be calibrated later for accurate absolute speed.

meter_per_pixel = 0.05


# Number of frames used for speed calculation.

speed_points = 10


# ============================================================
# 8. SPEED SMOOTHING
# ============================================================

# Store recent speed values for every vehicle.

speed_history = defaultdict(
    lambda: deque(
        maxlen=8
    )
)


# ============================================================
# 9. VEHICLE HISTORY
# ============================================================

vehicle_history = {}


# ============================================================
# 10. VEHICLE CLASSES
# ============================================================

vehicle_classes = [
    "car",
    "motorcycle",
    "bus",
    "truck"
]


# ============================================================
# 11. FRAME COUNTER
# ============================================================

frame_count = 0


# ============================================================
# 12. MAIN VIDEO LOOP
# ============================================================

while True:

    ret, frame = cap.read()


    if not ret:

        break


    frame_count += 1


    # ========================================================
    # 13. YOLO TRACKING
    # ========================================================

    results = model.track(

        frame,

        imgsz=640,

        conf=0.20,

        classes=[2, 3, 5, 7],

        persist=True,

        tracker="botsort.yaml",

        verbose=False
    )


    boxes = results[0].boxes


    # ========================================================
    # 14. PROCESS TRACKED VEHICLES
    # ========================================================

    if boxes.id is not None:

        track_ids = (
            boxes.id
            .int()
            .cpu()
            .tolist()
        )


        class_ids = (
            boxes.cls
            .int()
            .cpu()
            .tolist()
        )


        coordinates = (
            boxes.xyxy
            .cpu()
            .tolist()
        )


        # ====================================================
        # 15. PROCESS EACH VEHICLE
        # ====================================================

        for track_id, class_id, box in zip(
            track_ids,
            class_ids,
            coordinates
        ):


            # =================================================
            # 16. DETERMINE CLASS
            # =================================================

            if class_id == 2:

                class_name = "car"

            elif class_id == 3:

                class_name = "motorcycle"

            elif class_id == 5:

                class_name = "bus"

            elif class_id == 7:

                class_name = "truck"

            else:

                continue


            # =================================================
            # 17. NEW VEHICLE
            # =================================================

            if track_id not in vehicle_history:

                vehicle_history[
                    track_id
                ] = class_name


                print(
                    f"NEW VEHICLE | "
                    f"Vehicle ID: {track_id} | "
                    f"Class: {class_name}"
                )


            # =================================================
            # 18. GET BOUNDING BOX
            # =================================================

            x1, y1, x2, y2 = map(
                int,
                box
            )


            # =================================================
            # 19. CALCULATE VEHICLE CENTER
            # =================================================

            center_x = int(
                (x1 + x2) / 2
            )


            center_y = int(
                (y1 + y2) / 2
            )


            center = (
                center_x,
                center_y
            )


            # =================================================
            # 20. UPDATE TRAJECTORY
            # =================================================

            trajectory_manager.update(
                track_id,
                center
            )


            # =================================================
            # 21. GET TRAJECTORY
            # =================================================

            trajectory = (
                trajectory_manager
                .get_trajectory(track_id)
            )


            # =================================================
            # 22. CALCULATE RELATIVE SPEED
            # =================================================

            speed_kmh = 0.0


            if len(trajectory) >= speed_points:


                # =============================================
                # Get older point
                # =============================================

                old_x, old_y = (
                    trajectory[-speed_points]
                )


                # =============================================
                # Get current point
                # =============================================

                new_x, new_y = (
                    trajectory[-1]
                )


                # =============================================
                # Pixel displacement
                # =============================================

                dx = (
                    new_x -
                    old_x
                )


                dy = (
                    new_y -
                    old_y
                )


                # =============================================
                # Pixel distance
                # =============================================

                pixel_distance = math.sqrt(

                    (
                        dx ** 2
                    )
                    +
                    (
                        dy ** 2
                    )

                )


                # =============================================
                # Time difference
                # =============================================

                time_seconds = (
                    speed_points - 1
                ) / fps


                if time_seconds > 0:


                    # =========================================
                    # Pixel speed
                    # =========================================

                    pixel_speed = (
                        pixel_distance /
                        time_seconds
                    )


                    # =========================================
                    # Convert to meters/second
                    # =========================================

                    meters_per_second = (
                        pixel_speed *
                        meter_per_pixel
                    )


                    # =========================================
                    # Convert to km/h
                    # =========================================

                    raw_speed_kmh = (
                        meters_per_second *
                        3.6
                    )


                    # =========================================
                    # Store speed
                    # =========================================

                    speed_history[
                        track_id
                    ].append(
                        raw_speed_kmh
                    )


                    # =========================================
                    # Smooth speed
                    # =========================================

                    if len(
                        speed_history[track_id]
                    ) > 0:

                        speed_kmh = (
                            sum(
                                speed_history[
                                    track_id
                                ]
                            )
                            /
                            len(
                                speed_history[
                                    track_id
                                ]
                            )
                        )


            # =================================================
            # 23. GET DIRECTION
            # =================================================

            direction = (
                trajectory_manager
                .get_direction(
                    track_id,
                    points=10,
                    threshold=5
                )
            )


            # =================================================
            # 24. CHECK STOPPED
            # =================================================

            stopped = (
                trajectory_manager
                .is_stopped(
                    track_id,
                    points=10,
                    threshold=5
                )
            )


            if stopped:

                status = "STOPPED"

                # Force speed close to zero
                # when vehicle is stationary.

                speed_kmh = 0.0

            else:

                status = "MOVING"


            # =================================================
            # 25. ZONE CHECK
            # =================================================

            zone_event = (
                zone_manager
                .check_zone_change(
                    track_id,
                    center
                )
            )


            current_zone = (
                zone_manager
                .get_zone(
                    center
                )
            )


            # =================================================
            # 26. EVENT ENGINE
            # =================================================

            event_engine.check_event(

                track_id,

                class_name,

                direction,

                status
            )


            # =================================================
            # 27. DRAW BOUNDING BOX
            # =================================================

            cv2.rectangle(

                frame,

                (x1, y1),

                (x2, y2),

                (0, 255, 0),

                2
            )


            # =================================================
            # 28. DRAW CENTER POINT
            # =================================================

            cv2.circle(

                frame,

                center,

                4,

                (0, 0, 255),

                -1
            )


            # =================================================
            # 29. DRAW TRAJECTORY
            # =================================================

            for i in range(
                1,
                len(trajectory)
            ):

                cv2.line(

                    frame,

                    trajectory[i - 1],

                    trajectory[i],

                    (255, 0, 0),

                    2
                )


            # =================================================
            # 30. VEHICLE LABEL
            # =================================================

            vehicle_label = (

                f"ID: {track_id} | "
                f"{class_name}"

            )


            cv2.putText(

                frame,

                vehicle_label,

                (x1, y1 - 40),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.5,

                (0, 255, 0),

                2
            )


            # =================================================
            # 31. SPEED LABEL
            # =================================================

            speed_label = (

                f"Relative Speed: "
                f"{speed_kmh:.1f} km/h"

            )


            cv2.putText(

                frame,

                speed_label,

                (x1, y1 - 20),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.5,

                (0, 255, 255),

                2
            )


            # =================================================
            # 32. DIRECTION + STATUS
            # =================================================

            direction_label = (

                f"{direction} | "
                f"{status}"

            )


            cv2.putText(

                frame,

                direction_label,

                (x1, y2 + 20),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.5,

                (255, 255, 255),

                2
            )


    # ========================================================
    # 33. VEHICLE COUNTS
    # ========================================================

    total_vehicles = len(
        vehicle_history
    )


    car_count = 0

    motorcycle_count = 0

    bus_count = 0

    truck_count = 0


    for vehicle_class in (
        vehicle_history.values()
    ):

        if vehicle_class == "car":

            car_count += 1

        elif vehicle_class == "motorcycle":

            motorcycle_count += 1

        elif vehicle_class == "bus":

            bus_count += 1

        elif vehicle_class == "truck":

            truck_count += 1


    # ========================================================
    # 34. DISPLAY TOTAL VEHICLES
    # ========================================================

    cv2.putText(

        frame,

        f"Total Vehicles: {total_vehicles}",

        (20, 30),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.7,

        (255, 255, 255),

        2
    )


    # ========================================================
    # 35. DISPLAY CAR COUNT
    # ========================================================

    cv2.putText(

        frame,

        f"Cars: {car_count}",

        (20, 60),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )


    # ========================================================
    # 36. DISPLAY MOTORCYCLE COUNT
    # ========================================================

    cv2.putText(

        frame,

        f"Motorcycles: {motorcycle_count}",

        (20, 90),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )


    # ========================================================
    # 37. DISPLAY BUS COUNT
    # ========================================================

    cv2.putText(

        frame,

        f"Buses: {bus_count}",

        (20, 120),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )


    # ========================================================
    # 38. DISPLAY TRUCK COUNT
    # ========================================================

    cv2.putText(

        frame,

        f"Trucks: {truck_count}",

        (20, 150),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.6,

        (255, 255, 255),

        2
    )


    # ========================================================
    # 39. DISPLAY FRAME
    # ========================================================

    cv2.imshow(

        "Industrial CCTV Intelligence System",

        frame
    )


    # ========================================================
    # 40. EXIT
    # ========================================================

    key = cv2.waitKey(1) & 0xFF


    if key == ord("q"):

        break


# ============================================================
# 41. RELEASE RESOURCES
# ============================================================

cap.release()

cv2.destroyAllWindows()