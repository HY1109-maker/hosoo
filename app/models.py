from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from . import db, login_manager
from datetime import datetime
import pytz

def get_jst_now():
    return datetime.now(pytz.timezone('Asia/Tokyo'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(64), nullable=False, default='staff')
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'))
    # ▼▼▼ ユーザーからログを参照するためのリレーションシップを追加 ▼▼▼
    inventory_logs = db.relationship('InventoryLog', back_populates='user', lazy='dynamic')
    product_logs = db.relationship('ProductLog', back_populates='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Store(db.Model):
    # ...変更なし...
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    address = db.Column(db.String(128))
    inventories = db.relationship('Inventory', back_populates='store', lazy='dynamic')
    def __repr__(self):
        return f'<Store {self.name}>'

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_number = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(128), nullable=False)
    price = db.Column(db.String(128), nullable=True)
    cost = db.Column(db.String(128), nullable=True)

    inventories = db.relationship('Inventory', back_populates='product', lazy='dynamic')
    product_logs = db.relationship('ProductLog', back_populates='product', lazy='dynamic')
    def __repr__(self):
        return f'<Product {self.name}>'

class Inventory(db.Model):
    # ...変更なし...
    id = db.Column(db.Integer, primary_key=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    threshold = db.Column(db.Integer, nullable=False, default=10)
    last_updated = db.Column(db.DateTime, default=get_jst_now, onupdate=get_jst_now)
    product = db.relationship('Product', back_populates='inventories')
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    store = db.relationship('Store', back_populates='inventories')
    store_id = db.Column(db.Integer, db.ForeignKey('store.id'), nullable=False)
    # ▼▼▼ 在庫からログを参照するためのリレーションシップを追加 ▼▼▼
    inventory_logs = db.relationship('InventoryLog', back_populates='inventory', lazy='dynamic', cascade="all, delete-orphan")

# --- ▼▼▼ InventoryLogモデルを修正 ▼▼▼ ---
class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=get_jst_now, nullable=False)
    quantity_before = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer, nullable=False)
    threshold_before = db.Column(db.Integer, nullable=False)
    threshold_after = db.Column(db.Integer, nullable=False)
    # 外部キー
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # リレーションシップ
    inventory = db.relationship('Inventory', back_populates='inventory_logs')
    user = db.relationship('User', back_populates='inventory_logs')

    def __repr__(self):
        return f'<Log {self.timestamp}>'


class ProductLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=get_jst_now, nullable=False)
    change_set_id = db.Column(db.String(36), nullable=False, default=lambda: str(uuid.uuid4()))
    field_changed = db.Column(db.String(64), nullable=False) # 'name' or 'item_number'
    value_before = db.Column(db.String(128), nullable=False)
    value_after = db.Column(db.String(128), nullable=False)
    # 外部キー
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    # リレーションシップ
    product = db.relationship('Product', back_populates='product_logs')
    user = db.relationship('User', back_populates='product_logs')

    def __repr__(self):
        return f'<ProductLog {self.timestamp}>'
    
import uuid