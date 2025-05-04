
import json
import requests
from io import BytesIO
import os
from embeddings.embedding_utils import get_embedding
from embeddings.visual_search import find_similar_items
from PIL import Image
from config.config import MANIFEST_PATH
from flask import current_app
from urllib.parse import unquote, quote

with open(MANIFEST_PATH, 'r') as f:
    manifest = json.load(f)

def find_product_from_url(image_url):
    # Try quoting it
    encoded_url = quote(image_url, safe=':/')

    for brand, products in manifest.items():
        for product, colors in products.items():
            for color, images in colors.items():
                for img in images:
                    if img == encoded_url:
                        return brand, product
    return None, None

def generate_recommendations(query_image_path_or_url, image_urls, embeddings, n_neighbors=5):
    if query_image_path_or_url.startswith('http://') or query_image_path_or_url.startswith('https://'):
        response = requests.get(query_image_path_or_url)
        response.raise_for_status()
        image = Image.open(BytesIO(response.content)).convert('RGB')
    else:
        full_local_path = os.path.join(current_app.root_path, query_image_path_or_url.lstrip('/'))
        image = Image.open(full_local_path).convert('RGB')

    query_embedding = get_embedding(image)

    similar_indices = find_similar_items(query_embedding, embeddings, n_neighbors)
    
    recommended_products = []
    seen = set()

    for idx in similar_indices: 
        img_url = image_urls[idx]  # Now image_urls are full S3 URLs


        brand, product = find_product_from_url(img_url)
        
        if not brand or not product:
            print(f"No product found for {img_url}")
            continue
        
        if product and (brand, product) not in seen:
            seen.add((brand, product))
            recommended_products.append((brand, product))

    return recommended_products