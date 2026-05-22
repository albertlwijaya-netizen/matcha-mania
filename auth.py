from flask import Blueprint, request, session, render_template, redirect, url_for
from koneksi import get_db_connection

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        print(f"Mencoba Login: {username}") 

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        try:
            # Cari user yang cocok
            sql = "SELECT * FROM users WHERE username=%s AND password=%s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            
            if user:
                # CEK STATUS AKTIF (Pastikan kolom is_active sudah ada di database)
                if not user.get('is_active', True): 
                    print(f"Login Ditolak: Akun {username} ditangguhkan.")
                    return render_template("login.html", error="Akun Anda ditangguhkan oleh Admin!")

                print(f"Login Berhasil! Role: {user['role']}")
                session['logged_in'] = True
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('home')) 
            else:
                print("Login Gagal: Username atau Password salah")
                return render_template("login.html", error="Username atau Password salah!")
        
        except Exception as e:
            print(f"Error Database: {e}")
            return render_template("login.html", error="Terjadi kesalahan koneksi database")
            
        finally:
            cursor.close()
            db.close()
            
    return render_template("login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    print("User telah logout.")
    return redirect(url_for('auth.login'))