import os
import time
from typing import List, Dict, Any, Optional

try:
    from .adb_manager import ADBManager
    from .categorizer import categorize_file, format_size
except (ImportError, ValueError):
    from adb_manager import ADBManager
    from categorizer import categorize_file, format_size


class ScanResult:
    def __init__(self):
        self.source_type: str = "none"  # "adb" or "folder"
        self.source_path: str = ""
        self.total_files: int = 0
        self.total_bytes: int = 0
        self.categories: Dict[str, Dict[str, Any]] = {
            "important_docs": {
                "label": "Important Documents",
                "badge_color": "success",
                "icon": "file-earmark-text",
                "description": "Work & personal documents (PDF, Word, Excel, text, scans)",
                "action": "KEEP & BACKUP",
                "default_checked_clean": False,
                "default_checked_backup": True,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "camera_media": {
                "label": "Camera Photos & Videos",
                "badge_color": "info",
                "icon": "camera",
                "description": "Original photos & videos shot with your phone camera",
                "action": "KEEP & BACKUP",
                "default_checked_clean": False,
                "default_checked_backup": True,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "messaging_docs": {
                "label": "WhatsApp / Telegram Docs",
                "badge_color": "success",
                "icon": "chat-dots",
                "description": "Documents received via WhatsApp, Telegram, and chats",
                "action": "KEEP & BACKUP",
                "default_checked_clean": False,
                "default_checked_backup": True,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "screenshots": {
                "label": "Screenshots & Screen Captures",
                "badge_color": "warning",
                "icon": "crop",
                "description": "Screen captures, meme clippings, and screen recordings",
                "action": "TARGET FOR CLEANING",
                "default_checked_clean": True,
                "default_checked_backup": False,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "junk_cache": {
                "label": "Cache, Thumbnails & Junk",
                "badge_color": "danger",
                "icon": "trash3",
                "description": "App thumbnails, trash folders, stickers cache & temp debris",
                "action": "SAFE TO CLEAN",
                "default_checked_clean": True,
                "default_checked_backup": False,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "apks": {
                "label": "Leftover APK Installers",
                "badge_color": "warning",
                "icon": "box-seam",
                "description": "Old APK packages left inside Downloads folder",
                "action": "REVIEW & CLEAN",
                "default_checked_clean": True,
                "default_checked_backup": False,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "other_images": {
                "label": "Other Saved Images",
                "badge_color": "secondary",
                "icon": "image",
                "description": "Downloaded web images, wallpapers, social media pictures",
                "action": "OPTIONAL REVIEW",
                "default_checked_clean": False,
                "default_checked_backup": False,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "other_videos": {
                "label": "Other Downloaded Videos",
                "badge_color": "secondary",
                "icon": "film",
                "description": "Downloaded movies, social clips, status videos",
                "action": "OPTIONAL REVIEW",
                "default_checked_clean": False,
                "default_checked_backup": False,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "audio_music": {
                "label": "Audio & Voice Notes",
                "badge_color": "info",
                "icon": "music-note",
                "description": "Music files, recordings, voice notes",
                "action": "OPTIONAL KEEP",
                "default_checked_clean": False,
                "default_checked_backup": False,
                "count": 0,
                "bytes": 0,
                "files": []
            },
            "other_files": {
                "label": "Other Files & Downloads",
                "badge_color": "secondary",
                "icon": "folder",
                "description": "Unsorted downloads and archives",
                "action": "OPTIONAL REVIEW",
                "default_checked_clean": False,
                "default_checked_backup": False,
                "count": 0,
                "bytes": 0,
                "files": []
            }
        }

    def add_file(self, full_path: str, filename: str, size: int, mtime: int):
        cat_info = categorize_file(full_path, filename, size)
        cat_key = cat_info["category"]
        if cat_key not in self.categories:
            cat_key = "other_files"

        file_entry = {
            "id": f"{cat_key}_{len(self.categories[cat_key]['files']) + 1}",
            "path": full_path,
            "filename": filename,
            "size": size,
            "size_str": format_size(size),
            "mtime": mtime,
            "category": cat_key,
            "category_label": cat_info.get("category_label", cat_key),
            "badge": cat_info.get("badge", "File"),
            "badge_color": cat_info.get("badge_color", "secondary"),
            "recommendation": cat_info.get("recommendation", "REVIEW"),
            "description": cat_info.get("description", "")
        }

        self.categories[cat_key]["files"].append(file_entry)
        self.categories[cat_key]["count"] += 1
        self.categories[cat_key]["bytes"] += size
        self.total_files += 1
        self.total_bytes += size

    def to_summary_dict(self) -> Dict[str, Any]:
        """Returns JSON-serializable overview of categories and statistics."""
        cat_summaries = {}
        for k, v in self.categories.items():
            cat_summaries[k] = {
                "key": k,
                "label": v["label"],
                "badge_color": v["badge_color"],
                "icon": v["icon"],
                "description": v["description"],
                "action": v["action"],
                "default_checked_clean": v["default_checked_clean"],
                "default_checked_backup": v["default_checked_backup"],
                "count": v["count"],
                "bytes": v["bytes"],
                "bytes_formatted": format_size(v["bytes"]),
                "files_count": len(v["files"])
            }
        
        # Calculate cleanable vs keepable potential
        cleanable_bytes = sum(v["bytes"] for k, v in self.categories.items() if v["default_checked_clean"])
        keepable_bytes = sum(v["bytes"] for k, v in self.categories.items() if v["default_checked_backup"])

        return {
            "source_type": self.source_type,
            "source_path": self.source_path,
            "total_files": self.total_files,
            "total_bytes": self.total_bytes,
            "total_formatted": format_size(self.total_bytes),
            "cleanable_bytes": cleanable_bytes,
            "cleanable_formatted": format_size(cleanable_bytes),
            "keepable_bytes": keepable_bytes,
            "keepable_formatted": format_size(keepable_bytes),
            "categories": cat_summaries
        }


class FileScanner:
    def __init__(self, adb_manager: ADBManager):
        self.adb_manager = adb_manager
        self.last_scan: Optional[ScanResult] = None

    def scan_adb_device(self, progress_callback=None) -> ScanResult:
        """Scan connected ADB Android phone."""
        res = ScanResult()
        res.source_type = "adb"
        res.source_path = "/sdcard"

        raw_files = self.adb_manager.scan_storage_files(progress_callback=progress_callback)
        total = len(raw_files)
        
        for i, item in enumerate(raw_files):
            if progress_callback and i % 50 == 0:
                progress_callback(f"Categorizing files... ({i}/{total})", 50 + int((i / max(total, 1)) * 50))
            res.add_file(item["path"], item["filename"], item["size"], item["mtime"])

        self.last_scan = res
        return res

    def scan_local_folder(self, folder_path: str, progress_callback=None) -> ScanResult:
        """Scan a local folder, mounted MTP drive or USB directory."""
        res = ScanResult()
        res.source_type = "folder"
        res.source_path = folder_path

        if not os.path.exists(folder_path):
            self.last_scan = res
            return res

        all_entries = []
        if progress_callback:
            progress_callback("Scanning folder structure...", 10)

        for root, dirs, files in os.walk(folder_path):
            for file in files:
                full_p = os.path.join(root, file)
                all_entries.append(full_p)

        total = len(all_entries)
        for i, full_p in enumerate(all_entries):
            if progress_callback and i % 50 == 0:
                progress_callback(f"Analyzing {os.path.basename(full_p)}...", int((i / max(total, 1)) * 100))
            
            try:
                stat = os.stat(full_p)
                size = stat.st_size
                mtime = int(stat.st_mtime)
            except Exception:
                size = 0
                mtime = int(time.time())

            res.add_file(full_p, os.path.basename(full_p), size, mtime)

        self.last_scan = res
        return res
