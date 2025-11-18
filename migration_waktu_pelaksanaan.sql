-- Migration Script: Mengubah waktu_pelaksanaan menjadi waktu_pelaksanaan_dimulai dan waktu_pelaksanaan_selesai
-- Jalankan script ini di database MySQL/MariaDB

-- 1. Tambahkan kolom baru waktu_pelaksanaan_dimulai
ALTER TABLE tb_kegiatan 
ADD COLUMN waktu_pelaksanaan_dimulai DATE NULL AFTER waktu_pelaksanaan;

-- 2. Tambahkan kolom baru waktu_pelaksanaan_selesai
ALTER TABLE tb_kegiatan 
ADD COLUMN waktu_pelaksanaan_selesai DATE NULL AFTER waktu_pelaksanaan_dimulai;

-- 3. Copy data dari waktu_pelaksanaan ke waktu_pelaksanaan_dimulai (untuk data existing)
UPDATE tb_kegiatan 
SET waktu_pelaksanaan_dimulai = waktu_pelaksanaan 
WHERE waktu_pelaksanaan_dimulai IS NULL;

-- 4. Set waktu_pelaksanaan_selesai sama dengan waktu_pelaksanaan_dimulai untuk data existing
UPDATE tb_kegiatan 
SET waktu_pelaksanaan_selesai = waktu_pelaksanaan_dimulai 
WHERE waktu_pelaksanaan_selesai IS NULL;

-- 5. Set kolom baru menjadi NOT NULL setelah data di-copy
ALTER TABLE tb_kegiatan 
MODIFY COLUMN waktu_pelaksanaan_dimulai DATE NOT NULL;

ALTER TABLE tb_kegiatan 
MODIFY COLUMN waktu_pelaksanaan_selesai DATE NOT NULL;

-- 6. Hapus kolom lama waktu_pelaksanaan (HATI-HATI: Backup dulu sebelum menjalankan!)
-- ALTER TABLE tb_kegiatan DROP COLUMN waktu_pelaksanaan;

-- Catatan: 
-- - Script di atas akan menambahkan kolom baru dan mengisi dengan data dari kolom lama
-- - Baris terakhir (DROP COLUMN) di-comment untuk keamanan, uncomment setelah memastikan semua berjalan dengan baik
-- - Pastikan untuk backup database sebelum menjalankan script ini

