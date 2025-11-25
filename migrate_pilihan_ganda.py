"""
Simple SQL migration to update 'Tes Pilihan Ganda' criteria type to 'kuantitatif'

Run this in your MySQL/MariaDB client or phpMyAdmin
"""

# SQL Query to update the criteria type
UPDATE_QUERY = """
-- Update all criteria with 'Pilihan Ganda' in the name to kuantitatif type
UPDATE tb_kriteria
SET jenis_kriteria = 'kuantitatif'
WHERE nama_kriteria LIKE '%Pilihan Ganda%';

-- Verify the update
SELECT id_kriteria, nama_kriteria, jenis_kriteria, event_id
FROM tb_kriteria
WHERE nama_kriteria LIKE '%Pilihan Ganda%';
"""

print("=" * 80)
print("SQL MIGRATION: Update Tes Pilihan Ganda to Kuantitatif")
print("=" * 80)
print()
print("Copy and run the following SQL query in your database client:")
print()
print(UPDATE_QUERY)
print()
print("=" * 80)
print("After running the query:")
print("1. Refresh your grading form page")
print("2. 'Tes Pilihan Ganda' should now show a numeric input (1-100)")
print("=" * 80)
