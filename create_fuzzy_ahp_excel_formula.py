"""
Script untuk membuat Model Tabel Excel Perhitungan Fuzzy AHP dengan RUMUS EXCEL
Data dapat diubah langsung di Excel dan hasil akan otomatis terhitung
Digunakan untuk validasi hasil perhitungan sistem
"""

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill, Protection
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import FormulaRule, DataBarRule
from openpyxl.comments import Comment

# Create workbook
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Fuzzy AHP Calculator"

# Styles
header_font = Font(bold=True, size=11, color="FFFFFF")
title_font = Font(bold=True, size=14, color="1F4E79")
subtitle_font = Font(bold=True, size=11, color="1F4E79")
section_font = Font(bold=True, size=12, color="FFFFFF")
normal_font = Font(size=10)
input_font = Font(size=11, color="0000FF")
formula_font = Font(size=10, italic=True, color="808080")
center_align = Alignment(horizontal='center', vertical='center', wrap_text=True)
left_align = Alignment(horizontal='left', vertical='center')
thin_border = Border(
    left=Side(style='thin'),
    right=Side(style='thin'),
    top=Side(style='thin'),
    bottom=Side(style='thin')
)
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
section_fill = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
green_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
yellow_fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
orange_fill = PatternFill(start_color="ED7D31", end_color="ED7D31", fill_type="solid")
light_blue_fill = PatternFill(start_color="D6DCE4", end_color="D6DCE4", fill_type="solid")
light_green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
light_yellow_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")
input_fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")  # Light yellow for input

# Kriteria
kriteria = [
    "Status Keaktifan",
    "Pencapaian SKU", 
    "Pencapaian SPG",
    "Kesehatan Jasmani",
    "Tes Wawancara",
    "Tes Pilihan Ganda"
]
n = len(kriteria)

# Random Index values
ri_values = [0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.46, 1.49, 1.51, 1.58]

def apply_header_style(cell, fill=header_fill):
    cell.font = header_font
    cell.alignment = center_align
    cell.border = thin_border
    cell.fill = fill

def apply_cell_style(cell):
    cell.font = normal_font
    cell.alignment = center_align
    cell.border = thin_border

def apply_input_style(cell):
    cell.font = input_font
    cell.alignment = center_align
    cell.border = thin_border
    cell.fill = input_fill

def apply_section_header(ws, row, text, col_start=1, col_end=10):
    cell = ws.cell(row=row, column=col_start)
    cell.value = text
    cell.font = section_font
    cell.fill = section_fill
    cell.alignment = center_align
    ws.merge_cells(start_row=row, start_column=col_start, end_row=row, end_column=col_end)
    for c in range(col_start, col_end + 1):
        ws.cell(row=row, column=c).border = thin_border

current_row = 1

# ============================================
# HEADER
# ============================================
ws['A1'] = "MODEL PERHITUNGAN FUZZY AHP - DENGAN RUMUS EXCEL"
ws['A1'].font = Font(bold=True, size=16, color="1F4E79")
ws.merge_cells('A1:J1')

ws['A2'] = "Sel berwarna KUNING adalah INPUT yang dapat diubah. Hasil akan otomatis terhitung."
ws['A2'].font = Font(italic=True, size=10, color="FF0000")
ws.merge_cells('A2:J2')

ws['A4'] = "Nama Peserta:"
ws['B4'] = "David Kulian"
ws['B4'].font = Font(bold=True)
ws['B4'].fill = input_fill
ws['D4'] = "Jumlah Kriteria (n):"
ws['E4'] = n
ws['E4'].font = Font(bold=True, size=12)

current_row = 6

# ============================================
# TABEL SKALA TFN (Referensi)
# ============================================
apply_section_header(ws, current_row, "TABEL REFERENSI SKALA FUZZY (TFN)", 1, 10)
current_row += 1

# Header
headers = ["Intensitas", "l", "m", "u", "", "Intensitas", "1/l", "1/m", "1/u"]
for i, h in enumerate(headers, 1):
    cell = ws.cell(row=current_row, column=i)
    cell.value = h
    apply_header_style(cell)
current_row += 1

# TFN Scale data - stored in cells for formula reference
tfn_data = [
    (1, 1, 1, 1),
    (2, 0.5, 1, 1.5),
    (3, 1, 1.5, 2),
    (4, 1.5, 2, 2.5),
    (5, 2, 2.5, 3),
    (6, 2.5, 3, 3.5),
    (7, 3, 3.5, 4),
    (8, 3.5, 4, 4.5),
    (9, 4, 4.5, 4.5)
]

tfn_start_row = current_row
for i, (intensity, l, m, u) in enumerate(tfn_data):
    ws.cell(row=current_row, column=1).value = intensity
    ws.cell(row=current_row, column=2).value = l
    ws.cell(row=current_row, column=3).value = m
    ws.cell(row=current_row, column=4).value = u
    
    # Reciprocal (kebalikan) - menggunakan formula
    ws.cell(row=current_row, column=6).value = intensity
    ws.cell(row=current_row, column=7).value = f"=1/D{current_row}"  # 1/u
    ws.cell(row=current_row, column=8).value = f"=1/C{current_row}"  # 1/m
    ws.cell(row=current_row, column=9).value = f"=1/B{current_row}"  # 1/l
    
    for c in range(1, 10):
        apply_cell_style(ws.cell(row=current_row, column=c))
    current_row += 1

tfn_end_row = current_row - 1
current_row += 1

# ============================================
# MATRIKS PERBANDINGAN BERPASANGAN (CRISP) - INPUT
# ============================================
apply_section_header(ws, current_row, "LANGKAH 1: MATRIKS PERBANDINGAN BERPASANGAN (CRISP) - INPUT", 1, 10)
current_row += 1

ws.cell(row=current_row, column=1).value = "Masukkan nilai perbandingan (1-9). Nilai di bawah diagonal akan otomatis dihitung (resiprokal)."
ws.cell(row=current_row, column=1).font = Font(italic=True, size=9, color="666666")
ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=10)
current_row += 1

crisp_start_row = current_row

# Header row
ws.cell(row=current_row, column=1).value = "Kriteria"
apply_header_style(ws.cell(row=current_row, column=1))
for j, krit in enumerate(kriteria, start=2):
    cell = ws.cell(row=current_row, column=j)
    cell.value = krit
    apply_header_style(cell)

# Extra columns for GM and Eigenvector
ws.cell(row=current_row, column=n+2).value = "GM"
ws.cell(row=current_row, column=n+3).value = "Eigenvector"
apply_header_style(ws.cell(row=current_row, column=n+2), fill=green_fill)
apply_header_style(ws.cell(row=current_row, column=n+3), fill=green_fill)
current_row += 1

crisp_data_start = current_row

# Data rows dengan formula
for i in range(n):
    # Kriteria name
    cell = ws.cell(row=current_row, column=1)
    cell.value = kriteria[i]
    cell.font = Font(bold=True, size=10)
    cell.border = thin_border
    cell.fill = light_blue_fill
    cell.alignment = left_align
    
    for j in range(n):
        cell = ws.cell(row=current_row, column=j + 2)
        if i == j:
            # Diagonal = 1 (fixed)
            cell.value = 1
            apply_cell_style(cell)
        elif i < j:
            # Upper triangle - INPUT (dapat diubah)
            cell.value = 1  # Default value
            apply_input_style(cell)
            cell.comment = Comment("INPUT: Masukkan nilai 1-9", "System")
        else:
            # Lower triangle - FORMULA (resiprokal dari upper)
            upper_cell = get_column_letter(i + 2) + str(crisp_data_start + j)
            cell.value = f"=1/{upper_cell}"
            apply_cell_style(cell)
            cell.fill = light_green_fill
    
    # Geometric Mean formula: =PRODUCT(range)^(1/n)
    gm_range = f"{get_column_letter(2)}{current_row}:{get_column_letter(n+1)}{current_row}"
    gm_cell = ws.cell(row=current_row, column=n+2)
    gm_cell.value = f"=PRODUCT({gm_range})^(1/{n})"
    apply_cell_style(gm_cell)
    gm_cell.fill = light_green_fill
    
    current_row += 1

crisp_data_end = current_row - 1

# Sum of GM
ws.cell(row=current_row, column=n+1).value = "Total GM:"
ws.cell(row=current_row, column=n+1).font = Font(bold=True)
gm_sum_cell = ws.cell(row=current_row, column=n+2)
gm_sum_cell.value = f"=SUM({get_column_letter(n+2)}{crisp_data_start}:{get_column_letter(n+2)}{crisp_data_end})"
gm_sum_cell.font = Font(bold=True)
apply_cell_style(gm_sum_cell)
gm_sum_cell.fill = yellow_fill

gm_sum_ref = f"${get_column_letter(n+2)}${current_row}"
current_row += 1

# Add Eigenvector formulas (need to go back and add them)
for i in range(n):
    row = crisp_data_start + i
    ev_cell = ws.cell(row=row, column=n+3)
    gm_cell_ref = f"{get_column_letter(n+2)}{row}"
    ev_cell.value = f"={gm_cell_ref}/{gm_sum_ref}"
    apply_cell_style(ev_cell)
    ev_cell.fill = light_green_fill

# Sum of Eigenvector (should be 1)
ws.cell(row=current_row-1, column=n+3).value = f"=SUM({get_column_letter(n+3)}{crisp_data_start}:{get_column_letter(n+3)}{crisp_data_end})"
ws.cell(row=current_row-1, column=n+3).font = Font(bold=True)
apply_cell_style(ws.cell(row=current_row-1, column=n+3))
ws.cell(row=current_row-1, column=n+3).fill = yellow_fill

current_row += 1

# ============================================
# PERHITUNGAN LAMBDA MAX & KONSISTENSI
# ============================================
apply_section_header(ws, current_row, "LANGKAH 2 & 3: PERHITUNGAN LAMBDA MAX & UJI KONSISTENSI", 1, 10)
current_row += 1

# A*w calculation (untuk lambda max)
ws.cell(row=current_row, column=1).value = "Perhitungan A*w (Matriks x Eigenvector):"
ws.cell(row=current_row, column=1).font = subtitle_font
current_row += 1

ws.cell(row=current_row, column=1).value = "Kriteria"
ws.cell(row=current_row, column=2).value = "A*w"
ws.cell(row=current_row, column=3).value = "(A*w)/w"
apply_header_style(ws.cell(row=current_row, column=1))
apply_header_style(ws.cell(row=current_row, column=2))
apply_header_style(ws.cell(row=current_row, column=3))
current_row += 1

aw_start_row = current_row
for i in range(n):
    ws.cell(row=current_row, column=1).value = kriteria[i]
    apply_cell_style(ws.cell(row=current_row, column=1))
    ws.cell(row=current_row, column=1).fill = light_blue_fill
    
    # A*w = SUMPRODUCT of row i in crisp matrix with eigenvector column
    crisp_row_range = f"{get_column_letter(2)}{crisp_data_start + i}:{get_column_letter(n+1)}{crisp_data_start + i}"
    ev_range = f"${get_column_letter(n+3)}${crisp_data_start}:${get_column_letter(n+3)}${crisp_data_end}"
    
    aw_cell = ws.cell(row=current_row, column=2)
    aw_cell.value = f"=SUMPRODUCT({crisp_row_range},{ev_range})"
    apply_cell_style(aw_cell)
    aw_cell.fill = light_green_fill
    
    # (A*w)/w
    ev_cell_ref = f"{get_column_letter(n+3)}{crisp_data_start + i}"
    ratio_cell = ws.cell(row=current_row, column=3)
    ratio_cell.value = f"=B{current_row}/{ev_cell_ref}"
    apply_cell_style(ratio_cell)
    ratio_cell.fill = light_green_fill
    
    current_row += 1

aw_end_row = current_row - 1
current_row += 1

# Lambda Max, CI, CR calculation
ws.cell(row=current_row, column=1).value = "Lambda Max (λmax):"
ws.cell(row=current_row, column=1).font = subtitle_font
lambda_max_cell = ws.cell(row=current_row, column=2)
lambda_max_cell.value = f"=AVERAGE(C{aw_start_row}:C{aw_end_row})"
lambda_max_cell.font = Font(bold=True, size=14, color="ED7D31")
lambda_max_cell.fill = yellow_fill
apply_cell_style(lambda_max_cell)
lambda_max_ref = f"$B${current_row}"

ws.cell(row=current_row, column=4).value = "Rumus: λmax = (1/n) * Σ(A*w/w)"
ws.cell(row=current_row, column=4).font = formula_font
current_row += 1

# CI
ws.cell(row=current_row, column=1).value = "Consistency Index (CI):"
ws.cell(row=current_row, column=1).font = subtitle_font
ci_cell = ws.cell(row=current_row, column=2)
ci_cell.value = f"=({lambda_max_ref}-{n})/({n}-1)"
ci_cell.font = Font(bold=True, size=12)
ci_cell.fill = light_green_fill
apply_cell_style(ci_cell)
ci_ref = f"$B${current_row}"

ws.cell(row=current_row, column=4).value = "Rumus: CI = (λmax - n) / (n - 1)"
ws.cell(row=current_row, column=4).font = formula_font
current_row += 1

# RI
ws.cell(row=current_row, column=1).value = "Random Index (RI):"
ws.cell(row=current_row, column=1).font = subtitle_font
ri_cell = ws.cell(row=current_row, column=2)
ri_cell.value = ri_values[n-1]  # RI for n=6 is 1.24
ri_cell.font = Font(bold=True, size=12)
apply_cell_style(ri_cell)
ri_ref = f"$B${current_row}"

ws.cell(row=current_row, column=4).value = f"Untuk n={n}, RI = {ri_values[n-1]}"
ws.cell(row=current_row, column=4).font = formula_font
current_row += 1

# CR
ws.cell(row=current_row, column=1).value = "Consistency Ratio (CR):"
ws.cell(row=current_row, column=1).font = subtitle_font
cr_cell = ws.cell(row=current_row, column=2)
cr_cell.value = f"=IF({ri_ref}=0,0,{ci_ref}/{ri_ref})"
cr_cell.font = Font(bold=True, size=14)
cr_cell.fill = yellow_fill
apply_cell_style(cr_cell)
cr_ref = f"$B${current_row}"

ws.cell(row=current_row, column=4).value = "Rumus: CR = CI / RI"
ws.cell(row=current_row, column=4).font = formula_font
current_row += 1

# Status Konsistensi
ws.cell(row=current_row, column=1).value = "Status Konsistensi:"
ws.cell(row=current_row, column=1).font = subtitle_font
status_cell = ws.cell(row=current_row, column=2)
status_cell.value = f'=IF({cr_ref}<=0.1,"KONSISTEN (CR <= 0.1)","TIDAK KONSISTEN (CR > 0.1)")'
status_cell.font = Font(bold=True, size=11)
apply_cell_style(status_cell)
ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=4)

current_row += 2

# ============================================
# MATRIKS FUZZY (TFN)
# ============================================
apply_section_header(ws, current_row, "LANGKAH 4: FUZZIFIKASI MATRIKS PERBANDINGAN (TFN)", 1, 20)
current_row += 1

ws.cell(row=current_row, column=1).value = "Nilai crisp dikonversi ke Triangular Fuzzy Number (l, m, u) menggunakan tabel referensi di atas"
ws.cell(row=current_row, column=1).font = Font(italic=True, size=9, color="666666")
ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=20)
current_row += 1

fuzzy_start_row = current_row

# Header row
ws.cell(row=current_row, column=1).value = "Kriteria"
apply_header_style(ws.cell(row=current_row, column=1))

col_idx = 2
for krit in kriteria:
    ws.merge_cells(start_row=current_row, start_column=col_idx, end_row=current_row, end_column=col_idx+2)
    cell = ws.cell(row=current_row, column=col_idx)
    cell.value = krit[:10]
    apply_header_style(cell)
    col_idx += 3
current_row += 1

# Sub-header (l, m, u)
ws.cell(row=current_row, column=1).value = ""
apply_header_style(ws.cell(row=current_row, column=1), fill=yellow_fill)
col_idx = 2
for _ in kriteria:
    for label in ["l", "m", "u"]:
        cell = ws.cell(row=current_row, column=col_idx)
        cell.value = label
        apply_header_style(cell, fill=yellow_fill)
        col_idx += 1
current_row += 1

fuzzy_data_start = current_row

# Data rows dengan formula VLOOKUP
for i in range(n):
    cell = ws.cell(row=current_row, column=1)
    cell.value = kriteria[i]
    cell.font = Font(bold=True, size=9)
    cell.border = thin_border
    cell.fill = light_blue_fill
    
    col_idx = 2
    for j in range(n):
        crisp_cell = f"{get_column_letter(j+2)}{crisp_data_start + i}"
        
        # Formula untuk mengambil TFN berdasarkan nilai crisp
        # Menggunakan INDEX/MATCH atau VLOOKUP
        tfn_table = f"$A${tfn_start_row}:$D${tfn_end_row}"
        
        if i <= j:
            # Upper triangle atau diagonal - gunakan TFN langsung
            l_formula = f"=INDEX($B${tfn_start_row}:$B${tfn_end_row},MATCH(ROUND(ABS({crisp_cell}),0),$A${tfn_start_row}:$A${tfn_end_row},0))"
            m_formula = f"=INDEX($C${tfn_start_row}:$C${tfn_end_row},MATCH(ROUND(ABS({crisp_cell}),0),$A${tfn_start_row}:$A${tfn_end_row},0))"
            u_formula = f"=INDEX($D${tfn_start_row}:$D${tfn_end_row},MATCH(ROUND(ABS({crisp_cell}),0),$A${tfn_start_row}:$A${tfn_end_row},0))"
        else:
            # Lower triangle - gunakan reciprocal (1/u, 1/m, 1/l)
            upper_crisp = f"{get_column_letter(i+2)}{crisp_data_start + j}"
            l_formula = f"=1/INDEX($D${tfn_start_row}:$D${tfn_end_row},MATCH(ROUND(ABS({upper_crisp}),0),$A${tfn_start_row}:$A${tfn_end_row},0))"
            m_formula = f"=1/INDEX($C${tfn_start_row}:$C${tfn_end_row},MATCH(ROUND(ABS({upper_crisp}),0),$A${tfn_start_row}:$A${tfn_end_row},0))"
            u_formula = f"=1/INDEX($B${tfn_start_row}:$B${tfn_end_row},MATCH(ROUND(ABS({upper_crisp}),0),$A${tfn_start_row}:$A${tfn_end_row},0))"
        
        ws.cell(row=current_row, column=col_idx).value = l_formula
        ws.cell(row=current_row, column=col_idx+1).value = m_formula
        ws.cell(row=current_row, column=col_idx+2).value = u_formula
        
        for c in range(col_idx, col_idx+3):
            apply_cell_style(ws.cell(row=current_row, column=c))
            if i > j:
                ws.cell(row=current_row, column=c).fill = light_green_fill
        
        col_idx += 3
    
    current_row += 1

fuzzy_data_end = current_row - 1
current_row += 1

# ============================================
# PERHITUNGAN FUZZY SYNTHETIC EXTENT
# ============================================
apply_section_header(ws, current_row, "LANGKAH 5: PERHITUNGAN FUZZY SYNTHETIC EXTENT", 1, 10)
current_row += 1

ws.cell(row=current_row, column=1).value = "Si = (Σl, Σm, Σu) untuk setiap baris, lalu dinormalisasi"
ws.cell(row=current_row, column=1).font = Font(italic=True, size=9, color="666666")
ws.merge_cells(start_row=current_row, start_column=1, end_row=current_row, end_column=10)
current_row += 1

# Header
ws.cell(row=current_row, column=1).value = "Kriteria"
ws.cell(row=current_row, column=2).value = "Σl"
ws.cell(row=current_row, column=3).value = "Σm"
ws.cell(row=current_row, column=4).value = "Σu"
for c in range(1, 5):
    apply_header_style(ws.cell(row=current_row, column=c))
current_row += 1

sum_start = current_row
# Calculate sum of each row
for i in range(n):
    ws.cell(row=current_row, column=1).value = kriteria[i]
    apply_cell_style(ws.cell(row=current_row, column=1))
    ws.cell(row=current_row, column=1).fill = light_blue_fill
    
    # Sum l columns (every 3rd starting from col 2)
    l_cells = "+".join([f"{get_column_letter(2 + j*3)}{fuzzy_data_start + i}" for j in range(n)])
    ws.cell(row=current_row, column=2).value = f"={l_cells}"
    apply_cell_style(ws.cell(row=current_row, column=2))
    ws.cell(row=current_row, column=2).fill = light_green_fill
    
    # Sum m columns
    m_cells = "+".join([f"{get_column_letter(3 + j*3)}{fuzzy_data_start + i}" for j in range(n)])
    ws.cell(row=current_row, column=3).value = f"={m_cells}"
    apply_cell_style(ws.cell(row=current_row, column=3))
    ws.cell(row=current_row, column=3).fill = light_green_fill
    
    # Sum u columns
    u_cells = "+".join([f"{get_column_letter(4 + j*3)}{fuzzy_data_start + i}" for j in range(n)])
    ws.cell(row=current_row, column=4).value = f"={u_cells}"
    apply_cell_style(ws.cell(row=current_row, column=4))
    ws.cell(row=current_row, column=4).fill = light_green_fill
    
    current_row += 1

sum_end = current_row - 1

# Total row
ws.cell(row=current_row, column=1).value = "TOTAL"
ws.cell(row=current_row, column=1).font = Font(bold=True)
apply_cell_style(ws.cell(row=current_row, column=1))

for c in range(2, 5):
    col_letter = get_column_letter(c)
    ws.cell(row=current_row, column=c).value = f"=SUM({col_letter}{sum_start}:{col_letter}{sum_end})"
    ws.cell(row=current_row, column=c).font = Font(bold=True)
    apply_cell_style(ws.cell(row=current_row, column=c))
    ws.cell(row=current_row, column=c).fill = yellow_fill

total_row = current_row
current_row += 2

# ============================================
# BOBOT AKHIR KRITERIA
# ============================================
apply_section_header(ws, current_row, "RINGKASAN: BOBOT KRITERIA HASIL FUZZY AHP", 1, 10)
current_row += 1

ws.cell(row=current_row, column=1).value = "No"
ws.cell(row=current_row, column=2).value = "Kriteria"
ws.cell(row=current_row, column=3).value = "Bobot (wi)"
ws.cell(row=current_row, column=4).value = "Bobot (%)"
apply_header_style(ws.cell(row=current_row, column=1), fill=green_fill)
apply_header_style(ws.cell(row=current_row, column=2), fill=green_fill)
apply_header_style(ws.cell(row=current_row, column=3), fill=green_fill)
apply_header_style(ws.cell(row=current_row, column=4), fill=green_fill)
current_row += 1

bobot_start = current_row
for i in range(n):
    ws.cell(row=current_row, column=1).value = i + 1
    apply_cell_style(ws.cell(row=current_row, column=1))
    
    ws.cell(row=current_row, column=2).value = kriteria[i]
    apply_cell_style(ws.cell(row=current_row, column=2))
    
    # Eigenvector reference
    ev_ref = f"{get_column_letter(n+3)}{crisp_data_start + i}"
    ws.cell(row=current_row, column=3).value = f"={ev_ref}"
    apply_cell_style(ws.cell(row=current_row, column=3))
    ws.cell(row=current_row, column=3).fill = light_green_fill
    ws.cell(row=current_row, column=3).number_format = '0.0000'
    
    # Percentage
    ws.cell(row=current_row, column=4).value = f"={ev_ref}*100"
    apply_cell_style(ws.cell(row=current_row, column=4))
    ws.cell(row=current_row, column=4).fill = light_yellow_fill
    ws.cell(row=current_row, column=4).number_format = '0.00"%"'
    
    current_row += 1

bobot_end = current_row - 1

# Total
ws.cell(row=current_row, column=2).value = "TOTAL"
ws.cell(row=current_row, column=2).font = Font(bold=True)
apply_cell_style(ws.cell(row=current_row, column=2))

ws.cell(row=current_row, column=3).value = f"=SUM(C{bobot_start}:C{bobot_end})"
ws.cell(row=current_row, column=3).font = Font(bold=True)
apply_cell_style(ws.cell(row=current_row, column=3))
ws.cell(row=current_row, column=3).fill = yellow_fill

ws.cell(row=current_row, column=4).value = f"=SUM(D{bobot_start}:D{bobot_end})"
ws.cell(row=current_row, column=4).font = Font(bold=True)
apply_cell_style(ws.cell(row=current_row, column=4))
ws.cell(row=current_row, column=4).fill = yellow_fill

current_row += 2

# Status box
ws.cell(row=current_row, column=1).value = "STATUS:"
ws.cell(row=current_row, column=1).font = subtitle_font
ws.cell(row=current_row, column=2).value = f'=IF({cr_ref}<=0.1,"VALID - Hasil dapat digunakan","TIDAK VALID - Perbaiki matriks perbandingan")'
ws.cell(row=current_row, column=2).font = Font(bold=True, size=11)
ws.merge_cells(start_row=current_row, start_column=2, end_row=current_row, end_column=5)

# ============================================
# Set column widths
# ============================================
ws.column_dimensions['A'].width = 22
ws.column_dimensions['B'].width = 14
ws.column_dimensions['C'].width = 14
ws.column_dimensions['D'].width = 14
ws.column_dimensions['E'].width = 14
ws.column_dimensions['F'].width = 12
ws.column_dimensions['G'].width = 12
ws.column_dimensions['H'].width = 12
ws.column_dimensions['I'].width = 12
ws.column_dimensions['J'].width = 12
for j in range(11, 25):
    ws.column_dimensions[get_column_letter(j)].width = 7

# Save workbook
output_file = "d:/laragon/www/appSaringPramuka/Fuzzy_AHP_Calculator.xlsx"
wb.save(output_file)
print(f"[OK] File Excel dengan RUMUS berhasil dibuat: {output_file}")
print("\n=== CARA PENGGUNAAN ===")
print("1. Buka file Excel")
print("2. Cari sel berwarna KUNING MUDA (input cells)")
print("3. Ubah nilai pada MATRIKS PERBANDINGAN BERPASANGAN (diagonal atas)")
print("4. Masukkan nilai 1-9 sesuai skala Saaty")
print("5. Hasil akan OTOMATIS terhitung:")
print("   - Eigenvector (bobot kriteria)")
print("   - Lambda Max")
print("   - CI, CR, dan Status Konsistensi")
print("   - Matriks Fuzzy TFN")
print("   - Fuzzy Synthetic Extent")
print("6. Gunakan untuk validasi hasil perhitungan di sistem")
