from flask import Blueprint, jsonify, request, session
from koneksi import get_db_connection

# 1. DEFINISIKAN BLUEPRINT
admin_bp = Blueprint('admin', __name__)

# =========================
# DASHBOARD STATS
# =========================
@admin_bp.route("/api/stats")
def get_stats():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Gunakan IFNULL agar jika data kosong hasilnya 0 (bukan None)
        cursor.execute("SELECT IFNULL(SUM(total), 0) as omset, COUNT(*) as transaksi FROM transaksi")
        stats = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as total_produk FROM produk")
        produk = cursor.fetchone()
        
        return jsonify({
            "omset": stats['omset'],
            "transaksi": stats['transaksi'],
            "total_produk": produk['total_produk']
        })
    finally:
        cursor.close()
        db.close()

# =========================
# MANAJEMEN USER (KASIR)
# =========================

@admin_bp.route("/api/users", methods=["GET"])
def get_users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id, username, role, is_active FROM users WHERE username != %s", (session.get('username'),))
        users = cursor.fetchall()
        return jsonify(users)
    finally:
        cursor.close()
        db.close()

@admin_bp.route("/api/users", methods=["POST"])
def tambah_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'kasir')

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"error": "Username sudah terdaftar!"}), 400
        
        sql = "INSERT INTO users (username, password, role, is_active) VALUES (%s, %s, %s, TRUE)"
        cursor.execute(sql, (username, password, role))
        db.commit()
        return jsonify({"message": "User berhasil didaftarkan!"})
    finally:
        cursor.close()
        db.close()

@admin_bp.route("/api/users/toggle/<int:user_id>", methods=["POST"])
def toggle_user(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user: return jsonify({"error": "User tidak ditemukan"}), 404
            
        new_status = not user['is_active']
        cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
        db.commit()
        return jsonify({"message": "Status diperbarui", "new_status": new_status})
    finally:
        cursor.close()
        db.close()

# =========================
# MANAJEMEN PRODUK (MENU)
# =========================

@admin_bp.route("/produk", methods=["POST"])
def tambah_produk():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Perbaikan: %s harus berjumlah 6 sesuai kolom
        sql = "INSERT INTO produk (cat, nama, harga, gambar, badge, stok) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (data['cat'], data['nama'], data['harga'], data['gambar'], data.get('badge', ''), data.get('stok', 0))
        cursor.execute(sql, val)
        db.commit()
        return jsonify({"message": "Produk berhasil ditambah"})
    finally:
        cursor.close()
        db.close()

@admin_bp.route("/produk/<int:id>", methods=["PUT"])
def edit_produk(id):
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        sql = """
            UPDATE produk 
            SET nama=%s, harga=%s, cat=%s, gambar=%s, stok=%s
            WHERE id=%s
        """
        val = (data['nama'], data['harga'], data['cat'], data['gambar'], data.get('stok', 0), id)
        cursor.execute(sql, val)
        db.commit()
        return jsonify({"message": "Produk diperbarui"})
    finally:
        cursor.close()
        db.close()

@admin_bp.route("/produk/<int:id>", methods=["DELETE"])
def hapus_produk(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM produk WHERE id=%s", (id,))
        db.commit()
        return jsonify({"message": "Produk dihapus"})
    finally:
        cursor.close()
        db.close()

# =========================
# LAPORAN PENJUALAN
# =========================

@admin_bp.route("/api/laporan/ringkasan")
def laporan_ringkasan():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # 1. RINGKASAN TOTAL (Tanpa Group By - Aman)
        cursor.execute("""
            SELECT IFNULL(SUM(total), 0) as total_duit, 
                   COUNT(*) as total_nota 
            FROM transaksi 
            WHERE DATE(created_at) BETWEEN %s AND %s
        """, (start_date, end_date))
        summary = cursor.fetchone()

        # 2. DATA GRAFIK (Grouping diperbaiki menggunakan alias yang sama)
        cursor.execute("""
            SELECT DATE(created_at) as tanggal, 
                   IFNULL(SUM(total), 0) as omset_harian
            FROM transaksi 
            WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY tanggal
            ORDER BY tanggal ASC
        """, (start_date, end_date))
        data_grafik = cursor.fetchall()

        # 3. PERFORMA KASIR
        cursor.execute("""
            SELECT kasir, 
                   IFNULL(SUM(total), 0) as total_omset, 
                   COUNT(*) as jml_transaksi
            FROM transaksi 
            WHERE DATE(created_at) BETWEEN %s AND %s
            GROUP BY kasir
            ORDER BY total_omset DESC
        """, (start_date, end_date))
        data_kasir = cursor.fetchall()

        # Proses data agar JSON aman dikirim (konversi decimal ke float)
        return jsonify({
            "total_omzet": float(summary['total_duit']),
            "total_transaksi": int(summary['total_nota']),
            "grafik": data_grafik,
            "kasir": data_kasir
        })
    except Exception as e:
        print(f"Error Laporan: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        db.close()