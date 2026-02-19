# 🥋 Taekwondo Garuda Club - E-Commerce & Blog

Aplikasi web E-Commerce perlengkapan Taekwondo dan Blog komunitas yang dibangun menggunakan **Flask**, **MongoDB**, dan **UIkit**. Proyek ini dilengkapi dengan fitur manajemen admin (CMS), integrasi Cloudinary untuk gambar, dan sistem checkout langsung ke WhatsApp.

## 🚀 Fitur Utama

* **Katalog Produk:** Tampilan produk yang responsif dengan fitur kategori dan pencarian.
* **Sistem Keranjang:** Manajemen belanja berbasis sesi.
* **Checkout WhatsApp:** Integrasi pesanan langsung ke chat WhatsApp penjual.
* **Blog/Berita:** CMS untuk mengelola artikel dan berita klub.
* **Admin Dashboard:** Panel khusus untuk mengelola produk, blog, dan ulasan.
* **Cloud Storage:** Upload gambar otomatis ke Cloudinary.
* **SEO Ready:** Dilengkapi dengan `sitemap.xml` dan `robots.txt` dinamis.

---

## 📁 Struktur File

```text
PROYEK-TAEKWONDO/
├── static/              # Aset statis (CSS, JS, Images)
│   ├── css/             # style.css, uikit.min.css
│   ├── js/              # uikit.min.js, uikit-icons.min.js
│   └── images/          # Placeholder & Logo
├── templates/           # File HTML (Jinja2)
│   ├── includes/        # Partial templates (header, footer)
│   ├── about.html
│   ├── base.html
│   ├── cart.html
│   ├── dashboard.html
│   └── ... (file html lainnya)
├── app.py               # Logika utama Flask (Routes & Backend)
├── config.py            # Konfigurasi Environment Variables
├── requirements.txt     # Daftar library Python
├── vercel.json          # Konfigurasi deployment Vercel
├── .env                 # File rahasia (Credentials) - JANGAN DIUPLOAD
└── robots.txt           # SEO Configuration
```

---

## 🛠️ Instalasi Lokal

### 1. Prasyarat

* Python 3.8 ke atas
* Akun MongoDB Atlas (Gratis)
* Akun Cloudinary (Gratis)

### 2. Kloning & Persiapan Environment

```bash
# Masuk ke folder proyek
cd PROYEK-TAEKWONDO

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install library
pip install -r requirements.txt
```

### 3. Konfigurasi `.env`

Buat file bernama `.env` di root direktori dan isi dengan kredensial Anda:

```env
SECRET_KEY=kode_rahasia_anda
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/db_name
WHATSAPP_NUMBER=628123456789
CLOUDINARY_CLOUD_NAME=isi_disini
CLOUDINARY_API_KEY=isi_disini
CLOUDINARY_API_SECRET=isi_disini
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=email_anda@gmail.com
MAIL_PASSWORD=app_password_gmail
```

### 4. Jalankan Aplikasi

```bash
python app.py
```

Buka `http://127.0.0.1:5000` di browser Anda.

---

## ☁️ Deployment (Vercel)

Proyek ini sudah dikonfigurasi untuk **Vercel**. Ikuti langkah berikut:

1. **Push ke GitHub:** Upload semua file Anda ke repository GitHub (Pastikan `.env` tidak ikut terupload).
2. **Koneksikan ke Vercel:**
* Login ke [Vercel](https://vercel.com).
* Pilih **Add New Project** > Impor repository GitHub Anda.


3. **Environment Variables:**
* Di Vercel, masuk ke bagian **Settings > Environment Variables**.
* Masukkan semua kunci dan nilai yang ada di file `.env` Anda tadi ke sini.


4. **Deploy:** Klik button **Deploy**. Vercel akan membaca `vercel.json` dan menginstal `requirements.txt` secara otomatis.

---

## 📝 Catatan Penting

* **Format Rupiah:** Di dalam template, gunakan filter `| format_rupiah` untuk menampilkan harga yang rapi.
* **Admin Pertama:** Untuk membuat akun admin pertama kali, aktifkan baris kode inisialisasi user di bagian bawah `app.py`, jalankan sekali, lalu matikan kembali untuk keamanan.
* **Sitemap:** Setelah deploy, ubah `base_url` di fungsi `sitemap` pada `app.py` menjadi domain asli Anda agar SEO berjalan maksimal.
