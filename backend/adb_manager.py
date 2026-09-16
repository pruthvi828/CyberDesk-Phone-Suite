import os
import re
import subprocess
import shutil
import time
from typing import List, Dict, Any, Optional, Tuple


class ADBManager:
    """Manages ADB connectivity, device querying, file scanning, backup, and cleanup."""

    def __init__(self, adb_path: str = "adb"):
        self.adb_path = shutil.which(adb_path) or adb_path
        self.current_device_id: Optional[str] = None

    def is_adb_installed(self) -> bool:
        """Check if ADB executable is accessible in PATH."""
        try:
            res = subprocess.run([self.adb_path, "version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False

    def get_devices(self) -> List[Dict[str, Any]]:
        """List attached devices with their state and properties."""
        devices = []
        try:
            res = subprocess.run([self.adb_path, "devices", "-l"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
            lines = res.stdout.strip().splitlines()
            for line in lines[1:]:
                line = line.strip()
                if not line or line.startswith("*"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    device_id = parts[0]
                    state = parts[1]  # 'device', 'unauthorized', 'offline'
                    
                    # Extract metadata from key:value pairs like model:Pixel_7 product:panther
                    metadata = {}
                    for item in parts[2:]:
                        if ':' in item:
                            k, v = item.split(':', 1)
                            metadata[k] = v
                    
                    devices.append({
                        "id": device_id,
                        "state": state,
                        "model": metadata.get("model", "Android Device"),
                        "device": metadata.get("device", ""),
                        "product": metadata.get("product", "")
                    })
        except Exception as e:
            print(f"Error fetching ADB devices: {e}")
        return devices

    def select_device(self, device_id: Optional[str] = None) -> bool:
        """Select active device. If None, picks the first authorized device."""
        devices = self.get_devices()
        if not devices:
            self.current_device_id = None
            return False
        
        if device_id:
            for d in devices:
                if d["id"] == device_id and d["state"] == "device":
                    self.current_device_id = device_id
                    return True
            return False

        # Pick first ready device
        for d in devices:
            if d["state"] == "device":
                self.current_device_id = d["id"]
                return True
        
        # If all unauthorized or offline, select first anyway
        self.current_device_id = devices[0]["id"]
        return False

    def run_cmd(self, args: List[str], timeout: int = 30) -> Tuple[int, str, str]:
        """Run ADB command targeting current selected device."""
        if not self.current_device_id:
            self.select_device()

        cmd = [self.adb_path]
        if self.current_device_id:
            cmd.extend(["-s", self.current_device_id])
        cmd.extend(args)

        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout, errors='replace')
            return res.returncode, res.stdout, res.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)

    def get_device_details(self) -> Dict[str, Any]:
        """Fetch battery, storage, brand, model, and OS version."""
        if not self.current_device_id:
            devices = self.get_devices()
            if devices:
                self.select_device()
            else:
                return {"connected": False, "reason": "No device attached"}

        # Check authorization
        devs = self.get_devices()
        cur = next((d for d in devs if d["id"] == self.current_device_id), None)
        if not cur:
            return {"connected": False, "reason": "Device disconnected"}
        if cur["state"] == "unauthorized":
            return {
                "connected": False,
                "state": "unauthorized",
                "id": self.current_device_id,
                "reason": "Please check your phone screen and tap 'Allow USB Debugging'."
            }
        if cur["state"] != "device":
            return {
                "connected": False,
                "state": cur["state"],
                "id": self.current_device_id,
                "reason": f"Device is in {cur['state']} state."
            }

        # Model and Brand
        _, brand, _ = self.run_cmd(["shell", "getprop", "ro.product.brand"])
        _, model, _ = self.run_cmd(["shell", "getprop", "ro.product.model"])
        _, android_ver, _ = self.run_cmd(["shell", "getprop", "ro.build.version.release"])
        _, sdk_ver, _ = self.run_cmd(["shell", "getprop", "ro.build.version.sdk"])

        # Storage info via df /sdcard or df /data
        _, df_out, _ = self.run_cmd(["shell", "df", "-k", "/sdcard"])
        storage_total_kb = 0
        storage_used_kb = 0
        storage_avail_kb = 0
        
        for line in df_out.splitlines():
            parts = line.split()
            if len(parts) >= 6 and (parts[0].startswith('/dev') or parts[-1].endswith('/sdcard') or parts[-1].endswith('/emulated')):
                try:
                    storage_total_kb = int(parts[1])
                    storage_used_kb = int(parts[2])
                    storage_avail_kb = int(parts[3])
                    break
                except ValueError:
                    pass

        # Battery
        _, batt_out, _ = self.run_cmd(["shell", "dumpsys", "battery"])
        battery_level = 0
        for line in batt_out.splitlines():
            if "level:" in line:
                try:
                    battery_level = int(line.split("level:")[1].strip())
                except ValueError:
                    pass

        return {
            "connected": True,
            "state": "ready",
            "id": self.current_device_id,
            "brand": brand.strip().capitalize() if brand else "Android",
            "model": model.strip() if model else "Smartphone",
            "android_version": android_ver.strip() if android_ver else "Unknown",
            "sdk_version": sdk_ver.strip() if sdk_ver else "Unknown",
            "battery": battery_level,
            "storage": {
                "total_bytes": storage_total_kb * 1024,
                "used_bytes": storage_used_kb * 1024,
                "free_bytes": storage_avail_kb * 1024,
                "used_percent": round((storage_used_kb / max(storage_total_kb, 1)) * 100, 1)
            }
        }

    def scan_storage_files(self, progress_callback=None) -> List[Dict[str, Any]]:
        """
        Scans all files in internal storage (/sdcard/).
        Uses efficient shell commands to collect path, size, and modification timestamp.
        """
        if not self.current_device_id:
            return []

        # We will scan standard user directories:
        # /sdcard/DCIM, /sdcard/Pictures, /sdcard/Documents, /sdcard/Download, /sdcard/Movies,
        # /sdcard/Music, /sdcard/Android/media (WhatsApp/Telegram), /sdcard/WhatsApp, etc.
        target_dirs = [
            "/sdcard/DCIM",
            "/sdcard/Pictures",
            "/sdcard/Documents",
            "/sdcard/Download",
            "/sdcard/Movies",
            "/sdcard/Music",
            "/sdcard/Android/media",
            "/sdcard/WhatsApp",
            "/sdcard/Telegram",
            "/sdcard/Recordings",
            "/sdcard/Audiobooks",
            "/sdcard/Podcasts"
        ]

        # First, test if find with printf or stat is available
        # On Android Toybox, find has -exec or standard output
        # Let's run a robust script via `find <dirs> -type f` and `ls -l`
        files_list = []
        
        # Test directory existence on device
        existing_dirs = []
        for d in target_dirs:
            code, out, _ = self.run_cmd(["shell", f"[ -d '{d}' ] && echo 'exists'"])
            if "exists" in out:
                existing_dirs.append(d)

        if not existing_dirs:
            existing_dirs = ["/sdcard"]

        total_dirs = len(existing_dirs)
        for i, d in enumerate(existing_dirs):
            if progress_callback:
                progress_callback(f"Scanning {d}...", int((i / total_dirs) * 50))
            
            # Use toybox stat or find + ls
            cmd = f"find '{d}' -type f -exec stat -c '%s %Y %n' '{{}}' +"
            code, out, err = self.run_cmd(["shell", cmd], timeout=60)
            
            # Fallback to ls -l if stat -c failed
            if code != 0 or not out.strip():
                fallback_cmd = f"find '{d}' -type f"
                code2, out2, _ = self.run_cmd(["shell", fallback_cmd], timeout=60)
                if code2 == 0 and out2:
                    for filepath in out2.strip().splitlines():
                        filepath = filepath.strip()
                        if filepath and not filepath.startswith('find:'):
                            files_list.append({
                                "path": filepath,
                                "size": 0,
                                "mtime": int(time.time()),
                                "filename": os.path.basename(filepath)
                            })
                continue

            for line in out.strip().splitlines():
                line = line.strip()
                if not line or line.startswith('find:') or line.startswith('stat:'):
                    continue
                parts = line.split(' ', 2)
                if len(parts) == 3:
                    try:
                        size = int(parts[0])
                        mtime = int(parts[1])
                        path = parts[2]
                        files_list.append({
                            "path": path,
                            "size": size,
                            "mtime": mtime,
                            "filename": os.path.basename(path)
                        })
                    except ValueError:
                        continue

        return files_list

    def pull_file(self, remote_path: str, local_dest: str) -> bool:
        """Pull single file from Android device to local PC destination."""
        os.makedirs(os.path.dirname(local_dest), exist_ok=True)
        code, _, _ = self.run_cmd(["pull", remote_path, local_dest], timeout=120)
        return code == 0

    def delete_file(self, remote_path: str) -> bool:
        """Permanently delete file on device."""
        # Sanitize remote path to avoid accidental full sdcard wipe
        if not remote_path.startswith("/sdcard/") and not remote_path.startswith("/storage/"):
            return False
        if remote_path.strip() in ["/sdcard", "/sdcard/", "/storage/emulated/0", "/storage/emulated/0/"]:
            return False
        
        code, _, _ = self.run_cmd(["shell", "rm", "-f", f"'{remote_path}'"], timeout=15)
        return code == 0

    def pair_wireless(self, address: str, code: str) -> Tuple[bool, str]:
        """Pair with an Android device over Wi-Fi using IP:port and 6-digit code."""
        code_res, out, err = self.run_cmd(["pair", address, code], timeout=15)
        combined = (out + "\n" + err).strip()
        if code_res == 0 or "Successfully paired" in combined or "already paired" in combined.lower():
            return True, combined
        return False, combined

    def connect_wireless(self, address: str) -> Tuple[bool, str]:
        """Connect to an Android device over Wi-Fi (IP:port)."""
        code_res, out, err = self.run_cmd(["connect", address], timeout=15)
        combined = (out + "\n" + err).strip()
        if "connected to" in combined.lower():
            return True, combined
        return False, combined

    def delete_empty_dirs(self, root_dir: str = "/sdcard") -> int:
        """Remove empty directories to clean leftover debris."""
        cmd = f"find '{root_dir}' -mindepth 1 -type d -empty -delete"
        code, _, _ = self.run_cmd(["shell", cmd], timeout=30)
        return 1 if code == 0 else 0
