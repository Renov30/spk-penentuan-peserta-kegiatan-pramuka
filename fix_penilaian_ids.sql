-- This script fixes the id_users in tb_penilaian table
-- The issue: id_users was set to admin ID (2) instead of the actual participant's user ID

-- First, let's see what we have
SELECT p.id_penilaian, p.id_users, p.evaluator_id, p.id_kriteria, p.nilai,
       u.nama_lengkap as current_user_name,
       e.nama_lengkap as evaluator_name
FROM tb_penilaian p
LEFT JOIN users u ON p.id_users = u.id
LEFT JOIN users e ON p.evaluator_id = e.id
WHERE p.id_users = 2  -- Admin ID
ORDER BY p.id_penilaian;

-- To fix this, we need to know which participant each score belongs to
-- Based on the screenshot, the scores are for criteria 139-144 (Event 36)
-- And they should belong to a participant, not the admin

-- IMPORTANT: Before running the UPDATE, you need to identify the correct participant ID
-- You can do this by checking which participant was being graded when these scores were saved

-- Example fix (REPLACE 38 with the actual participant's user ID):
-- UPDATE tb_penilaian 
-- SET id_users = 38  -- Replace with correct participant user ID
-- WHERE id_users = 2 
-- AND evaluator_id = 40  -- The evaluator who created these scores
-- AND id_kriteria IN (139, 140, 141, 142, 143, 144);  -- The criteria for this event
