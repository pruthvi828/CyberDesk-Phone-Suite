import subprocess
import os
import sys
import time
import json

def run_adb(device_ip, cmd):
    dev = f"{device_ip}:5555" if ":" not in device_ip else device_ip
    full_cmd = ['adb', '-s', dev, 'shell'] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True, errors='replace')
    return res.stdout.strip()

def connect_firetv(device_ip):
    target = f"{device_ip}:5555" if ":" not in device_ip else device_ip
    print(f"📡 Connecting to Fire TV Stick at {target}...")
    res = subprocess.run(['adb', 'connect', target], capture_output=True, text=True)
    out = res.stdout.strip()
    print(f"  • Result: {out}")
    time.sleep(1)
    
    # Check devices
    devs = subprocess.run(['adb', 'devices'], capture_output=True, text=True).stdout
    if target in devs and "device" in devs:
        return True, "Connected successfully"
    elif "unauthorized" in devs:
        return False, "Unauthorized! Please click 'Always Allow' prompt on your TV screen using remote."
    else:
        return False, f"Could not connect: {out}"

def diagnose(device_ip):
    print("=" * 70)
    print("   🔥 AMAZON FIRE TV STICK FULL SYSTEM DIAGNOSTIC")
    print("=" * 70)

    target = f"{device_ip}:5555" if ":" not in device_ip else device_ip
    
    ok, msg = connect_firetv(device_ip)
    if not ok:
        print(f"\n❌ Connection Error: {msg}")
        return

    print("\n✅ Connected! Gathering hardware & OS telemetry...\n")

    # 1. Device Info
    model = run_adb(target, ['getprop', 'ro.product.model'])
    brand = run_adb(target, ['getprop', 'ro.product.brand'])
    fireos_ver = run_adb(target, ['getprop', 'ro.build.version.name'])
    android_ver = run_adb(target, ['getprop', 'ro.build.version.release'])
    sdk = run_adb(target, ['getprop', 'ro.build.version.sdk'])

    print(f"📱 Model: {brand} {model}")
    print(f"⚙️ OS: Fire OS {fireos_ver} (Android {android_ver}, API {sdk})")

    # 2. Storage
    print("\n💾 1. Storage Status:")
    df_out = run_adb(target, ['df', '-h', '/data'])
    for line in df_out.splitlines():
        if '/data' in line or 'Filesystem' in line:
            print(f"   {line}")

    # 3. RAM & Memory
    print("\n🧠 2. Memory & RAM Allocation:")
    meminfo = run_adb(target, ['cat', '/proc/meminfo'])
    mem_dict = {}
    for line in meminfo.splitlines():
        parts = line.split(':')
        if len(parts) == 2:
            mem_dict[parts[0].strip()] = parts[1].strip()
    
    total_ram = mem_dict.get('MemTotal', 'N/A')
    free_ram = mem_dict.get('MemFree', 'N/A')
    avail_ram = mem_dict.get('MemAvailable', 'N/A')
    cached_ram = mem_dict.get('Cached', 'N/A')
    print(f"   • Total RAM: {total_ram}")
    print(f"   • Available RAM: {avail_ram} (Free: {free_ram}, Cached: {cached_ram})")

    # 4. Top Installed Streaming & 3rd Party Apps
    print("\n📺 3. Installed Streaming & 3rd Party Apps:")
    packages = run_adb(target, ['pm', 'list', 'packages', '-3'])
    pkg_list = [p.replace('package:', '').strip() for p in packages.splitlines() if p.strip()]
    
    streaming_apps = {
        'com.amazon.firetv.youtube': 'YouTube on Fire TV',
        'com.google.android.youtube.tv': 'YouTube TV',
        'com.netflix.ninja': 'Netflix',
        'com.jio.media.ondemand': 'JioCinema',
        'in.startv.hotstar': 'Disney+ Hotstar',
        'com.graymatrix.did': 'Zee5',
        'com.sonyliv': 'SonyLIV',
        'org.xbmc.kodi': 'Kodi Media Center',
        'com.mxtech.videoplayer.ad': 'MX Player',
        'tv.smartstube': 'SmartTube',
    }

    found_streamers = []
    for pkg in pkg_list:
        name = streaming_apps.get(pkg, pkg)
        found_streamers.append((pkg, name))
        print(f"   • {name} ({pkg})")

    print(f"\n   Total 3rd-party/user packages installed: {len(pkg_list)}")

    # 5. App Cache Footprint (Top Space Consumers)
    print("\n🧹 4. App Cache Audit (Potential Space Savers):")
    cache_dirs = run_adb(target, ['ls', '-ld', '/sdcard/Android/data/*/cache'])
    # Check /sdcard/Android/data
    data_usage = run_adb(target, ['du', '-sh', '/sdcard/Android/data/*'])
    has_cache = False
    for line in data_usage.splitlines():
        if line.strip() and not 'Permission denied' in line:
            print(f"   • {line.strip()}")
            has_cache = True
    if not has_cache:
        print("   • Standard external cache is clean.")

    # 6. Thermal & Temperature Check
    print("\n🌡️ 5. Thermal & Processor Status:")
    thermal_out = run_adb(target, ['cat', '/sys/class/thermal/thermal_zone0/temp'])
    try:
        temp_c = int(thermal_out.strip()) / 1000.0 if len(thermal_out.strip()) > 3 else int(thermal_out.strip())
        print(f"   • CPU Temperature: {temp_c:.1f}°C")
        if temp_c > 75:
            print("   ⚠️ Warning: Fire TV is running hot! May cause UI lag/buffering.")
        else:
            print("   ✅ Temperature is within normal operating range.")
    except Exception:
        print(f"   • Thermal reading: {thermal_out or 'Normal'}")

    print("\n" + "=" * 70)
    print("🎯 DIAGNOSTIC COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ip = sys.argv[1]
    else:
        ip = input("Enter Fire TV Stick IP address (e.g. 192.168.0.xxx): ").strip()
    
    if ip:
        diagnose(ip)
    else:
        print("No IP address provided.")
