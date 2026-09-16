import os
import json
import time
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
try:
    from .adb_manager import ADBManager
    from .categorizer import format_size
except (ImportError, ValueError):
    from adb_manager import ADBManager
    from categorizer import format_size


class SafeOperationsManager:
    def __init__(self, adb_manager: ADBManager):
        self.adb_manager = adb_manager

    def backup_files(
        self,
        files: List[Dict[str, Any]],
        destination_root: str,
        source_type: str = "adb",
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Safely copies selected files to a organized backup directory on the PC.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = os.path.join(destination_root, f"Phone_Backup_{timestamp}")
        os.makedirs(backup_dir, exist_ok=True)

        successful_copies = []
        failed_copies = []
        total_bytes_copied = 0
        total_files = len(files)

        for i, item in enumerate(files):
            rel_cat = item.get("category", "other_files")
            filename = item.get("filename", "unknown")
            src_path = item.get("path", "")
            size = item.get("size", 0)

            # Map category to structured subfolder
            cat_folder_map = {
                "important_docs": "01_Important_Documents",
                "messaging_docs": "02_WhatsApp_Telegram_Docs",
                "camera_media": "03_Camera_Photos_Videos",
                "audio_music": "04_Audio_Recordings",
                "other_images": "05_Saved_Images",
                "other_videos": "06_Saved_Videos",
                "other_files": "07_Other_Files"
            }
            subfolder = cat_folder_map.get(rel_cat, "08_Uncategorized")
            target_folder = os.path.join(backup_dir, subfolder)
            os.makedirs(target_folder, exist_ok=True)
            
            target_path = os.path.join(target_folder, filename)
            
            # Prevent filename collision
            if os.path.exists(target_path):
                base, ext = os.path.splitext(filename)
                target_path = os.path.join(target_folder, f"{base}_{i}{ext}")

            if progress_callback:
                progress_callback(f"Backing up: {filename}", int(((i + 1) / max(total_files, 1)) * 100))

            success = False
            if source_type == "adb":
                success = self.adb_manager.pull_file(src_path, target_path)
            else:
                try:
                    shutil.copy2(src_path, target_path)
                    success = os.path.exists(target_path)
                except Exception as e:
                    success = False

            if success:
                successful_copies.append({
                    "src": src_path,
                    "dest": target_path,
                    "size": size,
                    "filename": filename
                })
                total_bytes_copied += size
            else:
                failed_copies.append({
                    "src": src_path,
                    "filename": filename
                })

        # Save backup manifest
        manifest = {
            "timestamp": timestamp,
            "backup_dir": backup_dir,
            "total_requested": total_files,
            "successful_count": len(successful_copies),
            "failed_count": len(failed_copies),
            "total_bytes_copied": total_bytes_copied,
            "total_formatted": format_size(total_bytes_copied),
            "files": successful_copies
        }
        with open(os.path.join(backup_dir, "backup_manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest

    def clean_files(
        self,
        files: List[Dict[str, Any]],
        source_type: str = "adb",
        dry_run: bool = False,
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Deletes selected files (or simulates deletion if dry_run=True).
        """
        total_files = len(files)
        deleted_files = []
        failed_deletions = []
        freed_bytes = 0

        if dry_run:
            for item in files:
                freed_bytes += item.get("size", 0)
                deleted_files.append({
                    "path": item.get("path"),
                    "filename": item.get("filename"),
                    "size": item.get("size", 0),
                    "size_str": format_size(item.get("size", 0))
                })
            return {
                "dry_run": True,
                "total_target_files": total_files,
                "total_freed_bytes": freed_bytes,
                "freed_formatted": format_size(freed_bytes),
                "preview_files": deleted_files
            }

        # Actual Deletion
        for i, item in enumerate(files):
            path = item.get("path", "")
            filename = item.get("filename", "")
            size = item.get("size", 0)

            if progress_callback and i % 10 == 0:
                progress_callback(f"Cleaning: {filename}", int(((i + 1) / max(total_files, 1)) * 100))

            success = False
            if source_type == "adb":
                success = self.adb_manager.delete_file(path)
            else:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                        success = not os.path.exists(path)
                except Exception:
                    success = False

            if success:
                deleted_files.append({
                    "path": path,
                    "filename": filename,
                    "size": size
                })
                freed_bytes += size
            else:
                failed_deletions.append({
                    "path": path,
                    "filename": filename
                })

        # Remove empty debris dirs if ADB
        if source_type == "adb":
            self.adb_manager.delete_empty_dirs("/sdcard/Pictures/Screenshots")
            self.adb_manager.delete_empty_dirs("/sdcard/DCIM/Screenshots")
            self.adb_manager.delete_empty_dirs("/sdcard/Screenshots")

        return {
            "dry_run": False,
            "total_requested": total_files,
            "deleted_count": len(deleted_files),
            "failed_count": len(failed_deletions),
            "freed_bytes": freed_bytes,
            "freed_formatted": format_size(freed_bytes),
            "deleted_files": deleted_files,
            "failed_files": failed_deletions
        }
