"""
Script migration untuk menambahkan kolom permissions ke tabel users
Jalankan script ini untuk menambahkan kolom permissions ke database

CATATAN PENTING:
Jika script ini gagal karena error ENUM (1291), itu karena ada masalah dengan 
ENUM definition di kolom status yang memiliki duplikasi empty string.
Silakan jalankan perintah SQL berikut secara manual di MySQL/MariaDB:

ALTER TABLE users ADD COLUMN permissions TEXT NULL;

Atau gunakan phpMyAdmin / MySQL Workbench untuk menambahkan kolom secara manual.
"""
from app import create_app, db
from sqlalchemy import text
import sys

app = create_app()

with app.app_context():
    try:
        # Cek apakah kolom permissions sudah ada
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = DATABASE() 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'permissions'
            """))
            
            exists = result.fetchone()[0] > 0
            
            if exists:
                print("SUKSES: Kolom 'permissions' sudah ada di tabel users.")
                print("Migration tidak diperlukan. Aplikasi siap digunakan!")
                sys.exit(0)
        
        print("Kolom 'permissions' belum ada. Mencoba menambahkan...")
        print("(Jika terjadi error ENUM, silakan jalankan SQL secara manual)")
        
        # Coba menggunakan raw connection dengan error handling yang lebih baik
        raw_conn = db.engine.raw_connection()
        cursor = raw_conn.cursor()
        
        try:
            # Nonaktifkan strict mode sementara untuk menghindari error ENUM
            cursor.execute("SET SESSION sql_mode = 'NO_ENGINE_SUBSTITUTION'")
            
            # Coba tambahkan kolom
            cursor.execute("ALTER TABLE users ADD COLUMN permissions TEXT NULL")
            raw_conn.commit()
            print("SUKSES: Kolom 'permissions' berhasil ditambahkan!")
            
        except Exception as alter_error:
            error_code = getattr(alter_error, 'args', [None])[0] if hasattr(alter_error, 'args') else None
            
            # Error 1291 adalah masalah ENUM, tapi kita coba verifikasi dulu
            if error_code == 1291 or "1291" in str(alter_error):
                print("\nWARNING: Terjadi error ENUM (1291).")
                print("Ini biasanya karena duplikasi empty string di ENUM status.")
                print("Memverifikasi apakah kolom sudah ditambahkan...")
                
                # Verifikasi
                cursor.execute("""
                    SELECT COUNT(*) as count 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'users' 
                    AND COLUMN_NAME = 'permissions'
                """)
                check_result = cursor.fetchone()
                
                if check_result and check_result[0] > 0:
                    print("SUKSES: Kolom 'permissions' sudah ada di database!")
                    print("(Meskipun ada warning ENUM, kolom berhasil ditambahkan)")
                else:
                    print("\nERROR: Kolom tidak berhasil ditambahkan karena masalah ENUM.")
                    print("\nSOLUSI: Jalankan perintah berikut secara manual di MySQL:")
                    print("=" * 60)
                    print("ALTER TABLE users ADD COLUMN permissions TEXT NULL;")
                    print("=" * 60)
                    sys.exit(1)
            else:
                raise alter_error
        
        finally:
            cursor.close()
            raw_conn.close()
            
    except Exception as e:
        print(f"\nERROR: {e}")
        print("\nSOLUSI: Jalankan perintah SQL berikut secara manual di MySQL:")
        print("=" * 60)
        print("ALTER TABLE users ADD COLUMN permissions TEXT NULL;")
        print("=" * 60)
        print("\nAtau gunakan phpMyAdmin / MySQL Workbench untuk menambahkan kolom secara manual.")
        sys.exit(1)
