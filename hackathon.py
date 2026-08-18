"""
MODULE 1 — Blank Image Filtering
Tiger Intelligence System
"""

import os
import shutil
import cv2
import numpy as np

# ---------- CONFIG ----------
INPUT_DIR = "images"
PROCESSED_DIR = "processed"
QUARANTINE_DIR = "quarantine"

BRIGHTNESS_LOW = 20
BRIGHTNESS_HIGH = 235
VARIANCE_THRESHOLD = 100
EDGE_DENSITY_THRESHOLD = 0.015
FAIL_VOTES_NEEDED = 2
# -----------------------------


def ensure_dirs():
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    os.makedirs(QUARANTINE_DIR, exist_ok=True)


def analyze_image(path):
    image = cv2.imread(path)
    if image is None:
        return True, {"error": "unreadable"}

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    mean_brightness = float(np.mean(gray))
    brightness_fail = mean_brightness < BRIGHTNESS_LOW or mean_brightness > BRIGHTNESS_HIGH

    variance = float(np.var(gray))
    variance_fail = variance < VARIANCE_THRESHOLD

    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.count_nonzero(edges)) / edges.size
    edge_fail = edge_density < EDGE_DENSITY_THRESHOLD

    votes = sum([brightness_fail, variance_fail, edge_fail])
    is_blank = votes >= FAIL_VOTES_NEEDED

    stats = {
        "brightness": round(mean_brightness, 2),
        "variance": round(variance, 2),
        "edge_density": round(edge_density, 4),
        "votes_failed": votes,
    }

    return is_blank, stats


def process_images():
    ensure_dirs()

    for filename in os.listdir(INPUT_DIR):
        src_path = os.path.join(INPUT_DIR, filename)

        if not os.path.isfile(src_path):
            continue

        is_blank, stats = analyze_image(src_path)

        if is_blank:
            dest_path = os.path.join(QUARANTINE_DIR, filename)
            print(f"[QUARANTINE] {filename} -> {stats}")
        else:
            dest_path = os.path.join(PROCESSED_DIR, filename)
            print(f"[OK]         {filename} -> {stats}")

        shutil.copy2(src_path, dest_path)


if __name__ == "__main__":
    print("Starting processing...")
    process_images()
    print("Done.")
   