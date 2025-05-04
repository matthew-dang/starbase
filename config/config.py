import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

STATIC_FOLDER = os.path.join(BASE_DIR, 'app', 'static')

RAW_IMAGES_PATH = os.path.join(STATIC_FOLDER, 'H&M')
RAW_IMAGES_PATH2 = os.path.join(STATIC_FOLDER, 'Zara')
RAW_IMAGES_PATH3 = os.path.join(STATIC_FOLDER, 'Abercrombie')

PROCESSED_IMAGES_PATH = os.path.join(BASE_DIR, 'scripts')

EMBEDDINGS_FILE = os.path.join(PROCESSED_IMAGES_PATH, 'embeddings.npy')

MANIFEST_PATH = os.path.join(STATIC_FOLDER, 'manifest.json')

S3_BASE_URL = "https://starbase-images.s3.us-east-2.amazonaws.com"