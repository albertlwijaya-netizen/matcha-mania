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
        # Hitung Omset dan Total Transaksi
        cursor.execute("SELECT SUM(total) as omset, COUNT(*) as transaksi FROM transaksi")
        stats = cursor.fetchone()
        
        # Hitung Total Produk
        cursor.execute("SELECT COUNT(*) as total_produk FROM produk")
        produk = cursor.fetchone()
        
        return jsonify({
            "omset": stats['omset'] or 0,
            "transaksi": stats['transaksi'] or 0,
            "total_produk": produk['total_produk'] or 0
        })
    finally:
        cursor.close()
        db.close()

# =========================
# MANAJEMEN USER (KASIR)
# =========================

# Ambil daftar semua kasir
@admin_bp.route("/api/users", methods=["GET"])
def get_users():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Menampilkan semua user kecuali admin yang sedang login
        cursor.execute("SELECT id, username, role, is_active FROM users WHERE username != %s", (session.get('username'),))
        users = cursor.fetchall()
        return jsonify(users)
    finally:
        cursor.close()
        db.close()

# Tambah Kasir Baru
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

# Toggle status kasir (Aktif/Non-aktif)
@admin_bp.route("/api/users/toggle/<int:user_id>", methods=["POST"])
def toggle_user(user_id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("SELECT is_active FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        if not user:
            return jsonify({"error": "User tidak ditemukan"}), 404
            
        new_status = not user['is_active']
        cursor.execute("UPDATE users SET is_active = %s WHERE id = %s", (new_status, user_id))
        db.commit()
        return jsonify({"message": "Status berhasil diperbarui", "new_status": new_status})
    finally:
        cursor.close()
        db.close()

# =========================
# MANAJEMEN PRODUK (MENU)
# =========================

# Tambah Produk Baru
@admin_bp.route("/produk", methods=["POST"])
def tambah_produk():
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        sql = "INSERT INTO produk (cat, nama, harga, gambar, badge) VALUES (%s, %s, %s, %s, %s)"
        val = (data['cat'], data['nama'], data['harga'], data['gambar'], data.get('badge', ''))
        cursor.execute(sql, val)
        db.commit()
        return jsonify({"message": "Produk berhasil ditambah"})
    finally:
        cursor.close()
        db.close()

# Edit Produk (Mendukung Modal UI Baru)
@admin_bp.route("/produk/<int:id>", methods=["PUT"])
def edit_produk(id):
    data = request.json
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # Query Update Lengkap agar Kategori dan Gambar juga bisa diubah
        sql = """
            UPDATE produk 
            SET nama=%s, harga=%s, cat=%s, gambar=%s 
            WHERE id=%s
        """
        val = (data['nama'], data['harga'], data['cat'], data['gambar'], id)
        cursor.execute(sql, val)
        db.commit()
        return jsonify({"message": "Produk berhasil diperbarui"})
    finally:
        cursor.close()
        db.close()

# Hapus Produk
@admin_bp.route("/produk/<int:id>", methods=["DELETE"])
def hapus_produk(id):
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    try:
        cursor.execute("DELETE FROM produk WHERE id=%s", (id,))
        db.commit()
        return jsonify({"message": "Produk berhasil dihapus"})
    finally:
        cursor.close()
        db.close()