from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
import psycopg
import os


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# DATABASE SETTINGS
# =========================================================

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "industrial_cctv")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# =========================================================
# FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Industrial CCTV Vehicle Intelligence API",
    description="API for vehicle detection, tracking and event analytics",
    version="1.0.0"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    if not DB_PASSWORD:
        raise RuntimeError(
            "DB_PASSWORD is missing from backend/.env"
        )

    try:

        connection = psycopg.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )

        return connection

    except Exception as e:

        raise RuntimeError(
            f"PostgreSQL connection failed: {e}"
        )


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Industrial CCTV Vehicle Intelligence API",
        "status": "running"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health_check():

    connection = None

    try:

        connection = get_connection()

        return {
            "status": "healthy",
            "database": "connected"
        }

    except Exception as e:

        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

    finally:

        if connection:
            connection.close()


# =========================================================
# GET ALL VEHICLES
# =========================================================

@app.get("/vehicles")
def get_vehicles():

    connection = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                vehicle_id,
                class,
                first_frame,
                last_frame,
                frames_visible,
                first_seen_seconds,
                last_seen_seconds,
                final_state,
                final_direction
            FROM vehicles
            ORDER BY vehicle_id;
            """
        )

        rows = cursor.fetchall()

        vehicles = []

        for row in rows:

            vehicles.append(
                {
                    "vehicle_id": row[0],
                    "class": row[1],
                    "first_frame": row[2],
                    "last_frame": row[3],
                    "frames_visible": row[4],
                    "first_seen_seconds": float(row[5]),
                    "last_seen_seconds": float(row[6]),
                    "final_state": row[7],
                    "final_direction": row[8]
                }
            )

        return {
            "total": len(vehicles),
            "vehicles": vehicles
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if connection:
            connection.close()


# =========================================================
# GET ONE VEHICLE
# =========================================================

@app.get("/vehicles/{vehicle_id}")
def get_vehicle(vehicle_id: int):

    connection = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                vehicle_id,
                class,
                first_frame,
                last_frame,
                frames_visible,
                first_seen_seconds,
                last_seen_seconds,
                final_state,
                final_direction
            FROM vehicles
            WHERE vehicle_id = %s;
            """,
            (vehicle_id,)
        )

        vehicle = cursor.fetchone()

        if vehicle is None:

            raise HTTPException(
                status_code=404,
                detail="Vehicle not found"
            )

        cursor.execute(
            """
            SELECT
                event_id,
                frame,
                timestamp_seconds,
                event_type,
                event_value
            FROM events
            WHERE vehicle_id = %s
            ORDER BY timestamp_seconds;
            """,
            (vehicle_id,)
        )

        event_rows = cursor.fetchall()

        events = []

        for row in event_rows:

            events.append(
                {
                    "event_id": row[0],
                    "frame": row[1],
                    "timestamp_seconds": float(row[2]),
                    "event_type": row[3],
                    "event_value": row[4]
                }
            )

        return {
            "vehicle": {
                "vehicle_id": vehicle[0],
                "class": vehicle[1],
                "first_frame": vehicle[2],
                "last_frame": vehicle[3],
                "frames_visible": vehicle[4],
                "first_seen_seconds": float(vehicle[5]),
                "last_seen_seconds": float(vehicle[6]),
                "final_state": vehicle[7],
                "final_direction": vehicle[8]
            },
            "events": events
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if connection:
            connection.close()


# =========================================================
# GET ALL EVENTS
# =========================================================

@app.get("/events")
def get_events():

    connection = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                event_id,
                frame,
                timestamp_seconds,
                vehicle_id,
                class,
                event_type,
                event_value
            FROM events
            ORDER BY timestamp_seconds;
            """
        )

        rows = cursor.fetchall()

        events = []

        for row in rows:

            events.append(
                {
                    "event_id": row[0],
                    "frame": row[1],
                    "timestamp_seconds": float(row[2]),
                    "vehicle_id": row[3],
                    "class": row[4],
                    "event_type": row[5],
                    "event_value": row[6]
                }
            )

        return {
            "total": len(events),
            "events": events
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if connection:
            connection.close()


# =========================================================
# ANALYTICS
# =========================================================

@app.get("/analytics")
def get_analytics():

    connection = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        # Total vehicles
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM vehicles;
            """
        )

        total_vehicles = cursor.fetchone()[0]

        # Cars
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM vehicles
            WHERE class = 'car';
            """
        )

        total_cars = cursor.fetchone()[0]

        # Trucks
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM vehicles
            WHERE class = 'truck';
            """
        )

        total_trucks = cursor.fetchone()[0]

        # Total events
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM events;
            """
        )

        total_events = cursor.fetchone()[0]

        # Moving vehicles
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM vehicles
            WHERE final_state = 'MOVING';
            """
        )

        moving_vehicles = cursor.fetchone()[0]

        # Stopped vehicles
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM vehicles
            WHERE final_state = 'STOPPED';
            """
        )

        stopped_vehicles = cursor.fetchone()[0]

        # Direction statistics
        cursor.execute(
            """
            SELECT
                final_direction,
                COUNT(*)
            FROM vehicles
            GROUP BY final_direction
            ORDER BY COUNT(*) DESC;
            """
        )

        direction_rows = cursor.fetchall()

        directions = {}

        for direction, count in direction_rows:

            directions[
                direction or "UNKNOWN"
            ] = count

        return {
            "total_vehicles": total_vehicles,
            "cars": total_cars,
            "trucks": total_trucks,
            "total_events": total_events,
            "moving_vehicles": moving_vehicles,
            "stopped_vehicles": stopped_vehicles,
            "directions": directions
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if connection:
            connection.close()