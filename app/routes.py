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
from config.config import RAW_IMAGES_PATH, EMBEDDINGS_FILE, RAW_IMAGES_PATH2, RAW_IMAGES_PATH3

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
    # Handle form submission for quiz answers
    if request.method == 'POST':
        # Retrieve answers from the form
        answer1 = request.form.get('question1')
        answer2 = request.form.get('question2')
        answer3 = request.form.get('question3')

        # Process the answers here, save them to the database, etc.
        # For example, update the user's preferences in the database
        current_user.preference1 = answer1
        current_user.preference2 = answer2
        current_user.preference3 = answer3

        db.session.commit()

        # Redirect the user to a success page or the homepage
        flash('Quiz completed! Thanks for your answers.', 'success')
        return redirect(url_for('main.home'))

    return render_template('quiz.html')

@main.route('/dashboard')
@login_required
def dashboard():
    metadata = load_metadata()

    embeddings_data = load_embeddings(EMBEDDINGS_FILE)
    image_paths = embeddings_data['paths']
    embeddings = embeddings_data['embeddings']

    preference = UserPreference.query.filter_by(user_id=current_user.id).first()
    selected_images_web = json.loads(preference.selected_images)  # List of 6 images

    selected_images = [os.path.join(current_app.root_path, img.lstrip('/')) for img in selected_images_web]

    favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()
    favorite_names = [fav.product_name for fav in favorites]

    favorite_image_paths = []
    for name in favorite_names:
        folder_path = os.path.join(RAW_IMAGES_PATH, name)
        if not os.path.exists(folder_path):
            folder_path = os.path.join(RAW_IMAGES_PATH2, name)
        if os.path.exists(folder_path):
            for color_folder in os.listdir(folder_path):
                color_path = os.path.join(folder_path, color_folder)
                if os.path.isdir(color_path):
                    images = os.listdir(color_path)
                    if images:
                        favorite_image_paths.append(os.path.join(color_path, images[0]))
                        break

    query_images = selected_images + favorite_image_paths

    print(f"Favorite names: {favorite_names}")
    print(f"Favorite image paths: {favorite_image_paths}")
    print(f"Query images: {query_images}")

    # Generate recommendations for each query image
    all_recommendations = set()
    for query_image in query_images:
        recommended_folders = generate_recommendations(query_image, image_paths, embeddings)
        all_recommendations.update(recommended_folders)

    # Collect images from recommended folders
    recommendations = []

    for folder in all_recommendations:
        website_name = os.path.basename(os.path.dirname(folder))
        # if not folder.startswith(RAW_IMAGES_PATH) and not folder.startswith(RAW_IMAGES_PATH2):
        #     continue
        # Gather color folders and images
        color_folders = [os.path.join(folder, subfolder) for subfolder in os.listdir(folder)
                        if os.path.isdir(os.path.join(folder, subfolder))]
            
        colors = {}
        for color_folder in color_folders:
            color_name = os.path.basename(color_folder)
            images = [
                url_for('static', filename=os.path.relpath(os.path.join(color_folder, img), os.path.join(current_app.root_path, 'static')).replace('\\', '/'))
                for img in os.listdir(color_folder) if img.lower().endswith(('png', 'jpg', 'jpeg', 'avif'))
            ]
            colors[color_name] = images

        if colors:
            first_image = None
            for image_list in colors.values():
                if image_list:  # Check if the list is not empty
                    first_image = image_list[0]
                    break

            if first_image is None:
                # Handle the case where no images exist (e.g., skip this product)
                continue
            product_info = metadata.get(os.path.basename(folder), {'price': 'N/A', 'product_url': '#'})
            recommendations.append({
                'folder': os.path.basename(folder),
                'website': website_name,
                'colors': colors,
                'main_image': first_image,
                'price': product_info['price']
            })
    print(f"Total recommendations generated: {len(all_recommendations)} folders")

    favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()
    favorite_names = [fav.product_name for fav in favorites]
    return render_template('dashboard.html', recommendations=recommendations, favorite_names=favorite_names)

@main.route('/product/<product_name>')
def product_detail(product_name):
    # Locate product folder
    product_folder = None
    for path in [RAW_IMAGES_PATH, RAW_IMAGES_PATH2, RAW_IMAGES_PATH3]:
        potential_folder = os.path.join(path, product_name)
        if os.path.exists(potential_folder):
            product_folder = potential_folder
            break

    if not product_folder:
        return "Product not found", 404
    color_folders = [os.path.join(product_folder, subfolder) for subfolder in os.listdir(product_folder)
                     if os.path.isdir(os.path.join(product_folder, subfolder))]

    colors = {}
    for color_folder in color_folders:
        color_name = os.path.basename(color_folder)
        images = [
            url_for('static', filename=os.path.relpath(os.path.join(color_folder, img), os.path.join(current_app.root_path, 'static')).replace('\\', '/'))
            for img in os.listdir(color_folder) if img.lower().endswith(('png', 'jpg', 'jpeg', 'avif'))
        ]
        colors[color_name] = images

    # Optionally load metadata like product_url, price
    metadata = load_metadata()
    product_info = metadata.get(product_name, {'price': 'N/A', 'product_url': '#'})

    return render_template('product_detail.html', product_name=product_name, colors=colors, product_info=product_info)

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
    # Load user's favorites
    favorites = UserFavorite.query.filter_by(user_id=current_user.id).all()
    favorite_names = [fav.product_name for fav in favorites]

    # Gather images for each favorite product
    favorite_items = []
    for name in favorite_names:
        product_folder = None
        for path in [RAW_IMAGES_PATH, RAW_IMAGES_PATH2, RAW_IMAGES_PATH3]:
            potential_folder = os.path.join(path, name)
            if os.path.exists(potential_folder):
                product_folder = potential_folder
                break

        if not product_folder:
            continue  # Skip if folder doesn't exist

        color_folders = [os.path.join(product_folder, subfolder) for subfolder in os.listdir(product_folder)
                         if os.path.isdir(os.path.join(product_folder, subfolder))]

        colors = {}
        for color_folder in color_folders:
            color_name = os.path.basename(color_folder)
            images = [
                url_for('static', filename=os.path.relpath(os.path.join(color_folder, img), os.path.join(current_app.root_path, 'static')).replace('\\', '/'))
                for img in os.listdir(color_folder) if img.lower().endswith(('png', 'jpg', 'jpeg', 'avif'))
            ]
            colors[color_name] = images

        if colors:
            first_image = None
            for image_list in colors.values():
                if image_list:
                    first_image = image_list[0]
                    break

            favorite_items.append({
                'folder': name,
                'colors': colors,
                'main_image': first_image
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