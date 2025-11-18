-- Migration Script: Menambahkan kolom kegiatan_id ke tabel participants
-- Jalankan script ini di database MySQL/MariaDB

-- 1. Tambahkan kolom kegiatan_id (nullable, dengan foreign key)
ALTER TABLE participants 
ADD COLUMN kegiatan_id INT NULL AFTER foto;

-- 2. Tambahkan foreign key constraint ke tabel tb_kegiatan
ALTER TABLE participants 
ADD CONSTRAINT fk_participants_kegiatan 
FOREIGN KEY (kegiatan_id) REFERENCES tb_kegiatan(id_kegiatan) 
ON DELETE SET NULL ON UPDATE CASCADE;

-- Catatan: 
-- - Kolom kegiatan_id dibuat nullable karena peserta yang sudah ada mungkin belum terdaftar di kegiatan
-- - Foreign key constraint memastikan integritas data
-- - ON DELETE SET NULL: jika kegiatan dihapus, kegiatan_id peserta akan di-set NULL
-- - ON UPDATE CASCADE: jika id_kegiatan berubah, akan otomatis update di participants
-- - Pastikan untuk backup database sebelum menjalankan script ini

