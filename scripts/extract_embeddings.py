import sys
import os
import numpy as np
from PIL import Image

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from embeddings.embedding_utils import get_embedding, save_embeddings
from config.config import RAW_IMAGES_PATH, RAW_IMAGES_PATH2, RAW_IMAGES_PATH3

def select_images_for_model(root):
    all_products = {}

    for product_folder in os.listdir(root):
        product_path = os.path.join(root, product_folder)
        if not os.path.isdir(product_path):
            continue

        all_color_images = []
        for color_folder in os.listdir(product_path):
            color_path = os.path.join(product_path, color_folder)
            if not os.path.isdir(color_path):
                continue

            for img_file in os.listdir(color_path):
                if img_file.lower().endswith(('jpg', 'jpeg', 'png')):
                    img_path = os.path.join(color_path, img_file)
                    all_color_images.append(img_path)

        if all_color_images:
            all_products[product_folder] = all_color_images

    return all_products

def main():
    products_1 = select_images_for_model(RAW_IMAGES_PATH)
    products_2 = select_images_for_model(RAW_IMAGES_PATH2)
    products_3 = select_images_for_model(RAW_IMAGES_PATH3)

    all_products = {**products_1, **products_2, **products_3}

    final_image_paths = []
    final_embeddings = []

    for product_folder, image_paths in all_products.items():
        product_embeddings = []
        for img_path in image_paths:
            emb = get_embedding(img_path)
            product_embeddings.append(emb)

        if product_embeddings:
            avg_embedding = np.mean(np.vstack(product_embeddings), axis=0)
            # Pick a representative image (like first one)
            rep_img_path = image_paths[0]

            final_image_paths.append(rep_img_path)
            final_embeddings.append(avg_embedding)

    save_embeddings(final_image_paths, final_embeddings)

if __name__ == "__main__":
    main()