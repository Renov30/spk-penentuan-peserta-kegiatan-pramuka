-- Script migration untuk menambahkan kolom permissions ke tabel users
-- Jalankan script ini langsung di MySQL/MariaDB

-- Cek apakah kolom sudah ada, jika belum tambahkan
SET @col_exists = (SELECT COUNT(*) 
                   FROM INFORMATION_SCHEMA.COLUMNS 
                   WHERE TABLE_SCHEMA = DATABASE() 
                   AND TABLE_NAME = 'users' 
                   AND COLUMN_NAME = 'permissions');

SET @sql = IF(@col_exists = 0,
              'ALTER TABLE users ADD COLUMN permissions TEXT NULL',
              'SELECT "Kolom permissions sudah ada" AS message');

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;
