import urllib.request
import zipfile
import os
import shutil

SCRCPY_URL = "https://github.com/Genymobile/scrcpy/releases/download/v3.1/scrcpy-win64-v3.1.zip"
DEST_DIR = os.path.join("d:\\projects\\PHONE CLEAN\\backend", "scrcpy")
ZIP_PATH = os.path.join("d:\\projects\\PHONE CLEAN\\backend", "scrcpy.zip")

print("⚡ Downloading standalone scrcpy directly...")
headers = {'User-Agent': 'Mozilla/5.0'}
req = urllib.request.Request(SCRCPY_URL, headers=headers)

with urllib.request.urlopen(req) as resp, open(ZIP_PATH, 'wb') as out_file:
    shutil.copyfileobj(resp, out_file)

print("📦 Extracting scrcpy...")
with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
    zip_ref.extractall(DEST_DIR)

print("✅ Standalone scrcpy ready at:", DEST_DIR)
for root, dirs, files in os.walk(DEST_DIR):
    for f in files:
        if f.endswith(".exe"):
            print("Found executable:", os.path.join(root, f))
