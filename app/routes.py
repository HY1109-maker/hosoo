from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, abort
from werkzeug.utils import secure_filename
from flask_login import login_user, logout_user, login_required, current_user
from .models import User, Product, Store, Inventory, InventoryLog, ProductLog
from . import db
from .forms import RegistrationForm, LoginForm, ProductForm, EditInventoryForm, AllocateInventoryForm, InventoryEntryForm, CsvUploadForm, AdminEditProfileForm, StoreForm, EditProductForm, AddProductForm
import pandas as pd
import os
import chardet
from .decorators import admin_required

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
@login_required
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
    # 店舗で絞り込むためのクエリパラメータを取得
    store_id_filter = request.args.get('store_id', type=int)

    # 全ての店舗と商品を取得
    stores = Store.query.order_by('name').all()
    products = Product.query.order_by('name').all()

    # 表示用のデータを格納する辞書を準備
    product_inventory_data = {}

    for p in products:
        # ▼▼▼ 在庫数を格納する辞書を改良 ▼▼▼
        # { '店舗名': (数量, 在庫ID), ... } という形式で保存
        inventory_by_store = {s.name: None for s in stores}
        last_updated = None
        is_alert_row = False
        
        for inv in p.inventories:
            inventory_by_store[inv.store.name] = {
                'quantity': inv.quantity,
                'id': inv.id,
                'threshold': inv.threshold
            } # 数量とIDをタプルで保存
            last_updated = inv.last_updated
            if inv.quantity <= inv.threshold:
                is_alert_row = True

        product_inventory_data[p.id] = {
            'product': p,
            'inventories': inventory_by_store,
            'last_updated': last_updated,
            'is_alert_row': is_alert_row
        }
    
    # 絞り込みが指定されている場合は、その店舗の在庫がある商品だけにフィルタリング
    if store_id_filter:
        filtered_store = Store.query.get(store_id_filter)
        if filtered_store:
            product_inventory_data = {
                pid: data for pid, data in product_inventory_data.items()
                if data['inventories'].get(filtered_store.name) is not None
            }
    


    return render_template('products.html', 
                           stores=stores, 
                           product_data=product_inventory_data,
                           selected_store_id=store_id_filter)


@main.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    form=ProductForm()
    if form.validate_on_submit():
        product = Product(
            item_number = form.item_number.data,
            name = form.name.data
        )
        db.session.add(product)
        db.session.commit()

        flash(f'新しいプロダクト[{product.name}]がマスタに登録されました。続けて初期在庫を割り当てます。', 'info')

        return redirect(url_for('main.allocate_inventory', product_id=product.id))
    return render_template('add_product.html', title='商品マスタ登録', form=form)

@main.route('/allocate_inventory/<int:product_id>', methods=['POST', 'GET'])
@login_required
def allocate_inventory(product_id):
    product = Product.query.get_or_404(product_id)
    form = AllocateInventoryForm()

    if request.method == 'POST' and form.validate_on_submit():
        for entry in form.inventories.data:
            store_id = int(entry['store_id'])
            quantity = int(entry['quantity'])

            inventory = Inventory.query.filter_by(product_id=product.id, store_id=store_id).first()
            if inventory:
                inventory.quantity = quantity
            else:
                inventory = Inventory(
                    product_id = product.id,
                    store_id=store_id,
                    quantity=quantity
                )
                db.session.add(inventory)

        db.session.commit()
        flash(f'[{product.name}]の在庫情報を保存しました。')
        return redirect(url_for('main.products'))
    
    all_stores = Store.query.order_by('name').all()
    for store in all_stores:
        form.inventories.append_entry({
            'store_id': store.id,
            'store_name': store.name
        })
    
    return render_template('allocate_inventory.html', title='在庫割り当て', form=form, product=product)

@main.route('/edit_product/<int:product_id>', methods=['GET','POST'])
@login_required
def edit_product(product_id):
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

@main.route('/edit_inventory/<int:inventory_id>', methods=['GET', 'POST'])
@login_required
def edit_inventory(inventory_id):
    """特定の在庫情報を編集する"""
    # 編集対象の在庫情報をIDで取得。見つからなければ404エラー
    inventory = Inventory.query.get_or_404(inventory_id)
    form = EditInventoryForm()

    if form.validate_on_submit():
        # --- 1. ログを記録 ---
        # 変更前の在庫数を記録
        quantity_before = inventory.quantity
        threshold_before = inventory.threshold
        
        log_entry = InventoryLog(
            inventory=inventory,
            user=current_user,
            quantity_before=quantity_before,
            quantity_after=form.quantity.data,
            threshold_before=threshold_before,
            threshold_after=form.threshold.data
        )
        db.session.add(log_entry)

        # --- 2. quantity and threshold will be updated---
        inventory.quantity = form.quantity.data
        inventory.threshold = form.threshold.data
        
        # --- 3. Log and inventory are commited ---
        db.session.commit()

        if inventory.quantity != quantity_before and inventory.threshold != threshold_before:
            flash(f'「{inventory.product.name}」の在庫と閾値が更新されました。')
        elif inventory.quantity != quantity_before and inventory.threshold == threshold_before:
            flash(f'「{inventory.product.name}」の在庫が更新されました。')
        elif inventory.quantity == quantity_before and inventory.threshold != threshold_before:
            flash(f'「{inventory.product.name}」の閾値が更新されました。')

        
        flash(f'「{inventory.product.name}」の在庫が更新されました。')
        return redirect(url_for('main.products'))

    # ページが最初に表示された(GETリクエストの)場合、フォームに現在の在庫数を表示
    elif request.method == 'GET':
        form.quantity.data = inventory.quantity

    return render_template('edit_inventory.html', title='在庫編集', form=form, inventory=inventory)

@main.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('プロダクトが削除されました')
    return redirect(url_for('main.products'))


@main.route('/api/update_inventory', methods=['POST'])
@login_required
def update_inventory():
    data = request.get_json()
    inventory_id = data.get('inventory_id')
    new_quantity = int(data.get('quantity', 0)) # 数値に変換
    new_threshold = int(data.get('threshold', 10)) # 数値に変換

    if current_user.role not in ['admin', 'manager']:
        return jsonify({'status': 'error', 'message': 'この操作を行う権限がありません'}), 403 # 403: Forbidden

    data = request.get_json()

    # --- A: 新規作成の場合 ---
    if inventory_id == 'new':
        product_id = data.get('product_id')
        store_id = data.get('store_id')

        if current_user.role == 'manager' and current_user.store_id != store_id:
            return jsonify({'status': 'error', 'message': '所属ストア以外の在庫は作成できません'})
        if not all([product_id, store_id]):
            return jsonify({'status': 'error', 'message': '商品または店舗IDがありません'}), 400

        # 新しい在庫レコードを作成
        inventory = Inventory(
            product_id=product_id,
            store_id=store_id,
            quantity=new_quantity,
            threshold=new_threshold
        )
        db.session.add(inventory)
        db.session.commit() # コミットしてinventory.idを確定させる
        
        # ログは新規作成なので「0から」として記録
        log_entry = InventoryLog(inventory=inventory, user=current_user, quantity_before=0, quantity_after=new_quantity, threshold_before=0, threshold_after=new_threshold)
        db.session.add(log_entry)

    # --- B: 既存の在庫を更新する場合 ---
    else:
        inventory = Inventory.query.get(int(inventory_id))
        if current_user.role == 'manager' and current_user.store_id != inventory.store_id:
            return jsonify({'status': 'error', 'message': '所属ストア以外の在庫は編集できません'}), 403
        if not inventory:
            return jsonify({'status': 'error', 'message': '在庫が見つかりません'}), 404
        if inventory.quantity == new_quantity and inventory.threshold == new_threshold:
            return jsonify({'status': 'error', 'message': '変更がありませんでした'}), 403
        
        # ログ記録
        quantity_before = inventory.quantity
        threshold_before = inventory.threshold
        log_entry = InventoryLog(inventory=inventory, user=current_user, quantity_before=quantity_before, quantity_after=new_quantity, threshold_before=threshold_before, threshold_after=new_threshold)
        db.session.add(log_entry)
        
        # 在庫更新
        inventory.quantity = new_quantity
        inventory.threshold = new_threshold

    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': '在庫が更新されました',
        'inventory_id': inventory.id, # ★新しいIDを返す
        'new_quantity': inventory.quantity,
        'new_threshold': inventory.threshold
    })

@main.route('/admin/import_data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_data():
    form = CsvUploadForm()
    if form.validate_on_submit():
        f = form.csv_file.data
        filename = secure_filename(f.filename)
        filepath = os.path.join(current_app.instance_path, 'uploads', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        f.save(filepath)

        try:
            # --- ▼▼▼ ここからが新しいロジック ▼▼▼ ---
            if filename.endswith(('.xlsx', '.xlsm')): # .xlsxにも対応
                df = pd.read_excel(filepath)
            else:
                # 2. chardetで文字コードを自動検出
                with open(filepath, 'rb') as rawdata:
                    result = chardet.detect(rawdata.read())
                
                detected_encoding = result['encoding']
                print(f"Detected encoding: {detected_encoding}") # ターミナルで確認用

                # 3. 検出したエンコーディングでファイルを読み込む
                df = pd.read_csv(filepath, encoding=detected_encoding, on_bad_lines='warn')
            # --- ▲▲▲ 新しいロジックここまで ▲▲▲ ---

            # --- ▼▼▼ データベース処理のロジック (変更なし) ▼▼▼ ---
            updated_count = 0
            created_count = 0

            for index, row in df.iterrows():
                if not all(k in row for k in ['品番', '店舗名', '在庫数']):
                    flash('CSVのヘッダーに「品番」「店舗名」「在庫数」が含まれている必要があります', 'danger')
                    return redirect(url_for('main.import_data'))
                
                store = Store.query.filter_by(name=row['店舗名']).first()
                if not store:
                    store = Store(name=row['店舗名'])
                    db.session.add(store)

                product = Product.query.filter_by(item_number=row['品番']).first()
                if not product:
                    if '商品名' not in row:
                        flash(f"新しい品番 {row['品番']}には「商品名」が必要です", 'danger')
                        continue
                    product = Product(item_number=row['品番'], name=row['商品名'])
                    db.session.add(product)

                inventory = Inventory.query.filter_by(product=product, store=store).first()
                if inventory:
                    inventory.quantity = int(row['在庫数'])
                    updated_count += 1
                else:
                    inventory = Inventory(product=product, store=store, quantity=int(row['在庫数']))
                    db.session.add(inventory)
                    created_count += 1
            
            db.session.commit()
            flash(f'インポート完了！ {created_count}件の新規在庫を登録し、{updated_count}件の在庫を更新しました。', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'インポート中にエラーが発生しました : {e}', 'danger')
        
        return redirect(url_for('main.products'))
    
    return render_template('import_data.html', title='データインポート', form=form)

@main.route('/user/<username>')
@login_required
def user_profile(username):
    user = User.query.filter_by(username=username).first()
    return render_template('user_profile.html', user=user)


@main.route('/admin/users')
@login_required
@admin_required
def manage_users():
    users = User.query.order_by(User.username).all()
    return render_template('manage_users.html', users=users)

@main.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminEditProfileForm(user=user)

    if form.validate_on_submit():
        user.email = form.email.data
        user.role = form.role.data
        user.store_id = form.store.data if form.store.data != 0 else None
        db.session.commit()
        flash('ユーザー情報が更新されました')
        return redirect(url_for('main.manage_users'))
    
    elif request.method == 'GET':
        form.email.data = user.email
        form.role.data = user.role
        form.store.data = user.store_id if user.store_id else 0
        # usernameはreadonlyなので、表示用に設定は不要
        form.username.data = user.username

    return render_template('edit_user.html', form=form, user=user)

@main.route('/admin/stores', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_stores():
    form = StoreForm()

    if form.validate_on_submit():
        store = Store(name = form.name.data, address = form.address.data)
        db.session.add(store)
        db.session.commit()
        flash('新しいストアが登録されました')
        return redirect(url_for('main.manage_stores'))
    
    stores = Store.query.order_by('name').all()
    return render_template('manage_stores.html', stores=stores, form=form)

@main.route('/delete_inventory/<int:inventory_id>', methods=['POST'])
@login_required
def delete_inventory(inventory_id):
    if current_user.role not in ['admin', 'manager']:
        flash('この操作を行う権限がありません', 'danger')
        return redirect(url_for('main.products'))
    
    inventory = Inventory.query.get_or_404(inventory_id)
    
    if current_user.role == 'manager' and current_user.store_id != inventory.store_id:
        flash('所属ストア以外の在庫の削除はできません', 'danger')
        return redirect(url_for('main.products'))
    
    product_name = inventory.product.name
    store_name = inventory.store.name
    
    db.session.delete(inventory)
    db.session.commit()
    flash(f'{product_name}の在庫情報 {store_name}が削除されました')
    return redirect(url_for('main.products'))

@main.route('/logs')
@login_required
def view_logs():
    # 権限チェック（管理者または店長のみ）
    if current_user.role not in ['admin', 'manager']:
        abort(403)

    page = request.args.get('page', 1, type=int)
    
    # 店長の場合は、自分の店舗のログのみ表示
    if current_user.role == 'manager':
        # manager's store_id must exist
        if not current_user.store_id:
             return render_template('logs.html', pagination=None)
        
        # Get inventories for the manager's store
        store_inventories = Inventory.query.filter_by(store_id=current_user.store_id).all()
        inventory_ids = [inv.id for inv in store_inventories]
        
        pagination = InventoryLog.query.filter(InventoryLog.inventory_id.in_(inventory_ids)).order_by(InventoryLog.timestamp.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
    else: # 管理者の場合
        pagination = InventoryLog.query.order_by(InventoryLog.timestamp.desc()).paginate(
            page=page, per_page=20, error_out=False
        )
        
    logs = pagination.items
    return render_template('logs.html', logs=logs, pagination=pagination)


@main.route('/products_master')
@login_required
def products_master():
    """商品マスタ一覧ページ"""
    # 閲覧は全てのログインユーザーに許可
    products = Product.query.order_by(Product.name).all() # 商品名を基準にソート
    return render_template('products_master.html', products=products)


@main.route('/edit_product_master/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product_master(product_id):
    """商品マスタ編集ページ（マネージャー以上が編集可能）"""
    # 権限チェック (管理者または店長のみ編集可能)
    if current_user.role not in ['admin', 'manager']:
        flash('商品マスタを編集する権限がありません。', 'danger')
        abort(403) # 403 Forbiddenを返すか、products_masterにリダイレクト

    product = Product.query.get_or_404(product_id)
    form = EditProductForm(original_item_number=product.item_number) # 元の品番を渡してフォームを初期化

    if form.validate_on_submit():
        # 変更前の値をログ記録用に保持
        before_values = {
            'item_number': product.item_number,
            'name': product.name,
            'price': product.price,
            'cost': product.cost
        }
        
        # データベースを更新
        product.item_number = form.item_number.data
        product.name = form.name.data
        product.price = form.price.data if form.price.data is not None else None # 空欄の場合はNoneを保存
        product.cost = form.cost.data if form.cost.data is not None else None   # 空欄の場合はNoneを保存
        
        # 変更があった項目をProductLogに記録
        if before_values['item_number'] != product.item_number:
            log = ProductLog(product=product, user=current_user, field_changed='品番', 
                             value_before=str(before_values['item_number']), value_after=str(product.item_number))
            db.session.add(log)
        if before_values['name'] != product.name:
            log = ProductLog(product=product, user=current_user, field_changed='商品名', 
                             value_before=str(before_values['name']), value_after=str(product.name))
            db.session.add(log)
        if before_values['price'] != product.price:
            log = ProductLog(product=product, user=current_user, field_changed='販売価格', 
                             value_before=str(before_values['price']), value_after=str(product.price))
            db.session.add(log)
        if before_values['cost'] != product.cost:
            log = ProductLog(product=product, user=current_user, field_changed='原価', 
                             value_before=str(before_values['cost']), value_after=str(product.cost))
            db.session.add(log)

        db.session.commit()
        flash('商品マスタ情報が更新されました。', 'success') # flashメッセージに'success'カテゴリを付けて色分け
        return redirect(url_for('main.products_master'))

    elif request.method == 'GET':
        # GETリクエストの場合、フォームに現在の値を設定
        form.item_number.data = product.item_number
        form.name.data = product.name
        form.price.data = product.price
        form.cost.data = product.cost
        
    return render_template('edit_product_master.html', form=form, product=product)

@main.route('/admin/import_products_master', methods=['GET', 'POST'])
@login_required
@admin_required # 管理者のみがアクセス可能
def import_products_master():
    form = CsvUploadForm() # 既存のファイルアップロードフォームを使用

    if form.validate_on_submit():
        f = form.csv_file.data
        filename = secure_filename(f.filename)
        filepath = os.path.join(current_app.instance_path, 'uploads', filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        f.save(filepath)

        try:
            # ExcelまたはCSVファイルをPandasで読み込み
            if filename.endswith(('.xlsx', '.xlsm')):
                df = pd.read_excel(filepath)
            else:
                with open(filepath, 'rb') as rawdata:
                    result = chardet.detect(rawdata.read()) # 文字コード自動検出
                df = pd.read_csv(filepath, encoding=result['encoding'], on_bad_lines='warn')

            updated_count = 0
            created_count = 0

            # 必須列のチェック
            required_columns = ['品番', '商品名']
            if not all(col in df.columns for col in required_columns):
                flash(f'CSV/Excelファイルには「{", ".join(required_columns)}」の列が必要です。', 'danger')
                return redirect(url_for('main.import_products_master'))

            # 各行の商品データを処理
            for index, row in df.iterrows():
                item_number = str(row['品番']).strip() # 品番は文字列として扱い、前後空白を除去

                # 品番で既存商品を検索
                product = Product.query.filter_by(item_number=item_number).first()

                if product:
                    # 商品が存在すれば更新
                    product.name = str(row['商品名']).strip()
                    product.price = int(row['販売価格']) if '販売価格' in row and pd.notna(row['販売価格']) else None
                    product.cost = int(row['原価']) if '原価' in row and pd.notna(row['原価']) else None
                    updated_count += 1
                else:
                    # 商品が存在しなければ新規作成
                    product = Product(
                        item_number=item_number,
                        name=str(row['商品名']).strip(),
                        price=int(row['販売価格']) if '販売価格' in row and pd.notna(row['販売価格']) else None,
                        cost=int(row['原価']) if '原価' in row and pd.notna(row['原価']) else None
                    )
                    db.session.add(product)
                    created_count += 1

            db.session.commit()
            flash(f'商品マスタのインポートが完了しました。{created_count}件を新規登録し、{updated_count}件を更新しました。', 'success')
            return redirect(url_for('main.products_master'))

        except Exception as e:
            db.session.rollback() # エラー時はロールバック
            flash(f'インポート中にエラーが発生しました: {e}', 'danger')
        finally:
            # アップロードされたファイルを削除
            if os.path.exists(filepath):
                os.remove(filepath)
        
    return render_template('import_products_master.html', title='商品マスタインポート', form=form)

@main.route('/add_product_master', methods=['GET', 'POST'])
@login_required
def add_product_master():
    # 権限チェック (マネージャー以上)
    if current_user.role not in ['admin', 'manager']:
        abort(403)
        
    form = AddProductForm()
    
    if form.validate_on_submit():
        product = Product(
            item_number=form.item_number.data,
            name=form.name.data,
            price=form.price.data,
            cost=form.cost.data
        )
        db.session.add(product)
        db.session.commit()
        flash('新しい商品が商品マスタに追加されました。')
        return redirect(url_for('main.products_master'))

    return render_template('add_product_master.html', form=form)






