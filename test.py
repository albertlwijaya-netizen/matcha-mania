import mysql.connector

try:
    db = mysql.connector.connect(
        host="gateway01.ap-southeast-1.prod.alicloud.tidbcloud.com",
        user="4FeMwYQyixhQ4Ke.root",
        password="PEdAk2nrdaf8MI9e",
        database="matcha",
        port=4000,
        ssl_disabled=False
    )

    print("Koneksi berhasil!")

except Exception as e:
    print("Koneksi gagal:", e)