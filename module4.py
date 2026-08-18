"""
MODULE 4 — Deviation & Alert System
Tiger Intelligence System
"""

import sqlite3
import pandas as pd
import datetime

# ---------- CONFIG ----------
DB_PATH = "tiger_database.db"
STATIONS_CSV = "stations.csv"
IMAGE_STATIONS_CSV = "image_stations.csv"

RANGE_SHIFT_KM = 5.0        # distance from tiger's usual center to trigger alert
ABSENCE_DAYS = 30           # days without sighting to trigger alert
# -----------------------------


def load_data():
    conn = sqlite3.connect(DB_PATH)
    sightings = pd.read_sql_query("SELECT * FROM sightings", conn)
    conn.close()

    stations = pd.read_csv(STATIONS_CSV)
    image_stations = pd.read_csv(IMAGE_STATIONS_CSV)

    data = sightings.merge(image_stations, on="image", how="left")
    data = data.merge(stations, on="station_id", how="left")
    data = data.dropna(subset=["latitude", "longitude"])
    data["date"] = pd.to_datetime(data["date"])

    return data


def check_new_station(tiger_data):
    alerts = []
    seen_stations = set()

    for _, row in tiger_data.sort_values("date").iterrows():
        if row["station_id"] not in seen_stations:
            if seen_stations:  # not the very first sighting ever
                alerts.append(f"NEW STATION -> {row['tiger_id']} seen at new station {row['station_id']} on {row['date'].date()}")
            seen_stations.add(row["station_id"])

    return alerts


def check_zone_alerts(tiger_data):
    alerts = []
    for _, row in tiger_data.iterrows():
        if row["zone"] == "village":
            alerts.append(f"VILLAGE ALERT -> {row['tiger_id']} detected in VILLAGE zone ({row['station_id']}) on {row['date'].date()}")
        elif row["zone"] == "buffer":
            alerts.append(f"BUFFER ALERT -> {row['tiger_id']} detected in BUFFER zone ({row['station_id']}) on {row['date'].date()}")
    return alerts


def check_range_shift(tiger_data):
    alerts = []
    center_lat = tiger_data["latitude"].mean()
    center_lon = tiger_data["longitude"].mean()

    for _, row in tiger_data.iterrows():
        # rough distance in km using simple degree-to-km conversion
        dist_km = ((row["latitude"] - center_lat) ** 2 + (row["longitude"] - center_lon) ** 2) ** 0.5 * 111
        if dist_km > RANGE_SHIFT_KM:
            alerts.append(f"RANGE SHIFT -> {row['tiger_id']} moved {round(dist_km,2)} km from usual range on {row['date'].date()}")

    return alerts


def check_absence(tiger_data):
    alerts = []
    last_seen = tiger_data["date"].max()
    days_since = (pd.Timestamp(datetime.date.today()) - last_seen).days

    if days_since > ABSENCE_DAYS:
        alerts.append(f"ABSENCE ALERT -> {tiger_data['tiger_id'].iloc[0]} not seen for {days_since} days (last seen {last_seen.date()})")

    return alerts


def run_alerts():
    data = load_data()

    if data.empty:
        print("No sighting data available.")
        return

    all_alerts = []

    for tiger_id, tiger_data in data.groupby("tiger_id"):
        all_alerts += check_new_station(tiger_data)
        all_alerts += check_zone_alerts(tiger_data)
        all_alerts += check_range_shift(tiger_data)
        all_alerts += check_absence(tiger_data)

    print(f"\nTotal alerts generated: {len(all_alerts)}\n")

    if all_alerts:
        for alert in all_alerts:
            print(f"🚨 {alert}")
    else:
        print("No alerts. All tigers within normal patterns.")


if __name__ == "__main__":
    print("Starting Module 4: Alert System...")
    run_alerts()
    print("\nDone.")