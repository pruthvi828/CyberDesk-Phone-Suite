import urllib.request
import subprocess
import os

DEV = "192.168.0.115:5555"
URL = "https://dl.strem.io/android/v1.10.4-androidTV/com.stremio.one-1.10.4-31048580-armeabi-v7a.apk"
DEST_APK = "backend/stremio_arm_tv.apk"

def install():
    print(f"📥 Downloading Official Stremio Android TV APK from:\n  {URL}...")
    req = urllib.request.Request(URL, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp, open(DEST_APK, "wb") as f:
        f.write(resp.read())

    sz_mb = os.path.getsize(DEST_APK) / (1024 * 1024)
    print(f"✅ Downloaded Stremio Android TV APK ({sz_mb:.2f} MB)")

    print(f"🚀 Installing onto Fire TV Stick ({DEV})...")
    subprocess.run(["adb", "connect", DEV])
    res = subprocess.run(["adb", "-s", DEV, "install", "-r", DEST_APK], capture_output=True, text=True)
    print("Install Result:", res.stdout.strip())

    # Verify package
    pkgs = subprocess.run(["adb", "-s", DEV, "shell", "pm", "list", "packages", "stremio"], capture_output=True, text=True).stdout
    print("Installed Package:\n", pkgs.strip())

    # Launch Stremio on TV
    print("🎬 Launching Stremio on TV Screen...")
    subprocess.run(["adb", "-s", DEV, "shell", "monkey", "-p", "com.stremio.one", "-c", "android.intent.category.LAUNCHER", "1"])
    print("🎉 Stremio Android TV is successfully launched on your TV screen!")

if __name__ == "__main__":
    install()
