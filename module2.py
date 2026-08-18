"""
MODULE 2 — Tiger Identification (Stripe Matching)
Tiger Intelligence System
"""

import os
import cv2
import sqlite3
import datetime

# ---------- CONFIG ----------
PROCESSED_DIR = "processed"
TIGERS_DB_DIR = "tigers_db"
IDENTIFIED_DIR = "identified"
UNMATCHED_DIR = "unmatched"
DB_PATH = "tiger_database.db"

MATCH_THRESHOLD = 15
NEXT_ID_COUNTER = 1
# -----------------------------

orb = cv2.ORB_create(nfeatures=1000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)


def ensure_dirs():
    os.makedirs(TIGERS_DB_DIR, exist_ok=True)
    os.makedirs(IDENTIFIED_DIR, exist_ok=True)
    os.makedirs(UNMATCHED_DIR, exist_ok=True)


def setup_database():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sightings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tiger_id TEXT,
            image TEXT,
            confidence REAL,
            date TEXT
        )
    """)
    conn.commit()
    return conn


def is_valid_image(path):
    """Reject non-image files like .crdownload, .txt, etc."""
    valid_extensions = (".jpg", ".jpeg", ".png", ".bmp")
    return path.lower().endswith(valid_extensions)


def get_features(image_path):
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        return None, None
    kp, des = orb.detectAndCompute(img, None)
    return kp, des


def load_known_tigers():
    known = {}
    for tiger_id in os.listdir(TIGERS_DB_DIR):
        tiger_folder = os.path.join(TIGERS_DB_DIR, tiger_id)
        if not os.path.isdir(tiger_folder):
            continue
        for ref_img in os.listdir(tiger_folder):
            ref_path = os.path.join(tiger_folder, ref_img)
            if not is_valid_image(ref_path):
                continue
            kp, des = get_features(ref_path)
            if des is not None:
                known.setdefault(tiger_id, []).append(des)
    return known


def match_tiger(des, known_tigers):
    best_id = None
    best_score = 0

    for tiger_id, des_list in known_tigers.items():
        for known_des in des_list:
            if known_des is None or des is None:
                continue
            matches = bf.match(des, known_des)
            good_matches = [m for m in matches if m.distance < 60]
            score = len(good_matches)
            if score > best_score:
                best_score = score
                best_id = tiger_id

    return best_id, best_score


def register_new_tiger(image_path, des):
    global NEXT_ID_COUNTER
    while True:
        new_id = f"T{NEXT_ID_COUNTER:03d}"
        new_folder = os.path.join(TIGERS_DB_DIR, new_id)
        if not os.path.exists(new_folder):
            break
        NEXT_ID_COUNTER += 1

    os.makedirs(new_folder, exist_ok=True)
    filename = os.path.basename(image_path)
    ref_save_path = os.path.join(new_folder, filename)

    img = cv2.imread(image_path)
    if img is not None:
        try:
            cv2.imwrite(ref_save_path, img)
        except Exception as e:
            print(f"[WARN]   Could not save reference for {filename}: {e}")

    NEXT_ID_COUNTER += 1
    return new_id


def process_images():
    ensure_dirs()
    conn = setup_database()
    cur = conn.cursor()

    known_tigers = load_known_tigers()

    for filename in os.listdir(PROCESSED_DIR):
        image_path = os.path.join(PROCESSED_DIR, filename)

        if not os.path.isfile(image_path):
            continue

        if not is_valid_image(image_path):
            print(f"[SKIP]   {filename} -> not a valid image file")
            continue

        kp, des = get_features(image_path)

        if des is None:
            print(f"[SKIP]   {filename} -> unreadable or no features found")
            continue

        best_id, score = match_tiger(des, known_tigers)

        if best_id and score >= MATCH_THRESHOLD:
            confidence = min(round((score / 50) * 100, 1), 99.9)
            print(f"[MATCH]  {filename} -> {best_id} (confidence {confidence}%)")
            dest = os.path.join(IDENTIFIED_DIR, filename)
        else:
            new_id = register_new_tiger(image_path, des)
            known_tigers.setdefault(new_id, []).append(des)
            best_id = new_id
            confidence = 100.0
            print(f"[NEW]    {filename} -> registered as {new_id}")
            dest = os.path.join(IDENTIFIED_DIR, filename)

        img_to_save = cv2.imread(image_path)
        if img_to_save is not None:
            try:
                cv2.imwrite(dest, img_to_save)
            except Exception as e:
                print(f"[WARN]   Could not save {filename} to identified/: {e}")

        cur.execute(
            "INSERT INTO sightings (tiger_id, image, confidence, date) VALUES (?, ?, ?, ?)",
            (best_id, filename, confidence, str(datetime.date.today()))
        )
        conn.commit()

    conn.close()


if __name__ == "__main__":
    print("Starting Module 2: Tiger Identification...")
    process_images()
    print("Done.")
