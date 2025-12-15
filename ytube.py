import json
import os
import yt_dlp
import streamlink
from datetime import datetime, timedelta, timezone

# Configuration
INPUT_FILE = 'ytube.json'
OUTPUT_FILE = 'playlist.m3u'
COOKIE_FILE = 'cookies.txt'  # <--- NEW CONFIG

def get_ist_time():
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    return (utc_now + ist_offset).strftime('%Y-%m-%d %H:%M:%S IST')

def fetch_with_ytdlp(url):
    """
    Uses yt-dlp with Cookies to bypass the 'Bot' check.
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'live_from_start': True,
        'geo_bypass': True,
    }

    # IMPORTANT: Use cookies if the file exists
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # 1. Check direct URL
            if info.get('url') and '.m3u8' in info.get('url', ''):
                return info['url']
            
            # 2. Check formats
            formats = info.get('formats', [])
            m3u8_formats = [f for f in formats if 'm3u8' in f.get('protocol', '')]
            
            if m3u8_formats:
                # Return the best quality m3u8
                return m3u8_formats[0]['url']
    except Exception:
        pass
    return None

def fetch_with_streamlink(url):
    """
    Fallback method using Streamlink
    """
    try:
        session = streamlink.Streamlink()
        session.set_option("http-headers", {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
            "Referer": "https://www.youtube.com/"
        })
        streams = session.streams(url)
        if streams and 'best' in streams:
            return streams['best'].url
    except Exception:
        pass
    return None

def generate_playlist():
    if not os.path.exists(INPUT_FILE):
        print("Error: ytube.json missing.")
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
    ]
    
    print(f"Update Started: {current_time}")
    
    if os.path.exists(COOKIE_FILE):
        print(f"Authentication: Using {COOKIE_FILE}")
    else:
        print("Authentication: No cookies found (High risk of failure in Actions)")

    count = 0
    for channel in channels:
        name = channel.get('name', 'Unknown')
        url = channel.get('url')
        group = channel.get('group', 'General')
        logo = channel.get('logo', '')

        print(f"Fetching: {name}...", end=" ", flush=True)

        # 1. Try yt-dlp WITH COOKIES (Best for bypassing blocks)
        link = fetch_with_ytdlp(url)
        
        # 2. Fallback to Streamlink if failed
        if not link:
            link = fetch_with_streamlink(url)

        if link:
            print("OK")
            m3u_content.append(f'#EXTINF:-1 group-title="{group}" tvg-logo="{logo}",{name}')
            m3u_content.append(link)
            count += 1
        else:
            print("FAILED")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(m3u_content))
    
    print(f"\nDone. Saved {count} channels.")

if __name__ == "__main__":
    generate_playlist()
