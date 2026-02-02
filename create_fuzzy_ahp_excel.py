"""
Script untuk membuat Model Tabel Excel Perhitungan Fuzzy AHP
Data: David Kulian - Raimuna Daerah (25 January 2026)
"""

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
import math

# Create workbook
wb = openpyxl.Workbook()

# Styles
header_font = Font(bold=True, size=12, color="FFFFFF")
title_font = Font(bold=True, size=14)
subtitle_font = Font(bold=True, size=11)
normal_font = Font(size=10)
center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
left_align = Alignment(horizontal='left', vertical='center')
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
green_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
yellow_fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
light_blue_fill = PatternFill(start_color="D6DCE4", end_color="D6DCE4", fill_type="solid")
light_green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")

# Kriteria (dari screenshot)
kriteria = [
    "Status Keaktifan di Gugus Depan",
    "Pencapaian SKU",
    "Pencapaian SPG",
    "Kesehatan Jasmani dan Rohani",
    "Tes Wawancara",
    "Tes Pilihan Ganda"
]
n = len(kriteria)

# Matriks perbandingan berpasangan (Crisp) - dari screenshot semua nilai 1
crisp_matrix = [
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1]
]

# Tabel konversi TFN (Triangular Fuzzy Number)
tfn_scale = {
    1: (1, 1, 1),
    2: (1/2, 1, 3/2),
    3: (1, 3/2, 2),
    4: (3/2, 2, 5/2),
    5: (2, 5/2, 3),
    6: (5/2, 3, 7/2),
    7: (3, 7/2, 4),
    8: (7/2, 4, 9/2),
    9: (4, 9/2, 9/2)
}

tfn_reciprocal = {
    1: (1, 1, 1),
    2: (2/3, 1, 2),
    3: (1/2, 2/3, 1),
    4: (0.40, 1/2, 2/3),
    5: (1/3, 0.40, 1/2),
    6: (0.29, 1/3, 0.40),
    7: (1/4, 0.29, 1/3),
    8: (0.22, 1/4, 0.29),
    9: (0.22, 0.22, 1/4)
}

# Random Index values
ri_table = {
    1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
    7: 1.32, 8: 1.41, 9: 1.46, 10: 1.49, 11: 1.51, 12: 1.58
}

def apply_header_style(cell, fill=header_fill):
    cell.font = header_font
    cell.alignment = center_align
    cell.border = thin_border
    cell.fill = fill

def apply_cell_style(cell, is_header=False):
    cell.font = normal_font
    cell.alignment = center_align
    cell.border = thin_border

# ============================================
# SHEET 1: Data Peserta & Skala Perbandingan
# ============================================
ws1 = wb.active
ws1.title = "1. Data & Skala"

# Header info
ws1['A1'] = "MODEL PERHITUNGAN FUZZY AHP"
ws1['A1'].font = Font(bold=True, size=16)
ws1.merge_cells('A1:G1')

ws1['A3'] = "Nama Peserta:"
ws1['B3'] = "David Kulian"
ws1['A4'] = "Kegiatan:"
ws1['B4'] = "Raimuna Daerah"
ws1['A5'] = "Tanggal:"
ws1['B5'] = "25 January 2026"
ws1['A6'] = "Peringkat:"
ws1['B6'] = "#1"
ws1['B6'].font = Font(bold=True, size=14, color="FF6B00")

# Tabel Skala Saaty
ws1['A9'] = "Tabel Skala Perbandingan Tingkat Kepentingan (Saaty)"
ws1['A9'].font = subtitle_font
ws1.merge_cells('A9:D9')

ws1['A10'] = "Intensitas"
ws1['B10'] = "Definisi"
apply_header_style(ws1['A10'])
apply_header_style(ws1['B10'])
ws1.merge_cells('B10:D10')

saaty_scale = [
    (1, "Kedua elemen sama penting (Equal Importance)"),
    (3, "Elemen satu sedikit lebih penting (Slightly More Importance)"),
    (5, "Elemen satu lebih penting (Materially More Importance)"),
    (7, "Satu elemen jelas lebih penting (Significantly More Importance)"),
    (9, "Satu elemen mutlak lebih penting (Absolutely More Importance)"),
    ("2,4,6,8", "Nilai-nilai diantara dua pertimbangan yang berdekatan")
]

for i, (intensitas, definisi) in enumerate(saaty_scale, start=11):
    ws1[f'A{i}'] = intensitas
    ws1[f'B{i}'] = definisi
    apply_cell_style(ws1[f'A{i}'])
    apply_cell_style(ws1[f'B{i}'])
    ws1.merge_cells(f'B{i}:D{i}')

# Tabel Skala Fuzzy (TFN)
ws1['A19'] = "Tabel Skala Nilai Fuzzy (TFN)"
ws1['A19'].font = subtitle_font
ws1.merge_cells('A19:E19')

ws1['A20'] = "Intensitas"
ws1['B20'] = "TFN (l, m, u)"
ws1['C20'] = "Kebalikan"
apply_header_style(ws1['A20'])
apply_header_style(ws1['B20'])
apply_header_style(ws1['C20'])
ws1.merge_cells('B20:C20')
ws1.merge_cells('C20:E20')

# Insert TFN values
row = 21
for i in range(1, 10):
    l, m, u = tfn_scale[i]
    rl, rm, ru = tfn_reciprocal[i]
    ws1[f'A{row}'] = i
    ws1[f'B{row}'] = f"({l:.2f}, {m:.2f}, {u:.2f})" if l != 1 else f"({int(l)}, {int(m)}, {int(u)})"
    ws1[f'D{row}'] = f"({rl:.2f}, {rm:.2f}, {ru:.2f})" if rl != 1 else f"({int(rl)}, {int(rm)}, {int(ru)})"
    apply_cell_style(ws1[f'A{row}'])
    apply_cell_style(ws1[f'B{row}'])
    apply_cell_style(ws1[f'D{row}'])
    ws1.merge_cells(f'B{row}:C{row}')
    ws1.merge_cells(f'D{row}:E{row}')
    row += 1

# Set column widths
ws1.column_dimensions['A'].width = 15
ws1.column_dimensions['B'].width = 25
ws1.column_dimensions['C'].width = 20
ws1.column_dimensions['D'].width = 20
ws1.column_dimensions['E'].width = 15

# ============================================
# SHEET 2: Matriks Perbandingan Berpasangan (Crisp)
# ============================================
ws2 = wb.create_sheet("2. Matriks Crisp")

ws2['A1'] = "LANGKAH 1: Matriks Perbandingan Berpasangan (Crisp)"
ws2['A1'].font = title_font
ws2.merge_cells('A1:H1')

ws2['A3'] = "Matriks ini bersifat resiprokal dengan aij = 1 dan aji = 1/aij"
ws2.merge_cells('A3:H3')

# Header row
ws2['A5'] = "Kriteria"
apply_header_style(ws2['A5'])
for j, krit in enumerate(kriteria, start=2):
    col = get_column_letter(j)
    ws2[f'{col}5'] = krit[:15] + "..." if len(krit) > 15 else krit
    apply_header_style(ws2[f'{col}5'])

# Data rows
for i, krit in enumerate(kriteria):
    row = i + 6
    ws2[f'A{row}'] = krit[:20] + "..." if len(krit) > 20 else krit
    ws2[f'A{row}'].font = Font(bold=True, size=10)
    ws2[f'A{row}'].border = thin_border
    ws2[f'A{row}'].fill = light_blue_fill
    
    for j in range(n):
        col = get_column_letter(j + 2)
        ws2[f'{col}{row}'] = crisp_matrix[i][j]
        apply_cell_style(ws2[f'{col}{row}'])

# Set column widths
ws2.column_dimensions['A'].width = 25
for j in range(2, 8):
    ws2.column_dimensions[get_column_letter(j)].width = 12

# ============================================
# SHEET 3: Perhitungan Vector Eigen
# ============================================
ws3 = wb.create_sheet("3. Vector Eigen")

ws3['A1'] = "LANGKAH 2: Perhitungan Vector Eigen (Geometric Mean Method)"
ws3['A1'].font = title_font
ws3.merge_cells('A1:J1')

ws3['A3'] = "Rumus: GMi = (∏ aij)^(1/n)"
ws3['A4'] = "wi = GMi / Σ GMi"

# Calculate Geometric Mean
gm_values = []
for i in range(n):
    product = 1
    for j in range(n):
        product *= crisp_matrix[i][j]
    gm = product ** (1/n)
    gm_values.append(gm)

sum_gm = sum(gm_values)
eigenvector = [gm / sum_gm for gm in gm_values]

# Header
ws3['A7'] = "Kriteria"
ws3['B7'] = "Geometric Mean (GMi)"
ws3['C7'] = "Eigenvector (wi)"
apply_header_style(ws3['A7'])
apply_header_style(ws3['B7'])
apply_header_style(ws3['C7'])

# Data
for i, krit in enumerate(kriteria):
    row = i + 8
    ws3[f'A{row}'] = krit[:25] + "..." if len(krit) > 25 else krit
    ws3[f'B{row}'] = round(gm_values[i], 4)
    ws3[f'C{row}'] = round(eigenvector[i], 4)
    apply_cell_style(ws3[f'A{row}'])
    apply_cell_style(ws3[f'B{row}'])
    apply_cell_style(ws3[f'C{row}'])

# Sum row
ws3[f'A{n+8}'] = "TOTAL"
ws3[f'B{n+8}'] = round(sum_gm, 4)
ws3[f'C{n+8}'] = round(sum(eigenvector), 4)
ws3[f'A{n+8}'].font = Font(bold=True)
ws3[f'B{n+8}'].font = Font(bold=True)
ws3[f'C{n+8}'].font = Font(bold=True)
apply_cell_style(ws3[f'A{n+8}'])
apply_cell_style(ws3[f'B{n+8}'])
apply_cell_style(ws3[f'C{n+8}'])

# Lambda Max calculation
# λmax = (1/n) × Σ (Amxw)i
lambda_max = 6.00  # From screenshot

ws3['E7'] = "Lambda Max (λmax)"
ws3['E7'].font = subtitle_font
ws3['E8'] = lambda_max
ws3['E8'].font = Font(bold=True, size=16, color="FF6B00")
ws3['E9'] = "λmax = (1/n) × Σ (Aw)i"

# Set column widths
ws3.column_dimensions['A'].width = 30
ws3.column_dimensions['B'].width = 22
ws3.column_dimensions['C'].width = 18
ws3.column_dimensions['E'].width = 20

# ============================================
# SHEET 4: Uji Konsistensi
# ============================================
ws4 = wb.create_sheet("4. Uji Konsistensi")

ws4['A1'] = "LANGKAH 3: Uji Konsistensi Matriks Perbandingan"
ws4['A1'].font = title_font
ws4.merge_cells('A1:G1')

ws4['A3'] = "Uji konsistensi dilakukan untuk memastikan penilaian bersifat rasional dan tidak saling bertentangan."
ws4.merge_cells('A3:G3')
ws4['A4'] = "Matriks dinyatakan konsisten jika CR ≤ 0.1"
ws4.merge_cells('A4:G4')

# CI calculation
ci = (lambda_max - n) / (n - 1)
ri = ri_table[n]
cr = ci / ri if ri != 0 else 0

# CI Box
ws4['A7'] = "Consistency Index (CI)"
ws4['A7'].font = subtitle_font
ws4['A8'] = round(ci, 4)
ws4['A8'].font = Font(bold=True, size=16, color="008000")
ws4['A9'] = "CI = (λmax - n) / (n - 1)"

# RI Box
ws4['C7'] = "Random Index (RI)"
ws4['C7'].font = subtitle_font
ws4['C8'] = ri
ws4['C8'].font = Font(bold=True, size=16)
ws4['C9'] = f"n = {n}"

# CR Box
ws4['E7'] = "Consistency Ratio (CR)"
ws4['E7'].font = subtitle_font
ws4['E8'] = round(cr, 4)
ws4['E8'].font = Font(bold=True, size=16, color="008000")
if cr <= 0.1:
    ws4['E9'] = "✓ Konsisten (CR ≤ 0.1)"
    ws4['E9'].font = Font(color="008000")
else:
    ws4['E9'] = "✗ Tidak Konsisten (CR > 0.1)"
    ws4['E9'].font = Font(color="FF0000")

# Tabel Random Index
ws4['A12'] = "Tabel Random Index (RI)"
ws4['A12'].font = subtitle_font

ws4['A13'] = "n"
for i in range(1, 13):
    col = get_column_letter(i + 1)
    ws4[f'{col}13'] = i
    apply_header_style(ws4[f'{col}13'])
apply_header_style(ws4['A13'])

ws4['A14'] = "RI"
for i in range(1, 13):
    col = get_column_letter(i + 1)
    ws4[f'{col}14'] = ri_table[i]
    apply_cell_style(ws4[f'{col}14'])
apply_cell_style(ws4['A14'])

ws4.column_dimensions['A'].width = 22
ws4.column_dimensions['C'].width = 18
ws4.column_dimensions['E'].width = 22

# ============================================
# SHEET 5: Matriks Fuzzy (TFN)
# ============================================
ws5 = wb.create_sheet("5. Matriks Fuzzy TFN")

ws5['A1'] = "LANGKAH 4: Fuzzifikasi Matriks Perbandingan Berpasangan"
ws5['A1'].font = title_font
ws5.merge_cells('A1:T1')

ws5['A3'] = "Setelah matriks dinyatakan konsisten, nilai crisp dikonversi ke Triangular Fuzzy Number (TFN) = (l, m, u)"
ws5.merge_cells('A3:T3')

# Header row - 3 columns per criterion (l, m, u)
ws5['A5'] = "Kriteria"
apply_header_style(ws5['A5'])

col_idx = 2
for krit in kriteria:
    short_name = krit[:10] + "..." if len(krit) > 10 else krit
    ws5.merge_cells(start_row=5, start_column=col_idx, end_row=5, end_column=col_idx+2)
    cell = ws5.cell(row=5, column=col_idx)
    cell.value = short_name
    apply_header_style(cell)
    
    # Sub-headers for l, m, u
    ws5.cell(row=6, column=col_idx).value = "l"
    ws5.cell(row=6, column=col_idx+1).value = "m"
    ws5.cell(row=6, column=col_idx+2).value = "u"
    for c in range(col_idx, col_idx+3):
        apply_header_style(ws5.cell(row=6, column=c), fill=yellow_fill)
    
    col_idx += 3

ws5.merge_cells('A5:A6')

# Data rows
for i, krit in enumerate(kriteria):
    row = i + 7
    ws5[f'A{row}'] = krit[:15] + "..." if len(krit) > 15 else krit
    ws5[f'A{row}'].font = Font(bold=True, size=10)
    ws5[f'A{row}'].border = thin_border
    ws5[f'A{row}'].fill = light_blue_fill
    
    col_idx = 2
    for j in range(n):
        crisp_val = crisp_matrix[i][j]
        l, m, u = tfn_scale.get(crisp_val, (1, 1, 1))
        
        ws5.cell(row=row, column=col_idx).value = round(l, 2)
        ws5.cell(row=row, column=col_idx+1).value = round(m, 2)
        ws5.cell(row=row, column=col_idx+2).value = round(u, 2)
        
        for c in range(col_idx, col_idx+3):
            apply_cell_style(ws5.cell(row=row, column=c))
        
        col_idx += 3

# Set column widths
ws5.column_dimensions['A'].width = 18
for j in range(2, 21):
    ws5.column_dimensions[get_column_letter(j)].width = 6

# ============================================
# SHEET 6: Ringkasan Hasil
# ============================================
ws6 = wb.create_sheet("6. Ringkasan Hasil")

ws6['A1'] = "RINGKASAN PERHITUNGAN FUZZY AHP"
ws6['A1'].font = title_font
ws6.merge_cells('A1:E1')

ws6['A3'] = "Nama Peserta:"
ws6['B3'] = "David Kulian"
ws6['B3'].font = Font(bold=True)
ws6['A4'] = "Kegiatan:"
ws6['B4'] = "Raimuna Daerah"
ws6['A5'] = "Tanggal Penilaian:"
ws6['B5'] = "25 January 2026"

# Bobot Kriteria
ws6['A8'] = "BOBOT KRITERIA HASIL FUZZY AHP"
ws6['A8'].font = subtitle_font
ws6.merge_cells('A8:C8')

ws6['A9'] = "No"
ws6['B9'] = "Kriteria"
ws6['C9'] = "Bobot (wi)"
apply_header_style(ws6['A9'])
apply_header_style(ws6['B9'])
apply_header_style(ws6['C9'])

for i, krit in enumerate(kriteria):
    row = i + 10
    ws6[f'A{row}'] = i + 1
    ws6[f'B{row}'] = krit
    ws6[f'C{row}'] = round(eigenvector[i], 4)
    apply_cell_style(ws6[f'A{row}'])
    apply_cell_style(ws6[f'B{row}'])
    apply_cell_style(ws6[f'C{row}'])

# Status Konsistensi
row = n + 12
ws6[f'A{row}'] = "STATUS KONSISTENSI"
ws6[f'A{row}'].font = subtitle_font
ws6.merge_cells(f'A{row}:C{row}')

ws6[f'A{row+1}'] = "Consistency Index (CI)"
ws6[f'B{row+1}'] = round(ci, 4)
ws6[f'A{row+2}'] = "Random Index (RI)"
ws6[f'B{row+2}'] = ri
ws6[f'A{row+3}'] = "Consistency Ratio (CR)"
ws6[f'B{row+3}'] = round(cr, 4)
ws6[f'A{row+4}'] = "Status"
if cr <= 0.1:
    ws6[f'B{row+4}'] = "KONSISTEN ✓"
    ws6[f'B{row+4}'].font = Font(bold=True, color="008000")
else:
    ws6[f'B{row+4}'] = "TIDAK KONSISTEN ✗"
    ws6[f'B{row+4}'].font = Font(bold=True, color="FF0000")

# Ranking
row = n + 18
ws6[f'A{row}'] = "PERINGKAT AKHIR"
ws6[f'A{row}'].font = subtitle_font
ws6.merge_cells(f'A{row}:C{row}')

ws6[f'A{row+1}'] = "Peringkat"
ws6[f'B{row+1}'] = "#1"
ws6[f'B{row+1}'].font = Font(bold=True, size=20, color="FF6B00")

ws6.column_dimensions['A'].width = 25
ws6.column_dimensions['B'].width = 35
ws6.column_dimensions['C'].width = 15

# Save workbook
output_file = "d:/laragon/www/appSaringPramuka/Fuzzy_AHP_David_Kulian.xlsx"
wb.save(output_file)
print(f"File Excel berhasil dibuat: {output_file}")
print("\nFile berisi 6 sheet:")
print("1. Data & Skala - Informasi peserta dan tabel skala")
print("2. Matriks Crisp - Matriks perbandingan berpasangan")
print("3. Vector Eigen - Perhitungan Geometric Mean & Eigenvector")
print("4. Uji Konsistensi - CI, RI, dan CR")
print("5. Matriks Fuzzy TFN - Fuzzifikasi matriks")
print("6. Ringkasan Hasil - Resume perhitungan")
