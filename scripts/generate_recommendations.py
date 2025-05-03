import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from recommendation.recommendation_engine import generate_recommendations
from recommendation.user_interaction import get_user_query, display_recommendations
from embeddings.embedding_utils import load_embeddings
from config.config import EMBEDDINGS_FILE


def main():
    # Load embeddings
    embeddings_data = load_embeddings(EMBEDDINGS_FILE)
    image_paths = embeddings_data['paths']
    embeddings = embeddings_data['embeddings']
    
    # Get user query
    query_image_path = get_user_query()
    
    # Generate recommendations
    recommendations = generate_recommendations(query_image_path, image_paths, embeddings)
    
    # Display recommendations
    display_recommendations(recommendations)
    
if __name__ == "__main__":
    main()