import os
import logging

from app import create_app, db
from flask_migrate import Migrate
from app.models import User, Store, Product, Inventory, InventoryLog, ProductLog 

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# 環境変数'FLASK_CONFIG'があればそれを使う。なければ'default'を使う
config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)
migrate = Migrate(app, db)

# flask shell で便利に使うための設定は残す
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 'Store': Store, 'Product': Product, 
        'Inventory': Inventory, 'InventoryLog': InventoryLog, 'ProductLog': ProductLog
    }

if __name__ == '__main__':
    from apscheduler.schedulers.background import BackgroundScheduler
    from app.tasks import check_stock_levels
    # scheduler
    scheduler = BackgroundScheduler(daemon=True)
    # every 9:30 am, running check_stock_levels
    # in this test interval, seconds=60 , mail will send every 60sec. 
    scheduler.add_job(check_stock_levels, 'interval', seconds=30)
    # 本番用: scheduler.add_job(check_stock_levels, 'cron', hour=9, minute=30)
    scheduler.start()

    app.run(use_reloader=False) # debug=True はconfigから読み込まれるので不要