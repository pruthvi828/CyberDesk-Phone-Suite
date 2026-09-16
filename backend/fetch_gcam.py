import urllib.request
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
url = 'https://www.celsoazevedo.com/files/android/google-camera/dev-bsg/f/dl390/'
req = urllib.request.Request(url, headers=headers)
html = urllib.request.urlopen(req, timeout=10).read().decode('utf-8', errors='ignore')

apk_links = re.findall(r'href="([^"]+\.apk)"', html)
for l in apk_links:
    print("APK:", l)
