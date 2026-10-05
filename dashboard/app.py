import os
import requests
import pandas as pd
import streamlit as st


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Industrial CCTV Vehicle Intelligence",
    page_icon="🚗",
    layout="wide"
)


# =========================================================
# API CONFIGURATION
# =========================================================

API_URL = "http://127.0.0.1:8000"


# =========================================================
# PROJECT PATHS
# =========================================================

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

VIDEO_PATH = os.path.join(
    PROJECT_ROOT,
    "output",
    "traffic_demo_full_h264.mp4"
)


# =========================================================
# API HELPER
# =========================================================

def get_api_data(endpoint):
    """
    Fetch JSON data from FastAPI.
    """

    try:

        response = requests.get(
            f"{API_URL}{endpoint}",
            timeout=5
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:

        st.error(
            "Cannot connect to FastAPI. "
            "Make sure the backend is running."
        )

        return None

    except requests.exceptions.Timeout:

        st.error(
            "FastAPI request timed out."
        )

        return None

    except requests.exceptions.RequestException as e:

        st.error(
            f"API request failed: {e}"
        )

        return None


# =========================================================
# HEADER
# =========================================================

st.title(
    "🚗 Industrial CCTV Vehicle Intelligence"
)

st.caption(
    "YOLO11s + BoT-SORT + PostgreSQL + FastAPI + Streamlit"
)


# =========================================================
# DEMO VIDEO
# =========================================================

st.subheader(
    "🎥 Vehicle Intelligence Demo"
)


if os.path.exists(VIDEO_PATH):

    # Center the video inside the page
    video_col_left, video_col, video_col_right = st.columns(
        [1, 2, 1]
    )

    with video_col:

        st.video(
            VIDEO_PATH,
            width=1500
        )

else:

    st.error(
        "Demo video not found."
    )

    st.write(
        "Expected location:"
    )

    st.code(
        VIDEO_PATH
    )

    st.write(
        "Expected filename:"
    )

    st.code(
        "traffic_demo_full_h264.mp4"
    )


# =========================================================
# REFRESH BUTTON
# =========================================================

if st.button(
    "🔄 Refresh Dashboard"
):

    st.rerun()


# =========================================================
# HEALTH CHECK
# =========================================================

health = get_api_data(
    "/health"
)


if health is None:

    st.stop()


if health.get("status") == "healthy":

    st.success(
        "FastAPI connected • PostgreSQL connected"
    )

else:

    st.warning(
        "FastAPI is running, but PostgreSQL "
        "connection needs attention."
    )


# =========================================================
# ANALYTICS
# =========================================================

analytics = get_api_data(
    "/analytics"
)


if analytics is None:

    st.stop()


# =========================================================
# KPI VALUES
# =========================================================

total_vehicles = analytics.get(
    "total_vehicles",
    0
)

cars = analytics.get(
    "cars",
    0
)

trucks = analytics.get(
    "trucks",
    0
)

total_events = analytics.get(
    "total_events",
    0
)

moving = analytics.get(
    "moving_vehicles",
    0
)

stopped = analytics.get(
    "stopped_vehicles",
    0
)


# =========================================================
# VEHICLE ANALYTICS
# =========================================================

st.subheader(
    "📊 Vehicle Analytics"
)


col1, col2, col3, col4, col5, col6 = (
    st.columns(6)
)


with col1:

    st.metric(
        "Total Vehicles",
        total_vehicles
    )


with col2:

    st.metric(
        "Cars",
        cars
    )


with col3:

    st.metric(
        "Trucks",
        trucks
    )


with col4:

    st.metric(
        "Total Events",
        total_events
    )


with col5:

    st.metric(
        "Moving",
        moving
    )


with col6:

    st.metric(
        "Stopped",
        stopped
    )


# =========================================================
# DIRECTION SUMMARY
# =========================================================

st.subheader(
    "🧭 Direction Summary"
)


directions = analytics.get(
    "directions",
    {}
)


if directions:

    direction_df = pd.DataFrame(
        {
            "Direction": list(
                directions.keys()
            ),

            "Vehicles": list(
                directions.values()
            )
        }
    )


    chart_col, table_col = st.columns(
        [2, 1]
    )


    with chart_col:

        st.bar_chart(
            direction_df.set_index(
                "Direction"
            )
        )


    with table_col:

        st.dataframe(
            direction_df,

            use_container_width=True,

            hide_index=True
        )

else:

    st.info(
        "No direction data available."
    )


# =========================================================
# TRACKED VEHICLES
# =========================================================

st.subheader(
    "🚘 Tracked Vehicles"
)


vehicles_data = get_api_data(
    "/vehicles"
)


if vehicles_data is not None:

    vehicles = vehicles_data.get(
        "vehicles",
        []
    )


    if vehicles:

        vehicles_df = pd.DataFrame(
            vehicles
        )


        display_columns = [
            "vehicle_id",
            "class",
            "first_seen_seconds",
            "last_seen_seconds",
            "frames_visible",
            "final_state",
            "final_direction"
        ]


        available_columns = [
            column
            for column in display_columns
            if column in vehicles_df.columns
        ]


        st.dataframe(
            vehicles_df[
                available_columns
            ],

            use_container_width=True,

            hide_index=True
        )

    else:

        st.info(
            "No vehicle records found."
        )


# =========================================================
# VEHICLE SEARCH
# =========================================================

st.subheader(
    "🔎 Vehicle Details"
)


vehicle_id = st.number_input(
    "Vehicle ID",

    min_value=1,

    value=1,

    step=1
)


if st.button(
    "Search Vehicle"
):

    vehicle_data = get_api_data(
        f"/vehicles/{vehicle_id}"
    )


    if vehicle_data is not None:

        vehicle = vehicle_data.get(
            "vehicle"
        )

        events = vehicle_data.get(
            "events",
            []
        )


        if vehicle:

            detail_col1, detail_col2, detail_col3, detail_col4 = (
                st.columns(4)
            )


            with detail_col1:

                st.metric(
                    "Vehicle ID",
                    vehicle["vehicle_id"]
                )


            with detail_col2:

                st.metric(
                    "Class",
                    vehicle["class"]
                )


            with detail_col3:

                st.metric(
                    "State",
                    vehicle["final_state"]
                )


            with detail_col4:

                st.metric(
                    "Direction",
                    vehicle["final_direction"]
                )


            st.write(
                "### Vehicle Events"
            )


            if events:

                vehicle_events_df = pd.DataFrame(
                    events
                )


                st.dataframe(
                    vehicle_events_df,

                    use_container_width=True,

                    hide_index=True
                )

            else:

                st.info(
                    "No events found for this vehicle."
                )


        else:

            st.warning(
                f"Vehicle ID {vehicle_id} was not found."
            )


# =========================================================
# ALL EVENTS
# =========================================================

st.subheader(
    "⚡ Event Log"
)


events_data = get_api_data(
    "/events"
)


if events_data is not None:

    events = events_data.get(
        "events",
        []
    )


    if events:

        events_df = pd.DataFrame(
            events
        )


        event_columns = [
            "event_id",
            "timestamp_seconds",
            "vehicle_id",
            "class",
            "event_type",
            "event_value"
        ]


        available_event_columns = [
            column
            for column in event_columns
            if column in events_df.columns
        ]


        st.dataframe(
            events_df[
                available_event_columns
            ],

            use_container_width=True,

            hide_index=True
        )

    else:

        st.info(
            "No events found."
        )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Industrial CCTV Vehicle Intelligence | "
    "Custom YOLO11s | BoT-SORT | "
    "Trajectory | Direction | EventEngine | "
    "PostgreSQL | FastAPI | Streamlit"
)