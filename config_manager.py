import datetime
import json
import os

CONFIG_FILE = "starlink_config.json"
ADDON_FILE = "starlink_addons.json"
ARCHIVE_FILE = "monthly_archives.json"
AUDIT_FILE = "audit_logs.json"

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
    wib_time = datetime.datetime.now()
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

def load_locales():
    return {
      "id": {
        "title": "🌐 MONITORING JARINGAN KAPAL (STARLINK & MIKROTIK)",
        "access_time": "Waktu Akses",
        "ctrl_panel": "⚙️ Panel Kontrol",
        "sl_config": "📡 Konfigurasi Starlink",
        "total_quota": "Total Kuota Bulan Ini (GB)",
        "total_used": "Total Terpakai Saat Ini (GB)",
        "rem_days": "Sisa Hari Siklus",
        "reset_date": "Tanggal Reset",
        "alloc_backup": "⚙️ Alokasi & Backup",
        "bosun_alloc": "Alokasi Khusus Bosun (GB)",
        "backup_res": "Cadangan Sisa / Backup (GB)",
        "backup_notes": "Keterangan Backup",
        "save_conf": "💾 Simpan Konfigurasi",
        "conf_saved": "Konfigurasi disimpan!",
        "status_title": "📊 Status Starlink & Perbandingan Jaringan",
        "starlink_rem": "Sisa Kuota Starlink",
        "crew_rem": "Total Sisa Limit Crew",
        "lost_data": "LOST DATA",
        "starlink_used": "Starlink Terpakai",
        "mikrotik_total": "Total Mikrotik Users",
        "hotspot_active": "Hotspot Active",
        "danger": "⚠️ BAHAYA: Kebutuhan data tidak mencukupi (Defisit)",
        "safe": "✅ AMAN: Kebutuhan data mencukupi (Surplus)",
        "notes": "Catatan Alokasi Backup",
        "hotspot_recap": "👥 Rekapitulasi Pengguna Hotspot Mikrotik",
        "fail_conn": "[GAGAL] Tidak dapat terhubung ke Mikrotik.",
        "no_data": "Data hotspot kosong.",
        "online_users": "🔥 Pengguna Hotspot Online Saat Ini (Active)",
        "no_active": "Tidak ada pengguna aktif saat ini.",
        "download_recap": "📥 Unduh rekapan data penggunaan kuota hotspot crew.",
        "btn_download": "📄 Download Rekap (CSV)",
        "status_exhausted": "PAS / HABIS KUOTA",
        "status_critical": "KRITIS",
        "status_safe": "Aman",
        "status_active": "Aktif (Unlimited)",
        "status_unused": "Belum Digunakan"
      },
      "en": {
        "title": "🌐 VESSEL NETWORK MONITORING (STARLINK & MIKROTIK)",
        "access_time": "Access Time",
        "ctrl_panel": "⚙️ Control Panel",
        "sl_config": "📡 Starlink Configuration",
        "total_quota": "Total Monthly Quota (GB)",
        "total_used": "Current Total Used (GB)",
        "rem_days": "Remaining Cycle Days",
        "reset_date": "Reset Date",
        "alloc_backup": "⚙️ Allocation & Backup",
        "bosun_alloc": "Bosun Dedicated Allocation (GB)",
        "backup_res": "Remaining Reserve / Backup (GB)",
        "backup_notes": "Backup Notes",
        "save_conf": "💾 Save Configuration",
        "conf_saved": "Configuration saved!",
        "status_title": "📊 Starlink Status & Network Comparison",
        "starlink_rem": "Starlink Remaining Quota",
        "crew_rem": "Total Crew Remaining Limit",
        "lost_data": "LOST DATA",
        "starlink_used": "Starlink Used",
        "mikrotik_total": "Total MikroTik Users",
        "hotspot_active": "Active Hotspot",
        "danger": "⚠️ DANGER: Data requirement is insufficient (Deficit)",
        "safe": "✅ SAFE: Data requirement is sufficient (Surplus)",
        "notes": "Backup Allocation Notes",
        "hotspot_recap": "👥 MikroTik Hotspot User Recapitulation",
        "fail_conn": "[FAILED] Unable to connect to Mikrotik.",
        "no_data": "Hotspot data is empty.",
        "online_users": "🔥 Currently Online Hotspot Users",
        "no_active": "No active users currently online.",
        "download_recap": "📥 Download crew hotspot quota usage recapitulation.",
        "btn_download": "📄 Download Recap (CSV)",
        "status_exhausted": "EXHAUSTED / NO QUOTA",
        "status_critical": "CRITICAL",
        "status_safe": "Safe",
        "status_active": "Active (Unlimited)",
        "status_unused": "Unused"
      }
    }

def load_audit_logs():
    if os.path.exists(AUDIT_FILE):
        with open(AUDIT_FILE, "r") as f:
            return json.load(f)
    return []

def save_audit_log(action_desc, admin_user):
    logs = load_audit_logs()
    wib_time = datetime.datetime.now()
    new_log = {
        "timestamp": wib_time.strftime("%d/%m/%Y %H:%M:%S WIB"),
        "admin": admin_user,
        "action": action_desc
    }
    logs.insert(0, new_log)
    with open(AUDIT_FILE, "w") as f:
        json.dump(logs, f, indent=4)