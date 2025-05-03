import os
import torch
import numpy as np
from PIL import Image
from torchvision import transforms
from embeddings.embedding_model import EmbeddingModel

# Define image transformations (resize, normalize)
preprocess = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the pretrained ResNet50 model
model = EmbeddingModel()
model.eval()

def get_embedding(image_path):
    img = Image.open(image_path).convert('RGB')
    img_tensor = preprocess(img).unsqueeze(0).to(device)  # Add batch dimension
    with torch.no_grad():
        embedding = model(img_tensor)
    return embedding.squeeze().cpu().numpy()


def save_embeddings(image_paths, embeddings, filename='embeddings.npy'):
    np.save(filename, {'paths': image_paths, 'embeddings': embeddings})

def load_embeddings(filename='embeddings.npy'):
    return np.load(filename, allow_pickle=True).item()