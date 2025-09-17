from app import create_app, db
from app.models import Inventory, User
from app.email import send_email
from flask import render_template

def check_stock_levels():
    app = create_app()
    with app.app_context():
        print("checking stock levels ...")

        low_stock_items = Inventory.query.filter(Inventory.quantity <= Inventory.threshold).all()

        if low_stock_items:
            print(f"Found {len(low_stock_items)} low stock items.")

            recipients = [user.email for user in User.query.filter_by(role='admin').all()]

            if not recipients:
                print('No recipients found')
                return
            
            send_email(
                recipients,
                '【デイリーレポート】在庫アラート通知',
                'email/summary_alert',
                items=low_stock_items
            )
            print(f"Stock alert summary sent to {recipients}")
        
        else:
            print("No low stock items found.")