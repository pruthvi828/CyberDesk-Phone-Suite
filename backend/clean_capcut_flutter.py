import subprocess
import os

def run_adb(cmd):
    res = subprocess.run(['adb', 'shell'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
    return res.stdout

def run_adb_cmd(cmd):
    res = subprocess.run(['adb'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
    return res.stdout

def clean_selected():
    print("=== 1. CLEANING CAPCUT VIDEO EDITOR CACHE (947 MB) ===")
    out_capcut = run_adb(['rm', '-rf', '/sdcard/Android/data/com.lemon.lvoverseas/*'])
    print("CapCut cache wiped successfully.")

    print("\n=== 2. CLEANING 167 TEMP UI & EXPORT IMAGES IN /sdcard/Pictures/ ===")
    out_imgs = run_adb(['rm', '-f', '/sdcard/Pictures/file_00000000*'])
    print("167 temp export images deleted.")

    print("\n=== 3. UNINSTALLING UNUSED FLUTTER & TEST APPS ===")
    flutter_apps = [
        "com.codekaaru.attendancejack",
        "com.aistudio.fittrackpro.kzwxqy",
        "com.example.stu27",
        "com.example.stravaloop",
        "com.example.campus_os",
        "com.example.revo27",
        "com.example.redish27",
        "com.aistudio.fitcoach.vxqlyt",
        "com.example.revo_27",
        "com.aistudio.smartattendance.extc",
        "com.example.revoo27",
        "com.aistudio.deadlinetracker.app",
        "com.rovo27.rovo27_flutter",
        "com.aistudio.studentos.uwrks",
        "com.anonymous.ReVo27",
        "com.aistudio.academiccompanion.prvthv",
        "com.aistudio.splitshare.kvwzpt",
        "com.example.dtbm_treasure_hunt",
        "com.example.kollage"
    ]

    for pkg in flutter_apps:
        res = run_adb_cmd(['uninstall', pkg]).strip()
        print(f"Uninstalled {pkg}: {res}")

    print("\n=== 4. CURRENT STORAGE UPDATE ===")
    df = run_adb(['df', '-h', '/sdcard'])
    print(df.strip())

if __name__ == "__main__":
    clean_selected()
