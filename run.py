import os
from app import create_app

# 環境変数'FLASK_CONFIG'があればそれを使う。なければ'default'を使う
config_name = os.getenv('FLASK_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    app.run() # debug=True はconfigから読み込まれるので不要