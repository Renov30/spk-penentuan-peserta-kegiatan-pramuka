# Implementasi Fuzzy AHP Lengkap

## Ringkasan
Implementasi algoritma Fuzzy AHP lengkap sesuai dengan teori dari PDF yang diberikan. Sistem ini sekarang menggunakan metode Fuzzy AHP standar dengan:
1. Matriks perbandingan berpasangan
2. Fuzzifikasi menggunakan Triangular Fuzzy Number (TFN)
3. Sintesis Fuzzy (Fuzzy Synthetic Extent)
4. Perbandingan probabilitas V(M2 ≥ M1)
5. Defuzzifikasi ordinat d'(Ai)

## File yang Dibuat/Dimodifikasi

### 1. `app/ahp_calculator.py` (BARU)
Modul untuk perhitungan AHP dan Fuzzy AHP lengkap:
- `AHPCalculator`: Perhitungan AHP standar (eigenvector, lambda max, konsistensi)
- `FuzzyAHPCalculator`: Perhitungan Fuzzy AHP dengan TFN, sintesis fuzzy, dan perbandingan probabilitas
- Skala TFN sesuai PDF: (1,1,1), (1/2,1,3/2), (1,3/2,2), ..., (4,9/2,5)

### 2. `app/fuzzy_ahp.py` (DIMODIFIKASI)
Fungsi utama untuk perhitungan SPK:
- `calculate_ahp_weights()`: Hitung bobot menggunakan AHP standar
- `calculate_fuzzy_ahp_weights()`: Hitung bobot menggunakan Fuzzy AHP
- `save_pairwise_matrix()`: Simpan matriks perbandingan ke database
- `get_pairwise_matrix_from_db()`: Ambil matriks dari database
- `calculate_spk()`: Fungsi utama untuk menghitung SPK (menggunakan bobot dari AHP/Fuzzy AHP)

### 3. `app/models.py` (DIMODIFIKASI)
Model database baru:
- `PairwiseComparison`: Menyimpan matriks perbandingan berpasangan
- `AHPResults`: Menyimpan hasil perhitungan AHP (lambda max, CI, CR, weights)

### 4. `run.py` (DIMODIFIKASI)
Route baru:
- `/admin/pembobotan_kriteria`: Halaman input matriks perbandingan dan perhitungan AHP
- `/api/save_pairwise_matrix/<event_id>`: API untuk menyimpan matriks
- `/api/calculate_ahp/<event_id>`: API untuk menghitung bobot AHP/Fuzzy AHP

### 5. `app/templates/pembobotan_kriteria.html` (DIMODIFIKASI)
Template lengkap untuk:
- Input matriks perbandingan berpasangan (skala 1-9)
- Menampilkan hasil perhitungan AHP (lambda max, CI, CR, konsistensi)
- Menampilkan bobot kriteria hasil perhitungan

### 6. `migration_ahp_tables.sql` (BARU)
Script SQL untuk membuat tabel baru:
- `tb_pairwise_comparison`: Tabel matriks perbandingan
- `tb_ahp_results`: Tabel hasil perhitungan AHP

## Cara Menggunakan

### 1. Migrasi Database
Jalankan script SQL untuk membuat tabel baru:
```sql
-- Jalankan migration_ahp_tables.sql di database MySQL
```

### 2. Input Matriks Perbandingan Berpasangan
1. Buka halaman `/admin/pembobotan_kriteria`
2. Pilih kegiatan yang ingin dihitung bobot kriterianya
3. Input nilai perbandingan berpasangan (skala 1-9):
   - 1 = Sama penting
   - 3 = Sedikit lebih penting
   - 5 = Lebih penting
   - 7 = Sangat lebih penting
   - 9 = Mutlak lebih penting
   - 2, 4, 6, 8 = Nilai antara
4. Klik "Simpan Matriks"

### 3. Hitung Bobot AHP/Fuzzy AHP
1. Setelah matriks tersimpan, klik "Hitung Fuzzy AHP" atau "Hitung AHP"
2. Sistem akan:
   - Menghitung eigenvector (untuk AHP)
   - Fuzzifikasi matriks ke TFN (untuk Fuzzy AHP)
   - Menghitung Fuzzy Synthetic Extent (untuk Fuzzy AHP)
   - Menghitung perbandingan probabilitas (untuk Fuzzy AHP)
   - Uji konsistensi (CI dan CR)
   - Simpan bobot ke tabel Criteria

### 4. Hitung SPK
Setelah bobot dihitung, sistem akan otomatis menggunakan bobot tersebut saat menghitung SPK menggunakan fungsi `calculate_spk()`.

## Algoritma yang Diimplementasikan

### 1. AHP Standar
- Matriks perbandingan berpasangan
- Perhitungan eigenvector menggunakan geometric mean
- Perhitungan lambda maksimum
- Uji konsistensi (CI dan CR)
- CR ≤ 0.1 untuk konsisten

### 2. Fuzzy AHP
- Fuzzifikasi matriks perbandingan ke TFN
- Perhitungan Fuzzy Synthetic Extent (Si)
- Perbandingan probabilitas V(M2 ≥ M1)
- Defuzzifikasi ordinat d'(Ai)
- Normalisasi vektor bobot

### 3. Perhitungan SPK
- Fuzzifikasi nilai penilaian peserta
- Agregasi dengan bobot dari AHP/Fuzzy AHP
- Defuzzifikasi menggunakan Center of Area
- Ranking peserta

## Perbedaan dengan Implementasi Sebelumnya

| Aspek | Sebelumnya | Sekarang |
|-------|-----------|----------|
| Matriks Perbandingan | ❌ Tidak ada | ✅ Ada |
| Perhitungan Eigenvector | ❌ Tidak ada | ✅ Ada |
| Uji Konsistensi | ❌ Tidak ada | ✅ Ada |
| Fuzzifikasi Matriks | ❌ Tidak ada | ✅ Ada |
| Sintesis Fuzzy | ❌ Tidak ada | ✅ Ada |
| Perbandingan Probabilitas | ❌ Tidak ada | ✅ Ada |
| Defuzzifikasi Ordinat | ❌ Tidak ada | ✅ Ada |

## Catatan Penting

1. **Skala Perbandingan**: Gunakan skala 1-9 sesuai teori AHP. Nilai kebalikan (1/2, 1/3, dst.) akan otomatis dihitung.

2. **Konsistensi**: Pastikan CR ≤ 0.1. Jika tidak konsisten, periksa kembali matriks perbandingan.

3. **Bobot Otomatis**: Setelah perhitungan AHP/Fuzzy AHP, bobot akan otomatis tersimpan di tabel `tb_kriteria` dan digunakan untuk perhitungan SPK.

4. **Backward Compatibility**: Sistem tetap mendukung bobot manual (jika tidak ada matriks perbandingan), tetapi disarankan menggunakan AHP/Fuzzy AHP untuk hasil yang lebih akurat.

## Testing

Untuk menguji implementasi:
1. Buat kegiatan baru dengan beberapa kriteria
2. Input matriks perbandingan berpasangan
3. Hitung bobot menggunakan Fuzzy AHP
4. Verifikasi CR ≤ 0.1
5. Hitung SPK dan lihat hasil ranking

## Referensi

Implementasi mengikuti teori dari PDF "Langkah-langkah Perhitungan Metode Fuzzy Analytical Hierarchy Process (Fuzzy AHP)" yang diberikan.

