import os
import json
import sys
from urllib.parse import quote
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from config.config import BASE_FOLDER
BASE_URL = "https://starbase-images.s3.us-east-2.amazonaws.com"

ALLOWED_BRANDS = ['Abercrombie', 'H&M', 'Zara']

manifest = {}

for brand in os.listdir(BASE_FOLDER):
    if brand not in ALLOWED_BRANDS:
        continue

    brand_path = os.path.join(BASE_FOLDER, brand)
    if not os.path.isdir(brand_path):
        continue

    for product in os.listdir(brand_path):
        product_path = os.path.join(brand_path, product)
        if not os.path.isdir(product_path):
            continue

        for color in os.listdir(product_path):
            color_path = os.path.join(product_path, color)
            if not os.path.isdir(color_path):
                continue

            images = []
            for img_file in os.listdir(color_path):
                if img_file.lower().endswith(('jpg', 'jpeg', 'png', 'avif')):
                    image_url = f"{BASE_URL}/{quote(brand)}/{quote(product)}/{quote(color)}/{quote(img_file)}"
                    images.append(image_url)

            if images:
                manifest.setdefault(brand, {}).setdefault(product, {})[color] = images

with open('manifest.json', 'w') as f:
    json.dump(manifest, f, indent=2)

