import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# このスクリプトが要求する権限（今回はメール送信のみ）
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    """
    Googleの認証フローを実行し、token.jsonを生成するスクリプト。
    初回実行時のみ使用する。
    """
    creds = None
    # 既にtoken.jsonが存在するかチェック
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # トークンが存在しないか、無効な場合に認証フローを開始
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        
        # 新しく取得した認証情報（トークン）を保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    
    print("認証に成功しました！ 'token.json' が作成されました。")
    print("このファイルも .gitignore に追加するのを忘れないでください。")

if __name__ == '__main__':
    main()