-- Migration script untuk menambahkan tabel AHP
-- Jalankan script ini di database MySQL

-- Tabel untuk menyimpan matriks perbandingan berpasangan
CREATE TABLE IF NOT EXISTS `tb_pairwise_comparison` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `event_id` INT NOT NULL,
  `criteria_i_id` INT NOT NULL,
  `criteria_j_id` INT NOT NULL,
  `comparison_value` FLOAT NOT NULL COMMENT 'Nilai perbandingan 1-9',
  `fuzzy_l` FLOAT NULL COMMENT 'Lower bound TFN',
  `fuzzy_m` FLOAT NULL COMMENT 'Middle bound TFN',
  `fuzzy_u` FLOAT NULL COMMENT 'Upper bound TFN',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`event_id`) REFERENCES `tb_kegiatan`(`id_kegiatan`) ON DELETE CASCADE,
  FOREIGN KEY (`criteria_i_id`) REFERENCES `tb_kriteria`(`id_kriteria`) ON DELETE CASCADE,
  FOREIGN KEY (`criteria_j_id`) REFERENCES `tb_kriteria`(`id_kriteria`) ON DELETE CASCADE,
  INDEX `idx_event` (`event_id`),
  INDEX `idx_criteria_i` (`criteria_i_id`),
  INDEX `idx_criteria_j` (`criteria_j_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Tabel untuk menyimpan hasil perhitungan AHP
CREATE TABLE IF NOT EXISTS `tb_ahp_results` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `event_id` INT NOT NULL UNIQUE,
  `lambda_max` FLOAT NULL,
  `ci` FLOAT NULL COMMENT 'Consistency Index',
  `cr` FLOAT NULL COMMENT 'Consistency Ratio',
  `is_consistent` BOOLEAN DEFAULT FALSE,
  `eigenvector_json` TEXT NULL COMMENT 'JSON array eigenvector',
  `weights_json` TEXT NULL COMMENT 'JSON object weights',
  `pairwise_matrix_json` TEXT NULL COMMENT 'JSON matrix',
  `calculated_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`event_id`) REFERENCES `tb_kegiatan`(`id_kegiatan`) ON DELETE CASCADE,
  INDEX `idx_event` (`event_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

