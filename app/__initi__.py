from flask import Flask
from config import config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name='default'):
    # application factory function
    app = Flask(__name__)

    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from . import models
    with app.app_context():
        db.create_all()

    return app