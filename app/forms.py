from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, HiddenField, FieldList, FormField, SelectField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional, NumberRange
from app.models import User, Product, Store, Inventory # --- Userモデルをインポート ---
from flask_wtf.file import FileField, FileRequired, FileAllowed

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

class CsvUploadForm(FlaskForm):
    csv_file = FileField('CSV/Excelファイル', validators=[
        FileRequired(),
        FileAllowed(['csv', 'xlsx'], 'CSVまたはExcelファイルを選択してください')
    ])

    submit = SubmitField('データをインポート')

class AdminEditProfileForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()], render_kw={'readonly': True})
    email = StringField('メールアドレス', validators=[DataRequired(), Email()])
    # 役割を選択するためのドロップダウンリスト
    role = SelectField('役割', choices=[
        ('staff', 'スタッフ'),
        ('manager', 'マネージャー'),
        ('admin', '管理者')
    ], validators=[DataRequired()])
    # 所属店舗を選択するためのドロップダウンリスト
    store = SelectField('所属店舗', coerce=int)
    submit = SubmitField('更新')

    def __init__(self, user, *args, **kwargs):
        super(AdminEditProfileForm, self).__init__(*args, **kwargs)
        # 店舗の選択肢を動的に設定
        self.store.choices = [(s.id, s.name) for s in Store.query.order_by('name').all()]
        # 「未所属」の選択肢を追加
        self.store.choices.insert(0, (0, '--- 未所属 ---'))
        self.user = user

    # 自分以外のユーザーで、メールアドレスが既に使われていないかチェック
    def validate_email(self, email):
        if email.data != self.user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('このメールアドレスは既に使用されています。')
            
class StoreForm(FlaskForm):
    name = StringField('店舗名', validators=[DataRequired()])
    address = StringField('住所')
    submit = SubmitField('保存')

    def validate_name(self, name):
        store = Store.query.filter_by(name=name.data).first()
        if store:
            raise ValidationError('この店舗名は既に使用されています。')
        
        
class EditProductForm(FlaskForm):
    item_number = StringField('品番', validators=[DataRequired()])
    name = StringField('商品名', validators=[DataRequired()])
    price = IntegerField('販売価格', validators=[Optional(), NumberRange(min=0)]) # Optionalで未入力も許可
    cost = IntegerField('原価', validators=[Optional(), NumberRange(min=0)])     # NumberRangeで0以上の整数を強制
    submit = SubmitField('更新')

    # 品番の重複チェックのための初期化
    def __init__(self, original_item_number, *args, **kwargs):
        super(EditProductForm, self).__init__(*args, **kwargs)
        self.original_item_number = original_item_number # 元の品番を保持

    # 品番が、自分以外の既存商品と重複していないかチェックするバリデータ
    def validate_item_number(self, item_number):
        if item_number.data != self.original_item_number: # 品番が変更された場合のみチェック
            product = Product.query.filter_by(item_number=item_number.data).first()
            if product:
                raise ValidationError('この品番は既に使用されています。')
            


