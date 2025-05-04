import os
import csv
from flask import Blueprint, flash, render_template, request, redirect, url_for, jsonify, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from recommendation.recommendation_engine import generate_recommendations
from embeddings.embedding_utils import load_embeddings
from .models import User, UserPreference, UserFavorite
from . import db, login_manager
import json
from config.config import RAW_IMAGES_PATH, EMBEDDINGS_FILE, RAW_IMAGES_PATH2, RAW_IMAGES_PATH3, MANIFEST_PATH

def load_metadata():
    metadata = {}
    for path in [RAW_IMAGES_PATH, RAW_IMAGES_PATH2, RAW_IMAGES_PATH3]:
        metadata_file = os.path.join(path, "metadata.csv")
        if os.path.exists(metadata_file):
            with open(metadata_file, mode="r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    metadata[row['title']] = {
                        'price': row.get('price', 'N/A'),
                        'product_url': row.get('product_url', '#')
                    }
    return metadata

def load_manifest():
    with open(MANIFEST_PATH, 'r') as f:
        return json.load(f)
    
def find_product_in_manifest(manifest, product_name):
    for brand, products in manifest.items():
        if product_name in products:
            return brand, products[product_name]
    return None, None

main = Blueprint('main', __name__)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@main.route('/')
def home():
    return render_template('home.html', user=current_user, open_modal=None)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('home.html', open_modal='login')
    return render_template('home.html')

@main.route('/register', methods=['POST'])
def register():
    email = request.form['email'].strip().lower()

    # 1) Duplicate‑email check
    if User.query.filter_by(email=email).first():
        flash('That email is already registered. Please log in.', 'danger')
        return render_template('home.html', open_modal='register')

    # 2) Create the new user
    password = request.form['password']
    hashed_pw = generate_password_hash(password)  # defaults to pbkdf2:sha256
    new_user = User(email=email, password=hashed_pw)
    db.session.add(new_user)
    db.session.commit()

    # 3) Log them in + redirect (no more modal)
    login_user(new_user)
    flash('Successfully registered and logged in!', 'success')
    return redirect(url_for('main.quiz'))

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/quiz', methods=['GET', 'POST'])
@login_required
def quiz():
    return render_template('quiz.html')

@main.route('/dashboard')
@login_required
def dashboard():
    # Load manifest.json (all your S3 images)
    manifest = load_manifest()
    metadata = load_metadata()

    # Load embeddings (already trained on S3 images paths)
    embeddings_data = load_embeddings(EMBEDDINGS_FILE)
    image_paths = embeddings_data['paths']
    embeddings = embeddings_data['embeddings']

    # Load user preference images
    preference = UserPreference.query.filter_by(user_id=current_user.id).first()
    selected_images_web = json.loads(preference.selected_images) if preference else []

    selected_images = [os.path.join(current_app.root_path, img.lstrip('/')) for img in selected_images_web]


    # selected_images_web are already URLs from your style quiz
    query_images = selected_images.copy()

    # Load favorites
    favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()
    favorite_names = [fav.product_name for fav in favorites]

    # Match favorite products by product_name
    for fav_name in favorite_names:
        found = False
        for brand, products in manifest.items():
            if fav_name in products:
                # Pick the first image from any color
                for color_images in products[fav_name].values():
                    if color_images:
                        query_images.append(color_images[0])  # Add first image of favorite
                        found = True
                        break
            if found:
                break

    # Generate recommendations
    all_recommendations = set()
    for query_image in query_images:
        recommended_folders = generate_recommendations(query_image, image_paths, embeddings)
        all_recommendations.update(recommended_folders)

    # Build dashboard recommendation cards
    recommendations = []

    for brand, product_name in all_recommendations: 
        if brand in manifest and product_name in manifest[brand]:
            color_images = manifest[brand][product_name]

            first_image = None
            for images in color_images.values():
                if images:
                    first_image = images[0]
                    break

            if not first_image:
                continue
            normalized_product_name = product_name.strip()
            product_info = metadata.get(normalized_product_name, {'price': 'N/A', 'product_url': '#'})

            recommendations.append({
                'folder': product_name,
                'website': brand,
                'colors': color_images,
                'main_image': first_image,
                'price': product_info['price']
            })

    return render_template('dashboard.html', recommendations=recommendations, favorite_names=favorite_names)

@main.route('/product/<product_name>')
def product_detail(product_name):
    manifest = load_manifest()
    metadata = load_metadata()

    product_brand, product_data = find_product_in_manifest(manifest, product_name)
    if not product_data:
        return "Product not found", 404

    colors = {}
    for color_name, images in product_data.items():
        colors[color_name] = images

    normalized_product_name = product_name.strip()
    product_info = next((info for title, info in metadata.items() if title.lower().strip() == normalized_product_name.lower()), None)
    if not product_info:
        product_info = {'price': 'N/A', 'product_url': '#'}

    return render_template('product_detail.html', 
                           product_name=product_name, 
                           colors=colors, 
                           product_info=product_info,
                           brand=product_brand)

def matches_style(text, keywords):
    return any(keyword in text.lower() for keyword in keywords)

@main.route('/favorite', methods=['POST'])
@login_required
def favorite():
    data = request.get_json()
    product_name = data.get('product_name')

    if not product_name:
        return jsonify({'status': 'error', 'message': 'No product name provided'}), 400

    # Check if already favorited
    existing_favorite = UserFavorite.query.filter_by(user_id=current_user.id, product_name=product_name).first()
    if existing_favorite:
        return jsonify({'status': 'success'})  # Already favorited, do nothing

    # Save new favorite
    new_favorite = UserFavorite(user_id=current_user.id, product_name=product_name)
    db.session.add(new_favorite)
    db.session.commit()

    return jsonify({'status': 'success'})

@main.route('/unfavorite', methods=['POST'])
@login_required
def unfavorite():
    data = request.get_json()
    product_name = data.get('product_name')

    if not product_name:
        return jsonify({'status': 'error', 'message': 'No product name provided'}), 400

    # Remove from UserFavorite table
    favorite = UserFavorite.query.filter_by(user_id=current_user.id, product_name=product_name).first()
    if favorite:
        db.session.delete(favorite)
        db.session.commit()

    return jsonify({'status': 'success'})

@main.route('/favorites')
@login_required
def favorites_page():
    manifest = load_manifest()
    metadata = load_metadata()

    favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()
    favorite_names = [fav.product_name for fav in favorites]

    favorite_items = []

    for product_name in favorite_names:
        product_brand, product_data = find_product_in_manifest(manifest, product_name)
        if not product_data:
            continue

        colors = {color: images for color, images in product_data.items()}

        first_image = None
        for image_list in colors.values():
            if image_list:
                first_image = image_list[0]
                break

        if not first_image:
            continue

        normalized_product_name = product_name.strip()
        product_info = next((info for title, info in metadata.items() if title.lower().strip() == normalized_product_name.lower()), None)
        if not product_info:
            product_info = {'price': 'N/A', 'product_url': '#'}

        favorite_items.append({
            'folder': product_name,
            'website': product_brand,
            'colors': colors,
            'main_image': first_image,
            'price': product_info['price'],
            'product_url': product_info['product_url']
        })

    return render_template('favorites.html', favorites=favorite_items)

@main.route('/review')
def review():
    return render_template('review.html')


@main.route('/submit_final', methods=['POST'])
@login_required
def submit_final():
    data = request.get_json()
    images = data.get('images', [])

    if not images:
        return jsonify({'status': 'error', 'message': 'No images provided'}), 400

    # Save final selected images under selected_images
    preference = UserPreference.query.filter_by(user_id=current_user.id).first()
    if preference:
        preference.selected_images = json.dumps(images)
    else:
        preference = UserPreference(
            user_id=current_user.id,
            selected_images=json.dumps(images)
        )
        db.session.add(preference)

    db.session.commit()

    print("Final selected images saved to selected_images:", images)
    return jsonify({'status': 'success'})
