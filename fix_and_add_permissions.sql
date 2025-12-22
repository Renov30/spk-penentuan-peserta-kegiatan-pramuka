-- Script untuk memperbaiki ENUM status dan menambahkan kolom permissions
-- Jalankan script ini di MySQL/MariaDB

-- Langkah 1: Perbaiki ENUM status terlebih dahulu (hapus duplikasi empty string)
-- Hati-hati: Backup database terlebih dahulu!

-- Cek struktur ENUM saat ini
SHOW COLUMNS FROM users WHERE Field = 'status';

-- Jika ada masalah dengan ENUM, perbaiki dengan mengubah ENUM definition
-- Pastikan tidak ada duplikasi value '' (empty string)
-- Ubah ENUM menjadi: ENUM('aktif', 'non-aktif') jika perlu

-- Langkah 2: Tambahkan kolom permissions
-- Jika kolom belum ada, tambahkan:
ALTER TABLE users ADD COLUMN permissions TEXT NULL;

-- Verifikasi kolom sudah ditambahkan
SHOW COLUMNS FROM users WHERE Field = 'permissions';
