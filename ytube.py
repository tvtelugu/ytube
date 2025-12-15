import json
import yt_dlp
import os

# Configuration
INPUT_FILE = 'ytube.json'
OUTPUT_FILE = 'playlist.m3u'

def get_live_url(youtube_url):
    # 'all' fetches everything so we don't get "format not available" errors
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'all', 
        'live_from_start': True,
        'geo_bypass': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            
            # METHOD: Manually filter for the HLS (.m3u8) stream
            formats = info.get('formats', [])
            
            # Find all formats that are m3u8
            m3u8_formats = [f for f in formats if 'm3u8' in f.get('protocol', '') or '.m3u8' in f.get('url', '')]
            
            if not m3u8_formats:
                return None

            # Sort by bitrate (highest quality first) and take the best one
            best_format = sorted(m3u8_formats, key=lambda x: x.get('tbr', 0) or 0, reverse=True)[0]
            return best_format['url']
                
    except Exception as e:
        # If it fails, return None so we can skip it
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

    # Start the playlist
    m3u_content = ["#EXTM3U"]
    count = 0
    
    print(f"Processing {len(channels)} channels...")

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
            print("FAILED (Offline or Blocked)")

    # Only write file if we actually found something (or just write header)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(m3u_content))
    
    print(f"\nDone. Added {count} channels to {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_playlist()
