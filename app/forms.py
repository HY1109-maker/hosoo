from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, HiddenField, IntegerField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional, NumberRange
from app.models import User # --- Userモデルをインポート ---

class LoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = StringField('パスワード', validators=[DataRequired()])
    remember_me = BooleanField('ログインを記録する')
    submit = SubmitField('サインイン')

class RegistrationForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    password2 = PasswordField(
        '確認用パスワード', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('登録')
    
    # check whether the username is already used or not
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('別のユーザー名を使用してください')
        
    
    # check whether the email is already used or not
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('別のメールアドレスを使用してください')


class ProductForm(FlaskForm):
    item_number = StringField('品番', validators=[DataRequired()])
    name = StringField('品名', validators=[DataRequired()])
    stock_quantity = IntegerField('在庫数', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('保存')