import json
import os
import yt_dlp
import streamlink
from datetime import datetime, timedelta, timezone

# Configuration
INPUT_FILE = 'ytube.json'
OUTPUT_FILE = 'playlist.m3u'

def get_ist_time():
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    return (utc_now + ist_offset).strftime('%Y-%m-%d %H:%M:%S IST')

# --- STRATEGY 1: Streamlink ---
def fetch_streamlink(url):
    try:
        session = streamlink.Streamlink()
        session.set_option("http-headers", {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.youtube.com/"
        })
        streams = session.streams(url)
        if streams and 'best' in streams:
            return streams['best'].url
    except Exception:
        pass
    return None

# --- STRATEGY 2: yt-dlp (iOS Client) ---
def fetch_ytdlp_ios(url):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'extractor_args': {'youtube': {'player_client': ['ios']}}, # Pretend to be an iPhone
        'geo_bypass': True,
    }
    return run_ytdlp(url, opts)

# --- STRATEGY 3: yt-dlp (Android Client) ---
def fetch_ytdlp_android(url):
    opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'extractor_args': {'youtube': {'player_client': ['android']}}, # Pretend to be Android
        'geo_bypass': True,
    }
    return run_ytdlp(url, opts)

def run_ytdlp(url, opts):
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            # Check direct URL
            if info.get('url') and '.m3u8' in info.get('url', ''):
                return info['url']
            # Check formats
            formats = info.get('formats', [])
            m3u8 = [f for f in formats if 'm3u8' in f.get('protocol', '')]
            if m3u8:
                return m3u8[0]['url']
    except Exception:
        pass
    return None

def generate_playlist():
    if not os.path.exists(INPUT_FILE):
        print("Error: ytube.json not found.")
        return

    try:
        with open(INPUT_FILE, 'r') as f:
            channels = json.load(f)
    except:
        print("Error: Invalid JSON.")
        return

    current_time = get_ist_time()
    m3u_content = [
        "#EXTM3U",
        f"# Playlist Updated: {current_time}",
        "# User-Agent: Mozilla/5.0" 
    ]
    
    print(f"Update Started: {current_time}")
    
    count = 0
    for channel in channels:
        name = channel.get('name', 'Unknown')
        url = channel.get('url')
        group = channel.get('group', 'General')
        logo = channel.get('logo', '')

        print(f"Fetching: {name}...", end=" ", flush=True)

        # Try Strategy 1
        link = fetch_streamlink(url)
        
        # Try Strategy 2 if 1 failed
        if not link:
            link = fetch_ytdlp_ios(url)
            
        # Try Strategy 3 if 1 & 2 failed
        if not link:
            link = fetch_ytdlp_android(url)

        if link:
            print("OK")
            m3u_content.append(f'#EXTINF:-1 group-title="{group}" tvg-logo="{logo}",{name}')
            m3u_content.append(link)
            count += 1
        else:
            print("FAILED (All methods)")

    with open(OUTPUT_FILE, 'w') as f:
        f.write("\n".join(m3u_content))
    
    print(f"\nDone. Saved {count} channels to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_playlist()
