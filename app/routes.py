from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
from .forms import RegistrationForm, LoginForm

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