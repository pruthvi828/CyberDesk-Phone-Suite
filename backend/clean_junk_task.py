from backend.adb_manager import ADBManager
from backend.scanner import FileScanner
from backend.cleaner import SafeOperationsManager

def clean_junk():
    adb = ADBManager()
    scanner = FileScanner(adb)
    ops = SafeOperationsManager(adb)

    print("1. Scanning phone storage...")
    res = scanner.scan_adb_device()

    targets = []
    for k in ["junk_cache", "apks"]:
        if k in res.categories:
            targets.extend(res.categories[k]["files"])

    print(f"2. Found {len(targets)} thumbnails and junk files.")
    if targets:
        result = ops.clean_files(targets, source_type="adb", dry_run=False)
        print(f"✅ Cleaned: {result['deleted_count']} files. Freed: {result['freed_formatted']}")
    else:
        print("No junk files remaining.")

if __name__ == "__main__":
    clean_junk()
