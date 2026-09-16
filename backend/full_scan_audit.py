import subprocess
import os

def run_adb(cmd):
    res = subprocess.run(['adb', 'shell'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
    return res.stdout

def full_audit():
    print("=== 1. SCREENSHOTS & CAMERA BURST SHOTS ===")
    for d in ['/sdcard/Pictures/Screenshots', '/sdcard/DCIM/Screenshots', '/sdcard/DCIM/Camera/Cshot']:
        out = run_adb(['du', '-sh', d]).strip()
        print(f"{d:<40} : {out}")

    print("\n=== 2. WHATSAPP MEDIA CLUTTER ===")
    wa_base = '/sdcard/Android/media/com.whatsapp/WhatsApp/Media'
    for sub in ['WhatsApp Video/Sent', 'WhatsApp Images/Sent', 'WhatsApp Animated Gifs', 'WhatsApp Audio/Sent', 'WhatsApp Voice Notes', 'WhatsApp Stickers', 'WhatsApp Video', 'WhatsApp Images']:
        full_p = f"{wa_base}/{sub}"
        out = run_adb(['du', '-sh', full_p]).strip()
        print(f"{sub:<35} : {out}")

    print("\n=== 3. APP RESIDUAL DATA & OFFLINE CACHES ON STORAGE ===")
    apps = [
        ('Adobe Lightroom Mobile Cache/Edits', 'com.adobe.lrmobile'),
        ('CapCut Video Editor Cache/Drafts', 'com.lemon.lvoverseas'),
        ('Chrome Cache & Offline Storage', 'com.android.chrome'),
        ('Facebook App Manager Debris', 'com.facebook.appmanager'),
        ('TeraBox Offline Storage', 'com.dubox.drive'),
        ('Grok App Cache', 'ai.x.grok'),
        ('Strava Cache', 'com.strava'),
        ('Telegram Messenger Cache', 'org.telegram.messenger'),
        ('Canva Editor Cache', 'com.canva.editor'),
        ('Snapchat Local Storage', 'com.snapchat.android')
    ]
    for label, pkg in apps:
        p = f"/sdcard/Android/data/{pkg}"
        out = run_adb(['du', '-sh', p]).strip()
        print(f"{label:<38} ({pkg}) : {out}")

    print("\n=== 4. OTHER USER FOLDERS ===")
    for d in ['/sdcard/Movies', '/sdcard/Pictures', '/sdcard/Music', '/sdcard/Documents']:
        out = run_adb(['du', '-sh', d]).strip()
        print(f"{d:<35} : {out}")

    print("\n=== 5. UNUSED DEVELOPMENT / TEST APKS INSTALLED ===")
    out_pkgs = run_adb(['pm', 'list', 'packages', '-3'])
    test_pkgs = []
    for line in out_pkgs.splitlines():
        p = line.replace('package:', '').strip()
        if any(p.startswith(prefix) for prefix in ['com.example.', 'com.aistudio.', 'com.rovo27.', 'com.anonymous.', 'com.codekaaru.']):
            test_pkgs.append(p)
    print(f"Found {len(test_pkgs)} test/flutter app packages:")
    for tp in test_pkgs:
        print(f"  • {tp}")

if __name__ == "__main__":
    full_audit()
