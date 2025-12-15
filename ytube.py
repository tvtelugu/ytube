import json
import os
import streamlink
from datetime import datetime, timedelta, timezone

# Configuration
INPUT_FILE = 'ytube.json'
OUTPUT_FILE = 'playlist.m3u'

def get_ist_time():
    """Returns current time in Indian Standard Time (UTC+05:30)"""
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    ist_now = utc_now + ist_offset
    return ist_now.strftime('%Y-%m-%d %H:%M:%S IST')

def get_live_url(youtube_url):
    """
    Uses Streamlink to fetch the HLS URL.
    """
    session = streamlink.Streamlink()
    
    # Mimic a browser to avoid simple bot detection
    session.set_option("http-headers", {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.youtube.com/"
    })

    try:
        streams = session.streams(youtube_url)
        if not streams:
            return None

        # 'best' selects the highest resolution HLS stream available
        if 'best' in streams:
            return streams['best'].url
        elif 'worst' in streams:
            return streams['worst'].url
        return None

    except Exception:
        return None

def generate_playlist():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: {INPUT_FILE} not found.")
        return

    try:
        with open(INPUT_FILE, 'r', encoding='utf-8') as f:
            channels = json.load(f)
    except Exception:
        print("Error: JSON file is invalid.")
        return

    # Header with IST Timestamp
    current_time = get_ist_time()
    m3u_content = ["#EXTM3U"]
    m3u_content.append(f"# Playlist Updated: {current_time}")
    
    print(f"Starting Update: {current_time}")
    print(f"Processing {len(channels)} channels...")

    count = 0
    for channel in channels:
        name = channel.get('name', 'Unknown')
        url = channel.get('url')
        group = channel.get('group', 'General')
        logo = channel.get('logo', '')

        print(f"Fetching: {name}...", end=" ", flush=True)
        
        stream_url = get_live_url(url)

        if stream_url:
            m3u_content.append(f'#EXTINF:-1 group-title="{group}" tvg-logo="{logo}",{name}')
            m3u_content.append(stream_url)
            print("OK")
            count += 1
        else:
            print("FAILED")

    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(m3u_content))
    
    print(f"\nDone. Updated {OUTPUT_FILE} with {count} channels.")

if __name__ == "__main__":
    generate_playlist()
