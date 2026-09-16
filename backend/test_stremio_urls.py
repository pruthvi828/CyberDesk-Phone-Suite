import urllib.request
import re

url = "https://www.stremio.com/downloads"
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    html = resp.read().decode('utf-8', errors='replace')

for m in re.finditer(r'href=[\'"](https://dl\.strem\.io/android/[^\'"]+)[\'"]', html):
    link = m.group(1)
    if "apk" in link:
        print(link)
