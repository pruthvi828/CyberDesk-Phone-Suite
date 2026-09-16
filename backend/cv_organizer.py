import os
import shutil
import re
import cv2
import numpy as np
from datetime import datetime
from PIL import Image, ExifTags

def extract_date_from_file(file_path):
    """Extract year and month from EXIF data, filename, or file mtime."""
    filename = os.path.basename(file_path)
    
    # 1. Try filename regex pattern (e.g. IMG_20180425_..., VID_20190526_..., img-20120323...)
    date_match = re.search(r'(20\d\d|19\d\d)[-_]?(0[1-9]|1[0-2])[-_]?(0[1-9]|[12]\d|3[01])', filename)
    if date_match:
        year, month, _ = date_match.groups()
        return year, f"{year}-{month}"

    # 2. Try EXIF metadata
    try:
        ext = os.path.splitext(filename)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.heic', '.webp']:
            with Image.open(file_path) as img:
                exif = img._getexif()
                if exif:
                    for tag_id, value in exif.items():
                        tag = ExifTags.TAGS.get(tag_id, tag_id)
                        if tag in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
                            # Format usually "YYYY:MM:DD HH:MM:SS"
                            dt = datetime.strptime(str(value)[:10], "%Y:%m:%d")
                            return str(dt.year), f"{dt.year}-{dt.month:02d}"
    except Exception:
        pass

    # 3. Fallback to file creation / modified time
    try:
        mtime = os.path.getmtime(file_path)
        dt = datetime.fromtimestamp(mtime)
        return str(dt.year), f"{dt.year}-{dt.month:02d}"
    except Exception:
        return "Unknown_Year", "Unknown_Month"

def analyze_image_cv(file_path):
    """
    Analyzes an image using OpenCV:
    - Computes blurriness score using Laplacian variance
    - Computes brightness and dimensions
    """
    try:
        # Read image
        img = cv2.imread(file_path)
        if img is None:
            return {"valid": False}

        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Laplacian variance for blur detection (higher = sharper, < 25 = blurry)
        blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
        is_blurry = blur_score < 20.0 and min(h, w) > 400

        # Mean brightness (0-255)
        brightness = float(np.mean(gray))

        return {
            "valid": True,
            "width": w,
            "height": h,
            "blur_score": round(float(blur_score), 2),
            "is_blurry": is_blurry,
            "brightness": round(brightness, 1)
        }
    except Exception:
        return {"valid": False}

def organize_pendrive(drive_path="E:\\", dry_run=False):
    print("=" * 60)
    print(f"  🧠 Computer Vision & Metadata Pen Drive Organizer")
    print("=" * 60)

    vault_root = os.path.join(drive_path, "Organized_Vault")
    photos_root = os.path.join(vault_root, "01_Photos")
    videos_root = os.path.join(vault_root, "02_Videos")
    edits_root = os.path.join(photos_root, "Edits_and_Creations")
    blurry_root = os.path.join(vault_root, "03_Blurry_Photos_Review")

    img_exts = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.raw', '.svg'}
    vid_exts = {'.mp4', '.mkv', '.avi', '.mov', '.wmv', '.3gp', '.flv', '.webm', '.m4v'}

    files_to_process = []
    for root, dirs, files in os.walk(drive_path):
        if "System Volume Information" in root or "Organized_Vault" in root:
            continue
        for f in files:
            files_to_process.append(os.path.join(root, f))

    print(f"🔍 Found {len(files_to_process)} media files to organize.\n")

    organized_count = 0
    blurry_count = 0
    videos_count = 0
    photos_count = 0

    plan = []

    for i, src_path in enumerate(files_to_process):
        filename = os.path.basename(src_path)
        ext = os.path.splitext(filename)[1].lower()
        src_lower = src_path.lower()

        year, month = extract_date_from_file(src_path)
        
        # Check if it's from Rajasthan Trip
        is_rajasthan = "rajasthan" in src_lower
        is_edit = "picture edit" in src_lower or "edit" in filename.lower()

        target_dir = None
        category = ""

        if ext in vid_exts:
            videos_count += 1
            if is_rajasthan:
                target_dir = os.path.join(videos_root, f"{year}_Rajasthan_Trip")
            else:
                target_dir = os.path.join(videos_root, year)
            category = "Video"

        elif ext in img_exts:
            photos_count += 1
            # Run CV Analysis
            cv_info = analyze_image_cv(src_path)
            
            if cv_info.get("is_blurry", False):
                blurry_count += 1
                target_dir = blurry_root
                category = "Blurry Photo"
            elif is_edit:
                target_dir = edits_root
                category = "Edited Photo"
            elif is_rajasthan:
                target_dir = os.path.join(photos_root, f"{year}_Rajasthan_Trip")
                category = "Photo (Trip)"
            else:
                target_dir = os.path.join(photos_root, year)
                category = "Photo"
        else:
            target_dir = os.path.join(vault_root, "04_Other_Files")
            category = "Other"

        dest_path = os.path.join(target_dir, filename)
        plan.append({
            "src": src_path,
            "dest": dest_path,
            "category": category,
            "year": year,
            "filename": filename
        })

    # Execute moves
    print(f"🚀 Organizing {len(plan)} files into systematic folders...")
    for item in plan:
        target_folder = os.path.dirname(item["dest"])
        os.makedirs(target_folder, exist_ok=True)
        
        # Handle collision
        dest = item["dest"]
        if os.path.exists(dest) and dest != item["src"]:
            base, ext = os.path.splitext(item["filename"])
            dest = os.path.join(target_folder, f"{base}_copy{ext}")

        if not dry_run:
            try:
                shutil.move(item["src"], dest)
                organized_count += 1
            except Exception as e:
                print(f"Error moving {item['src']}: {e}")

    # Remove old empty directories left behind
    for root, dirs, files in os.walk(drive_path, topdown=False):
        if "System Volume Information" in root or "Organized_Vault" in root or root == drive_path:
            continue
        try:
            if not os.listdir(root):
                os.rmdir(root)
        except Exception:
            pass

    print("\n" + "=" * 60)
    print(f"✨ Organization Complete! Successfully organized {organized_count} files:")
    print(f"  • 📸 Photos Organized:   {photos_count}")
    print(f"  • 🎥 Videos Organized:   {videos_count}")
    print(f"  • 🔍 Blurry Flagged:     {blurry_count} (placed in 03_Blurry_Photos_Review)")
    print("=" * 60)

if __name__ == "__main__":
    organize_pendrive("E:\\", dry_run=False)
