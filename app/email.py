import os.path
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from flask import current_app, render_template

# 認証スコープ（メール送信権限）
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_gmail_service():
    """
    認証を行い、Gmail APIサービスを操作するためのオブジェクトを返す関数
    """
    creds = None
    # token.jsonから認証情報を読み込む
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 認証情報が無効な場合は、リフレッシュまたは再認証を試みる
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # この部分はauthenticate_gmail.pyで実行済みなので、通常は通らない
            # もしtoken.jsonがない場合は、再度認証が必要
            flow = InstalledAppFlow.from_client_secrets_file(
                'client_secret.json', SCOPES)
            creds = flow.run_local_server(port=8080)
        
        # 新しい認証情報を保存
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        service = build('gmail', 'v1', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None

def send_email(to, subject, template, **kwargs):
    """
    Gmail APIを使ってメールを送信する新しい関数
    """
    try:
        service = get_gmail_service()
        # メール本文をHTMLテンプレートから生成
        html_body = render_template(template + '.html', **kwargs)
        
        # メールメッセージを作成
        message = MIMEText(html_body, 'html')
        message['to'] = ", ".join(to) # 複数の宛先に対応
        message['from'] = 'me' # 'me'は認証済みのアカウントを指す
        message['subject'] = subject
        
        # base64エンコードして、APIで送信できる形式にする
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {'raw': encoded_message}
        
        # Gmail APIを呼び出してメールを送信
        send_message = (service.users().messages().send(userId="me", body=create_message).execute())
        print(f"Message Id: {send_message['id']} sent to {to}")

    except HttpError as error:
        print(f'An error occurred during email sending: {error}')
    except Exception as e:
        print(f"An unexpected error occurred: {e}")