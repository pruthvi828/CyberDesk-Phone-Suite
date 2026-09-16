import os
import re
from typing import Dict, Any, Tuple

# Extension definitions
DOC_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
    '.txt', '.csv', '.epub', '.rtf', '.odt', '.pages', '.numbers',
    '.key', '.md', '.json', '.xml', '.html', '.htm', '.log'
}

IMPORTANT_DOC_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
    '.txt', '.csv', '.epub', '.rtf', '.odt', '.pages', '.numbers', '.key'
}

IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif', '.bmp', '.tiff', '.dng', '.raw'}
VIDEO_EXTENSIONS = {'.mp4', '.mov', '.mkv', '.avi', '.3gp', '.webm', '.m4v', '.wmv'}
AUDIO_EXTENSIONS = {'.mp3', '.m4a', '.aac', '.wav', '.ogg', '.opus', '.flac'}
APK_EXTENSIONS = {'.apk', '.xapk', '.apks'}

# Patterns for Screenshots
SCREENSHOT_PATH_PATTERNS = [
    re.compile(r'[/\\_.-]screenshots?[/\\_.-]?', re.IGNORECASE),
    re.compile(r'[/\\_.-]screen_?record(ing|er)s?[/\\_.-]?', re.IGNORECASE),
    re.compile(r'[/\\_.-]screencaptures?[/\\_.-]?', re.IGNORECASE),
    re.compile(r'[/\\_.-]screen_?shots?[/\\_.-]?', re.IGNORECASE),
]

SCREENSHOT_FILENAME_PATTERNS = [
    re.compile(r'^screenshot[s_.-]', re.IGNORECASE),
    re.compile(r'^screen_?record(ing)?[_.-]', re.IGNORECASE),
    re.compile(r'^screen_?capture[_.-]', re.IGNORECASE),
    re.compile(r'^capture[_.-]\d+', re.IGNORECASE),
    re.compile(r'[-_]screenshot[-_.]', re.IGNORECASE),
]

# Patterns for Camera media
CAMERA_PATH_PATTERNS = [
    re.compile(r'[/\\-]dcim[/\\-]camera', re.IGNORECASE),
    re.compile(r'[/\\-]dcim[/\\-]100media', re.IGNORECASE),
    re.compile(r'[/\\-]dcim[/\\-]100andro', re.IGNORECASE),
    re.compile(r'[/\\-]pictures[/\\-]camera', re.IGNORECASE),
    re.compile(r'[/\\-]movies[/\\-]camera', re.IGNORECASE),
]

# Patterns for Junk and Cache
JUNK_PATTERNS = [
    re.compile(r'[/\\]\.thumbnails([/\\]|$)', re.IGNORECASE),
    re.compile(r'[/\\]\.cache([/\\]|$)', re.IGNORECASE),
    re.compile(r'[/\\]\.trashed([/\\]|$)', re.IGNORECASE),
    re.compile(r'[/\\]\.trash([/\\]|$)', re.IGNORECASE),
    re.compile(r'[/\\]lost\.dir([/\\]|$)', re.IGNORECASE),
    re.compile(r'[/\\]\.nomedia$', re.IGNORECASE),
    re.compile(r'[/\\]\.tmp[/\\]', re.IGNORECASE),
    re.compile(r'thumbdata\d*[-_]', re.IGNORECASE),
    re.compile(r'whatsapp[/\\].*[/\\].*stickers', re.IGNORECASE),
    re.compile(r'whatsapp[/\\].*[/\\].*statuses', re.IGNORECASE),
    re.compile(r'whatsapp[/\\].*[/\\].*trash', re.IGNORECASE),
    re.compile(r'telegram[/\\].*[/\\].*cache', re.IGNORECASE),
]

# Patterns for Messaging Docs
MESSAGING_DOCS_PATTERNS = [
    re.compile(r'whatsapp[/\\].*[/\\].*documents', re.IGNORECASE),
    re.compile(r'telegram[/\\].*[/\\].*documents', re.IGNORECASE),
    re.compile(r'signal[/\\].*[/\\].*documents', re.IGNORECASE),
]


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string (KB, MB, GB)."""
    if size_bytes < 0:
        return "0 B"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def categorize_file(rel_path: str, filename: str, size: int = 0) -> Dict[str, Any]:
    """
    Categorize a file based on its relative path, filename, and extension.
    Returns category key, category name, recommendation (KEEP, REVIEW, CLEAN),
    and descriptive tags.
    """
    clean_path = rel_path.replace('\\', '/')
    name_lower = filename.lower()
    _, ext = os.path.splitext(name_lower)

    # 1. Check for Junk & Cache first
    for pattern in JUNK_PATTERNS:
        if pattern.search(clean_path) or pattern.search(filename):
            return {
                "category": "junk_cache",
                "category_label": "Cache & System Junk",
                "recommendation": "CLEAN",
                "badge": "Junk",
                "badge_color": "danger",
                "keep_default": False,
                "can_delete": True,
                "description": "App cache, thumbnails, trash leftovers, or temporary storage."
            }

    # 2. Check for Screenshots & Screen Recordings
    is_screenshot = False
    for pattern in SCREENSHOT_PATH_PATTERNS:
        if pattern.search(clean_path):
            is_screenshot = True
            break
    if not is_screenshot:
        for pattern in SCREENSHOT_FILENAME_PATTERNS:
            if pattern.search(filename):
                is_screenshot = True
                break

    if is_screenshot:
        return {
            "category": "screenshots",
            "category_label": "Screenshots & Screen Captures",
            "recommendation": "CLEAN",
            "badge": "Screenshot",
            "badge_color": "warning",
            "keep_default": False,
            "can_delete": True,
            "description": "Captured screen image or video recording."
        }

    # 3. Check for Messaging Documents (WhatsApp / Telegram Docs)
    for pattern in MESSAGING_DOCS_PATTERNS:
        if pattern.search(clean_path):
            return {
                "category": "messaging_docs",
                "category_label": "Messaging Documents",
                "recommendation": "KEEP",
                "badge": "Msg Doc",
                "badge_color": "success",
                "keep_default": True,
                "can_delete": False,
                "description": "Document shared via WhatsApp, Telegram, or messaging app."
            }

    # 4. Check for Important Documents
    if ext in IMPORTANT_DOC_EXTENSIONS or '/documents/' in clean_path.lower():
        if ext in IMPORTANT_DOC_EXTENSIONS:
            return {
                "category": "important_docs",
                "category_label": "Important Documents",
                "recommendation": "KEEP",
                "badge": "Doc",
                "badge_color": "success",
                "keep_default": True,
                "can_delete": False,
                "description": f"Document file ({ext.upper().replace('.', '')})."
            }

    # 5. Check for Genuine Camera Photos & Videos
    is_camera = False
    for pattern in CAMERA_PATH_PATTERNS:
        if pattern.search(clean_path):
            is_camera = True
            break
    
    if is_camera and (ext in IMAGE_EXTENSIONS or ext in VIDEO_EXTENSIONS):
        return {
            "category": "camera_media",
            "category_label": "Camera Photos & Videos",
            "recommendation": "KEEP",
            "badge": "Camera",
            "badge_color": "info",
            "keep_default": True,
            "can_delete": False,
            "description": "Original photo/video captured with phone camera."
        }

    # 6. APK files (Installer packages left in storage)
    if ext in APK_EXTENSIONS:
        return {
            "category": "apks",
            "category_label": "APK App Installers",
            "recommendation": "REVIEW",
            "badge": "APK",
            "badge_color": "warning",
            "keep_default": False,
            "can_delete": True,
            "description": "Android APK package installer file taking up storage."
        }

    # 7. Other Images & Videos (Saved images, Wallpapers, Social Media downloads)
    if ext in IMAGE_EXTENSIONS:
        return {
            "category": "other_images",
            "category_label": "Other Images & Downloads",
            "recommendation": "REVIEW",
            "badge": "Image",
            "badge_color": "secondary",
            "keep_default": True,
            "can_delete": True,
            "description": "Downloaded or saved image."
        }

    if ext in VIDEO_EXTENSIONS:
        return {
            "category": "other_videos",
            "category_label": "Other Videos & Media",
            "recommendation": "REVIEW",
            "badge": "Video",
            "badge_color": "secondary",
            "keep_default": True,
            "can_delete": True,
            "description": "Downloaded or saved video file."
        }

    if ext in AUDIO_EXTENSIONS:
        return {
            "category": "audio_music",
            "category_label": "Audio & Music",
            "recommendation": "KEEP",
            "badge": "Audio",
            "badge_color": "info",
            "keep_default": True,
            "can_delete": True,
            "description": "Audio track, voice note or music file."
        }

    # 8. Fallback / Other files
    return {
        "category": "other_files",
        "category_label": "Other Files & Downloads",
        "recommendation": "REVIEW",
        "badge": "File",
        "badge_color": "secondary",
        "keep_default": True,
        "can_delete": True,
        "description": "Uncategorized file."
    }
