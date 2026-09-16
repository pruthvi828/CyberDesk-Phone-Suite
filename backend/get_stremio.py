import urllib.request
import re
import subprocess
import os

DEV = "192.168.0.115:5555"

def main():
    print("🔍 1. Fetching latest official Stremio Android TV APK links...")
    url = "https://www.stremio.com/downloads"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='replace')

    # Look for ARM Android TV apk
    # Typically: https://dl.strem.io/android/v.../stremio-arm.apk or com.stremio.one...
    links = re.findall(r'href=[\'"]([^\'"]+stremio[^\'"]*android[^\'"]*\.apk|https://dl\.strem\.io/android/[^\'"]+\.apk)[\'"]', html, re.IGNORECASE)
    
    print(f"Found {len(links)} links:")
    tv_arm_link = None
    for link in links:
        print("  •", link)
        if "arm" in link.lower() and ("tv" in link.lower() or "one" in link.lower() or "android" in link.lower()):
            if "arm64" not in link.lower(): # Fire TV Stick is 32-bit ARM (armeabi-v7a)
                tv_arm_link = link
                break

    if not tv_arm_link and links:
        # Pick first 32-bit arm or general link
        for link in links:
            if "arm64" not in link.lower():
                tv_arm_link = link
                break

    if not tv_arm_link:
        # Fallback to standard known direct endpoint
        tv_arm_link = "https://dl.strem.io/android/1.6.12-arm/com.stremio.one-1.6.12-10049442.apk"

    print(f"\n🎯 Selected Target APK: {tv_arm_link}")

    dest_file = "backend/stremio_tv.apk"
    print(f"📥 2. Downloading Stremio Android TV APK...")
    req2 = urllib.request.Request(tv_arm_link, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req2) as r, open(dest_file, "wb") as f:
        f.write(r.read())

    sz_mb = os.path.getsize(dest_file) / (1024 * 1024)
    print(f"✅ Downloaded Stremio APK: {sz_mb:.2f} MB")

    print(f"🚀 3. Installing onto Fire TV Stick ({DEV}) via ADB...")
    subprocess.run(["adb", "connect", DEV])
    res = subprocess.run(["adb", "-s", DEV, "install", "-r", dest_file], capture_output=True, text=True)
    print("Installation Output:", res.stdout.strip())

    # Check installed package
    pkgs = subprocess.run(["adb", "-s", DEV, "shell", "pm", "list", "packages", "stremio"], capture_output=True, text=True).stdout
    print("Installed Stremio Package:\n", pkgs.strip())

    # Launch Stremio on TV
    print("🎬 4. Launching Stremio on Fire TV Screen...")
    subprocess.run(["adb", "-s", DEV, "shell", "monkey", "-p", "com.stremio.one", "-c", "android.intent.category.LAUNCHER", "1"])
    print("✨ Stremio is now LIVE on TV!")

if __name__ == "__main__":
    main()
