from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # 1. Add columns to tb_kegiatan if they don't exist
    with db.engine.connect() as conn:
        # Check if columns exist (simple try-catch approach or inspection)
        try:
            conn.execute(text("ALTER TABLE tb_kegiatan ADD COLUMN tanggal_tes DATE"))
            print("Added column tanggal_tes")
        except Exception as e:
            print(f"Column tanggal_tes might already exist or error: {e}")
            
        try:
            conn.execute(text("ALTER TABLE tb_kegiatan ADD COLUMN tempat_tes VARCHAR(100)"))
            print("Added column tempat_tes")
        except Exception as e:
            print(f"Column tempat_tes might already exist or error: {e}")

        # 2. Create tb_event_evaluator table
        # Since db.create_all() usually creates new tables but doesn't alter existing ones,
        # we can try running it again to create the new association table.
        try:
            db.create_all()
            print("Ran db.create_all() to ensure tb_event_evaluator exists")
        except Exception as e:
            print(f"Error creating tables: {e}")
            
    print("Migration completed.")
