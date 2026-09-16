# 📱 Phone Data Cleaner & Safe Backup Suite

Clean unnecessary junk, screenshots, and leftover app files from your phone via USB while safeguarding and backing up all your **important documents**, **camera photos & videos**, and **meaningful records**.

---

## 🌟 Key Features

1. **Safety First (Backup Before Clean)**:
   - 🛡️ One-click safe backup of all important documents (`.pdf`, `.docx`, `.xlsx`, `.txt`, scanned files), WhatsApp docs, and genuine camera photos directly onto your PC (`D:\Phone_Safe_Backup`).
2. **Intelligent Segregation**:
   - 📸 **Camera Photos/Videos**: Kept safe.
   - ✂️ **Screenshots & Screen Captures**: Accurately detected and isolated for deletion.
   - 🧹 **Junk & Cache**: `.thumbnails`, `.cache`, WhatsApp stickers trash, leftover `.tmp` and `.apk` installers flagged for 1-click clean.
   - 📄 **Meaningful Documents**: Work, study, and financial documents are strictly preserved.
3. **Dual Connection Modes**:
   - **ADB Direct USB Mode**: Automatic deep scan of internal storage `/sdcard/` over USB cable.
   - **Local / MTP Folder Mode**: Works with any mounted phone folder or USB drive.
4. **Dry Run Preview**:
   - Review exact filenames, paths, and total gigabytes before confirming any deletion.

---

## 🚀 How to Run

### Option 1: One-Click GUI Launcher (Recommended)
Double-click `start_cleaner.bat` in this folder, or run:
```bash
python backend/app.py
```
Then open **[http://127.0.0.1:8484](http://127.0.0.1:8484)** in your web browser.

---

### Option 2: Command-Line (CLI) Mode
To scan connected USB phone:
```bash
python cli.py --mode adb
```

To backup all docs and photos:
```bash
python cli.py --mode adb --backup --backup-dest "D:\Phone_Safe_Backup"
```

To preview cleanup of screenshots & junk (Dry Run):
```bash
python cli.py --mode adb --clean-screenshots --clean-junk --dry-run
```

To execute cleanup:
```bash
python cli.py --mode adb --clean-screenshots --clean-junk
```

---

## 🔌 Connecting your Phone via USB (Quick Guide)

1. Connect your phone to your PC with a **USB cable**.
2. Set USB mode to **File Transfer (MTP)** on your phone.
3. Enable **USB Debugging**:
   - Open **Settings > About Phone**.
   - Tap **Build Number** 7 times until Developer Mode is unlocked.
   - Go to **Settings > System / Developer Options** > Turn on **USB Debugging**.
   - Tap **Allow USB Debugging** on the phone prompt and check *"Always allow from this computer"*.
