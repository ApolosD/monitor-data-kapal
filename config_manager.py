import datetime
import json
import os

CONFIG_FILE = "starlink_config.json"
ADDON_FILE = "starlink_addons.json"
ARCHIVE_FILE = "monthly_archives.json"

def gib_to_gb(value_gib):
    return round(value_gib * 1.07374, 2)

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {
        "total_gb": 750.0,
        "used_gb": 674.0,
        "sisa_hari": 10,
        "tanggal_reset": "25/08/2026",
        "alokasi_bosun": 10.0,
        "cadangan_sisa": 22.0,
        "catatan_backup": "10 GB dialokasikan untuk Bosun, sisa 22 GB untuk backup data lost",
        "last_updated": "Belum pernah diupdate",
    }

def save_config(data):
    wib_time = datetime.datetime.utcnow() + datetime.timedelta(hours=7)
    data["last_updated"] = wib_time.strftime("%d/%m/%Y %H:%M:%S")
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f)

def load_addons():
    if os.path.exists(ADDON_FILE):
        with open(ADDON_FILE, "r") as f:
            return json.load(f)
    return []

def save_addons(addons):
    with open(ADDON_FILE, "w") as f:
        json.dump(addons, f)

def load_archives():
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_archive(month_name, data_df):
    archives = load_archives()
    archives[month_name] = data_df.to_dict(orient="records")
    with open(ARCHIVE_FILE, "w") as f:
        json.dump(archives, f, indent=4)
