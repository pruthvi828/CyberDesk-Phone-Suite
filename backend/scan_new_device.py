import subprocess
import os
import json
from collections import defaultdict
from backend.categorizer import categorize_file, format_size
from backend.adb_manager import ADBManager

def run_adb(cmd, dev_id="UCWSUKMVHQUWXC8D"):
    res = subprocess.run(['adb', '-s', dev_id, 'shell'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
    return res.stdout

def scan_device(dev_id="UCWSUKMVHQUWXC8D"):
    print("=" * 65)
    print("   📱 Deep Storage Scan & Intelligence Audit (New Phone)")
    print("=" * 65)

    adb = ADBManager()
    adb.select_device(dev_id)
    details = adb.get_device_details()

    print(f"\n📲 DEVICE INFORMATION:")
    print(f"  • Brand & Model:    {details.get('brand')} {details.get('model')} (ID: {dev_id})")
    print(f"  • Android Version:  Android {details.get('android_version')} (SDK {details.get('sdk_version')})")
    print(f"  • Battery Level:    {details.get('battery')}%")
    storage = details.get('storage', {})
    total_gb = storage.get('total_bytes', 0) / (1024**3)
    used_gb = storage.get('used_bytes', 0) / (1024**3)
    free_gb = storage.get('free_bytes', 0) / (1024**3)
    used_pct = storage.get('used_percent', 0)
    print(f"  • Storage Overview: {used_gb:.2f} GB Used / {total_gb:.2f} GB Total ({free_gb:.2f} GB Free — {used_pct}% Full)")

    # 1. Scan storage files
    print("\n🔍 1. SCANNING ALL STORAGE DIRECTORIES (/sdcard/)...")
    target_dirs = [
        "/sdcard/DCIM",
        "/sdcard/Pictures",
        "/sdcard/Documents",
        "/sdcard/Download",
        "/sdcard/Movies",
        "/sdcard/Music",
        "/sdcard/Android/media",
        "/sdcard/WhatsApp",
        "/sdcard/Telegram",
        "/sdcard/Recordings"
    ]

    all_files = []
    for d in target_dirs:
        cmd = f"find '{d}' -type f -exec stat -c '%s %Y %n' '{{}}' +"
        out = run_adb(['sh', '-c', cmd], dev_id=dev_id)
        for line in out.strip().splitlines():
            line = line.strip()
            if not line or line.startswith('find:') or line.startswith('stat:'):
                continue
            parts = line.split(' ', 2)
            if len(parts) == 3:
                try:
                    size = int(parts[0])
                    mtime = int(parts[1])
                    path = parts[2]
                    all_files.append({
                        "size": size,
                        "mtime": mtime,
                        "path": path,
                        "filename": os.path.basename(path)
                    })
                except ValueError:
                    pass

    total_storage_bytes = sum(f["size"] for f in all_files)
    print(f"  • Found {len(all_files):,} files taking {format_size(total_storage_bytes)} across user directories.")

    # 2. Categorize files
    categories = defaultdict(lambda: {"count": 0, "bytes": 0, "files": []})
    for f in all_files:
        cat_info = categorize_file(f["path"], f["filename"], f["size"])
        ckey = cat_info["category"]
        categories[ckey]["count"] += 1
        categories[ckey]["bytes"] += f["size"]
        categories[ckey]["label"] = cat_info["category_label"]
        categories[ckey]["recommendation"] = cat_info["recommendation"]
        categories[ckey]["files"].append(f)

    print("\n📊 2. STORAGE BREAKDOWN BY CATEGORY:")
    print(f"  {'Category':<32} | {'Count':>8} | {'Total Size':>12} | {'Action'}")
    print("  " + "-" * 68)
    for ckey, cdata in sorted(categories.items(), key=lambda x: x[1]["bytes"], reverse=True):
        print(f"  {cdata['label']:<32} | {cdata['count']:>8,} | {format_size(cdata['bytes']):>12} | [{cdata['recommendation']}]")

    # 3. Check App Cache & Large App Data
    print("\n🧠 3. APP STORAGE & RESIDUAL CACHE AUDIT:")
    out_disk = run_adb(['dumpsys', 'diskstats'], dev_id=dev_id)
    pkg_names = []
    app_sizes = []
    cache_sizes = []
    for line in out_disk.splitlines():
        if line.startswith('Package Names:'):
            pkg_names = [p.strip() for p in line.split(':', 1)[1].strip()[1:-1].split(',')]
        elif line.startswith('App Data Sizes:'):
            raw = line.split(':', 1)[1].strip()[1:-1].split(',')
            app_sizes = [int(x) if x.isdigit() else 0 for x in raw]
        elif line.startswith('Cache Sizes:'):
            raw = line.split(':', 1)[1].strip()[1:-1].split(',')
            cache_sizes = [int(x) if x.isdigit() else 0 for x in raw]

    apps = []
    for i in range(min(len(pkg_names), len(app_sizes))):
        pname = pkg_names[i]
        asz = app_sizes[i]
        csz = cache_sizes[i] if i < len(cache_sizes) else 0
        apps.append((asz + csz, asz, csz, pname))

    apps.sort(reverse=True)
    for total, asz, csz, pname in apps[:15]:
        if total > 100 * 1024 * 1024:  # > 100 MB
            print(f"  • {pname:<36} : {format_size(total):>10} (Cache: {format_size(csz)})")

    # 4. Check Gallery Blob Cache / Trash
    blob_out = run_adb(['du', '-sh', '/sdcard/Android/data/com.coloros.gallery3d/files'], dev_id=dev_id).strip()
    if blob_out:
        print(f"  • Gallery Cache/Trash (`com.coloros.gallery3d`): {blob_out}")

    # 5. Top 10 Largest Files
    all_files.sort(key=lambda x: x["size"], reverse=True)
    print("\n🏆 4. TOP 10 LARGEST FILES ON THIS PHONE:")
    for f in all_files[:10]:
        print(f"  {format_size(f['size']):>10}  :  {f['path']}")

    # 6. Specific Deletable Summary
    cleanable_files = [f for ckey in ['screenshots', 'junk_cache', 'apks'] for f in categories[ckey]["files"]]
    cleanable_bytes = sum(f["size"] for f in cleanable_files)
    print("\n🧹 5. INSTANT CLEANABLE CANDIDATES:")
    print(f"  • Cleanable Screenshots & Junk: {len(cleanable_files):,} files ({format_size(cleanable_bytes)})")

if __name__ == "__main__":
    scan_device("UCWSUKMVHQUWXC8D")
