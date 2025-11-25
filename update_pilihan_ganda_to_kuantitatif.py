"""
Script to update 'Tes Pilihan Ganda' criteria type to 'kuantitatif'
This will make the grading form show a numeric input (1-100) instead of Likert scale
"""

import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Import models after db is initialized
from app.models import Criteria

def update_pilihan_ganda_to_kuantitatif():
    with app.app_context():
        # Find all criteria with "Pilihan Ganda" in the name
        criteria_list = Criteria.query.filter(
            Criteria.nama_kriteria.like('%Pilihan Ganda%')
        ).all()
        
        if not criteria_list:
            print("❌ No criteria found with 'Pilihan Ganda' in the name")
            return
        
        print(f"Found {len(criteria_list)} criteria to update:")
        print("-" * 80)
        
        for criteria in criteria_list:
            print(f"ID: {criteria.id_kriteria}")
            print(f"Name: {criteria.nama_kriteria}")
            print(f"Current Type: {criteria.jenis_kriteria}")
            print(f"Event ID: {criteria.event_id}")
            
            # Update to kuantitatif
            old_type = criteria.jenis_kriteria
            criteria.jenis_kriteria = 'kuantitatif'
            
            print(f"✓ Updated: {old_type} → kuantitatif")
            print("-" * 80)
        
        # Commit changes
        try:
            db.session.commit()
            print(f"\n✅ Successfully updated {len(criteria_list)} criteria to 'kuantitatif'")
            print("\nNext steps:")
            print("1. Refresh the grading form page")
            print("2. You should now see a numeric input (1-100) for 'Tes Pilihan Ganda'")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error updating criteria: {e}")

if __name__ == '__main__':
    print("=" * 80)
    print("UPDATE TES PILIHAN GANDA TO KUANTITATIF")
    print("=" * 80)
    print()
    update_pilihan_ganda_to_kuantitatif()
