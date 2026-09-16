#!/usr/bin/env python3
"""
Phone Clean & Safe Backup CLI
Provides terminal-based phone scanning, backup of important documents, and safe cleanup.
"""

import sys
import os
import argparse
from backend.adb_manager import ADBManager
from backend.scanner import FileScanner
from backend.cleaner import SafeOperationsManager
from backend.categorizer import format_size


def main():
    parser = argparse.ArgumentParser(description="Phone USB Data Cleaner & Safe Backup")
    parser.add_argument("--mode", choices=["adb", "folder"], default="adb", help="Connection mode (adb or folder)")
    parser.add_argument("--path", type=str, default="", help="Folder path when using folder mode")
    parser.add_argument("--backup", action="store_true", help="Backup important documents and photos to PC")
    parser.add_argument("--backup-dest", type=str, default="D:\\Phone_Safe_Backup", help="Backup destination directory")
    parser.add_argument("--clean-screenshots", action="store_true", help="Clean screenshots & screen captures")
    parser.add_argument("--clean-junk", action="store_true", help="Clean app cache, thumbnails & debris")
    parser.add_argument("--dry-run", action="store_true", help="Simulate cleanup without actually deleting files")

    args = parser.parse_args()

    print("=" * 60)
    print("   📱 Phone USB Data Cleaner & Safe Backup Suite")
    print("=" * 60)

    adb = ADBManager()
    scanner = FileScanner(adb)
    ops = SafeOperationsManager(adb)

    # 1. Device check
    if args.mode == "adb":
        if not adb.is_adb_installed():
            print("❌ ADB is not installed or not in PATH.")
            sys.exit(1)
        
        details = adb.get_device_details()
        if not details.get("connected"):
            print(f"⚠️  No device ready: {details.get('reason', 'Check USB connection')}")
            sys.exit(1)

        print(f"✅ Connected to: {details['brand']} {details['model']} (Android {details['android_version']})")
        print(f"🔋 Battery: {details['battery']}% | Storage Used: {details['storage']['used_percent']}%")
        print("🔍 Scanning phone storage (/sdcard/)...")
        res = scanner.scan_adb_device(progress_callback=lambda msg, pct: print(f"  [{pct}%] {msg}", end="\r"))
    else:
        if not os.path.exists(args.path):
            print(f"❌ Folder path does not exist: {args.path}")
            sys.exit(1)
        print(f"🔍 Scanning local directory: {args.path}...")
        res = scanner.scan_local_folder(args.path, progress_callback=lambda msg, pct: print(f"  [{pct}%] {msg}", end="\r"))

    print("\n" + "-" * 60)
    print(f"📊 Scan Complete! Found {res.total_files} files ({res.to_summary_dict()['total_formatted']})\n")

    summary = res.to_summary_dict()
    for k, cat in summary["categories"].items():
        if cat["count"] > 0:
            print(f"  • {cat['label']:<32} : {cat['count']:>5} files ({cat['bytes_formatted']:>10}) -> [{cat['action']}]")
    print("-" * 60)

    # 2. Backup if requested
    if args.backup:
        keep_cats = ["important_docs", "messaging_docs", "camera_media"]
        files_to_backup = []
        for k in keep_cats:
            if k in res.categories:
                files_to_backup.extend(res.categories[k]["files"])

        print(f"\n🛡️  Backing up {len(files_to_backup)} important files to: {args.backup_dest}...")
        manifest = ops.backup_files(
            files=files_to_backup,
            destination_root=args.backup_dest,
            source_type=res.source_type,
            progress_callback=lambda msg, pct: print(f"  [{pct}%] {msg}", end="\r")
        )
        print(f"\n✅ Backup Complete! Saved {manifest['successful_count']} files to: {manifest['backup_dir']}")

    # 3. Clean if requested
    clean_cats = []
    if args.clean_screenshots:
        clean_cats.append("screenshots")
    if args.clean_junk:
        clean_cats.extend(["junk_cache", "apks"])

    if clean_cats:
        files_to_clean = []
        for k in clean_cats:
            if k in res.categories:
                files_to_clean.extend(res.categories[k]["files"])

        if args.dry_run:
            print(f"\n🔍 [DRY RUN] Simulating cleanup for {len(files_to_clean)} files...")
            result = ops.clean_files(files_to_clean, source_type=res.source_type, dry_run=True)
            print(f"✨ Would delete: {result['total_target_files']} files")
            print(f"💾 Would free up: {result['freed_formatted']}")
        else:
            confirm = input(f"\n⚠️  Are you sure you want to permanently delete {len(files_to_clean)} files from phone? (y/N): ")
            if confirm.lower() == 'y':
                print("🧹 Cleaning files...")
                result = ops.clean_files(files_to_clean, source_type=res.source_type, dry_run=False)
                print(f"✅ Cleanup finished! Deleted {result['deleted_count']} files. Freed: {result['freed_formatted']}")
            else:
                print("🚫 Cleanup aborted.")


if __name__ == "__main__":
    main()
