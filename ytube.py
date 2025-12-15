import json
import re
import requests
import os

# Configuration
INPUT_FILE = 'ytube.json'
OUTPUT_FILE = 'playlist.m3u'

def get_direct_hls(youtube_url):
    session = requests.Session()
    # Headers mimic a real browser to avoid "Consent" pages
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.youtube.com/',
    }

    try:
        print(f"  [GET] Downloading source...", end=" ", flush=True)
        response = session.get(youtube_url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Status {response.status_code}")
            return None

        html = response.text

        # Regex to find the hlsManifestUrl
        # We capture the value inside the quotes
        pattern = r'"hlsManifestUrl":"(https://manifest\.googlevideo\.com/api/manifest/hls_variant/.*?)"'
        match = re.search(pattern, html)

        if match:
            raw_url = match.group(1)
            # Fix escaped slashes (e.g., https:\/\/ -> https://)
            clean_url = raw_url.replace('\\/', '/')
            print("Found!")
            return clean_url
        else:
            print("Not found (Offline/Geo-blocked)")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_playlist():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except Exception as e:
        print(f"JSON Error: {e}")
        return

    m3u_content = ["#EXTM3U"]
    
    print(f"Processing {len(channels)} channels...")

    for channel in channels:
        name = channel.get('name', 'Unknown')
        url = channel.get('url')
        group = channel.get('group', 'General')
        logo = channel.get('logo', '')

        print(f"Checking: {name}")
        
        if not url: continue

        stream_url = get_direct_hls(url)

        if stream_url:
            m3u_content.append(f'#EXTINF:-1 group-title="{group}" tvg-logo="{logo}",{name}')
            m3u_content.append(stream_url)
        else:
            print(f"  [OFFLINE] Skipping {name}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(m3u_content))
    
    print(f"\nSaved to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_playlist()
