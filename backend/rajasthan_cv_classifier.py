import os
import shutil
import re
import cv2
import numpy as np
from datetime import datetime
from PIL import Image

def get_hsv_features(image_path):
    """Extract color histogram and scene background features."""
    try:
        img = cv2.imread(image_path)
        if img is None:
            return None
        # Resize for consistent feature extraction
        img_resized = cv2.resize(img, (256, 256))
        hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)

        # 3D HSV Histogram (8 bins for H, 8 for S, 8 for V)
        hist = cv2.calcHist([hsv], [0, 1, 2], None, [8, 8, 8], [0, 180, 0, 256, 0, 256])
        cv2.normalize(hist, hist)
        hist_flat = hist.flatten()

        # Warm / Sandstone / Desert color ratio (Hue: 10-30, Sat: >40, Val: >50)
        sandstone_mask = cv2.inRange(hsv, np.array([10, 40, 50]), np.array([30, 255, 255]))
        sandstone_ratio = np.sum(sandstone_mask > 0) / (256 * 256)

        # Edge texture density (architectural details)
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_density = np.sum(edges > 0) / (256 * 256)

        return {
            "hist": hist_flat,
            "sandstone_ratio": sandstone_ratio,
            "edge_density": edge_density
        }
    except Exception:
        return None

def compute_similarity(feat1, feat2):
    """Compute histogram correlation and background color match score."""
    if feat1 is None or feat2 is None:
        return 0.0
    # Histogram correlation (-1 to 1)
    corr = cv2.compareHist(feat1["hist"].astype(np.float32), feat2["hist"].astype(np.float32), cv2.HISTCMP_CORREL)
    corr = max(0.0, corr)
    return corr

def classify_and_consolidate_rajasthan(drive_path="E:\\Organized_Vault"):
    print("=" * 60)
    print("   🏰 Computer Vision Rajasthan Photo & Scene Recognizer")
    print("=" * 60)

    target_photos_folder = os.path.join(drive_path, "01_Photos", "Rajasthan_Trip_Collection")
    target_videos_folder = os.path.join(drive_path, "02_Videos", "Rajasthan_Trip_Collection")
    os.makedirs(target_photos_folder, exist_ok=True)
    os.makedirs(target_videos_folder, exist_ok=True)

    # 1. Collect all known Rajasthan photos as ground truth references
    ref_features = []
    known_rajasthan_dirs = [
        os.path.join(drive_path, "01_Photos", "2019_Rajasthan_Trip"),
        os.path.join(drive_path, "01_Photos", "2020_Rajasthan_Trip"),
        os.path.join(drive_path, "01_Photos", "2008_Rajasthan_Trip"),
        os.path.join(drive_path, "01_Photos", "2009_Rajasthan_Trip")
    ]

    for d in known_rajasthan_dirs:
        if os.path.exists(d):
            for f in os.listdir(d):
                p = os.path.join(d, f)
                if os.path.isfile(p):
                    feat = get_hsv_features(p)
                    if feat:
                        ref_features.append(feat)

    print(f"📊 Extracted visual signatures from {len(ref_features)} known Rajasthan reference photos.\n")

    # 2. Scan all other photos and videos across the drive
    all_files = []
    for root, dirs, files in os.walk(drive_path):
        if "Rajasthan_Trip_Collection" in root:
            continue
        for f in files:
            all_files.append(os.path.join(root, f))

    print(f"🔍 Scanning all {len(all_files)} files on pen drive with Computer Vision...")

    matched_photos = []
    matched_videos = []

    vid_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.3gp'}

    for fpath in all_files:
        fname = os.path.basename(fpath)
        ext = os.path.splitext(fname)[1].lower()
        fpath_lower = fpath.lower()

        # Direct name/folder match
        is_rajasthan_name = "rajasthan" in fpath_lower or "raj" in fname.lower()
        
        # Check if video
        if ext in vid_exts:
            if is_rajasthan_name:
                matched_videos.append((fpath, 1.0, "Filename/Path Tag"))
            continue

        # Check photo via CV
        if is_rajasthan_name:
            matched_photos.append((fpath, 1.0, "Tag/Folder Match"))
            continue

        # Extract features and compare with Rajasthan reference cluster
        feat = get_hsv_features(fpath)
        if feat and ref_features:
            # Check maximum similarity with any reference photo
            max_sim = max(compute_similarity(feat, ref) for ref in ref_features[:40])
            
            # If high color & architectural similarity or high sandstone warm ratio
            if max_sim >= 0.72 or (feat["sandstone_ratio"] > 0.25 and max_sim >= 0.60):
                matched_photos.append((fpath, max_sim, f"CV Match ({max_sim*100:.1f}%)"))

    print(f"\n✨ Visual Analysis Results:")
    print(f"  • Found {len(matched_photos)} Rajasthan Photos")
    print(f"  • Found {len(matched_videos)} Rajasthan Videos\n")

    # 3. Consolidate into Rajasthan_Trip_Collection
    print("🚀 Grouping all Rajasthan media into dedicated album...")
    for src, score, reason in matched_photos:
        fname = os.path.basename(src)
        dest = os.path.join(target_photos_folder, fname)
        if os.path.exists(dest) and dest != src:
            base, ext = os.path.splitext(fname)
            dest = os.path.join(target_photos_folder, f"{base}_alt{ext}")
        shutil.move(src, dest)
        print(f"  [Moved Photo] {fname} ➔ ({reason})")

    for src, score, reason in matched_videos:
        fname = os.path.basename(src)
        dest = os.path.join(target_videos_folder, fname)
        if os.path.exists(dest) and dest != src:
            base, ext = os.path.splitext(fname)
            dest = os.path.join(target_videos_folder, f"{base}_alt{ext}")
        shutil.move(src, dest)
        print(f"  [Moved Video] {fname} ➔ ({reason})")

    # Clean empty old trip subfolders
    for d in known_rajasthan_dirs:
        try:
            if os.path.exists(d) and not os.listdir(d):
                os.rmdir(d)
        except Exception:
            pass

    # Clean videos old trip subfolders
    for d in [
        os.path.join(drive_path, "02_Videos", "2019_Rajasthan_Trip"),
        os.path.join(drive_path, "02_Videos", "2008_Rajasthan_Trip"),
        os.path.join(drive_path, "02_Videos", "2009_Rajasthan_Trip")
    ]:
        try:
            if os.path.exists(d) and not os.listdir(d):
                os.rmdir(d)
        except Exception:
            pass

    print("\n" + "=" * 60)
    print(f"🎉 Complete! All {len(matched_photos)} Photos and {len(matched_videos)} Videos are now in:")
    print(f"  📂 {target_photos_folder}")
    print(f"  📂 {target_videos_folder}")
    print("=" * 60)

if __name__ == "__main__":
    classify_and_consolidate_rajasthan("E:\\Organized_Vault")
