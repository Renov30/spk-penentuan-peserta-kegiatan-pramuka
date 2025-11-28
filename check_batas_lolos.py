from app import create_app, db
from app.models import Event

app = create_app()

with app.app_context():
    # Cek semua event dan batas_lolos mereka
    events = Event.query.all()
    
    print("=== Status Batas Lolos untuk Semua Event ===")
    print(f"Total events: {len(events)}\n")
    
    for event in events:
        print(f"ID: {event.id_kegiatan}")
        print(f"Nama: {event.nama_kegiatan}")
        print(f"Batas Lolos: {event.batas_lolos}")
        print("-" * 50)
    
    # Test update
    if events:
        test_event = events[0]
        print(f"\n=== Test Update Event ID {test_event.id_kegiatan} ===")
        print(f"Batas Lolos sebelum: {test_event.batas_lolos}")
        
        # Coba update
        test_event.batas_lolos = 5
        try:
            db.session.commit()
            print(f"Batas Lolos sesudah: {test_event.batas_lolos}")
            print("✓ Update berhasil!")
            
            # Rollback untuk tidak mengubah data asli
            test_event.batas_lolos = test_event.batas_lolos or 3
            db.session.commit()
        except Exception as e:
            print(f"✗ Update gagal: {e}")
            db.session.rollback()
