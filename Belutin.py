import pandas as pd
from werkzeug.utils import secure_filename
from flask import Flask, render_template_string, request, redirect, session
from supabase import create_client, Client
from dotenv import load_dotenv
from email.message import EmailMessage
from datetime import timedelta
import smtplib, ssl, random, os, json, datetime

# ---- SESSION SETUP ----
load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") 
app.permanent_session_lifetime = timedelta(days=7)
# ------------------------

# =======================================
# Fungsi Format Rupiah 
# =======================================
def rupiah_small(nominal):
    try:
        nominal = float(nominal)
    except:
        nominal = 0
    return f"Rp {nominal:,.0f}".replace(",", ".")

# ---------------------------
# KONFIGURASI DASAR
# ---------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

app = Flask(__name__)
app.secret_key = os.urandom(24)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------------------
# TEMPLATE LOGIN PAGE (UPDATED)
# ---------------------------
login_page = """
<!doctype html>
<html>
<head>
    <title>BELUT.IN — Login</title>
    <style>
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            text-align: center;
            margin-top:60px;
            color:white;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .card {
            background: rgba(255,255,255,0.1);
            display:inline-block;
            padding:40px 50px;
            border-radius:20px;
            box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            width:400px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.2);
         }
        img {
            width:120px;
            margin-bottom:20px;
            filter: drop-shadow(0 0 10px #00bfff);
        }
        h2 {
            color: #ffffff;
            font-size: 28px;
            margin-bottom: 30px;
            text-shadow: 0 2px 10px rgba(0,123,255,0.5);
        }
        input, select {
            width:100%;
            padding:14px;
            margin:12px 0;
            border:none;
            border-radius:12px;
            font-size:16px;
            background: rgba(255,255,255,0.9);
            font-family: 'Poppins', sans-serif;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color:white;
            padding:14px 30px;
            border:none;
            border-radius:12px;
            cursor:pointer;
            font-weight:600;
            font-size:18px;
            transition: all 0.3s ease;
            margin-top: 15px;
            width: 100%;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        .msg { 
            color:#ffcccb; 
            margin-top:15px; 
            font-weight:bold; 
            background: rgba(255,0,0,0.2);
            padding: 10px;
            border-radius: 8px;
        }
        label { 
            font-weight:600; 
            font-size:16px; 
            display: block;
            text-align: left;
            margin-bottom: 8px;
            color: #e6f7ff;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="card">
        <img src="/static/logo_belutin.png" alt="BELUT.IN Logo">
        <h2>🐍 BELUT.IN Login</h2>
        <form method="POST" action="/auth">
            <label for="action">Pilih Tindakan:</label>
            <select id="action" name="action">
                <option value="login">Masuk</option>
                <option value="signup">Daftar</option>
            </select>
            <label for="email">Email:</label>
            <input type="email" name="email" placeholder="Masukkan email" required>
            <label for="password">Password:</label>
            <input type="password" name="password" placeholder="Masukkan password" required>
            <button type="submit">Lanjutkan</button>
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
    <title>Verifikasi OTP - BELUT.IN</title>
    <style>
        body {
            text-align: center;
            font-family: 'Poppins', sans-serif;
            margin: 0;
            padding: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: rgba(255, 255, 255, 0.1);
            padding: 40px 50px;
            border-radius: 20px;
            box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            width: 400px;
        }
        img {
            width:120px;
            margin-bottom:20px;
            filter: drop-shadow(0 0 10px #00bfff);
        }
        h2 {
            color: #ffffff;
            font-size: 28px;
            margin-bottom: 30px;
            text-shadow: 0 2px 10px rgba(0,123,255,0.5);
        }
        input {
            padding: 14px;
            font-size: 18px;
            border-radius: 12px;
            border: none;
            width: 100%;
            margin-bottom: 25px;
            background: rgba(255,255,255,0.9);
            font-family: 'Poppins', sans-serif;
            text-align: center;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 14px 30px;
            border: none;
            border-radius: 12px;
            cursor: pointer;
            font-weight: 600;
            font-size: 18px;
            transition: all 0.3s ease;
            width: 100%;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
        }
        button:hover { 
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        p { 
            color: #ffcccb; 
            font-weight: 600; 
            background: rgba(255,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
            margin-top: 15px;
        }
        .instruction {
            color: #e6f7ff;
            margin-bottom: 25px;
            font-size: 16px;
        }
    </style>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <img src="/static/logo_belutin.png" alt="BELUT.IN Logo">
        <h2>🔐 Verifikasi OTP</h2>
        <p class="instruction">Masukkan kode OTP yang telah dikirim ke email Anda</p>
        <form method="POST" action="/verify_otp">
            <input type="text" name="otp_input" placeholder="Masukkan 6 digit OTP" required pattern="\\d{6}" maxlength="6">
            <button type="submit">Verifikasi Sekarang</button>
        </form>
        {% if message %}
            <p>{{ message }}</p>
        {% endif %}
    </div>
</body>
</html>
"""

# ---------------------------
# DATA AKUN
# ---------------------------
DAFTAR_AKUN = [
    # ASET LANCAR
    {"kode": "1-1100", "nama": "Kas", "kategori": "Aset"},
    {"kode": "1-1110", "nama": "Kas di Bank", "kategori": "Aset"},
    {"kode": "1-1200", "nama": "Piutang Dagang", "kategori": "Aset"},
    {"kode": "1-1310", "nama": "Persediaan Bibit Belut Standar", "kategori": "Aset"},
    {"kode": "1-1320", "nama": "Persediaan Bibit Belut Super", "kategori": "Aset"},
    {"kode": "1-1410", "nama": "Persediaan Belut Standar", "kategori": "Aset"},
    {"kode": "1-1420", "nama": "Persediaan Belut Super", "kategori": "Aset"},
    {"kode": "1-1510", "nama": "Persediaan Pakan Belut Standar", "kategori": "Aset"},
    {"kode": "1-1520", "nama": "Persediaan Pakan Belut Super", "kategori": "Aset"},
    {"kode": "1-1600", "nama": "Perlengkapan", "kategori": "Aset"},
    
    # ASET TETAP
    {"kode": "1-2100", "nama": "Tanah", "kategori": "Aset"},
    {"kode": "1-2200", "nama": "Bangunan", "kategori": "Aset"},
    {"kode": "1-2210", "nama": "Akumulasi Penyusutan Bangunan", "kategori": "Aset"},
    {"kode": "1-2300", "nama": "Kendaraan", "kategori": "Aset"},
    {"kode": "1-2310", "nama": "Akumulasi Penyusutan Kendaraan", "kategori": "Aset"},
    {"kode": "1-2400", "nama": "Peralatan", "kategori": "Aset"},
    {"kode": "1-2410", "nama": "Akumulasi Penyusutan Peralatan", "kategori": "Aset"},
    
    # LIABILITAS
    {"kode": "2-1100", "nama": "Utang Dagang", "kategori": "Liabilitas"},
    {"kode": "2-1200", "nama": "Utang Biaya", "kategori": "Liabilitas"},
    {"kode": "2-2100", "nama": "Pinjaman Bank BCA", "kategori": "Liabilitas"},
    
    # EKUITAS
    {"kode": "3-1100", "nama": "Modal Pemilik", "kategori": "Ekuitas"},
    {"kode": "3-1200", "nama": "Prive", "kategori": "Ekuitas"},
    {"kode": "3-1300", "nama": "Ikhtisar Laba Rugi", "kategori": "Ekuitas"},
    
    # PENDAPATAN
    {"kode": "4-1110", "nama": "Penjualan Belut Standar", "kategori": "Pendapatan"},
    {"kode": "4-1120", "nama": "Penjualan Belut Super", "kategori": "Pendapatan"},
    
    # HARGA POKOK PENJUALAN
    {"kode": "5-1110", "nama": "Harga Pokok Penjualan Belut Standar", "kategori": "HPP"},
    {"kode": "5-1120", "nama": "Harga Pokok Penjualan Belut Super", "kategori": "HPP"},
    
    # PEMBELIAN
    {"kode": "5-1210", "nama": "Pembelian Bibit Belut Standar", "kategori": "Pembelian"},
    {"kode": "5-1220", "nama": "Pembelian Bibit Belut Super", "kategori": "Pembelian"},
    {"kode": "5-1310", "nama": "Pembelian Pakan Belut Standar", "kategori": "Pembelian"},
    {"kode": "5-1320", "nama": "Pembelian Pakan Belut Super", "kategori": "Pembelian"},
    
    # BEBAN OPERASIONAL
    {"kode": "6-1100", "nama": "Beban Listrik dan Air", "kategori": "Beban"},
    {"kode": "6-1200", "nama": "Beban Perlengkapan", "kategori": "Beban"},
    {"kode": "6-1300", "nama": "Beban Depresiasi", "kategori": "Beban"},
    {"kode": "6-1410", "nama": "Beban Pakan Belut Standar", "kategori": "Beban"},
    {"kode": "6-1420", "nama": "Beban Pakan Belut Super", "kategori": "Beban"},
    {"kode": "6-1500", "nama": "Beban Lain-Lain", "kategori": "Beban"},
    
    # PENDAPATAN LAIN-LAIN
    {"kode": "8-1100", "nama": "Pendapatan Bunga", "kategori": "Pendapatan Lain"},
    {"kode": "8-1200", "nama": "Pendapatan Denda", "kategori": "Pendapatan Lain"},
    {"kode": "8-1300", "nama": "Pendapatan Lain-Lain", "kategori": "Pendapatan Lain"},
    
    # BEBAN LAIN-LAIN
    {"kode": "9-1100", "nama": "Beban Bunga", "kategori": "Beban Lain"},
    {"kode": "9-1200", "nama": "Beban Administrasi Bank", "kategori": "Beban Lain"},
    {"kode": "9-1300", "nama": "Beban Denda", "kategori": "Beban Lain"}
]

# ---------------------------
# FUNGSI HELPER
# ---------------------------
def simpan_jurnal_auto(keterangan, tanggal, debit_akun, kredit_akun, nominal):
    """
    Menyimpan jurnal otomatis ke database
    """
    user = session.get("user_email")
    
    data = {
        "description": keterangan,
        "date": tanggal,
        "lines": [
            {"account_code": debit_akun["kode"], "account_name": debit_akun["nama"], "debit": nominal, "credit": 0},
            {"account_code": kredit_akun["kode"], "account_name": kredit_akun["nama"], "debit": 0, "credit": nominal},
        ],
        "user_email": user,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    
    # Simpan ke database
    supabase.table("general_journal").insert(data).execute()

def ambil_semua_jurnal():
    """
    Mengambil semua jurnal dari database untuk user yang sedang login
    """
    user = session.get("user_email")  
    
    res = supabase.table("general_journal").select("*").eq("user_email", user).order("date", desc=False).execute()
    hasil = []
    
    for j in res.data or []:
        lines = j.get("lines", [])
        if isinstance(lines, str):
            try:
                lines = json.loads(lines)
            except:
                lines = []
        
        for b in lines:
            hasil.append({
                "tanggal": j["date"],
                "akun": b.get("account_name", ""),
                "kode": b.get("account_code", ""),
                "debit": b.get("debit", 0),
                "kredit": b.get("credit", 0),
                "keterangan": j["description"]
            })
    
    return hasil

def rupiah_small(nilai):
    """
    Format angka ke format Rupiah
    """
    try:
        return f"Rp {int(nilai):,}".replace(",", ".")
    except:
        return "Rp 0"

def get_akun_dict():
    user = session.get("user_email")
    akun_dict = {}
    
    # 1. AMBIL DATA JURNAL UMUM
    res = supabase.table("general_journal").select("*")\
        .eq("user_email", user).execute()
    data = res.data or []
    
    for row in data:
        lines = row.get("lines", [])
        if isinstance(lines, str):
            try:
                lines = json.loads(lines)
            except:
                lines = []
        
        for b in lines:
            kode = b.get("account_code")
            if kode not in akun_dict:
                akun_dict[kode] = {
                    "akun": b.get("account_name"),
                    "total_debit": 0,
                    "total_kredit": 0,
                    "transaksi": []
                }
            akun_dict[kode]["total_debit"] += float(b.get("debit") or 0)
            akun_dict[kode]["total_kredit"] += float(b.get("credit") or 0)
            akun_dict[kode]["transaksi"].append({
                "tanggal": row.get("date"),
                "keterangan": row.get("description"),
                "debit": b.get("debit"),
                "kredit": b.get("credit")
            })
    
    # 2. AMBIL DATA JURNAL PENYESUAIAN DAN TAMBAHKAN
    try:
        res_penyesuaian = supabase.table("adjustment_journal").select("*")\
            .eq("user_email", user).execute()
        data_penyesuaian = res_penyesuaian.data or []
        
        for row in data_penyesuaian:
            kode = row.get("ref")
            if not kode or row.get("is_indent"):  # Skip baris indent/penjelas
                continue
                
            if kode not in akun_dict:
                akun_dict[kode] = {
                    "akun": row.get("description"),
                    "total_debit": 0,
                    "total_kredit": 0,
                    "transaksi": []
                }
            
            akun_dict[kode]["total_debit"] += float(row.get("debit") or 0)
            akun_dict[kode]["total_kredit"] += float(row.get("credit") or 0)
            akun_dict[kode]["transaksi"].append({
                "tanggal": row.get("date"),
                "keterangan": f"PENYESUAIAN: {row.get('description')}",
                "debit": row.get("debit"),
                "kredit": row.get("credit")
            })
    except Exception as e:
        print(f"Error mengambil jurnal penyesuaian: {e}")
    
    # 3. AMBIL SALDO AWAL
    opening = supabase.table("opening_balance").select("*").execute().data or []
    for o in opening:
        kode = o["account_code"]
        if kode not in akun_dict:
            akun_dict[kode] = {
                "akun": o["account_name"],
                "total_debit": 0,
                "total_kredit": 0,
                "transaksi": []
            }
        akun_dict[kode]["total_debit"] += float(o.get("debit") or 0)
        akun_dict[kode]["total_kredit"] += float(o.get("credit") or 0)
        akun_dict[kode]["transaksi"].append({
            "tanggal": "Saldo Awal",
            "keterangan": "Saldo Awal",
            "debit": o["debit"],
            "kredit": o["credit"]
        })
    
    return akun_dict
# ---------------------------
# DASHBOARD LAYOUT
# ---------------------------
dashboard_layout_modern = """
<!doctype html>
<html>
<head>
<nav style="background: linear-gradient(135deg, #667eea, #764ba2); padding:10px;"></nav>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>BELUT.IN — Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root{
      --bg:#ffffff;
      --card1: linear-gradient(135deg,#6dd5ed,#2193b0);
      --card2: linear-gradient(135deg,#a18cd1,#fbc2eb);
      --card3: linear-gradient(135deg,#f6d365,#fda085);
      --card4: linear-gradient(135deg,#cfd9df,#e2ebf0);
      --accent:#003d80;
      --muted:#6b7a90;
      --radius:16px;
      font-family: 'Poppins', sans-serif;
    }
    html,body{margin:0;padding:0;background:var(--bg);color:var(--accent);min-height:100%}
    .top-banner{
      background: linear-gradient(135deg, #667eea, #764ba2);
      display:flex;
      gap:20px;
      align-items:center;
      flex-wrap:wrap;
      position:relative;
    }
    .logo-corner{
      position:absolute;
      top:15px;
      left:18px;
      width:50px;
      height:50px;
    }
    .logo-corner img{
      width:100%;
      height:100%;
      object-fit:contain;
      filter: drop-shadow(0 2px 8px rgba(0,0,0,0.2));
    }
    .banner-left{flex:1;min-width:240px;color:white;margin-left:60px}
    .banner-left h1{margin:0;font-size:22px;letter-spacing:0.2px}
    .banner-left p{margin:6px 0 0 0;opacity:0.95}
    .banner-img{width:160px;height:100px;border-radius:12px;overflow:hidden;box-shadow:0 8px 30px rgba(0,0,0,0.12)}
    .banner-img img{width:100%;height:100%;object-fit:cover;display:block}

    .container{max-width:1100px;margin:22px auto;padding:0 18px}
    .grid{
      display:grid;
      grid-template-columns: repeat(auto-fit,minmax(220px,1fr));
      gap:18px;
      margin-top:22px;
    }
    .card{
      background:linear-gradient(135deg, #ffffff, #ffffff);
      border-radius:var(--radius);
      padding:18px;
      box-shadow:0 6px 20px rgba(15,20,40,0.06);
      transition: transform .28s ease, box-shadow .28s ease;
      cursor:pointer;
      color:white;
      min-height:140px;
      display:flex;
      flex-direction:column;
      justify-content:space-between;
      overflow:hidden;
    }
    .card:hover{ transform: translateY(-8px); box-shadow:0 18px 40px rgba(2,48,71,0.12); }
    .card .title{font-weight:600;font-size:16px}
    .card .desc{font-size:13px;opacity:0.95;margin-top:8px;color:rgba(255,255,255,0.92)}
    .card .icon{width:56px;height:56px;border-radius:12px;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.12);backdrop-filter: blur(2px)}
    .card.small{min-height:120px}

    /* warna per card (override) */
    .c1{background:var(--card1)}
    .c2{background:var(--card2); color:#2b1036}
    .c3{background:var(--card3); color:#3b2f1f}
    .c4{background:var(--card4); color:#17324d}
    .c5{background: linear-gradient(135deg,#7bdcb5,#4da0ff)}
    .c6{background: linear-gradient(135deg,#ffd6a5,#fd5a5a)}

    /* small info row */
    .row-info{display:flex;gap:14px;align-items:center}
    .stat{background:rgba(255,255,255,0.9);padding:8px 12px;border-radius:10px;font-weight:600;color:#5a4a7d;box-shadow:0 2px 8px rgba(0,0,0,0.05)}

    /* footer / header nav */
    .nav{
      display:flex;gap:16px;align-items:center;justify-content:flex-end;padding:10px 18px;background:transparent;
      color:var(--accent)
    }
    .nav a{color:var(--accent);text-decoration:none;font-weight:600}
    .welcome{font-size:13px;color:var(--muted);margin-top:6px}

    /* responsive adjustments */
    @media (max-width:640px){
      .banner-img{width:120px;height:80px}
      .banner-left h1{font-size:18px}
      .banner-left{margin-left:0}
      .logo-corner{position:static;margin-bottom:10px}
    }
    /* button like link inside card */
    .link-btn{display:inline-block;padding:8px 12px;border-radius:10px;background:rgba(255,255,255,0.12);font-weight:600;text-decoration:none;color:inherit;margin-top:10px}
  </style>
</head>
<body>
  
  <div class="top-banner">
    <div class="logo-corner">
      <img src="/static/logo_belutin.png" alt="BELUT.IN Logo">
    </div>
    <div class="banner-left">
      <h1>Selamat Datang di BELUT.IN — Sistem Informasi Akuntansi Budidaya Belut Djong Java</h1>
      <p>Platform akuntansi yang membantu mengelola produksi, persediaan, transaksi, dan laporan keuangan usaha budidaya belut. Ringkas, modern, dan siap pakai sejak.</p>
      <div class="welcome">Halo, <strong>{{ user }}</strong> · <span style="opacity:0.85">Kelola transaksi & laporan dengan cepat</span></div>
    </div>
    <div class="banner-img">
      <img src="/static/kolam_belut.png" alt="Kolam Belut">
    </div>
  </div>

  <div class="container">
    <div class="nav">
      <a href="/logout" style="color:#c33">Logout</a>
    </div>

    <div style="display:flex;gap:18px;align-items:center;justify-content:space-between;flex-wrap:wrap">
      <div style="min-width:220px">
        <h2 style="margin:0;color:#1c3b5a">Dashboard</h2>
        <div class="welcome">Pilih menu untuk mulai bekerja</div>
      </div>
      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap">
        <div class="stat">Saldo Kas: {{ saldo_kas }}</div>
        <div class="stat">Total Transaksi: {{ total_transaksi }}</div>
      </div>
    </div>

    <div class="grid" style="margin-top:18px;">
      <a href="/tentang" style="text-decoration:none">
        <div class="card c2">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div class="title">Tentang Aplikasi</div>
              <div class="desc">Info singkat & visi misi Djong Java.</div>
            </div>
            <div class="icon">ℹ</div>
          </div>
          <div class="link-btn">Baca selengkapnya →</div>
        </div>
      </a>

      <a href="/saldo_awal" style="text-decoration:none">
        <div class="card c1">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div class="title">Input Saldo Awal</div>
              <div class="desc">Masukkan saldo awal akun (Excel / manual).</div>
            </div>
            <div class="icon">📥</div>
          </div>
          <div class="link-btn">Buka Form</div>
        </div>
      </a>

      <a href="/transaksi" style="text-decoration:none">
        <div class="card c3">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div class="title">Input Transaksi</div>
              <div class="desc">Catat penjualan & pembelian (Tunai / Kredit).</div>
            </div>
            <div class="icon">💸</div>
          </div>
          <div class="link-btn">Masuk →</div>
        </div>
      </a>

      <a href="/informasi-produk" style="text-decoration:none">
        <div class="card c5">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div class="title">Informasi Produk</div>
              <div class="desc">Lihat Informasi Produk Djong Java.</div>
            </div>
            <div class="icon">🐟</div>
          </div>
          <div class="link-btn">Lihat Informasi Produk</div>
        </div>
      </a>

      <a href="/akuntansi" style="text-decoration:none">
        <div class="card c4">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div class="title">Akuntansi</div>
              <div class="desc">Jurnal, Buku Besar, Neraca, Laporan</div>
            </div>
            <div class="icon">📚</div>
          </div>
          <div class="link-btn">Buka Menu Akuntansi</div>
        </div>
      </a>

      <a href="/histori" style="text-decoration:none">
        <div class="card c6">
          <div style="display:flex;justify-content:space-between;align-items:flex-start">
            <div>
              <div class="title">Histori Transaksi</div>
              <div class="desc">Riwayat transaksi seperti mutasi rekening.</div>
            </div>
            <div class="icon">🕘</div>
          </div>
          <div class="link-btn">Cek Riwayat</div>
        </div>
      </a>
    </div>
  </div>
</body>
</html>
"""
# =======================================
# ROUTES
# =======================================
@app.route("/", methods=["GET"])
@app.route("/dashboard", methods=["GET"])
def home():
    if session.get("user_email"):
        saldo_kas_str = "Rp0"
        total_transaksi_str = "0"
        
        try:
            res = supabase.table("general_journal").select("*").execute()
            total_transaksi_str = str(len(res.data or []))
        except:
            pass
        
        html = dashboard_layout_modern.replace("{{ user }}", session.get("user_email", ""))
        html = html.replace("{{ saldo_kas }}", saldo_kas_str)
        html = html.replace("{{ total_transaksi }}", total_transaksi_str)
        return render_template_string(html)
    
    return render_template_string(login_page)

@app.route("/auth", methods=["POST"])
def auth():
    email = request.form["email"]
    password = request.form["password"]
    action = request.form["action"]

    user_data = supabase.table("users").select("*").eq("email", email).execute()
    user_exists = len(user_data.data) > 0

    if action == "signup":
        if user_exists:
            return render_template_string(login_page, message="Email sudah terdaftar.")
        supabase.table("users").insert({"email": email, "password": password}).execute()
        return render_template_string(login_page, message="Akun berhasil dibuat, silakan login.")

    elif action == "login":
        if not user_exists:
            return render_template_string(login_page, message="Akun belum terdaftar.")
        user = user_data.data[0]
        if user["password"] != password:
            return render_template_string(login_page, message="Password salah.")

        otp = str(random.randint(100000, 999999))
        session["pending_email"] = email
        session["otp"] = otp

        try:
            msg = EmailMessage()
            msg["Subject"] = "Kode OTP BELUT.IN"
            msg["From"] = EMAIL_SENDER
            msg["To"] = email
            msg.set_content(f"Kode OTP kamu adalah {otp}")

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
                server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
                server.send_message(msg)
        except Exception as e:
            print(f"Error sending email: {e}")
            return render_template_string(login_page, message="Error mengirim OTP.")

        return render_template_string(otp_page, message="OTP telah dikirim ke email!")

@app.route("/verify_otp", methods=["POST"])
def verify_otp():
    otp_input = request.form["otp_input"]
    if otp_input == session.get("otp"):
        session["user_email"] = session.get("pending_email")
        session.pop("otp", None)
        session.pop("pending_email", None)
        return redirect("/dashboard")
    else:
        return render_template_string(otp_page, message="OTP salah.")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/tentang")
def tentang():
    if not session.get("user_email"):
        return redirect("/")
        
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Tentang Aplikasi - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h1 {
                color: #667eea;
                font-size: 28px;
                text-align: center;
                margin-bottom: 20px;
            }
            p {
                line-height: 1.8;
                font-size: 16px;
                text-align: justify;
                color: #2d3748;
            }
            .footer {
                margin-top: 30px;
                padding-top: 20px;
                text-align: center;
                font-size: 13px;
                color: #718096;
                border-top: 2px solid #e2e8f0;
            }
            a.button {
                display: inline-block;
                margin-top: 20px;
                background: #667eea;
                color: white;
                padding: 12px 25px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            a.button:hover {
                background: #764ba2;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📖 Sistem Informasi Akuntansi Budidaya Belut Djong Java</h1>
            <p><strong>BELUT.IN</strong> adalah Sistem Informasi Akuntansi khusus untuk 
                        usaha budidaya belut — dikembangkan untuk membantu petani dan pengelola usaha 
                        budidaya belut (Djong Java) dalam mencatat transaksi, mengelola persediaan, dan 
                        menghasilkan laporan keuangan secara cepat dan akurat. BELUT.IN dirancang agar mudah digunakan 
                        oleh pelaku usaha tanpa latar belakang akuntansi mendalam.</p>
                                  
            <p><strong>Apa yang bisa dilakukan:</strong></p>
            <ul>
                <li>Mencatat transaksi penjualan & pembelian.</li>
                <li>Mengelola saldo awal dan persediaan belut.</li>
                <li>Menghasilkan Jurnal Umum, Buku Besar, Neraca Saldo, Laporan Laba Rugi, Laporan Arus Kas, dan laporan lainnya.</li>
                <li>Mengarsipkan histori transaksi sehingga mudah dilacak.</li>
            </ul>
            <div class="footer">
                © 2025 Djong Java | Dikembangkan oleh Kelompok 12
                <br>
                <a href="/dashboard" class="button">⬅ Kembali ke Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/saldo_awal", methods=["GET", "POST"])
def saldo_awal():
    if not session.get("user_email"):
        return redirect("/")

    success_msg = ""
    error_msg = ""

    if request.method == "POST":
        action = request.form.get("action")
        
        # HAPUS SATU AKUN
        if action == "delete_one":
            try:
                entry_id = request.form.get("entry_id")
                supabase.table("opening_balance").delete().eq("id", entry_id).execute()
                success_msg = "✅ Saldo awal berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        # RESET SEMUA DATA
        elif action == "reset_all":
            try:
                # Hapus semua data saldo awal
                all_data = supabase.table("opening_balance").select("id").execute().data or []
                for item in all_data:
                    supabase.table("opening_balance").delete().eq("id", item["id"]).execute()
                success_msg = "✅ Semua saldo awal berhasil direset!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"

        # INPUT MANUAL
        else:
            try:
                kode_akun = request.form.get("kode")
                if not kode_akun:
                    error_msg = "⚠ Pilih akun!"
                else:
                    nama_akun = next(a["nama"] for a in DAFTAR_AKUN if a["kode"] == kode_akun)
                    debit = float(request.form.get("debit") or 0)
                    kredit = float(request.form.get("kredit") or 0)

                    supabase.table("opening_balance").insert({
                        "account_code": kode_akun,
                        "account_name": nama_akun,
                        "debit": debit,
                        "credit": kredit,
                        "created_at": datetime.datetime.utcnow().isoformat()
                    }).execute()

                    success_msg = f"✅ Saldo awal {nama_akun} berhasil disimpan!"
                    
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"

    # Ambil data saldo awal
    data = supabase.table("opening_balance").select("*").execute().data or []
    
    # Build rows dengan tombol hapus
    rows = ""
    for d in data:
        rows += f"""
        <tr>
            <td>{d['account_code']}</td>
            <td>{d['account_name']}</td>
            <td style="text-align:right;">{rupiah_small(d['debit'])}</td>
            <td style="text-align:right;">{rupiah_small(d['credit'])}</td>
            <td style="text-align:center;">
                <form method="POST" style="display:inline;" onsubmit="return confirm('Hapus saldo awal untuk akun {d['account_name']}?');">
                    <input type="hidden" name="action" value="delete_one">
                    <input type="hidden" name="entry_id" value="{d['id']}">
                    <button type="submit" class="btn-delete">🗑</button>
                </form>
            </td>
        </tr>
        """

    options = "".join([f"<option value='{a['kode']}'>{a['nama']}</option>" for a in DAFTAR_AKUN])

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Saldo Awal - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            h3 {
                color: #2d3748;
                margin: 20px 0 15px 0;
                font-size: 20px;
            }
            .alert {
                padding: 15px;
                margin: 15px 0;
                border-radius: 8px;
                font-weight: 600;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border-left: 4px solid #28a745;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border-left: 4px solid #dc3545;
            }
            .flex {
                display: flex;
                gap: 30px;
                flex-wrap: wrap;
                margin-bottom: 40px;
            }
            .box {
                flex: 1;
                min-width: 300px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 25px;
                border-radius: 15px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .box h3 {
                color: #2d3748;
                margin-top: 0;
                margin-bottom: 20px;
                font-size: 18px;
            }
            label {
                display: block;
                margin: 12px 0 5px 0;
                font-weight: 600;
                color: #2d3748;
            }
            input, select {
                width: 100%;
                padding: 12px;
                margin: 8px 0;
                border-radius: 8px;
                border: 1px solid #cbd5e0;
                font-family: 'Poppins', sans-serif;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            button {
                width: 100%;
                padding: 12px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                font-family: 'Poppins', sans-serif;
                transition: 0.3s;
            }
            .btn-primary {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                margin-top: 10px;
            }
            .btn-primary:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            .info-text {
                font-size: 12px;
                color: #4a5568;
                margin-top: 10px;
                font-style: italic;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-radius: 12px;
                overflow: hidden;
            }
            thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e2e8f0;
                color: #2d3748;
            }
            tbody tr:hover {
                background: #f7fafc;
            }
            .btn-delete {
                background: #dc3545;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                font-size: 14px;
                width: auto;
            }
            .btn-delete:hover {
                background: #c82333;
                transform: scale(1.05);
            }
            .bottom-actions {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .btn-reset {
                background: #dc3545;
                color: white;
                padding: 12px 25px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
                display: inline-block;
                border: none;
                cursor: pointer;
            }
            .btn-reset:hover {
                background: #c82333;
                transform: translateY(-2px);
            }
            .btn-back {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 12px 25px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
                display: inline-block;
            }
            .btn-back:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>💰 Input Saldo Awal</h2>
            
            {% if success_msg %}
                <div class="alert success">{{ success_msg }}</div>
            {% endif %}
            {% if error_msg %}
                <div class="alert error">{{ error_msg }}</div>
            {% endif %}
            
            <div class="flex">
                <div class="box">
                    <h3>📝 Input Manual</h3>
                    <form method="POST">
                        <label>Akun</label>
                        <select name="kode" required>
                            <option value="">-- Pilih Akun --</option>
                            {{ options|safe }}
                        </select>
                        <label>Debit (Rp)</label>
                        <input type="number" name="debit" step="0.01" value="0">
                        <label>Kredit (Rp)</label>
                        <input type="number" name="kredit" step="0.01" value="0">
                        <button type="submit" class="btn-primary">💾 Simpan</button>
                    </form>
                </div>
            <h3>📋 Daftar Saldo Awal</h3>
            <table>
                <thead>
                    <tr>
                        <th style="width:15%;">Kode</th>
                        <th style="width:40%;">Nama Akun</th>
                        <th style="width:18%; text-align:right;">Debit</th>
                        <th style="width:18%; text-align:right;">Kredit</th>
                        <th style="width:9%; text-align:center;">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% if rows %}
                        {{ rows|safe }}
                    {% else %}
                        <tr>
                            <td colspan="5" style="text-align:center; padding:30px; color:#999;">
                                Belum ada data saldo awal. Silakan input manual atau upload Excel.
                            </td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
            
            <div class="bottom-actions">
                <a href="/dashboard" class="btn-back">⬅ Kembali ke Dashboard</a>
                
                <form method="POST" style="display:inline;" onsubmit="return confirm('⚠ PERHATIAN!\\n\\nAnda akan menghapus SEMUA data saldo awal.\\nApakah Anda yakin?');">
                    <input type="hidden" name="action" value="reset_all">
                    <button type="submit" class="btn-reset">🗑 Reset Semua Data</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    """, options=options, rows=rows, success_msg=success_msg, error_msg=error_msg)
@app.route("/transaksi")
def transaksi_menu():
    """Halaman menu pilihan transaksi"""
    if not session.get("user_email"):
        return redirect("/")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Input Transaksi - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                max-width: 900px;
                width: 100%;
                background: white;
                padding: 50px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 20px;
                font-size: 36px;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 50px;
                font-size: 16px;
            }
            .menu-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 30px;
                margin-bottom: 40px;
            }
            .menu-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 30px;
                border-radius: 15px;
                text-align: center;
                cursor: pointer;
                transition: transform 0.3s, box-shadow 0.3s;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                text-decoration: none;
                color: white;
            }
            .menu-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .menu-icon {
                font-size: 60px;
                margin-bottom: 20px;
            }
            .menu-title {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            .menu-desc {
                font-size: 14px;
                opacity: 0.9;
            }
            .btn-back {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 12px 25px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-back:hover {
                background: #764ba2;
                transform: translateY(-2px);
            }
            .back-section {
                text-align: center;
                padding-top: 30px;
                border-top: 2px solid #e2e8f0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>💼 Input Transaksi</h2>
            <p class="subtitle">Pilih jenis transaksi yang ingin Anda input</p>
            
            <div class="menu-grid">
                <a href="/transaksi/penjualan" class="menu-card">
                    <div class="menu-icon">💰</div>
                    <div class="menu-title">Penjualan</div>
                    <div class="menu-desc">Input transaksi penjualan belut</div>
                </a>
                <a href="/transaksi/pembelian" class="menu-card">
                    <div class="menu-icon">🛒</div>
                    <div class="menu-title">Pembelian</div>
                    <div class="menu-desc">Input transaksi pembelian</div>
                </a>
                <a href="/transaksi/lainnya" class="menu-card">
                    <div class="menu-icon">💸</div>
                    <div class="menu-title">Lainnya</div>
                    <div class="menu-desc">Input transaksi lainnya</div>
                </a>
            </div>
            
            <div class="back-section">
                <a href="/dashboard" class="btn-back">⬅ Kembali ke Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/transaksi/penjualan", methods=["GET", "POST"])
def transaksi_penjualan():
    if not session.get("user_email"):
        return redirect("/")

    success_msg = ""
    error_msg = ""

    akun_kas = next(a for a in DAFTAR_AKUN if a["nama"] == "Kas")
    akun_kas_bank = next(a for a in DAFTAR_AKUN if a["nama"] == "Kas di Bank")
    akun_piutang = next(a for a in DAFTAR_AKUN if a["nama"] == "Piutang Dagang")
    
    # Hanya penjualan belut
    akun_penjualan = [a for a in DAFTAR_AKUN if a["kategori"] == "Pendapatan" and "Penjualan Belut" in a["nama"]]

    HARGA_BELUT = {
        "Penjualan Belut Standar": 50000,
        "Penjualan Belut Super": 65000
    }

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "delete":
            try:
                entry_id = request.form.get("entry_id")
                supabase.table("general_journal").delete().eq("id", entry_id).execute()
                success_msg = "✅ Transaksi berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        elif action == "reset_all":
            try:
                supabase.table("general_journal").delete().like("description", "%Penjualan%").execute()
                success_msg = "✅ Semua transaksi penjualan berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        else:
            try:
                akun_kode = request.form.get("akun", "")
                tanggal = request.form.get("tanggal", "")
                metode = request.form.get("metode", "")
                kuantitas = float(request.form.get("kuantitas", 0))

                if not tanggal or not akun_kode:
                    error_msg = "⚠ Lengkapi semua field!"
                elif kuantitas <= 0:
                    error_msg = "⚠ Kuantitas harus lebih dari 0!"
                else:
                    akun = next(a for a in DAFTAR_AKUN if a["kode"] == akun_kode)
                    harga_per_kg = HARGA_BELUT.get(akun["nama"], 0)
                    nominal = kuantitas * harga_per_kg

                    if metode == "Tunai":
                        debit = akun_kas
                    elif metode == "Transfer":
                        debit = akun_kas_bank
                    else:
                        debit = akun_piutang
                    
                    kredit = akun
                    # Hilangkan kata "Penjualan" dari nama akun
                    nama_belut = akun['nama'].replace("Penjualan ", "")
                    keterangan = f"Penjualan {nama_belut} - {kuantitas} kg ({metode})"
                    simpan_jurnal_auto(keterangan, tanggal, debit, kredit, nominal)
                    success_msg = f"✅ Transaksi penjualan berhasil disimpan! Total: {rupiah_small(nominal)}"

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"

    try:
        res = supabase.table("general_journal").select("*").like("description", "%Penjualan%").order("date.desc,id.desc").limit(5).execute()
        recent_transactions = res.data or []
    except:
        recent_transactions = []

    recent_rows = ""
    for trx in recent_transactions:
        lines = trx.get('lines', [])
        for idx, line in enumerate(lines):
            account_code = line.get('account_code', '')
            account_name = next((a["nama"] for a in DAFTAR_AKUN if a["kode"] == account_code), account_code)
            debit = rupiah_small(line.get('debit', 0))
            kredit = rupiah_small(line.get('credit', 0))
            
            if idx == 0:
                recent_rows += f"""
                <tr>
                    <td rowspan="{len(lines)}" style="vertical-align:top;">{trx.get('date')}</td>
                    <td style="padding-left:15px;">{account_name}</td>
                    <td style="text-align:right;">{debit}</td>
                    <td style="text-align:right;">{kredit}</td>
                    <td rowspan="{len(lines)}" style="text-align:center; vertical-align:middle;">
                        <form method="POST" style="display:inline;" onsubmit="return confirm('Hapus transaksi ini?');">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="entry_id" value="{trx.get('id')}">
                            <button type="submit" class="btn-delete">🗑</button>
                        </form>
                    </td>
                </tr>
                """
            else:
                recent_rows += f"""
                <tr>
                    <td style="padding-left:30px;">{account_name}</td>
                    <td style="text-align:right;">{debit}</td>
                    <td style="text-align:right;">{kredit}</td>
                </tr>
                """
        
        recent_rows += f"""
        <tr style="background:#f9fafb;">
            <td colspan="4" style="padding-left:15px; font-style:italic; color:#666; font-size:12px;">
                <em>{trx.get('description')}</em>
            </td>
        </tr>
        """

    options_penjualan = "".join([f"<option value='{a['kode']}'>{a['nama']}</option>" for a in akun_penjualan])

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transaksi Penjualan</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Poppins', sans-serif; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                min-height: 100vh; 
                padding: 20px; 
            }
            .container { 
                max-width: 900px; 
                margin: 40px auto; 
                background: white; 
                padding: 40px; 
                border-radius: 20px; 
                box-shadow: 0 15px 50px rgba(0,0,0,0.3); 
            }
            h2 { 
                color: #667eea; 
                text-align: center; 
                margin-bottom: 30px; 
                font-size: 32px; 
            }
            h3 { 
                color: #2d3748; 
                margin: 30px 0 15px 0; 
                font-size: 20px; 
            }
            .info-box { 
                background: #e7f3ff; 
                padding: 15px; 
                border-radius: 10px; 
                margin-bottom: 20px; 
                font-size: 14px; 
                border-left: 4px solid #667eea; 
            }
            .total-box { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 20px; 
                border-radius: 10px; 
                margin: 20px 0; 
                font-weight: bold; 
                color: white; 
                font-size: 20px; 
                text-align: center; 
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3); 
            }
            .detail-hitung { 
                background: #f7fafc; 
                padding: 15px; 
                border-radius: 8px; 
                margin: 10px 0; 
                font-size: 14px; 
                color: #4a5568; 
                border-left: 3px solid #667eea; 
            }
            label { 
                font-weight: 600; 
                display: block; 
                margin: 15px 0 8px; 
                color: #2d3748; 
            }
            input, select { 
                width: 100%; 
                padding: 12px; 
                border-radius: 8px; 
                border: 1px solid #ddd; 
                box-sizing: border-box; 
                font-family: 'Poppins', sans-serif; 
                font-size: 14px;
            }
            input:focus, select:focus { 
                outline: none; 
                border-color: #667eea; 
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1); 
            }
            button { 
                width: 100%; 
                background: #667eea; 
                color: white; 
                padding: 15px; 
                border: none; 
                border-radius: 10px; 
                cursor: pointer; 
                font-weight: 600; 
                margin-top: 20px; 
                font-size: 16px; 
                transition: 0.3s; 
            }
            button:hover { 
                background: #764ba2; 
                transform: translateY(-2px); 
            }
            .alert { 
                padding: 15px; 
                margin-bottom: 20px; 
                border-radius: 8px; 
                font-weight: 600; 
            }
            .success { 
                background: #d4edda; 
                color: #155724; 
                border-left: 4px solid #28a745; 
            }
            .error { 
                background: #f8d7da; 
                color: #721c24; 
                border-left: 4px solid #dc3545; 
            }
            .recent-transactions { 
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); 
                padding: 20px; 
                border-radius: 15px; 
                margin-top: 30px; 
            }
            table { 
                width: 100%; 
                border-collapse: collapse; 
                margin-top: 15px; 
                background: white; 
                border-radius: 10px; 
                overflow: hidden; 
            }
            th { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 12px; 
                text-align: left; 
                font-size: 13px; 
                font-weight: 600; 
            }
            td { 
                padding: 10px 12px; 
                border-bottom: 1px solid #e2e8f0; 
                font-size: 13px; 
            }
            tbody tr:hover { 
                background: #f7fafc; 
            }
            .btn-delete { 
                background: #dc3545; 
                color: white; 
                padding: 6px 12px; 
                border-radius: 6px; 
                font-size: 14px; 
                width: auto; 
                margin: 0; 
                border: none;
                cursor: pointer;
            }
            .btn-delete:hover { 
                background: #c82333; 
                transform: scale(1.05); 
            }
            .btn-reset-all { 
                background: #dc3545; 
                color: white; 
                padding: 8px 16px; 
                border-radius: 8px; 
                font-size: 13px; 
                font-weight: 600; 
                border: none; 
                cursor: pointer; 
                transition: 0.3s; 
                width: auto; 
                margin: 10px 0 0 0; 
            }
            .btn-reset-all:hover { 
                background: #c82333; 
                transform: translateY(-2px); 
                box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3); 
            }
            .empty-state { 
                text-align: center; 
                padding: 30px; 
                color: #999; 
                font-style: italic; 
            }
            .btn-back { 
                display: inline-block; 
                margin-top: 20px; 
                background: #6c757d; 
                color: white; 
                padding: 10px 20px; 
                border-radius: 8px; 
                text-decoration: none; 
                font-weight: 600; 
                transition: 0.3s; 
                width: auto; 
            }
            .btn-back:hover { 
                background: #5a6268; 
            }
            .back-section { 
                text-align: center; 
                margin-top: 20px; 
                padding-top: 20px; 
                border-top: 2px solid #e2e8f0; 
            }
        </style>
        <script>
            function hitungTotal() {
                const akunSelect = document.getElementById('akun-penjualan');
                const kuantitasInput = document.getElementById('kuantitas');
                const totalBox = document.getElementById('total-penjualan');
                const detailHitung = document.getElementById('detail-hitung');
                
                const kuantitas = parseFloat(kuantitasInput.value) || 0;
                const namaAkun = akunSelect.options[akunSelect.selectedIndex].text;
                
                let harga = 0;
                let jenisLabel = '';
                
                // Deteksi jenis belut dari nama akun
                if (namaAkun.includes('Super')) { 
                    harga = 65000;
                    jenisLabel = 'Belut Super';
                } else if (namaAkun.includes('Standar')) { 
                    harga = 50000;
                    jenisLabel = 'Belut Standar';
                }
                
                const total = kuantitas * harga;
                
                // Update tampilan total
                if (total > 0 && jenisLabel) {
                    totalBox.innerHTML = '💰 TOTAL: <span style="font-size:24px;">Rp ' + total.toLocaleString('id-ID') + '</span>';
                    detailHitung.innerHTML = '📊 ' + jenisLabel + ': ' + kuantitas + ' kg × Rp ' + harga.toLocaleString('id-ID') + '/kg';
                    detailHitung.style.display = 'block';
                } else {
                    totalBox.innerHTML = '💰 TOTAL: <span style="font-size:24px;">Rp 0</span>';
                    detailHitung.style.display = 'none';
                }
            }
            
            // Jalankan perhitungan saat halaman load jika ada nilai default
            window.onload = function() {
                hitungTotal();
            };
        </script>
    </head>
    <body>
        <div class="container">
            <h2>💰 Transaksi Penjualan</h2>
            
            {% if success_msg %}
            <div class="alert success">{{ success_msg }}</div>
            {% endif %}
            
            {% if error_msg %}
            <div class="alert error">{{ error_msg }}</div>
            {% endif %}
            
            <div class="info-box">
                📋 <strong>Harga:</strong> Belut Super = Rp 65.000/kg | Belut Standar = Rp 50.000/kg
            </div>
            
            <form method="POST">
                <label>Tanggal *</label>
                <input type="date" name="tanggal" required>
                
                <label>Jenis Belut *</label>
                <select name="akun" id="akun-penjualan" required onchange="hitungTotal()">
                    <option value="">-- Pilih Jenis Belut --</option>
                    {{ options_penjualan|safe }}
                </select>
                
                <label>Metode Pembayaran *</label>
                <select name="metode" required>
                    <option value="Tunai">Tunai (Kas)</option>
                    <option value="Transfer">Transfer (Kas di Bank)</option>
                    <option value="Kredit">Kredit (Piutang)</option>
                </select>
                
                <label>Kuantitas (kg) *</label>
                <input type="number" name="kuantitas" id="kuantitas" step="0.01" min="0.01" required oninput="hitungTotal()" placeholder="Masukkan jumlah kg">
                
                <div class="detail-hitung" id="detail-hitung" style="display:none;"></div>
                <div class="total-box" id="total-penjualan">💰 TOTAL: <span style="font-size:24px;">Rp 0</span></div>
                
                <button type="submit">💾 Simpan Transaksi Penjualan</button>
            </form>
            
            <div class="recent-transactions">
                <h3>📋 Transaksi Terakhir</h3>
                {% if recent_rows %}
                <table>
                    <thead>
                        <tr>
                            <th>Tanggal</th>
                            <th>Akun</th>
                            <th style="text-align:right;">Debit</th>
                            <th style="text-align:right;">Kredit</th>
                            <th style="text-align:center; width:80px;">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {{ recent_rows|safe }}
                    </tbody>
                </table>
                <form method="POST" style="margin-top:15px;" onsubmit="return confirm('⚠️ PERHATIAN: Hapus SEMUA transaksi penjualan?');">
                    <input type="hidden" name="action" value="reset_all">
                    <button type="submit" class="btn-reset-all">🗑️ Hapus Semua Transaksi Penjualan</button>
                </form>
                {% else %}
                <div class="empty-state">Belum ada transaksi penjualan</div>
                {% endif %}
            </div>
            
            <div class="back-section">
                <a href="/transaksi" class="btn-back">⬅ Kembali ke Menu Transaksi</a>
            </div>
        </div>
    </body>
    </html>
    """, options_penjualan=options_penjualan, success_msg=success_msg, error_msg=error_msg, recent_rows=recent_rows)
@app.route("/transaksi/pembelian", methods=["GET", "POST"])
def transaksi_pembelian():
    if not session.get("user_email"):
        return redirect("/")

    success_msg = ""
    error_msg = ""

    akun_kas = next(a for a in DAFTAR_AKUN if a["nama"] == "Kas")
    akun_kas_bank = next(a for a in DAFTAR_AKUN if a["nama"] == "Kas di Bank")
    akun_utang = next(a for a in DAFTAR_AKUN if a["nama"] == "Utang Dagang")
    
    # Hanya pembelian bibit dan pakan
    akun_pembelian = [a for a in DAFTAR_AKUN if a["kategori"] == "Pembelian"]

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "delete":
            try:
                entry_id = request.form.get("entry_id")
                supabase.table("general_journal").delete().eq("id", entry_id).execute()
                success_msg = "✅ Transaksi berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        elif action == "reset_all":
            try:
                supabase.table("general_journal").delete().like("description", "%Pembelian%").execute()
                success_msg = "✅ Semua transaksi pembelian berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        else:
            try:
                akun_kode = request.form.get("akun", "")
                tanggal = request.form.get("tanggal", "")
                metode = request.form.get("metode", "")
                nominal = float(request.form.get("nominal", 0))

                if not tanggal or not akun_kode:
                    error_msg = "⚠ Lengkapi semua field!"
                elif nominal <= 0:
                    error_msg = "⚠ Nominal harus lebih dari 0!"
                else:
                    akun = next(a for a in DAFTAR_AKUN if a["kode"] == akun_kode)
                    
                    if metode == "Tunai":
                        kredit = akun_kas
                    elif metode == "Transfer":
                        kredit = akun_kas_bank
                    else:
                        kredit = akun_utang
                    
                    debit = akun
                    keterangan = f"Pembelian {akun['nama']} ({metode})"
                    simpan_jurnal_auto(keterangan, tanggal, debit, kredit, nominal)
                    success_msg = f"✅ Transaksi Pembelian berhasil disimpan!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"

    try:
        res = supabase.table("general_journal").select("*").like("description", "%Pembelian%").order("date.desc,id.desc").limit(5).execute()
        recent_transactions = res.data or []
    except:
        recent_transactions = []

    recent_rows = ""
    for trx in recent_transactions:
        lines = trx.get('lines', [])
        for idx, line in enumerate(lines):
            account_code = line.get('account_code', '')
            account_name = next((a["nama"] for a in DAFTAR_AKUN if a["kode"] == account_code), account_code)
            debit = rupiah_small(line.get('debit', 0))
            kredit = rupiah_small(line.get('credit', 0))
            
            if idx == 0:
                recent_rows += f"""
                <tr>
                    <td rowspan="{len(lines)}" style="vertical-align:top;">{trx.get('date')}</td>
                    <td style="padding-left:15px;">{account_name}</td>
                    <td style="text-align:right;">{debit}</td>
                    <td style="text-align:right;">{kredit}</td>
                    <td rowspan="{len(lines)}" style="text-align:center; vertical-align:middle;">
                        <form method="POST" style="display:inline;" onsubmit="return confirm('Hapus transaksi ini?');">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="entry_id" value="{trx.get('id')}">
                            <button type="submit" class="btn-delete">🗑</button>
                        </form>
                    </td>
                </tr>
                """
            else:
                recent_rows += f"""
                <tr>
                    <td style="padding-left:30px;">{account_name}</td>
                    <td style="text-align:right;">{debit}</td>
                    <td style="text-align:right;">{kredit}</td>
                </tr>
                """
        
        recent_rows += f"""
        <tr style="background:#f9fafb;">
            <td colspan="4" style="padding-left:15px; font-style:italic; color:#666; font-size:12px;">
                <em>{trx.get('description')}</em>
            </td>
        </tr>
        """

    options_pembelian = "".join([f"<option value='{a['kode']}'>{a['nama']}</option>" for a in akun_pembelian])

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transaksi Pembelian</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin:0; padding:0; box-sizing:border-box; }
            body { font-family:'Poppins',sans-serif; background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); min-height:100vh; padding:20px; }
            .container { max-width:900px; margin:40px auto; background:white; padding:40px; border-radius:20px; box-shadow:0 15px 50px rgba(0,0,0,0.3); }
            h2 { color:#667eea; text-align:center; margin-bottom:30px; font-size:32px; }
            h3 { color:#2d3748; margin:0; font-size:20px; }
            label { font-weight:600; display:block; margin:15px 0 8px; color:#2d3748; }
            input, select { width:100%; padding:12px; border-radius:8px; border:1px solid #ddd; box-sizing:border-box; font-family:'Poppins',sans-serif; }
            input:focus, select:focus { outline:none; border-color:#667eea; box-shadow:0 0 0 3px rgba(102,126,234,0.1); }
            button { width:100%; background:#667eea; color:white; padding:15px; border:none; border-radius:10px; cursor:pointer; font-weight:600; margin-top:20px; font-size:16px; transition:0.3s; }
            button:hover { background:#764ba2; transform:translateY(-2px); }
            .alert { padding:15px; margin-bottom:20px; border-radius:8px; font-weight:600; }
            .success { background:#d4edda; color:#155724; border-left:4px solid #28a745; }
            .error { background:#f8d7da; color:#721c24; border-left:4px solid #dc3545; }
            .recent-transactions { background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%); padding:20px; border-radius:15px; margin-top:30px; }
            table { width:100%; border-collapse:collapse; margin-top:15px; background:white; border-radius:10px; overflow:hidden; }
            th { background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); color:white; padding:12px; text-align:left; font-size:13px; font-weight:600; }
            td { padding:10px 12px; border-bottom:1px solid #e2e8f0; font-size:13px; }
            tbody tr:hover { background:#f7fafc; }
            .btn-delete { background:#dc3545; color:white; padding:6px 12px; border-radius:6px; font-size:14px; width:auto; margin:0; }
            .btn-delete:hover { background:#c82333; transform:scale(1.05); }
            .btn-reset-all { background:#dc3545; color:white; padding:8px 16px; border-radius:8px; font-size:13px; font-weight:600; border:none; cursor:pointer; transition:0.3s; width:auto; margin:10px 0 0 0; }
            .btn-reset-all:hover { background:#c82333; transform:translateY(-2px); box-shadow:0 4px 12px rgba(220,53,69,0.3); }
            .empty-state { text-align:center; padding:30px; color:#999; font-style:italic; }
            .btn-back { display:inline-block; margin-top:20px; background:#6c757d; color:white; padding:10px 20px; border-radius:8px; text-decoration:none; font-weight:600; transition:0.3s; width:auto; }
            .btn-back:hover { background:#5a6268; }
            .back-section { text-align:center; margin-top:20px; padding-top:20px; border-top:2px solid #e2e8f0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🛒 Transaksi Pembelian</h2>
            {% if success_msg %}<div class="alert success">{{ success_msg }}</div>{% endif %}
            {% if error_msg %}<div class="alert error">{{ error_msg }}</div>{% endif %}
            <form method="POST">
                <label>Tanggal *</label>
                <input type="date" name="tanggal" required>
                <label>Jenis Pembelian *</label>
                <select name="akun" required>
                    <option value="">-- Pilih Jenis Pembelian --</option>
                    {{ options_pembelian|safe }}
                </select>
                <label>Metode Pembayaran *</label>
                <select name="metode" required>
                    <option value="Tunai">Tunai (Kas)</option>
                    <option value="Transfer">Transfer (Kas di Bank)</option>
                    <option value="Kredit">Kredit (Utang)</option>
                </select>
                <label>Nominal (Rp) *</label>
                <input type="number" name="nominal" step="0.01" min="1" required>
                <button type="submit">💾 Simpan Transaksi Pembelian</button>
            </form>
            <div class="recent-transactions">
            </div>
            <div class="back-section"><a href="/transaksi" class="btn-back">⬅ Kembali ke Menu Transaksi</a></div>
        </div>
    </body>
    </html>
    """, options_pembelian=options_pembelian, success_msg=success_msg, error_msg=error_msg, recent_rows=recent_rows)

@app.route("/transaksi/lainnya", methods=["GET", "POST"])
def transaksi_lainnya():
    if not session.get("user_email"):
        return redirect("/")

    success_msg = ""
    error_msg = ""

    # Tambahkan akun Beban Listrik dan Air jika belum ada
    beban_listrik_air = {
        "kode": "6-1100",
        "nama": "Beban Listrik dan Air",
        "kategori": "Beban"
    }
    
    # Cek apakah akun sudah ada di DAFTAR_AKUN
    if not any(a["kode"] == "6-1100" for a in DAFTAR_AKUN):
        DAFTAR_AKUN.append(beban_listrik_air)

    # Akun untuk transaksi lainnya - SEMUA akun termasuk Kas, Kas di Bank, Piutang
    akun_lainnya = [a for a in DAFTAR_AKUN if a["kategori"] in ["Aset", "Liabilitas", "Ekuitas", 
                    "Biaya", "Beban", "Pendapatan Lain", "Beban Lain"] 
                    and "Persediaan" not in a["nama"]
                    and "Penjualan Belut" not in a["nama"]]

    if request.method == "POST":
        action = request.form.get("action")
        
        if action == "delete":
            try:
                entry_id = request.form.get("entry_id")
                supabase.table("general_journal").delete().eq("id", entry_id).execute()
                success_msg = "✅ Transaksi berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        elif action == "reset_all":
            try:
                supabase.table("general_journal").delete().like("description", "%Lainnya%").execute()
                success_msg = "✅ Semua transaksi lainnya berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        else:
            try:
                akun_debit_kode = request.form.get("akun_debit", "")
                akun_kredit_kode = request.form.get("akun_kredit", "")
                tanggal = request.form.get("tanggal", "")
                nominal = float(request.form.get("nominal", 0))
                keterangan = request.form.get("keterangan", "")

                if not tanggal or not akun_debit_kode or not akun_kredit_kode:
                    error_msg = "⚠ Lengkapi semua field!"
                elif nominal <= 0:
                    error_msg = "⚠ Nominal harus lebih dari 0!"
                elif akun_debit_kode == akun_kredit_kode:
                    error_msg = "⚠ Akun debit dan kredit tidak boleh sama!"
                else:
                    akun_debit = next(a for a in DAFTAR_AKUN if a["kode"] == akun_debit_kode)
                    akun_kredit = next(a for a in DAFTAR_AKUN if a["kode"] == akun_kredit_kode)
                    
                    if not keterangan:
                        keterangan = f"Transaksi Lainnya: {akun_debit['nama']} ke {akun_kredit['nama']}"
                    else:
                        keterangan = f"Transaksi Lainnya: {keterangan}"
                    
                    simpan_jurnal_auto(keterangan, tanggal, akun_debit, akun_kredit, nominal)
                    success_msg = f"✅ Transaksi berhasil disimpan! Total: {rupiah_small(nominal)}"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"

    try:
        res = supabase.table("general_journal").select("*").like("description", 
        "%Lainnya%").order("date.desc,id.desc").limit(5).execute()
        recent_transactions = res.data or []
    except:
        recent_transactions = []

    recent_rows = ""
    for trx in recent_transactions:
        lines = trx.get('lines', [])
        for idx, line in enumerate(lines):
            account_code = line.get('account_code', '')
            account_name = next((a["nama"] for a in DAFTAR_AKUN if a["kode"] == account_code), account_code)
            debit = rupiah_small(line.get('debit', 0))
            kredit = rupiah_small(line.get('credit', 0))
            
            if idx == 0:
                recent_rows += f"""
                <tr>
                    <td rowspan="{len(lines)}" style="vertical-align:top;">{trx.get('date')}</td>
                    <td style="padding-left:15px;">{account_name}</td>
                    <td style="text-align:right;">{debit}</td>
                    <td style="text-align:right;">{kredit}</td>
                    <td rowspan="{len(lines)}" style="text-align:center; vertical-align:middle;">
                        <form method="POST" style="display:inline;" onsubmit="return confirm('Hapus transaksi ini?');">
                            <input type="hidden" name="action" value="delete">
                            <input type="hidden" name="entry_id" value="{trx.get('id')}">
                            <button type="submit" class="btn-delete">🗑</button>
                        </form>
                    </td>
                </tr>
                """
            else:
                recent_rows += f"""
                <tr>
                    <td style="padding-left:30px;">{account_name}</td>
                    <td style="text-align:right;">{debit}</td>
                    <td style="text-align:right;">{kredit}</td>
                </tr>
                """
        
        recent_rows += f"""
        <tr style="background:#f9fafb;">
            <td colspan="4" style="padding-left:15px; font-style:italic; color:#666; font-size:12px;">
                <em>{trx.get('description')}</em>
            </td>
        </tr>
        """

    # Group akun berdasarkan kategori untuk dropdown
    options_html = ""
    categories = {}
    for akun in akun_lainnya:
        kat = akun["kategori"]
        if kat not in categories:
            categories[kat] = []
        categories[kat].append(akun)
    
    for kat, akuns in sorted(categories.items()):
        options_html += f"<optgroup label='{kat}'>"
        for akun in akuns:
            options_html += f"<option value='{akun['kode']}'>{akun['nama']}</option>"
        options_html += "</optgroup>"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transaksi Lainnya</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin:0; padding:0; box-sizing:border-box; }
            body { 
                font-family:'Poppins',sans-serif; 
                background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); 
                min-height:100vh; 
                padding:20px; 
            }
            .container { 
                max-width:900px; 
                margin:40px auto; 
                background:white; 
                padding:40px; 
                border-radius:20px; 
                box-shadow:0 15px 50px rgba(0,0,0,0.3); 
            }
            h2 { 
                color:#667eea; 
                text-align:center; 
                margin-bottom:30px; 
                font-size:32px; 
            }
            h3 { 
                color:#2d3748; 
                margin:30px 0 15px 0; 
                font-size:20px; 
            }
            .info-box { 
                background:#fff3cd; 
                padding:15px; 
                border-radius:10px; 
                margin-bottom:20px; 
                font-size:14px; 
                border-left:4px solid #ffc107; 
            }
            label { 
                font-weight:600; 
                display:block; 
                margin:15px 0 8px; 
                color:#2d3748; 
            }
            input, select, textarea { 
                width:100%; 
                padding:12px; 
                border-radius:8px; 
                border:1px solid #ddd; 
                box-sizing:border-box; 
                font-family:'Poppins',sans-serif;
                font-size:14px;
            }
            textarea { 
                min-height:80px; 
                resize:vertical; 
            }
            input:focus, select:focus, textarea:focus { 
                outline:none; 
                border-color:#667eea; 
                box-shadow:0 0 0 3px rgba(102,126,234,0.1); 
            }
            button { 
                width:100%; 
                background:#667eea; 
                color:white; 
                padding:15px; 
                border:none; 
                border-radius:10px; 
                cursor:pointer; 
                font-weight:600; 
                margin-top:20px; 
                font-size:16px; 
                transition:0.3s; 
            }
            button:hover { 
                background:#764ba2; 
                transform:translateY(-2px); 
            }
            .alert { 
                padding:15px; 
                margin-bottom:20px; 
                border-radius:8px; 
                font-weight:600; 
            }
            .success { 
                background:#d4edda; 
                color:#155724; 
                border-left:4px solid #28a745; 
            }
            .error { 
                background:#f8d7da; 
                color:#721c24; 
                border-left:4px solid #dc3545; 
            }
            .recent-transactions { 
                background:linear-gradient(135deg,#f5f7fa 0%,#c3cfe2 100%); 
                padding:20px; 
                border-radius:15px; 
                margin-top:30px; 
            }
            table { 
                width:100%; 
                border-collapse:collapse; 
                margin-top:15px; 
                background:white; 
                border-radius:10px; 
                overflow:hidden; 
            }
            th { 
                background:linear-gradient(135deg,#667eea 0%,#764ba2 100%); 
                color:white; 
                padding:12px; 
                text-align:left; 
                font-size:13px; 
                font-weight:600; 
            }
            td { 
                padding:10px 12px; 
                border-bottom:1px solid #e2e8f0; 
                font-size:13px; 
            }
            tbody tr:hover { 
                background:#f7fafc; 
            }
            .btn-delete { 
                background:#dc3545; 
                color:white; 
                padding:6px 12px; 
                border-radius:6px; 
                font-size:14px; 
                width:auto; 
                margin:0;
                border:none;
                cursor:pointer;
            }
            .btn-delete:hover { 
                background:#c82333; 
                transform:scale(1.05); 
            }
            .btn-reset-all { 
                background:#dc3545; 
                color:white; 
                padding:8px 16px; 
                border-radius:8px; 
                font-size:13px; 
                font-weight:600; 
                border:none; 
                cursor:pointer; 
                transition:0.3s; 
                width:auto; 
                margin:10px 0 0 0; 
            }
            .btn-reset-all:hover { 
                background:#c82333; 
                transform:translateY(-2px); 
                box-shadow:0 4px 12px rgba(220,53,69,0.3); 
            }
            .empty-state { 
                text-align:center; 
                padding:30px; 
                color:#999; 
                font-style:italic; 
            }
            .btn-back { 
                display:inline-block; 
                margin-top:20px; 
                background:#6c757d; 
                color:white; 
                padding:10px 20px; 
                border-radius:8px; 
                text-decoration:none; 
                font-weight:600; 
                transition:0.3s; 
                width:auto; 
            }
            .btn-back:hover { 
                background:#5a6268; 
            }
            .back-section { 
                text-align:center; 
                margin-top:20px; 
                padding-top:20px; 
                border-top:2px solid #e2e8f0; 
            }
            .jurnal-hint { 
                background:#e7f3ff; 
                padding:12px; 
                border-radius:8px; 
                margin-top:15px; 
                font-size:13px; 
                border-left:4px solid #667eea; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📝 Transaksi Lainnya</h2>
            
            {% if success_msg %}
            <div class="alert success">{{ success_msg }}</div>
            {% endif %}
            
            {% if error_msg %}
            <div class="alert error">{{ error_msg }}</div>
            {% endif %}
            
            <div class="info-box">
                ⚠ <strong>Perhatian:</strong> Anda perlu menentukan akun Debit dan Kredit secara manual. 
                Pastikan sudah memahami prinsip jurnal akuntansi. Akun Kas, Kas di Bank, dan Piutang Dagang tersedia di dropdown.
            </div>
            
            <form method="POST">
                <label>Tanggal *</label>
                <input type="date" name="tanggal" required>
                
                <label>Akun Debit (D) *</label>
                <select name="akun_debit" required>
                    <option value="">-- Pilih Akun Debit --</option>
                    {{ options_html|safe }}
                </select>
                
                <label>Akun Kredit (K) *</label>
                <select name="akun_kredit" required>
                    <option value="">-- Pilih Akun Kredit --</option>
                    {{ options_html|safe }}
                </select>
                
                <label>Nominal (Rp) *</label>
                <input type="number" name="nominal" step="0.01" min="1" required placeholder="Masukkan nominal">
                
                <label>Keterangan (Opsional)</label>
                <textarea name="keterangan" placeholder="Contoh: Pembayaran listrik bulan Desember 2024"></textarea>
                
                <div class="jurnal-hint">
                    💡 <strong>Tips Jurnal:</strong><br>
                    • Beban/Aset bertambah = Debit<br>
                    • Pendapatan/Utang/Modal bertambah = Kredit<br>
                    • Contoh: Bayar listrik tunai → D: Beban Listrik dan Air, K: Kas<br>
                    • Terima piutang → D: Kas, K: Piutang Dagang
                </div>
                
                <button type="submit">💾 Simpan Transaksi</button>
            </form>
            
            <div class="recent-transactions">
                <h3>📋 Transaksi Terakhir</h3>
                {% if recent_rows %}
                <table>
                    <thead>
                        <tr>
                            <th>Tanggal</th>
                            <th>Akun</th>
                            <th style="text-align:right;">Debit</th>
                            <th style="text-align:right;">Kredit</th>
                            <th style="text-align:center; width:80px;">Aksi</th>
                        </tr>
                    </thead>
                    <tbody>
                        {{ recent_rows|safe }}
                    </tbody>
                </table>
                <form method="POST" style="margin-top:15px;" onsubmit="return confirm('⚠️ PERHATIAN: Hapus SEMUA transaksi lainnya?');">
                    <input type="hidden" name="action" value="reset_all">
                    <button type="submit" class="btn-reset-all">🗑️ Hapus Semua Transaksi Lainnya</button>
                </form>
                {% else %}
                <div class="empty-state">Belum ada transaksi lainnya</div>
                {% endif %}
            </div>
            
            <div class="back-section">
                <a href="/transaksi" class="btn-back">⬅ Kembali ke Menu Transaksi</a>
            </div>
        </div>
    </body>
    </html>
    """, options_html=options_html, success_msg=success_msg, error_msg=error_msg, recent_rows=recent_rows)
@app.route("/informasi-produk")
def informasi_produk():
    if not session.get("user_email"):
        return redirect("/")
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Informasi Produk - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1200px; 
                margin: 40px auto; 
            }
            .header {
                text-align: center;
                color: white;
                margin-bottom: 50px;
            }
            .header h1 { 
                font-size: 42px; 
                margin-bottom: 15px;
                text-shadow: 0 4px 10px rgba(0,0,0,0.2);
            }
            .header p { 
                opacity: 0.95; 
                font-size: 18px; 
            }
            .products {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(450px, 1fr));
                gap: 40px;
                margin-bottom: 40px;
            }
            .product-card {
                background: white;
                border-radius: 25px;
                padding: 40px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            .product-card:hover { 
                transform: translateY(-10px); 
                box-shadow: 0 20px 60px rgba(0,0,0,0.4);
            }
            .product-card::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 6px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .product-image {
                text-align: center;
                margin-bottom: 30px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 20px;
                padding: 30px;
            }
            .product-image img {
                width: 200px;
                height: 200px;
                object-fit: contain;
                filter: drop-shadow(0 4px 15px rgba(0,0,0,0.1));
            }
            .product-title {
                font-size: 32px;
                font-weight: 700;
                color: #667eea;
                margin-bottom: 20px;
                text-align: center;
            }
            .product-price {
                font-size: 28px;
                font-weight: 700;
                color: #2d3748;
                text-align: center;
                background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 25px;
                padding: 15px;
                background: #fff3cd;
                border-radius: 15px;
                border-left: 5px solid #ffc107;
            }
            .product-description {
                color: #4a5568;
                line-height: 1.8;
                font-size: 15px;
                margin-bottom: 20px;
            }
            .product-features {
                background: #f7fafc;
                padding: 20px;
                border-radius: 15px;
                margin-top: 20px;
            }
            .product-features h4 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 18px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .product-features ul {
                list-style: none;
                padding: 0;
            }
            .product-features li {
                padding: 8px 0;
                padding-left: 25px;
                position: relative;
                color: #4a5568;
                font-size: 14px;
            }
            .product-features li:before {
                content: '✓';
                position: absolute;
                left: 0;
                color: #48bb78;
                font-weight: bold;
                font-size: 16px;
            }
            .badge {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 8px 20px;
                border-radius: 20px;
                font-size: 13px;
                font-weight: 600;
                margin-top: 15px;
            }
            .comparison {
                background: white;
                border-radius: 25px;
                padding: 40px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
                margin-bottom: 40px;
            }
            .comparison h2 {
                text-align: center;
                color: #667eea;
                font-size: 32px;
                margin-bottom: 30px;
            }
            .comparison-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            .comparison-table th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }
            .comparison-table td {
                padding: 15px;
                border-bottom: 1px solid #e2e8f0;
                color: #4a5568;
            }
            .comparison-table tr:hover {
                background: #f7fafc;
            }
            .back-btn { 
                text-align: center; 
                margin-top: 40px; 
            }
            .back-btn a {
                display: inline-block;
                background: white;
                color: #667eea;
                padding: 15px 35px;
                border-radius: 15px;
                text-decoration: none;
                font-weight: 600;
                font-size: 16px;
                transition: 0.3s;
                box-shadow: 0 5px 20px rgba(0,0,0,0.2);
            }
            .back-btn a:hover { 
                transform: translateY(-3px); 
                box-shadow: 0 8px 25px rgba(0,0,0,0.3); 
            }
            @media (max-width: 768px) {
                .products {
                    grid-template-columns: 1fr;
                }
                .header h1 {
                    font-size: 32px;
                }
                .product-title {
                    font-size: 26px;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1> Informasi Produk Belut</h1>
                <p>Belut Berkualitas Premium dari Djong Java</p>
            </div>

            <div class="products">
                <!-- Belut Standar -->
                <div class="product-card">
                    <div class="product-image">
                        <img src="/static/belut_standar.png" alt="Belut Standar">
                    </div>
                    <div class="product-title">Belut Standar</div>
                    <div class="product-price">💰 Rp 50.000 / kg</div>
                    <div class="product-description">
                        <strong>Belut Standar</strong> merupakan produk belut pilihan dengan kualitas baik yang cocok untuk konsumsi rumah tangga dan restoran. Belut dengan daging yang kenyal dan rasa yang lezat.
                    </div>
                    <div class="product-features">
                        <h4>✨ Keunggulan Produk</h4>
                        <ul>
                            <li>Daging kenyal dan segar</li>
                            <li>Harga ekonomis dan terjangkau</li>
                            <li>Cocok untuk berbagai olahan masakan</li>
                            <li>Dipelihara dengan pakan berkualitas</li>
                            <li>Bebas bau lumpur dan bersih</li>
                        </ul>
                    </div>
                    <span class="badge">🌟 Best Seller</span>
                </div>

                <!-- Belut Super -->
                <div class="product-card">
                    <div class="product-image">
                        <img src="/static/belut_super.png" alt="Belut Super">
                    </div>
                    <div class="product-title">Belut Super</div>
                    <div class="product-price">💎 Rp 65.000 / kg</div>
                    <div class="product-description">
                        <strong>Belut Super</strong> adalah produk belut premium dengan kualitas terbaik. Memiliki daging yang lebih tebal dibandingkan belut standar. Sangat cocok untuk hidangan spesial dan acara penting.
                    </div>
                    <div class="product-features">
                        <h4>✨ Keunggulan Produk</h4>
                        <ul>
                            <li>Daging super tebal dan berkualitas premium</li>
                            <li>Kandungan protein lebih tinggi</li>
                            <li>Rasa lebih gurih dan lezat</li>
                            <li>Dipelihara dengan pakan khusus premium</li>
                            <li>Proses sortir ketat untuk kualitas terbaik</li>
                            <li>Cocok untuk hidangan mewah dan restoran bintang</li>
                        </ul>
                    </div>
                    <span class="badge">👑 Premium Quality</span>
                </div>
            </div>

            <!-- Tabel Perbandingan -->
            <div class="comparison">
                <h2>📊 Perbandingan Produk</h2>
                <table class="comparison-table">
                    <thead>
                        <tr>
                            <th>Aspek</th>
                            <th>Belut Standar</th>
                            <th>Belut Super</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td><strong>Harga per Kg</strong></td>
                            <td>Rp 50.000</td>
                            <td>Rp 65.000</td>
                        </tr>
                        <tr>
                            <td><strong>Ketebalan Daging</strong></td>
                            <td>Sedang</td>
                            <td>Tebal & Premium</td>
                        </tr>
                        <tr>
                            <td><strong>Kualitas</strong></td>
                            <td>Baik</td>
                            <td>Premium</td>
                        </tr>
                        <tr>
                            <td><strong>Pakan</strong></td>
                            <td>Pakan Standar</td>
                            <td>Pakan Premium Khusus</td>
                        </tr>
                        <tr>
                            <td><strong>Kandungan Protein</strong></td>
                            <td>Tinggi</td>
                            <td>Sangat Tinggi</td>
                        </tr>
                        <tr>
                            <td><strong>Cocok Untuk</strong></td>
                            <td>Konsumsi rumah tangga, warung</td>
                            <td>Restoran premium, acara spesial</td>
                        </tr>
                        <tr>
                            <td><strong>Target Market</strong></td>
                            <td>Pasar umum</td>
                            <td>Pasar premium & export</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="back-btn">
                <a href="/dashboard">⬅ Kembali ke Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content
@app.route("/jurnal")
def jurnal():
    # Cek apakah user sudah login
    if not session.get("user_email"):
        return redirect("/")

    # Ambil semua data jurnal
    data = ambil_semua_jurnal()

    # Inisialisasi variabel untuk tabel
    rows = ""
    total_debit = 0
    total_kredit = 0

    # Bangun baris tabel dan hitung total debit/kredit
    for d in data:
        rows += f"""
        <tr>
            <td>{d['tanggal']}</td>
            <td>{d['kode']}</td>
            <td>{d['akun']}</td>
            <td>{d['keterangan']}</td>
            <td style='text-align:right;'>{rupiah_small(d['debit'])}</td>
            <td style='text-align:right;'>{rupiah_small(d['kredit'])}</td>
        </tr>
        """
        total_debit += d['debit']
        total_kredit += d['kredit']

    # Buat tabel HTML
    if data:
        tabel_html = f"""
        <table>
            <thead>
                <tr>
                    <th>Tanggal</th>
                    <th>Kode Akun</th>
                    <th>Nama Akun</th>
                    <th>Keterangan</th>
                    <th style="text-align:right;">Debit</th>
                    <th style="text-align:right;">Kredit</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
            <tfoot>
                <tr>
                    <td colspan="4" style="text-align:right;">TOTAL</td>
                    <td style="text-align:right;">{rupiah_small(total_debit)}</td>
                    <td style="text-align:right;">{rupiah_small(total_kredit)}</td>
                </tr>
            </tfoot>
        </table>
        """
    else:
        tabel_html = """
        <div class="empty-state">
            <p style="font-size:48px;">📭</p>
            <h3>Belum Ada Jurnal</h3>
            <p>Silakan input transaksi terlebih dahulu</p>
        </div>
        """

    # Render halaman dengan semua data
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Jurnal Umum - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .info-box {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }
            .info-box p {
                color: #2d3748;
                font-size: 14px;
                margin: 5px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-radius: 12px;
                overflow: hidden;
            }
            thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e2e8f0;
                color: #2d3748;
            }
            tbody tr:hover { background: #f7fafc; }
            tfoot { background: #f7fafc; font-weight: 700; }
            tfoot td {
                padding: 15px;
                font-size: 16px;
                border-top: 3px solid #667eea;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .empty-state {
                text-align: center;
                padding: 60px 20px;
                color: #718096;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📘 Jurnal Umum</h2>

            <div class="info-box">
                <p><strong>Total Transaksi:</strong> {{ jumlah_entri }} entri</p>
                <p><strong>Total Debit:</strong> {{ total_debit }} | <strong>Total Kredit:</strong> {{ total_kredit }}</strong></p>
            </div>

            {{ tabel_html|safe }}

            <div class="back-section">
                <a href="/akuntansi">⬅  Kembali ke Menu Akuntansi</a>
            </div>

        </div>
    </body>
    </html>
    """,
    tabel_html=tabel_html,
    jumlah_entri=len(data),
    total_debit=rupiah_small(total_debit),
    total_kredit=rupiah_small(total_kredit)
    )

@app.route("/neraca_saldo")
def neraca_saldo():
    if not session.get("user_email"):
        return redirect("/")
    
    akun_dict = get_akun_dict()
    
    neraca_html = ""
    total_debit = 0
    total_kredit = 0

    for k, v in sorted(akun_dict.items()):
        # Hitung saldo = total_debit - total_kredit
        saldo = v['total_debit'] - v['total_kredit']
        
        # Tentukan posisi saldo (debit atau kredit)
        if saldo > 0:
            # Saldo Debit
            debit_display = rupiah_small(saldo)
            kredit_display = rupiah_small(0)
            total_debit += saldo
        elif saldo < 0:
            # Saldo Kredit (saldo negatif berarti kredit)
            debit_display = rupiah_small(0)
            kredit_display = rupiah_small(abs(saldo))
            total_kredit += abs(saldo)
        else:
            # Saldo 0
            debit_display = rupiah_small(0)
            kredit_display = rupiah_small(0)
        
        neraca_html += f"""
        <tr>
            <td>{k}</td>
            <td>{v['akun']}</td>
            <td style='text-align:right;'>{debit_display}</td>
            <td style='text-align:right;'>{kredit_display}</td>
        </tr>
        """
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Neraca Saldo</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .info-box {
                background: #e7f3ff;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                font-size: 14px;
                border-left: 4px solid #667eea;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
            }
            td {
                padding: 12px;
                border-bottom: 1px solid #e2e8f0;
            }
            tbody tr:hover {
                background: #f7fafc;
            }
            tfoot {
                background: #e3f2fd;
                font-weight: 700;
            }
            tfoot td {
                padding: 15px;
                border-top: 3px solid #667eea;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .btn-back {
                display: inline-block;
                padding: 12px 25px;
                background: #667eea;
                color: white;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-back:hover {
                background: #764ba2;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>⚖ Neraca Saldo</h2>
            
            <div class="info-box">
                💡 <strong>Info:</strong> Neraca saldo menampilkan saldo akhir setiap akun (Debit - Kredit).
                Total Debit harus sama dengan Total Kredit untuk memastikan keseimbangan pembukuan.
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Kode Akun</th>
                        <th>Nama Akun</th>
                        <th style="text-align:right;">Debit</th>
                        <th style="text-align:right;">Kredit</th>
                    </tr>
                </thead>
                <tbody>
                    {{ neraca_html|safe }}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2" style="text-align:right;"><strong>TOTAL</strong></td>
                        <td style="text-align:right;"><strong>{{ total_debit }}</strong></td>
                        <td style="text-align:right;"><strong>{{ total_kredit }}</strong></td>
                    </tr>
                </tfoot>
            </table>
            <div class="back-section">
                <a href="/akuntansi" class="btn-back">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """, neraca_html=neraca_html, total_debit=rupiah_small(total_debit), total_kredit=rupiah_small(total_kredit))
@app.route("/akuntansi")
def akuntansi():
    if not session.get("user_email"):
        return redirect("/")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Menu Akuntansi - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .menu-list {
                list-style: none;
                padding: 0;
            }
            .menu-list li {
                margin: 15px 0;
            }
            .menu-list a {
                display: block;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 12px;
                text-decoration: none;
                color: #2d3748;
                font-weight: 600;
                font-size: 16px;
                transition: 0.3s;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            .menu-list a:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .btn-back {
                display: inline-block;
                margin-top: 30px;
                background: #667eea;
                color: white;
                padding: 12px 25px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-back:hover {
                background: #764ba2;
                transform: translateY(-2px);
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📚 Menu Akuntansi</h2>
            <ul class="menu-list">
                <li><a href="/jurnal">📘 Jurnal Umum</a></li>
                <li><a href="/neraca_saldo">⚖ Neraca Saldo Sebelum Penyesuaian</a></li>
                <li><a href="/jurnal_penyesuaian">🔄 Jurnal Penyesuaian</a></li>
                <li><a href="/neraca_saldo_setelah_penyesuaian">⚖ Neraca Saldo Setelah Penyesuaian</a></li>
                <li><a href="/laporan">📊 Laporan Keuangan</a></li>
                <li><a href="/jurnal_penutup">📕 Jurnal Penutup</a></li>
                <li><a href="/buku_besar">📗 Buku Besar</a></li>
                <li><a href="/neraca_saldo_penutup">⚖ Neraca Saldo Setelah Penutup</a></li>
            </ul>
            </ul>
            <div class="back-section">
                <a href="/dashboard" class="btn-back">⬅ Kembali ke Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/histori", methods=["GET", "POST"])
def histori():
    if not session.get("user_email"):
        return redirect("/")

    user = session.get("user_email")
    success_msg = ""
    error_msg = ""

    if request.method == "POST":
        action = request.form.get("action")
        
        # Hapus satu transaksi
        if action == "delete":
            try:
                entry_id = request.form.get("entry_id")
                supabase.table("general_journal").delete().eq("id", entry_id).eq("user_email", user).execute()
                success_msg = "✅ Transaksi berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
        
        # Reset semua transaksi
        elif action == "reset_all":
            try:
                supabase.table("general_journal").delete().eq("user_email", user).execute()
                success_msg = "✅ Semua transaksi berhasil dihapus!"
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"

    # Ambil data transaksi
    res = supabase.table("general_journal").select("*") \
        .eq("user_email", user) \
        .order("date", desc=True) \
        .order("id", desc=True) \
        .execute()
    data = res.data or []

    rows = ""
    for j in data:
        tgl = j.get("date")
        desc = j.get("description")
        entry_id = j.get("id")
        lines = j.get("lines") or []
        if isinstance(lines, str):
            try:
                lines = json.loads(lines)
            except:
                lines = []
        
        summary = []
        for b in lines:
            # Cari nama akun dari account_code
            account_code = b.get('account_code', '')
            account_name = ''
            for akun in DAFTAR_AKUN:
                if akun['kode'] == account_code:
                    account_name = akun['nama']
                    break
            
            # Fallback jika tidak ketemu
            if not account_name:
                account_name = b.get("account_name") or account_code
            
            debit = b.get("debit") or 0
            kredit = b.get("credit") or 0
            summary.append(f"{account_name}: D {rupiah_small(debit)} / K {rupiah_small(kredit)}")
        
        rows += f"""
        <tr>
            <td>{tgl}</td>
            <td>{desc}</td>
            <td>{'<br>'.join(summary)}</td>
            <td style="text-align:center;">
                <form method="POST" style="display:inline;" onsubmit="return confirm('Hapus transaksi ini?');">
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="entry_id" value="{entry_id}">
                    <button type="submit" class="btn-delete">🗑</button>
                </form>
            </td>
        </tr>
        """

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Histori Transaksi - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container { 
                max-width: 1200px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 { 
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .alert {
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border-left: 4px solid #28a745;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border-left: 4px solid #dc3545;
            }
            .table-container {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 20px;
            }
            table { 
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 10px;
                overflow: hidden;
            }
            thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            th, td { 
                padding: 12px;
                text-align: left;
                font-size: 13px;
            }
            th {
                font-weight: 600;
            }
            td {
                border-bottom: 1px solid #e2e8f0;
            }
            tbody tr:hover { 
                background: #f7fafc;
            }
            .btn-delete {
                background: #dc3545;
                color: white;
                padding: 6px 12px;
                border-radius: 6px;
                border: none;
                cursor: pointer;
                font-size: 14px;
                transition: 0.3s;
            }
            .btn-delete:hover {
                background: #c82333;
                transform: scale(1.05);
            }
            .btn-reset-all {
                background: #dc3545;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                border: none;
                cursor: pointer;
                font-size: 14px;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-reset-all:hover {
                background: #c82333;
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(220, 53, 69, 0.3);
            }
            .reset-container {
                text-align: right;
                margin-top: 15px;
                padding-top: 15px;
                border-top: 2px solid #cbd5e0;
            }
            .btn-back {
                display: inline-block;
                margin-top: 20px;
                background: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-back:hover {
                background: #5a6268;
            }
            .back-section {
                text-align: center;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .empty-state {
                text-align: center;
                padding: 50px;
                color: #999;
                font-style: italic;
                font-size: 16px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🕘 Histori Transaksi</h2>
            
            {% if success_msg %}
                <div class="alert success">{{ success_msg }}</div>
            {% endif %}
            {% if error_msg %}
                <div class="alert error">{{ error_msg }}</div>
            {% endif %}
            
            <div class="table-container">
                {% if rows %}
                    <table>
                        <thead>
                            <tr>
                                <th style="width:15%;">Tanggal</th>
                                <th style="width:35%;">Keterangan</th>
                                <th style="width:40%;">Rincian</th>
                                <th style="width:10%; text-align:center;">Aksi</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{ rows|safe }}
                        </tbody>
                    </table>
                    
                    <!-- Tombol Reset di Pojok Kanan Bawah -->
                    <div class="reset-container">
                        <form method="POST" style="display:inline;" onsubmit="return confirm('⚠ PERINGATAN!\\n\\nAnda akan menghapus SEMUA transaksi.\\nTindakan ini TIDAK BISA dibatalkan!\\n\\nLanjutkan?');">
                            <input type="hidden" name="action" value="reset_all">
                            <button type="submit" class="btn-reset-all">🗑 Reset Semua Transaksi</button>
                        </form>
                    </div>
                {% else %}
                    <div class="empty-state">
                        📭 Belum ada histori transaksi
                    </div>
                {% endif %}
            </div>
            
            <div class="back-section">
                <a href="/dashboard" class="btn-back">⬅ Kembali ke Dashboard</a>
            </div>
        </div>
    </body>
    </html>
    """, rows=rows, success_msg=success_msg, error_msg=error_msg)

@app.route("/laporan")
def laporan():
    if not session.get("user_email"):
        return redirect("/")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Menu Laporan Keuangan</title>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 900px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .menu-list {
                list-style: none;
                padding: 0;
            }
            .menu-list li {
                margin: 15px 0;
            }
            .menu-list a {
                display: block;
                padding: 20px;
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                border-radius: 12px;
                text-decoration: none;
                color: #2d3748;
                font-weight: 600;
                font-size: 16px;
                transition: 0.3s;
                box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            }
            .menu-list a:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(0,0,0,0.15);
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .btn-back {
                display: inline-block;
                padding: 12px 25px;
                background: #667eea;
                color: white;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-back:hover {
                background: #764ba2;
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 Menu Laporan Keuangan</h2>
            <ul class="menu-list">
                <li><a href="/laporan_laba_rugi">💰 Laporan Laba Rugi</a></li>
                <li><a href="/laporan_perubahan_modal">💼 Laporan Perubahan Modal</a></li>
                <li><a href="/laporan_posisi_keuangan">⚖ Laporan Posisi Keuangan (Neraca)</a></li>
                <li><a href="/laporan_arus_kas">💵 Laporan Arus Kas</a></li>
            </ul>
            <div class="back-section">
                <a href="/akuntansi" class="btn-back">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/laporan_laba_rugi")
def laporan_laba_rugi():
    if not session.get("user_email"):
        return redirect("/")

    user = session.get("user_email")
    
    # Ambil data jurnal umum
    try:
        res = supabase.table("general_journal").select("*").eq("user_email", user).execute()
        journal_data = res.data or []
    except:
        journal_data = []
    
    # Ambil data jurnal penyesuaian
    try:
        res_adj = supabase.table("adjustment_journal").select("*").eq("user_email", user).execute()
        adj_data = res_adj.data or []
    except:
        adj_data = []
    
    # Rekapitulasi per akun dari jurnal umum
    akun_dict = {}
    for j in journal_data:
        lines = j.get("lines", [])
        if isinstance(lines, str):
            try:
                lines = json.loads(lines)
            except:
                lines = []
        
        for line in lines:
            kode = line.get("account_code")
            nama = line.get("account_name")
            debit = float(line.get("debit") or 0)
            kredit = float(line.get("credit") or 0)
            
            if kode not in akun_dict:
                akun_dict[kode] = {"nama": nama, "debit": 0, "kredit": 0}
            
            akun_dict[kode]["debit"] += debit
            akun_dict[kode]["kredit"] += kredit
    
    # Tambahkan jurnal penyesuaian
    for adj in adj_data:
        kode = adj.get("ref")
        nama = adj.get("description")
        debit = float(adj.get("debit") or 0)
        kredit = float(adj.get("credit") or 0)
        
        if kode not in akun_dict:
            akun_dict[kode] = {"nama": nama, "debit": 0, "kredit": 0}
        
        akun_dict[kode]["debit"] += debit
        akun_dict[kode]["kredit"] += kredit
    
    # PENDAPATAN (4-xxxx)
    pendapatan_items = []
    for kode, data in sorted(akun_dict.items()):
        if kode.startswith('4-'):
            nilai = data["kredit"] - data["debit"]
            if nilai != 0:
                pendapatan_items.append({"nama": data["nama"], "nilai": nilai})
    
    total_pendapatan = sum(item["nilai"] for item in pendapatan_items)
    
    # HARGA POKOK PENJUALAN (5-11xx dan 5-12xx untuk HPP)
    hpp_items = []
    for kode, data in sorted(akun_dict.items()):
        if kode.startswith('5-11') or kode.startswith('5-12'):
            nilai = data["debit"] - data["kredit"]
            if nilai != 0:
                hpp_items.append({"nama": data["nama"], "nilai": nilai})
    
    # Pembelian Bibit/Pakan (5-13xx, 5-14xx)
    pembelian_items = []
    for kode, data in sorted(akun_dict.items()):
        if kode.startswith('5-13') or kode.startswith('5-14'):
            nilai = data["debit"] - data["kredit"]
            if nilai != 0:
                pembelian_items.append({"nama": data["nama"], "nilai": nilai})
    
    total_hpp = sum(item["nilai"] for item in hpp_items) + sum(item["nilai"] for item in pembelian_items)
    laba_kotor = total_pendapatan - total_hpp
    
    # BEBAN OPERASIONAL (6-xxxx kecuali beban lain)
    beban_operasional = []
    for kode, data in sorted(akun_dict.items()):
        if kode.startswith('6-') and not kode.startswith('6-2') and not kode.startswith('6-3'):
            nilai = data["debit"] - data["kredit"]
            if nilai != 0:
                beban_operasional.append({"nama": data["nama"], "nilai": nilai})
    
    total_beban_operasional = sum(item["nilai"] for item in beban_operasional)
    pendapatan_dari_operasional = laba_kotor - total_beban_operasional
    
    # PENDAPATAN DAN KEUNTUNGAN LAINNYA
    pendapatan_lain = []
    for kode, data in sorted(akun_dict.items()):
        if kode.startswith('4-2') or 'bunga' in data["nama"].lower() or 'denda' in data["nama"].lower():
            if kode.startswith('4-'):
                nilai = data["kredit"] - data["debit"]
                if nilai != 0:
                    pendapatan_lain.append({"nama": data["nama"], "nilai": nilai})
    
    total_pendapatan_lain = sum(item["nilai"] for item in pendapatan_lain)
    
    # BEBAN DAN KERUGIAN LAINNYA
    beban_lain = []
    for kode, data in sorted(akun_dict.items()):
        if kode.startswith('6-2') or kode.startswith('6-3'):
            nilai = data["debit"] - data["kredit"]
            if nilai != 0:
                beban_lain.append({"nama": data["nama"], "nilai": nilai})
    
    total_beban_lain = sum(item["nilai"] for item in beban_lain)
    total_pendapatan_beban_lain = total_pendapatan_lain - total_beban_lain
    laba_bersih = pendapatan_dari_operasional + total_pendapatan_beban_lain
    
    # Hitung nilai absolut untuk laba/rugi bersih
    laba_bersih_abs = abs(laba_bersih)
    status_laba_rugi = "LABA BERSIH" if laba_bersih >= 0 else "RUGI BERSIH"
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laporan Laba Rugi - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 40px auto;
                background: white;
                padding: 50px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                text-align: center;
                color: #2d3748;
                font-size: 18px;
                font-weight: 700;
                margin-bottom: 5px;
            }
            h3 {
                text-align: center;
                color: #2d3748;
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 20px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .header-row {
                background: #2d3748;
                color: white;
            }
            .header-row th {
                padding: 12px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
            }
            .header-row th:last-child {
                text-align: right;
            }
            td {
                padding: 8px 12px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 14px;
            }
            .indent-1 {
                padding-left: 30px;
            }
            .indent-2 {
                padding-left: 50px;
            }
            .section-title {
                font-weight: 700;
                background: #f7fafc;
                color: #2d3748;
            }
            .subtotal-row {
                font-weight: 700;
                background: #edf2f7;
            }
            .total-row {
                font-weight: 700;
                background: #cbd5e0;
                font-size: 15px;
            }
            .final-row {
                font-weight: 700;
                background: #a0aec0;
                color: #1a202c;
                font-size: 16px;
            }
            .amount {
                text-align: right;
                font-family: 'Courier New', monospace;
            }
            .btn-back {
                display: inline-block;
                margin-top: 30px;
                padding: 12px 25px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 12px;
                font-weight: 600;
                transition: 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .btn-back:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            @media print {
                body { background: white; padding: 0; }
                .container { box-shadow: none; }
                .back-section { display: none; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>BELUT.IN</h2>
            <h2>LAPORAN LABA RUGI</h2>
            <h3>31 Desember 2025</h3>
            
            <table>
                <thead>
                    <tr class="header-row">
                        <th>Keterangan</th>
                        <th style="text-align:right;">Jumlah</th>
                    </tr>
                </thead>
                <tbody>
                    <!-- PENDAPATAN -->
                    <tr class="section-title">
                        <td><strong>Pendapatan:</strong></td>
                        <td></td>
                    </tr>
                    {% for item in pendapatan_items %}
                    <tr>
                        <td class="indent-1">{{ item.nama }}</td>
                        <td class="amount">{{ rupiah_small(item.nilai) }}</td>
                    </tr>
                    {% endfor %}
                    <tr class="subtotal-row">
                        <td class="indent-2"><strong>Total Pendapatan</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(total_pendapatan) }}</strong></td>
                    </tr>
                    
                    <!-- HARGA POKOK PENJUALAN -->
                    <tr class="section-title">
                        <td><strong>Harga Pokok Penjualan:</strong></td>
                        <td></td>
                    </tr>
                    {% for item in hpp_items %}
                    <tr>
                        <td class="indent-1">{{ item.nama }}</td>
                        <td class="amount">{{ rupiah_small(item.nilai) }}</td>
                    </tr>
                    {% endfor %}
                    {% for item in pembelian_items %}
                    <tr>
                        <td class="indent-1">{{ item.nama }}</td>
                        <td class="amount">{{ rupiah_small(item.nilai) }}</td>
                    </tr>
                    {% endfor %}
                    <tr class="subtotal-row">
                        <td class="indent-2"><strong>Total Harga Pokok Penjualan</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(total_hpp) }}</strong></td>
                    </tr>
                    <tr class="total-row">
                        <td><strong>Laba Kotor:</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(laba_kotor) }}</strong></td>
                    </tr>
                    
                    <!-- BEBAN OPERASIONAL -->
                    <tr class="section-title">
                        <td><strong>Beban Operasional:</strong></td>
                        <td></td>
                    </tr>
                    {% for item in beban_operasional %}
                    <tr>
                        <td class="indent-1">{{ item.nama }}</td>
                        <td class="amount">{{ rupiah_small(item.nilai) }}</td>
                    </tr>
                    {% endfor %}
                    <tr class="subtotal-row">
                        <td class="indent-2"><strong>Total Beban Operasional</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(total_beban_operasional) }}</strong></td>
                    </tr>
                    <tr class="total-row">
                        <td><strong>Pendapatan dari Operasional:</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(pendapatan_dari_operasional) }}</strong></td>
                    </tr>
                    
                    <!-- PENDAPATAN LAINNYA -->
                    <tr class="section-title">
                        <td><strong>Pendapatan dan Keuntungan Lainnya:</strong></td>
                        <td></td>
                    </tr>
                    {% if pendapatan_lain %}
                        {% for item in pendapatan_lain %}
                        <tr>
                            <td class="indent-1">{{ item.nama }}</td>
                            <td class="amount">{{ rupiah_small(item.nilai) }}</td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td class="indent-1" style="color:#999; font-style:italic;">-</td>
                            <td></td>
                        </tr>
                    {% endif %}
                    <tr class="subtotal-row">
                        <td class="indent-2"><strong>Total Pendapatan Lainnya</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(total_pendapatan_lain) }}</strong></td>
                    </tr>
                    
                    <!-- BEBAN LAINNYA -->
                    <tr class="section-title">
                        <td><strong>Beban dan Kerugian Lainnya:</strong></td>
                        <td></td>
                    </tr>
                    {% if beban_lain %}
                        {% for item in beban_lain %}
                        <tr>
                            <td class="indent-1">{{ item.nama }}</td>
                            <td class="amount">{{ rupiah_small(item.nilai) }}</td>
                        </tr>
                        {% endfor %}
                    {% else %}
                        <tr>
                            <td class="indent-1" style="color:#999; font-style:italic;">-</td>
                            <td></td>
                        </tr>
                    {% endif %}
                    <tr class="subtotal-row">
                        <td class="indent-2"><strong>Total Beban Lainnya</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(total_beban_lain) }}</strong></td>
                    </tr>
                    <tr class="total-row">
                        <td><strong>Total Pendapatan dan Beban Lainnya:</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(total_pendapatan_beban_lain) }}</strong></td>
                    </tr>
                    
                    <!-- LABA BERSIH -->
                    <tr class="final-row">
                        <td><strong>{{ status_laba_rugi }}</strong></td>
                        <td class="amount"><strong>{{ rupiah_small(laba_bersih_abs) }}</strong></td>
                    </tr>
                </tbody>
            </table>
            
            <div class="back-section">
                <a href="/akuntansi" class="btn-back">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """,
    pendapatan_items=pendapatan_items,
    total_pendapatan=total_pendapatan,
    hpp_items=hpp_items,
    pembelian_items=pembelian_items,
    total_hpp=total_hpp,
    laba_kotor=laba_kotor,
    beban_operasional=beban_operasional,
    total_beban_operasional=total_beban_operasional,
    pendapatan_dari_operasional=pendapatan_dari_operasional,
    pendapatan_lain=pendapatan_lain,
    total_pendapatan_lain=total_pendapatan_lain,
    beban_lain=beban_lain,
    total_beban_lain=total_beban_lain,
    total_pendapatan_beban_lain=total_pendapatan_beban_lain,
    laba_bersih_abs=laba_bersih_abs,
    status_laba_rugi=status_laba_rugi,
    rupiah_small=rupiah_small)

@app.route("/laporan_perubahan_modal")
def laporan_perubahan_ekuitas():
    if not session.get("user_email"):
        return redirect("/")

    akun_dict = get_akun_dict()

    # Perhitungan
    pendapatan = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('4-'))
    beban = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() if k.startswith('5-') or k.startswith('6-'))
    laba_rugi = pendapatan - beban
    
    modal_awal = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('3-1'))
    prive = sum(v['total_debit'] for k, v in akun_dict.items() if k.startswith('3-2'))
    modal_akhir = modal_awal + laba_rugi - prive

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laporan Perubahan Ekuitas</title>
        <style>
            body { font-family: Arial; background:#f0f4f8; margin:0; padding:20px; }
            .container { max-width:900px; margin:40px auto; background:white; padding:40px; border-radius:12px; }
            h2 { color:#004080; text-align:center; margin-bottom:10px; }
            h4, h5, h6 { text-align:center; color:#666; margin:5px 0; }
            .report-card { background:#f9f9f9; padding:20px; margin-bottom:20px; border-radius:10px; }
            table { width:100%; border-collapse:collapse; margin:10px 0; }
            td { padding:8px; border-bottom:1px solid #ddd; }
            .total-row { background:#e3f2fd; font-weight:700; }
            a { display:inline-block; margin-top:20px; padding:10px 15px; background:#004080; color:white; text-decoration:none; border-radius:8px; }
            a:hover { background:#003060; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>💼 Laporan Perubahan Ekuitas</h2>
            <h4>BELUT.IN</h4>
            <h5>LAPORAN PERUBAHAN EKUITAS</h5>
            <h6>Untuk Periode yang Berakhir 31 Desember 2025</h6>
            
            <div class="report-card">
                <table>
                    <tr>
                        <td>Modal Awal</td>
                        <td style="text-align:right;">{{ modal_awal }}</td>
                    </tr>
                    <tr>
                        <td style="padding-left:20px;">Laba Bersih</td>
                        <td style="text-align:right;">{{ laba_rugi_str }}</td>
                    </tr>
                    <tr>
                        <td style="padding-left:20px;">Prive</td>
                        <td style="text-align:right;">({{ prive }})</td>
                    </tr>
                    <tr class="total-row">
                        <td><strong>Modal Akhir</strong></td>
                        <td style="text-align:right;"><strong>{{ modal_akhir }}</strong></td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align:center;">
                <a href="/laporan">⬅ Kembali ke Menu Laporan</a>
            </div>
        </div>
    </body>
    </html>
    """, 
    modal_awal=rupiah_small(modal_awal),
    prive=rupiah_small(prive),
    laba_rugi_str=rupiah_small(laba_rugi),
    modal_akhir=rupiah_small(modal_akhir))


@app.route("/laporan_posisi_keuangan")
def laporan_neraca():
    if not session.get("user_email"):
        return redirect("/")

    akun_dict = get_akun_dict()

    # Perhitungan Laba Rugi untuk Ekuitas
    pendapatan = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('4-'))
    beban = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() if k.startswith('5-') or k.startswith('6-'))
    laba_rugi = pendapatan - beban

    # Perhitungan Modal
    modal_awal = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('3-1'))
    prive = sum(v['total_debit'] for k, v in akun_dict.items() if k.startswith('3-2'))
    modal_akhir = modal_awal + laba_rugi - prive

    # Neraca
    aset = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() if k.startswith('1-'))
    liabilitas = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('2-'))
    ekuitas = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('3-')) + laba_rugi
    
    # Klasifikasi Aset
    aset_lancar = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() 
                  if k.startswith('1-1') or k.startswith('1-2') or k.startswith('1-3'))
    aset_tetap_kotor = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() 
                      if k.startswith('1-4'))
    akumulasi_penyusutan = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() 
                          if k.startswith('1-5'))
    aset_tetap = aset_tetap_kotor - akumulasi_penyusutan

    # Klasifikasi Liabilitas
    liabilitas_lancar = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() 
                       if k.startswith('2-1'))
    liabilitas_panjang = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() 
                        if k.startswith('2-2'))

    total_pasiva = liabilitas + ekuitas

    # Rows untuk Neraca - Aset Lancar
    aset_lancar_rows = "".join([
        f"<tr><td style='padding-left:20px;'>{v['akun']}</td><td style='text-align:right;'>{rupiah_small(v['total_debit'] - v['total_kredit'])}</td></tr>"
        for k,v in akun_dict.items() if k.startswith('1-1') or k.startswith('1-2') or k.startswith('1-3')
    ])
    
    # Rows untuk Neraca - Aset Tetap
    template_aset_tetap = [
        ('1-41', 'Tanah'),
        ('1-42', 'Bangunan'),
        ('1-51', 'Akumulasi Penyusutan Bangunan'),
        ('1-43', 'Kendaraan'),
        ('1-52', 'Akumulasi Penyusutan Kendaraan'),
        ('1-44', 'Peralatan'),
        ('1-53', 'Akumulasi Penyusutan Peralatan'),
    ]
    
    aset_tetap_rows = ""
    for kode_prefix, nama_akun in template_aset_tetap:
        nilai = 0
        for k, v in akun_dict.items():
            if k.startswith(kode_prefix):
                if kode_prefix.startswith('1-5'):
                    nilai += v['total_kredit'] - v['total_debit']
                else:
                    nilai += v['total_debit'] - v['total_kredit']
        
        if kode_prefix.startswith('1-5'):
            if nilai > 0:
                aset_tetap_rows += f"<tr><td style='padding-left:20px;'>{nama_akun}</td><td style='text-align:right;'>({rupiah_small(nilai)})</td></tr>"
            else:
                aset_tetap_rows += f"<tr><td style='padding-left:20px;'>{nama_akun}</td><td style='text-align:right;'>{rupiah_small(0)}</td></tr>"
        else:
            aset_tetap_rows += f"<tr><td style='padding-left:20px;'>{nama_akun}</td><td style='text-align:right;'>{rupiah_small(nilai)}</td></tr>"
            
    # Rows untuk Neraca - Liabilitas Lancar
    template_liabilitas_lancar = [
        ('2-12', 'Utang Biaya'),
    ]

    liabilitas_lancar_rows = ""
    for kode_prefix, nama_akun in template_liabilitas_lancar:
        nilai = 0
        for k, v in akun_dict.items():
            if k.startswith(kode_prefix):
                nilai += v['total_kredit'] - v['total_debit']
        liabilitas_lancar_rows += f"<tr><td style='padding-left:20px;'>{nama_akun}</td><td style='text-align:right;'>{rupiah_small(nilai)}</td></tr>"

    # Rows untuk Neraca - Liabilitas Jangka Panjang
    template_liabilitas_panjang = [
        ('2-21', 'Pinjaman Bank BCA'),
    ]

    liabilitas_panjang_rows = ""
    for kode_prefix, nama_akun in template_liabilitas_panjang:
        nilai = 0
        for k, v in akun_dict.items():
            if k.startswith(kode_prefix):
                nilai += v['total_kredit'] - v['total_debit']
        liabilitas_panjang_rows += f"<tr><td style='padding-left:20px;'>{nama_akun}</td><td style='text-align:right;'>{rupiah_small(nilai)}</td></tr>"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laporan Posisi Keuangan</title>
        <style>
            body { font-family: Arial; background:#f0f4f8; margin:0; padding:20px; }
            .container { max-width:1200px; margin:40px auto; background:white; padding:40px; border-radius:12px; }
            h2 { color:#004080; text-align:center; margin-bottom:10px; }
            h4, h5, h6 { text-align:center; color:#666; margin:5px 0; }
            .report-card { background:#f9f9f9; padding:20px; margin-bottom:20px; border-radius:10px; }
            table { width:100%; border-collapse:collapse; margin:10px 0; }
            td { padding:8px; border-bottom:1px solid #ddd; }
            .total-row { background:#e3f2fd; font-weight:700; }
            .flex { display:grid; grid-template-columns:1fr 1fr; gap:20px; }
            a { display:inline-block; margin-top:20px; padding:10px 15px; background:#004080; color:white; text-decoration:none; border-radius:8px; }
            a:hover { background:#003060; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>⚖ Laporan Posisi Keuangan</h2>
            <h4>BELUT.IN</h4>
            <h5>LAPORAN POSISI KEUANGAN</h5>
            <h6>Per 31 Desember 2025</h6>
            
            <div class="flex">
                <div class="report-card">
                    <h4>ASET</h4>
                    <table>
                        <tr style="background:#e3f2fd; font-weight:700;">
                            <td colspan="2">ASET LANCAR</td>
                        </tr>
                        {{ aset_lancar_rows|safe }}
                        <tr class="total-row">
                            <td style="padding-left:20px;">Total Aset Lancar</td>
                            <td style="text-align:right;">{{ total_aset_lancar }}</td>
                        </tr>
                        <tr style="height:10px;"><td colspan="2"></td></tr>
                        <tr style="background:#e3f2fd; font-weight:700;">
                            <td colspan="2">ASET TETAP</td>
                        </tr>
                        {{ aset_tetap_rows|safe }}
                        <tr class="total-row">
                            <td style="padding-left:20px;">Total Aset Tetap (Neto)</td>
                            <td style="text-align:right;">{{ total_aset_tetap }}</td>
                        </tr>
                        <tr style="height:15px;"><td colspan="2"></td></tr>
                        <tr style="background:#004080; color:white; font-weight:700; font-size:16px;">
                            <td><strong>TOTAL ASET</strong></td>
                            <td style="text-align:right;"><strong>{{ aset }}</strong></td>
                        </tr>
                    </table>
                </div>
                
                <div>
                    <div class="report-card">
                        <h4>KEWAJIBAN DAN EKUITAS</h4>
                        <table>
                            <tr style="background:#e3f2fd; font-weight:700;">
                                <td colspan="2">KEWAJIBAN LANCAR</td>
                            </tr>
                            {{ liabilitas_lancar_rows|safe }}
                            <tr class="total-row">
                                <td style="padding-left:20px;">Total Kewajiban Lancar</td>
                                <td style="text-align:right;">{{ total_liabilitas_lancar }}</td>
                            </tr>
                            <tr style="height:10px;"><td colspan="2"></td></tr>
                            <tr style="background:#e3f2fd; font-weight:700;">
                                <td colspan="2">KEWAJIBAN JANGKA PANJANG</td>
                            </tr>
                            {{ liabilitas_panjang_rows|safe }}
                            <tr class="total-row">
                                <td style="padding-left:20px;">Total Kewajiban Jangka Panjang</td>
                                <td style="text-align:right;">{{ total_liabilitas_panjang }}</td>
                            </tr>
                            <tr style="background:#b3d9ff; font-weight:700;">
                                <td><strong>TOTAL LIABILITAS</strong></td>
                                <td style="text-align:right;"><strong>{{ liabilitas }}</strong></td>
                                </tr>
                            <tr style="height:15px;"><td colspan="2"></td></tr>
                            <tr style="background:#e3f2fd; font-weight:700;">
                                <td colspan="2">EKUITAS</td>
                            </tr>
                            <tr>
                                <td style="padding-left:20px;">Modal Pemilik</td>
                                <td style="text-align:right;">{{ modal_akhir }}</td>
                            </tr>
                            <tr style="background:#b3d9ff; font-weight:700;">
                                <td><strong>TOTAL EKUITAS</strong></td>
                                <td style="text-align:right;"><strong>{{ ekuitas }}</strong></td>
                            </tr>
                            <tr style="height:15px;"><td colspan="2"></td></tr>
                            <tr style="background:#004080; color:white; font-weight:700; font-size:16px;">
                                <td><strong>TOTAL KEWAJIBAN DAN EKUITAS</strong></td>
                                <td style="text-align:right;"><strong>{{ total_pasiva }}</strong></td>
                            </tr>
                        </table>
                    </div>
                </div>
            </div>
            
            <div style="text-align:center;">
                <a href="/laporan">⬅ Kembali ke Menu Laporan</a>
            </div>
        </div>
    </body>
    </html>
    """,
    aset_lancar_rows=aset_lancar_rows,
    aset_tetap_rows=aset_tetap_rows,
    liabilitas_lancar_rows=liabilitas_lancar_rows,
    liabilitas_panjang_rows=liabilitas_panjang_rows,
    total_aset_lancar=rupiah_small(aset_lancar),
    total_aset_tetap=rupiah_small(aset_tetap),
    total_liabilitas_lancar=rupiah_small(liabilitas_lancar),
    total_liabilitas_panjang=rupiah_small(liabilitas_panjang),
    total_pasiva=rupiah_small(total_pasiva),
    aset=rupiah_small(aset),
    liabilitas=rupiah_small(liabilitas),
    ekuitas=rupiah_small(ekuitas),
    modal_akhir=rupiah_small(modal_akhir))

@app.route("/laporan_arus_kas")
def laporan_arus_kas():
    if not session.get("user_email"):
        return redirect("/")

    akun_dict = get_akun_dict()

    # ========================================
    # ARUS KAS - METODE LANGSUNG
    # ========================================
    
    # 1. ARUS KAS DARI AKTIVITAS OPERASI
    
    # a. Penerimaan Kas dari Pelanggan (Penjualan)
    # Ambil dari transaksi penjualan (kas masuk dari penjualan)
    penerimaan_pelanggan = 0
    try:
        res = supabase.table("general_journal").select("*").like("description", "%Penjualan%").execute()
        for jurnal in res.data or []:
            lines = jurnal.get('lines', [])
            if isinstance(lines, str):
                try:
                    lines = json.loads(lines)
                except:
                    lines = []
            
            for line in lines:
                # Cek jika debit ke Kas atau Kas di Bank (penerimaan tunai/transfer)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('debit', 0) > 0:
                    penerimaan_pelanggan += float(line.get('debit', 0))
    except:
        pass
    
    # b. Pembayaran kepada Pemasok (Pembelian)
    # Ambil dari transaksi pembelian (kas keluar untuk pembelian)
    pembayaran_pemasok = 0
    try:
        res = supabase.table("general_journal").select("*").like("description", "%Pembelian%").execute()
        for jurnal in res.data or []:
            lines = jurnal.get('lines', [])
            if isinstance(lines, str):
                try:
                    lines = json.loads(lines)
                except:
                    lines = []
            
            for line in lines:
                # Cek jika kredit dari Kas atau Kas di Bank (pengeluaran tunai/transfer)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('credit', 0) > 0:
                    pembayaran_pemasok += float(line.get('credit', 0))
    except:
        pass
    
    # c. Pembayaran Beban Operasi (Transaksi Lainnya)
    # Ambil dari transaksi lainnya yang merupakan beban
    pembayaran_beban_operasi = 0
    try:
        res = supabase.table("general_journal").select("*").like("description", "%Lainnya%").execute()
        for jurnal in res.data or []:
            lines = jurnal.get('lines', [])
            if isinstance(lines, str):
                try:
                    lines = json.loads(lines)
                except:
                    lines = []
            
            # Cek apakah ada kredit dari kas (pengeluaran kas untuk beban)
            ada_kredit_kas = False
            adalah_beban = False
            
            for line in lines:
                # Cek kredit dari Kas/Kas di Bank
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('credit', 0) > 0:
                    ada_kredit_kas = True
                    nominal_beban = float(line.get('credit', 0))
                
                # Cek apakah ada debit ke akun beban (kode 6- atau 9-)
                if line.get('account_code', '').startswith(('6-', '9-')) and line.get('debit', 0) > 0:
                    adalah_beban = True
            
            if ada_kredit_kas and adalah_beban:
                pembayaran_beban_operasi += nominal_beban
    except:
        pass
    
    # Total Kas Bersih dari Aktivitas Operasi
    kas_bersih_operasi = penerimaan_pelanggan - pembayaran_pemasok - pembayaran_beban_operasi
    
    # 2. ARUS KAS DARI AKTIVITAS INVESTASI
    pembelian_aset_tetap = 0
    penjualan_aset_tetap = 0
    
    try:
        res = supabase.table("general_journal").select("*").like("description", "%Lainnya%").execute()
        for jurnal in res.data or []:
            lines = jurnal.get('lines', [])
            if isinstance(lines, str):
                try:
                    lines = json.loads(lines)
                except:
                    lines = []
            
            for line in lines:
                # Pembelian aset tetap (kredit dari kas untuk beli aset)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('credit', 0) > 0:
                    # Cek apakah ada debit ke aset tetap (kode 1-2xxx kecuali akumulasi)
                    for other_line in lines:
                        if other_line.get('account_code', '').startswith('1-2') and not other_line.get('account_code', '').endswith('0') and other_line.get('debit', 0) > 0:
                            if '21' not in other_line.get('account_code', '') and '31' not in other_line.get('account_code', '') and '41' not in other_line.get('account_code', ''):  # bukan akumulasi
                                pembelian_aset_tetap += float(line.get('credit', 0))
                
                # Penjualan aset tetap (debit ke kas dari jual aset)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('debit', 0) > 0:
                    for other_line in lines:
                        if other_line.get('account_code', '').startswith('1-2') and other_line.get('credit', 0) > 0:
                            penjualan_aset_tetap += float(line.get('debit', 0))
    except:
        pass
    
    kas_bersih_investasi = penjualan_aset_tetap - pembelian_aset_tetap
    
    # 3. ARUS KAS DARI AKTIVITAS PENDANAAN
    penerimaan_pinjaman = 0
    pembayaran_pinjaman = 0
    tambahan_modal = 0
    pengambilan_prive = 0
    
    try:
        res = supabase.table("general_journal").select("*").like("description", "%Lainnya%").execute()
        for jurnal in res.data or []:
            lines = jurnal.get('lines', [])
            if isinstance(lines, str):
                try:
                    lines = json.loads(lines)
                except:
                    lines = []
            
            for line in lines:
                # Penerimaan pinjaman (debit kas, kredit utang jangka panjang)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('debit', 0) > 0:
                    for other_line in lines:
                        if other_line.get('account_code', '').startswith('2-2') and other_line.get('credit', 0) > 0:
                            penerimaan_pinjaman += float(line.get('debit', 0))
                
                # Pembayaran pinjaman (kredit kas, debit utang jangka panjang)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('credit', 0) > 0:
                    for other_line in lines:
                        if other_line.get('account_code', '').startswith('2-2') and other_line.get('debit', 0) > 0:
                            pembayaran_pinjaman += float(line.get('credit', 0))
                
                # Tambahan modal (debit kas, kredit modal)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('debit', 0) > 0:
                    for other_line in lines:
                        if other_line.get('account_code') == '3-1100' and other_line.get('credit', 0) > 0:
                            tambahan_modal += float(line.get('debit', 0))
                
                # Pengambilan prive (kredit kas, debit prive)
                if line.get('account_code') in ['1-1100', '1-1110'] and line.get('credit', 0) > 0:
                    for other_line in lines:
                        if other_line.get('account_code') == '3-1200' and other_line.get('debit', 0) > 0:
                            pengambilan_prive += float(line.get('credit', 0))
    except:
        pass
    
    kas_bersih_pendanaan = penerimaan_pinjaman + tambahan_modal - pembayaran_pinjaman - pengambilan_prive
    
    # Total perubahan kas
    kenaikan_kas = kas_bersih_operasi + kas_bersih_investasi + kas_bersih_pendanaan
    
    # Saldo kas akhir (Kas + Kas di Bank)
    saldo_kas_akhir = akun_dict.get('1-1100', {}).get('total_debit', 0) - akun_dict.get('1-1100', {}).get('total_kredit', 0)
    saldo_kas_akhir += akun_dict.get('1-1110', {}).get('total_debit', 0) - akun_dict.get('1-1110', {}).get('total_kredit', 0)
    
    saldo_kas_awal = saldo_kas_akhir - kenaikan_kas

    # Build rows untuk template
    arus_kas_operasi_rows = f"""
    <tr>
        <td style='padding-left:20px;'>Penerimaan Kas dari Pelanggan</td>
        <td style='text-align:right;'>{rupiah_small(penerimaan_pelanggan)}</td>
    </tr>
    <tr>
        <td style='padding-left:20px;'>Pembayaran kepada Pemasok</td>
        <td style='text-align:right;'>({rupiah_small(pembayaran_pemasok)})</td>
    </tr>
    <tr>
        <td style='padding-left:20px;'>Pembayaran Beban Operasi</td>
        <td style='text-align:right;'>({rupiah_small(pembayaran_beban_operasi)})</td>
    </tr>
    """
    
    arus_kas_investasi_rows = ""
    if pembelian_aset_tetap > 0:
        arus_kas_investasi_rows += f"""
        <tr>
            <td style='padding-left:20px;'>Pembelian Aset Tetap</td>
            <td style='text-align:right;'>({rupiah_small(pembelian_aset_tetap)})</td>
        </tr>
        """
    
    if penjualan_aset_tetap > 0:
        arus_kas_investasi_rows += f"""
        <tr>
            <td style='padding-left:20px;'>Penjualan Aset Tetap</td>
            <td style='text-align:right;'>{rupiah_small(penjualan_aset_tetap)}</td>
        </tr>
        """
    
    if not arus_kas_investasi_rows:
        arus_kas_investasi_rows = "<tr><td style='padding-left:20px;color:#999;'>Tidak ada transaksi</td><td></td></tr>"
    
    arus_kas_pendanaan_rows = ""
    if penerimaan_pinjaman > 0:
        arus_kas_pendanaan_rows += f"""
        <tr>
            <td style='padding-left:20px;'>Penerimaan dari Pinjaman Bank</td>
            <td style='text-align:right;'>{rupiah_small(penerimaan_pinjaman)}</td>
        </tr>
        """
    
    if tambahan_modal > 0:
        arus_kas_pendanaan_rows += f"""
        <tr>
            <td style='padding-left:20px;'>Penerimaan dari Pemilik (Modal)</td>
            <td style='text-align:right;'>{rupiah_small(tambahan_modal)}</td>
        </tr>
        """
    
    if pembayaran_pinjaman > 0:
        arus_kas_pendanaan_rows += f"""
        <tr>
            <td style='padding-left:20px;'>Pembayaran Pinjaman Bank</td>
            <td style='text-align:right;'>({rupiah_small(pembayaran_pinjaman)})</td>
        </tr>
        """
    
    if pengambilan_prive > 0:
        arus_kas_pendanaan_rows += f"""
        <tr>
            <td style='padding-left:20px;'>Pembayaran kepada Pemilik (Prive)</td>
            <td style='text-align:right;'>({rupiah_small(pengambilan_prive)})</td>
        </tr>
        """
    
    if not arus_kas_pendanaan_rows:
        arus_kas_pendanaan_rows = "<tr><td style='padding-left:20px;color:#999;'>Tidak ada transaksi</td><td></td></tr>"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Laporan Arus Kas</title>
        <style>
            body { font-family: Arial; background:#f0f4f8; margin:0; padding:20px; }
            .container { max-width:1000px; margin:40px auto; background:white; 
                padding:40px; border-radius:12px; box-shadow:0 4px 15px rgba(0,0,0,0.1); }
            h2 { color:#004080; text-align:center; margin-bottom:10px; font-size:28px; }
            h4, h5, h6 { text-align:center; color:#666; margin:5px 0; }
            .info-badge { background:#e7f3ff; padding:10px; 
                border-radius:8px; text-align:center; margin:20px 0; 
                color:#004080; font-weight:600; border-left:4px solid #004080; }
            .report-card { background:#f9f9f9; padding:20px; 
                margin-bottom:20px; border-radius:10px; }
            table { width:100%; border-collapse:collapse; margin:10px 0; }
            td { padding:10px; border-bottom:1px solid #ddd; }
            .total-row { background:#e3f2fd; font-weight:700; font-size:15px; }
            .section-header { background:#004080; color:white; font-weight:700; 
                font-size:14px; padding:12px !important; }
            .grand-total { background:#d4edda; font-size:18px; 
                border-top:3px solid #28a745; font-weight:700; }
            a { display:inline-block; margin-top:20px; padding:12px 20px; 
                background:#004080; color:white; text-decoration:none; border-radius:8px; transition:0.3s; }
            a:hover { background:#003060; transform:translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>💵 Laporan Arus Kas</h2>
            <h4>BELUT.IN</h4>
            <h5>LAPORAN ARUS KAS</h5>
            <h6>Untuk Periode yang Berakhir 31 Desember 2025</h6>
            
            <div class="info-badge">
                📊 Metode: Langsung (Direct Method)
            </div>
            
            <div class="report-card">
                <table>
                    <tr class="section-header">
                        <td colspan="2">ARUS KAS DARI AKTIVITAS OPERASI</td>
                    </tr>
                    {{ arus_kas_operasi_rows|safe }}
                    <tr class="total-row">
                        <td><strong>Kas Bersih dari Aktivitas Operasi</strong></td>
                        <td style="text-align:right;"><strong>{{ kas_bersih_operasi_str }}</strong></td>
                    </tr>
                    
                    <tr style="height:15px;"><td colspan="2"></td></tr>
                    
                    <tr class="section-header">
                        <td colspan="2">ARUS KAS DARI AKTIVITAS INVESTASI</td>
                    </tr>
                    {{ arus_kas_investasi_rows|safe }}
                    <tr class="total-row">
                        <td><strong>Kas Bersih dari Aktivitas Investasi</strong></td>
                        <td style="text-align:right;"><strong>{{ kas_bersih_investasi_str }}</strong></td>
                    </tr>
                    
                    <tr style="height:15px;"><td colspan="2"></td></tr>
                    
                    <tr class="section-header">
                        <td colspan="2">ARUS KAS DARI AKTIVITAS PENDANAAN</td>
                    </tr>
                    {{ arus_kas_pendanaan_rows|safe }}
                    <tr class="total-row">
                        <td><strong>Kas Bersih dari Aktivitas Pendanaan</strong></td>
                        <td style="text-align:right;"><strong>{{ kas_bersih_pendanaan_str }}</strong></td>
                    </tr>
                    
                    <tr style="height:20px;"><td colspan="2"></td></tr>
                    
                    <tr style="border-top:2px solid #004080; font-size:16px;">
                        <td><strong>Kenaikan/(Penurunan) Kas dan Setara Kas</strong></td>
                        <td style="text-align:right;"><strong>{{ kenaikan_kas_str }}</strong></td>
                    </tr>
                    <tr style="font-size:15px;">
                        <td><strong>Saldo Kas dan Setara Kas Awal Periode</strong></td>
                        <td style="text-align:right;"><strong>{{ saldo_kas_awal_str }}</strong></td>
                    </tr>
                    <tr class="grand-total">
                        <td><strong>Saldo Kas dan Setara Kas Akhir Periode</strong></td>
                        <td style="text-align:right;"><strong>{{ saldo_kas_akhir_str }}</strong></td>
                    </tr>
                </table>
            </div>
            
            <div style="text-align:center;">
                <a href="/akuntansi">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """,
    arus_kas_operasi_rows=arus_kas_operasi_rows,
    arus_kas_investasi_rows=arus_kas_investasi_rows,
    arus_kas_pendanaan_rows=arus_kas_pendanaan_rows,
    kas_bersih_operasi_str=rupiah_small(kas_bersih_operasi),
    kas_bersih_investasi_str=rupiah_small(kas_bersih_investasi),
    kas_bersih_pendanaan_str=rupiah_small(kas_bersih_pendanaan),
    kenaikan_kas_str=rupiah_small(kenaikan_kas),
    saldo_kas_awal_str=rupiah_small(saldo_kas_awal),
    saldo_kas_akhir_str=rupiah_small(saldo_kas_akhir))

@app.route("/jurnal_penyesuaian")
def jurnal_penyesuaian_menu():
    """Halaman menu pilihan jurnal penyesuaian"""
    if not session.get("user_email"):
        return redirect("/")
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Jurnal Penyesuaian - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .container {
                max-width: 900px;
                width: 100%;
                background: white;
                padding: 50px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 20px;
                font-size: 36px;
            }
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 50px;
                font-size: 16px;
            }
            .menu-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 30px;
                margin-bottom: 40px;
            }
            .menu-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px 30px;
                border-radius: 15px;
                text-align: center;
                cursor: pointer;
                transition: transform 0.3s, box-shadow 0.3s;
                box-shadow: 0 5px 20px rgba(0,0,0,0.1);
                text-decoration: none;
                color: white;
            }
            .menu-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .menu-icon {
                font-size: 60px;
                margin-bottom: 20px;
            }
            .menu-title {
                font-size: 24px;
                font-weight: 700;
                margin-bottom: 10px;
            }
            .menu-desc {
                font-size: 14px;
                opacity: 0.9;
            }
            .btn-back {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 12px 25px;
                border-radius: 12px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-back:hover {
                background: #764ba2;
                transform: translateY(-2px);
            }
            .back-section {
                text-align: center;
                padding-top: 30px;
                border-top: 2px solid #e2e8f0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📋 Jurnal Penyesuaian</h2>
            <p class="subtitle">Pilih menu yang ingin Anda akses</p>
            
            <div class="menu-grid">
                <a href="/jurnal_penyesuaian/input" class="menu-card">
                    <div class="menu-icon">✏</div>
                    <div class="menu-title">Input Transaksi</div>
                    <div class="menu-desc">Input jurnal penyesuaian baru</div>
                </a>
                
                <a href="/jurnal_penyesuaian/view" class="menu-card">
                    <div class="menu-icon">📊</div>
                    <div class="menu-title">Lihat Jurnal</div>
                    <div class="menu-desc">Lihat daftar jurnal penyesuaian</div>
                </a>
            </div>
            
            <div class="back-section">
                <a href="/akuntansi" class="btn-back">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.route("/jurnal_penyesuaian/input", methods=["GET", "POST"])
def jurnal_penyesuaian_input():
    if not session.get("user_email"):
        return redirect("/")
    
    success_msg = ""
    error_msg = ""
    
    if request.method == "POST":
        try:
            jurnal_type = request.form.get("jurnal_type")
            tanggal = request.form.get("tanggal")
            
            if not tanggal or not jurnal_type:
                error_msg = "⚠ Tanggal dan Jenis Penyesuaian harus diisi!"
            else:
                entries = []
                
                if jurnal_type == "penyusutan_bangunan":
                    harga_perolehan = float(request.form.get("harga_bangunan", 0))
                    penyusutan_bulan = harga_perolehan / 8 / 12  # Umur 8 tahun
                    
                    entries.append({
                        "no": 1, "date": tanggal, "description": "Beban Depresiasi",
                        "ref": "6-1300", "debit": penyusutan_bulan, "credit": 0, "is_indent": False
                    })
                    entries.append({
                        "no": 1, "date": tanggal, "description": "Akumulasi Penyusutan Bangunan",
                        "ref": "1-2210", "debit": 0, "credit": penyusutan_bulan, "is_indent": True
                    })
                
                elif jurnal_type == "penyusutan_kendaraan":
                    harga_perolehan = float(request.form.get("harga_kendaraan", 0))
                    penyusutan_bulan = harga_perolehan / 4 / 12  # Umur 4 tahun
                    
                    entries.append({
                        "no": 2, "date": tanggal, "description": "Beban Depresiasi",
                        "ref": "6-1300", "debit": penyusutan_bulan, "credit": 0, "is_indent": False
                    })
                    entries.append({
                        "no": 2, "date": tanggal, "description": "Akumulasi Penyusutan Kendaraan",
                        "ref": "1-2310", "debit": 0, "credit": penyusutan_bulan, "is_indent": True
                    })
                
                elif jurnal_type == "penyusutan_peralatan":
                    harga_perolehan = float(request.form.get("harga_peralatan", 0))
                    penyusutan_bulan = harga_perolehan / 4 / 12  # Umur 4 tahun
                    
                    entries.append({
                        "no": 3, "date": tanggal, "description": "Beban Depresiasi",
                        "ref": "6-1300", "debit": penyusutan_bulan, "credit": 0, "is_indent": False
                    })
                    entries.append({
                        "no": 3, "date": tanggal, "description": "Akumulasi Penyusutan Peralatan",
                        "ref": "1-2410", "debit": 0, "credit": penyusutan_bulan, "is_indent": True
                    })
                
                elif jurnal_type == "hpp_standar":
                    hpp_standar = float(request.form.get("hpp_standar", 0))
                    
                    if hpp_standar > 0:
                        entries.append({
                            "no": 4, "date": tanggal, "description": "Harga Pokok Penjualan Belut Standar",
                            "ref": "5-1110", "debit": hpp_standar, "credit": 0, "is_indent": False
                        })
                        entries.append({
                            "no": 4, "date": tanggal, "description": "Persediaan Belut Standar",
                            "ref": "1-1410", "debit": 0, "credit": hpp_standar, "is_indent": True
                        })
                
                elif jurnal_type == "hpp_super":
                    hpp_super = float(request.form.get("hpp_super", 0))
                    
                    if hpp_super > 0:
                        entries.append({
                            "no": 5, "date": tanggal, "description": "Harga Pokok Penjualan Belut Super",
                            "ref": "5-1120", "debit": hpp_super, "credit": 0, "is_indent": False
                        })
                        entries.append({
                            "no": 5, "date": tanggal, "description": "Persediaan Belut Super",
                            "ref": "1-1420", "debit": 0, "credit": hpp_super, "is_indent": True
                        })
                
                elif jurnal_type == "pakan_standar":
                    total_pakan_standar = float(request.form.get("pakan_standar", 0))
                    
                    if total_pakan_standar > 0:
                        entries.append({
                            "no": 6, "date": tanggal, "description": "Beban Pakan Belut Standar",
                            "ref": "6-1410", "debit": total_pakan_standar, "credit": 0, "is_indent": False
                        })
                        entries.append({
                            "no": 6, "date": tanggal, "description": "Pembelian Pakan Belut Standar",
                            "ref": "5-1310", "debit": 0, "credit": total_pakan_standar, "is_indent": True
                        })
                
                elif jurnal_type == "pakan_super":
                    total_pakan_super = float(request.form.get("pakan_super", 0))
                    
                    if total_pakan_super > 0:
                        entries.append({
                            "no": 7, "date": tanggal, "description": "Beban Pakan Belut Super",
                            "ref": "6-1420", "debit": total_pakan_super, "credit": 0, "is_indent": False
                        })
                        entries.append({
                            "no": 7, "date": tanggal, "description": "Pembelian Pakan Belut Super",
                            "ref": "5-1320", "debit": 0, "credit": total_pakan_super, "is_indent": True
                        })
                
                # Simpan ke database
                for entry in entries:
                    supabase.table("adjustment_journal").insert({
                        "no": entry["no"],
                        "date": entry["date"],
                        "description": entry["description"],
                        "ref": entry["ref"],
                        "debit": entry["debit"],
                        "credit": entry["credit"],
                        "is_indent": entry["is_indent"],
                        "user_email": session.get("user_email")
                    }).execute()
                
                if entries:
                    success_msg = f"✅ {len(entries)} entri jurnal penyesuaian berhasil ditambahkan!"
                else:
                    error_msg = "⚠ Tidak ada entri yang dibuat. Pastikan nilai > 0!"
                    
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Input Jurnal Penyesuaian - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1000px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .info-box {
                background: #fff3cd;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 30px;
                border-left: 4px solid #ffc107;
            }
            .form-group {
                margin-bottom: 25px;
            }
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2d3748;
            }
            input, select {
                width: 100%;
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #ddd;
                font-family: 'Poppins', sans-serif;
            }
            .jurnal-option {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 15px;
                border-left: 4px solid #667eea;
                cursor: pointer;
            }
            .jurnal-option:hover {
                background: #e9ecef;
            }
            .jurnal-option input[type="radio"] {
                width: auto;
                margin-right: 10px;
            }
            .jurnal-detail {
                display: none;
                padding: 15px;
                background: #e7f3ff;
                border-radius: 8px;
                margin-top: 10px;
            }
            .btn-submit {
                width: 100%;
                background: #28a745;
                color: white;
                padding: 15px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                font-size: 16px;
                transition: 0.3s;
            }
            .btn-submit:hover {
                background: #218838;
                transform: translateY(-2px);
            }
            .alert {
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            .success { background: #d4edda; color: #155724; border-left: 4px solid #28a745; }
            .error { background: #f8d7da; color: #721c24; border-left: 4px solid #dc3545; }
            .btn-back {
                display: inline-block;
                margin-top: 20px;
                background: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .input-method {
                display: flex;
                gap: 10px;
                margin-bottom: 10px;
            }
            .input-method-btn {
                flex: 1;
                padding: 10px;
                text-align: center;
                background: #f8f9fa;
                border: 2px solid #ddd;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                transition: 0.3s;
            }
            .input-method-btn.active {
                background: #667eea;
                color: white;
                border-color: #667eea;
            }
            .calculator-input {
                display: none;
            }
            .direct-input {
                display: block;
            }
            .result-display {
                margin-top: 5px;
                font-weight: bold;
                color: #28a745;
                min-height: 20px;
            }
            .calculator-hint {
                font-size: 12px;
                color: #666;
                margin-top: 5px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>✏ Input Jurnal Penyesuaian</h2>
            
            {% if success_msg %}
                <div class="alert success">{{ success_msg }}</div>
            {% endif %}
            {% if error_msg %}
                <div class="alert error">{{ error_msg }}</div>
            {% endif %}
            
            <form method="POST" id="mainForm">
                <div class="form-group">
                    <label>Tanggal Penyesuaian *</label>
                    <input type="date" name="tanggal" required value="2025-12-31">
                </div>
                
                <div class="form-group">
                    <label>Pilih Jenis Penyesuaian:</label>
                    
                    <!-- PENYUSUTAN BANGUNAN -->
                    <div class="jurnal-option" onclick="selectOption('opt1')">
                        <input type="radio" name="jurnal_type" value="penyusutan_bangunan" id="opt1">
                        <label for="opt1" style="display:inline; cursor:pointer; margin:0;">🏢 Penyusutan Bangunan</label>
                        <div class="jurnal-detail" id="penyusutan_bangunan_detail">
                            <label>Harga Perolehan Bangunan (Rp) *</label>
                            <input type="number" name="harga_bangunan" placeholder="Contoh: 24000000" step="0.01">
                            <small style="color:#666;">Rumus: Harga Perolehan ÷ 8 tahun ÷ 12 bulan</small>
                        </div>
                    </div>
                    
                    <!-- PENYUSUTAN KENDARAAN -->
                    <div class="jurnal-option" onclick="selectOption('opt2')">
                        <input type="radio" name="jurnal_type" value="penyusutan_kendaraan" id="opt2">
                        <label for="opt2" style="display:inline; cursor:pointer; margin:0;">🚗 Penyusutan Kendaraan</label>
                        <div class="jurnal-detail" id="penyusutan_kendaraan_detail">
                            <label>Harga Perolehan Kendaraan (Rp) *</label>
                            <input type="number" name="harga_kendaraan" placeholder="Contoh: 42000000" step="0.01">
                            <small style="color:#666;">Rumus: Harga Perolehan ÷ 4 tahun ÷ 12 bulan</small>
                        </div>
                    </div>
                    
                    <!-- PENYUSUTAN PERALATAN -->
                    <div class="jurnal-option" onclick="selectOption('opt3')">
                        <input type="radio" name="jurnal_type" value="penyusutan_peralatan" id="opt3">
                        <label for="opt3" style="display:inline; cursor:pointer; margin:0;">🔧 Penyusutan Peralatan</label>
                        <div class="jurnal-detail" id="penyusutan_peralatan_detail">
                            <label>Harga Perolehan Peralatan (Rp) *</label>
                            <input type="number" name="harga_peralatan" placeholder="Contoh: 12000000" step="0.01">
                            <small style="color:#666;">Rumus: Harga Perolehan ÷ 4 tahun ÷ 12 bulan</small>
                        </div>
                    </div>
                    
                    <!-- HPP BELUT STANDAR - DUAL INPUT -->
                    <div class="jurnal-option" onclick="selectOption('opt4')">
                        <input type="radio" name="jurnal_type" value="hpp_standar" id="opt4">
                        <label for="opt4" style="display:inline; cursor:pointer; margin:0;">🐟 HPP Belut Standar</label>
                        <div class="jurnal-detail" id="hpp_standar_detail">
                            <label>Nilai HPP Belut Standar (Rp) *</label>
                            
                            <div class="input-method">
                                <button type="button" class="input-method-btn direct-btn active" onclick="switchInputMethod(event, 'hpp_standar', 'direct')">
                                    Input Langsung
                                </button>
                                <button type="button" class="input-method-btn calculator-btn" onclick="switchInputMethod(event, 'hpp_standar', 'calculator')">
                                    Kalkulator
                                </button>
                            </div>
                            
                            <!-- Direct Input -->
                            <input type="text" id="hpp_standar_direct" class="direct-input" 
                                   placeholder="Contoh: 1800000" 
                                   onblur="formatNumber(this)"
                                   oninput="updateFromDirectInput(this, 'hpp_standar')">
                            
                            <!-- Calculator Input -->
                            <input type="text" id="hpp_standar_calculator" class="calculator-input" 
                                   placeholder="Contoh: 1500000+300000"
                                   oninput="calculateExpression(this, 'hpp_standar')">
                            
                            <div class="result-display" id="hpp_standar_result"></div>
                            <div class="calculator-hint" id="hpp_standar_hint">
                                💡 Gunakan +, -, *, / untuk perhitungan. Contoh: 1500000+300000
                            </div>
                            
                            <input type="hidden" name="hpp_standar" id="hpp_standar_value">
                            <small style="color:#666;">HPP = Persediaan Awal + Pembelian - Persediaan Akhir</small>
                        </div>
                    </div>
                    
                    <!-- HPP BELUT SUPER - DUAL INPUT -->
                    <div class="jurnal-option" onclick="selectOption('opt5')">
                        <input type="radio" name="jurnal_type" value="hpp_super" id="opt5">
                        <label for="opt5" style="display:inline; cursor:pointer; margin:0;">🐟 HPP Belut Super</label>
                        <div class="jurnal-detail" id="hpp_super_detail">
                            <label>Nilai HPP Belut Super (Rp) *</label>
                            
                            <div class="input-method">
                                <button type="button" class="input-method-btn direct-btn active" onclick="switchInputMethod(event, 'hpp_super', 'direct')">
                                    Input Langsung
                                </button>
                                <button type="button" class="input-method-btn calculator-btn" onclick="switchInputMethod(event, 'hpp_super', 'calculator')">
                                    Kalkulator
                                </button>
                            </div>
                            
                            <!-- Direct Input -->
                            <input type="text" id="hpp_super_direct" class="direct-input" 
                                   placeholder="Contoh: 1650000" 
                                   onblur="formatNumber(this)"
                                   oninput="updateFromDirectInput(this, 'hpp_super')">
                            
                            <!-- Calculator Input -->
                            <input type="text" id="hpp_super_calculator" class="calculator-input" 
                                   placeholder="Contoh: 1200000+450000"
                                   oninput="calculateExpression(this, 'hpp_super')">
                            
                            <div class="result-display" id="hpp_super_result"></div>
                            <div class="calculator-hint" id="hpp_super_hint">
                                💡 Gunakan +, -, *, / untuk perhitungan. Contoh: 1200000+450000
                            </div>
                            
                            <input type="hidden" name="hpp_super" id="hpp_super_value">
                            <small style="color:#666;">HPP = Persediaan Awal + Pembelian - Persediaan Akhir</small>
                        </div>
                    </div>
                    
                    <!-- BEBAN PAKAN STANDAR - DUAL INPUT -->
                    <div class="jurnal-option" onclick="selectOption('opt6')">
                        <input type="radio" name="jurnal_type" value="pakan_standar" id="opt6">
                        <label for="opt6" style="display:inline; cursor:pointer; margin:0;">🍚 Beban Pakan Belut Standar</label>
                        <div class="jurnal-detail" id="pakan_standar_detail">
                            <label>Total Pembelian Pakan Standar (Rp) *</label>
                            
                            <div class="input-method">
                                <button type="button" class="input-method-btn direct-btn active" onclick="switchInputMethod(event, 'pakan_standar', 'direct')">
                                    Input Langsung
                                </button>
                                <button type="button" class="input-method-btn calculator-btn" onclick="switchInputMethod(event, 'pakan_standar', 'calculator')">
                                    Kalkulator
                                </button>
                            </div>
                            
                            <!-- Direct Input -->
                            <input type="text" id="pakan_standar_direct" class="direct-input" 
                                   placeholder="Contoh: 500000" 
                                   onblur="formatNumber(this)"
                                   oninput="updateFromDirectInput(this, 'pakan_standar')">
                            
                            <!-- Calculator Input -->
                            <input type="text" id="pakan_standar_calculator" class="calculator-input" 
                                   placeholder="Contoh: 200000+300000"
                                   oninput="calculateExpression(this, 'pakan_standar')">
                            
                            <div class="result-display" id="pakan_standar_result"></div>
                            <div class="calculator-hint" id="pakan_standar_hint">
                                💡 Gunakan +, -, *, / untuk perhitungan. Contoh: 200000+300000
                            </div>
                            
                            <input type="hidden" name="pakan_standar" id="pakan_standar_value">
                            <small style="color:#666;">Total pembelian pakan selama periode berjalan</small>
                        </div>
                    </div>
                    
                    <!-- BEBAN PAKAN SUPER - DUAL INPUT -->
                    <div class="jurnal-option" onclick="selectOption('opt7')">
                        <input type="radio" name="jurnal_type" value="pakan_super" id="opt7">
                        <label for="opt7" style="display:inline; cursor:pointer; margin:0;">🍚 Beban Pakan Belut Super</label>
                        <div class="jurnal-detail" id="pakan_super_detail">
                            <label>Total Pembelian Pakan Super (Rp) *</label>
                            
                            <div class="input-method">
                                <button type="button" class="input-method-btn direct-btn active" onclick="switchInputMethod(event, 'pakan_super', 'direct')">
                                    Input Langsung
                                </button>
                                <button type="button" class="input-method-btn calculator-btn" onclick="switchInputMethod(event, 'pakan_super', 'calculator')">
                                    Kalkulator
                                </button>
                            </div>
                            
                            <!-- Direct Input -->
                            <input type="text" id="pakan_super_direct" class="direct-input" 
                                   placeholder="Contoh: 600000" 
                                   onblur="formatNumber(this)"
                                   oninput="updateFromDirectInput(this, 'pakan_super')">
                            
                            <!-- Calculator Input -->
                            <input type="text" id="pakan_super_calculator" class="calculator-input" 
                                   placeholder="Contoh: 250000+350000"
                                   oninput="calculateExpression(this, 'pakan_super')">
                            
                            <div class="result-display" id="pakan_super_result"></div>
                            <div class="calculator-hint" id="pakan_super_hint">
                                💡 Gunakan +, -, *, / untuk perhitungan. Contoh: 250000+350000
                            </div>
                            
                            <input type="hidden" name="pakan_super" id="pakan_super_value">
                            <small style="color:#666;">Total pembelian pakan selama periode berjalan</small>
                        </div>
                    </div>
                </div>
                
                <button type="submit" class="btn-submit">➕ Buat Jurnal Penyesuaian</button>
            </form>
            
            <div class="back-section">
                <a href="/jurnal_penyesuaian" class="btn-back">⬅ Kembali ke Menu Jurnal Penyesuaian</a>
            </div>
        </div>

        <script>
            function selectOption(optionId) {
                // Sembunyikan semua detail
                document.querySelectorAll('.jurnal-detail').forEach(detail => {
                    detail.style.display = 'none';
                });
                
                // Check radio button
                const radio = document.getElementById(optionId);
                radio.checked = true;
                
                // Tampilkan detail yang sesuai
                const detailId = radio.value + '_detail';
                const detailElement = document.getElementById(detailId);
                if (detailElement) {
                    detailElement.style.display = 'block';
                }
            }

            function switchInputMethod(event, fieldName, method) {
                event.preventDefault();
                event.stopPropagation();
                
                const parentDetail = document.getElementById(fieldName + '_detail');
                const buttons = parentDetail.querySelectorAll('.input-method-btn');
                buttons.forEach(btn => btn.classList.remove('active'));
                
                event.target.classList.add('active');
                
                const calculatorInput = document.getElementById(fieldName + '_calculator');
                const directInput = document.getElementById(fieldName + '_direct');
                const resultDisplay = document.getElementById(fieldName + '_result');
                const hint = document.getElementById(fieldName + '_hint');
                
                if (method === 'calculator') {
                    calculatorInput.style.display = 'block';
                    directInput.style.display = 'none';
                    resultDisplay.style.display = 'block';
                    hint.style.display = 'block';
                } else {
                    calculatorInput.style.display = 'none';
                    directInput.style.display = 'block';
                    resultDisplay.style.display = 'none';
                    hint.style.display = 'none';
                    resultDisplay.textContent = '';
                }
            }

            function calculateExpression(input, fieldName) {
                const value = input.value.trim();
                const resultElement = document.getElementById(fieldName + '_result');
                const directInput = document.getElementById(fieldName + '_direct');
                const hiddenInput = document.getElementById(fieldName + '_value');
                
                if (value === '') {
                    resultElement.textContent = '';
                    hiddenInput.value = '';
                    return;
                }
                
                try {
                    const result = eval(value.replace(/,/g, ''));
                    
                    if (!isNaN(result) && isFinite(result)) {
                        const formattedResult = result.toLocaleString('id-ID');
                        resultElement.textContent = 'Hasil: Rp ' + formattedResult;
                        hiddenInput.value = result;
                        directInput.value = result;
                    } else {
                        resultElement.textContent = 'Ekspresi tidak valid';
                        hiddenInput.value = '';
                    }
                } catch (e) {
                    resultElement.textContent = 'Ekspresi tidak valid';
                    hiddenInput.value = '';
                }
            }

            function updateFromDirectInput(input, fieldName) {
                const value = input.value.replace(/,/g, '');
                const hiddenInput = document.getElementById(fieldName + '_value');
                const calculatorInput = document.getElementById(fieldName + '_calculator');
                
                if (value === '') {
                    hiddenInput.value = '';
                    return;
                }
                
                const numericValue = parseFloat(value);
                if (!isNaN(numericValue) && isFinite(numericValue)) {
                    hiddenInput.value = numericValue;
                    calculatorInput.value = numericValue;
                } else {
                    hiddenInput.value = '';
                }
            }

            function formatNumber(input) {
                const value = input.value.replace(/,/g, '');
                if (value === '') return;
                
                const numericValue = parseFloat(value);
                if (!isNaN(numericValue) && isFinite(numericValue)) {
                    input.value = numericValue.toLocaleString('id-ID');
                }
            }
        </script>
    </body>
    </html>
    """, success_msg=success_msg, error_msg=error_msg)
                                  
@app.route("/jurnal_penyesuaian/view", methods=["GET", "POST"])
def jurnal_penyesuaian_view():
    if not session.get("user_email"):
        return redirect("/")
    
    success_msg = ""
    error_msg = ""
    
    if request.method == "POST":
        try:
            entry_id = request.form.get("entry_id")
            supabase.table("adjustment_journal").delete().eq("id", entry_id).eq("user_email", session.get("user_email")).execute()
            success_msg = "✅ Entry berhasil dihapus!"
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
    
    # Ambil data jurnal penyesuaian
    try:
        res = supabase.table("adjustment_journal").select("*").eq("user_email", session.get("user_email")).order("no, id").execute()
        entries = res.data or []
    except:
        entries = []
    
    # Build rows untuk tabel
    rows = ""
    total_debit = 0
    total_kredit = 0
    
    for entry in entries:
        indent_class = "indent" if entry.get("is_indent") else ""
        debit_val = entry.get('debit', 0)
        kredit_val = entry.get('credit', 0)
        
        total_debit += debit_val
        total_kredit += kredit_val
        
        rows += f"""
        <tr>
            <td class="center">{entry.get('no', '')}</td>
            <td class="center">{entry.get('date', '')}</td>
            <td class="{indent_class}">{entry.get('description', '')}</td>
            <td class="center">{entry.get('ref', '')}</td>
            <td class="amount">{rupiah_small(debit_val) if debit_val > 0 else ''}</td>
            <td class="amount">{rupiah_small(kredit_val) if kredit_val > 0 else ''}</td>
            <td class="center no-print">
                <form method="POST" style="display:inline;" onsubmit="return confirm('Hapus entry ini?');">
                    <input type="hidden" name="entry_id" value="{entry.get('id')}">
                    <button type="submit" class="btn-delete">🗑</button>
                </form>
            </td>
        </tr>
        """
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lihat Jurnal Penyesuaian - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2, h4, h5 {
                text-align: center;
                color: #667eea;
            }
            h2 { font-size: 32px; margin-bottom: 10px; }
            h4 { font-size: 18px; color: #666; margin: 5px 0; }
            h5 { font-size: 16px; color: #666; margin: 5px 0 30px 0; }
            
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                border: 2px solid #2d3748;
            }
            th {
                background: #2d3748;
                color: white;
                padding: 12px;
                text-align: center;
                border: 1px solid #000;
                font-weight: 600;
            }
            td {
                padding: 10px;
                border: 1px solid #2d3748;
                font-size: 13px;
            }
            .indent {
                padding-left: 40px !important;
            }
            .amount {
                text-align: right;
                font-family: 'Courier New', monospace;
            }
            .center {
                text-align: center;
            }
            .total-row {
                background: #e3f2fd;
                font-weight: 700;
            }
            .btn-delete {
                background: #dc3545;
                color: white;
                padding: 5px 10px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-size: 12px;
            }
            .btn-delete:hover {
                background: #c82333;
            }
            .alert {
                padding: 15px;
                margin-bottom: 20px;
                border-radius: 8px;
                font-weight: 600;
            }
            .success {
                background: #d4edda;
                color: #155724;
                border-left: 4px solid #28a745;
            }
            .error {
                background: #f8d7da;
                color: #721c24;
                border-left: 4px solid #dc3545;
            }
            .btn-print {
                background: #6c757d;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                margin-top: 20px;
            }
            .btn-print:hover {
                background: #5a6268;
            }
            .btn-back {
                display: inline-block;
                margin-top: 20px;
                background: #667eea;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                transition: 0.3s;
            }
            .btn-back:hover {
                background: #764ba2;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            @media print {
                .no-print { display: none; }
                body { background: white; padding: 0; }
                .container { box-shadow: none; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 Jurnal Penyesuaian</h2>
            <h4>BELUT.IN</h4>
            <h4>JURNAL PENYESUAIAN</h4>
            <h5>Per 31 Desember 2025</h5>
            
            {% if success_msg %}
                <div class="alert success no-print">{{ success_msg }}</div>
            {% endif %}
            {% if error_msg %}
                <div class="alert error no-print">{{ error_msg }}</div>
            {% endif %}

            <table>
                <thead>
                    <tr>
                        <th style="width:5%;">No.</th>
                        <th style="width:10%;">Tanggal</th>
                        <th style="width:35%;">Nama Akun</th>
                        <th style="width:10%;">Ref. Post.</th>
                        <th style="width:15%;">Debit</th>
                        <th style="width:15%;">Kredit</th>
                        <th class="no-print" style="width:10%;">Aksi</th>
                    </tr>
                </thead>
                <tbody>
                    {% if rows %}
                        {{ rows|safe }}
                        <tr class="total-row">
                            <td colspan="4" style="text-align:right;"><strong>TOTAL</strong></td>
                            <td class="amount"><strong>{{ total_debit }}</strong></td>
                            <td class="amount"><strong>{{ total_kredit }}</strong></td>
                            <td class="no-print"></td>
                        </tr>
                    {% else %}
                        <tr>
                            <td colspan="7" style="text-align:center; padding:30px; color:#999;">
                                Belum ada data jurnal penyesuaian.<br>
                                Klik "Input Transaksi" untuk menambahkan data.
                            </td>
                        </tr>
                    {% endif %}
                </tbody>
            </table>
            
            <div style="text-align:center;" class="no-print">
                <button onclick="window.print()" class="btn-print">🖨 Print Jurnal</button>
            </div>
            
            <div class="back-section no-print">
                <a href="/jurnal_penyesuaian" class="btn-back">⬅ Kembali ke Menu Jurnal Penyesuaian</a>
            </div>
        </div>
    </body>
    </html>
    """, 
    rows=rows,
    total_debit=rupiah_small(total_debit),
    total_kredit=rupiah_small(total_kredit),
    success_msg=success_msg, 
    error_msg=error_msg)

@app.route("/neraca_saldo_setelah_penyesuaian")
def neraca_saldo_setelah_penyesuaian():
    if not session.get("user_email"):
        return redirect("/")
    
    # AMBIL DATA DARI GENERAL JOURNAL
    akun_dict = get_akun_dict()
    
    # TAMBAHKAN DATA DARI ADJUSTMENT JOURNAL (JURNAL PENYESUAIAN)
    try:
        res = supabase.table("adjustment_journal").select("*").eq("user_email", session.get("user_email")).execute()
        adj_entries = res.data or []
        
        for entry in adj_entries:
            kode = entry.get('ref', '')
            debit = entry.get('debit', 0)
            kredit = entry.get('credit', 0)
            nama_akun = entry.get('description', '')
            
            if kode:
                if kode not in akun_dict:
                    # Jika akun belum ada, buat entry baru
                    akun_dict[kode] = {
                        'akun': nama_akun,
                        'total_debit': 0,
                        'total_kredit': 0
                    }
                
                # Tambahkan debit dan kredit dari jurnal penyesuaian
                akun_dict[kode]['total_debit'] += debit
                akun_dict[kode]['total_kredit'] += kredit
    except Exception as e:
        print(f"Error mengambil adjustment journal: {str(e)}")
    
    # ==============================
    # HITUNG SALDO AKHIR PER AKUN
    # ==============================
    neraca_html = ""
    total_debit_final = 0
    total_kredit_final = 0
    
    for kode in sorted(akun_dict.keys()):
        data = akun_dict[kode]
        total_debit = data["total_debit"]
        total_kredit = data["total_kredit"]
        
        # Hitung saldo nett
        saldo = total_debit - total_kredit
        
        # Tentukan posisi saldo berdasarkan saldo normal akun
        if kode.startswith('1-') or kode.startswith('5-') or kode.startswith('6-'):
            # Akun normal debit (Aset, HPP, Beban)
            if saldo >= 0:
                debit_display = saldo
                kredit_display = 0
            else:
                debit_display = 0
                kredit_display = abs(saldo)
        else:
            # Akun normal kredit (Kewajiban, Modal, Pendapatan)
            if saldo <= 0:
                debit_display = abs(saldo)
                kredit_display = 0
            else:
                debit_display = 0
                kredit_display = saldo
        
        # Hanya tampilkan akun yang punya saldo
        if debit_display > 0 or kredit_display > 0:
            total_debit_final += debit_display
            total_kredit_final += kredit_display
            
            neraca_html += f"""
            <tr>
                <td>{kode}</td>
                <td>{data['akun']}</td>
                <td style='text-align:right;'>{rupiah_small(debit_display) if debit_display > 0 else '-'}</td>
                <td style='text-align:right;'>{rupiah_small(kredit_display) if kredit_display > 0 else '-'}</td>
            </tr>
            """
    
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Neraca Saldo Setelah Penyesuaian - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .info-box {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }
            .info-box p {
                color: #2d3748;
                font-size: 14px;
                margin: 5px 0;
            }
            .alert-box {
                background: #d4edda;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                border-left: 4px solid #28a745;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-radius: 12px;
                overflow: hidden;
            }
            thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e2e8f0;
                color: #2d3748;
            }
            tbody tr:hover { background: #f7fafc; }
            tfoot {
                background: #f7fafc;
                font-weight: 700;
            }
            tfoot td {
                padding: 15px;
                font-size: 16px;
                border-top: 3px solid #667eea;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .back-section a {
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 600;
                transition: transform 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .back-section a:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            .btn-print {
                background: #6c757d;
                color: white;
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-weight: 600;
                margin-top: 20px;
            }
            .btn-print:hover {
                background: #5a6268;
            }
            @media print {
                .no-print { display: none; }
                body { background: white; padding: 0; }
                .container { box-shadow: none; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📊 Neraca Saldo Setelah Penyesuaian</h2>
            
            <div class="info-box">
                <p><strong>BELUT.IN - NERACA SALDO SETELAH PENYESUAIAN</strong></p>
                <p>Per 31 Desember 2025</p>
            </div>
            
            <div class="alert-box">
                <p style="color:#28a745; font-weight:600;">✓ Sudah termasuk jurnal penyesuaian</p>
                <p style="color:#666; font-size:13px; margin-top:5px;">
                    Saldo di bawah ini sudah menyertakan semua transaksi dari Jurnal Umum dan Jurnal Penyesuaian
                </p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width:15%;">Kode Akun</th>
                        <th style="width:45%;">Nama Akun</th>
                        <th style="width:20%; text-align:right;">Debit</th>
                        <th style="width:20%; text-align:right;">Kredit</th>
                    </tr>
                </thead>
                <tbody>
                    {{ neraca_html|safe }}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2" style="text-align:right;"><strong>TOTAL</strong></td>
                        <td style="text-align:right;"><strong>{{ total_debit }}</strong></td>
                        <td style="text-align:right;"><strong>{{ total_kredit }}</strong></td>
                    </tr>
                </tfoot>
            </table>
            
            <div style="text-align:center;" class="no-print">
                <button onclick="window.print()" class="btn-print">🖨 Print Neraca Saldo</button>
            </div>
            
            <div class="back-section no-print">
                <a href="/akuntansi">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """, 
    neraca_html=neraca_html,
    total_debit=rupiah_small(total_debit_final),
    total_kredit=rupiah_small(total_kredit_final))

@app.route("/jurnal_penutup")
def jurnal_penutup():
    if not session.get("user_email"):
        return redirect("/")

    akun_dict = get_akun_dict()

    # Perhitungan untuk jurnal penutup
    pendapatan = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('4-'))
    beban = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() if k.startswith('5-') or k.startswith('6-'))
    laba_rugi = pendapatan - beban
    prive = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() if k == '3-1200')

    # Membuat entri jurnal penutup
    jurnal_rows = ""
    
    # Menutup Pendapatan ke Ikhtisar Laba Rugi
    jurnal_rows += f"""
    <tr style="background:#e3f2fd;">
        <td colspan="4"><strong>Menutup Akun Pendapatan</strong></td>
    </tr>
    """
    for k, v in akun_dict.items():
        if k.startswith('4-') and (v['total_kredit'] - v['total_debit']) > 0:
            jurnal_rows += f"""
            <tr>
                <td style="padding-left:20px;">{v['akun']}</td>
                <td style="text-align:right;">{rupiah_small(v['total_kredit'] - v['total_debit'])}</td>
                <td style="text-align:right;">-</td>
                <td></td>
            </tr>
            """
    jurnal_rows += f"""
    <tr>
        <td style="padding-left:40px;">Ikhtisar Laba Rugi</td>
        <td style="text-align:right;">-</td>
        <td style="text-align:right;">{rupiah_small(pendapatan)}</td>
        <td style="font-style:italic; color:#666;">Menutup pendapatan</td>
    </tr>
    <tr style="height:10px;"><td colspan="4"></td></tr>
    """
    
    # Menutup Beban ke Ikhtisar Laba Rugi
    jurnal_rows += f"""
    <tr style="background:#e3f2fd;">
        <td colspan="4"><strong>Menutup Akun Beban</strong></td>
    </tr>
    <tr>
        <td style="padding-left:20px;">Ikhtisar Laba Rugi</td>
        <td style="text-align:right;">{rupiah_small(beban)}</td>
        <td style="text-align:right;">-</td>
        <td></td>
    </tr>
    """
    for k, v in akun_dict.items():
        if (k.startswith('5-') or k.startswith('6-')) and (v['total_debit'] - v['total_kredit']) > 0:
            jurnal_rows += f"""
            <tr>
                <td style="padding-left:40px;">{v['akun']}</td>
                <td style="text-align:right;">-</td>
                <td style="text-align:right;">{rupiah_small(v['total_debit'] - v['total_kredit'])}</td>
                <td></td>
            </tr>
            """
    jurnal_rows += f"""
    <tr>
        <td colspan="4" style="font-style:italic; color:#666; text-align:right;">Menutup beban</td>
    </tr>
    <tr style="height:10px;"><td colspan="4"></td></tr>
    """
    
    # Menutup Prive ke Modal
    if prive > 0:
        jurnal_rows += f"""
        <tr style="background:#e3f2fd;">
            <td colspan="4"><strong>Menutup Akun Prive</strong></td>
        </tr>
        <tr>
            <td style="padding-left:20px;">Modal Pemilik</td>
            <td style="text-align:right;">{rupiah_small(prive)}</td>
            <td style="text-align:right;">-</td>
            <td></td>
        </tr>
        <tr>
            <td style="padding-left:40px;">Prive</td>
            <td style="text-align:right;">-</td>
            <td style="text-align:right;">{rupiah_small(prive)}</td>
            <td style="font-style:italic; color:#666;">Menutup prive</td>
        </tr>
        <tr style="height:10px;"><td colspan="4"></td></tr>
        """

    # Menutup Ikhtisar Laba Rugi ke Modal
    if laba_rugi >= 0:
        jurnal_rows += f"""
        <tr style="background:#e3f2fd;">
            <td colspan="4"><strong>Menutup Laba Bersih ke Modal</strong></td>
        </tr>
        <tr>
            <td style="padding-left:20px;">Ikhtisar Laba Rugi</td>
            <td style="text-align:right;">{rupiah_small(laba_rugi)}</td>
            <td style="text-align:right;">-</td>
            <td></td>
        </tr>
        <tr>
            <td style="padding-left:40px;">Modal Pemilik</td>
            <td style="text-align:right;">-</td>
            <td style="text-align:right;">{rupiah_small(laba_rugi)}</td>
            <td style="font-style:italic; color:#666;">Menutup laba bersih</td>
        </tr>
        """
    else:
        jurnal_rows += f"""
        <tr style="background:#e3f2fd;">
            <td colspan="4"><strong>Menutup Rugi Bersih ke Modal</strong></td>
        </tr>
        <tr>
            <td style="padding-left:20px;">Modal Pemilik</td>
            <td style="text-align:right;">{rupiah_small(abs(laba_rugi))}</td>
            <td style="text-align:right;">-</td>
            <td></td>
        </tr>
        <tr>
            <td style="padding-left:40px;">Ikhtisar Laba Rugi</td>
            <td style="text-align:right;">-</td>
            <td style="text-align:right;">{rupiah_small(abs(laba_rugi))}</td>
            <td style="font-style:italic; color:#666;">Menutup rugi bersih</td>
        </tr>
        """
    jurnal_rows += "<tr style='height:10px;'><td colspan='4'></td></tr>"

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Jurnal Penutup - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .info-box {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }
            .info-box p {
                color: #2d3748;
                font-size: 14px;
                margin: 5px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-radius: 12px;
                overflow: hidden;
            }
            thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e2e8f0;
                color: #2d3748;
            }
            tbody tr:hover { background: #f7fafc; }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .back-section a {
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 600;
                transition: transform 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .back-section a:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📕 Jurnal Penutup</h2>
            
            <div class="info-box">
                <p><strong>BELUT.IN - JURNAL PENUTUP</strong></p>
                <p>Per 31 Desember 2025</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width:45%;">Akun</th>
                        <th style="width:20%;">Debit</th>
                        <th style="width:20%;">Kredit</th>
                        <th style="width:15%;">Keterangan</th>
                    </tr>
                </thead>
                <tbody>
                    {{ jurnal_rows|safe }}
                </tbody>
            </table>
            
            <div class="back-section">
                <a href="/akuntansi">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """, jurnal_rows=jurnal_rows)

@app.route("/buku_besar")
def buku_besar():
    if not session.get("user_email"):
        return redirect("/")

    user = session.get("user_email")
    
    # ==============================
    # 1. AMBIL SALDO AWAL
    # ==============================
    try:
        res_saldo = supabase.table("opening_balance").select("*").execute()
        saldo_awal_data = res_saldo.data or []
    except:
        saldo_awal_data = []
    
    saldo_awal_dict = {}
    for s in saldo_awal_data:
        kode = s.get("account_code")
        saldo_awal_dict[kode] = {
            "nama": s.get("account_name"),
            "debit": float(s.get("debit") or 0),
            "kredit": float(s.get("credit") or 0)
        }
    
    # ==============================
    # 2. AMBIL JURNAL UMUM
    # ==============================
    try:
        res = supabase.table("general_journal").select("*") \
            .eq("user_email", user) \
            .order("date", desc=False) \
            .order("id", desc=False) \
            .execute()
        journal_data = res.data or []
    except Exception as e:
        print(f"Error fetching journal: {e}")
        journal_data = []

    # ==============================
    # 3. PARSE LINES & REKAPITULASI PER AKUN
    # ==============================
    buku_besar = {}
    
    for j in journal_data:
        lines = j.get("lines", [])
        
        # Parse jika lines masih string
        if isinstance(lines, str):
            try:
                lines = json.loads(lines)
            except:
                lines = []
        
        # Loop setiap line
        for line in lines:
            kode = line.get("account_code")
            akun = line.get("account_name")
            debit = float(line.get("debit") or 0)
            kredit = float(line.get("credit") or 0)
            
            if kode not in buku_besar:
                buku_besar[kode] = {
                    "nama": akun,
                    "total_debit": 0,
                    "total_kredit": 0
                }
            
            buku_besar[kode]["total_debit"] += debit
            buku_besar[kode]["total_kredit"] += kredit

    # ==============================
    # 4. AMBIL JURNAL PENYESUAIAN
    # ==============================
    jp_per_akun = {}
    try:
        res2 = supabase.table("adjustment_journal").select("*") \
            .eq("user_email", user).order("date,id").execute()
        journal_adjust = res2.data or []
        
        for a in journal_adjust:
            kode = a.get("ref")
            debit = float(a.get("debit") or 0)
            kredit = float(a.get("credit") or 0)
            
            if kode not in jp_per_akun:
                jp_per_akun[kode] = {
                    "nama": a.get("description"),
                    "total_debit": 0,
                    "total_kredit": 0
                }
            
            jp_per_akun[kode]["total_debit"] += debit
            jp_per_akun[kode]["total_kredit"] += kredit
    except:
        journal_adjust = []

    # ==============================
    # 5. HITUNG LABA RUGI DAN PRIVE UNTUK JURNAL PENUTUP
    # ==============================
    pendapatan_total = sum(v['total_kredit'] - v['total_debit'] for k, v in buku_besar.items() if k.startswith('4-'))
    beban_total = sum(v['total_debit'] - v['total_kredit'] for k, v in buku_besar.items() if k.startswith('5-') or k.startswith('6-'))
    laba_rugi = pendapatan_total - beban_total
    prive_total = sum(v['total_debit'] for k, v in buku_besar.items() if k.startswith('3-2'))

    # ==============================
    # 6. GABUNGKAN SEMUA AKUN
    # ==============================
    semua_akun = set(saldo_awal_dict.keys()) | set(buku_besar.keys()) | set(jp_per_akun.keys())

    # ==============================
    # 7. GENERATE HTML - JURNAL PENUTUP DIREKAP SATU BARIS
    # ==============================
    html_output = ""
    
    for kode in sorted(semua_akun):
        # Ambil nama akun
        if kode in buku_besar:
            nama_akun = buku_besar[kode]["nama"]
        elif kode in saldo_awal_dict:
            nama_akun = saldo_awal_dict[kode]["nama"]
        elif kode in jp_per_akun:
            nama_akun = jp_per_akun[kode]["nama"]
        else:
            nama_akun = kode
        
        # Tentukan posisi saldo
        if kode.startswith('1-') or kode.startswith('5-') or kode.startswith('6-'):
            pos_saldo = "Debit"
        else:
            pos_saldo = "Kredit"
        
        # Hitung saldo awal
        if kode in saldo_awal_dict:
            saldo_awal_debit = saldo_awal_dict[kode]["debit"]
            saldo_awal_kredit = saldo_awal_dict[kode]["kredit"]
            if pos_saldo == "Debit":
                saldo_awal = saldo_awal_debit - saldo_awal_kredit
            else:
                saldo_awal = saldo_awal_kredit - saldo_awal_debit
        else:
            saldo_awal = 0
        
        html_output += f"""
        <div class="ledger-section">
            <div class="ledger-header">
                <div class="header-left">
                    <strong>Kode Akun</strong> {kode}<br>
                    <strong>Nama Akun</strong> {nama_akun}
                </div>
                <div class="header-right">
                    <strong>Pos Saldo</strong> {pos_saldo}<br>
                    <strong>Saldo Awal</strong> {rupiah_small(abs(saldo_awal))}
                </div>
            </div>
            
            <table class="ledger-table">
                <thead>
                    <tr>
                        <th style="width:8%;">No</th>
                        <th style="width:15%;">Tanggal</th>
                        <th style="width:10%;">Bukti</th>
                        <th style="width:37%;">Keterangan</th>
                        <th style="width:15%;">Debet</th>
                        <th style="width:15%;">Kredit</th>
                        <th style="width:15%;">Saldo</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        saldo = saldo_awal
        no_transaksi = 1
        
        # 1. Transaksi Jurnal Umum (jika ada)
        if kode in buku_besar:
            total_debit = buku_besar[kode]["total_debit"]
            total_kredit = buku_besar[kode]["total_kredit"]
            
            if pos_saldo == "Debit":
                saldo += total_debit - total_kredit
            else:
                saldo += total_kredit - total_debit
            
            html_output += f"""
                    <tr>
                        <td style="text-align:center;">{no_transaksi}</td>
                        <td style="text-align:center;">31/12/2025</td>
                        <td style="text-align:center;">JU</td>
                        <td>Rekapitulasi Jurnal Umum</td>
                        <td style="text-align:right;">{rupiah_small(total_debit) if total_debit > 0 else ''}</td>
                        <td style="text-align:right;">{rupiah_small(total_kredit) if total_kredit > 0 else ''}</td>
                        <td style="text-align:right;">{rupiah_small(abs(saldo))}</td>
                    </tr>
            """
            no_transaksi += 1
        
        # 2. Jurnal Penyesuaian (jika ada)
        if kode in jp_per_akun:
            total_debit_jp = jp_per_akun[kode]["total_debit"]
            total_kredit_jp = jp_per_akun[kode]["total_kredit"]
            
            if pos_saldo == "Debit":
                saldo += total_debit_jp - total_kredit_jp
            else:
                saldo += total_kredit_jp - total_debit_jp
            
            html_output += f"""
                    <tr>
                        <td style="text-align:center;">{no_transaksi}</td>
                        <td style="text-align:center;">31/12/2025</td>
                        <td style="text-align:center;">JPE</td>
                        <td>Rekapitulasi Jurnal Penyesuaian</td>
                        <td style="text-align:right;">{rupiah_small(total_debit_jp) if total_debit_jp > 0 else ''}</td>
                        <td style="text-align:right;">{rupiah_small(total_kredit_jp) if total_kredit_jp > 0 else ''}</td>
                        <td style="text-align:right;">{rupiah_small(abs(saldo))}</td>
                    </tr>
            """
            no_transaksi += 1
        
        # 3. Jurnal Penutup - REKAPITULASI SATU BARIS
        total_debit_jpt = 0
        total_kredit_jpt = 0
        
        # Untuk akun pendapatan dan beban - ditutup ke 0
        if kode.startswith('4-') or kode.startswith('5-') or kode.startswith('6-'):
            if saldo != 0:
                if kode.startswith('4-'):  # Pendapatan (normal balance kredit)
                    total_debit_jpt = abs(saldo)
                else:  # Beban (normal balance debit)
                    total_kredit_jpt = abs(saldo)
        
        # Untuk akun prive - ditutup ke Modal
        elif kode.startswith('3-2') and prive_total > 0:
            total_kredit_jpt = prive_total
        
        # Untuk akun modal - penutupan laba/rugi dan prive
        elif kode == '3-1100':
            if laba_rugi > 0:
                total_kredit_jpt = laba_rugi
            elif laba_rugi < 0:
                total_debit_jpt = abs(laba_rugi)
            
            if prive_total > 0:
                total_debit_jpt += prive_total
        
        # Tampilkan Jurnal Penutup jika ada transaksi
        if total_debit_jpt > 0 or total_kredit_jpt > 0:
            # Update saldo
            if pos_saldo == "Debit":
                saldo += total_debit_jpt - total_kredit_jpt
            else:
                saldo += total_kredit_jpt - total_debit_jpt
            
            html_output += f"""
                    <tr>
                        <td style="text-align:center;">{no_transaksi}</td>
                        <td style="text-align:center;">31/12/2025</td>
                        <td style="text-align:center;">JPT</td>
                        <td>Rekapitulasi Jurnal Penutup</td>
                        <td style="text-align:right;">{rupiah_small(total_debit_jpt) if total_debit_jpt > 0 else ''}</td>
                        <td style="text-align:right;">{rupiah_small(total_kredit_jpt) if total_kredit_jpt > 0 else ''}</td>
                        <td style="text-align:right;">{rupiah_small(abs(saldo))}</td>
                    </tr>
            """
        
        # Jika tidak ada transaksi sama sekali
        if no_transaksi == 1:
            html_output += f"""
                    <tr>
                        <td colspan="7" style="text-align:center; font-style:italic; color:#666; padding:15px;">
                            Tidak ada transaksi untuk akun ini
                        </td>
                    </tr>
            """
        
        html_output += """
                </tbody>
            </table>
        </div>
        """

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Buku Besar - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 40px;
                font-size: 32px;
            }
            .info-box {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }
            .info-box p {
                color: #2d3748;
                font-size: 14px;
                margin: 5px 0;
            }
            .ledger-section {
                margin-bottom: 40px;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            }
            .ledger-header {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 15px 20px;
                display: flex;
                justify-content: space-between;
                font-size: 13px;
            }
            .header-left strong, .header-right strong {
                color: #2d3748;
                margin-right: 10px;
            }
            .ledger-table {
                width: 100%;
                border-collapse: collapse;
                background: white;
            }
            .ledger-table thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .ledger-table th {
                padding: 12px 8px;
                font-weight: 600;
                font-size: 13px;
                text-transform: uppercase;
            }
            .ledger-table td {
                padding: 10px 8px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 13px;
                color: #2d3748;
            }
            .ledger-table tbody tr:nth-child(even) {
                background: #f7fafc;
            }
            .ledger-table tbody tr:hover {
                background: #edf2f7;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .back-section a {
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 600;
                transition: transform 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .back-section a:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>📒 Buku Besar Lengkap</h2>
            
            <div class="info-box">
                <p><strong>BELUT.IN - BUKU BESAR LENGKAP</strong></p>
                <p>Menampilkan semua transaksi: Jurnal Umum → Penyesuaian → Penutupan</p>
                <p>Per 31 Desember 2025</p>
            </div>

            {{ html_output|safe }}
            
            <div class="back-section">
                <a href="/akuntansi">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """, html_output=html_output)
@app.route("/neraca_saldo_penutup")
def neraca_saldo_penutup():
    if not session.get("user_email"):
        return redirect("/")

    akun_dict = get_akun_dict()
    
    # Perhitungan untuk jurnal penutup
    pendapatan = sum(v['total_kredit'] - v['total_debit'] for k, v in akun_dict.items() if k.startswith('4-'))
    beban = sum(v['total_debit'] - v['total_kredit'] for k, v in akun_dict.items() if k.startswith('5-') or k.startswith('6-'))
    laba_rugi = pendapatan - beban
    prive = sum(v['total_debit'] for k, v in akun_dict.items() if k.startswith('3-2'))

    # Buat rows untuk neraca saldo setelah penutupan
    neraca_rows = ""
    total_debit = 0
    total_kredit = 0
    
    # Hanya tampilkan akun neraca
    for kode, data in sorted(akun_dict.items()):
        # Skip akun nominal
        if kode.startswith('4-') or kode.startswith('5-') or kode.startswith('6-') or kode.startswith('3-2'):
            continue
        
        saldo = data['total_debit'] - data['total_kredit']
        
        # Adjust modal
        if kode.startswith('3-1'):
            saldo = saldo + laba_rugi - prive
        
        if saldo > 0:
            debit_val = saldo
            kredit_val = 0
            total_debit += debit_val
        else:
            debit_val = 0
            kredit_val = abs(saldo)
            total_kredit += kredit_val
        
        neraca_rows += f"""
        <tr>
            <td>{kode}</td>
            <td>{data['akun']}</td>
            <td style="text-align:right;">{rupiah_small(debit_val) if debit_val > 0 else '-'}</td>
            <td style="text-align:right;">{rupiah_small(kredit_val) if kredit_val > 0 else '-'}</td>
        </tr>
        """

    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Neraca Saldo Setelah Penutup - BELUT.IN</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Poppins', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            .container {
                max-width: 1400px;
                margin: 40px auto;
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 15px 50px rgba(0,0,0,0.3);
            }
            h2 {
                color: #667eea;
                text-align: center;
                margin-bottom: 30px;
                font-size: 32px;
            }
            .info-box {
                background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
                padding: 20px;
                border-radius: 15px;
                margin-bottom: 30px;
                text-align: center;
            }
            .info-box p {
                color: #2d3748;
                font-size: 14px;
                margin: 5px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                border-radius: 12px;
                overflow: hidden;
            }
            thead {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            th {
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
                text-transform: uppercase;
            }
            td {
                padding: 12px 15px;
                border-bottom: 1px solid #e2e8f0;
                color: #2d3748;
            }
            tbody tr:hover { background: #f7fafc; }
            tfoot {
                background: #f7fafc;
                font-weight: 700;
            }
            tfoot td {
                padding: 15px;
                font-size: 16px;
                border-top: 3px solid #667eea;
            }
            .back-section {
                text-align: center;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e2e8f0;
            }
            .back-section a {
                display: inline-block;
                padding: 12px 30px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: 600;
                transition: transform 0.3s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            .back-section a:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>⚖ Neraca Saldo Setelah Penutup</h2>
            
            <div class="info-box">
                <p><strong>BELUT.IN - NERACA SALDO SETELAH PENUTUP</strong></p>
                <p>Per 31 Desember 2025</p>
                <p style="font-style:italic; margin-top:10px;">💡 Hanya menampilkan akun neraca (Aset, Liabilitas, dan Modal setelah penutupan)</p>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width:15%;">Kode</th>
                        <th style="width:45%;">Nama Akun</th>
                        <th style="width:20%;">Debit</th>
                        <th style="width:20%;">Kredit</th>
                    </tr>
                </thead>
                <tbody>
                    {{ neraca_rows|safe }}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2"><strong>TOTAL</strong></td>
                        <td style="text-align:right;"><strong>{{ total_debit }}</strong></td>
                        <td style="text-align:right;"><strong>{{ total_kredit }}</strong></td>
                    </tr>
                </tfoot>
            </table>
            
            <div class="back-section">
                <a href="/akuntansi">⬅ Kembali ke Menu Akuntansi</a>
            </div>
        </div>
    </body>
    </html>
    """, 
    neraca_rows=neraca_rows,
    total_debit=rupiah_small(total_debit),
    total_kredit=rupiah_small(total_kredit))

if __name__ == "__main__":
    app.run(debug=True)
