-- Migration script untuk menambahkan tabel arsip seleksi
-- Jalankan script ini di database MySQL

CREATE TABLE IF NOT EXISTS `tb_arsip_seleksi` (
  `id_arsip` INT AUTO_INCREMENT PRIMARY KEY,
  `event_id` INT NOT NULL,
  `nama_arsip` VARCHAR(255) NOT NULL,
  `deskripsi` TEXT NULL,
  `file_path` VARCHAR(500) NULL COMMENT 'Path file PDF/Excel',
  `file_type` VARCHAR(50) NOT NULL DEFAULT 'pdf' COMMENT 'pdf atau excel',
  `tanggal_arsip` DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
  `dibuat_oleh` INT NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'aktif' COMMENT 'aktif, diarsipkan',
  FOREIGN KEY (`event_id`) REFERENCES `tb_kegiatan`(`id_kegiatan`) ON DELETE CASCADE,
  FOREIGN KEY (`dibuat_oleh`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_event` (`event_id`),
  INDEX `idx_tanggal` (`tanggal_arsip`),
  INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

