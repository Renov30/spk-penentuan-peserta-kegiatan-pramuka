from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    with db.engine.connect() as conn:
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS tb_penilaian (
                    id_penilaian INT AUTO_INCREMENT PRIMARY KEY,
                    id_users INT NOT NULL,
                    evaluator_id INT,
                    id_kriteria INT NOT NULL,
                    nilai FLOAT NOT NULL,
                    FOREIGN KEY (id_users) REFERENCES users(id),
                    FOREIGN KEY (evaluator_id) REFERENCES users(id),
                    FOREIGN KEY (id_kriteria) REFERENCES tb_kriteria(id_kriteria)
                ) ENGINE=InnoDB
            """))
            conn.commit()
            print("Successfully created tb_penilaian table")
        except Exception as e:
            print(f"Error: {e}")
