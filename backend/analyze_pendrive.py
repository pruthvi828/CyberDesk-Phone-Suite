import os
import hashlib
from collections import defaultdict

def format_size(size_bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def analyze_drive(drive_path="E:\\"):
    print(f"==================================================")
    print(f"      🔍 Deep Analysis of Pen Drive ({drive_path})")
    print(f"==================================================\n")

    if not os.path.exists(drive_path):
        print(f"❌ Drive {drive_path} not found!")
        return

    total_files = 0
    total_bytes = 0
    empty_folders = []
    non_empty_folders_count = 0

    category_stats = defaultdict(lambda: {"count": 0, "bytes": 0, "files": []})
    largest_files = []
    potential_junk_files = []

    # File extensions
    doc_exts = {'.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.csv'}
    img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.raw', '.svg'}
    vid_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.3gp', '.flv', '.webm', '.m4v'}
    aud_exts = {'.mp3', '.wav', '.m4a', '.aac', '.flac', '.ogg', '.opus'}
    arc_exts = {'.zip', '.rar', '.7z', '.tar', '.gz', '.iso', '.img'}
    app_exts = {'.exe', '.msi', '.apk', '.bat', '.cmd', '.ps1'}
    code_exts = {'.py', '.js', '.html', '.css', '.cpp', '.c', '.java', '.json', '.xml', '.sql'}
    junk_names = {'thumbs.db', '.ds_store', 'desktop.ini', 'autorun.inf', '$recycle.bin'}

    # Walk directory
    for root, dirs, files in os.walk(drive_path):
        # Check empty directory
        if not dirs and not files:
            empty_folders.append(root)
        else:
            if root != drive_path:
                non_empty_folders_count += 1

        for f in files:
            full_path = os.path.join(root, f)
            total_files += 1
            try:
                size = os.path.getsize(full_path)
            except Exception:
                size = 0

            total_bytes += size
            name_lower = f.lower()
            _, ext = os.path.splitext(name_lower)

            # Categorize
            if name_lower in junk_names or ext in ['.tmp', '.log', '.bak', '.chk'] or 'system volume information' in full_path.lower():
                cat = "Junk & System Artifacts"
                potential_junk_files.append((size, full_path))
            elif ext in doc_exts:
                cat = "Documents & Spreadsheets"
            elif ext in vid_exts:
                cat = "Video Files"
            elif ext in img_exts:
                cat = "Photos & Images"
            elif ext in aud_exts:
                cat = "Audio & Music"
            elif ext in arc_exts:
                cat = "Archives & Disk Images (ZIP/ISO)"
            elif ext in app_exts:
                cat = "Installers & Executables (EXE/APK)"
            elif ext in code_exts:
                cat = "Code & Developer Projects"
            else:
                cat = "Other / Miscellaneous Files"

            category_stats[cat]["count"] += 1
            category_stats[cat]["bytes"] += size
            category_stats[cat]["files"].append((size, full_path))
            largest_files.append((size, full_path))

    largest_files.sort(reverse=True)
    potential_junk_files.sort(reverse=True)

    print(f"📊 SUMMARY OVERVIEW:")
    print(f"  • Total Used Space: {format_size(total_bytes)}")
    print(f"  • Total Files:      {total_files:,}")
    print(f"  • Total Folders:    {len(empty_folders) + non_empty_folders_count:,}")
    print(f"  • Empty Folders:    {len(empty_folders):,} (Zero files inside)\n")

    print(f"📁 DATA BREAKDOWN BY CATEGORY:")
    for cat, data in sorted(category_stats.items(), key=lambda x: x[1]["bytes"], reverse=True):
        print(f"  • {cat:<36} : {data['count']:>5} files ({format_size(data['bytes']):>10})")

    print(f"\n📂 EMPTY FOLDERS FOUND ({len(empty_folders)} total):")
    if empty_folders:
        for ef in empty_folders[:20]:
            print(f"    [Empty] {ef}")
        if len(empty_folders) > 20:
            print(f"    ... and {len(empty_folders) - 20} more empty directories.")
    else:
        print("    None! No empty folders found.")

    print(f"\n🏆 TOP 15 LARGEST FILES ON PEN DRIVE:")
    for sz, p in largest_files[:15]:
        print(f"  {format_size(sz):>10}  :  {p}")

    junk_bytes = sum(j[0] for j in potential_junk_files)
    print(f"\n🧹 POTENTIAL JUNK & CLEARABLE DEBRIS:")
    print(f"  • Found {len(potential_junk_files)} junk files ({format_size(junk_bytes)})")
    print(f"  • Found {len(empty_folders)} empty folders ready to be cleaned")

if __name__ == "__main__":
    analyze_drive("E:\\")
