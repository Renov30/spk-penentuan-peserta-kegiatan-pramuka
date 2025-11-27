from app import create_app, db
from sqlalchemy import text

app = create_app()

def update_schema():
    with app.app_context():
        try:
            # Check if column exists
            check_query = text("SHOW COLUMNS FROM tb_kegiatan LIKE 'batas_lolos'")
            result = db.session.execute(check_query).fetchone()
            
            if not result:
                print("Adding 'batas_lolos' column to 'tb_kegiatan'...")
                alter_query = text("ALTER TABLE tb_kegiatan ADD COLUMN batas_lolos INT DEFAULT 3")
                db.session.execute(alter_query)
                db.session.commit()
                print("Column added successfully.")
            else:
                print("Column 'batas_lolos' already exists.")
                
        except Exception as e:
            print(f"Error updating schema: {e}")
            db.session.rollback()

if __name__ == "__main__":
    update_schema()
