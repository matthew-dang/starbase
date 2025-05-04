import json
import os
import sys
import numpy as np
from PIL import Image
import requests
from io import BytesIO
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from embeddings.embedding_utils import get_embedding, save_embeddings
from config.config import MANIFEST_PATH

def load_manifest(manifest_path):
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    return manifest

def select_images_from_manifest(manifest):
    all_products = {}

    for brand, products in manifest.items():
        for product, colors in products.items():
            all_color_images = []
            for color, image_urls in colors.items():
                all_color_images.extend(image_urls)

            if all_color_images:
                all_products[product] = all_color_images

    return all_products

def main():
    manifest = load_manifest(MANIFEST_PATH)  # or your path if different
    all_products = select_images_from_manifest(manifest)

    final_image_paths = []
    final_embeddings = []

    for product_folder, image_urls in all_products.items():
        
        product_embeddings = []
        for img_url in image_urls:
            try:
                response = requests.get(img_url)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert('RGB')
                emb = get_embedding(image)
                product_embeddings.append(emb)
            except Exception as e:
                print(f"failed to process image {e}")
                continue

        if product_embeddings:
            avg_embedding = np.mean(np.vstack(product_embeddings), axis=0)
            # Pick the first image URL as the representative
            rep_img_url = image_urls[0]

            final_image_paths.append(rep_img_url)  # Save the URL, not a local path
            final_embeddings.append(avg_embedding)

    save_embeddings(final_image_paths, final_embeddings)

    print(f" Finished extracting embeddings for {len(final_embeddings)} products.")

if __name__ == "__main__":
    main()