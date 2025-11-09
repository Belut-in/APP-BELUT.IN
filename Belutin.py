from flask import Flask, render_template_string, request, redirect, session
from supabase import create_client, Client
from dotenv import load_dotenv
from email.message import EmailMessage
import smtplib, ssl, random, os

# ---------------------------
# KONFIGURASI DASAR
# ---------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# KONFIGURASI EMAIL GMAIL
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ---------------------------
# TEMPLATE HTML + CSS
# ---------------------------

login_page = """
<!doctype html>
<html>
<head>
    <title>BELUT.IN — Login</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #004080, #1e90ff);
            text-align: center;
            margin: 0;
            padding: 0;
            color: white;
        }
        .card {
            background: rgba(255, 255, 255, 0.1);
            display: inline-block;
            padding: 40px 50px;
            border-radius: 15px;
            box-shadow: 0 0 20px rgba(0, 123, 255, 0.7);
            margin-top: 80px;
            width: 360px;
        }
        img {
            width: 120px;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 5px #00bfff);
        }
        input, select {
            width: 90%;
            padding: 12px;
            margin: 12px 0;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }
        button {
            background: #003366;
            color: white;
            padding: 12px 25px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            font-size: 18px;
            transition: background 0.3s ease;
        }
        button:hover {
            background: #001f33;
        }
        .msg {
            color: #ffcccb;
            margin-top: 15px;
            font-weight: bold;
        }
        label {
            font-weight: bold;
            font-size: 18px;
        }
        h2 {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="card">
        <img src="/static/logo_belutin.png" alt="Logo BELUT.IN">
        <h2>🐍 BELUT.IN Login</h2>
        <form method="POST" action="/auth">
            <label for="action">Pilih Tindakan:</label><br>
            <select id="action" name="action">
                <option value="login">Masuk</option>
                <option value="signup">Daftar</option>
            </select><br>
            <input type="email" name="email" placeholder="Email" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Lanjut</button>
        </form>
        {% if message %}
            <p class="msg">{{ message }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

otp_page = """
<!doctype html>
<html>
<head>
    <title>Verifikasi OTP</title>
    <style>
        body {
            text-align: center;
            font-family: Arial, sans-serif;
            margin-top: 100px;
            background: #004080;
            color: white;
        }
        input {
            padding: 12px;
            font-size: 18px;
            border-radius: 8px;
            border: none;
            width: 200px;
            margin-bottom: 20px;
        }
        button {
            background: #003366;
            color: white;
            padding: 12px 30px;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            font-weight: bold;
            font-size: 18px;
            transition: background 0.3s ease;
        }
        button:hover {
            background: #001f33;
        }
        p {
            color: #ff9999;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <h2>Masukkan Kode OTP yang Dikirim ke Email</h2>
    <form method="POST" action="/verify_otp">
        <input type="text" name="otp_input" placeholder="Masukkan 6 digit OTP" required pattern="\\d{6}" title="Masukkan 6 digit angka"><br>
        <button type="submit">Verifikasi</button>
    </form>
    {% if message %}
        <p>{{ message }}</p>
    {% endif %}
</body>
</html>
"""

dashboard_page = """
<!doctype html>
<html>
<head>
    <title>BELUT.IN — Dashboard</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            background: linear-gradient(to bottom, #003366, #87cefa);
            color: #003366;
        }
        .navbar {
            background: #003366;
            color: white;
            padding: 15px 30px;
            display: flex;
            align-items: center;
        }
        .navbar img {
            width: 50px;
            margin-right: 15px;
        }
        .navbar b {
            font-size: 20px;
            margin-right: 30px;
        }
        .navbar a {
            color: white;
            margin-right: 20px;
            text-decoration: none;
            font-weight: bold;
        }
        .navbar a:hover {
            text-decoration: underline;
        }
        .navbar .logout {
            margin-left: auto;
            color: yellow;
        }
        .content {
            padding: 40px;
            text-align: center;
        }
        h1 {
            font-size: 32px;
            margin-bottom: 20px;
        }
        p {
            font-size: 20px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <img src="/static/logo_belutin.png" alt="Logo BELUT.IN">
        <b>BELUT.IN</b>
        <a href="/">Home</a>
        <a href="/produksi">Produksi</a>
        <a href="/stok">Stok</a>
        <a href="/penjualan">Penjualan</a>
        <a href="/laporan">Laporan Keuangan</a>
        <a href="/logout" class="logout">Logout</a>
    </div>
    <div class="content">
        {% block content %}
        <h1>Selamat Datang di Sistem Manajemen Akuntansi Budidaya Belut 🐍</h1>
        <p>Aplikasi ini digunakan untuk pencatatan transaksi dan manajemen budidaya belut PT Djong Java.</p>
        {% endblock %}
    </div>
</body>
</html>
"""

# ---------------------------
# FUNGSI BANTUAN
# ---------------------------
def send_otp_via_email(recipient_email, otp_code):
    msg = EmailMessage()
    msg["Subject"] = "Kode OTP Login BELUT.IN"
    msg["From"] = EMAIL_SENDER
    msg["To"] = recipient_email
    msg.set_content(f"Halo! 👋\n\nKode OTP kamu adalah: {otp_code}\nJangan bagikan ke siapa pun ya!\n\n- Tim BELUT.IN")

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
        server.send_message(msg)

# ---------------------------
# ROUTES
# ---------------------------
@app.route("/", methods=["GET"])
def home():
    if session.get("user_email"):
        return render_template_string(dashboard_page)
    return render_template_string(login_page)

@app.route("/auth", methods=["POST"])
def auth():
    email = request.form.get("email")
    password = request.form.get("password")
    action = request.form.get("action")

    try:
        if action == "signup":
            supabase.auth.sign_up({"email": email, "password": password})
            msg = "Pendaftaran berhasil! Cek email kamu untuk verifikasi."
            return render_template_string(login_page, message=msg)
        elif action == "login":
            user = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if user and user.user:
                otp = random.randint(100000, 999999)
                session["pending_email"] = user.user.email
                session["otp_code"] = str(otp)
                send_otp_via_email(user.user.email, otp)
                return render_template_string(otp_page)
            else:
                msg = "Login gagal! Coba lagi."
        else:
            msg = "Tindakan tidak dikenal."
    except Exception as e:
        msg = f"Error: {e}"

    return render_template_string(login_page, message=msg)

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    otp_input = request.form.get("otp_input")
    if otp_input == session.get("otp_code"):
        session["user_email"] = session.get("pending_email")
        session.pop("otp_code", None)
        session.pop("pending_email", None)
        return redirect("/")
    return render_template_string(otp_page, message="Kode OTP salah!")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/produksi")
def produksi():
    content = "<h2>📊 Halaman Produksi</h2>"
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", content))

@app.route("/stok")
def stok():
    content = "<h2>📦 Manajemen Stok</h2>"
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", content))

@app.route("/penjualan")
def penjualan():
    content = "<h2>💰 Data Penjualan</h2>"
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", content))

@app.route("/laporan")
def laporan():
    content = "<h2>📑 Laporan Keuangan</h2>"
    return render_template_string(dashboard_page.replace("{% block content %}", "").replace("{% endblock %}", content))

# ---------------------------
# JALANKAN APP
# ---------------------------
if __name__ == "__main__":
    app.run(debug=True)
