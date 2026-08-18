"""
DASHBOARD — Tiger Intelligence System
"""

import streamlit as st
import sqlite3
import pandas as pd
import folium
from streamlit_folium import st_folium

# ---------- CONFIG ----------
DB_PATH = "tiger_database.db"
STATIONS_CSV = "stations.csv"
IMAGE_STATIONS_CSV = "image_stations.csv"
# -----------------------------

st.set_page_config(page_title="Tiger Intelligence System", layout="wide")


def load_data():
    conn = sqlite3.connect(DB_PATH)
    sightings = pd.read_sql_query("SELECT * FROM sightings", conn)
    conn.close()

    stations = pd.read_csv(STATIONS_CSV)
    image_stations = pd.read_csv(IMAGE_STATIONS_CSV)

    data = sightings.merge(image_stations, on="image", how="left")
    data = data.merge(stations, on="station_id", how="left")
    data = data.dropna(subset=["latitude", "longitude"])
    return data


st.title("🐅 Tiger Intelligence System")

data = load_data()

if data.empty:
    st.warning("No sighting data found. Run Module 1-4 first.")
else:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Sightings", len(data))
    col2.metric("Unique Tigers", data["tiger_id"].nunique())
    col3.metric("Stations Used", data["station_id"].nunique())

    st.divider()

    st.subheader("📍 Tiger Movement Map")

    center_lat = data["latitude"].mean()
    center_lon = data["longitude"].mean()
    tiger_map = folium.Map(location=[center_lat, center_lon], zoom_start=11)

    colors = ["red", "blue", "green", "purple", "orange"]
    tiger_ids = data["tiger_id"].unique()
    color_map = {tid: colors[i % len(colors)] for i, tid in enumerate(tiger_ids)}

    for tiger_id in tiger_ids:
        tdata = data[data["tiger_id"] == tiger_id].sort_values("date")
        points = list(zip(tdata["latitude"], tdata["longitude"]))

        for _, row in tdata.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['tiger_id']} | {row['image']} | {row['date']}",
                icon=folium.Icon(color=color_map[tiger_id])
            ).add_to(tiger_map)

        if len(points) > 1:
            folium.PolyLine(points, color=color_map[tiger_id], weight=3).add_to(tiger_map)

    st_folium(tiger_map, width=1200, height=500)

    st.divider()

    st.subheader("📋 Recent Sightings")
    st.dataframe(data[["tiger_id", "image", "confidence", "date", "station_id", "zone"]].sort_values("date", ascending=False))
    