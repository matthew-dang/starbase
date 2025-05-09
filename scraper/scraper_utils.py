import os
import requests
from urllib.parse import urlparse
from PIL import Image
from io import BytesIO


def download_image(url, folder, min_width=200, min_height=200):
    if not url or not url.startswith('http'):
        print(f"Invalid URL: {url}")
        return

    os.makedirs(folder, exist_ok=True)
    filename = os.path.basename(url.split("?")[0])
    filepath = os.path.join(folder, filename)

    if os.path.exists(filepath):
        print(f"Downloaded {url} already")
        return
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": url,
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    }

    try:
        response = requests.get(url, headers=headers, stream=True)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            width, height = img.size
            if width < min_width or height < min_height:
                print(f"Skipped image {url} due to small size ({width}x{height})")
                return

            img.save(filepath)
            print(f"Downloaded {url} to {folder}")
        else:
            print(f"Failed to download: {url}")
    except Exception as e:
        print(f"Error downloading image {url}: {e}")