import os
from embeddings.embedding_utils import get_embedding
from embeddings.visual_search import find_similar_items
import clip
import torch
from PIL import Image

device = "cuda" if torch.cuda.is_available() else "cpu"
clip_model, preprocess_clip = clip.load("ViT-B/32", device=device)

def generate_recommendations(query_image_path, image_paths, embeddings, n_neighbors=5):
    query_embedding = get_embedding(query_image_path)
    similar_indices = find_similar_items(query_embedding, embeddings, n_neighbors)
    
    recommended_folders = []
    for idx in similar_indices: 
        img_path = image_paths[idx]
        folder_path = os.path.dirname(img_path)           # e.g. raw_images/Shirt_001/Black
        product_folder = os.path.dirname(folder_path)     # e.g. raw_images/Shirt_001
        recommended_folders.append(product_folder)

    seen = set()
    unique_folders = []
    for folder in recommended_folders:
        if folder not in seen:
            seen.add(folder)
            unique_folders.append(folder)

    return unique_folders
