from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, LoginManager
from . import db, login_manager
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_number = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, default=0)
    
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
