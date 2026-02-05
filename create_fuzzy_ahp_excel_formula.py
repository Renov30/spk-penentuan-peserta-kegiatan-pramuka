"""
Script untuk membuat Model Tabel Excel Perhitungan Fuzzy AHP
VERSI 4 - Formula sederhana tanpa INDEX/MATCH untuk menghindari corrupt file
"""

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# Create workbook
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Fuzzy AHP"

# Styles
header_font = Font(bold=True, size=11, color="FFFFFF")
subtitle_font = Font(bold=True, size=11, color="1F4E79")
section_font = Font(bold=True, size=12, color="FFFFFF")
normal_font = Font(size=10)
input_font = Font(size=11, color="0000FF")
center_align = Alignment(horizontal='center', vertical='center')
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
light_blue_fill = PatternFill(start_color="D6DCE4", end_color="D6DCE4", fill_type="solid")
light_green_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
input_fill = PatternFill(start_color="FFFFCC", end_color="FFFFCC", fill_type="solid")

kriteria = ["K1", "K2", "K3", "K4", "K5", "K6"]
kriteria_full = [
    "Status Keaktifan",
    "Pencapaian SKU", 
    "Pencapaian SPG",
    "Kesehatan Jasmani",
    "Tes Wawancara",
    "Tes Pilihan Ganda"
]
n = 6

def style_header(cell, fill=header_fill):
    cell.font = header_font
    cell.alignment = center_align
    cell.border = thin_border
    cell.fill = fill

def style_cell(cell):
    cell.font = normal_font
    cell.alignment = center_align
    cell.border = thin_border

def style_input(cell):
    cell.font = input_font
    cell.alignment = center_align
    cell.border = thin_border
    cell.fill = input_fill

def section_header(row, text, col_end=9):
    cell = ws.cell(row=row, column=1)
    cell.value = text
    cell.font = section_font
    cell.fill = section_fill
    cell.alignment = center_align
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=col_end)

row = 1

# Title
ws['A1'] = "FUZZY AHP CALCULATOR"
ws['A1'].font = Font(bold=True, size=16, color="1F4E79")
ws.merge_cells('A1:I1')

ws['A2'] = "Ubah nilai di sel KUNING (diagonal atas matriks)"
ws['A2'].font = Font(italic=True, color="FF0000")
ws.merge_cells('A2:I2')

row = 4

# ============================================
# MATRIKS PERBANDINGAN BERPASANGAN
# ============================================
section_header(row, "MATRIKS PERBANDINGAN BERPASANGAN (CRISP)")
row += 1

# Header
ws.cell(row=row, column=1).value = ""
style_header(ws.cell(row=row, column=1))
for j in range(n):
    cell = ws.cell(row=row, column=j+2)
    cell.value = kriteria[j]
    style_header(cell)

# GM dan Wi headers
ws.cell(row=row, column=8).value = "GM"
ws.cell(row=row, column=9).value = "Wi"
style_header(ws.cell(row=row, column=8), fill=green_fill)
style_header(ws.cell(row=row, column=9), fill=green_fill)
row += 1

data_start = row  # Row 6

# Data matriks - simplified
for i in range(n):
    cell = ws.cell(row=row, column=1)
    cell.value = kriteria[i]
    cell.font = Font(bold=True)
    cell.border = thin_border
    cell.fill = light_blue_fill
    
    for j in range(n):
        cell = ws.cell(row=row, column=j+2)
        if i == j:
            cell.value = 1
            style_cell(cell)
        elif i < j:
            # Upper triangle - INPUT
            cell.value = 1
            style_input(cell)
        else:
            # Lower triangle - reciprocal formula
            # Referensi ke sel di upper triangle
            upper_row = data_start + j
            upper_col = get_column_letter(i + 2)
            cell.value = f"=1/{upper_col}{upper_row}"
            style_cell(cell)
            cell.fill = light_green_fill
    
    # GM formula: =(B*C*D*E*F*G)^(1/6)
    gm_cell = ws.cell(row=row, column=8)
    cols = "B C D E F G".split()
    gm_formula = f"=({cols[0]}{row}*{cols[1]}{row}*{cols[2]}{row}*{cols[3]}{row}*{cols[4]}{row}*{cols[5]}{row})^(1/6)"
    gm_cell.value = gm_formula
    style_cell(gm_cell)
    gm_cell.fill = light_green_fill
    gm_cell.number_format = '0.0000'
    
    row += 1

data_end = row - 1  # Row 11

# Total GM
ws.cell(row=row, column=7).value = "Total:"
ws.cell(row=row, column=7).font = Font(bold=True)

gm_sum = ws.cell(row=row, column=8)
gm_sum.value = f"=SUM(H{data_start}:H{data_end})"
gm_sum.font = Font(bold=True)
style_cell(gm_sum)
gm_sum.fill = yellow_fill
gm_sum_ref = f"$H${row}"

# Wi formulas
for i in range(n):
    r = data_start + i
    wi_cell = ws.cell(row=r, column=9)
    wi_cell.value = f"=H{r}/{gm_sum_ref}"
    style_cell(wi_cell)
    wi_cell.fill = light_green_fill
    wi_cell.number_format = '0.0000'

# Sum Wi
wi_sum = ws.cell(row=row, column=9)
wi_sum.value = f"=SUM(I{data_start}:I{data_end})"
wi_sum.font = Font(bold=True)
style_cell(wi_sum)
wi_sum.fill = yellow_fill

row += 2

# ============================================
# PERHITUNGAN KONSISTENSI
# ============================================
section_header(row, "PERHITUNGAN KONSISTENSI")
row += 1

# A*w header
ws.cell(row=row, column=1).value = "Kriteria"
ws.cell(row=row, column=2).value = "A*w"
ws.cell(row=row, column=3).value = "(A*w)/w"
style_header(ws.cell(row=row, column=1))
style_header(ws.cell(row=row, column=2))
style_header(ws.cell(row=row, column=3))
row += 1

aw_start = row

for i in range(n):
    ws.cell(row=row, column=1).value = kriteria[i]
    style_cell(ws.cell(row=row, column=1))
    ws.cell(row=row, column=1).fill = light_blue_fill
    
    crisp_row = data_start + i
    
    # A*w = B*I6 + C*I7 + D*I8 + E*I9 + F*I10 + G*I11
    aw_cell = ws.cell(row=row, column=2)
    parts = []
    for j in range(n):
        col = get_column_letter(j + 2)
        wi_row = data_start + j
        parts.append(f"{col}{crisp_row}*$I${wi_row}")
    aw_cell.value = "=" + "+".join(parts)
    style_cell(aw_cell)
    aw_cell.fill = light_green_fill
    aw_cell.number_format = '0.0000'
    
    # (A*w)/w
    ratio_cell = ws.cell(row=row, column=3)
    ratio_cell.value = f"=B{row}/$I${data_start + i}"
    style_cell(ratio_cell)
    ratio_cell.fill = light_green_fill
    ratio_cell.number_format = '0.0000'
    
    row += 1

aw_end = row - 1
row += 1

# Lambda Max
lambda_row = row
ws.cell(row=row, column=1).value = "Lambda Max:"
ws.cell(row=row, column=1).font = subtitle_font
ws.cell(row=row, column=2).value = f"=AVERAGE(C{aw_start}:C{aw_end})"
ws.cell(row=row, column=2).font = Font(bold=True, size=14, color="ED7D31")
ws.cell(row=row, column=2).fill = yellow_fill
style_cell(ws.cell(row=row, column=2))
row += 1

# CI
ci_row = row
ws.cell(row=row, column=1).value = "CI:"
ws.cell(row=row, column=1).font = subtitle_font
ws.cell(row=row, column=2).value = f"=(B{lambda_row}-6)/5"
ws.cell(row=row, column=2).font = Font(bold=True)
ws.cell(row=row, column=2).fill = light_green_fill
style_cell(ws.cell(row=row, column=2))
row += 1

# RI
ri_row = row
ws.cell(row=row, column=1).value = "RI (n=6):"
ws.cell(row=row, column=1).font = subtitle_font
ws.cell(row=row, column=2).value = 1.24
ws.cell(row=row, column=2).font = Font(bold=True)
style_cell(ws.cell(row=row, column=2))
row += 1

# CR
cr_row = row
ws.cell(row=row, column=1).value = "CR:"
ws.cell(row=row, column=1).font = subtitle_font
ws.cell(row=row, column=2).value = f"=B{ci_row}/B{ri_row}"
ws.cell(row=row, column=2).font = Font(bold=True, size=14)
ws.cell(row=row, column=2).fill = yellow_fill
style_cell(ws.cell(row=row, column=2))
row += 1

# Status
ws.cell(row=row, column=1).value = "Status:"
ws.cell(row=row, column=1).font = subtitle_font
ws.cell(row=row, column=2).value = f'=IF(B{cr_row}<=0.1,"KONSISTEN","TIDAK KONSISTEN")'
ws.cell(row=row, column=2).font = Font(bold=True, size=12)
style_cell(ws.cell(row=row, column=2))
ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=3)

row += 2

# ============================================
# TABEL TFN
# ============================================
section_header(row, "TABEL SKALA FUZZY (TFN)")
row += 1

headers = ["Nilai", "l", "m", "u"]
for i, h in enumerate(headers):
    cell = ws.cell(row=row, column=i+1)
    cell.value = h
    style_header(cell)
row += 1

tfn_start = row
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

for val, l, m, u in tfn_data:
    ws.cell(row=row, column=1).value = val
    ws.cell(row=row, column=2).value = l
    ws.cell(row=row, column=3).value = m
    ws.cell(row=row, column=4).value = u
    for c in range(1, 5):
        style_cell(ws.cell(row=row, column=c))
    row += 1

tfn_end = row - 1
row += 1

# ============================================
# MATRIKS FUZZY
# ============================================
section_header(row, "MATRIKS FUZZY (TFN) - LOOKUP MANUAL", col_end=19)
row += 1

ws.cell(row=row, column=1).value = "Gunakan tabel TFN di atas untuk konversi nilai crisp ke (l, m, u)"
ws.cell(row=row, column=1).font = Font(italic=True, size=9, color="666666")
ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=19)
row += 1

# Header
ws.cell(row=row, column=1).value = ""
style_header(ws.cell(row=row, column=1))

col = 2
for k in kriteria:
    ws.merge_cells(start_row=row, start_column=col, end_row=row, end_column=col+2)
    cell = ws.cell(row=row, column=col)
    cell.value = k
    style_header(cell)
    col += 3
row += 1

# Sub-header
ws.cell(row=row, column=1).value = ""
style_header(ws.cell(row=row, column=1), fill=yellow_fill)
col = 2
for _ in range(n):
    for lbl in ["l", "m", "u"]:
        cell = ws.cell(row=row, column=col)
        cell.value = lbl
        style_header(cell, fill=yellow_fill)
        col += 1
row += 1

fuzzy_start = row

# Data - using VLOOKUP for TFN conversion
for i in range(n):
    cell = ws.cell(row=row, column=1)
    cell.value = kriteria[i]
    cell.font = Font(bold=True, size=9)
    cell.border = thin_border
    cell.fill = light_blue_fill
    
    col = 2
    for j in range(n):
        crisp_ref = f"{get_column_letter(j+2)}{data_start + i}"
        
        if i <= j:
            # Upper triangle - VLOOKUP dari tabel TFN
            l_formula = f"=VLOOKUP(ROUND({crisp_ref},0),$A${tfn_start}:$D${tfn_end},2,FALSE)"
            m_formula = f"=VLOOKUP(ROUND({crisp_ref},0),$A${tfn_start}:$D${tfn_end},3,FALSE)"
            u_formula = f"=VLOOKUP(ROUND({crisp_ref},0),$A${tfn_start}:$D${tfn_end},4,FALSE)"
        else:
            # Lower triangle - kebalikan (1/u, 1/m, 1/l)
            upper_ref = f"{get_column_letter(i+2)}{data_start + j}"
            l_formula = f"=1/VLOOKUP(ROUND({upper_ref},0),$A${tfn_start}:$D${tfn_end},4,FALSE)"
            m_formula = f"=1/VLOOKUP(ROUND({upper_ref},0),$A${tfn_start}:$D${tfn_end},3,FALSE)"
            u_formula = f"=1/VLOOKUP(ROUND({upper_ref},0),$A${tfn_start}:$D${tfn_end},2,FALSE)"
        
        ws.cell(row=row, column=col).value = l_formula
        ws.cell(row=row, column=col+1).value = m_formula
        ws.cell(row=row, column=col+2).value = u_formula
        
        for c in range(col, col+3):
            style_cell(ws.cell(row=row, column=c))
            ws.cell(row=row, column=c).number_format = '0.00'
            if i > j:
                ws.cell(row=row, column=c).fill = light_green_fill
        
        col += 3
    
    row += 1

row += 2

# ============================================
# RINGKASAN BOBOT
# ============================================
section_header(row, "RINGKASAN BOBOT KRITERIA")
row += 1

headers = ["No", "Kriteria", "Bobot", "%"]
for i, h in enumerate(headers):
    cell = ws.cell(row=row, column=i+1)
    cell.value = h
    style_header(cell, fill=green_fill)
row += 1

for i in range(n):
    ws.cell(row=row, column=1).value = i + 1
    style_cell(ws.cell(row=row, column=1))
    
    ws.cell(row=row, column=2).value = kriteria_full[i]
    style_cell(ws.cell(row=row, column=2))
    
    ws.cell(row=row, column=3).value = f"=I{data_start + i}"
    style_cell(ws.cell(row=row, column=3))
    ws.cell(row=row, column=3).fill = light_green_fill
    ws.cell(row=row, column=3).number_format = '0.0000'
    
    ws.cell(row=row, column=4).value = f"=I{data_start + i}*100"
    style_cell(ws.cell(row=row, column=4))
    ws.cell(row=row, column=4).number_format = '0.00"%"'
    
    row += 1

# Column widths
ws.column_dimensions['A'].width = 20
ws.column_dimensions['B'].width = 12
ws.column_dimensions['C'].width = 12
ws.column_dimensions['D'].width = 12
ws.column_dimensions['E'].width = 12
ws.column_dimensions['F'].width = 12
ws.column_dimensions['G'].width = 12
ws.column_dimensions['H'].width = 12
ws.column_dimensions['I'].width = 12
for j in range(10, 25):
    ws.column_dimensions[get_column_letter(j)].width = 6

# Save
output_file = "d:/laragon/www/appSaringPramuka/Fuzzy_AHP_Calculator_v4.xlsx"
wb.save(output_file)

print(f"[OK] File berhasil dibuat: {output_file}")
print(f"\nStruktur:")
print(f"  Matriks Crisp: B{data_start}:G{data_end}")
print(f"  GM: H{data_start}:H{data_end}")
print(f"  Wi: I{data_start}:I{data_end}")
print(f"  TFN Table: A{tfn_start}:D{tfn_end}")
