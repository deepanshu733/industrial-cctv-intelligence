# Industrial CCTV Vehicle Intelligence

An end-to-end computer vision system for detecting, tracking, and analyzing vehicles in CCTV-style traffic footage.

The project combines a custom fine-tuned YOLO11s detector with BoT-SORT tracking, trajectory analysis, direction estimation, event detection, PostgreSQL storage, a FastAPI backend, and a Streamlit dashboard.

## Features

* Custom vehicle detection using a fine-tuned YOLO11s model
* Car and truck detection
* Multi-object tracking with BoT-SORT
* Persistent vehicle IDs across frames
* Vehicle trajectory tracking
* Movement direction estimation: LEFT, RIGHT, UP, DOWN
* MOVING / STOPPED state detection
* Event generation for state and direction changes
* PostgreSQL database for storing vehicle and event information
* FastAPI REST API for database access
* Streamlit dashboard for analytics and vehicle search
* Demo video with tracking IDs, trajectories, directions, and events

## System Architecture

```text
                    CCTV Video
                        │
                        ▼
                Custom YOLO11s
                  Detection
                        │
                        ▼
                  BoT-SORT
                    Tracking
                        │
                        ▼
              Vehicle IDs + Boxes
                        │
                        ▼
                  Trajectory
                    Analysis
                        │
                        ▼
             Direction / State
             MOVING / STOPPED
                        │
                        ▼
                   EventEngine
                        │
                        ▼
                     CSV
                        │
                        ▼
                  PostgreSQL
                        │
                        ▼
                    FastAPI
                        │
                        ▼
                  Streamlit
                   Dashboard
```

## Project Structure

```text
industrial-cctv-intelligence/
│
├── backend/
│   ├── main.py
│   ├── .env
│   └── requirements.txt
│
├── dashboard/
│   └── app.py
│
├── models/
│   └── best.pt
│
├── src/
│   └── ...
│
├── videos/
│   └── traffic.mov
│
├── data/
│   ├── traffic_events.csv
│   └── traffic_vehicle_summary.csv
│
├── output/
│   └── traffic_demo_full_h264.mp4
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Model Training

The detector was created by fine-tuning a pretrained YOLO11s model on a custom annotated industrial CCTV dataset.

### Dataset

The original CVAT annotations contained:

* 102 annotated frames
* 428 total bounding boxes
* 395 car annotations
* 33 truck annotations
* 0 motorcycle annotations
* 0 bus annotations

Because consecutive video frames are highly correlated, a temporal split was used instead of a random image split.

### Final dataset split

```text
Training images:   71
Validation images: 21
Temporal gap:      10
```

The final training dataset used two classes:

```text
0 = car
1 = truck
```

### Training configuration

```text
Model:       YOLO11s
Pretrained:  Yes
Epochs:      50
Image size:  960
Batch size:  8
Optimizer:   AdamW
GPU:         NVIDIA Tesla T4
```

The model was fine-tuned from pretrained YOLO11s weights rather than trained from scratch because the custom dataset was relatively small.

## Validation Results

The best trained model achieved the following validation results:

### Car

```text
Precision:    0.855
Recall:       0.936
mAP@50:       0.966
mAP@50-95:    0.862
```

### Truck

```text
Precision:    1.000
Recall:       0.000
mAP@50:       0.000
mAP@50-95:    0.000
```

The truck class had only 33 annotated instances in the complete dataset, so its validation performance is not reliable and additional truck data would be needed for a stronger model.

The overall metrics should not be interpreted as a single "accuracy" score because the model performs very differently across the two classes.

## Tracking

BoT-SORT was selected for multi-object vehicle tracking.

The tracking pipeline maintains:

```text
Vehicle ID
Bounding Box
Center Point
Trajectory History
Movement State
Direction
```

The tracking system was tested on a separate CCTV video (`cctv_fixed.mp4`) as an unseen-video test.

The detector generalized to that footage and detected multiple cars and trucks, although track fragmentation and occasional ID switches remained.

## Trajectory and Direction

For each tracked vehicle, the system stores recent center points:

```text
(x1, y1)
(x2, y2)
(x3, y3)
...
```

The displacement of these points is used to estimate movement direction.

Possible directions are:

```text
LEFT
RIGHT
UP
DOWN
```

The system also estimates a movement state:

```text
MOVING
STOPPED
```

Direction changes are debounced so that short trajectory fluctuations do not immediately create a new direction event.

## EventEngine

The EventEngine generates events from vehicle behavior.

Example:

```text
Vehicle 3 → MOVING
Vehicle 3 → RIGHT
Vehicle 3 → STOPPED
```

Events are stored with frame and timestamp information.

Example event structure:

```text
frame
timestamp_seconds
vehicle_id
class
event_type
event_value
```

## PostgreSQL Database

The project uses PostgreSQL with two main tables.

### vehicles

```text
vehicle_id
class
first_frame
last_frame
frames_visible
first_seen_seconds
last_seen_seconds
final_state
final_direction
```

### events

```text
event_id
frame
timestamp_seconds
vehicle_id
class
event_type
event_value
```

The tables are connected using:

```text
events.vehicle_id
        ↓
vehicles.vehicle_id
```

## FastAPI Backend

The FastAPI backend exposes PostgreSQL data through REST endpoints.

### Available endpoints

```text
GET /
GET /health
GET /vehicles
GET /vehicles/{vehicle_id}
GET /events
GET /analytics
```

### Example

```text
GET /analytics
```

returns high-level information such as:

```text
Total vehicles
Cars
Trucks
Total events
Moving vehicles
Stopped vehicles
Direction statistics
```

Swagger documentation is available through:

```text
http://127.0.0.1:8000/docs
```

## Streamlit Dashboard

The Streamlit dashboard connects to the FastAPI backend and displays:

* Project demo video
* Total vehicles
* Cars
* Trucks
* Total events
* Moving vehicles
* Stopped vehicles
* Direction summary
* Tracked vehicle table
* Vehicle search
* Vehicle-specific event history
* Complete event log

Dashboard:

```text
http://localhost:8501
```

## Demo Video

The final demo uses `traffic.mov` and displays:

```text
Vehicle bounding boxes
Vehicle IDs
Trajectories
Direction
Movement state
Recent events
```

The demo video is a presentation artifact for showing the system visually.

## Technologies Used

```text
Python
YOLO11s
Ultralytics
OpenCV
BoT-SORT
NumPy
Pandas
PostgreSQL
FastAPI
Psycopg
Streamlit
Git / GitHub
```

## Installation

Create and activate a virtual environment:

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Environment Variables

Create `backend/.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=industrial_cctv
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD
```

Do not commit `.env` to GitHub.

## Running the Backend

From the `backend` folder:

```bash
uvicorn main:app --reload
```

Backend:

```text
http://127.0.0.1:8000
```

## Running the Dashboard

From the project root:

```bash
streamlit run dashboard/app.py
```

Dashboard:

```text
http://localhost:8501
```

Both FastAPI and Streamlit should be running at the same time.

## Limitations

This project is a working prototype rather than a production surveillance system.

### Limited training data

The custom dataset contains only 102 annotated frames, with relatively few truck examples.

### Tracking fragmentation

Some vehicles can receive new IDs after temporary detection loss or difficult tracking conditions.

Therefore:

```text
130 track IDs
```

does not necessarily mean 130 unique physical vehicles.

### Vehicle class coverage

The custom model was trained on:

```text
car
truck
```

It was not trained to reliably distinguish buses or motorcycles.

### Direction estimation

Direction is estimated from image-plane movement and should not be interpreted as real-world compass direction.

### Speed

Real-world speed calibration was intentionally not included in the current version.

### Camera conditions

Performance can change significantly with:

* camera angle
* object size
* occlusion
* lighting
* image quality
* camera movement

## Future Improvements

Possible future improvements include:

* More annotated CCTV footage
* More truck examples
* Additional vehicle classes
* Stronger re-identification
* Better handling of occlusion
* Camera calibration
* Real-world speed estimation
* More robust event logic
* Production database optimization
* Authentication for the API
* Cloud deployment
* Real-time CCTV streaming

## Key Learning Outcomes

This project demonstrates an end-to-end AI/ML workflow:

```text
Data Annotation
      ↓
Dataset Validation
      ↓
Temporal Train/Validation Split
      ↓
Transfer Learning
      ↓
Model Fine-Tuning
      ↓
Evaluation
      ↓
Object Tracking
      ↓
Trajectory Analysis
      ↓
Event Detection
      ↓
PostgreSQL
      ↓
FastAPI
      ↓
Streamlit Dashboard
```

The project therefore combines computer vision, machine learning, backend development, SQL, and dashboard development in a single application.

## Project Summary

**Industrial CCTV Vehicle Intelligence** is an end-to-end vehicle analytics system that fine-tunes YOLO11s for custom car and truck detection, tracks vehicles with BoT-SORT, analyzes their trajectories and movement direction, generates behavioral events, stores results in PostgreSQL, exposes them through FastAPI, and visualizes the data in a Streamlit dashboard.

---

### Author

**Deepanshu Bhardwaj**

GitHub: `https://github.com/deepanshu733`

LinkedIn: `https://www.linkedin.com/in/deepanshu-bhardwaj-15a6a92b`
