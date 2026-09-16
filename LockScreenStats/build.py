import os
import subprocess
import zipfile
import shutil

PROJECT_DIR = r"d:\projects\PHONE CLEAN\LockScreenStats"
SDK_DIR = r"C:\Users\Lenovo\AppData\Local\Android\Sdk"
BUILD_TOOLS = os.path.join(SDK_DIR, "build-tools", "35.0.0")
ANDROID_JAR = os.path.join(SDK_DIR, "platforms", "android-34", "android.jar")
JAVAC = r"C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\javac.exe"
KEYTOOL = r"C:\Program Files\Eclipse Adoptium\jdk-25.0.3.9-hotspot\bin\keytool.exe"

AAPT2 = os.path.join(BUILD_TOOLS, "aapt2.exe")
D8 = os.path.join(BUILD_TOOLS, "d8.bat")
ZIPALIGN = os.path.join(BUILD_TOOLS, "zipalign.exe")
APKSIGNER = os.path.join(BUILD_TOOLS, "apksigner.bat")

os.chdir(PROJECT_DIR)

# Clean and recreate build dirs
for d in ["build", "gen", "obj", "dex_out"]:
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d)

print("1. Compiling resources with aapt2...")
cmd_compile = [AAPT2, "compile", "--dir", "res", "-o", "build/res.zip"]
res = subprocess.run(cmd_compile, capture_output=True, text=True)
print(res.stdout, res.stderr)
if res.returncode != 0:
    raise RuntimeError("aapt2 compile failed")

print("2. Linking resources with aapt2...")
cmd_link = [
    AAPT2, "link",
    "-o", "build/base.apk",
    "-I", ANDROID_JAR,
    "--manifest", "AndroidManifest.xml",
    "--java", "gen",
    "build/res.zip",
    "--auto-add-overlay"
]
res = subprocess.run(cmd_link, capture_output=True, text=True)
print(res.stdout, res.stderr)
if res.returncode != 0:
    raise RuntimeError("aapt2 link failed")

print("3. Collecting Java sources...")
java_files = []
for root, _, files in os.walk("src"):
    for f in files:
        if f.endswith(".java"):
            java_files.append(os.path.join(root, f))
for root, _, files in os.walk("gen"):
    for f in files:
        if f.endswith(".java"):
            java_files.append(os.path.join(root, f))
print(f"Found {len(java_files)} Java files: {java_files}")

print("4. Compiling Java with javac...")
cmd_javac = [
    JAVAC,
    "-d", "obj",
    "-cp", ANDROID_JAR,
    "-source", "1.8",
    "-target", "1.8"
] + java_files
res = subprocess.run(cmd_javac, capture_output=True, text=True)
print(res.stdout, res.stderr)
if res.returncode != 0:
    raise RuntimeError("javac failed")

print("5. D8 Dexing...")
class_files = []
for root, _, files in os.walk("obj"):
    for f in files:
        if f.endswith(".class"):
            class_files.append(os.path.join(root, f))

cmd_d8 = [
    D8,
    "--output", "dex_out",
    "--lib", ANDROID_JAR
] + class_files
res = subprocess.run(cmd_d8, capture_output=True, text=True, shell=True)
print(res.stdout, res.stderr)
if res.returncode != 0:
    raise RuntimeError("d8 failed")

print("6. Packaging classes.dex into APK...")
# Copy base.apk to unsigned.apk
shutil.copy("build/base.apk", "build/unsigned.apk")
with zipfile.ZipFile("build/unsigned.apk", "a") as z:
    z.write("dex_out/classes.dex", "classes.dex")

print("7. Zipaligning APK...")
cmd_zipalign = [
    ZIPALIGN,
    "-p", "-f", "-v", "4",
    "build/unsigned.apk",
    "build/aligned.apk"
]
res = subprocess.run(cmd_zipalign, capture_output=True, text=True)
if res.returncode != 0:
    print(res.stderr)
    raise RuntimeError("zipalign failed")

print("8. Checking debug keystore...")
keystore = "debug.keystore"
if not os.path.exists(keystore):
    print("Generating debug keystore...")
    cmd_keytool = [
        KEYTOOL, "-genkeypair",
        "-keystore", keystore,
        "-storepass", "android",
        "-alias", "androiddebugkey",
        "-keypass", "android",
        "-dname", "CN=Android Debug,O=Android,C=US",
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "10000"
    ]
    subprocess.run(cmd_keytool, check=True)

print("9. Signing APK with apksigner...")
cmd_sign = [
    APKSIGNER, "sign",
    "--ks", keystore,
    "--ks-pass", "pass:android",
    "--key-pass", "pass:android",
    "--out", "build/LockScreenStats.apk",
    "build/aligned.apk"
]
res = subprocess.run(cmd_sign, capture_output=True, text=True, shell=True)
print(res.stdout, res.stderr)
if res.returncode != 0:
    raise RuntimeError("apksigner failed")

print("SUCCESS! Output APK: build/LockScreenStats.apk")
