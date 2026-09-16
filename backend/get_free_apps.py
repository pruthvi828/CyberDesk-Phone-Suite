import urllib.request
import re

url = 'https://onstream.to/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        matches = re.findall(r'https?://[^\s"\'<>]+', html)
        apk_links = [m for m in matches if 'apk' in m.lower() or 'download' in m.lower() or 'tv' in m.lower()]
        print("Matches found:")
        for link in set(apk_links):
            print(link)
except Exception as e:
    print("Error:", e)
