import os

def clean_pendrive(drive_path="E:\\"):
    print("=== 1. REMOVING DUPLICATE IMAGES ===")
    duplicate_file = os.path.join(drive_path, "rajasthan", "Rajasthan", "IMG_20180126_183928.jpg")
    if os.path.exists(duplicate_file):
        os.remove(duplicate_file)
        print(f"✅ Removed duplicate file: {duplicate_file}")
    else:
        print("Duplicate file not found or already removed.")

    print("\n=== 2. REMOVING EMPTY DIRECTORIES ===")
    removed_dirs = 0
    # Walk bottom-up to delete nested empty folders
    for root, dirs, files in os.walk(drive_path, topdown=False):
        if root == drive_path:
            continue
        try:
            # If folder has no files and no subdirectories
            if not os.listdir(root):
                os.rmdir(root)
                print(f"🗑️ Removed empty folder: {root}")
                removed_dirs += 1
        except Exception as e:
            print(f"Error removing {root}: {e}")

    print(f"\n✅ Finished! Removed {removed_dirs} empty folders.")

if __name__ == "__main__":
    clean_pendrive("E:\\")
