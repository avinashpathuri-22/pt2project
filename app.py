import os
from functools import wraps
from flask import Flask, render_template, redirect, url_for, session, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Product, User, Order, OrderItem, CartItem

app = Flask(__name__)
app.config['SECRET_KEY'] = 'aviproject_secret_key_123!'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'store.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def validate_session():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if not user:
            session.pop('user_id', None)

import urllib.parse
import os

BUCKET_NAME = "aviproject-images"
USE_S3 = os.environ.get('USE_S3', 'False').lower() in ['true', '1', 't']

@app.context_processor
def inject_globals():
    cart_count = 0
    current_user = None
    
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
        if current_user:
            cart_count = sum(item.quantity for item in current_user.cart_items)
    else:
        cart = session.get('cart', {})
        cart_count = sum(cart.values())
        
    def get_image_url(image_path):
        if USE_S3:
            filename = image_path.split('/')[-1]
            filename_encoded = urllib.parse.quote(filename)
            return f"https://{BUCKET_NAME}.s3.amazonaws.com/{filename_encoded}"
        return image_path
        
    return dict(cart_count=cart_count, current_user=current_user, get_image_url=get_image_url)

@app.route('/')
def index():
    query = request.args.get('q', '')
    max_price = request.args.get('max_price', type=float)
    
    products_query = Product.query
    
    if query:
        products_query = products_query.filter(Product.name.ilike(f'%{query}%'))
    if max_price:
        products_query = products_query.filter(Product.price <= max_price)
        
    products = products_query.all()
    return render_template('index.html', products=products, search_query=query, max_price=max_price)

@app.route('/product/<int:product_id>')
def product(product_id):
    product = Product.query.get_or_404(product_id)
    return render_template('product.html', product=product)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('login'))
            
        hashed_pw = generate_password_hash(password)
        new_user = User(full_name=full_name, email=email, password_hash=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            
            # Merge session cart to db cart
            session_cart = session.get('cart', {})
            if session_cart:
                for str_pid, qty in session_cart.items():
                    pid = int(str_pid)
                    cart_item = CartItem.query.filter_by(user_id=user.id, product_id=pid).first()
                    if cart_item:
                        cart_item.quantity += qty
                    else:
                        new_cart_item = CartItem(user_id=user.id, product_id=pid, quantity=qty)
                        db.session.add(new_cart_item)
                db.session.commit()
                session.pop('cart', None)
                flash('Your cart was successfully restored!', 'success')
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)

@app.route('/cart')
def cart():
    products_in_cart = []
    total = 0.0
    
    if 'user_id' in session:
        user_id = session['user_id']
        cart_items = CartItem.query.filter_by(user_id=user_id).all()
        for item in cart_items:
            subtotal = item.product.price * item.quantity
            total += subtotal
            products_in_cart.append({
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal
            })
    else:
        session_cart = session.get('cart', {})
        for str_pid, qty in session_cart.items():
            product = Product.query.get(int(str_pid))
            if product:
                subtotal = product.price * qty
                total += subtotal
                products_in_cart.append({
                    'product': product,
                    'quantity': qty,
                    'subtotal': subtotal
                })
                
    return render_template('cart.html', items=products_in_cart, total=total)

@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    qty_change = int(request.form.get('quantity', 1))
    
    if 'user_id' in session:
        user_id = session['user_id']
        cart_item = CartItem.query.filter_by(user_id=user_id, product_id=product_id).first()
        if cart_item:
            cart_item.quantity += qty_change
            if cart_item.quantity <= 0:
                db.session.delete(cart_item)
        elif qty_change > 0:
            cart_item = CartItem(user_id=user_id, product_id=product_id, quantity=qty_change)
            db.session.add(cart_item)
        db.session.commit()
    else:
        cart = session.get('cart', {})
        str_pid = str(product_id)
        current_qty = cart.get(str_pid, 0)
        new_qty = current_qty + qty_change
        
        if new_qty <= 0:
            cart.pop(str_pid, None)
        else:
            cart[str_pid] = new_qty
            
        session['cart'] = cart
        session.modified = True
        
    flash(f'{product.name} cart updated.', 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/remove-from-cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'user_id' in session:
        CartItem.query.filter_by(user_id=session['user_id'], product_id=product_id).delete()
        db.session.commit()
    else:
        cart = session.get('cart', {})
        str_pid = str(product_id)
        if str_pid in cart:
            cart.pop(str_pid)
            session['cart'] = cart
            session.modified = True
            
    flash('Item removed from cart.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    total = 0.0
    products_in_cart = []
    
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        cart_items = CartItem.query.filter_by(user_id=user.id).all()
        for item in cart_items:
            products_in_cart.append({'product': item.product, 'quantity': item.quantity})
            total += item.product.price * item.quantity
    else:
        user = None
        session_cart = session.get('cart', {})
        for str_pid, qty in session_cart.items():
            product = Product.query.get(int(str_pid))
            if product:
                products_in_cart.append({'product': product, 'quantity': qty})
                total += product.price * qty

    if not products_in_cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Must be logged in to place actual order to track it
        if not user:
            flash('Please log in or register to place your order.', 'info')
            return redirect(url_for('login', next=url_for('checkout')))
            
        # Update user details if provided
        user.address = request.form.get('address')
        user.city = request.form.get('city')
        user.pincode = request.form.get('pincode')
        
        # Create Order
        new_order = Order(user_id=user.id, total_amount=total, status='Pending')
        db.session.add(new_order)
        db.session.commit() # To get order.id
        
        # Create Order Items and adjust stock
        for item in products_in_cart:
            product = item['product']
            qty = item['quantity']
            order_item = OrderItem(order_id=new_order.id, product_id=product.id, quantity=qty, price=product.price)
            db.session.add(order_item)
            
            # Reduce stock
            if product.stock >= qty:
                product.stock -= qty
            else:
                product.stock = 0
                
        # Clear Cart
        CartItem.query.filter_by(user_id=user.id).delete()
        db.session.commit()
        
        flash('Success! Your order has been placed.', 'success')
        return redirect(url_for('order_success', order_id=new_order.id))
        
    return render_template('checkout.html', total=total, current_user=user)

@app.route('/order-success/<int:order_id>')
@login_required
def order_success(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
    return render_template('checkout.html', success=True, order=order)

@app.route('/orders')
@login_required
def orders():
    user_orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=user_orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.filter_by(id=order_id, user_id=session['user_id']).first_or_404()
    return render_template('order_detail.html', order=order)

@app.route('/admin/update-order-status/<int:order_id>', methods=['GET', 'POST'])
def update_order_status(order_id):
    # Minimal check for "Admin" - to test this easily as per requirements. 
    # Let's say user ID 1 is Admin, or we just allow anyone into this utility route.
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        new_status = request.form.get('status')
        if new_status:
            order.status = new_status
            db.session.commit()
            flash(f'Order #{order.id} status updated to {new_status}.', 'success')
        return redirect(url_for('update_order_status', order_id=order.id))
    
    statuses = ['Pending', 'Confirmed', 'Packed', 'Shipped', 'Out for Delivery', 'Delivered']
    return render_template('admin_orders.html', order=order, statuses=statuses)

if __name__ == '__main__':
    app.run(debug=True)
