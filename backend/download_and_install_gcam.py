import urllib.request
import os
import subprocess
import sys

DEV_ID = "VWGYW4SGJNYLEYQG"
APK_URL = "https://1-dontsharethislink.celsoazevedo.com/file/filesc/MGC_9.6.080_V48_snap.apk"
OUT_PATH = os.path.join("d:\\projects\\PHONE CLEAN\\backend", "GCam_BSG_9.6_snap.apk")

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://www.celsoazevedo.com/'
}

print(f"📥 1. Downloading GCam BSG 9.6 (Snapcam build) from:\n   {APK_URL}")
req = urllib.request.Request(APK_URL, headers=headers)

with urllib.request.urlopen(req, timeout=60) as resp:
    total_size = int(resp.headers.get('content-length', 0))
    print(f"   Size: {total_size / (1024*1024):.2f} MB")
    
    downloaded = 0
    chunk_size = 1024 * 512
    with open(OUT_PATH, 'wb') as f:
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            f.write(chunk)
            downloaded += len(chunk)
            pct = (downloaded / total_size * 100) if total_size else 0
            sys.stdout.write(f"\r   Progress: {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({pct:.1f}%)")
            sys.stdout.flush()

print(f"\n✅ Download complete: {OUT_PATH}")

print("\n📲 2. Installing GCam to Realme phone via ADB...")
res = subprocess.run(['adb', '-s', DEV_ID, 'install', '-r', '-g', OUT_PATH], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
print("STDOUT:", res.stdout.strip())
print("STDERR:", res.stderr.strip())

if "Success" in res.stdout:
    print("🎉 Successfully installed Google Camera (GCam) on your phone!")
else:
    print("⚠️ ADB install finished with result above.")
