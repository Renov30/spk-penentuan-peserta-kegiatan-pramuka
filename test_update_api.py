"""
Script untuk test API update_config
Jalankan aplikasi Flask terlebih dahulu, lalu jalankan script ini
"""
import requests
import json

# Konfigurasi
BASE_URL = "http://localhost:5000"  # Sesuaikan dengan port aplikasi Anda
EVENT_ID = 41  # ID event yang akan ditest (dari hasil check_batas_lolos.py)

# Data yang akan dikirim
test_data = {
    "event": {
        "nama_kegiatan": "Raimuna Internasional",
        "jenis_kegiatan": "Penegak dan Pandega",
        "skala_kegiatan": "Internasional",
        "kwartir_penyelenggara": "Test Kwartir",
        "tempat_pelaksanaan": "Test Location",
        "batas_lolos": 7  # Ubah dari 4 ke 7
    },
    "kuota": {
        "putra": 10,
        "putri": 10
    }
}

print("=== Test API Update Config ===")
print(f"Target: {BASE_URL}/api/update_config/{EVENT_ID}")
print(f"Data: {json.dumps(test_data, indent=2)}")
print("\nCatatan: Pastikan aplikasi Flask sudah running dan Anda sudah login sebagai admin")
print("\nTekan Enter untuk melanjutkan atau Ctrl+C untuk batal...")
input()

try:
    # Kirim request
    response = requests.post(
        f"{BASE_URL}/api/update_config/{EVENT_ID}",
        json=test_data,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        print("\n✓ Update berhasil!")
    else:
        print("\n✗ Update gagal!")
        
except requests.exceptions.ConnectionError:
    print("\n✗ Tidak bisa connect ke server. Pastikan aplikasi Flask sudah running.")
except Exception as e:
    print(f"\n✗ Error: {e}")
