from sklearn.neighbors import NearestNeighbors
import numpy as np

def find_similar_items(query_embedding, all_embeddings, n_neighbors=3):
    knn = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine')
    knn.fit(all_embeddings)
    _, indices = knn.kneighbors(query_embedding.reshape(1, -1))
    return indices[0]