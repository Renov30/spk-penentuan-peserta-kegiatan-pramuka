import sys
import os

# Menambahkan direktori aplikasi ke sys.path
sys.path.insert(0, os.path.dirname(__file__))

# Mengimpor aplikasi Flask
# Pastikan di run.py terdapat variabel 'app' (app = create_app())
from run import app as application

# Opsional: Jika hosting memerlukan objek 'application'
# application = app
