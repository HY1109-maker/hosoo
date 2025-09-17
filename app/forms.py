from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, HiddenField, FieldList, FormField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional, NumberRange
from app.models import User, Product, Store, Inventory # --- Userモデルをインポート ---

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
    # store = SelectField('店舗', coerce=int, validators=[DataRequired()])

    item_number = StringField('品番', validators=[DataRequired()])
    name = StringField('プロダクト名', validators=[DataRequired()])

    # stock_quantity = IntegerField('初期在庫数', validators=[DataRequired(), NumberRange(min=0)])

    submit = SubmitField('商品を登録')

    def validate_item_number(self, item_number):
        product = Product.query.filter_by(item_number=item_number.data).first()
        if product is not None:
            raise ValidationError('この商品は既に使用されています。')


class EditInventoryForm(FlaskForm):
    quantity = IntegerField('新しい在庫数', validators=[DataRequired(), NumberRange(min=0)])
    threshold = IntegerField('警告閾値', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('更新')


class InventoryEntryForm(FlaskForm):
    store_id = HiddenField()
    store_name = StringField('ストア名', render_kw={'readonly': True})
    quantity = IntegerField('初期在庫数', default=0, validators=[DataRequired(), NumberRange(min=0)])

    class Meta:
        csrf = False

class AllocateInventoryForm(FlaskForm):
    inventories = FieldList(FormField(InventoryEntryForm))
    submit = SubmitField('全店舗の在庫を保存')