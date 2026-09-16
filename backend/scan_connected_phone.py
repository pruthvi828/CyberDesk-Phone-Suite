import subprocess
import json
import re

DEV_ID = "VWGYW4SGJNYLEYQG"

def run_adb(cmd):
    res = subprocess.run(['adb', '-s', DEV_ID, 'shell'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
    return res.stdout.strip()

def get_prop(prop_name):
    return run_adb(['getprop', prop_name])

def get_setting(namespace, key):
    return run_adb(['settings', 'get', namespace, key])

def main():
    report = {}
    
    # Basic Specs
    report["brand"] = get_prop("ro.product.brand")
    report["manufacturer"] = get_prop("ro.product.manufacturer")
    report["model"] = get_prop("ro.product.model")
    report["market_name"] = get_prop("ro.product.marketname") or get_prop("ro.vendor.product.display")
    report["device"] = get_prop("ro.product.device")
    report["board"] = get_prop("ro.board.platform")
    report["chipset"] = get_prop("ro.soc.model") or get_prop("ro.chipname") or report["board"]
    report["android_version"] = get_prop("ro.build.version.release")
    report["sdk_version"] = get_prop("ro.build.version.sdk")
    report["security_patch"] = get_prop("ro.build.version.security_patch")
    report["build_id"] = get_prop("ro.build.display.id")
    report["realme_ui_ver"] = get_prop("ro.build.version.opporom") or get_prop("ro.rom.different.version") or get_prop("ro.build.version.oplusrom")
    report["cpu_abi"] = get_prop("ro.product.cpu.abi")

    # Display
    report["wm_size"] = run_adb(['wm', 'size'])
    report["wm_density"] = run_adb(['wm', 'density'])
    
    # Refresh rate
    display_info = run_adb(['dumpsys', 'display'])
    refresh_rates = re.findall(r'(\d+(?:\.\d+)?)\s*fps', display_info, re.IGNORECASE)
    if not refresh_rates:
        refresh_rates = re.findall(r'(\d+(?:\.\d+)?)\s*Hz', display_info, re.IGNORECASE)
    report["refresh_rates_found"] = sorted(list(set(refresh_rates)), key=lambda x: float(x) if x.replace('.','',1).isdigit() else 0, reverse=True)[:5]
    
    # RAM & Swap / ZRAM
    meminfo = run_adb(['cat', '/proc/meminfo'])
    for line in meminfo.splitlines():
        if "MemTotal:" in line:
            report["mem_total_kb"] = int(line.split()[1])
        elif "MemAvailable:" in line:
            report["mem_avail_kb"] = int(line.split()[1])
        elif "SwapTotal:" in line:
            report["swap_total_kb"] = int(line.split()[1])
        elif "SwapFree:" in line:
            report["swap_free_kb"] = int(line.split()[1])

    # CPU Cores
    cpuinfo = run_adb(['cat', '/proc/cpuinfo'])
    cores = len(re.findall(r'^processor\s*:', cpuinfo, re.MULTILINE))
    report["cpu_cores"] = cores

    # Battery
    battery_raw = run_adb(['dumpsys', 'battery'])
    batt = {}
    for line in battery_raw.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            batt[k.strip()] = v.strip()
    report["battery"] = batt

    # Storage
    df_out = run_adb(['df', '-h', '/data', '/sdcard'])
    report["storage_df"] = df_out

    # Developer settings current state
    report["dev_options_enabled"] = get_setting("global", "development_settings_enabled")
    report["window_anim"] = get_setting("global", "window_animation_scale")
    report["transition_anim"] = get_setting("global", "transition_animation_scale")
    report["animator_duration"] = get_setting("global", "animator_duration_scale")
    report["smallest_width"] = get_setting("secure", "display_density_forced")

    # Bloatware / Packages Scan
    all_packages = run_adb(['pm', 'list', 'packages']).splitlines()
    pkg_clean = [p.replace("package:", "").strip() for p in all_packages if p.strip()]
    report["total_packages"] = len(pkg_clean)
    
    # Known Realme / ColorOS / Oppo bloatware check
    known_bloat_signatures = [
        "com.heytap.browser",
        "com.heytap.market",
        "com.heytap.pictorial", # Lock screen magazine / ads
        "com.heytap.themestore",
        "com.heytap.cloud",
        "com.heytap.music",
        "com.heytap.accessory",
        "com.oppo.market",
        "com.coloros.gamespace",
        "com.coloros.floatassistant",
        "com.coloros.smartdrive",
        "com.coloros.video",
        "com.coloros.compass2",
        "com.glance.lockscreen",
        "com.finshell.fin",
        "com.facebook.katana",
        "com.facebook.system",
        "com.facebook.appmanager",
        "com.facebook.services",
        "com.google.android.apps.tachyon", # Meet
        "com.google.android.apps.subscriptions.red", # Google One
        "com.google.android.youtube",
        "com.snapchat.android",
        "com.netflix.mediaclient",
        "com.amazon.mShop.android.shopping"
    ]
    detected_bloat = [p for p in pkg_clean if any(sig in p for sig in known_bloat_signatures)]
    report["detected_target_bloat"] = detected_bloat

    # 3rd party apps
    third_party = run_adb(['pm', 'list', 'packages', '-3']).splitlines()
    report["third_party_count"] = len(third_party)
    report["third_party_sample"] = [p.replace("package:", "").strip() for p in third_party[:15]]

    print(json.dumps(report, indent=2))

if __name__ == "__main__":
    main()
