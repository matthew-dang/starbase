import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
RAW_IMAGES_PATH = os.path.join(BASE_DIR, 'app', 'static', 'H&M')
PROCESSED_IMAGES_PATH = os.path.join(BASE_DIR, 'scripts')
EMBEDDINGS_FILE = os.path.join(PROCESSED_IMAGES_PATH,'embeddings.npy')
RAW_IMAGES_PATH2 = os.path.join(BASE_DIR, 'app', 'static', 'Zara')
RAW_IMAGES_PATH3 = os.path.join(BASE_DIR, 'app', 'static', 'Abercrombie')