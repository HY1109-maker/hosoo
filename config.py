import os

# アプリケーションのルートディレクトリのパスを取得
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    全ての設定の基本となるベースクラス
    """
    # 全ての環境で共通の設定
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.googleemail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    MAIL_SENDER = f"在庫管理システム <{os.environ.get('MAIL_USERNAME')}>"

class DevelopmentConfig(Config):
    """
    開発環境用の設定
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'db.sqlite')

class ProductionConfig(Config):
    """
    本番環境用の設定
    """
    DEBUG = False
    # 本番環境ではPostgreSQLなど、より堅牢なデータベースを使うのが一般的
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'db.sqlite')

# 使用する設定を辞書にまとめる
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}