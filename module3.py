"""
MODULE 3 — Tiger Movement & Area Mapping
Tiger Intelligence System
"""

import sqlite3
import pandas as pd
import folium

# ---------- CONFIG ----------
DB_PATH = "tiger_database.db"
STATIONS_CSV = "stations.csv"
IMAGE_STATIONS_CSV = "image_stations.csv"
OUTPUT_MAP = "tiger_movement_map.html"
# -----------------------------


def load_sightings():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM sightings", conn)
    conn.close()
    return df


def load_stations():
    return pd.read_csv(STATIONS_CSV)


def load_image_stations():
    return pd.read_csv(IMAGE_STATIONS_CSV)


def build_full_dataset():
    sightings = load_sightings()
    stations = load_stations()
    image_stations = load_image_stations()

    merged = sightings.merge(image_stations, on="image", how="left")
    merged = merged.merge(stations, on="station_id", how="left")

    merged = merged.dropna(subset=["latitude", "longitude"])
    return merged


def create_map(data):
    if data.empty:
        print("No location data available to map.")
        return

    center_lat = data["latitude"].mean()
    center_lon = data["longitude"].mean()

    tiger_map = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    colors = ["red", "blue", "green", "purple", "orange", "darkred", "cadetblue"]
    tiger_ids = data["tiger_id"].unique()
    color_map = {tid: colors[i % len(colors)] for i, tid in enumerate(tiger_ids)}

    for tiger_id in tiger_ids:
        tiger_data = data[data["tiger_id"] == tiger_id].sort_values("date")
        points = list(zip(tiger_data["latitude"], tiger_data["longitude"]))

        for _, row in tiger_data.iterrows():
            folium.Marker(
                location=[row["latitude"], row["longitude"]],
                popup=f"{row['tiger_id']} | {row['image']} | {row['date']}",
                icon=folium.Icon(color=color_map[tiger_id])
            ).add_to(tiger_map)

        if len(points) > 1:
            folium.PolyLine(points, color=color_map[tiger_id], weight=3).add_to(tiger_map)

    tiger_map.save(OUTPUT_MAP)
    print(f"Map saved to {OUTPUT_MAP}")


def print_home_range_summary(data):
    print("\n--- Home Range Summary ---")
    for tiger_id, group in data.groupby("tiger_id"):
        num_locations = len(group)
        lat_range = group["latitude"].max() - group["latitude"].min()
        lon_range = group["longitude"].max() - group["longitude"].min()
        approx_area_km2 = round(lat_range * lon_range * 111 * 111, 2)

        print(f"Tiger {tiger_id}: {num_locations} sightings, approx range {approx_area_km2} km²")


if __name__ == "__main__":
    print("Starting Module 3: Movement & Mapping...")
    data = build_full_dataset()
    print(f"Loaded {len(data)} sightings with location data.")
    create_map(data)
    print_home_range_summary(data)
    print("Done.")