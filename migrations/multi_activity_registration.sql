-- Migration script to enable multiple activity registration
-- This creates the junction table for many-to-many relationship between participants and events

CREATE TABLE IF NOT EXISTS tb_participant_kegiatan (
    id INT AUTO_INCREMENT PRIMARY KEY,
    participant_id INT NOT NULL,
    kegiatan_id INT NOT NULL,
    tanggal_daftar TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    FOREIGN KEY (kegiatan_id) REFERENCES tb_kegiatan(id_kegiatan) ON DELETE CASCADE,
    UNIQUE KEY unique_participant_kegiatan (participant_id, kegiatan_id)
);

-- Migrate existing data from participants.kegiatan_id to the junction table
INSERT INTO tb_participant_kegiatan (participant_id, kegiatan_id)
SELECT id, kegiatan_id
FROM participants
WHERE kegiatan_id IS NOT NULL;

-- Note: The participants.kegiatan_id column is kept for backward compatibility
-- but will no longer be used by the application
