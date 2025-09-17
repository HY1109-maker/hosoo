import os
from app import create_app, db
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler
from app.tasks import check_stock_levels

# 環境変数'FLASK_CONFIG'があればそれを使う。なければ'default'を使う
config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)
migrate = Migrate(app, db)

if __name__ == '__main__':
    # scheduler
    scheduler = BackgroundScheduler(daemon=True)
    # every 9:30 am, running check_stock_levels
    # in this test interval, seconds=30 , every 30sec 
    scheduler.add_job(check_stock_levels, 'cron', hour=9, minute=30)

    scheduler.start()

    app.run() # debug=True はconfigから読み込まれるので不要