import subprocess
import os

def run_adb(cmd):
    res = subprocess.run(['adb', 'shell'] + cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors='replace')
    return res.stdout

def clean_non_personal_and_recordings():
    print("=== 1. DELETING LONG VOICE RECORDINGS ===")
    recordings = [
        "/sdcard/Music/Recordings/Standard Recordings/edc.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/tolaram  10th.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/jyoti 9th sept.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/broker.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/diven shrma.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/sharma 2.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/Standard recording 1.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/5-3 26 Bindra.mp3",
        "/sdcard/Music/Recordings/Standard Recordings/1..mp3"
    ]

    for r in recordings:
        run_adb(["rm", "-f", r])
        print(f"Deleted: {os.path.basename(r)}")

    print("\n=== 2. DELETING GENERIC STUDY / SYLLABUS / TEMP FILES ===")
    generic_docs = [
        "/sdcard/Download/SIGNALS AND SYSTEMS -- A Nagoor Kani -- 2010 -- Tata McGraw-Hill -- 9780070151390 -- 61a8c12e61061f5df5988c6b17e2e08c -- Anna’s Archive.pdf",
        "/sdcard/Download/M.D.Dayal (2019) (1).pdf",
        "/sdcard/Download/1.1 Diode.pdf",
        "/sdcard/Download/1.1 Zener diode regulator.pdf",
        "/sdcard/Download/1.2 BJT.pdf",
        "/sdcard/Download/1.2 FET.pdf",
        "/sdcard/Download/1.2 MOSFET.pdf",
        "/sdcard/Download/2.1 BJT DC analysis .pdf",
        "/sdcard/Download/2.2 FET DC Analysis .pdf",
        "/sdcard/Download/2.2 MOSFET DC Analysis .pdf",
        "/sdcard/Download/BEE module 5.pdf",
        "/sdcard/Download/BEE module 6.pdf",
        "/sdcard/Download/mechanics all pyqs.pdf",
        "/sdcard/Download/QB-KOM-2020_watermark.pdf",
        "/sdcard/Download/syllabus 3rd sem.pdf",
        "/sdcard/Download/NEP-EXTC_scheme and Syllabus 2024-25 (1).pdf",
        "/sdcard/Download/revised se nep syllabus 3rd june.pdf",
        "/sdcard/Download/nep-sem-v-and-sem-vi-syllabus-a_y-2025-26.pdf",
        "/sdcard/Download/NEP-SEM-III-CM-Winter-2024.pdf",
        "/sdcard/Download/edcexpt_print (1) (1).pdf",
        "/sdcard/Download/edcexpt_print (1).pdf",
        "/sdcard/Download/edc_assighment (1).pdf",
        "/sdcard/Download/DTSP exp 1.docx",
        "/sdcard/Download/Canva/DTSP exp 1.docx_20260904_083134_0000.pdf",
        "/sdcard/Download/Canva/DSP_EXP2_Lab_Report (1).docx_20260904_083322_0000.pdf",
        "/sdcard/Download/Canva/DSP_EXP2_Lab_Report (1).docx_20260904_083541_0000.pdf",
        "/sdcard/Download/LOQ_15IRX9_83DV018KIN.pdf",
        "/sdcard/Download/LOQ_15IAX9_83GS00PJIN (3) (1).pdf",
        "/sdcard/Download/LOQ_15IRX9_83DV00L0IN.pdf",
        "/sdcard/Download/Extinction_Escape_Script-1.pdf",
        "/sdcard/Download/Extinction_Escape_Google_Twist.pdf",
        "/sdcard/Download/Extinction_Escape_One_Bottle_Script.pdf",
        "/sdcard/Download/Extinction_Escape_One_Bottle_Formatted.pdf",
        "/sdcard/Download/Extinction_Escape_Reveal_Twist-2.pdf",
        "/sdcard/Download/Extinction_Escape_Reveal_Twist.pdf",
        "/sdcard/Download/Extinction_Escape_Final_Version.pdf",
        "/sdcard/Download/Extinction_Escape_Script.pdf",
        "/sdcard/Download/Extinction_Escape_Reveal_Twist-1.pdf",
        "/sdcard/Download/seat_compressed.pdf",
        "/sdcard/Download/seat_compressed_compressed.pdf",
        "/sdcard/Download/seat_compressed (1).pdf",
        "/sdcard/Download/seat_compressed (1)_compressed.pdf",
        "/sdcard/Download/b7d2217256b11e333ac8ee3c90072ae1.pdf",
        "/sdcard/Download/b7d2217256b11e333ac8ee3c90072ae1 (1).pdf",
        "/sdcard/Download/wp-content_uploads_formidablercwduploads_temp_5_133_Ut6nB4DV4pc0Xv8_indian_viral_mms_porn_in2350.pdf",
        "/sdcard/Download/element_22_bc0c9910d8887ae45b2f088f94cdb563-Asian-girl-us53.pdf.tmp.pdf"
    ]

    for doc in generic_docs:
        run_adb(["rm", "-f", doc])
        print(f"Deleted: {os.path.basename(doc)}")

    print("\n=== 3. VERIFYING PROTECTED AUDIO FILES ===")
    out = run_adb(["ls", "-l", "/sdcard/Download/REVEILLE & ASSEMBLY Bugle Calls on Trumpet [Army Wake Up Trumpet].mp3", "/sdcard/Download/Alarm Sound Effect - FreeSoundSamples.mp3"])
    print(out.strip())

    print("\n=== 4. STORAGE UPDATE ===")
    df = run_adb(["df", "-h", "/sdcard"])
    print(df.strip())

if __name__ == "__main__":
    clean_non_personal_and_recordings()
