from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Product
from . import db
from .forms import RegistrationForm, LoginForm, ProductForm

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
def index():
    # from DB, all post data is obtained with time order
    return render_template('index.html', title='Home')


@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash('ユーザー名かパスワードが有効ではありません')
            return redirect(url_for('main.login'))
        
        login_user(user, remember=form.remember_me.data)
        flash(f'{user.username}様 ログインが完了しました')
        return redirect(url_for('main.index'))
    return render_template('login.html', title ='Sign In', form =form)

@main.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("ユーザー登録が完了しました")
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)


@main.route('/products')
@login_required
def products():
    return render_template('products.html', title='Products')

@main.route('/route/add', methods=['GET', 'POST'])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        new_product = Product(
            item_number=form.item_number.data,
            name=form.name.data,
            stock_quantity=form.stock_quantity.data
        )
        db.session.add(new_product)
        db.session.commit()
        flash('プロダクトが登録されました')
        return redirect(url_for('main.products'))
    return render_template('add_product.html', title='プロダクト追加',form=form)


@main.route('/edit_product/<int:product_id>', methods=['GET','POST'])
@login_required
def edti_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    if form.validate_on_submit():
        product.item_number = form.item_number.data
        product.name = form.name.data
        product.stock_quantity = form.stock_quantity.data
        db.session.commit()
        flash('プロダクが更新されました')
        return redirect(url_for('main.products'))
    elif request.method == 'GET':
        form.item_number.data = product.item_number
        form.name.data = product.name
        form.stock_quantity.data = product.stock_quantity
    return render_template('edit_product.html', title='プロダクト編集', form=form)


@main.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('プロダクトが削除されました')
    return redirect(url_for('main.products'))

@main.route('/bill')
@login_required
def bill():
    return render_template('bill.html', title='Bill')

@main.route('/')
@login_required
def sails():
    return render_template('sails_index.html', title='Sails')

@main.route('/')
@login_required
def user_profile():
    return render_template('user_profile.html', title='Sails')