from app import create_app, db
from app.models import Criteria

app = create_app()

with app.app_context():
    print("-" * 50)
    print("VERIFICATION RESULTS")
    print("-" * 50)
    c = Criteria.query.filter(Criteria.nama_kriteria.like('%Pilihan Ganda%')).all()
    if not c:
        print("No criteria found.")
    for item in c:
        print(f"ID: {item.id_kriteria}")
        print(f"Name: {item.nama_kriteria}")
        print(f"Type: {item.jenis_kriteria}")
        print("-" * 20)
