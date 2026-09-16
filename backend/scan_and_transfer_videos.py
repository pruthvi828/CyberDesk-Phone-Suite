import subprocess
import os
import shutil
import time
import json

DEV_ID = "UCWSUKMVHQUWXC8D"
DEST_PENDRIVE = "E:\\Realme8_Phone_Videos"
STATUS_FILE = os.path.join(os.path.dirname(__file__), "migration_status.json")

def write_status(data):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        pass

def ensure_adb():
    # Make sure adb server is running
    subprocess.run(['adb', 'start-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_adb_shell(cmd, retries=3):
    for attempt in range(retries):
        ensure_adb()
        res = subprocess.run(['adb', '-s', DEV_ID, 'shell'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        if res.returncode == 0:
            return res.stdout
        time.sleep(1)
    return ""

def run_adb_pull(remote_path, local_path, retries=3):
    for attempt in range(retries):
        ensure_adb()
        res = subprocess.run(['adb', '-s', DEV_ID, 'pull', remote_path, local_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        if res.returncode == 0:
            return True
        time.sleep(1.5)
    return False

def run_adb_delete(remote_path, retries=3):
    for attempt in range(retries):
        ensure_adb()
        res = subprocess.run(['adb', '-s', DEV_ID, 'shell', 'rm', '-f', f'"{remote_path}"'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        if res.returncode == 0:
            return True
        time.sleep(1)
    return False

def get_file_size(remote_path):
    out = run_adb_shell(['stat', '-c', '%s', f'"{remote_path}"']).strip()
    try:
        return int(out.splitlines()[-1].strip())
    except Exception:
        return 0

def find_all_videos():
    dirs = [
        '/sdcard/DCIM',
        '/sdcard/Movies',
        '/sdcard/Download',
        '/sdcard/Pictures',
        '/sdcard/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Video'
    ]
    video_exts = {'.mp4', '.mov', '.mkv', '.3gp', '.webm', '.m4v', '.avi'}
    
    all_video_paths = []
    for d in dirs:
        out = run_adb_shell(['find', d, '-type', 'f'])
        for line in out.strip().splitlines():
            line = line.strip()
            if not line or line.startswith('find:') or 'No such file' in line or line.startswith('*'):
                continue
            ext = os.path.splitext(line)[1].lower()
            if ext in video_exts:
                all_video_paths.append(line)

    print(f"  • Located {len(all_video_paths)} video files on phone.")

    video_list = []
    for p in all_video_paths:
        sz = get_file_size(p)
        if sz > 0:
            video_list.append((sz, p))

    return video_list

def main():
    print("=" * 65)
    print("   🎥 Transfer Realme 8 Videos to Pen Drive & Free Space")
    print("=" * 65)

    if not os.path.exists("E:\\"):
        print("❌ Pen drive (E:\\) is not mounted!")
        write_status({"status": "error", "message": "Pen drive E: not mounted"})
        return

    os.makedirs(DEST_PENDRIVE, exist_ok=True)

    print("🔍 1. Scanning remaining videos on phone...")
    videos = find_all_videos()
    total_count = len(videos)
    total_bytes = sum(v[0] for v in videos)
    total_gb = total_bytes / (1024**3)

    print(f"📊 Remaining on phone: {total_count} videos ({total_gb:.2f} GB / {total_bytes / (1024**2):.1f} MB)\n")

    free_drive_bytes = shutil.disk_usage("E:\\").free
    print(f"💾 Pen Drive (E:\\) Free Space: {free_drive_bytes / (1024**3):.2f} GB")
    print(f"📁 Destination Folder: {DEST_PENDRIVE}\n")

    successful_transfers = []
    failed_transfers = []
    transferred_bytes = 0

    write_status({
        "status": "in_progress",
        "total_files": total_count,
        "processed_files": 0,
        "pending_files": total_count,
        "total_bytes": total_bytes,
        "transferred_bytes": 0,
        "current_file": "Starting transfer...",
        "percent": 0.0,
        "successful_count": 0,
        "failed_count": 0
    })

    print("🚀 2. Transferring, verifying, and deleting from phone...")
    for i, (sz, remote_p) in enumerate(videos):
        fname = os.path.basename(remote_p)
        local_dest = os.path.join(DEST_PENDRIVE, fname)

        percent = round(((i) / max(total_count, 1)) * 100, 1)

        write_status({
            "status": "in_progress",
            "total_files": total_count,
            "processed_files": i,
            "pending_files": total_count - i,
            "total_bytes": total_bytes,
            "transferred_bytes": transferred_bytes,
            "current_file": fname,
            "percent": percent,
            "successful_count": len(successful_transfers),
            "failed_count": len(failed_transfers)
        })

        print(f"  [{i+1}/{total_count}] ({sz/(1024*1024):.1f} MB) {fname}...", end="", flush=True)

        # Check if already safely copied to pen drive with matching size
        if os.path.exists(local_dest) and os.path.getsize(local_dest) == sz:
            del_ok = run_adb_delete(remote_p)
            if del_ok:
                print(" ✅ Verified existing & Deleted from phone.")
            else:
                print(" ✅ Verified on Pen Drive.")
            successful_transfers.append((sz, remote_p, local_dest))
            transferred_bytes += sz
            continue

        # If not, pull it
        ok = run_adb_pull(remote_p, local_dest)
        
        # Verify size matches byte-for-byte
        if ok and os.path.exists(local_dest) and os.path.getsize(local_dest) == sz:
            del_ok = run_adb_delete(remote_p)
            if del_ok:
                print(" ✅ Moved & Deleted from phone.")
            else:
                print(" ✅ Copied to Pen Drive.")
            successful_transfers.append((sz, remote_p, local_dest))
            transferred_bytes += sz
        else:
            print(" ❌ Failed! (Skipped deletion).")
            failed_transfers.append((sz, remote_p))

    final_status = {
        "status": "completed",
        "total_files": total_count,
        "processed_files": total_count,
        "pending_files": 0,
        "total_bytes": total_bytes,
        "transferred_bytes": transferred_bytes,
        "current_file": "Migration Finished!",
        "percent": 100.0,
        "successful_count": len(successful_transfers),
        "failed_count": len(failed_transfers)
    }
    write_status(final_status)

    print("\n" + "=" * 65)
    print(f"🎉 Transfer & Cleanup Complete!")
    print(f"  • Videos Transferred to Pen Drive: {len(successful_transfers)}")
    print(f"  • Total Space Freed on Phone:     {transferred_bytes / (1024**3):.2f} GB ({transferred_bytes / (1024**2):.1f} MB)")
    print(f"  • Saved Location on Pen Drive:    {DEST_PENDRIVE}")
    print("=" * 65)

    # Check updated phone storage
    df_out = run_adb_shell(['df', '-h', '/sdcard'])
    print("\n📱 Updated Phone Storage:")
    print(df_out.strip())

if __name__ == "__main__":
    main()
