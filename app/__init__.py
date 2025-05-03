from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'chuhbs'
    app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///C:/Users/Matthew Dang/Desktop/style-drobe/db.sqlite'

    db.init_app(app)
    login_manager.init_app(app)

    from .routes import main
    app.register_blueprint(main)

    return app