# Clothing Recommendation System

This project is a full-stack web application built with Flask that recommends clothing items based on visual similarity. The core machine learning component uses PyTorch and torchvision to extract visual embeddings from images using pretrained models such as ResNet18. These embeddings power a recommendation engine that matches and suggests similar clothing items.

## Technology Stack

- **Backend:** Flask, SQLAlchemy, Flask-Login
- **Machine Learning:** PyTorch, torchvision (ResNet18/ResNet50 for visual embeddings)
- **Image Processing:** Pillow, torchvision.transforms

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/matthew-dang/style-drobe.git
cd style-drobe
pip install -r requirements.txt