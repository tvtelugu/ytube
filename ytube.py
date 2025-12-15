import json
import os
import yt_dlp
import streamlink
from datetime import datetime, timedelta, timezone

# Configuration
INPUT_FILE = 'ytube.json'
M3U_FILE = 'playlist.m3u'
TXT_FILE = 'playlist.txt'   # <--- NEW OUTPUT FILE
COOKIE_FILE = 'cookies.txt'

def get_ist_time():
    utc_now = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    return (utc_now + ist_offset).strftime('%Y-%m-%d %H:%M:%S IST')

def fetch_with_ytdlp(url):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
        'live_from_start': True,
        'geo_bypass': True,
    }
    if os.path.exists(COOKIE_FILE):
        ydl_opts['cookiefile'] = COOKIE_FILE

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get('url') and '.m3u8' in info.get('url', ''):
                return info['url']
            formats = info.get('formats', [])
            m3u8_formats = [f for f in formats if 'm3u8' in f.get('protocol', '')]
            if m3u8_formats:
                return m3u8_formats[0]['url']
    except Exception:
        pass
    return None

def fetch_with_streamlink(url):
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
    
    # Initialize M3U Content
    m3u_content = [
        "#EXTM3U",
        f"# Playlist Updated: {current_time}",
    ]

    # Initialize TXT Content
    txt_content = [
        f"Playlist Updated: {current_time}",
        "===================================="
    ]
    
    print(f"Update Started: {current_time}")
    if os.path.exists(COOKIE_FILE):
        print(f"Authentication: Using {COOKIE_FILE}")

    count = 0
    for channel in channels:
        name = channel.get('name', 'Unknown')
        url = channel.get('url')
        group = channel.get('group', 'General')
        logo = channel.get('logo', '')

        print(f"Fetching: {name}...", end=" ", flush=True)

        link = fetch_with_ytdlp(url)
        if not link:
            link = fetch_with_streamlink(url)

        if link:
            print("OK")
            # Add to M3U
            m3u_content.append(f'#EXTINF:-1 group-title="{group}" tvg-logo="{logo}",{name}')
            m3u_content.append(link)
            
            # Add to TXT
            txt_content.append(f"\nChannel: {name}")
            txt_content.append(f"Link: {link}")
            
            count += 1
        else:
            print("FAILED")

    # Save M3U
    with open(M3U_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(m3u_content))

    # Save TXT
    with open(TXT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(txt_content))
    
    print(f"\nDone. Saved {count} channels to {M3U_FILE} and {TXT_FILE}")

if __name__ == "__main__":
    generate_playlist()
