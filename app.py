from flask import Flask, render_template, session, redirect, url_for, jsonify, request
from auth import auth_bp
from admin import admin_bp
from koneksi import get_db_connection

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
# CHECKOUT (DENGAN POTONG STOK)
# =========================
@app.route("/checkout", methods=["POST"])
def checkout():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    
    try:
        # 1. POTONG STOK
        # Frontend harus mengirimkan array 'cart_items' berisi [{id:1, qty:2}, ...]
        items = data.get('cart_items', [])
        
        for item in items:
            # Cek stok di DB dulu
            cursor.execute("SELECT stok, nama FROM produk WHERE id = %s", (item['id'],))
            res = cursor.fetchone()
            
            if not res:
                return jsonify({"error": "Produk tidak ditemukan"}), 404
                
            if res['stok'] < item['qty']:
                return jsonify({"error": f"Stok {res['nama']} tidak cukup!"}), 400
            
            # Update/Potong Stok
            cursor.execute("UPDATE produk SET stok = stok - %s WHERE id = %s", (item['qty'], item['id']))

        # 2. SIMPAN TRANSAKSI
        sql = """
        INSERT INTO transaksi(pelanggan, tipe_order, metode_bayar, subtotal, diskon, pajak, total, bayar, kembalian, pesanan, kasir)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """
        val = (
            data["pelanggan"], data["tipe_order"], data["metode_bayar"],
            data["subtotal"], data["diskon"], data["pajak"],
            data["total"], data["bayar"], data["kembalian"], data["pesanan"], data["kasir"]
        )
        cursor.execute(sql, val)
        
        # 3. COMMIT SEMUA PERUBAHAN (Stok + Transaksi)
        db.commit()
        return jsonify({"message": "Checkout Berhasil"})

    except Exception as e:
        # Jika ada error, batalkan semua perubahan (rollback)
        db.rollback()
        print(f"Error Checkout: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()

# =========================
# HISTORI TRANSAKSI
# =========================
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

    