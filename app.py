import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory, Response
from flask_pymongo import PyMongo
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from bson.objectid import ObjectId
import cloudinary
import cloudinary.uploader
import urllib.parse
from datetime import datetime
from flask_mail import Mail, Message

# Memuat variabel dari file .env
load_dotenv()

# Inisialisasi aplikasi Flask
app = Flask(__name__)

# Memuat konfigurasi dari file config.py
app.config.from_pyfile('config.py')

# Inisialisasi Flask-PyMongo, Bcrypt, dan Flask-Login
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# Inisialisasi Flask-Mail
mail = Mail(app)

# Konfigurasi Cloudinary
cloudinary.config(
    cloud_name=app.config['CLOUDINARY_CLOUD_NAME'],
    api_key=app.config['CLOUDINARY_API_KEY'],
    api_secret=app.config['CLOUDINARY_API_SECRET']
)

# Model pengguna untuk Flask-Login
class AdminUser(UserMixin):
    def __init__(self, user_data):
        self.username = user_data['username']
        self.id = str(user_data['_id'])
        self.password = user_data['password']

@login_manager.user_loader
def load_user(user_id):
    user_data = mongo.db.admin_users.find_one({'_id': ObjectId(user_id)})
    if user_data:
        return AdminUser(user_data)
    return None

# Fungsi filter Jinja2 untuk format rupiah (hanya untuk template)
@app.template_filter('format_rupiah')
def format_rupiah_filter(value):
    return "{:,.0f}".format(value).replace(",", ".")

# Fungsi Python untuk format rupiah (dapat dipanggil dari kode Python)
def format_rupiah_py(value):
    return "{:,.0f}".format(value).replace(",", ".")

# --- Rute-rute aplikasi utama ---

@app.route('/')
def index():
    products = list(mongo.db.products.find().limit(4))
    return render_template('index.html', products=products)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/products')
def products():
    query = {}
    search_query = request.args.get('q', '')
    if search_query:
        query = {'name': {'$regex': search_query, '$options': 'i'}}
    product_list = list(mongo.db.products.find(query))
    return render_template('products/product_list.html', products=product_list, search_query=search_query)

@app.route('/product/<product_id>')
def product_detail(product_id):
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if product:
        return render_template('products/product_detail.html', product=product)
    flash('Produk tidak ditemukan.', 'danger')
    return redirect(url_for('products'))

@app.route('/add_to_cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        flash('Produk tidak ditemukan.', 'danger')
        return redirect(url_for('products'))

    cart = session.get('cart', [])
    item_exist = False
    for item in cart:
        if item['id'] == product_id:
            item['quantity'] += 1
            item_exist = True
            break
    if not item_exist:
        cart.append({
            'id': product_id,
            'name': product['name'],
            'price': product['price'],
            'image_url': product['image_url'],
            'quantity': 1
        })

    session['cart'] = cart
    flash(f'{product["name"]} telah ditambahkan ke keranjang!', 'success')
    return redirect(url_for('products'))

@app.route('/add_review/<product_id>', methods=['POST'])
def add_review(product_id):
    product = mongo.db.products.find_one({'_id': ObjectId(product_id)})
    if not product:
        flash('Produk tidak ditemukan.', 'danger')
        return redirect(url_for('product_detail', product_id=product_id))

    author = request.form.get('author')
    rating = int(request.form.get('rating', 5))
    comment = request.form.get('comment')
    date_posted = datetime.utcnow()

    # Siapkan data ulasan
    review_data = {
        'author': author,
        'rating': rating,
        'comment': comment,
        'date_posted': date_posted
    }

    # Tambahkan ulasan ke produk yang sesuai
    mongo.db.products.update_one(
        {'_id': ObjectId(product_id)},
        {'$push': {'reviews': review_data}}
    )
    
    flash('Ulasan Anda berhasil ditambahkan!', 'success')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    cart_total = sum(int(item['price']) * int(item['quantity']) for item in cart_items)
    return render_template('cart/cart.html', cart_items=cart_items, cart_total=cart_total)

@app.route('/update_cart/<product_id>', methods=['POST'])
def update_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', [])
    for item in cart:
        if item['id'] == product_id:
            if quantity > 0:
                item['quantity'] = quantity
            else:
                cart.remove(item)
            break
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<product_id>', methods=['POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', [])
    cart = [item for item in cart if item['id'] != product_id]
    session['cart'] = cart
    flash('Produk telah dihapus dari keranjang.', 'info')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['POST'])
def checkout():
    cart = session.get('cart', [])
    if not cart:
        flash('Keranjang Anda kosong.', 'danger')
        return redirect(url_for('cart'))

    # Buat pesan WhatsApp
    message = "Halo, saya ingin memesan produk berikut:\n\n"
    total_price = 0
    for item in cart:
        subtotal = item['price'] * item['quantity']
        # Gunakan fungsi Python yang baru
        message += f"- {item['name']} ({item['quantity']}x) - Rp{format_rupiah_py(subtotal)}\n"
        total_price += subtotal
    # Gunakan fungsi Python untuk total harga
    message += f"\nTotal: Rp{format_rupiah_py(total_price)}"

    # Encode URL untuk WhatsApp
    whatsapp_number = app.config['WHATSAPP_NUMBER']
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"

    # Kosongkan keranjang setelah checkout
    session.pop('cart', None)
    flash('Pesanan Anda sedang diproses. Anda akan diarahkan ke WhatsApp untuk konfirmasi.', 'success')
    return redirect(whatsapp_url)

@app.route('/blog')
def blog():
    posts = list(mongo.db.blog_posts.find().sort('date_posted', -1))
    return render_template('blog/blog_list.html', posts=posts)

@app.route('/blog/<post_id>')
def blog_post(post_id):
    post = mongo.db.blog_posts.find_one({'_id': ObjectId(post_id)})
    if not post:
        flash('Artikel tidak ditemukan.', 'danger')
        return redirect(url_for('blog'))
    return render_template('blog/blog_post.html', post=post)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message_body = request.form.get('message')

        # Membuat objek pesan email
        msg = Message(subject=subject,
                      sender=app.config['MAIL_USERNAME'],
                      recipients=[app.config['MAIL_USERNAME']]) # Kirim ke email Anda sendiri
        
        # Isi pesan email
        msg.body = f"Anda menerima pesan dari formulir kontak di website.\n\n" \
                   f"Nama: {name}\n" \
                   f"Email: {email}\n" \
                   f"Pesan:\n{message_body}"

        try:
            mail.send(msg)
            flash('Pesan Anda berhasil terkirim!', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash(f'Terjadi kesalahan saat mengirim pesan: {e}', 'danger')
            return redirect(url_for('contact'))

    return render_template('contact.html')

# --- Rute-rute Admin ---

@app.route('/admin')
@login_required
def admin_dashboard():
    products_count = mongo.db.products.count_documents({})
    posts_count = mongo.db.blog_posts.count_documents({})
    return render_template('admin/dashboard.html', products_count=products_count, posts_count=posts_count)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_data = mongo.db.admin_users.find_one({'username': username})
        if user_data and bcrypt.check_password_hash(user_data['password'], password):
            user_obj = AdminUser(user_data)
            login_user(user_obj)
            return redirect(url_for('admin_dashboard'))
        flash('Username atau password salah.', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

# Rute CRUD Produk Admin
@app.route('/admin/products', methods=['GET', 'POST'])
@login_required
def admin_products():
    if request.method == 'POST':
        name = request.form.get('name')
        price = int(request.form.get('price'))
        description = request.form.get('description')
        image = request.files.get('image')

        image_url = None
        if image:
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result['url']

        mongo.db.products.insert_one({
            'name': name,
            'price': price,
            'description': description,
            'image_url': image_url
        })
        flash('Produk berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_products'))

    products_list = list(mongo.db.products.find())
    return render_template('admin/manage_products.html', products=products_list)

@app.route('/admin/products/delete/<product_id>', methods=['POST'])
@login_required
def admin_delete_product(product_id):
    mongo.db.products.delete_one({'_id': ObjectId(product_id)})
    flash('Produk berhasil dihapus.', 'success')
    return redirect(url_for('admin_products'))

# Rute CRUD Blog Admin
@app.route('/admin/blog', methods=['GET', 'POST'])
@login_required
def admin_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        image = request.files.get('image')

        image_url = None
        if image:
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result['url']

        mongo.db.blog_posts.insert_one({
            'title': title,
            'content': content,
            'image_url': image_url,
            'author': current_user.username,
            'date_posted': datetime.utcnow()
        })
        flash('Artikel blog berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_blog'))

    posts_list = list(mongo.db.blog_posts.find().sort('date_posted', -1))
    return render_template('admin/manage_blog.html', posts=posts_list)

@app.route('/admin/blog/delete/<post_id>', methods=['POST'])
@login_required
def admin_delete_blog_post(post_id):
    mongo.db.blog_posts.delete_one({'_id': ObjectId(post_id)})
    flash('Artikel blog berhasil dihapus.', 'success')
    return redirect(url_for('admin_blog'))

@app.route('/sitemap.xml')
def sitemap():
    # Ambil semua data produk dan blog dari database
    products = mongo.db.products.find()
    posts = mongo.db.blog_posts.find()

    # Buat header XML sitemap
    sitemap_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Tambahkan URL untuk halaman statis
    base_url = 'http://localost:5000' # Ganti dengan domain Anda yang sebenarnya
    today_date = datetime.utcnow().strftime('%Y-%m-%d')
    
    # Halaman utama
    sitemap_content += f'<url><loc>{base_url}/</loc><lastmod>{today_date}</lastmod><changefreq>weekly</changefreq><priority>1.0</priority></url>\n'
    # Halaman About
    sitemap_content += f'<url><loc>{base_url}/about</loc><lastmod>{today_date}</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>\n'
    # Halaman Produk
    sitemap_content += f'<url><loc>{base_url}/products</loc><lastmod>{today_date}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n'
    # Halaman Blog
    sitemap_content += f'<url><loc>{base_url}/blog</loc><lastmod>{today_date}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>\n'
    # Halaman Kontak
    sitemap_content += f'<url><loc>{base_url}/contact</loc><lastmod>{today_date}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n'

    # Tambahkan URL untuk setiap produk (dinamis)
    for product in products:
        product_url = f'{base_url}/product/{product["_id"]}'
        sitemap_content += f'<url><loc>{product_url}</loc><lastmod>{today_date}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'

    # Tambahkan URL untuk setiap postingan blog (dinamis)
    for post in posts:
        post_url = f'{base_url}/blog/{post["_id"]}'
        post_date = post['date_posted'].strftime('%Y-%m-%d')
        sitemap_content += f'<url><loc>{post_url}</loc><lastmod>{post_date}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n'

    # Tutup tag XML
    sitemap_content += '</urlset>'

    return Response(sitemap_content, mimetype='application/xml')

# Rute untuk menyajikan robots.txt
@app.route('/robots.txt')
def robots():
    return send_from_directory(app.root_path, 'robots.txt', mimetype='text/plain')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(app.root_path, 'favicon.ico', mimetype='image/vnd.microsoft.icon')

# --- Main execution ---
if __name__ == '__main__':

    # Memastikan user admin ada, jika belum ada akan dibuatkan
    # if not mongo.db.admin_users.find_one({'username': 'admin'}):
    #     hashed_password = bcrypt.generate_password_hash('admin123').decode('utf-8')
    #     mongo.db.admin_users.insert_one({'username': 'admin', 'password': hashed_password})
    #     print("Admin user created with username 'admin' and password 'admin123'")
    
    app.run(debug=True)