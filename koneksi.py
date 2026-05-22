import mysql.connector
from mysql.connector import pooling

# Konfigurasi sesuai data TiDB Anda
db_config = {
    "host": "gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
    "user": "4FeMwYQyixhQ4Ke.root",
    "password": "PEdAk2nrdaf8MI9e",
    "database": "matcha",
    "port": 4000,
}

# Membuat kolam koneksi (Pool)
try:
    db_pool = mysql.connector.pooling.MySQLConnectionPool(
        pool_name="matcha_pool",
        pool_size=5, # Menyediakan 5 koneksi stand-by
        pool_reset_session=True,
        **db_config
    )
    print("Koneksi Pool Berhasil Dibuat!")
except mysql.connector.Error as err:
    print(f"Error saat membuat pool: {err}")

# Fungsi bantuan untuk mengambil koneksi dari pool
def get_db_connection():
    return db_pool.get_connection()