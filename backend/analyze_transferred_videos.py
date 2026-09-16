import os
import cv2
import json

FOLDER = "E:\\Realme8_Phone_Videos"

def analyze():
    if not os.path.exists(FOLDER):
        print(f"Directory {FOLDER} does not exist.")
        return

    files = [os.path.join(FOLDER, f) for f in os.listdir(FOLDER) if os.path.isfile(os.path.join(FOLDER, f))]
    
    print(f"🔍 Analyzing {len(files)} videos in {FOLDER}...\n")

    analyzed = []
    for p in files:
        fname = os.path.basename(p)
        sz = os.path.getsize(p)
        sz_mb = sz / (1024 * 1024)

        cap = cv2.VideoCapture(p)
        if not cap.isOpened():
            analyzed.append({
                "path": p,
                "name": fname,
                "size_mb": round(sz_mb, 2),
                "duration": 0,
                "resolution": "Unknown",
                "category": "Corrupted / Unreadable",
                "reason": "Cannot open video stream"
            })
            continue

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = round(frame_count / fps, 1) if fps > 0 else 0
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        cap.release()

        # Categorize
        name_lower = fname.lower()
        if "blackhole" in name_lower or "_storage_emulated_0_" in name_lower:
            cat = "App Cache / Temporary Download"
            reason = "Blackhole app temporary/cached download"
        elif duration < 2.5 and sz_mb < 5.0:
            cat = "Accidental / 1-2s Empty Clip"
            reason = f"Extremely short clip ({duration}s, {sz_mb:.1f} MB)"
        elif duration < 4.0 and sz_mb < 8.0 and (w < 720 or h < 720):
            cat = "Low-Res Short Forward / Meme"
            reason = f"Low resolution ({w}x{h}) short clip ({duration}s)"
        elif "whatsapp" in name_lower or "vid_" in name_lower and (w < 1080 and h < 1080 and sz_mb < 15.0):
            cat = "WhatsApp Forward / Short Clip"
            reason = f"Low res WhatsApp forward ({w}x{h}, {duration}s)"
        elif fname.startswith("VID20") or fname.startswith("VID_20"):
            cat = "Camera Video Recording"
            reason = f"Full camera recording ({w}x{h}, {duration}s, {sz_mb:.1f} MB)"
        else:
            cat = "Other Video"
            reason = f"{w}x{h}, {duration}s, {sz_mb:.1f} MB"

        analyzed.append({
            "path": p,
            "name": fname,
            "size_mb": round(sz_mb, 2),
            "duration": duration,
            "resolution": f"{w}x{h}",
            "category": cat,
            "reason": reason
        })

    # Group by category
    categories = {}
    for item in analyzed:
        c = item["category"]
        if c not in categories:
            categories[c] = []
        categories[c].append(item)

    print("=" * 70)
    print("📊 Video Breakdown by Category:")
    print("=" * 70)
    for cat_name, items in categories.items():
        total_sz = sum(x["size_mb"] for x in items)
        print(f"\n📂 {cat_name} ({len(items)} files, {total_sz:.2f} MB):")
        for x in items[:15]:  # print first 15
            print(f"   • {x['name']} ({x['size_mb']} MB, {x['duration']}s, {x['resolution']}) - {x['reason']}")
        if len(items) > 15:
            print(f"   ... and {len(items)-15} more files.")

    # Save report
    with open("backend/video_analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, indent=2)

if __name__ == "__main__":
    analyze()
