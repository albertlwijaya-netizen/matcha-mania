from flask import Flask, render_template, session, redirect, url_for, jsonify, request
from auth import auth_bp
from admin import admin_bp
from koneksi import get_db_connection # Ganti importnya ke sini

app = Flask(__name__)
app.secret_key = "kopi_matcha_rahasia"

# Daftarkan Blueprint
app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)

@app.route("/")
def home():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    
    # Arahkan berdasarkan role
    if session.get('role') == 'admin':
        return render_template("admin_dashboard.html", user=session)
    else:
        return render_template("index.html", user=session)

# =========================
# GET PRODUK (Untuk Tampilan Kasir)
# =========================
@app.route("/produk", methods=["GET"])
def get_produk():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM produk")
        data = cursor.fetchall()
        return jsonify(data)
    finally:
        cursor.close()
        db.close()

# =========================
# CHECKOUT
# =========================
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    sql = """
    INSERT INTO transaksi(pelanggan, tipe_order, metode_bayar, subtotal, diskon, pajak, total, bayar, kembalian, pesanan)
    VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    val = (
        data["pelanggan"], data["tipe_order"], data["metode_bayar"],
        data["subtotal"], data["diskon"], data["pajak"],
        data["total"], data["bayar"], data["kembalian"], data["pesanan"]
    )
    
    try:
        cursor.execute(sql, val)
        db.commit()
        return jsonify({"message": "Checkout Berhasil"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()

@app.route("/transaksi", methods=["GET"])
def histori():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Ambil 20 transaksi terakhir
        cursor.execute("SELECT * FROM transaksi ORDER BY created_at DESC LIMIT 20")
        data = cursor.fetchall()
        return jsonify(data)
    finally:
        cursor.close()
        db.close()
        
if __name__ == "__main__":
    app.run(debug=True, port=5000)