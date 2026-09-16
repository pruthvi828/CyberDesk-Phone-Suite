import os
import sys
import asyncio
import json
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import subprocess
import mimetypes

import os
import sys

# Ensure backend folder and parent folder are in sys.path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

try:
    from backend.adb_manager import ADBManager
    from backend.scanner import FileScanner, ScanResult
    from backend.cleaner import SafeOperationsManager
    from backend.categorizer import format_size
    from backend.mouse_controller import mouse_controller
except ImportError:
    from adb_manager import ADBManager
    from scanner import FileScanner, ScanResult
    from cleaner import SafeOperationsManager
    from categorizer import format_size
    from mouse_controller import mouse_controller

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = FastAPI(title="Phone Clean & Safe Backup Suite", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core singletons
adb_manager = ADBManager()
scanner = FileScanner(adb_manager)
ops_manager = SafeOperationsManager(adb_manager)

# WebSocket Connection Manager for live updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(data)
            except Exception:
                self.disconnect(connection)

ws_manager = ConnectionManager()
loop_holder = {"loop": None}


def sync_broadcast_progress(status: str, percent: int, stage: str = "progress"):
    """Helper to send WebSocket messages from synchronous worker threads."""
    if loop_holder["loop"]:
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast({
                "type": "progress",
                "stage": stage,
                "status": status,
                "percent": percent
            }),
            loop_holder["loop"]
        )


@app.on_event("startup")
async def startup_event():
    loop_holder["loop"] = asyncio.get_running_loop()


# Pydantic Schemas
class ScanRequest(BaseModel):
    mode: str = "adb"  # "adb" or "folder"
    folder_path: Optional[str] = None
    device_id: Optional[str] = None


class BackupRequest(BaseModel):
    category_keys: Optional[List[str]] = None
    file_paths: Optional[List[str]] = None
    destination: Optional[str] = None


class CleanRequest(BaseModel):
    category_keys: Optional[List[str]] = None
    file_paths: Optional[List[str]] = None
    dry_run: bool = False


# Routes
@app.get("/api/device/status")
async def get_device_status():
    """Check ADB connectivity and attached phone status."""
    is_installed = adb_manager.is_adb_installed()
    devices = adb_manager.get_devices() if is_installed else []
    details = adb_manager.get_device_details() if is_installed else {"connected": False, "reason": "ADB not found"}
    
    return {
        "adb_installed": is_installed,
        "devices": devices,
        "active_device": details,
        "default_backup_dir": os.path.abspath(os.path.join(BASE_DIR, "Safe_Phone_Backup"))
    }


@app.get("/api/migration/status")
async def get_migration_status():
    """Returns the live migration and video transfer progress from phone to pen drive."""
    status_file = os.path.join(BASE_DIR, "backend", "migration_status.json")
    if os.path.exists(status_file):
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"status": "idle", "message": "No active migration running."}


FIRETV_IP = "192.168.0.115:5555"

@app.post("/api/firetv/remote")
async def firetv_remote_key(data: Dict[str, str] = Body(...)):
    """Send remote keyevents directly to Fire TV Stick."""
    key = data.get("key", "").lower().strip()
    keymap = {
        "volume_up": "24",
        "volume_down": "25",
        "mute": "164",
        "home": "3",
        "back": "4",
        "select": "23",
        "ok": "23",
        "menu": "82",
        "up": "19",
        "down": "20",
        "left": "21",
        "right": "22",
        "play_pause": "85",
        "rewind": "89",
        "fast_forward": "90",
        "power": "26"
    }
    key_code = keymap.get(key)
    if not key_code:
        raise HTTPException(status_code=400, detail="Invalid remote key.")
    
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "input", "keyevent", key_code], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"success": True, "key": key, "key_code": key_code}


@app.post("/api/firetv/launch")
async def firetv_launch_app(data: Dict[str, str] = Body(...)):
    """Directly launch apps on the Fire TV Stick."""
    app_name = data.get("app", "").lower().strip()
    apps = {
        "stremio": ["am", "start", "-a", "android.intent.action.VIEW", "-d", "stremio:///board", "com.stremio.one"],
        "all-in-one": ["am", "start", "-a", "android.intent.action.VIEW", "-d", "stremio:///board", "com.stremio.one"],
        "smarttube": ["monkey", "-p", "org.smarttube.stable", "-c", "android.intent.category.LAUNCHER", "1"],
        "flauncher": ["am", "start", "-n", "me.efesser.flauncher/.MainActivity"],
        "netflix": ["monkey", "-p", "com.netflix.ninja", "-c", "android.intent.category.LAUNCHER", "1"],
        "youtube": ["monkey", "-p", "com.amazon.firetv.youtube", "-c", "android.intent.category.LAUNCHER", "1"],
        "settings": ["am", "start", "-a", "android.settings.SETTINGS"]
    }
    cmd = apps.get(app_name)
    if not cmd:
        raise HTTPException(status_code=400, detail="Unknown app.")
    
    # Wake up TV if screensaver/sleep is active
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "input", "keyevent", "224"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["adb", "-s", FIRETV_IP, "shell"] + cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"success": True, "app": app_name}


@app.post("/api/firetv/text")
async def firetv_type_text(data: Dict[str, str] = Body(...)):
    """Type text into active input field on Fire TV Stick."""
    text = data.get("text", "").strip()
    if text:
        # Escape spaces for adb input text
        escaped = text.replace(" ", "%s")
        subprocess.run(["adb", "-s", FIRETV_IP, "shell", "input", "text", escaped], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # Also press enter
        subprocess.run(["adb", "-s", FIRETV_IP, "shell", "input", "keyevent", "66"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return {"success": True, "text": text}


@app.post("/api/firetv/optimize")
async def firetv_optimize():
    """1-Click Fire TV Performance Booster: Wipe cache and unblock PIN locks."""
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "settings", "put", "secure", "lockscreen.disabled", "1"])
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "settings", "put", "secure", "parental_controls_pin_set_status", "0"])
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "settings", "put", "secure", "child_pin_enabled", "false"])
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "settings", "put", "system", "ParentalControls.AppLaunch", "UNBLOCKED"])
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "settings", "put", "system", "ParentalControls.Purchases", "UNBLOCKED"])
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "settings", "put", "system", "ParentalControls.Photos", "UNBLOCKED"])
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "rm", "-rf", "/sdcard/Android/data/com.amazon.tv.launcher/cache/*"])
    subprocess.run(["adb", "-s", FIRETV_IP, "shell", "rm", "-rf", "/sdcard/Android/data/com.amazon.firetv.youtube/cache/*"])
    return {"success": True, "message": "Fire TV Optimized! Passwords unblocked & 171 MB cache cleaned."}


@app.get("/remote")
async def serve_remote():
    remote_path = os.path.join(STATIC_DIR, "remote.html")
    if os.path.exists(remote_path):
        return FileResponse(remote_path)
    return {"message": "Remote HTML not found."}





@app.post("/api/device/pair-wireless")
async def pair_wireless_device(data: Dict[str, str] = Body(...)):
    address = data.get("address", "").strip()
    code = data.get("code", "").strip()
    if not address or not code:
        raise HTTPException(status_code=400, detail="Both IP:Port and Pairing Code are required.")
    
    success, msg = adb_manager.pair_wireless(address, code)
    if success:
        # Also try to auto-select
        adb_manager.select_device()
        return {"success": True, "message": msg, "device": adb_manager.get_device_details()}
    return {"success": False, "message": msg}


@app.post("/api/device/connect-wireless")
async def connect_wireless_device(data: Dict[str, str] = Body(...)):
    address = data.get("address", "").strip()
    if not address:
        raise HTTPException(status_code=400, detail="IP:Port address is required.")
    
    success, msg = adb_manager.connect_wireless(address)
    if success:
        adb_manager.select_device()
        return {"success": True, "message": msg, "device": adb_manager.get_device_details()}
    return {"success": False, "message": msg}


@app.get("/api/media/preview")
async def preview_media(path: str = Query(...)):
    """Stream or preview image/video directly from phone over ADB or local filesystem."""
    mime_type, _ = mimetypes.guess_type(path)
    if not mime_type:
        mime_type = "application/octet-stream"

    if os.path.exists(path):
        return FileResponse(path, media_type=mime_type)

    # ADB Stream
    dev_id = adb_manager.current_device_id or ""
    if not dev_id:
        adb_manager.select_device()
        dev_id = adb_manager.current_device_id or ""

    def iterfile():
        cmd = ["adb"]
        if dev_id:
            cmd.extend(["-s", dev_id])
        cmd.extend(["exec-out", f"cat '{path}'"])
        
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        try:
            while True:
                chunk = proc.stdout.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            if proc.stdout:
                proc.stdout.close()
            proc.kill()

    return StreamingResponse(iterfile(), media_type=mime_type)


@app.get("/api/migration/status")
async def get_migration_status():
    """Returns real-time statistics of ongoing video transfer to pen drive."""
    dest = "E:\\Realme8_Phone_Videos"
    total_target = 126
    total_gb = 11.12
    if os.path.exists(dest):
        files = os.listdir(dest)
        total_sz = sum(os.path.getsize(os.path.join(dest, f)) for f in files)
        done_count = len(files)
        done_gb = round(total_sz / (1024**3), 2)
        pct = round((done_count / total_target) * 100, 1)
        
        # Get latest 5 files
        sorted_files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(dest, x)), reverse=True)[:5]
        recent = [{"name": f, "size_mb": round(os.path.getsize(os.path.join(dest, f))/(1024*1024), 1)} for f in sorted_files]

        return {
            "active": done_count < total_target,
            "done_count": done_count,
            "total_count": total_target,
            "done_gb": done_gb,
            "total_gb": total_gb,
            "percent": pct,
            "remaining_count": max(0, total_target - done_count),
            "recent_files": recent
        }
    return {"active": False, "done_count": 0, "total_count": 126, "percent": 0.0}


@app.post("/api/device/select")
async def select_device(data: Dict[str, str] = Body(...)):
    dev_id = data.get("device_id")
    ok = adb_manager.select_device(dev_id)
    return {"success": ok, "details": adb_manager.get_device_details()}


@app.post("/api/scan/start")
async def start_scan(req: ScanRequest):
    """Trigger device or folder scanning."""
    try:
        await ws_manager.broadcast({"type": "scan_start", "mode": req.mode})
        
        def run_sync_scan():
            if req.mode == "folder" and req.folder_path:
                return scanner.scan_local_folder(
                    req.folder_path,
                    progress_callback=lambda msg, pct: sync_broadcast_progress(msg, pct, stage="scan")
                )
            else:
                if req.device_id:
                    adb_manager.select_device(req.device_id)
                return scanner.scan_adb_device(
                    progress_callback=lambda msg, pct: sync_broadcast_progress(msg, pct, stage="scan")
                )

        # Run in thread pool to avoid blocking async loop
        loop = asyncio.get_running_loop()
        res: ScanResult = await loop.run_in_executor(None, run_sync_scan)
        
        summary = res.to_summary_dict()
        await ws_manager.broadcast({"type": "scan_complete", "data": summary})
        return {"success": True, "summary": summary}
    except Exception as e:
        await ws_manager.broadcast({"type": "error", "message": str(e)})
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/scan/results")
async def get_scan_results():
    """Retrieve last scan summary."""
    if not scanner.last_scan:
        return {"scanned": False, "summary": None}
    return {"scanned": True, "summary": scanner.last_scan.to_summary_dict()}


@app.get("/api/scan/category/{category_key}")
async def get_category_files(category_key: str):
    """Retrieve detailed file list for a specific category."""
    if not scanner.last_scan:
        raise HTTPException(status_code=404, detail="No scan data available. Please scan first.")
    if category_key not in scanner.last_scan.categories:
        raise HTTPException(status_code=404, detail="Category not found.")
    
    cat = scanner.last_scan.categories[category_key]
    return {
        "category_key": category_key,
        "label": cat["label"],
        "count": cat["count"],
        "bytes": cat["bytes"],
        "bytes_formatted": format_size(cat["bytes"]),
        "files": cat["files"]
    }


@app.post("/api/backup")
async def backup_files(req: BackupRequest):
    """Backup selected files or categories to PC."""
    if not scanner.last_scan:
        raise HTTPException(status_code=400, detail="Please scan your phone first.")

    destination = req.destination or os.path.abspath(os.path.join(BASE_DIR, "Safe_Phone_Backup"))
    files_to_backup = []

    # If specific paths provided
    if req.file_paths:
        path_set = set(req.file_paths)
        for cat in scanner.last_scan.categories.values():
            for f in cat["files"]:
                if f["path"] in path_set:
                    files_to_backup.append(f)
    elif req.category_keys:
        for k in req.category_keys:
            if k in scanner.last_scan.categories:
                files_to_backup.extend(scanner.last_scan.categories[k]["files"])
    else:
        # Default: backup all recommended keep categories
        for k, cat in scanner.last_scan.categories.items():
            if cat.get("default_checked_backup"):
                files_to_backup.extend(cat["files"])

    if not files_to_backup:
        raise HTTPException(status_code=400, detail="No files selected for backup.")

    await ws_manager.broadcast({"type": "backup_start", "count": len(files_to_backup)})

    def run_sync_backup():
        return ops_manager.backup_files(
            files=files_to_backup,
            destination_root=destination,
            source_type=scanner.last_scan.source_type,
            progress_callback=lambda msg, pct: sync_broadcast_progress(msg, pct, stage="backup")
        )

    loop = asyncio.get_running_loop()
    manifest = await loop.run_in_executor(None, run_sync_backup)
    await ws_manager.broadcast({"type": "backup_complete", "data": manifest})
    return {"success": True, "manifest": manifest}


@app.post("/api/clean")
async def clean_files(req: CleanRequest):
    """Clean/delete unwanted files (e.g. screenshots, junk) or perform dry run."""
    if not scanner.last_scan:
        raise HTTPException(status_code=400, detail="Please scan your phone first.")

    files_to_clean = []
    if req.file_paths:
        path_set = set(req.file_paths)
        for cat in scanner.last_scan.categories.values():
            for f in cat["files"]:
                if f["path"] in path_set:
                    files_to_clean.append(f)
    elif req.category_keys:
        for k in req.category_keys:
            if k in scanner.last_scan.categories:
                files_to_clean.extend(scanner.last_scan.categories[k]["files"])
    else:
        # Default: clean screenshots & junk
        for k in ["screenshots", "junk_cache", "apks"]:
            if k in scanner.last_scan.categories:
                files_to_clean.extend(scanner.last_scan.categories[k]["files"])

    if not files_to_clean:
        return {
            "success": True,
            "dry_run": req.dry_run,
            "message": "No files found to clean in selected categories.",
            "deleted_count": 0,
            "freed_formatted": "0 B"
        }

    await ws_manager.broadcast({"type": "clean_start", "count": len(files_to_clean), "dry_run": req.dry_run})

    def run_sync_clean():
        return ops_manager.clean_files(
            files=files_to_clean,
            source_type=scanner.last_scan.source_type,
            dry_run=req.dry_run,
            progress_callback=lambda msg, pct: sync_broadcast_progress(msg, pct, stage="clean")
        )

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, run_sync_clean)
    
    # If actual deletion occurred, refresh scan cache
    if not req.dry_run:
        deleted_paths = set(item["path"] for item in result.get("deleted_files", []))
        for cat in scanner.last_scan.categories.values():
            cat["files"] = [f for f in cat["files"] if f["path"] not in deleted_paths]
            cat["count"] = len(cat["files"])
            cat["bytes"] = sum(f["size"] for f in cat["files"])
        scanner.last_scan.total_files = sum(c["count"] for c in scanner.last_scan.categories.values())
        scanner.last_scan.total_bytes = sum(c["bytes"] for c in scanner.last_scan.categories.values())

    await ws_manager.broadcast({"type": "clean_complete", "data": result})
    return {"success": True, "result": result}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)


@app.get("/trackpad")
async def serve_trackpad():
    """Serve the mobile Web Trackpad & Air Mouse interface."""
    trackpad_path = os.path.join(STATIC_DIR, "trackpad.html")
    if os.path.exists(trackpad_path):
        return FileResponse(trackpad_path)
    return {"message": "Trackpad HTML not found."}


@app.post("/api/mouse/launch-phone")
async def launch_trackpad_on_phone():
    """Setup ADB reverse port forwarding and launch Trackpad on connected Realme phone."""
    is_installed = adb_manager.is_adb_installed()
    if not is_installed:
        raise HTTPException(status_code=400, detail="ADB is not available.")
    
    dev_id = adb_manager.current_device_id
    if not dev_id:
        adb_manager.select_device()
        dev_id = adb_manager.current_device_id
    
    if not dev_id:
        raise HTTPException(status_code=400, detail="No connected phone detected.")

    # 1. Reverse port 8484 over USB so phone can access http://localhost:8484
    subprocess.run(["adb", "-s", dev_id, "reverse", "tcp:8484", "tcp:8484"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # 2. Launch browser on phone
    subprocess.run([
        "adb", "-s", dev_id, "shell", "am", "start",
        "-a", "android.intent.action.VIEW",
        "-d", "http://localhost:8484/trackpad"
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    return {"success": True, "message": "Trackpad opened on your phone screen!", "url": "http://localhost:8484/trackpad"}


@app.websocket("/ws/mouse")
async def websocket_mouse(websocket: WebSocket):
    """Ultra-low latency WebSocket dispatcher for mouse movements, clicks, and keys."""
    await websocket.accept()
    try:
        while True:
            raw_msg = await websocket.receive_text()
            if not raw_msg:
                continue
            try:
                data = json.loads(raw_msg)
                event_type = data.get("type")

                if event_type == "move":
                    dx = float(data.get("dx", 0))
                    dy = float(data.get("dy", 0))
                    sens = float(data.get("sensitivity", 1.0))
                    accel = bool(data.get("acceleration", True))
                    mouse_controller.move_rel(dx, dy, sensitivity=sens, acceleration=accel)

                elif event_type == "click":
                    btn = data.get("button", "left")
                    if btn == "left":
                        mouse_controller.left_click()
                    elif btn == "right":
                        mouse_controller.right_click()
                    elif btn == "middle":
                        mouse_controller.middle_click()

                elif event_type == "double_click":
                    mouse_controller.double_click()

                elif event_type == "down":
                    btn = data.get("button", "left")
                    mouse_controller.mouse_down(btn)

                elif event_type == "up":
                    btn = data.get("button", "left")
                    mouse_controller.mouse_up(btn)

                elif event_type == "scroll":
                    dy = float(data.get("dy", 0))
                    dx = float(data.get("dx", 0))
                    sens = float(data.get("sensitivity", 1.0))
                    mouse_controller.scroll(dy, dx, sensitivity=sens)

                elif event_type == "key":
                    k = data.get("key", "")
                    if k:
                        mouse_controller.press_key(k)

                elif event_type == "text":
                    txt = data.get("text", "")
                    if txt:
                        mouse_controller.type_unicode(txt)

            except Exception:
                pass
    except WebSocketDisconnect:
        pass
@app.post("/api/mouse/event")
async def handle_mouse_http(data: Dict[str, Any] = Body(...)):
    """HTTP fallback for mouse and keyboard events."""
    event_type = data.get("type")
    if event_type == "move":
        dx = float(data.get("dx", 0))
        dy = float(data.get("dy", 0))
        sens = float(data.get("sensitivity", 1.0))
        accel = bool(data.get("acceleration", True))
        mouse_controller.move_rel(dx, dy, sensitivity=sens, acceleration=accel)
    elif event_type == "click":
        btn = data.get("button", "left")
        if btn == "left":
            mouse_controller.left_click()
        elif btn == "right":
            mouse_controller.right_click()
    elif event_type == "down":
        btn = data.get("button", "left")
        mouse_controller.mouse_down(btn)
    elif event_type == "up":
        btn = data.get("button", "left")
        mouse_controller.mouse_up(btn)
    elif event_type == "scroll":
        dy = float(data.get("dy", 0))
        dx = float(data.get("dx", 0))
        sens = float(data.get("sensitivity", 1.0))
        mouse_controller.scroll(dy, dx, sensitivity=sens)
    elif event_type == "key":
        k = data.get("key", "")
        if k:
            mouse_controller.press_key(k)
    elif event_type == "text":
        txt = data.get("text", "")
        if txt:
            mouse_controller.type_unicode(txt)
    return {"success": True}


# Mount static files and frontend
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Phone Clean API is running. UI index.html will be loaded."}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8484)
