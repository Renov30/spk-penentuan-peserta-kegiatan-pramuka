from flask import Flask, Response, request, render_template, request as flask_request, redirect, url_for, flash, session, jsonify, current_app
from flask_session import Session
from flask_session.sessions import FileSystemSessionInterface
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app import create_app, db
from app.models import Users, Participants, Notification, Event, Kuota, Criteria, HasilSeleksi, Penilaian, HimpunanKriteria, tb_participant_kegiatan, PairwiseComparison, AHPResults
from flask_mail import Mail, Message
from twilio.rest import Client
from authlib.integrations.flask_client import OAuth
from markupsafe import escape
from datetime import datetime, timedelta, date
from flask_wtf import CSRFProtect
from flask_wtf.csrf import CSRFProtect, CSRFError
from forms import LoginForm, RegisterForm
from config import Config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import current_user, LoginManager, login_user, login_required
from functools import wraps
from app.utils.utils import log_activity
from sqlalchemy.exc import IntegrityError
import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
import random, string
import logging
import secrets
import time
import os
import re
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

app = create_app()
app.config['SESSION_FILE_PATH'] = os.path.join(app.root_path, 'flask_session')
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
secret_key = os.getenv("APP_SECRET_KEY")
# Ensure secret_key is a string, not bytes
if isinstance(secret_key, bytes):
    secret_key = secret_key.decode('utf-8')
app.secret_key = secret_key or secrets.token_hex(32)

# Custom Session Interface to fix bytes/string issue
class FixedFileSystemSessionInterface(FileSystemSessionInterface):
    def generate_sid(self):
        """Generate session ID and ensure it's always a string"""
        sid = super().generate_sid()
        if isinstance(sid, bytes):
            # Convert bytes to string if needed
            try:
                sid = sid.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                # If decode fails, use base64 or hex encoding
                import base64
                sid = base64.urlsafe_b64encode(sid).decode('utf-8').rstrip('=')
        return sid
    
    def save_session(self, app, session, response):
        """Override save_session to ensure session_id is always a string"""
        # Monkey-patch response.set_cookie to ensure value is always string
        original_set_cookie = response.set_cookie
        
        def patched_set_cookie(key, value='', *args, **kwargs):
            # Ensure value is always a string
            if isinstance(value, bytes):
                try:
                    value = value.decode('utf-8')
                except (UnicodeDecodeError, AttributeError):
                    import base64
                    value = base64.urlsafe_b64encode(value).decode('utf-8').rstrip('=')
            return original_set_cookie(key, value, *args, **kwargs)
        
        # Temporarily replace set_cookie
        response.set_cookie = patched_set_cookie
        
        try:
            # Call parent save_session
            super().save_session(app, session, response)
        finally:
            # Restore original set_cookie
            response.set_cookie = original_set_cookie

# Initialize Flask-Session first to set up configuration
Session(app)

# Replace with custom session interface that fixes bytes/string issue
# Simply change the class of existing interface to our custom class
existing_interface = app.session_interface

# Change the class of the existing interface instance to our custom class
# This preserves all attributes and methods while adding our overrides
existing_interface.__class__ = FixedFileSystemSessionInterface

csrf = CSRFProtect(app)
app.config.from_object(Config)
limiter = Limiter(get_remote_address, app=app)
logging.basicConfig(filename='login.log', level=logging.INFO,
                    format='%(asctime)s %(levelname)s:%(message)s')

# Inisialisasi Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)

login_manager.login_view = 'login'  # nama fungsi view untuk login
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Tentukan folder upload (path absolut dari root aplikasi)
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Extension yang diizinkan untuk file
ALLOWED_EXTENSIONS_IMAGE = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_EXTENSIONS_DOC = {'csv', 'xls', 'xlsx'}

def allowed_file(filename, file_type='image'):
    """Validasi extension file"""
    if file_type == 'image':
        allowed = ALLOWED_EXTENSIONS_IMAGE
    else:
        allowed = ALLOWED_EXTENSIONS_DOC
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed

# Configure Flask-Mail OTP
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
mail = Mail(app)

# Whatsapp OTP
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")
client = Client(account_sid, auth_token)

def send_whatsapp_code(phone, code):
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    client = Client(account_sid, auth_token)
    message_body = f"Kode verifikasi Anda adalah: *{code}*.\nJangan bagikan kode ini kepada siapa pun."
    try:
        message = client.messages.create(
            body=message_body,
            from_='whatsapp:+14155238886',
            to=f'whatsapp:{phone}'
        )
        print("Pesan berhasil dikirim:", message.sid)
    except Exception as e:
        print("Gagal mengirim pesan:", e)

def normalize_phone_number(phone):
    phone = phone.strip()
    if phone.startswith('0'):
        return '+62' + phone[1:]
    elif phone.startswith('+62'):
        return phone
    elif phone.startswith('62'):
        return '+' + phone
    else:
        return phone
    
def generate_username(email):
    name_part = email.split('@')[0]
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"{name_part}_{random_suffix}"

# Google OAuth Config
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    access_token_url='https://oauth2.googleapis.com/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
    client_kwargs={'scope': 'openid email profile'},
)

# Fungsi untuk mengecek keberadaan username, nomor hp, email dan password serta untuk menghasilkan kode verifikasi 6 digit
def check_username_in_db(username):
    user = Users.query.filter_by(username=username).first()
    return user is not None

def check_phone_in_db(phone):
    user = Users.query.filter_by(nomor_hp=phone).first()
    return user is not None


def check_email_in_db(email):
    user = Users.query.filter_by(email=email).first()
    return user is not None

def check_password_in_db(username, password):
    user = Users.query.filter_by(username=username).first()
    if user:
        return check_password_hash(user.password, password)
    return False

def generate_verification_code():
    return random.randint(100000, 999999)

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    try:
        return render_template('csrf_error.html', reason=e.description), 400
    except:
        # Fallback jika template tidak ditemukan
        flash("Sesi Anda mungkin telah kedaluwarsa. Silakan refresh halaman dan coba lagi.", "danger")
        if current_user.is_authenticated:
            if current_user.level == 'admin':
                return redirect(url_for('admin_users'))
            elif current_user.level == 'penilai':
                return redirect(url_for('penilai_dashboard'))
            elif current_user.level == 'peserta':
                return redirect(url_for('peserta_dashboard'))
        return redirect(url_for('login'))

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template("429.html", message="Terlalu banyak percobaan login. Silakan coba lagi nanti."), 429

@app.context_processor
def inject_notifications():
    user = None
    unread_count = 0
    if session.get('username'):
        user = Users.query.filter_by(username=session.get('username')).first()
    elif session.get('user'):
        user = Users.query.filter_by(username=session['user'].get('username')).first()
    if user:
        unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
    return dict(notification_count=unread_count)

# --- Middleware untuk cek login dan role ---
def my_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # logika tambahan
        return f(*args, **kwargs)
    return decorated_function

# Endpoint login
@app.route('/login/', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        
        # Query user dari database
        user = Users.query.filter_by(username=username).first()
        
        if not user:
            logging.warning(f"Login gagal: username '{username}' tidak ditemukan.")
            flash("Username salah!", "danger")
        elif not check_password_hash(user.password, password):
            logging.warning(f"Login gagal: password salah untuk user '{username}'.")
            flash("Password salah!", "danger")
        else:
            login_user(user)
            session['username'] = username  
            session['role'] = user.level
            safe_username = escape(username)
            logging.info(f"User '{username}' berhasil login sebagai {user.level}.")
            flash(f"Login berhasil! Selamat datang, {safe_username}.", "success")
            session['first_time_login'] = True
            
            # Redirect sesuai role
            if user.level == "admin":
                return redirect(url_for('admin_dashboard'))
            elif user.level == "penilai":
                return redirect(url_for('penilai_dashboard'))
            elif user.level == "peserta":
                return redirect(url_for('peserta_dashboard'))
            else:
                # Default jika role tidak dikenali
                return redirect(url_for('login')) 
    return render_template('login.html', form=form)

# Endpoint login with Google
@app.route('/login/google/', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login_google():
    redirect_uri = url_for('login_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# Endpoint Callback Login With Google
@app.route('/login/google/callback/')
def login_google_callback():
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')  
        resp.raise_for_status()  
        user_info = resp.json()
    except Exception as e:
        logging.warning(f"Login Google gagal: {e}") 
        flash("Gagal login dengan Google. Silakan coba lagi.", "danger")
        return redirect(url_for('login'))
    
    # Proses lanjut jika data user berhasil diambil
    email = user_info.get('email')
    username = user_info.get('name') or "Pengguna"
    picture = user_info.get('picture') or "img/default-user.png"
    
    if not email:
        flash("Email dari akun Google tidak ditemukan.", "danger")
        return redirect(url_for('login'))
    
    # ✅ Validasi hanya email Gmail
    if not email.endswith('@gmail.com'):
        flash("Login hanya diizinkan dengan akun Gmail.", "danger")
        return redirect(url_for('login'))
    
    user = Users.query.filter_by(email=email).first()
    if user:
        # Update foto dari Google jika belum tersimpan
        if not user.foto or user.foto == "img/default-user.png":
            user.foto = user_info.get('picture') or "img/default-user.png"
            db.session.commit()
            
        session['username'] = user.username
        session['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'nama_lengkap': user.nama_lengkap,
            'foto': user.foto,
            'level': user.level
        }
        session['first_time_login'] = True
        session.modified = True 
        print("✅ Session set:", session.get('user'))
        logging.info(f"User '{user.username}' berhasil login via Google.")
        flash(f"Login berhasil! Selamat datang, {escape(user.nama_lengkap)}.", "success")
        
        # Redirect sesuai role
        if user.level == "admin":
            return redirect(url_for('admin_dashboard'))
        elif user.level == "penilai":
            return redirect(url_for('penilai_dashboard'))
        elif user.level == "peserta":
            return redirect(url_for('peserta_dashboard'))
        else:
            return redirect(url_for('admin_dashboard'))
    else:
        # Jika belum ada, arahkan ke konfirmasi registrasi
        session['pending_user'] = user_info
        logging.warning(f"Percobaan login Google dari email '{email}' belum terdaftar.")
        flash("Akun Google Anda belum terdaftar. Lanjutkan registrasi?", "warning")
        return redirect(url_for('confirm_register'))
    
# Endpoint Fisrt Confirm Register With Google
@app.route('/confirm-register/')
def confirm_register():
    user_info = session.get('pending_user')
    if not user_info:
        flash("Data user tidak ditemukan. Silakan login ulang.", "danger")
        return redirect(url_for('login'))
    form = RegisterForm()
    return render_template("confirm_register.html", user=user_info, form=form)

# Endpoint Confirm Register With Google
@app.route('/confirm-register', methods=['POST'])
def do_register():
    user_info = session.get('pending_user')
    if not user_info:
        flash("Data user tidak ditemukan. Silakan login ulang.", "danger")
        return redirect(url_for('login'))
    
    form = RegisterForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = user_info['email']
        
    # Validasi apakah username atau email sudah digunakan
        if Users.query.filter_by(email=email).first():
            flash("Email sudah digunakan. Silakan login.", "warning")
            return redirect(url_for('login'))
        if Users.query.filter_by(username=username).first():
            flash("Username sudah digunakan.", "warning")
            return redirect(url_for('confirm_register'))
    
        # Simpan ke database
        new_user = Users(
                username=username,
                password=generate_password_hash(secrets.token_urlsafe(12), method='pbkdf2:sha256'),
                nama_lengkap=user_info['name'],
                email=user_info['email'],
                jenis_kelamin='laki-laki',
                usia='0',
                foto=user_info.get('picture', 'img/default-user.png'),
                nomor_hp='',
                level='peserta',
                reset_token="",
                login_method="google",
                sidebar_state="expanded",
                status='aktif'
        )
        try:
            db.session.add(new_user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logging.error(f"Gagal menyimpan user Google baru: {e}")
            flash("Terjadi kesalahan saat registrasi. Coba lagi.", "danger")
            return redirect(url_for('confirm_register'))

        # Set session
        session['user'] = {
            'id': new_user.id,
            'username': new_user.username,
            'email': new_user.email,
            'nama_lengkap': new_user.nama_lengkap,
            'foto': new_user.foto,
            'level': new_user.level
        }
        print("Session setelah login Google:", dict(session))
        logging.info(f"User baru '{username}' berhasil registrasi dan login via Google.")
        flash("Registrasi berhasil! Anda sudah login untuk pertama kali.", "welcome")
        session['username'] = new_user.username
        session['first_time_login'] = True
        return redirect(url_for('index'))
    return render_template("confirm_register.html", user=user_info, form=form)

# Endpoint register
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('fullName', '').strip()
        email = request.form.get('email', '').strip().lower()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirmPassword', '')
        level = 'peserta'  
        
        # Apakah ada kolom yang kosong?
        if not all([full_name, email, username, password, confirm_password]):
            flash("Semua kolom wajib diisi.", "danger")
            return redirect(url_for('register'))
        
        # Validasi password dengan regex
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_pattern, password):
            flash("Password must have at least 8 characters, including uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for('register'))
        
        # Validasi apakah password dan confirmPassword cocok
        if password != confirm_password:
            flash("Password and Confirm Password must match!", "danger")
            return redirect(url_for('register'))
        
        # Cek keberadaan username dan email di database
        user_exists = check_username_in_db(username)
        email_exists = check_email_in_db(email)
        
        if not user_exists and not email_exists:
           # Enkripsi password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16) 
            # Masukkan data ke database
            try:
                # Ambil field tambahan dari form atau gunakan default
                jenis_kelamin = request.form.get('jenis_kelamin', 'laki-laki')
                usia = request.form.get('usia', '0')
                nomor_hp = request.form.get('nomor_hp', '')
                foto = request.form.get('foto', 'img/default-user.png')
                
                new_user = Users(
                    username=username,
                    password=hashed_password,
                    nama_lengkap=full_name,
                    email=email,
                    jenis_kelamin=jenis_kelamin,
                    usia=usia,
                    foto=foto,
                    nomor_hp=nomor_hp,
                    level=level,
                    reset_token="",
                    login_method="manual",
                    sidebar_state="expanded",
                    status='aktif'
                )
                db.session.add(new_user)
                db.session.commit()
                flash("Registrasi berhasil! Selamat datang di sistem kami. Silakan login untuk mulai menggunakan fitur.", "welcome")
                return redirect(url_for('login'))
            except IntegrityError as e:
                db.session.rollback()
                logging.error(f"Error during registration: {e}")
                flash("An error occurred during registration, Please try again.", "danger")
                print(e)
        elif user_exists and email_exists:
            flash("Username dan email Anda telah terdaftar.", "danger")
        elif user_exists:
            flash("Username Anda telah terdaftar.", "danger")
        elif email_exists:
            flash("Email Anda telah terdaftar.", "danger")
        return redirect(url_for('register'))
    return render_template('register.html')

# Endpoint Register With Google
@app.route('/register/google/', methods=['GET', 'POST'])
def register_google():
    redirect_uri = url_for('register_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

# Endpoint Callback Register With Google
@app.route('/register/google/callback/')
def register_google_callback():
    try:
        token = google.authorize_access_token()
        resp = google.get('userinfo')
        resp.raise_for_status() 
        user_info = resp.json()
    except Exception as e:
        print(f"Google registrasi error: {e}") 
        flash("Gagal melakukan registrasi dengan Google. Silakan coba lagi.", "danger")
        return redirect(url_for('register'))
    
    email = user_info['email']
    username = generate_username(email)
    
    # Simpan ke database
    new_user = Users(
            username=username,
            password=generate_password_hash(secrets.token_urlsafe(12), method='pbkdf2:sha256'),
            nama_lengkap=user_info['name'],
            email=user_info['email'],
            jenis_kelamin='laki-laki',
            usia='0',
            foto=user_info.get('picture', 'img/default-user.png'),
            nomor_hp='',
            level='peserta',
            reset_token="",
            login_method="google",
            sidebar_state="expanded",
            status='aktif'
    )
    if Users.query.filter_by(email=email).first():
        flash("Email sudah digunakan. Silakan login.", "warning")
        return redirect(url_for('login'))
    db.session.add(new_user)
    db.session.commit()
    
    # Login langsung setelah registrasi
    login_user(new_user)
    session['username'] = new_user.username
    session['user'] = {
        'id': new_user.id,
        'username': new_user.username,
        'email': new_user.email,
        'nama_lengkap': new_user.nama_lengkap,
        'foto': new_user.foto,
        'level': new_user.level
    }
    flash("Registrasi berhasil! Selamat datang pengguna baru. Anda sekarang login untuk pertama kali.", "welcome")
    return redirect(url_for('admin_dashboard'))

# Endpoint Find Account
@app.route('/find_account/', methods=['GET', 'POST'])
def find_account():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('no-hp')
        # Pastikan username diisi
        if not username:
            flash('Username wajib diisi.', 'danger')
            return redirect(url_for('find_account'))

        # ===== Kondisi 1: Username + Email =====
        if email and not phone:
            # Validasi format email
            email_pattern = r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
            if not re.match(email_pattern, email):
                flash('Alamat email tidak valid.', 'danger')
                return redirect(url_for('find_account'))
            user_exists = check_username_in_db(username)
            email_exists = check_email_in_db(email)

            if user_exists and email_exists:
                verification_code = generate_verification_code()
                session['verification_code'] = verification_code
                session['verification_code_expiry'] = time.time() + 180
                session['username'] = username
                # Kirim kode via email
                msg = Message('Verifikasi Akun Anda',
                              sender='adip98816@gmail.com',
                              recipients=[email])
                safe_code = escape(verification_code)
                msg.html = f"""
                <p>Halo,</p>
                <p>Berikut adalah kode verifikasi 6 digit untuk mengakses akun Anda:</p>
                <h2>{safe_code}</h2>
                <p>Atau klik <a href="{url_for('verify_code', _external=True)}" style="color: blue;">link ini</a> untuk melanjutkan.</p>
                """
                mail.send(msg)
                flash(f'Kode verifikasi telah dikirim ke email {escape(email)}', 'success')
                return redirect(url_for('verify_code'))
            elif not user_exists and not email_exists:
                flash('Username dan email tidak ditemukan.', 'danger')
            elif not user_exists:
                flash('Username tidak ditemukan.', 'danger')
            elif not email_exists:
                flash('Email tidak ditemukan.', 'danger')
    
        # ===== Kondisi 2: Username + Nomor HP =====
        elif phone and not email:
            normalized_phone = normalize_phone_number(phone)
            phone_pattern = r'^\+628\d{7,12}$'
            if not re.match(phone_pattern, normalized_phone):
                flash('Format nomor HP tidak valid. Gunakan nomor Indonesia.', 'danger')
                return redirect(url_for('find_account'))
            # Cek keberadaan username dan nomor HP di database
            user_exists = check_username_in_db(username)
            hp_exists = check_phone_in_db(normalized_phone)
            if user_exists and hp_exists:
                verification_code = generate_verification_code()
                session['verification_code'] = verification_code
                session['verification_code_expiry'] = time.time() + 180  # berlaku 3 menit
                session['username'] = username
                session['phone'] = normalized_phone
                send_whatsapp_code(normalized_phone, verification_code)
                flash(f'Kode verifikasi telah dikirim ke nomor WhatsApp {normalized_phone}', 'success')
                return redirect(url_for('verify_code'))
            # Penanganan error spesifik
            if not user_exists and not hp_exists:
                flash('Username dan nomor HP tidak ditemukan.', 'danger')
            elif not user_exists:
                flash('Username tidak ditemukan.', 'danger')
            elif not hp_exists:
                flash('Nomor HP tidak ditemukan.', 'danger')
            return redirect(url_for('find_account'))
        else:
            flash('Harap isi email atau nomor HP.', 'danger')
        return redirect(url_for('find_account'))
    return render_template('find_account.html')

# Endpoint untuk verify_code
@app.route('/verify_code/', methods=['GET', 'POST'])
def verify_code():
    if request.method == 'GET':
        expiry_time = session.get('verification_code_expiry', 0)
        return render_template('verify_code.html', expiry_time=int(expiry_time))
    # Metode untuk memproses data JSON
    expiry_time = session.get('verification_code_expiry', 0)
    data = request.get_json()
    if not data or 'verification_code' not in data:
        return jsonify({'message': 'Verification code is required.'}), 400
    code = data['verification_code']
    if time.time() > expiry_time:
        return jsonify({'message': 'Verification code has expired.'}), 400
    if 'verification_code' in session and session['verification_code'] == int(code):
        # Generate reset token dan set waktu kedaluwarsa
        reset_token = secrets.token_hex(16)
        expiry_time = datetime.now() + timedelta(minutes=10)
        username = session.get('username')
        user = Users.query.filter_by(username=username).first()
        if not user:
            return jsonify({'message': 'User not found.'}), 404
        # Simpan token dan waktu kedaluwarsa di database lalu sertakan URL reset password dengan token
        user.reset_token = reset_token
        user.token_exp = expiry_time
        db.session.commit()
        reset_password_url = escape(url_for('reset_password', token=reset_token, _external=True))
        return jsonify({
            'message': 'Verification successful.',
            'redirect_url': reset_password_url
        }), 200
    else:
        return jsonify({'message': 'Incorrect verification code.'}), 400
    
# Endpoint Reset Password
@app.route('/reset_password/', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        reset_token = request.args.get('token')
        if not reset_token:
            return jsonify({'error': "Token tidak ditemukan."}), 400
        # Validasi token
        user = Users.query.filter_by(reset_token=reset_token).first()
        if not user or datetime.now() > user.token_exp:
            if user:
                user.reset_token = None
                user.token_exp = None
                db.session.commit()
            return jsonify({'error': "Token tidak valid atau telah kedaluwarsa."}), 400
        # Jika token valid, arahkan ke halaman reset password
        return render_template('reset_password.html', token=escape(reset_token))
    if request.method == 'POST':
        data = request.get_json()
        reset_token = data.get('reset_token')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        # Debug input
        print(f"Reset token: {reset_token}, Password baru: {new_password}")
        # Validasi input
        if not reset_token or not new_password or not confirm_password:
            return jsonify({'error': "Semua data harus diisi."}), 400
        # Validasi pola password
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_pattern, new_password):
            return jsonify({'error': "Password harus terdiri dari minimal 8 karakter, termasuk huruf besar, kecil, angka, dan simbol."}), 400
        if new_password != confirm_password:
            return jsonify({'error': "Password dan konfirmasi password tidak cocok."}), 400
        # Validasi token
        user = Users.query.filter_by(reset_token=reset_token).first()
        if not user:
            return jsonify({'error': "Token reset password tidak valid."}), 400
        if datetime.now() > user.token_exp:
            user.reset_token = None
            user.token_exp = None
            db.session.commit()
            return jsonify({'error': "Token reset password telah kedaluwarsa."}), 400
        # Update password
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256', salt_length=16)
        user.password = hashed_password
        user.reset_token = None
        user.token_exp = None
        db.session.commit()
        print("Password berhasil diubah.")
        return jsonify({'message': "Password Anda telah berhasil diubah!"}), 200
    
# Route Index
@app.route("/")
@app.route("/index/")
def index():
    username = None
    user_data = None
    notification_count = 0
    profile_picture = None
    
    print("session keys:", session.keys())
    print("first_time_login:", session.get("first_time_login"))
    print("Session di /index/:", dict(session))
    first_time = session.get('first_time_login', None)

    # Cek login via session username (manual)
    if 'username' in session:
        username = session['username']
        user = Users.query.filter_by(username=username).first()
        if user:
            notification_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
            profile_picture = user.foto
        else:
            session.pop('username', None)

    # Cek login via session user (Google OAuth)
    elif 'user' in session:
        user_data = session['user'] 
        username = user_data.get('username')
        profile_picture = user_data.get('foto')
        user_id = user_data.get('id')
        if user_id:
            notification_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
            
    # Fix broken or missing profile picture - default to profil-default.png
    if not profile_picture or profile_picture in ['img/default-user.png', '']:
        profile_picture = 'images/profil-default.png'
        
    return render_template('index.html', username=username, profile_picture=profile_picture, notification_count=notification_count, user_data=user_data, first_time_login=first_time, debug_theme=session.get("theme"))

@app.route("/clear-first-login-flag", methods=["POST"])
@csrf.exempt
def clear_first_login_flag():
    session.pop('first_time_login', None)
    return '', 204

@app.before_request
def check_session():
    print("Session sekarang:", dict(session))
    
@app.route('/set-language/<lang_code>')
def set_language(lang_code):
    if lang_code in ['id', 'en']:
        session['lang'] = lang_code
    return redirect(request.referrer or url_for('index'))

@app.context_processor
def inject_current_lang():
    return dict(current_lang=session.get('lang', 'id'))

@app.route('/set-theme/<theme>', methods=['POST'])
def set_theme(theme):
    if theme in ['light', 'dark']:
        session['theme'] = theme
        session.modified = True
        return '', 204
    return 'Invalid theme', 400

@app.context_processor
def inject_theme():
    return dict(current_theme=session.get('theme', 'light'))

@app.route('/save_sidebar_state', methods=['POST'])
@login_required
def save_sidebar_state():
    data = request.get_json()
    state = data.get('state')

    if state not in ['expanded', 'collapsed']:
        return jsonify({'status': 'error', 'message': 'Invalid state'}), 400

    current_user.sidebar_state = state
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Sidebar state saved'})

# --- Route Dashboard Admin ---
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    sidebar_state = current_user.sidebar_state or 'expanded'
    if 'username' not in session:
        flash("Silakan login terlebih dahulu", "warning")
        return redirect(url_for('login'))
    
    user = current_user
    if not user:
        flash("Akses ditolak. User tidak valid!", "danger")
        return redirect(url_for('index'))
    
    # Cek level user
    if user.level == 'penilai':
        return redirect(url_for('penilai_dashboard'))
    elif user.level == 'peserta':
        return redirect(url_for('peserta_dashboard'))
    elif user.level != 'admin':
        flash("Akses ditolak. Anda bukan admin!", "danger")
        return redirect(url_for('index'))
    
    total_users = Users.query.count()
    total_participants = Participants.query.count() if db.inspect(db.engine).has_table("participants") else 0
    total_criteria = Criteria.query.count() if db.inspect(db.engine).has_table("criteria") else 0
    total_notifications = Notification.query.count()

    return render_template(
        'dashboard_admin.html',
        total_users=total_users,
        total_participants=total_participants,
        total_criteria=total_criteria,
        total_notifications=total_notifications,
        user=user,
        sidebar_state=sidebar_state
    )

# Route untuk melihat data penugasan penilai
@app.route('/admin/view_penugasan_penilai')
@login_required
def admin_view_penugasan_penilai():
    sidebar_state = current_user.sidebar_state or 'expanded'
    if 'username' not in session:
        flash("Silakan login terlebih dahulu", "warning")
        return redirect(url_for('login'))
    
    user = current_user
    if not user or user.level != 'admin':
        flash("Akses ditolak!", "danger")
        return redirect(url_for('index'))
    
    # Ambil semua event beserta kriteria dan evaluator yang ditugaskan
    events = Event.query.all()
    
    # Siapkan data untuk ditampilkan
    assignment_data = []
    for event in events:
        event_info = {
            'event': event,
            'criteria_assignments': []
        }
        
        # Ambil semua kriteria untuk event ini
        criteria_list = Criteria.query.filter_by(event_id=event.id_kegiatan).all()
        
        for criteria in criteria_list:
            # Ambil evaluator yang ditugaskan untuk kriteria ini
            evaluators = criteria.evaluators  # Menggunakan relationship yang sudah didefinisikan
            
            event_info['criteria_assignments'].append({
                'criteria': criteria,
                'evaluators': evaluators
            })
        
        assignment_data.append(event_info)
    
    return render_template(
        'penugasan_penilai_view.html',
        assignment_data=assignment_data,
        user=user,
        sidebar_state=sidebar_state
    )


# Middleware untuk membatasi akses hanya admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'role' not in session or session['role'] != 'admin':
            flash("Akses ditolak! Hanya admin yang bisa membuka halaman ini.", "error")
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# API Get Penilaian Peserta per Kegiatan
@app.route('/api/penilaian/peserta/<int:kegiatan_id>')
@login_required
@admin_required
def get_penilaian_peserta(kegiatan_id):
    try:
        # Ambil semua peserta yang terdaftar di kegiatan ini melalui many-to-many relationship
        peserta_list = Participants.query.join(
            tb_participant_kegiatan,
            Participants.id == tb_participant_kegiatan.c.participant_id
        ).filter(
            tb_participant_kegiatan.c.kegiatan_id == kegiatan_id
        ).all()
        
        data = []
        for p in peserta_list:
            # Cari user yang associated dengan peserta ini (berdasarkan email atau nama)
            # Note: Idealnya Participants punya relasi ke Users, tapi jika tidak ada kita cari manual
            # Asumsi: Participants.email match dengan Users.email
            user = Users.query.filter_by(email=p.email).first()
            
            status_validasi = "Belum Dinilai"
            total_nilai = 0
            has_nilai = False
            
            if user:
                # Cek penilaian
                penilaian = Penilaian.query.filter_by(id_users=user.id, id_kriteria=Criteria.query.filter_by(event_id=kegiatan_id).first().id_kriteria if Criteria.query.filter_by(event_id=kegiatan_id).first() else 0).all()
                
                # Hitung total nilai (simplifikasi, bisa disesuaikan dengan logika penilaian yang kompleks)
                nilai_records = Penilaian.query.filter(
                    Penilaian.id_users == user.id,
                    Penilaian.id_kriteria.in_([c.id_kriteria for c in Criteria.query.filter_by(event_id=kegiatan_id).all()])
                ).all()
                
                if nilai_records:
                    has_nilai = True
                    total_nilai = sum([n.nilai for n in nilai_records])
                    status_validasi = "Sudah Dinilai" # Bisa dikembangkan lagi logikanya
            
            data.append({
                'id': user.id if user else None, # User ID untuk keperluan hapus penilaian
                'participant_id': p.id,
                'nama': p.nama_lengkap,
                'golongan': p.golongan,
                'nilai': total_nilai if has_nilai else '-',
                'status': status_validasi,
                'has_nilai': has_nilai
            })
            
        return jsonify({'status': 'success', 'data': data}), 200
    except Exception as e:
        current_app.logger.exception('Error in /api/penilaian/peserta:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API Get Detail Penilaian per Kriteria
@app.route('/api/penilaian/detail/<int:user_id>/<int:kegiatan_id>')
@login_required
@admin_required
def get_detail_penilaian(user_id, kegiatan_id):
    try:
        # Ambil semua kriteria untuk kegiatan ini
        kriteria_list = Criteria.query.filter_by(event_id=kegiatan_id).all()
        
        data = []
        for kriteria in kriteria_list:
            # Ambil nilai untuk kriteria ini
            penilaian = Penilaian.query.filter_by(
                id_users=user_id,
                id_kriteria=kriteria.id_kriteria
            ).first()
            
            # Ambil nama penilai jika ada
            penilai_nama = None
            if penilaian and penilaian.evaluator_id:
                evaluator = Users.query.get(penilaian.evaluator_id)
                if evaluator:
                    penilai_nama = evaluator.nama_lengkap
            
            data.append({
                'kriteria': kriteria.nama_kriteria,
                'bobot': kriteria.bobot,
                'nilai': penilaian.nilai if penilaian else 0,
                'penilai': penilai_nama
            })
        
        return jsonify({'status': 'success', 'data': data}), 200
    except Exception as e:
        current_app.logger.exception('Error in /api/penilaian/detail:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Route View Detail Penilaian Peserta (Halaman)
@app.route('/admin/penilaian/detail_view/<int:user_id>/<int:kegiatan_id>')
@login_required
@admin_required
def admin_penilaian_detail_view(user_id, kegiatan_id):
    try:
        user = Users.query.get_or_404(user_id)
        participant = Participants.query.filter_by(email=user.email).first()
        event = Event.query.get_or_404(kegiatan_id)
        
        # Ambil semua kriteria untuk kegiatan ini
        kriteria_list = Criteria.query.filter_by(event_id=kegiatan_id).all()
        
        detail_scores = []
        for kriteria in kriteria_list:
            # Ambil nilai untuk kriteria ini
            penilaian = Penilaian.query.filter_by(
                id_users=user_id,
                id_kriteria=kriteria.id_kriteria
            ).first()
            
            # Ambil nama penilai jika ada
            penilai_nama = None
            if penilaian and penilaian.evaluator_id:
                evaluator = Users.query.get(penilaian.evaluator_id)
                if evaluator:
                    penilai_nama = evaluator.nama_lengkap
            
            detail_scores.append({
                'kriteria': kriteria.nama_kriteria,
                'bobot': kriteria.bobot,
                'nilai': penilaian.nilai if penilaian else 0,
                'penilai': penilai_nama
            })
            
        sidebar_state = current_user.sidebar_state or 'expanded'
            
        return render_template(
            'penilaian_peserta_detail.html',
            user=current_user,
            participant=participant,
            event=event,
            detail_scores=detail_scores,
            sidebar_state=sidebar_state
        )
    except Exception as e:
        current_app.logger.exception('Error in admin_penilaian_detail_view:')
        flash(f"Terjadi kesalahan: {str(e)}", "danger")
        return redirect(url_for('admin_manajemen_seleksi'))

# API Hapus Penilaian Peserta
@app.route('/api/penilaian/hapus', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def delete_penilaian():
    try:
        data = request.get_json(force=True)
        user_id = data.get('user_id')
        kegiatan_id = data.get('kegiatan_id')
        
        if not user_id or not kegiatan_id:
            return jsonify({'status': 'error', 'message': 'Parameter tidak lengkap'}), 400
            
        # Cari kriteria yang berhubungan dengan kegiatan ini
        criteria_ids = [c.id_kriteria for c in Criteria.query.filter_by(event_id=kegiatan_id).all()]
        
        if not criteria_ids:
             return jsonify({'status': 'error', 'message': 'Tidak ada kriteria untuk kegiatan ini'}), 404

        # Hapus penilaian
        deleted_count = Penilaian.query.filter(
            Penilaian.id_users == user_id,
            Penilaian.id_kriteria.in_(criteria_ids)
        ).delete(synchronize_session=False)
        
        # Hapus juga hasil seleksi jika ada
        HasilSeleksi.query.filter_by(id_users=user_id).delete()
        
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'Berhasil menghapus {deleted_count} data penilaian'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in /api/penilaian/hapus:')
        return jsonify({'status': 'error', 'message': str(e)}), 500




@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.all()
    users_data = []
    for u in users:
        user_dict = u.to_dict()
        # Cari biodata berdasarkan email
        biodata = Participants.query.filter_by(email=u.email).first()
        if biodata:
            # Tambahkan data biodata ke user_dict
            user_dict['biodata'] = {
                'nama_lengkap': biodata.nama_lengkap or '',
                'tanggal_lahir': biodata.tanggal_lahir.strftime('%Y-%m-%d') if biodata.tanggal_lahir else '',
                'alamat_tinggal': biodata.alamat_tinggal or '',
                'golongan': biodata.golongan or '',
                'tingkatan': biodata.tingkatan or '',
                'asal_gudep': biodata.asal_gudep or '',
                'asal_kwarran': biodata.asal_kwarran or '',
                'asal_kwarcab': biodata.asal_kwarcab or '',
                'asal_kwarda': biodata.asal_kwarda or '',
                'usia': biodata.usia or '',
                'jenis_kelamin': biodata.jenis_kelamin or '',
                'email': biodata.email or '',
                'nomor_hp': biodata.nomor_hp or '',
                'foto': biodata.foto or ''
            }
        else:
            user_dict['biodata'] = None
        users_data.append(user_dict)
    return render_template('manajemen_pengguna.html', sidebar_state=sidebar_state, users=users_data, time=time)

@app.route('/admin/add_user', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    sidebar_state = current_user.sidebar_state or 'expanded'

    if request.method == 'POST':
        # Ambil data dari form
        nama_lengkap = request.form.get('fullName')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form['confirmPassword']
        level = request.form.get('level')  

        # Validasi password dengan regex
        password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$"
        if not re.match(password_pattern, password):
            flash("Password must have at least 8 characters, including uppercase, lowercase, number, and special character.", "danger")
            return redirect(url_for('admin_users'))
        # Validasi apakah password dan confirmPassword cocok
        if password != confirm_password:
            flash("Password and Confirm Password must match!", "danger")
            return redirect(url_for('admin_users'))
        # Cek keberadaan username dan email di database
        user_exists = check_username_in_db(username)
        email_exists = check_email_in_db(email)
        if not user_exists and not email_exists:
            # Enkripsi password
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16) 
            # Masukkan data ke database
            try:
                # Ambil field tambahan dari form atau gunakan default
                jenis_kelamin = request.form.get('jenis_kelamin', 'laki-laki')
                usia = request.form.get('usia', '0')
                nomor_hp = request.form.get('nomor_hp', '')
                foto = request.form.get('foto', 'img/default-user.png')
                
                new_user = Users(
                    username=username,
                    password=hashed_password,
                    nama_lengkap=nama_lengkap,
                    email=email,
                    jenis_kelamin=jenis_kelamin,
                    usia=usia,
                    foto=foto,
                    nomor_hp=nomor_hp,
                    level=level,
                    reset_token="",
                    login_method="manual",
                    sidebar_state="expanded",
                    status='aktif'
                )
                db.session.add(new_user)
                db.session.commit()
                flash("Akun berhasil dibuat!", "success")
                return redirect(url_for('admin_users'))
            except Exception as e:
                db.session.rollback()
                logging.error(f"Error during registration: {e}")
                flash("An error occurred during registration, Please try again.", "danger")
                print(e)
        elif user_exists and email_exists:
            flash("Username dan email Anda telah terdaftar.", "danger")
        elif user_exists:
            flash("Username Anda telah terdaftar.", "danger")
        elif email_exists:
            flash("Email Anda telah terdaftar.", "danger")
        return redirect(url_for('admin_users'))
    return render_template('manajemen_pengguna.html', sidebar_state=sidebar_state, users=Users.query.all(), time=time)

# Admin/Import Data User
@app.route('/admin/import_users', methods=['POST'])
@login_required
@admin_required
def admin_import_users():
    if 'file' not in request.files:
        flash('Tidak ada file yang diupload!', 'error')
        return redirect(url_for('admin_users'))
    
    file = request.files['file']
    if not file.filename:
        flash('Nama file tidak valid!', 'error')
        return redirect(url_for('admin_users'))

    if file.mimetype not in [
        'text/csv',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]:
        flash('Tipe file tidak didukung!', 'error')
        return redirect(url_for('admin_users'))

    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if not allowed_file(file.filename, 'doc'):
        flash('Format file tidak diizinkan! Gunakan CSV atau Excel.', 'error')
        return redirect(url_for('admin_users'))

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        df = pd.read_csv(filepath) if ext == 'csv' else pd.read_excel(filepath)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_").str.replace("-", "_")

        required_cols = ['nama_lengkap', 'username', 'email', 'level']
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            flash(f"Kolom berikut tidak ditemukan: {', '.join(missing)}", 'error')
            return redirect(url_for('admin_users'))

        existing_usernames = {u[0] for u in db.session.query(Users.username).all()}
        valid_levels = {'admin', 'penilai', 'peserta'}
        count_added, count_skipped = 0, 0
        new_users = []

        for _, row in df.iterrows():
            # Validasi
            if pd.isna(row['username']) or pd.isna(row['email']):
                count_skipped += 1
                continue
            if row['username'] in existing_usernames:
                count_skipped += 1
                continue
            if row['level'] not in valid_levels:
                count_skipped += 1
                continue
            if '@' not in str(row['email']):
                count_skipped += 1
                continue

            password = row['password'] if 'password' in df.columns and pd.notna(row['password']) else '12345678'
            new_users.append(Users(
                nama_lengkap=row['nama_lengkap'],
                username=row['username'],
                email=row['email'],
                password=generate_password_hash(str(password)),
                level=row['level'],
                jenis_kelamin=row.get('jenis_kelamin'),
                usia=row.get('usia', 0),
                nomor_hp=row.get('nomor_hp', "")
            ))
            count_added += 1

        if new_users:
            db.session.bulk_save_objects(new_users)
            db.session.commit()
            flash({
                'category': 'success',
                'title': 'Import Berhasil ✅',
                'message': f'{count_added} pengguna baru ditambahkan, {count_skipped} dilewati.'
            })
        else:
            flash({
                'category': 'danger',
                'title': 'Tidak Ada Data Baru ⚠️',
                'message': 'File sudah diproses, tetapi tidak ada pengguna baru yang ditambahkan.'
            })
    except Exception as e:
        db.session.rollback()
        app.logger.exception(f"Import gagal: {e}")
        flash(f'Terjadi kesalahan saat import: {e}', 'error')
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)
    return redirect(url_for('admin_users'))

# Download Data User
@app.route('/download_users')
def download_users():
    users = Users.query.order_by(Users.nama_lengkap.asc()).all()
    
    # Jika tidak ada data pengguna
    if not users:
        flash({
            'category': 'warning',
            'title': 'Tidak Ada Data ⚠️',
            'message': 'Tidak ada data pengguna yang tersedia untuk diunduh.'
        })
        return redirect(url_for('admin_users'))
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Data Pengguna"
    headers = ['No', 'Nama Lengkap', 'Username', 'Email', 'Level', 'Status']
    ws.append(headers)
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="4F81BD")
    center_align = Alignment(horizontal="center", vertical="center")
    thin_border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin"),
    )
    
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_align
        cell.border = thin_border
    
    for i, u in enumerate(users, start=1):
        ws.append([
            i,
            u.nama_lengkap or '',
            u.username or '',
            u.email or '',
            u.level or '',
            u.status or ''
        ])
        
    # Auto width untuk setiap kolom
    for column_cells in ws.columns:
        length = max(len(str(cell.value)) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = length + 2
    ws.freeze_panes = "A2"
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"data_pengguna_{timestamp}.xlsx"
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

# Admin/Delete User
@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    # Hanya admin boleh hapus
    if current_user.level != "admin":
        flash("Anda tidak memiliki izin untuk menghapus pengguna.", "danger")
        return redirect(url_for('admin_users'))
    
    user = Users.query.get(user_id)
    if not user:
        flash("Pengguna tidak ditemukan!", "danger")
        return redirect(url_for('admin_users'))
    
    # Proteksi: admin tidak bisa menghapus dirinya sendiri
    if user.id == current_user.id:
        flash("Anda tidak dapat menghapus akun Anda sendiri!", "warning")
        return redirect(url_for('admin_users'))
    try:
        db.session.delete(user)
        db.session.commit()
        flash(f"Pengguna '{user.username}' berhasil dihapus!", "success")
        logging.info(f"User '{user.username}' berhasil dihapus oleh admin.")
    except Exception as e:
        db.session.rollback()
        flash("Terjadi kesalahan saat menghapus data.", "danger")
        logging.error(f"Gagal menghapus user_id {user_id}: {e}")
    return redirect(url_for('admin_users'))

# Admin/Edit User
@app.route('/admin/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = Users.query.get(user_id)
    if not user:
        flash("Pengguna tidak ditemukan!", "danger")
        return redirect(url_for('admin_users'))
    
    # Jika GET request, hanya redirect ke halaman manajemen pengguna
    # (form edit ditangani di frontend dengan Alpine.js)
    if request.method == 'GET':
        return redirect(url_for('admin_users'))
    
    # POST request - proses update data
    try:
        # Update data dari form
        # Field required
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        if not nama_lengkap:
            flash("Nama lengkap harus diisi.", "danger")
            return redirect(url_for('admin_users'))
        user.nama_lengkap = nama_lengkap
        
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash("Email harus diisi.", "danger")
            return redirect(url_for('admin_users'))
        # Cek apakah email sudah digunakan oleh user lain
        existing_user = Users.query.filter(Users.email == email, Users.id != user_id).first()
        if existing_user:
            flash("Email sudah digunakan oleh pengguna lain.", "danger")
            return redirect(url_for('admin_users'))
        user.email = email
        
        username = request.form.get('username', '').strip()
        if not username:
            flash("Username harus diisi.", "danger")
            return redirect(url_for('admin_users'))
        # Cek apakah username sudah digunakan oleh user lain
        existing_user = Users.query.filter(Users.username == username, Users.id != user_id).first()
        if existing_user:
            flash("Username sudah digunakan oleh pengguna lain.", "danger")
            return redirect(url_for('admin_users'))
        user.username = username
        
        # Field optional dengan validasi
        level = request.form.get('level', '').strip()
        if level and level in ['admin', 'penilai', 'peserta']:
            user.level = level
        elif not user.level:  # Pastikan level selalu ada
            user.level = 'peserta'
        
        status = request.form.get('status', '').strip()
        if status:
            # Normalisasi status: "nonaktif" -> "non-aktif"
            if status == 'nonaktif':
                status = 'non-aktif'
            if status in ['aktif', 'non-aktif']:
                user.status = status
        elif not user.status:  # Pastikan status selalu ada
            user.status = 'aktif'
        
        jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
        if jenis_kelamin:
            # Normalisasi jenis kelamin
            if jenis_kelamin.lower() in ['laki-laki', 'laki laki']:
                user.jenis_kelamin = 'laki-laki'
            elif jenis_kelamin.lower() == 'perempuan':
                user.jenis_kelamin = 'perempuan'
        elif not user.jenis_kelamin:  # Pastikan jenis_kelamin selalu ada
            user.jenis_kelamin = 'laki-laki'
        
        usia = request.form.get('usia', '').strip()
        if usia:
            user.usia = str(usia)  # Pastikan string
        elif not user.usia:  # Jika kosong dan belum ada nilai sebelumnya
            user.usia = '0'
        
        nomor_hp = request.form.get('nomor_hp', '').strip()
        if nomor_hp:
            user.nomor_hp = nomor_hp
        elif not user.nomor_hp:  # Jika kosong dan belum ada nilai sebelumnya
            user.nomor_hp = ''

        # Handle upload foto jika ada
        foto_file = request.files.get('foto')
        if foto_file and foto_file.filename:
            # Validasi file extension
            if not allowed_file(foto_file.filename, 'image'):
                flash("Format file tidak didukung! Gunakan file gambar (png, jpg, jpeg, gif).", "danger")
                return redirect(url_for('admin_users'))
            
            try:
                # Generate unique filename
                filename = secure_filename(foto_file.filename)
                if not filename:
                    flash("Nama file tidak valid.", "danger")
                    return redirect(url_for('admin_users'))
                    
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_filename = f"{timestamp}_{filename}"
                
                # Buat folder users jika belum ada
                users_upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'users')
                os.makedirs(users_upload_dir, exist_ok=True)
                
                # Simpan file
                foto_path = os.path.join(users_upload_dir, unique_filename)
                foto_file.save(foto_path)
                
                # Verifikasi file berhasil disimpan
                if os.path.exists(foto_path) and os.path.getsize(foto_path) > 0:
                    # Update path foto (relative dari static folder untuk url_for)
                    user.foto = f"uploads/users/{unique_filename}"
                    logging.info(f"Foto berhasil diupload untuk user_id {user_id}: {foto_path}")
                else:
                    flash("Gagal menyimpan file foto. Silakan coba lagi.", "danger")
                    logging.error(f"File tidak ditemukan atau kosong setelah save: {foto_path}")
                    return redirect(url_for('admin_users'))
            except Exception as e:
                flash(f"Terjadi kesalahan saat mengupload foto: {str(e)}", "danger")
                logging.error(f"Error uploading foto for user_id {user_id}: {e}")
                current_app.logger.exception('Error uploading foto:')
                return redirect(url_for('admin_users'))

        db.session.commit()
        flash(f"Data pengguna '{user.username}' berhasil diperbarui!", "success")
        log_activity(
            current_user.id,
            f'Mengupdate data pengguna: {user.username}'
        )
    except IntegrityError as e:
        db.session.rollback()
        flash("Email atau username sudah digunakan oleh pengguna lain.", "danger")
        logging.error(f"Integrity error saat update user_id {user_id}: {e}")
        current_app.logger.exception('Integrity error in edit_user:')
    except ValueError as e:
        db.session.rollback()
        flash(f"Data tidak valid: {str(e)}", "danger")
        logging.error(f"Value error saat update user_id {user_id}: {e}")
        current_app.logger.exception('Value error in edit_user:')
    except Exception as e:
        db.session.rollback()
        error_msg = str(e)
        flash(f"Terjadi kesalahan saat memperbarui data: {error_msg}", "danger")
        logging.error(f"Gagal memperbarui user_id {user_id}: {error_msg}")
        current_app.logger.exception('Error in edit_user:')
        # Print error untuk debugging
        print(f"ERROR in edit_user: {error_msg}")
        import traceback
        traceback.print_exc()
    
    return redirect(url_for('admin_users'))

# Manajemen Seleksi   
@app.route('/admin/manajemen_seleksi')
@login_required
@admin_required
def admin_manajemen_seleksi():
    sidebar_state = current_user.sidebar_state or 'expanded'
    
    # Get all events
    kegiatan_list = Event.query.all()
    
    # Convert to serializable format if needed
    kegiatan_data = []
    for kegiatan in kegiatan_list:
        # Hitung jumlah peserta
        jumlah_peserta = kegiatan.registered_participants.count()
        
        kegiatan_data.append({
            'id': kegiatan.id_kegiatan,
            'nama': kegiatan.nama_kegiatan,
            'jenis': kegiatan.jenis_kegiatan,
            'waktu_mulai': kegiatan.waktu_pelaksanaan_dimulai.strftime('%Y-%m-%d') if kegiatan.waktu_pelaksanaan_dimulai else None,
            'waktu_selesai': kegiatan.waktu_pelaksanaan_selesai.strftime('%Y-%m-%d') if kegiatan.waktu_pelaksanaan_selesai else None,
            'jumlah_peserta': jumlah_peserta
        })
    
    return render_template("manajemen_seleksi.html", kegiatan_list=kegiatan_list, kegiatan_data=kegiatan_data, sidebar_state=sidebar_state)

# Route untuk halaman penugasan penilai
@app.route('/admin/penugasan_penilai')
@login_required
@admin_required
def admin_penugasan_penilai():
    sidebar_state = current_user.sidebar_state or 'expanded'
    events = Event.query.all()
    evaluators = Users.query.filter_by(level='penilai').all()
    
    # Build assignment matrix
    assignments = {}
    for evaluator in evaluators:
        evaluator_assignments = {}
        
        # Get assigned criteria grouped by event
        # We assume evaluator.assigned_criteria exists due to the backref in Criteria model
        if hasattr(evaluator, 'assigned_criteria'):
            for criterion in evaluator.assigned_criteria:
                if criterion.event_id not in evaluator_assignments:
                    evaluator_assignments[criterion.event_id] = []
                evaluator_assignments[criterion.event_id].append(criterion.id_kriteria)
        
        assignments[evaluator.id] = evaluator_assignments
    
    # Prepare criteria data for frontend
    events_criteria = {}
    for event in events:    
        events_criteria[event.id_kegiatan] = [
            {'id': c.id_kriteria, 'nama': c.nama_kriteria} 
            for c in event.kriteria
        ]

    return render_template(
        "manajemen-seleksi/penugasan_penilai.html", 
        events=events,
        evaluators=evaluators,
        assignments=assignments,
        events_criteria=events_criteria,
        sidebar_state=sidebar_state
    )

# API untuk update penugasan kriteria penilai
@app.route('/api/update_evaluator_criteria', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def update_evaluator_criteria():
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        evaluator_id = data.get('evaluator_id')
        criteria_ids = data.get('criteria_ids', []) # List of selected criteria IDs
        
        if not event_id or not evaluator_id:
            return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
        
        event = Event.query.get_or_404(event_id)
        evaluator = Users.query.get_or_404(evaluator_id)
        
        # 1. Update Criteria Assignment
        # Get all criteria for this event
        event_criteria = Criteria.query.filter_by(event_id=event_id).all()
        
        # Remove evaluator from all event criteria first
        for criterion in event_criteria:
            if evaluator in criterion.evaluators:
                criterion.evaluators.remove(evaluator)
        
        # Add evaluator to selected criteria
        for c_id in criteria_ids:
            criterion = Criteria.query.get(c_id)
            if criterion and criterion.event_id == int(event_id):
                criterion.evaluators.append(evaluator)
        
        # 2. Sync with Event Assignment (tb_event_evaluator)
        # If evaluator has ANY criteria assigned, they should be in event.evaluators
        # If they have NO criteria assigned, they should be removed from event.evaluators (subject to min 3 rule)
        
        has_criteria = len(criteria_ids) > 0
        
        if has_criteria:
            if evaluator not in event.evaluators:
                event.evaluators.append(evaluator)
        else:
            # Trying to remove evaluator from event completely
            if evaluator in event.evaluators:
                # Check min 3 rule
                # We need to count how many evaluators are assigned to this event
                # excluding the current one if we are about to remove them
                current_evaluator_count = len(event.evaluators)
                
                if current_evaluator_count <= 3:
                     # Revert criteria changes? 
                     # Or just block the whole operation if it results in < 3 evaluators?
                     # But wait, maybe they just wanted to change criteria, not remove the user?
                     # If criteria_ids is empty, it means they are being unassigned.
                     
                     db.session.rollback()
                     return jsonify({
                         'status': 'error', 
                         'message': 'Minimal 3 penilai harus ditugaskan! Tidak dapat menghapus penilai ini.'
                     }), 400
                
                event.evaluators.remove(evaluator)
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Penugasan berhasil diperbarui'}), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error updating evaluator criteria:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Legacy API (kept for reference or fallback, but logic moved to update_evaluator_criteria)
@app.route('/api/assign_evaluator', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def assign_evaluator():
    return jsonify({'status': 'error', 'message': 'Please use criteria assignment'}), 400

@app.route('/api/unassign_evaluator', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def unassign_evaluator():
     return jsonify({'status': 'error', 'message': 'Please use criteria assignment'}), 400

# API untuk get assignments
@app.route('/api/get_assignments')
@login_required
@admin_required
def get_assignments():
    try:
        events = Event.query.all()
        result = []
        
        for event in events:
            event_data = {
                'id': event.id_kegiatan,
                'nama': event.nama_kegiatan,
                'evaluators': [{'id': e.id, 'nama': e.nama_lengkap} for e in event.evaluators]
            }
            result.append(event_data)
        
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        current_app.logger.exception('Error getting assignments:')
        return jsonify({'status': 'error', 'message': str(e)}), 500


# Konfigurasi Seleksi
@app.route('/api/save_config', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def save_config():
    try:
        data = request.get_json(force=True)
        activities = data.get('activities', [])
        criteria_list = data.get('criteria', [])

        if not activities and not criteria_list:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400
        created_events = []

        # Buat Event & Kuota
        for act in activities:
            nama = (act.get('nama') or '').strip()
            if not nama:
                continue
            
            # Parse tanggal
            mulai_date = None
            selesai_date = None
            waktu_pelaksanaan_dimulai_date = None
            waktu_pelaksanaan_selesai_date = None
            try:
                if act.get('mulai'):
                    # Handle datetime-local format (YYYY-MM-DDTHH:mm)
                    mulai_str = act['mulai']
                    if 'T' in mulai_str:
                        mulai_date = datetime.strptime(mulai_str.split('T')[0], '%Y-%m-%d').date()
                    else:
                        mulai_date = datetime.strptime(mulai_str, '%Y-%m-%d').date()
                if act.get('selesai'):
                    # Handle datetime-local format (YYYY-MM-DDTHH:mm)
                    selesai_str = act['selesai']
                    if 'T' in selesai_str:
                        selesai_date = datetime.strptime(selesai_str.split('T')[0], '%Y-%m-%d').date()
                    else:
                        selesai_date = datetime.strptime(selesai_str, '%Y-%m-%d').date()
                # Parse waktu pelaksanaan dimulai dan selesai
                if act.get('waktuMulai'):
                    try:
                        # Format datetime-local: "YYYY-MM-DDTHH:mm" atau "YYYY-MM-DD"
                        waktu_str = act['waktuMulai']
                        if 'T' in waktu_str:
                            waktu_pelaksanaan_dimulai_date = datetime.strptime(waktu_str.split('T')[0], '%Y-%m-%d').date()
                        else:
                            waktu_pelaksanaan_dimulai_date = datetime.strptime(waktu_str, '%Y-%m-%d').date()
                    except Exception:
                        waktu_pelaksanaan_dimulai_date = mulai_date if mulai_date else None
                else:
                    waktu_pelaksanaan_dimulai_date = mulai_date if mulai_date else None
                
                if act.get('waktuSelesai'):
                    try:
                        # Format datetime-local: "YYYY-MM-DDTHH:mm" atau "YYYY-MM-DD"
                        waktu_str = act['waktuSelesai']
                        if 'T' in waktu_str:
                            waktu_pelaksanaan_selesai_date = datetime.strptime(waktu_str.split('T')[0], '%Y-%m-%d').date()
                        else:
                            waktu_pelaksanaan_selesai_date = datetime.strptime(waktu_str, '%Y-%m-%d').date()
                    except Exception:
                        waktu_pelaksanaan_selesai_date = selesai_date if selesai_date else waktu_pelaksanaan_dimulai_date
                else:
                    waktu_pelaksanaan_selesai_date = selesai_date if selesai_date else waktu_pelaksanaan_dimulai_date
            except Exception:
                pass
            
            # Normalisasi jenis_kegiatan (ENUM case-sensitive)
            jenis_kegiatan_map = {
                'siaga': 'Siaga',
                'penggalang': 'Penggalang',
                'penegak': 'Penegak',
                'pandega': 'Pandega',
                'penegak dan pandega': 'Penegak dan Pandega'
            }
            jenis_raw = (act.get('jenis') or '').strip().lower()
            jenis_kegiatan = jenis_kegiatan_map.get(jenis_raw, 'Siaga')  # Default ke Siaga
            
            # Normalisasi skala_kegiatan (ENUM case-sensitive)
            skala_kegiatan_map = {
                'ranting': 'Ranting',
                'cabang': 'Cabang',
                'daerah': 'Daerah',
                'nasional': 'Nasional',
                'internasional': 'Internasional'
            }
            skala_raw = (act.get('skala') or '').strip().lower()
            skala_kegiatan = skala_kegiatan_map.get(skala_raw, 'Ranting')  # Default ke Ranting
            
            # Validasi tempat_pelaksanaan
            tempat = (act.get('tempat') or '').strip()
            if not tempat:
                tempat = '-'
            
            # Validasi kwartir_penyelenggara
            kwartir = (act.get('kwartir') or '').strip()
            if not kwartir:
                kwartir = 'Kwartir Ranting'
            
            # Pastikan semua tanggal ada
            if not mulai_date:
                mulai_date = datetime.utcnow().date()
            if not selesai_date:
                selesai_date = mulai_date
            if not waktu_pelaksanaan_dimulai_date:
                waktu_pelaksanaan_dimulai_date = mulai_date
            if not waktu_pelaksanaan_selesai_date:
                waktu_pelaksanaan_selesai_date = waktu_pelaksanaan_dimulai_date
            
            # Validasi: Periode Seleksi harus selesai sebelum Waktu Pelaksanaan dimulai
            # Cek apakah mulai periode seleksi >= waktu pelaksanaan
            if mulai_date >= waktu_pelaksanaan_dimulai_date:
                return jsonify({
                    'status': 'error', 
                    'message': f'Periode Seleksi (mulai) untuk kegiatan "{nama}" harus sebelum Waktu Pelaksanaan dimulai'
                }), 400
            
            # Cek apakah selesai periode seleksi >= waktu pelaksanaan
            if selesai_date >= waktu_pelaksanaan_dimulai_date:
                return jsonify({
                    'status': 'error', 
                    'message': f'Periode Seleksi (selesai) untuk kegiatan "{nama}" harus sebelum Waktu Pelaksanaan dimulai'
                }), 400
            
            # Validasi: Waktu Pelaksanaan tidak boleh dalam kurun waktu Periode Seleksi
            # Cek apakah waktu pelaksanaan mulai dalam periode seleksi
            if waktu_pelaksanaan_dimulai_date >= mulai_date and waktu_pelaksanaan_dimulai_date <= selesai_date:
                return jsonify({
                    'status': 'error', 
                    'message': f'Waktu Pelaksanaan (mulai) untuk kegiatan "{nama}" tidak boleh dalam kurun waktu Periode Seleksi'
                }), 400
            
            # Cek apakah waktu pelaksanaan selesai dalam periode seleksi
            if waktu_pelaksanaan_selesai_date >= mulai_date and waktu_pelaksanaan_selesai_date <= selesai_date:
                return jsonify({
                    'status': 'error', 
                    'message': f'Waktu Pelaksanaan (selesai) untuk kegiatan "{nama}" tidak boleh dalam kurun waktu Periode Seleksi'
                }), 400
            
            # Cek apakah waktu pelaksanaan overlap dengan periode seleksi (waktu pelaksanaan mencakup seluruh periode seleksi)
            if waktu_pelaksanaan_dimulai_date <= mulai_date and waktu_pelaksanaan_selesai_date >= selesai_date:
                return jsonify({
                    'status': 'error', 
                    'message': f'Waktu Pelaksanaan untuk kegiatan "{nama}" tidak boleh mencakup seluruh Periode Seleksi'
                }), 400
            
            # Parse jadwal tes (now as text)
            tanggal_tes = (act.get('tanggalTes') or '').strip()
            
            # Parse tempat tes
            tempat_tes = (act.get('tempatTes') or '').strip()
            
            event = Event(
                jenis_kegiatan=jenis_kegiatan,
                nama_kegiatan=nama,
                waktu_pelaksanaan_dimulai=waktu_pelaksanaan_dimulai_date,
                waktu_pelaksanaan_selesai=waktu_pelaksanaan_selesai_date,
                tempat_pelaksanaan=tempat,
                skala_kegiatan=skala_kegiatan,
                kwartir_penyelenggara=kwartir,
                mulai=mulai_date,
                selesai=selesai_date,
                tanggal_tes=tanggal_tes if tanggal_tes else None,
                tempat_tes=tempat_tes if tempat_tes else None
            )
            db.session.add(event)
            db.session.flush()
            
            # Ambil data kuota dari act (sudah disinkronkan dari contingents di frontend)
            putra = int(act.get('putra') or act.get('umpiPutra') or 0)
            putri = int(act.get('putri') or act.get('umpiPutri') or 0)
            
            kuota = Kuota(
                event_id=event.id_kegiatan,
                putra=putra,
                putri=putri
            )
            db.session.add(kuota)
            created_events.append(event)
            
            # Buat Criteria untuk event ini dari activities[index].criteria
            criteria_list = act.get('criteria', [])
            for c in criteria_list:
                nama_kriteria = (c.get('nama') or '').strip()
                if not nama_kriteria:
                    continue
                
                # Ambil skala (bobot) dari kriteria
                skala = c.get('skala') or c.get('bobot') or 0
                bobot = float(skala) if skala else 0.0
                
                # Ambil jenis kriteria
                jenis_kriteria_raw = c.get('jenis', 'Kualitatif')
                if isinstance(jenis_kriteria_raw, list):
                    # Jika jenis adalah array (untuk Tes Wawancara), gabungkan
                    aspek_str = ', '.join(jenis_kriteria_raw) if jenis_kriteria_raw else ''
                    jenis_kriteria = 'Kualitatif'  # Default untuk wawancara
                else:
                    # Jika jenis adalah string
                    jenis_kriteria = jenis_kriteria_raw if jenis_kriteria_raw else 'Kualitatif'
                    aspek_str = ''
                
                # Ambil jumlah soal jika ada
                jumlah_soal = c.get('jumlah_soal') or c.get('jumlahSoal') or None
                
                # Ambil deskripsi jika ada
                deskripsi = c.get('deskripsi', '')
                
                crit = Criteria(
                    event_id=event.id_kegiatan,
                    nama_kriteria=nama_kriteria,
                    aspek=aspek_str,
                    bobot=bobot,
                    deskripsi=deskripsi,
                    jenis_kriteria=jenis_kriteria,
                    jumlah_soal=int(jumlah_soal) if jumlah_soal else None
                )
                db.session.add(crit)
        
        # Fallback: jika criteria_list dikirim terpisah (backward compatibility)
        # Hanya diproses jika tidak ada criteria di dalam activities
        if criteria_list and not any(act.get('criteria') for act in activities):
            target_event_id = created_events[0].id_kegiatan if created_events else None
            for c in criteria_list:
                nama_kriteria = (c.get('nama') or '').strip()
                if not nama_kriteria:
                    continue
                    
                bobot = float(c.get('bobot') or c.get('skala') or 0)
                aspek = c.get('aspek', [])
                aspek_str = ', '.join(aspek) if isinstance(aspek, list) else (aspek or '')
                jumlah_soal = c.get('jumlah_soal') or c.get('jumlahSoal') or None
                deskripsi = c.get('deskripsi', '')
                jenis_kriteria = c.get('jenis_kriteria', 'Kualitatif')
                if isinstance(c.get('jenis'), list):
                    aspek_str = ', '.join(c.get('jenis', []))
                    jenis_kriteria = 'Kualitatif'
                elif c.get('jenis'):
                    jenis_kriteria = c.get('jenis')
                
                if target_event_id is None:
                    today = datetime.utcnow().date()
                    placeholder = Event(
                        jenis_kegiatan='Siaga',  # Default ENUM value
                        nama_kegiatan='(Default) Konfigurasi Seleksi',
                        waktu_pelaksanaan_dimulai=today,
                        waktu_pelaksanaan_selesai=today,
                        tempat_pelaksanaan='-',
                        skala_kegiatan='Ranting',  # Default ENUM value
                        kwartir_penyelenggara='-',
                        mulai=today,
                        selesai=today
                    )
                    db.session.add(placeholder)
                    db.session.flush()
                    target_event_id = placeholder.id_kegiatan
                crit = Criteria(
                    event_id=target_event_id,
                    nama_kriteria=nama_kriteria,
                    aspek=aspek_str,
                    bobot=bobot,
                    deskripsi=deskripsi,
                    jenis_kriteria=jenis_kriteria,
                    jumlah_soal=int(jumlah_soal) if jumlah_soal else None
                )
                db.session.add(crit)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Konfigurasi berhasil disimpan'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in /api/save_config:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API Get Konfigurasi Seleksi
@app.route('/api/get_config/<int:event_id>')
@login_required
@admin_required
def get_config(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        kuota = Kuota.query.filter_by(event_id=event_id).first()
        criteria_list = Criteria.query.filter_by(event_id=event_id).all()
        
        config_data = {
            'event': {
                'id': event.id_kegiatan,
                'nama_kegiatan': event.nama_kegiatan,
                'jenis_kegiatan': event.jenis_kegiatan,
                'skala_kegiatan': event.skala_kegiatan,
                'kwartir_penyelenggara': event.kwartir_penyelenggara,
                'tempat_pelaksanaan': event.tempat_pelaksanaan,
                'waktu_pelaksanaan_dimulai': event.waktu_pelaksanaan_dimulai.isoformat() if event.waktu_pelaksanaan_dimulai else None,
                'waktu_pelaksanaan_selesai': event.waktu_pelaksanaan_selesai.isoformat() if event.waktu_pelaksanaan_selesai else None,
                'mulai': event.mulai.isoformat() if event.mulai else None,
                'selesai': event.selesai.isoformat() if event.selesai else None,
                'tanggal_tes': event.tanggal_tes,
                'tempat_tes': event.tempat_tes
            },
            'kuota': {
                'putra': kuota.putra if kuota else 0,
                'putri': kuota.putri if kuota else 0
            },
            'criteria': [{
                'id': c.id_kriteria,
                'nama_kriteria': c.nama_kriteria,
                'bobot': c.bobot,
                'jenis_kriteria': c.jenis_kriteria,
                'aspek': c.aspek,
                'deskripsi': c.deskripsi,
                'jumlah_soal': c.jumlah_soal
            } for c in criteria_list]
        }
        return jsonify({'status': 'success', 'data': config_data}), 200
    except Exception as e:
        current_app.logger.exception('Error in /api/get_config:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Halaman View Konfigurasi Seleksi
@app.route('/admin/view_config')
@login_required
@admin_required
def view_config():
    sidebar_state = current_user.sidebar_state or 'expanded'
    events = Event.query.order_by(Event.id_kegiatan.desc()).all()
    return render_template("manajemen-seleksi/view_konfigurasi.html", 
                         events=events, 
                         sidebar_state=sidebar_state, 
                         user=current_user)

# API Update Konfigurasi Seleksi
@app.route('/api/update_config/<int:event_id>', methods=['PUT', 'POST'])
@login_required
@admin_required
@csrf.exempt
def update_config(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        data = request.get_json(force=True)
        
        # Update Event
        if 'event' in data:
            evt_data = data['event']
            if 'nama_kegiatan' in evt_data:
                event.nama_kegiatan = evt_data['nama_kegiatan'].strip()
            if 'jenis_kegiatan' in evt_data:
                jenis_kegiatan_map = {
                    'siaga': 'Siaga', 'penggalang': 'Penggalang', 'penegak': 'Penegak',
                    'pandega': 'Pandega', 'penegak dan pandega': 'Penegak dan Pandega'
                }
                jenis_raw = evt_data['jenis_kegiatan'].strip().lower()
                event.jenis_kegiatan = jenis_kegiatan_map.get(jenis_raw, event.jenis_kegiatan)
            if 'skala_kegiatan' in evt_data:
                skala_kegiatan_map = {
                    'ranting': 'Ranting', 'cabang': 'Cabang', 'daerah': 'Daerah',
                    'nasional': 'Nasional', 'internasional': 'Internasional'
                }
                skala_raw = evt_data['skala_kegiatan'].strip().lower()
                event.skala_kegiatan = skala_kegiatan_map.get(skala_raw, event.skala_kegiatan)
            if 'kwartir_penyelenggara' in evt_data:
                event.kwartir_penyelenggara = evt_data['kwartir_penyelenggara'].strip()
            if 'tempat_pelaksanaan' in evt_data:
                event.tempat_pelaksanaan = evt_data['tempat_pelaksanaan'].strip()
            if 'waktu_pelaksanaan_dimulai' in evt_data and evt_data['waktu_pelaksanaan_dimulai']:
                try:
                    event.waktu_pelaksanaan_dimulai = datetime.strptime(evt_data['waktu_pelaksanaan_dimulai'], '%Y-%m-%d').date()
                except:
                    pass
            if 'waktu_pelaksanaan_selesai' in evt_data and evt_data['waktu_pelaksanaan_selesai']:
                try:
                    event.waktu_pelaksanaan_selesai = datetime.strptime(evt_data['waktu_pelaksanaan_selesai'], '%Y-%m-%d').date()
                except:
                    pass
            if 'mulai' in evt_data and evt_data['mulai']:
                try:
                    event.mulai = datetime.strptime(evt_data['mulai'], '%Y-%m-%d').date()
                except:
                    pass
            if 'selesai' in evt_data and evt_data['selesai']:
                try:
                    event.selesai = datetime.strptime(evt_data['selesai'], '%Y-%m-%d').date()
                except:
                    pass
            if 'tanggal_tes' in evt_data:
                event.tanggal_tes = evt_data['tanggal_tes'].strip() if evt_data['tanggal_tes'] else None
            if 'tempat_tes' in evt_data:
                event.tempat_tes = evt_data['tempat_tes'].strip() if evt_data['tempat_tes'] else None
        
        # Update Kuota
        if 'kuota' in data:
            kuota = Kuota.query.filter_by(event_id=event_id).first()
            if kuota:
                if 'putra' in data['kuota']:
                    kuota.putra = int(data['kuota']['putra'] or 0)
                if 'putri' in data['kuota']:
                    kuota.putri = int(data['kuota']['putri'] or 0)
            else:
                kuota = Kuota(
                    event_id=event_id,
                    putra=int(data['kuota'].get('putra', 0)),
                    putri=int(data['kuota'].get('putri', 0))
                )
                db.session.add(kuota)
        
        # Update Criteria
        if 'criteria' in data:
            # Get existing criteria map {id: object}
            existing_criteria = {c.id_kriteria: c for c in Criteria.query.filter_by(event_id=event_id).all()}
            
            # Process incoming criteria
            incoming_ids = []
            for c in data['criteria']:
                crit_id = c.get('id')
                
                if crit_id and crit_id in existing_criteria:
                    # Update existing
                    crit = existing_criteria[crit_id]
                    crit.nama_kriteria = c.get('nama_kriteria', '').strip() or 'Unnamed Criteria'
                    crit.bobot = float(c.get('bobot', 0))
                    crit.aspek = ', '.join(c.get('aspek', [])) if isinstance(c.get('aspek'), list) else (c.get('aspek', '') or '')
                    crit.deskripsi = c.get('deskripsi', '')
                    crit.jenis_kriteria = c.get('jenis_kriteria', 'Kualitatif')
                    crit.jumlah_soal = int(c.get('jumlah_soal')) if c.get('jumlah_soal') else None
                    incoming_ids.append(crit_id)
                else:
                    # Create new
                    new_crit = Criteria(
                        event_id=event_id,
                        nama_kriteria=c.get('nama_kriteria', '').strip() or 'Unnamed Criteria',
                        bobot=float(c.get('bobot', 0)),
                        aspek=', '.join(c.get('aspek', [])) if isinstance(c.get('aspek'), list) else (c.get('aspek', '') or ''),
                        deskripsi=c.get('deskripsi', ''),
                        jenis_kriteria=c.get('jenis_kriteria', 'Kualitatif'),
                        jumlah_soal=int(c.get('jumlah_soal')) if c.get('jumlah_soal') else None
                    )
                    db.session.add(new_crit)
            
            # Delete removed criteria (only if not referenced)
            for crit_id, crit in existing_criteria.items():
                if crit_id not in incoming_ids:
                    try:
                        db.session.delete(crit)
                        db.session.flush() # Check for integrity error immediately
                    except IntegrityError:
                        db.session.rollback()
                        # If referenced, just skip deletion or log warning
                        current_app.logger.warning(f"Cannot delete criteria {crit_id} because it is referenced.")
                        pass
        
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Konfigurasi berhasil diperbarui'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in /api/update_config:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API Delete Konfigurasi Seleksi
@app.route('/api/delete_config/<int:event_id>', methods=['DELETE', 'POST'])
@login_required
@admin_required
@csrf.exempt
def delete_config(event_id):
    try:
        event = Event.query.get_or_404(event_id)
        event_name = event.nama_kegiatan
        
        # Ambil semua kriteria ID dari kegiatan
        criteria = Criteria.query.filter_by(event_id=event_id).all()
        criteria_ids = [c.id_kriteria for c in criteria]
        
        # Hapus penilaian yang terkait dengan kriteria tersebut
        if criteria_ids:
            Penilaian.query.filter(Penilaian.id_kriteria.in_(criteria_ids)).delete(synchronize_session=False)
        
        # Hapus hasil seleksi yang terkait dengan kegiatan
        HasilSeleksi.query.filter_by(event_id=event_id).delete(synchronize_session=False)
        
        # Hapus akan cascade otomatis ke Kuota dan Criteria karena cascade="all, delete-orphan"
        db.session.delete(event)
        db.session.commit()
        
        return jsonify({'status': 'success', 'message': f'Konfigurasi "{event_name}" berhasil dihapus'}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in /api/delete_config:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API Delete Banyak Konfigurasi Seleksi
@app.route('/api/delete_config_bulk', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def delete_config_bulk():
    try:
        data = request.get_json(force=True)
        event_ids = data.get('event_ids', [])
        
        if not event_ids or not isinstance(event_ids, list):
            return jsonify({'status': 'error', 'message': 'Tidak ada ID konfigurasi yang dipilih'}), 400
        
        # Validasi bahwa semua event_id adalah integer
        try:
            event_ids = [int(eid) for eid in event_ids]
        except (ValueError, TypeError):
            return jsonify({'status': 'error', 'message': 'Format ID konfigurasi tidak valid'}), 400
        
        if len(event_ids) == 0:
            return jsonify({'status': 'error', 'message': 'Tidak ada konfigurasi yang dipilih'}), 400
        
        # Query semua event yang akan dihapus
        events = Event.query.filter(Event.id_kegiatan.in_(event_ids)).all()
        
        if not events:
            return jsonify({'status': 'error', 'message': 'Konfigurasi yang dipilih tidak ditemukan'}), 404
        
        # Simpan nama-nama event untuk pesan sukses
        event_names = [event.nama_kegiatan for event in events]
        deleted_count = len(events)
        
        # Ambil semua kriteria ID dari kegiatan yang akan dihapus
        criteria_ids = []
        for event in events:
            criteria = Criteria.query.filter_by(event_id=event.id_kegiatan).all()
            criteria_ids.extend([c.id_kriteria for c in criteria])
        
        # Hapus penilaian yang terkait dengan kriteria tersebut
        if criteria_ids:
            Penilaian.query.filter(Penilaian.id_kriteria.in_(criteria_ids)).delete(synchronize_session=False)
        
        # Hapus hasil seleksi yang terkait dengan kegiatan
        HasilSeleksi.query.filter(HasilSeleksi.event_id.in_(event_ids)).delete(synchronize_session=False)
        
        # Hapus semua event (cascade akan menghapus Kuota dan Criteria secara otomatis)
        for event in events:
            db.session.delete(event)
        
        db.session.commit()
        
        message = f'{deleted_count} konfigurasi berhasil dihapus'
        if deleted_count == 1:
            message = f'Konfigurasi "{event_names[0]}" berhasil dihapus'
        elif deleted_count <= 3:
            message = f'{deleted_count} konfigurasi berhasil dihapus: {", ".join(event_names)}'
        
        return jsonify({'status': 'success', 'message': message}), 200
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in /api/delete_config_bulk:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API Kegiatan 
@app.route('/api/kegiatan')
@login_required
@admin_required
def api_kegiatan():
    kegiatan = Event.query.all()
    result = [
        {
            "id": k.id_kegiatan,
            "nama_kegiatan": k.nama_kegiatan,
            "jenis_kegiatan": k.jenis_kegiatan,
            "waktu_pelaksanaan_dimulai": k.waktu_pelaksanaan_dimulai.strftime("%Y-%m-%d") if k.waktu_pelaksanaan_dimulai else None,
            "waktu_pelaksanaan_selesai": k.waktu_pelaksanaan_selesai.strftime("%Y-%m-%d") if k.waktu_pelaksanaan_selesai else None,
            "tempat_pelaksanaan": k.tempat_pelaksanaan,
            "skala_kegiatan": k.skala_kegiatan,
            "kwartir_penyelenggara": k.kwartir_penyelenggara,
            "mulai": k.mulai.strftime("%Y-%m-%d"),
            "selesai": k.selesai.strftime("%Y-%m-%d"),
        }
        for k in kegiatan
    ]
    return jsonify(result)

# API Kuota Kegiatan
@app.route('/api/kuota/<int:event_id>')
@login_required
@admin_required
def api_kuota(event_id):
    event = Event.query.get_or_404(event_id)
    if not event.kuota:
        return jsonify({"putra": 0, "putri": 0})

    # asumsi tabel Kuota punya kolom putra & putri
    kuota = event.kuota[0]
    return jsonify({
        "putra": kuota.putra,
        "putri": kuota.putri
    })

# API Data Peserta
@app.route("/api/peserta/<int:kegiatan_id>")
def get_peserta(kegiatan_id):
    peserta = Participants.query.filter_by(kegiatan_id=kegiatan_id).all()
    data = []
    for p in peserta:
        data.append({
            "nama_lengkap": p.nama_lengkap,
            "tanggal_lahir": str(p.tanggal_lahir),
            "jenis_kelamin": p.jenis_kelamin,
            "usia": p.usia,
            "alamat_tinggal": p.alamat_tinggal,
            "golongan": p.golongan,
            "tingkatan": p.tingkatan,
            "asal_gudep": p.asal_gudep,
            "asal_kwarran": p.asal_kwarran,
            "asal_kwarcab": p.asal_kwarcab,
            "asal_kwarda": p.asal_kwarda,
            "nomor_hp": p.nomor_hp,
            "email": p.email
        })
    return jsonify(data)

# API Search Peserta untuk Kelola Profil
@app.route("/api/peserta/search")
@login_required
@admin_required
def api_search_peserta():
    """API untuk mencari peserta berdasarkan email atau nama"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'message': 'Query tidak boleh kosong'}), 400
        
        # Cari peserta berdasarkan email atau nama
        peserta = Participants.query.filter(
            (Participants.email.ilike(f'%{query}%')) |
            (Participants.nama_lengkap.ilike(f'%{query}%'))
        ).first()
        
        if not peserta:
            return jsonify({'success': False, 'message': 'Peserta tidak ditemukan'}), 404
        
        # Format data peserta
        data = {
            'success': True,
            'peserta': {
                'id': peserta.id,
                'nama_lengkap': peserta.nama_lengkap or '',
                'tanggal_lahir': peserta.tanggal_lahir.strftime('%Y-%m-%d') if peserta.tanggal_lahir else '',
                'jenis_kelamin': peserta.jenis_kelamin or '',
                'usia': peserta.usia or '',
                'alamat_tinggal': peserta.alamat_tinggal or '',
                'golongan': peserta.golongan or '',
                'tingkatan': peserta.tingkatan or '',
                'asal_gudep': peserta.asal_gudep or '',
                'asal_kwarran': peserta.asal_kwarran or '',
                'asal_kwarcab': peserta.asal_kwarcab or '',
                'asal_kwarda': peserta.asal_kwarda or '',
                'nomor_hp': peserta.nomor_hp or '',
                'email': peserta.email or '',
                'foto': peserta.foto or 'img/default-user.png'
            }
        }
        
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error in api_search_peserta: {e}")
        current_app.logger.exception('Error in api_search_peserta:')
        return jsonify({'success': False, 'message': str(e)}), 500

# API List Peserta (gabungan users + participants)
@app.route("/api/peserta/list")
@login_required
@admin_required
def api_list_peserta():
    """API untuk mendapatkan semua data peserta (gabungan users dan participants)"""
    try:
        # Ambil semua user dengan level peserta
        users_peserta = Users.query.filter_by(level='peserta').all()
        
        peserta_data = []
        for user in users_peserta:
            # Cari data biodata dari tabel participants berdasarkan email
            biodata = Participants.query.filter_by(email=user.email).first()
            
            # Gabungkan data dari users dan participants
            peserta_item = {
                'id': user.id,
                'user_id': user.id,
                'participant_id': biodata.id if biodata else None,
                'username': user.username or '',
                'nama_lengkap': biodata.nama_lengkap if biodata and biodata.nama_lengkap else (user.nama_lengkap or ''),
                'email': user.email or '',
                'jenis_kelamin': biodata.jenis_kelamin if biodata and biodata.jenis_kelamin else (user.jenis_kelamin or ''),
                'usia': str(biodata.usia) if biodata and biodata.usia else (user.usia or '0'),
                'nomor_hp': biodata.nomor_hp if biodata and biodata.nomor_hp else (user.nomor_hp or ''),
                'foto': user.foto if user.foto and user.foto != 'img/default-user.png' else (biodata.foto if biodata and biodata.foto else 'img/default-user.png'),
                'status': user.status or 'aktif',
                'golongan': biodata.golongan if biodata else '',
                'tingkatan': biodata.tingkatan if biodata else '',
                'tanggal_lahir': biodata.tanggal_lahir.strftime('%Y-%m-%d') if biodata and biodata.tanggal_lahir else '',
                'alamat_tinggal': biodata.alamat_tinggal if biodata else '',
                'asal_gudep': biodata.asal_gudep if biodata else '',
                'asal_kwarran': biodata.asal_kwarran if biodata else '',
                'asal_kwarcab': biodata.asal_kwarcab if biodata else '',
                'asal_kwarda': biodata.asal_kwarda if biodata else ''
            }
            peserta_data.append(peserta_item)
        
        return jsonify({'success': True, 'peserta': peserta_data})
    except Exception as e:
        logging.error(f"Error in api_list_peserta: {e}")
        current_app.logger.exception('Error in api_list_peserta:')
        return jsonify({'success': False, 'message': str(e)}), 500

# API Add Peserta
@app.route("/api/peserta/add", methods=['POST'])
@login_required
@admin_required
def api_add_peserta():
    """API untuk menambah data peserta (users + participants)"""
    try:
        # Ambil data dari form
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
        usia = request.form.get('usia', '0').strip()
        nomor_hp = request.form.get('nomor_hp', '').strip()
        status = request.form.get('status', 'aktif').strip()
        
        # Validasi required fields
        if not nama_lengkap or not username or not email:
            return jsonify({'success': False, 'message': 'Nama lengkap, username, dan email wajib diisi'}), 400
        
        # Cek apakah username sudah ada
        if Users.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': 'Username sudah digunakan'}), 400
        
        # Cek apakah email sudah ada
        if Users.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email sudah digunakan'}), 400
        
        # Hash password jika ada
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16) if password else ''
        
        # Buat user baru
        new_user = Users(
            username=username,
            password=hashed_password,
            nama_lengkap=nama_lengkap,
            email=email,
            jenis_kelamin=jenis_kelamin or 'laki-laki',
            usia=usia or '0',
            nomor_hp=nomor_hp,
            level='peserta',
            status=status,
            foto='img/default-user.png',
            login_method='manual'
        )
        db.session.add(new_user)
        db.session.flush()  # Untuk mendapatkan ID user
        
        # Buat data participants jika ada data tambahan
        golongan = request.form.get('golongan', '').strip()
        tingkatan = request.form.get('tingkatan', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir', '').strip()
        alamat_tinggal = request.form.get('alamat_tinggal', '').strip()
        asal_gudep = request.form.get('asal_gudep', '').strip()
        asal_kwarran = request.form.get('asal_kwarran', '').strip()
        asal_kwarcab = request.form.get('asal_kwarcab', '').strip()
        asal_kwarda = request.form.get('asal_kwarda', '').strip()
        
        if golongan or tingkatan or tanggal_lahir or alamat_tinggal:
            # Konversi usia ke integer jika ada
            usia_int = int(usia) if usia and usia.isdigit() else 0
            
            new_participant = Participants(
                nama_lengkap=nama_lengkap,
                email=email,
                jenis_kelamin=jenis_kelamin or 'laki-laki',
                usia=usia_int,
                nomor_hp=nomor_hp,
                tanggal_lahir=datetime.strptime(tanggal_lahir, '%Y-%m-%d').date() if tanggal_lahir else datetime.now().date(),
                alamat_tinggal=alamat_tinggal or '',
                golongan=golongan or 'siaga',
                tingkatan=tingkatan or 'siaga mula',
                asal_gudep=asal_gudep or '',
                asal_kwarran=asal_kwarran or '',
                asal_kwarcab=asal_kwarcab or '',
                asal_kwarda=asal_kwarda or '',
                foto='img/default-user.png',
                level='peserta'
            )
            db.session.add(new_participant)
        
        db.session.commit()
        
        log_activity(current_user.id, f'Menambah peserta baru: {username}')
        return jsonify({'success': True, 'message': 'Peserta berhasil ditambahkan'})
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Data tidak valid: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in api_add_peserta: {e}")
        current_app.logger.exception('Error in api_add_peserta:')
        return jsonify({'success': False, 'message': str(e)}), 500

# API Edit Peserta
@app.route("/api/peserta/edit/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def api_edit_peserta(user_id):
    """API untuk mengedit data peserta (users + participants)"""
    try:
        user = Users.query.get(user_id)
        if not user or user.level != 'peserta':
            return jsonify({'success': False, 'message': 'Peserta tidak ditemukan'}), 404
        
        # Update data user
        nama_lengkap = request.form.get('nama_lengkap', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
        usia = request.form.get('usia', '0').strip()
        nomor_hp = request.form.get('nomor_hp', '').strip()
        status = request.form.get('status', 'aktif').strip()
        
        if nama_lengkap:
            user.nama_lengkap = nama_lengkap
        if username and username != user.username:
            # Cek apakah username sudah digunakan
            if Users.query.filter(Users.username == username, Users.id != user_id).first():
                return jsonify({'success': False, 'message': 'Username sudah digunakan'}), 400
            user.username = username
        if email and email != user.email:
            # Cek apakah email sudah digunakan
            if Users.query.filter(Users.email == email, Users.id != user_id).first():
                return jsonify({'success': False, 'message': 'Email sudah digunakan'}), 400
            user.email = email
        if jenis_kelamin:
            user.jenis_kelamin = jenis_kelamin
        if usia:
            user.usia = usia
        if nomor_hp:
            user.nomor_hp = nomor_hp
        if status:
            user.status = status
        
        # Update atau buat data participants
        biodata = Participants.query.filter_by(email=user.email).first()
        
        golongan = request.form.get('golongan', '').strip()
        tingkatan = request.form.get('tingkatan', '').strip()
        tanggal_lahir = request.form.get('tanggal_lahir', '').strip()
        alamat_tinggal = request.form.get('alamat_tinggal', '').strip()
        asal_gudep = request.form.get('asal_gudep', '').strip()
        asal_kwarran = request.form.get('asal_kwarran', '').strip()
        asal_kwarcab = request.form.get('asal_kwarcab', '').strip()
        asal_kwarda = request.form.get('asal_kwarda', '').strip()
        
        if biodata:
            # Update existing biodata
            if nama_lengkap:
                biodata.nama_lengkap = nama_lengkap
            if jenis_kelamin:
                biodata.jenis_kelamin = jenis_kelamin
            if usia:
                biodata.usia = int(usia) if usia.isdigit() else 0
            if nomor_hp:
                biodata.nomor_hp = nomor_hp
            if email:
                biodata.email = email
            if tanggal_lahir:
                biodata.tanggal_lahir = datetime.strptime(tanggal_lahir, '%Y-%m-%d').date()
            if alamat_tinggal:
                biodata.alamat_tinggal = alamat_tinggal
            if golongan:
                biodata.golongan = golongan
            if tingkatan:
                biodata.tingkatan = tingkatan
            if asal_gudep:
                biodata.asal_gudep = asal_gudep
            if asal_kwarran:
                biodata.asal_kwarran = asal_kwarran
            if asal_kwarcab:
                biodata.asal_kwarcab = asal_kwarcab
            if asal_kwarda:
                biodata.asal_kwarda = asal_kwarda
        elif golongan or tingkatan or tanggal_lahir or alamat_tinggal:
            # Buat biodata baru jika ada data
            usia_int = int(usia) if usia and usia.isdigit() else 0
            new_biodata = Participants(
                nama_lengkap=nama_lengkap or user.nama_lengkap,
                email=email or user.email,
                jenis_kelamin=jenis_kelamin or user.jenis_kelamin,
                usia=usia_int,
                nomor_hp=nomor_hp or user.nomor_hp,
                tanggal_lahir=datetime.strptime(tanggal_lahir, '%Y-%m-%d').date() if tanggal_lahir else datetime.now().date(),
                alamat_tinggal=alamat_tinggal or '',
                golongan=golongan or 'siaga',
                tingkatan=tingkatan or 'siaga mula',
                asal_gudep=asal_gudep or '',
                asal_kwarran=asal_kwarran or '',
                asal_kwarcab=asal_kwarcab or '',
                asal_kwarda=asal_kwarda or '',
                foto=user.foto or 'img/default-user.png',
                level='peserta'
            )
            db.session.add(new_biodata)
        
        db.session.commit()
        
        log_activity(current_user.id, f'Mengupdate data peserta: {user.username}')
        return jsonify({'success': True, 'message': 'Data peserta berhasil diperbarui'})
        
    except ValueError as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Data tidak valid: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in api_edit_peserta: {e}")
        current_app.logger.exception('Error in api_edit_peserta:')
        return jsonify({'success': False, 'message': str(e)}), 500

# API Delete Peserta
@app.route("/api/peserta/delete/<int:user_id>", methods=['POST'])
@login_required
@admin_required
def api_delete_peserta(user_id):
    """API untuk menghapus data peserta (users + participants)"""
    try:
        user = Users.query.get(user_id)
        if not user or user.level != 'peserta':
            return jsonify({'success': False, 'message': 'Peserta tidak ditemukan'}), 404
        
        username = user.username
        email = user.email
        
        # Hapus data participants jika ada
        biodata = Participants.query.filter_by(email=email).first()
        if biodata:
            db.session.delete(biodata)
        
        # Hapus user
        db.session.delete(user)
        db.session.commit()
        
        log_activity(current_user.id, f'Menghapus peserta: {username}')
        return jsonify({'success': True, 'message': 'Peserta berhasil dihapus'})
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error in api_delete_peserta: {e}")
        current_app.logger.exception('Error in api_delete_peserta:')
        return jsonify({'success': False, 'message': str(e)}), 500

# Tambah Kegiatan
@app.route('/admin/tambah_seleksi', methods=['GET', 'POST'])
@login_required
@admin_required
def tambah_seleksi():
    if request.method == 'POST':
        nama = request.form['nama_kegiatan']
        jenis = request.form['jenis_kegiatan']
        waktu_dimulai = request.form.get('waktu_pelaksanaan_dimulai', request.form.get('waktu_pelaksanaan', ''))
        waktu_selesai = request.form.get('waktu_pelaksanaan_selesai', waktu_dimulai)
        tempat = request.form['tempat_pelaksanaan']
        skala = request.form['skala_kegiatan']
        kwartir = request.form['kwartir_penyelenggara']
        
        # New Fields
        tanggal_tes = request.form.get('tanggal_tes')
        tempat_tes = request.form.get('tempat_tes')
        evaluator_ids = request.form.getlist('evaluators')

        new_event = Event(
            nama_kegiatan=nama,
            jenis_kegiatan=jenis,
            waktu_pelaksanaan_dimulai=datetime.strptime(waktu_dimulai, '%Y-%m-%d').date() if waktu_dimulai else datetime.utcnow().date(),
            waktu_pelaksanaan_selesai=datetime.strptime(waktu_selesai, '%Y-%m-%d').date() if waktu_selesai else datetime.utcnow().date(),
            tempat_pelaksanaan=tempat,
            skala_kegiatan=skala,
            kwartir_penyelenggara=kwartir,
            mulai=datetime.utcnow().date(),
            selesai=datetime.utcnow().date(),
            tanggal_tes=tanggal_tes if tanggal_tes else None,
            tempat_tes=tempat_tes
        )
        
        # Assign Evaluators
        if evaluator_ids:
            evaluators = Users.query.filter(Users.id.in_(evaluator_ids)).all()
            new_event.evaluators = evaluators
            
        db.session.add(new_event)
        db.session.commit()

        flash('Kegiatan berhasil ditambahkan!', 'success')
        return redirect(url_for('admin_manajemen_seleksi'))
    
    # Get all evaluators
    evaluators = Users.query.filter_by(level='penilai').all()
    return render_template("tambah_kegiatan.html", evaluators=evaluators)

# Edit Kegiatan
@app.route('/admin/edit_kegiatan/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_kegiatan(id):
    event = Event.query.get_or_404(id)
    if request.method == 'POST':
        event.nama_kegiatan = request.form['nama_kegiatan']
        event.jenis_kegiatan = request.form['jenis_kegiatan']
        if 'waktu_pelaksanaan_dimulai' in request.form:
            event.waktu_pelaksanaan_dimulai = datetime.strptime(request.form['waktu_pelaksanaan_dimulai'], '%Y-%m-%d').date()
        if 'waktu_pelaksanaan_selesai' in request.form:
            event.waktu_pelaksanaan_selesai = datetime.strptime(request.form['waktu_pelaksanaan_selesai'], '%Y-%m-%d').date()
        elif 'waktu_pelaksanaan' in request.form:
            # Fallback untuk backward compatibility
            waktu = datetime.strptime(request.form['waktu_pelaksanaan'], '%Y-%m-%d').date()
            event.waktu_pelaksanaan_dimulai = waktu
            event.waktu_pelaksanaan_selesai = waktu
        event.tempat_pelaksanaan = request.form['tempat_pelaksanaan']
        
        # Update Test Details
        tanggal_tes = request.form.get('tanggal_tes')
        if tanggal_tes:
            event.tanggal_tes = tanggal_tes
        event.tempat_tes = request.form.get('tempat_tes')
        
        # Update Evaluators
        evaluator_ids = request.form.getlist('evaluators')
        if evaluator_ids:
            evaluators = Users.query.filter(Users.id.in_(evaluator_ids)).all()
            event.evaluators = evaluators
        else:
            event.evaluators = []
            
        db.session.commit()
        flash('Kegiatan berhasil diupdate!', 'success')
        return redirect(url_for('admin_manajemen_seleksi'))
    
    # Get all evaluators
    evaluators = Users.query.filter_by(level='penilai').all()
    return render_template("edit_kegiatan.html", event=event, evaluators=evaluators)

# Hapus Kegiatan
@app.route('/admin/hapus_kegiatan/<int:id>', methods=['GET'])
@login_required
@admin_required
def hapus_kegiatan(id):
    event = Event.query.get_or_404(id)
    
    # Ambil semua kriteria ID dari kegiatan
    criteria = Criteria.query.filter_by(event_id=id).all()
    criteria_ids = [c.id_kriteria for c in criteria]
    
    # Hapus penilaian yang terkait dengan kriteria tersebut
    if criteria_ids:
        Penilaian.query.filter(Penilaian.id_kriteria.in_(criteria_ids)).delete(synchronize_session=False)
    
    # Hapus hasil seleksi yang terkait dengan kegiatan
    HasilSeleksi.query.filter_by(event_id=id).delete(synchronize_session=False)
    
    db.session.delete(event)
    db.session.commit()
    flash('Kegiatan berhasil dihapus!', 'danger')
    return redirect(url_for('admin_manajemen_seleksi'))

@app.route('/admin/detail_kegiatan/<int:id>')
@login_required
@admin_required
def detail_kegiatan(id):
    event = Event.query.get_or_404(id)
    return render_template("detail_kegiatan.html", event=event)

@app.route('/admin/kriteria')
@login_required
@admin_required
def admin_kriteria():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.count()
    return render_template('data_kriteria.html', sidebar_state=sidebar_state, user=users, time=time)
    
@app.route('/admin/pembobotan_kriteria')
@login_required
@admin_required
def admin_pembobotan_kriteria():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.count()
    
    # Ambil semua kegiatan untuk dropdown
    events = Event.query.order_by(Event.waktu_pelaksanaan_dimulai.desc()).all()
    
    # Ambil event_id dari query parameter jika ada
    selected_event_id = request.args.get('event_id', type=int)
    selected_event = None
    criteria_list = []
    pairwise_matrix = None
    ahp_results = None
    
    if selected_event_id:
        selected_event = Event.query.get(selected_event_id)
        if selected_event:
            criteria_list = Criteria.query.filter_by(event_id=selected_event_id).order_by(Criteria.id_kriteria).all()
            
            # Cek apakah sudah ada matriks perbandingan
            from app.fuzzy_ahp import get_pairwise_matrix_from_db
            import numpy as np
            criteria_ids = [c.id_kriteria for c in criteria_list]
            if criteria_ids:
                pairwise_matrix = get_pairwise_matrix_from_db(selected_event_id, criteria_ids)
            
            # Ambil hasil AHP jika ada
            ahp_results = AHPResults.query.filter_by(event_id=selected_event_id).first()
    
    return render_template(
        'pembobotan_kriteria.html', 
        sidebar_state=sidebar_state, 
        user=users, 
        time=time,
        events=events,
        selected_event=selected_event,
        criteria_list=criteria_list,
        pairwise_matrix=pairwise_matrix.tolist() if pairwise_matrix is not None else None,
        ahp_results=ahp_results
    )


# API untuk menyimpan matriks perbandingan berpasangan
@app.route('/api/save_pairwise_matrix/<int:event_id>', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def save_pairwise_matrix(event_id):
    """API untuk menyimpan matriks perbandingan berpasangan"""
    try:
        data = request.get_json(force=True)
        matrix_data = data.get('matrix', [])
        
        if not matrix_data:
            return jsonify({'success': False, 'message': 'Matriks tidak boleh kosong'}), 400
        
        # Ambil kriteria
        criterias = Criteria.query.filter_by(event_id=event_id).order_by(Criteria.id_kriteria).all()
        if not criterias:
            return jsonify({'success': False, 'message': 'Tidak ada kriteria untuk kegiatan ini'}), 400
        
        criteria_ids = [c.id_kriteria for c in criterias]
        n = len(criterias)
        
        # Validasi ukuran matriks
        if len(matrix_data) != n or any(len(row) != n for row in matrix_data):
            return jsonify({'success': False, 'message': f'Ukuran matriks harus {n}x{n}'}), 400
        
        # Konversi ke numpy array
        import numpy as np
        matrix = np.array(matrix_data, dtype=float)
        
        # Validasi nilai (harus 1-9 atau kebalikannya)
        for i in range(n):
            for j in range(n):
                if i == j:
                    if matrix[i, j] != 1.0:
                        return jsonify({'success': False, 'message': f'Diagonal harus 1.0 (baris {i+1}, kolom {j+1})'}), 400
                else:
                    val = matrix[i, j]
                    if val < 1/9 or val > 9:
                        return jsonify({'success': False, 'message': f'Nilai harus antara 1/9 sampai 9 (baris {i+1}, kolom {j+1})'}), 400
        
        # Simpan matriks
        from app.fuzzy_ahp import save_pairwise_matrix
        success, message = save_pairwise_matrix(event_id, criteria_ids, matrix)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        logging.error(f"Error saving pairwise matrix: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# API untuk menghitung bobot AHP
@app.route('/api/calculate_ahp/<int:event_id>', methods=['POST'])
@login_required
@admin_required
@csrf.exempt
def calculate_ahp(event_id):
    """API untuk menghitung bobot menggunakan AHP"""
    try:
        data = request.get_json(force=True)
        use_fuzzy = data.get('use_fuzzy', True)
        
        from app.fuzzy_ahp import calculate_ahp_weights, calculate_fuzzy_ahp_weights
        
        if use_fuzzy:
            success, message, results = calculate_fuzzy_ahp_weights(event_id)
        else:
            success, message, results = calculate_ahp_weights(event_id)
        
        if success:
            # Ambil hasil AHP yang sudah disimpan
            ahp_result = AHPResults.query.filter_by(event_id=event_id).first()
            result_data = {
                'success': True,
                'message': message,
                'results': results
            }
            
            if ahp_result:
                result_data['ahp_result'] = {
                    'lambda_max': float(ahp_result.lambda_max) if ahp_result.lambda_max else None,
                    'ci': float(ahp_result.ci) if ahp_result.ci else None,
                    'cr': float(ahp_result.cr) if ahp_result.cr else None,
                    'is_consistent': ahp_result.is_consistent,
                    'weights_json': ahp_result.weights_json
                }
            
            return jsonify(result_data)
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        logging.error(f"Error calculating AHP: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500

@app.route('/admin/peserta')
@login_required
@admin_required
def admin_peserta():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.count()
    return render_template('data_peserta.html', sidebar_state=sidebar_state, user=users, time=time)
    
@app.route('/admin/hasil_seleksi')
@login_required
@admin_required
def admin_hasil_seleksi():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.count()
    return render_template('hasil_seleksi.html', sidebar_state=sidebar_state, user=users, time=time)

@app.route('/admin/notifikasi')
@login_required
@admin_required
def admin_notifikasi():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.count()
    return render_template('notifikasi.html', sidebar_state=sidebar_state, user=users, time=time)
    
@app.route('/admin/log_aktivitas')
@login_required
@admin_required
def admin_log_aktivitas():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.count()
    return render_template('log_aktivity.html', sidebar_state=sidebar_state, user=users, time=time)

@app.route('/admin/settings')
@login_required
@admin_required
def admin_settings():
    sidebar_state = current_user.sidebar_state or 'expanded'
    users = Users.query.count()
    return render_template('settings.html', sidebar_state=sidebar_state, user=users, time=time)
    
@app.route('/penilai/dashboard')
@login_required
def penilai_dashboard():
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))

    # Ambil semua kegiatan yang aktif
    events = Event.query.order_by(Event.waktu_pelaksanaan_dimulai.desc()).all()
    
    # Tambahkan flag is_assigned untuk setiap event
    for event in events:
        event.is_assigned = current_user in event.evaluators
    
    # Hitung total peserta (dari tabel participants)
    total_peserta = Participants.query.count()
    
    sidebar_state = current_user.sidebar_state or 'expanded'

    return render_template(
        'penilai/dashboard.html',
        events=events,
        total_peserta=total_peserta,
        sidebar_state=sidebar_state
    )

@app.route('/penilai/penilaian')
@login_required
def penilai_penilaian():
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))

    # Ambil semua kegiatan yang aktif
    events = Event.query.order_by(Event.waktu_pelaksanaan_dimulai.desc()).all()
    
    # Tambahkan flag is_assigned untuk setiap event
    for event in events:
        event.is_assigned = current_user in event.evaluators
        event.jumlah_peserta = event.registered_participants.count()
    
    sidebar_state = current_user.sidebar_state or 'expanded'

    return render_template(
        'penilai/penilaian.html',
        events=events,
        sidebar_state=sidebar_state
    )

@app.route('/penilai/event/<int:event_id>/participants')
@login_required
def penilai_event_participants(event_id):
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    
    # Check if evaluator is assigned to this event
    if current_user not in event.evaluators:
        flash("Anda tidak ditugaskan untuk menilai kegiatan ini.", "error")
        return redirect(url_for('penilai_dashboard'))
    
    participants = event.registered_participants.all()
    
    # Cek status penilaian untuk setiap peserta oleh penilai ini
    for p in participants:
        # Cari user ID dari tabel Users berdasarkan email peserta
        user_peserta = Users.query.filter_by(email=p.email).first()
        if user_peserta:
            # Cek apakah sudah ada nilai dari penilai ini untuk peserta ini
            # Asumsi: jika ada minimal 1 nilai, dianggap sudah dinilai (bisa diperbaiki logikanya nanti)
            existing_score = Penilaian.query.filter_by(
                id_users=user_peserta.id, 
                evaluator_id=current_user.id
            ).first()
            p.is_graded = True if existing_score else False
            p.user_id_for_link = user_peserta.id # Use temp attribute for link
        else:
            p.is_graded = False
            p.user_id_for_link = 0 # Fallback

    sidebar_state = current_user.sidebar_state or 'expanded'
    
    return render_template(
        'penilai/list_peserta.html',
        event=event,
        participants=participants,
        sidebar_state=sidebar_state
    )

@app.route('/penilai/event/<int:event_id>/grade/<int:participant_id>', methods=['GET', 'POST'])
@login_required
def penilai_input_score(event_id, participant_id):
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    participant_user = Users.query.get_or_404(participant_id)
    participant_biodata = Participants.query.filter_by(email=participant_user.email).first()
    
    # If no biodata exists, create a temporary object with user data
    if not participant_biodata:
        # Create a simple object to hold the necessary data
        class ParticipantData:
            def __init__(self, user):
                self.id = user.id
                self.nama_lengkap = user.nama_lengkap or user.username
                self.email = user.email
                self.asal_gudep = ''
                self.golongan = 'N/A'
                self.tingkatan = 'N/A'
                self.usia = user.usia or '0'
                self.foto = user.foto or 'img/default-user.png'
        
        participant_biodata = ParticipantData(participant_user)
    
    # Ambil kriteria untuk event ini
    # Filter berdasarkan penugasan
    user_assigned_criteria = [c for c in current_user.assigned_criteria if c.event_id == event_id]
    
    if user_assigned_criteria:
        criterias = user_assigned_criteria
    else:
        # Fallback: jika tidak ada assignment spesifik (legacy), tampilkan semua
        criterias = Criteria.query.filter_by(event_id=event_id).all()
    
    # Ambil himpunan kriteria untuk dropdown
    for c in criterias:
        c.himpunan = HimpunanKriteria.query.filter_by(id_kriteria=c.id_kriteria).all()
        
    # Ambil nilai yang sudah ada (jika edit)
    existing_scores = {}
    scores_query = Penilaian.query.filter_by(
        id_users=participant_id,
        evaluator_id=current_user.id
    ).all()
    for s in scores_query:
        existing_scores[s.id_kriteria] = s.nilai

    if request.method == 'POST':
        try:
            # DEBUG LOGGING
            with open('debug_scores.log', 'a') as f:
                f.write(f"\n--- SAVING SCORES ---\n")
                f.write(f"Participant ID (from route): {participant_id}\n")
                f.write(f"Participant User ID: {participant_user.id}\n")
                f.write(f"Evaluator ID: {current_user.id}\n")
                f.write(f"Event ID: {event_id}\n")
            
            for criteria in criterias:
                score_val = request.form.get(f'score_{criteria.id_kriteria}')
                if score_val:
                    # Cek apakah update atau insert
                    penilaian = Penilaian.query.filter_by(
                        id_users=participant_id,
                        evaluator_id=current_user.id,
                        id_kriteria=criteria.id_kriteria
                    ).first()
                    
                    if penilaian:
                        penilaian.nilai = float(score_val)
                    else:
                        penilaian = Penilaian(
                            id_users=participant_id,
                            evaluator_id=current_user.id,
                            id_kriteria=criteria.id_kriteria,
                            nilai=float(score_val)
                        )
                        db.session.add(penilaian)
                    
                    # DEBUG: Log what we're saving
                    with open('debug_scores.log', 'a') as f:
                        f.write(f"Saving: Criteria {criteria.id_kriteria}, Score {score_val}, id_users={participant_id}\n")
            
            db.session.commit()
            flash("Penilaian berhasil disimpan!", "success")
            return redirect(url_for('penilai_event_participants', event_id=event_id))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error saving score: {e}")
            flash("Terjadi kesalahan saat menyimpan nilai.", "danger")

    sidebar_state = current_user.sidebar_state or 'expanded'

    return render_template(
        'penilai/form_penilaian.html',
        event=event,
        participant=participant_biodata,
        participant_user=participant_user,
        criterias=criterias,
        existing_scores=existing_scores,
        sidebar_state=sidebar_state
    )

@app.route('/penilai/event/<int:event_id>/view/<int:participant_id>')
@login_required
def penilai_view_score(event_id, participant_id):
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    event = Event.query.get_or_404(event_id)
    participant_user = Users.query.get_or_404(participant_id)
    participant_biodata = Participants.query.filter_by(email=participant_user.email).first()
    
    # If no biodata exists, create a temporary object with user data
    if not participant_biodata:
        class ParticipantData:
            def __init__(self, user):
                self.id = user.id
                self.nama_lengkap = user.nama_lengkap or user.username
                self.email = user.email
                self.asal_gudep = ''
                self.golongan = 'N/A'
                self.tingkatan = 'N/A'
                self.usia = user.usia or '0'
                self.foto = user.foto or 'img/default-user.png'
        
        participant_biodata = ParticipantData(participant_user)
    
    # Ambil SEMUA kriteria untuk event ini
    all_criterias = Criteria.query.filter_by(event_id=event_id).all()
    
    # Identifikasi kriteria yang ditugaskan ke user ini
    assigned_criteria_ids = [c.id_kriteria for c in current_user.assigned_criteria if c.event_id == event_id]
    
    # Ambil himpunan kriteria untuk dropdown
    for c in all_criterias:
        c.himpunan = HimpunanKriteria.query.filter_by(id_kriteria=c.id_kriteria).all()
        
    # Ambil SEMUA nilai yang sudah ada untuk peserta ini (dari penilai manapun)
    existing_scores = {}
    scores_query = Penilaian.query.filter_by(
        id_users=participant_id
    ).all()
    
    # Mapping nilai: Prioritaskan nilai dari current_user jika ada, jika tidak pakai nilai orang lain
    # (Dalam sistem ideal, mungkin kita ingin menampilkan siapa yang menilai, tapi untuk sekarang kita ambil nilai 'terbaru' atau 'milik sendiri')
    for s in scores_query:
        # Jika belum ada di map, masukkan
        if s.id_kriteria not in existing_scores:
            existing_scores[s.id_kriteria] = s.nilai
        # Jika sudah ada, tapi ini punya current_user, timpa (karena kita ingin lihat nilai kita sendiri jika ada)
        elif s.evaluator_id == current_user.id:
            existing_scores[s.id_kriteria] = s.nilai
            
    # DEBUG LOGGING TO FILE
    with open('debug_scores.log', 'a') as f:
        f.write(f"\n--- DEBUG: Viewing scores for Event {event_id}, Participant {participant_id} ---\n")
        f.write(f"Found {len(all_criterias)} criteria\n")
        f.write(f"Found {len(scores_query)} raw scores\n")
        f.write(f"Existing Scores Map: {existing_scores}\n")
        for c in all_criterias:
            f.write(f"Criteria {c.id_kriteria} ({c.nama_kriteria}) - Score: {existing_scores.get(c.id_kriteria)}\n")

    sidebar_state = current_user.sidebar_state or 'expanded'

    return render_template(
        'penilai/view_penilaian.html',
        event=event,
        participant=participant_biodata,
        participant_user=participant_user,
        criterias=all_criterias,
        assigned_criteria_ids=assigned_criteria_ids,
        existing_scores=existing_scores,
        sidebar_state=sidebar_state
    )

@app.route('/penilai/biodata', methods=['GET', 'POST'])
@login_required
def penilai_biodata():
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            nama_lengkap = request.form.get('nama_lengkap', '').strip()
            usia = request.form.get('usia', '0').strip()
            jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
            nomor_hp = request.form.get('nomor_hp', '').strip()
            
            # Update Users table
            current_user.nama_lengkap = nama_lengkap
            current_user.usia = usia
            current_user.jenis_kelamin = jenis_kelamin
            current_user.nomor_hp = nomor_hp
            
            # Handle photo upload if any
            if 'foto' in request.files:
                file = request.files['foto']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Rename file to avoid conflict
                    ext = filename.rsplit('.', 1)[1].lower()
                    new_filename = f"{current_user.username}_{int(time.time())}.{ext}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    current_user.foto = f"img/{new_filename}"
            
            db.session.commit()
            flash("Data profil berhasil diperbarui!", "success")
            return redirect(url_for('penilai_biodata'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating evaluator data: {e}")
            flash("Terjadi kesalahan saat menyimpan data.", "danger")
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'penilai/biodata.html',
        sidebar_state=sidebar_state,
        user=current_user
    )

@app.route('/penilai/hasil-penilaian')
@login_required
def penilai_hasil_penilaian():
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    # Get all assigned events
    assigned_events = Event.query.filter(Event.evaluators.any(id=current_user.id)).all()
    
    # Get selected event from query parameter
    selected_event_id = request.args.get('event_id', type=int)
    selected_event = None
    results = []
    
    if selected_event_id:
        # Verify the event is assigned to this evaluator
        selected_event = Event.query.get(selected_event_id)
        if selected_event and selected_event in assigned_events:
            from app.fuzzy_ahp import calculate_spk
            
            # Calculate SPK for this event
            success, msg = calculate_spk(selected_event_id)
            if not success:
                logging.warning(f"Gagal hitung SPK untuk event {selected_event_id}: {msg}")
            
            # Fetch results for this event only
            hasil_seleksi = db.session.query(
                HasilSeleksi,
                Users,
                Participants
            ).join(
                Users, HasilSeleksi.id_users == Users.id
            ).outerjoin(
                Participants, Users.email == Participants.email
            ).filter(
                HasilSeleksi.event_id == selected_event_id
            ).order_by(
                HasilSeleksi.ranking.asc()
            ).all()
            
            # Build results list
            for hasil, user, participant in hasil_seleksi:
                results.append({
                    'hasil': hasil,
                    'user': user,
                    'participant': participant
                })
        else:
            flash("Kegiatan tidak ditemukan atau Anda tidak memiliki akses.", "error")
            selected_event = None

    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'penilai/hasil_penilaian.html',
        assigned_events=assigned_events,
        selected_event=selected_event,
        results=results,
        sidebar_state=sidebar_state
    )

@app.route('/penilai/detail-nilai/<int:user_id>/<int:event_id>')
@login_required
def penilai_detail_nilai(user_id, event_id):
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    # Verify event is assigned to this evaluator
    event = Event.query.get_or_404(event_id)
    if current_user not in event.evaluators:
        flash("Anda tidak memiliki akses ke kegiatan ini.", "error")
        return redirect(url_for('penilai_hasil_penilaian'))
    
    # Get participant info
    user = Users.query.get_or_404(user_id)
    participant = Participants.query.filter_by(email=user.email).first()
    
    # Get final result
    hasil_seleksi = HasilSeleksi.query.filter_by(
        id_users=user_id,
        event_id=event_id
    ).first()
    
    # Get all criteria for this event
    criterias = Criteria.query.filter_by(event_id=event_id).all()
    
    # Calculate total weight
    total_bobot = sum(c.bobot for c in criterias)
    
    # Get all scores and calculate breakdown
    calculation_details = []
    fuzzy_total_l = 0
    fuzzy_total_m = 0
    fuzzy_total_u = 0
    
    for criteria in criterias:
        # Normalized weight
        weight = (criteria.bobot / total_bobot) if total_bobot > 0 else 0
        
        # Get average score from all evaluators
        avg_score = db.session.query(db.func.avg(Penilaian.nilai)).filter_by(
            id_users=user_id,
            id_kriteria=criteria.id_kriteria
        ).scalar()
        
        if avg_score is not None:
            score = float(avg_score)
            
            # Fuzzification logic (same as fuzzy_ahp.py)
            if score <= 5:  # Likert scale
                if score <= 1:
                    l, m, u = 1, 1, 2
                elif score <= 2:
                    l, m, u = 1, 2, 3
                elif score <= 3:
                    l, m, u = 2, 3, 4
                elif score <= 4:
                    l, m, u = 3, 4, 5
                else:
                    l, m, u = 4, 5, 5
            else:  # 0-100 scale
                l = max(0, score - 5)
                m = score
                u = min(100, score + 5)
            
            # Weighted fuzzy values
            weighted_l = l * weight
            weighted_m = m * weight
            weighted_u = u * weight
            
            # Accumulate totals
            fuzzy_total_l += weighted_l
            fuzzy_total_m += weighted_m
            fuzzy_total_u += weighted_u
            
            calculation_details.append({
                'criteria': criteria,
                'weight': weight,
                'raw_score': score,
                'fuzzy_l': l,
                'fuzzy_m': m,
                'fuzzy_u': u,
                'weighted_l': weighted_l,
                'weighted_m': weighted_m,
                'weighted_u': weighted_u
            })
    
    # Final defuzzified score
    final_score = (fuzzy_total_l + fuzzy_total_m + fuzzy_total_u) / 3 if calculation_details else 0
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'penilai/detail_nilai.html',
        user=user,
        participant=participant,
        event=event,
        hasil_seleksi=hasil_seleksi,
        calculation_details=calculation_details,
        fuzzy_total_l=fuzzy_total_l,
        fuzzy_total_m=fuzzy_total_m,
        fuzzy_total_u=fuzzy_total_u,
        final_score=final_score,
        sidebar_state=sidebar_state
    )


@app.route('/admin/hasil-penilaian')
@login_required
@admin_required
def admin_hasil_penilaian():
    # Get all events
    all_events = Event.query.order_by(Event.waktu_pelaksanaan_dimulai.desc()).all()
    
    # Get selected event from query parameter
    selected_event_id = request.args.get('event_id', type=int)
    selected_event = None
    results = []
    
    if selected_event_id:
        selected_event = Event.query.get(selected_event_id)
        if selected_event:
            from app.fuzzy_ahp import calculate_spk
            
            # Calculate SPK for this event
            success, msg = calculate_spk(selected_event_id)
            if not success:
                logging.warning(f"Gagal hitung SPK untuk event {selected_event_id}: {msg}")
            
            # Fetch results for this event only
            hasil_seleksi = db.session.query(
                HasilSeleksi,
                Users,
                Participants
            ).join(
                Users, HasilSeleksi.id_users == Users.id
            ).outerjoin(
                Participants, Users.email == Participants.email
            ).filter(
                HasilSeleksi.event_id == selected_event_id
            ).order_by(
                HasilSeleksi.ranking.asc()
            ).all()
            
            # Build results list
            for hasil, user, participant in hasil_seleksi:
                results.append({
                    'hasil': hasil,
                    'user': user,
                    'participant': participant
                })
        else:
            flash("Kegiatan tidak ditemukan.", "error")
            selected_event = None

    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'admin/hasil_penilaian.html',
        assigned_events=all_events,
        selected_event=selected_event,
        results=results,
        sidebar_state=sidebar_state
    )

@app.route('/admin/detail-nilai/<int:user_id>/<int:event_id>')
@login_required
@admin_required
def admin_detail_nilai(user_id, event_id):
    # Get event
    event = Event.query.get_or_404(event_id)
    
    # Get participant info
    user = Users.query.get_or_404(user_id)
    participant = Participants.query.filter_by(email=user.email).first()
    
    # Get final result
    hasil_seleksi = HasilSeleksi.query.filter_by(
        id_users=user_id,
        event_id=event_id
    ).first()
    
    # Get all criteria for this event
    criterias = Criteria.query.filter_by(event_id=event_id).all()
    
    # Calculate total weight
    total_bobot = sum(c.bobot for c in criterias)
    
    # Get all scores and calculate breakdown
    calculation_details = []
    fuzzy_total_l = 0
    fuzzy_total_m = 0
    fuzzy_total_u = 0
    
    for criteria in criterias:
        # Normalized weight
        weight = (criteria.bobot / total_bobot) if total_bobot > 0 else 0
        
        # Get average score from all evaluators
        avg_score = db.session.query(db.func.avg(Penilaian.nilai)).filter_by(
            id_users=user_id,
            id_kriteria=criteria.id_kriteria
        ).scalar()
        
        if avg_score is not None:
            score = float(avg_score)
            
            # Fuzzification logic (same as fuzzy_ahp.py)
            if score <= 5:  # Likert scale
                if score <= 1:
                    l, m, u = 1, 1, 2
                elif score <= 2:
                    l, m, u = 1, 2, 3
                elif score <= 3:
                    l, m, u = 2, 3, 4
                elif score <= 4:
                    l, m, u = 3, 4, 5
                else:
                    l, m, u = 4, 5, 5
            else:  # 0-100 scale
                l = max(0, score - 5)
                m = score
                u = min(100, score + 5)
            
            # Weighted fuzzy values
            weighted_l = l * weight
            weighted_m = m * weight
            weighted_u = u * weight
            
            # Accumulate totals
            fuzzy_total_l += weighted_l
            fuzzy_total_m += weighted_m
            fuzzy_total_u += weighted_u
            
            calculation_details.append({
                'criteria': criteria,
                'weight': weight,
                'raw_score': score,
                'fuzzy_l': l,
                'fuzzy_m': m,
                'fuzzy_u': u,
                'weighted_l': weighted_l,
                'weighted_m': weighted_m,
                'weighted_u': weighted_u
            })
    
    # Final defuzzified score
    final_score = (fuzzy_total_l + fuzzy_total_m + fuzzy_total_u) / 3 if calculation_details else 0
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'admin/detail_nilai.html',
        user=user,
        participant=participant,
        event=event,
        hasil_seleksi=hasil_seleksi,
        calculation_details=calculation_details,
        fuzzy_total_l=fuzzy_total_l,
        fuzzy_total_m=fuzzy_total_m,
        fuzzy_total_u=fuzzy_total_u,
        final_score=final_score,
        sidebar_state=sidebar_state
    )


@app.route('/penilai/hasil-seleksi')
@login_required
def penilai_hasil_seleksi():
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    # Get all assigned events
    assigned_events = Event.query.filter(Event.evaluators.any(id=current_user.id)).all()
    
    # Get selected event from query parameter
    selected_event_id = request.args.get('event_id', type=int)
    selected_event = None
    results = []
    
    if selected_event_id:
        # Verify the event is assigned to this evaluator
        selected_event = Event.query.get(selected_event_id)
        if selected_event and selected_event in assigned_events:
            # Fetch results for this event only
            # Join with Participants to get gender (for quota check if needed in template)
            hasil_seleksi_query = db.session.query(
                HasilSeleksi,
                Users,
                Participants
            ).join(
                Users, HasilSeleksi.id_users == Users.id
            ).outerjoin(
                Participants, Users.email == Participants.email
            ).filter(
                HasilSeleksi.event_id == selected_event_id
            ).order_by(
                HasilSeleksi.ranking.asc()
            ).all()
            
            # Process results to include passing status logic explicitly if needed
            # Although template can do it, it's good to have it ready.
            # Using simple query logic for now.
            
            kuota = Kuota.query.filter_by(event_id=selected_event_id).first()
            
            for hasil, user, participant in hasil_seleksi_query:
                results.append({
                    'hasil': hasil,
                    'user': user,
                    'participant': participant
                })
        else:
            flash("Kegiatan tidak ditemukan atau Anda tidak memiliki akses.", "error")
            selected_event = None
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'penilai/hasil_seleksi.html',
        assigned_events=assigned_events,
        selected_event=selected_event,
        results=results,
        sidebar_state=sidebar_state
    )

@app.route('/penilai/notifikasi')
@login_required
def penilai_notifikasi():
    if current_user.level != 'penilai':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    # Get notifications for this evaluator
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'penilai/notifikasi.html',
        notifications=notifications,
        sidebar_state=sidebar_state
    )

@app.route('/peserta/dashboard')
@login_required
def peserta_dashboard():
    """Dashboard for participants showing scores and rankings for all registered activities"""
    
    if current_user.level != 'peserta':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    # Get current user's participant record
    participant = Participants.query.filter_by(email=current_user.email).first()
    
    # Get all registered activities for this participant
    registered_activities = []
    if participant:
        registered_activities = Event.query.join(
            tb_participant_kegiatan,
            Event.id_kegiatan == tb_participant_kegiatan.c.kegiatan_id
        ).filter(
            tb_participant_kegiatan.c.participant_id == participant.id
        ).all()
    
    # Calculate scores for each activity
    activity_scores = []
    for event in registered_activities:
        # Get all criteria for this event
        criteria_list = Criteria.query.filter_by(event_id=event.id_kegiatan).all()
        
        # Calculate total score
        total_score = 0
        has_scores = False
        
        for criterion in criteria_list:
            penilaian = Penilaian.query.filter_by(
                id_users=current_user.id,
                id_kriteria=criterion.id_kriteria
            ).first()
            
            if penilaian:
                # Calculate weighted score
                weighted_score = penilaian.nilai * (criterion.bobot / 100)
                total_score += weighted_score
                has_scores = True
        
        # Get ranking from HasilSeleksi table
        hasil = HasilSeleksi.query.filter_by(
            id_users=current_user.id,
            event_id=event.id_kegiatan
        ).first()
        
        activity_scores.append({
            'event': event,
            'final_score': round(total_score, 2) if has_scores else None,
            'ranking': hasil.ranking if hasil else None,
            'has_scores': has_scores
        })
    
    # Check if any selection period has ended
    is_selection_ended = any(
        event.selesai and event.selesai < date.today()
        for event in registered_activities
    )
    
    # Determine status
    status_seleksi = 'Terdaftar' if registered_activities else 'Belum ada status'
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    
    return render_template(
        'peserta/dashboard.html',
        biodata=participant,
        registered_activities=registered_activities,
        activity_scores=activity_scores,
        is_selection_ended=is_selection_ended,
        status_seleksi=status_seleksi,
        user=current_user,
        sidebar_state=sidebar_state,
        today=date.today()
    )

@app.route('/peserta/notifikasi')
@login_required
def peserta_notifikasi():
    if current_user.level != 'peserta':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.id.desc()).all()
    
    return render_template(
        'peserta/notifikasi.html',
        notifications=notifications,
        sidebar_state=sidebar_state,
        user=current_user
    )

@app.route('/peserta/hasil_seleksi')
@login_required
def peserta_hasil_seleksi():
    if current_user.level != 'peserta':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    biodata = Participants.query.filter_by(email=current_user.email).first()
    
    results_data = []
    
    if biodata:
        # Get all registered activities via the many-to-many relationship
        # Assuming biodata.registered_activities is the relationship to Event
        registered_activities = biodata.registered_activities.all()
        
        for event in registered_activities:
            # Check for existing result
            hasil = HasilSeleksi.query.filter_by(
                id_users=current_user.id,
                event_id=event.id_kegiatan
            ).first()
            
            status_text = "Dalam Proses"
            temp_score = 0
            has_temp_score = False
            
            if hasil:
                    status_text = "Selesai"
            else:
                # If no final result, calculate temporary score from Penilaian
                criteria_list = Criteria.query.filter_by(event_id=event.id_kegiatan).all()
                current_score = 0
                count_rated = 0
                
                # Check directly in Penilaian table
                # We need to sum (nilai * bobot) / 100 or similar based on formula
                # Using simple weighted sum for display
                # Note: This is an approximation if the final formula is Fuzzy AHP
                # But good enough for "Temporary Score"
                
                # Retrieve all ratings for this user and event criterias
                if criteria_list:
                    criteria_ids = [c.id_kriteria for c in criteria_list]
                    ratings = Penilaian.query.filter(
                        Penilaian.id_users == current_user.id,
                        Penilaian.id_kriteria.in_(criteria_ids)
                    ).all()
                    
                    rating_map = {r.id_kriteria: r.nilai for r in ratings}
                    
                    total_bobot = sum(c.bobot for c in criteria_list)
                    
                    if ratings:
                         has_temp_score = True
                         for c in criteria_list:
                             if c.id_kriteria in rating_map:
                                 # Normalize weight usually happens in calculation, 
                                 # here we assume simple weighted sum: value * (bobot/total_bobot)
                                 # or just value * bobot if bobot is percentage.
                                 # Let's align with dashboard logic: weighted_score = nilai * (bobot / 100)
                                 # Assuming bobot is 0-100.
                                 if total_bobot > 0:
                                     val = rating_map[c.id_kriteria]
                                     # Simple weighted average 
                                     # (value * weight) / total_weight
                                     # This keeps result in same scale as value (e.g. 1-100)
                                     current_score += val * (c.bobot / total_bobot)

                    temp_score = current_score

            results_data.append({
                'event': event,
                'hasil': hasil,
                'status_text': status_text,
                'temp_score': temp_score,
                'has_temp_score': has_temp_score
            })

    return render_template(
        'peserta/hasil_seleksi.html',
        results_data=results_data,
        biodata=biodata,
        sidebar_state=sidebar_state,
        user=current_user
    )

@app.route('/peserta/hasil_seleksi/<int:event_id>')
@login_required
def peserta_detail_nilai(event_id):
    """Halaman detail nilai semua peserta untuk kegiatan tertentu"""
    if current_user.level != 'peserta':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))
    
    # Verify that the current user is registered for this event
    biodata = Participants.query.filter_by(email=current_user.email).first()
    if not biodata:
        flash("Data peserta tidak ditemukan.", "error")
        return redirect(url_for('peserta_hasil_seleksi'))
    
    # Check if user is registered for this event
    event = Event.query.get_or_404(event_id)
    if event not in biodata.registered_activities.all():
        flash("Anda tidak terdaftar untuk kegiatan ini.", "error")
        return redirect(url_for('peserta_hasil_seleksi'))
    
    # Get all results for this event, ordered by ranking
    hasil_seleksi_query = db.session.query(
        HasilSeleksi,
        Users,
        Participants
    ).join(
        Users, HasilSeleksi.id_users == Users.id
    ).outerjoin(
        Participants, Users.email == Participants.email
    ).filter(
        HasilSeleksi.event_id == event_id
    ).order_by(
        HasilSeleksi.ranking.asc()
    ).all()
    
    # Process results
    results = []
    kuota = Kuota.query.filter_by(event_id=event_id).first()
    
    for hasil, user, participant in hasil_seleksi_query:
        results.append({
            'hasil': hasil,
            'user': user,
            'participant': participant
        })
    
    sidebar_state = current_user.sidebar_state or 'expanded'
    return render_template(
        'peserta/detail_nilai.html',
        event=event,
        results=results,
        kuota=kuota,
        sidebar_state=sidebar_state,
        user=current_user,
        biodata=biodata
    )

@app.route('/peserta/data', methods=['GET', 'POST'])
@login_required
def peserta_data():
    if current_user.level != 'peserta':
        flash("Anda tidak memiliki akses ke halaman ini.", "error")
        return redirect(url_for('index'))

    # Ambil data biodata
    biodata = Participants.query.filter_by(email=current_user.email).first()
    
    if request.method == 'POST':
        try:
            nama_lengkap = request.form.get('nama_lengkap', '').strip()
            tanggal_lahir = request.form.get('tanggal_lahir', '').strip()
            alamat_tinggal = request.form.get('alamat_tinggal', '').strip()
            golongan = request.form.get('golongan', '').strip()
            tingkatan = request.form.get('tingkatan', '').strip()
            asal_gudep = request.form.get('asal_gudep', '').strip()
            asal_kwarran = request.form.get('asal_kwarran', '').strip()
            asal_kwarcab = request.form.get('asal_kwarcab', '').strip()
            asal_kwarda = request.form.get('asal_kwarda', '').strip()
            usia = request.form.get('usia', '0').strip()
            jenis_kelamin = request.form.get('jenis_kelamin', '').strip()
            nomor_hp = request.form.get('nomor_hp', '').strip()
            
            # Update Users table
            current_user.nama_lengkap = nama_lengkap
            current_user.usia = usia
            current_user.jenis_kelamin = jenis_kelamin
            current_user.nomor_hp = nomor_hp
            
            # Handle photo upload if any
            if 'foto' in request.files:
                file = request.files['foto']
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Rename file to avoid conflict
                    ext = filename.rsplit('.', 1)[1].lower()
                    new_filename = f"{current_user.username}_{int(time.time())}.{ext}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], new_filename))
                    current_user.foto = f"uploads/{new_filename}"
                    if biodata:
                        biodata.foto = f"uploads/{new_filename}"

            if not biodata:
                # Create new biodata
                biodata = Participants(
                    nama_lengkap=nama_lengkap,
                    email=current_user.email,
                    tanggal_lahir=datetime.strptime(tanggal_lahir, '%Y-%m-%d').date() if tanggal_lahir else datetime.now().date(),
                    alamat_tinggal=alamat_tinggal,
                    golongan=golongan,
                    tingkatan=tingkatan,
                    asal_gudep=asal_gudep,
                    asal_kwarran=asal_kwarran,
                    asal_kwarcab=asal_kwarcab,
                    asal_kwarda=asal_kwarda,
                    usia=int(usia) if usia.isdigit() else 0,
                    jenis_kelamin=jenis_kelamin,
                    nomor_hp=nomor_hp,
                    foto=current_user.foto,
                    level='peserta'
                )
                db.session.add(biodata)
            else:
                # Update existing biodata
                biodata.nama_lengkap = nama_lengkap
                if tanggal_lahir:
                    biodata.tanggal_lahir = datetime.strptime(tanggal_lahir, '%Y-%m-%d').date()
                biodata.alamat_tinggal = alamat_tinggal
                biodata.golongan = golongan
                biodata.tingkatan = tingkatan
                biodata.asal_gudep = asal_gudep
                biodata.asal_kwarran = asal_kwarran
                biodata.asal_kwarcab = asal_kwarcab
                biodata.asal_kwarda = asal_kwarda
                biodata.usia = int(usia) if usia.isdigit() else 0
                biodata.jenis_kelamin = jenis_kelamin
                biodata.nomor_hp = nomor_hp
            
            db.session.commit()
            flash("Data peserta berhasil diperbarui!", "success")
            return redirect(url_for('peserta_data'))
            
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating participant data: {e}")
            flash("Terjadi kesalahan saat menyimpan data.", "danger")

    # Check completeness
    is_complete = False
    missing_fields = []
    if biodata:
        required_fields = [
            'nama_lengkap', 'tanggal_lahir', 'alamat_tinggal', 'golongan', 
            'tingkatan', 'asal_gudep', 'asal_kwarran', 'asal_kwarcab', 
            'asal_kwarda', 'usia', 'jenis_kelamin', 'nomor_hp'
        ]
        for field in required_fields:
            val = getattr(biodata, field)
            if not val or val == '' or val == 0:
                missing_fields.append(field)
        
        if not missing_fields:
            is_complete = True
    else:
        missing_fields = ['All Data']

    sidebar_state = current_user.sidebar_state or 'expanded'
    
    return render_template(
        'peserta/data_peserta.html',
        biodata=biodata,
        user=current_user,
        sidebar_state=sidebar_state,
        is_complete=is_complete,
        missing_fields=missing_fields
    )

# API untuk mendapatkan kegiatan/seleksi yang tersedia (sedang dibuka)
@app.route('/api/kegiatan_tersedia')
@login_required
def api_kegiatan_tersedia():
    """Mengembalikan daftar kegiatan yang sedang membuka seleksi (tanggal sekarang antara mulai dan selesai)"""
    try:
        if current_user.level != 'peserta':
            return jsonify({'status': 'error', 'message': 'Akses ditolak'}), 403
        
        today = datetime.utcnow().date()
        
        # Ambil kegiatan yang sedang membuka seleksi (tanggal sekarang antara mulai dan selesai)
        kegiatan_list = Event.query.filter(
            Event.mulai <= today,
            Event.selesai >= today
        ).order_by(Event.mulai.desc()).all()
        
        # Ambil biodata peserta untuk cek apakah sudah terdaftar
        biodata = Participants.query.filter_by(email=current_user.email).first()
        peserta_kegiatan_ids = []
        if biodata:
            # Get all registered activities from many-to-many relationship
            peserta_kegiatan_ids = [k.id_kegiatan for k in biodata.registered_activities.all()]
        
        result = []
        for kegiatan in kegiatan_list:
            kuota = Kuota.query.filter_by(event_id=kegiatan.id_kegiatan).first()
            
            # Hitung jumlah peserta yang sudah terdaftar
            peserta_terdaftar = kegiatan.registered_participants.count()
            peserta_putra = kegiatan.registered_participants.filter(Participants.jenis_kelamin == 'laki-laki').count()
            peserta_putri = kegiatan.registered_participants.filter(Participants.jenis_kelamin == 'perempuan').count()
            
            # Cek apakah peserta sudah terdaftar di kegiatan ini
            sudah_terdaftar = kegiatan.id_kegiatan in peserta_kegiatan_ids
            
            result.append({
                'id_kegiatan': kegiatan.id_kegiatan,
                'nama_kegiatan': kegiatan.nama_kegiatan,
                'jenis_kegiatan': kegiatan.jenis_kegiatan,
                'skala_kegiatan': kegiatan.skala_kegiatan,
                'kwartir_penyelenggara': kegiatan.kwartir_penyelenggara,
                'tempat_pelaksanaan': kegiatan.tempat_pelaksanaan,
                'waktu_pelaksanaan_dimulai': kegiatan.waktu_pelaksanaan_dimulai.strftime('%Y-%m-%d') if kegiatan.waktu_pelaksanaan_dimulai else None,
                'waktu_pelaksanaan_selesai': kegiatan.waktu_pelaksanaan_selesai.strftime('%Y-%m-%d') if kegiatan.waktu_pelaksanaan_selesai else None,
                'periode_seleksi_mulai': kegiatan.mulai.strftime('%Y-%m-%d') if kegiatan.mulai else None,
                'periode_seleksi_selesai': kegiatan.selesai.strftime('%Y-%m-%d') if kegiatan.selesai else None,
                'kuota_putra': kuota.putra if kuota else 0,
                'kuota_putri': kuota.putri if kuota else 0,
                'peserta_terdaftar': peserta_terdaftar,
                'peserta_putra_terdaftar': peserta_putra,
                'peserta_putri_terdaftar': peserta_putri,
                'sisa_kuota_putra': (kuota.putra if kuota else 0) - peserta_putra,
                'sisa_kuota_putri': (kuota.putri if kuota else 0) - peserta_putri,
                'sudah_terdaftar': sudah_terdaftar,
                'status': 'Terdaftar' if sudah_terdaftar else 'Tersedia'
            })
        
        return jsonify({'status': 'success', 'data': result}), 200
    except Exception as e:
        current_app.logger.exception('Error in /api/kegiatan_tersedia:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API untuk peserta mendaftar/bergabung ke seleksi
@app.route('/api/daftar_seleksi', methods=['POST'])
@login_required
@csrf.exempt
def api_daftar_seleksi():
    """Endpoint untuk peserta mendaftar ke seleksi kegiatan"""
    try:
        if current_user.level != 'peserta':
            return jsonify({'status': 'error', 'message': 'Akses ditolak'}), 403
        
        data = request.get_json(force=True)
        kegiatan_id = data.get('kegiatan_id')
        
        if not kegiatan_id:
            return jsonify({'status': 'error', 'message': 'ID kegiatan tidak ditemukan'}), 400
        
        # Cek apakah kegiatan ada dan sedang membuka seleksi
        kegiatan = Event.query.get(kegiatan_id)
        if not kegiatan:
            return jsonify({'status': 'error', 'message': 'Kegiatan tidak ditemukan'}), 404
        
        today = datetime.utcnow().date()
        if today < kegiatan.mulai or today > kegiatan.selesai:
            return jsonify({
                'status': 'error', 
                'message': 'Pendaftaran seleksi untuk kegiatan ini belum dibuka atau sudah ditutup'
            }), 400
        
        # Cek apakah peserta sudah punya biodata
        biodata = Participants.query.filter_by(email=current_user.email).first()
        if not biodata:
            return jsonify({
                'status': 'error', 
                'message': 'Biodata Anda belum terdaftar. Silakan hubungi administrator untuk mendaftarkan biodata.'
            }), 400
        
        # Cek apakah sudah terdaftar di kegiatan yang sama
        if kegiatan in biodata.registered_activities.all():
            return jsonify({
                'status': 'error', 
                'message': 'Anda sudah terdaftar di kegiatan ini'
            }), 400
        
        # Cek kuota
        kuota = Kuota.query.filter_by(event_id=kegiatan_id).first()
        if kuota:
            peserta_putra = kegiatan.registered_participants.filter(Participants.jenis_kelamin == 'laki-laki').count()
            peserta_putri = kegiatan.registered_participants.filter(Participants.jenis_kelamin == 'perempuan').count()
            
            if biodata.jenis_kelamin == 'laki-laki' and peserta_putra >= kuota.putra:
                return jsonify({
                    'status': 'error', 
                    'message': 'Kuota untuk peserta putra sudah penuh'
                }), 400
            elif biodata.jenis_kelamin == 'perempuan' and peserta_putri >= kuota.putri:
                return jsonify({
                    'status': 'error', 
                    'message': 'Kuota untuk peserta putri sudah penuh'
                }), 400
        
        # Daftarkan peserta ke kegiatan menggunakan many-to-many relationship
        biodata.registered_activities.append(kegiatan)
        db.session.commit()
        
        # Log aktivitas
        log_activity(
            current_user.id,
            f'Mendaftar ke seleksi kegiatan: {kegiatan.nama_kegiatan}'
        )
        
        return jsonify({
            'status': 'success', 
            'message': f'Berhasil mendaftar ke seleksi kegiatan: {kegiatan.nama_kegiatan}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in /api/daftar_seleksi:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API untuk peserta membatalkan pendaftaran seleksi
@app.route('/api/batal_daftar_seleksi', methods=['POST'])
@login_required
@csrf.exempt
def api_batal_daftar_seleksi():
    """Endpoint untuk peserta membatalkan pendaftaran ke seleksi kegiatan"""
    try:
        if current_user.level != 'peserta':
            return jsonify({'status': 'error', 'message': 'Akses ditolak'}), 403
        
        data = request.get_json(force=True)
        kegiatan_id = data.get('kegiatan_id')
        
        if not kegiatan_id:
            return jsonify({'status': 'error', 'message': 'ID kegiatan tidak ditemukan'}), 400
        
        # Cek apakah kegiatan ada
        kegiatan = Event.query.get(kegiatan_id)
        if not kegiatan:
            return jsonify({'status': 'error', 'message': 'Kegiatan tidak ditemukan'}), 404
        
        # Cek apakah peserta sudah punya biodata
        biodata = Participants.query.filter_by(email=current_user.email).first()
        if not biodata:
            return jsonify({
                'status': 'error', 
                'message': 'Biodata Anda belum terdaftar. Silakan hubungi administrator untuk mendaftarkan biodata.'
            }), 400
        
        # Cek apakah peserta terdaftar di kegiatan ini
        if kegiatan not in biodata.registered_activities.all():
            return jsonify({
                'status': 'error', 
                'message': 'Anda belum terdaftar di kegiatan ini'
            }), 400
        
        # Cek apakah sudah ada hasil seleksi (jika sudah ada hasil seleksi, tidak bisa dibatalkan)
        hasil_seleksi = HasilSeleksi.query.filter_by(id_users=current_user.id).first()
        if hasil_seleksi:
            return jsonify({
                'status': 'error', 
                'message': 'Tidak dapat membatalkan pendaftaran karena seleksi sudah selesai'
            }), 400
        
        # Batalkan pendaftaran (remove from many-to-many relationship)
        biodata.registered_activities.remove(kegiatan)
        db.session.commit()
        
        # Log aktivitas
        log_activity(
            current_user.id,
            f'Membatalkan pendaftaran seleksi kegiatan: {kegiatan.nama_kegiatan}'
        )
        
        return jsonify({
            'status': 'success', 
            'message': f'Berhasil membatalkan pendaftaran ke seleksi kegiatan: {kegiatan.nama_kegiatan}'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception('Error in /api/batal_daftar_seleksi:')
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/logout/')
def logout():
    session.clear()
    session.pop('username', None)
    flash("Anda telah logout.", "info")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
 