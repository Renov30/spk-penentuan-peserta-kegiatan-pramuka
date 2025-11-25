-- Check the jenis_kriteria for "Tes Pilihan Ganda"
SELECT id_kriteria, nama_kriteria, jenis_kriteria, event_id
FROM tb_kriteria
WHERE nama_kriteria LIKE '%Pilihan Ganda%'
OR nama_kriteria LIKE '%Tes Pilihan%';

-- If the jenis_kriteria is not 'kuantitatif', update it:
-- UPDATE tb_kriteria
-- SET jenis_kriteria = 'kuantitatif'
-- WHERE nama_kriteria LIKE '%Pilihan Ganda%';
