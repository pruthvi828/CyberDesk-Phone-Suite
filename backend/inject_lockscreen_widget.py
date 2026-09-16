import subprocess
import json
import time

DEV_ID = "VWGYW4SGJNYLEYQG"

def run_adb(cmd):
    res = subprocess.run(["adb", "-s", DEV_ID] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
    return res.stdout.strip()

# 1. Get current config
raw_data = run_adb(["shell", "settings", "get", "system", "keyguard_style_personality_data"])
print("Raw data length:", len(raw_data))

try:
    data = json.loads(raw_data)
    style_data_str = data.get("styleData", "{}")
    style_data = json.loads(style_data_str)

    widget_style = style_data.get("widgetStyleConfig", {})
    style_widgets = widget_style.get("styleWidgetsConfig", {})
    grid_data = style_widgets.get("gridDataString", [])

    print("Current widgets count:", len(grid_data))

    # Define Battery Widget Card
    battery_card_content = {
        "cardType": 300001,
        "cardId": 1000001,
        "instantCardUrl": "hap://widget/com.oplus.battery.card/cards/smallcard?__RPK_PATH__=android://com.oplus.battery/assets/com.oplus.battery.card.release.1.0.19.rpk&__LOC_VER__=10019&__LOAD_STRATEGY__=0"
    }

    battery_widget = {
        "localType": 1,
        "uniqueId": "300001&1000001",
        "location": {
            "startRow": 0,
            "startCol": 3
        },
        "size": {
            "rowSpan": 1,
            "colSpan": 1
        },
        "cardContent": json.dumps(battery_card_content)
    }

    # Filter out existing widget at col 3 if any
    new_grid = [w for w in grid_data if w.get("location", {}).get("startCol") != 3]
    new_grid.append(battery_widget)

    style_widgets["gridDataString"] = new_grid
    widget_style["styleWidgetsConfig"] = style_widgets
    style_data["widgetStyleConfig"] = widget_style
    data["styleData"] = json.dumps(style_data)
    data["lastModifyTime"] = int(time.time() * 1000)

    updated_json_str = json.dumps(data)

    # Write back to settings
    escaped_str = updated_json_str.replace("'", "'\\''")
    res = run_adb(["shell", f"settings put system keyguard_style_personality_data '{escaped_str}'"])
    print("Settings put result:", res)

    # Send broadcast / refresh keyguard
    run_adb(["shell", "am broadcast -a com.oplus.keyguard.action.CLOCK_AND_WIDGET_STYLE_CHANGED"])
    run_adb(["shell", "am broadcast -a com.oplus.wallpaper.UPDATE_LOCKSCREEN_CONFIG"])
    print("Successfully injected Battery Remaining widget into Lock Screen!")

except Exception as e:
    print("Error updating lock screen config:", e)
