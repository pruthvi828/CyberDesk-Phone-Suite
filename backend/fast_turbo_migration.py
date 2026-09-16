import subprocess
import os
import shutil
import time
import json
import tempfile
from concurrent.futures import ThreadPoolExecutor

DEV_ID = "UCWSUKMVHQUWXC8D"
DEST_PENDRIVE = "E:\\Realme8_Phone_Videos"
SSD_BUFFER_DIR = os.path.join(tempfile.gettempdir(), "phone_clean_turbo_buffer")
STATUS_FILE = os.path.join(os.path.dirname(__file__), "migration_status.json")

os.makedirs(SSD_BUFFER_DIR, exist_ok=True)
os.makedirs(DEST_PENDRIVE, exist_ok=True)

def write_status(data):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def ensure_adb():
    subprocess.run(['adb', 'start-server'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def run_adb_shell(cmd, retries=3):
    for _ in range(retries):
        ensure_adb()
        res = subprocess.run(['adb', '-s', DEV_ID, 'shell'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        if res.returncode == 0:
            return res.stdout
        time.sleep(1)
    return ""

def run_adb_pull(remote_path, local_path, retries=3):
    for _ in range(retries):
        ensure_adb()
        res = subprocess.run(['adb', '-s', DEV_ID, 'pull', remote_path, local_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
        if res.returncode == 0:
            return True
        time.sleep(1)
    return False

def run_adb_delete(remote_path, retries=3):
    for _ in range(retries):
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

def fast_copy_file(src, dst, buffer_size=8*1024*1024):
    """Buffered high-speed sequential copy for FAT32 flash pen drives"""
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        while True:
            buf = fsrc.read(buffer_size)
            if not buf:
                break
            fdst.write(buf)

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

    video_list = []
    for p in all_video_paths:
        sz = get_file_size(p)
        if sz > 0:
            video_list.append((sz, p))

    return video_list

def main():
    print("=" * 65)
    print("   ⚡ TURBO HIGH-SPEED VIDEO MIGRATION (SSD Buffer + Async Flash)")
    print("=" * 65)

    if not os.path.exists("E:\\"):
        print("❌ Pen drive (E:\\) is not mounted!")
        write_status({"status": "error", "message": "Pen drive E: not mounted"})
        return

    print("🔍 Scanning videos remaining on phone...")
    videos = find_all_videos()
    total_count = len(videos)
    total_bytes = sum(v[0] for v in videos)
    total_gb = total_bytes / (1024**3)

    print(f"📊 Remaining: {total_count} videos ({total_gb:.2f} GB / {total_bytes / (1024**2):.1f} MB)")

    successful_transfers = []
    failed_transfers = []
    transferred_bytes = 0
    start_time = time.time()

    for i, (sz, remote_p) in enumerate(videos):
        fname = os.path.basename(remote_p)
        ssd_temp = os.path.join(SSD_BUFFER_DIR, fname)
        final_dest = os.path.join(DEST_PENDRIVE, fname)

        elapsed = max(time.time() - start_time, 1.0)
        speed_mb_s = (transferred_bytes / (1024 * 1024)) / elapsed if transferred_bytes > 0 else 22.0
        remaining_bytes = total_bytes - transferred_bytes
        remaining_sec = int((remaining_bytes / (1024 * 1024)) / max(speed_mb_s, 5.0))
        rem_min = remaining_sec // 60
        rem_sec = remaining_sec % 60
        eta_str = f"{rem_min}m {rem_sec:02d}s"

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
            "speed_mb_s": round(speed_mb_s, 1),
            "eta": eta_str,
            "successful_count": len(successful_transfers),
            "failed_count": len(failed_transfers)
        })

        print(f"  [{i+1}/{total_count}] ({sz/(1024*1024):.1f} MB) {fname} | Speed: {speed_mb_s:.1f} MB/s | ETA: {eta_str}...", end="", flush=True)

        # Check if already verified on pen drive
        if os.path.exists(final_dest) and os.path.getsize(final_dest) == sz:
            run_adb_delete(remote_p)
            print(" ✅ (Already on Pen Drive -> Deleted from Phone)")
            successful_transfers.append((sz, remote_p))
            transferred_bytes += sz
            continue

        # Step 1: High-Speed Pull to NVMe SSD
        pull_ok = run_adb_pull(remote_p, ssd_temp)
        if not pull_ok or not os.path.exists(ssd_temp) or os.path.getsize(ssd_temp) != sz:
            print(" ❌ Pull Failed! Skipping.")
            failed_transfers.append((sz, remote_p))
            if os.path.exists(ssd_temp):
                try: os.remove(ssd_temp)
                except: pass
            continue

        # Step 2: High-Speed Buffered Flash Write to Pen Drive
        try:
            fast_copy_file(ssd_temp, final_dest)
        except Exception as e:
            print(f" ❌ Pen Drive Write Error: {e}")
            failed_transfers.append((sz, remote_p))
            continue
        finally:
            try: os.remove(ssd_temp)
            except: pass

        # Step 3: Byte Verification & Phone Cleanup
        if os.path.exists(final_dest) and os.path.getsize(final_dest) == sz:
            run_adb_delete(remote_p)
            print(" ✅ Moved & Deleted from phone.")
            successful_transfers.append((sz, remote_p))
            transferred_bytes += sz
        else:
            print(" ❌ Size Mismatch on Pen Drive! Kept on phone.")
            failed_transfers.append((sz, remote_p))

    # Finish
    write_status({
        "status": "completed",
        "total_files": total_count,
        "processed_files": total_count,
        "pending_files": 0,
        "total_bytes": total_bytes,
        "transferred_bytes": transferred_bytes,
        "current_file": "Migration Complete!",
        "percent": 100.0,
        "speed_mb_s": 0.0,
        "eta": "0m 00s",
        "successful_count": len(successful_transfers),
        "failed_count": len(failed_transfers)
    })

    print("\n" + "=" * 65)
    print("🎉 Turbo Migration Complete!")
    print(f"  • Total Videos Transferred: {len(successful_transfers)}")
    print(f"  • Total Space Freed:       {transferred_bytes / (1024**3):.2f} GB")
    print("=" * 65)

    df_out = run_adb_shell(['df', '-h', '/sdcard'])
    print("\n📱 Updated Phone Storage:")
    print(df_out.strip())

if __name__ == "__main__":
    main()
