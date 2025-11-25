-- Check if there are scores for criteria 144 (Tes Pilihan Ganda)
SELECT p.id_penilaian, p.id_users, p.evaluator_id, p.id_kriteria, p.nilai,
       u.nama_lengkap as participant_name,
       e.nama_lengkap as evaluator_name,
       k.nama_kriteria
FROM tb_penilaian p
LEFT JOIN users u ON p.id_users = u.id
LEFT JOIN users e ON p.evaluator_id = e.id
LEFT JOIN tb_kriteria k ON p.id_kriteria = k.id_kriteria
WHERE p.id_kriteria = 144
ORDER BY p.id_penilaian DESC;

-- If you see scores with id_users=2 (admin) that should belong to a participant,
-- you can fix them with this UPDATE statement:
-- UPDATE tb_penilaian 
-- SET id_users = 38  -- Replace with the correct participant's user ID
-- WHERE id_kriteria = 144 
-- AND id_users = 2;
