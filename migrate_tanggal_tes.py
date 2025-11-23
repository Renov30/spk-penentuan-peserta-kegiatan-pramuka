from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            # Change tanggal_tes from DATE to VARCHAR(255)
            conn.execute(text("ALTER TABLE tb_kegiatan MODIFY COLUMN tanggal_tes VARCHAR(255)"))
            conn.commit()
            print("Successfully changed tanggal_tes to VARCHAR(255)")
        except Exception as e:
            print(f"Error: {e}")
