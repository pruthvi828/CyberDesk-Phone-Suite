import ctypes
import time
import pyautogui

# Disable pyautogui failsafe and pause for instant 0ms response
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.0

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x01000

KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004


class MouseController:
    """Robust zero-latency Windows mouse, trackpad, air-mouse and keyboard controller."""

    def __init__(self):
        try:
            self.user32 = ctypes.windll.user32
        except Exception:
            self.user32 = None
        self.is_dragging = False

    def move_rel(self, dx: float, dy: float, sensitivity: float = 1.0, acceleration: bool = True):
        """Move cursor relative to current position with smooth acceleration."""
        if acceleration:
            dist = (dx * dx + dy * dy) ** 0.5
            factor = 1.0 + min(dist / 30.0, 2.0)
            dx = dx * sensitivity * factor
            dy = dy * sensitivity * factor
        else:
            dx = dx * sensitivity
            dy = dy * sensitivity

        idx = int(round(dx))
        idy = int(round(dy))

        if idx == 0 and idy == 0:
            return

        # Method 1: PyAutoGUI moveRel
        try:
            pyautogui.moveRel(idx, idy, _pause=False)
        except Exception:
            # Fallback: Win32 mouse_event
            if self.user32:
                try:
                    self.user32.mouse_event(MOUSEEVENTF_MOVE, idx, idy, 0, 0)
                except Exception:
                    pass

    def left_click(self):
        """Perform Left Click."""
        try:
            pyautogui.click(button='left', _pause=False)
        except Exception:
            if self.user32:
                self.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                time.sleep(0.01)
                self.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

    def right_click(self):
        """Perform Right Click."""
        try:
            pyautogui.click(button='right', _pause=False)
        except Exception:
            if self.user32:
                self.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                time.sleep(0.01)
                self.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    def middle_click(self):
        """Perform Middle Click."""
        try:
            pyautogui.click(button='middle', _pause=False)
        except Exception:
            if self.user32:
                self.user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                time.sleep(0.01)
                self.user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)

    def double_click(self):
        """Perform Double Click."""
        try:
            pyautogui.doubleClick(button='left', _pause=False)
        except Exception:
            self.left_click()
            time.sleep(0.05)
            self.left_click()

    def mouse_down(self, button: str = "left"):
        """Hold down mouse button for dragging."""
        btn = 'left' if button not in ('left', 'right', 'middle') else button
        try:
            pyautogui.mouseDown(button=btn, _pause=False)
            self.is_dragging = True
        except Exception:
            if self.user32:
                flag = MOUSEEVENTF_LEFTDOWN if btn == 'left' else (MOUSEEVENTF_RIGHTDOWN if btn == 'right' else MOUSEEVENTF_MIDDLEDOWN)
                self.user32.mouse_event(flag, 0, 0, 0, 0)
                self.is_dragging = True

    def mouse_up(self, button: str = "left"):
        """Release mouse button after dragging."""
        btn = 'left' if button not in ('left', 'right', 'middle') else button
        try:
            pyautogui.mouseUp(button=btn, _pause=False)
            self.is_dragging = False
        except Exception:
            if self.user32:
                flag = MOUSEEVENTF_LEFTUP if btn == 'left' else (MOUSEEVENTF_RIGHTUP if btn == 'right' else MOUSEEVENTF_MIDDLEUP)
                self.user32.mouse_event(flag, 0, 0, 0, 0)
                self.is_dragging = False

    def scroll(self, dy: float, dx: float = 0.0, sensitivity: float = 1.0):
        """Perform vertical & horizontal scroll."""
        if dy != 0:
            amount = int(round(dy * 12 * sensitivity))
            if amount != 0:
                try:
                    pyautogui.scroll(amount, _pause=False)
                except Exception:
                    if self.user32:
                        self.user32.mouse_event(MOUSEEVENTF_WHEEL, 0, 0, amount * 10, 0)
        if dx != 0:
            hamount = int(round(dx * 12 * sensitivity))
            if hamount != 0:
                try:
                    pyautogui.hscroll(hamount, _pause=False)
                except Exception:
                    pass

    def press_key(self, key_name: str):
        """Trigger keyboard hotkeys and media controls."""
        key_map = {
            "enter": "enter",
            "backspace": "backspace",
            "tab": "tab",
            "esc": "esc",
            "space": "space",
            "left": "left",
            "up": "up",
            "right": "right",
            "down": "down",
            "pageup": "pageup",
            "pagedown": "pagedown",
            "win": "win",
            "vol_up": "volumeup",
            "vol_down": "volumedown",
            "vol_mute": "volumemute",
            "media_play": "playpause",
            "media_next": "nexttrack",
            "media_prev": "prevtrack",
        }

        if key_name in key_map:
            try:
                pyautogui.press(key_map[key_name], _pause=False)
            except Exception as e:
                print(f"Error pressing key {key_name}: {e}")
        elif key_name == "alt_tab":
            try:
                pyautogui.hotkey('alt', 'tab', _pause=False)
            except Exception:
                pass
        elif key_name == "win_d":
            try:
                pyautogui.hotkey('win', 'd', _pause=False)
            except Exception:
                pass

    def type_unicode(self, text: str):
        """Type text into active PC application."""
        if not text:
            return
        try:
            pyautogui.write(text, interval=0.01)
        except Exception:
            if self.user32:
                for char in text:
                    code = ord(char)
                    self.user32.keybd_event(0, code, KEYEVENTF_UNICODE, 0)
                    self.user32.keybd_event(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)


mouse_controller = MouseController()
