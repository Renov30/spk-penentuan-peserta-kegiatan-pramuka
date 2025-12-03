from app import db
from app.models import Penilaian, Criteria, HasilSeleksi, Users, Participants, Event
import pandas as pd
import numpy as np

def calculate_spk(event_id):
    """
    Menghitung SPK menggunakan metode Fuzzy AHP.
    Langkah-langkah:
    1. Ambil data penilaian dan kriteria.
    2. Fuzzifikasi nilai (Konversi nilai tegas ke bilangan fuzzy segitiga).
    3. Agregasi nilai fuzzy dengan bobot kriteria.
    4. Defuzzifikasi (Center of Area) untuk mendapatkan nilai akhir tegas.
    5. Ranking peserta.
    6. Simpan hasil ke database.
    """
    
    # 1. Ambil Kriteria dan Bobot
    criterias = Criteria.query.filter_by(event_id=event_id).all()
    if not criterias:
        return False, "Tidak ada kriteria untuk kegiatan ini."
    
    # Bobot kriteria (Crisp Weight from AHP) - Asumsi bobot di DB sudah ternormalisasi (total = 1)
    # Jika belum, sebaiknya dinormalisasi dulu.
    total_bobot = sum(c.bobot for c in criterias)
    criteria_weights = {c.id_kriteria: (c.bobot / total_bobot if total_bobot > 0 else 0) for c in criterias}

    # 2. Ambil Peserta yang mengikuti kegiatan ini
    event = Event.query.get(event_id)
    if not event:
        return False, "Kegiatan tidak ditemukan."
        
    participants = event.registered_participants.all()
    
    # Fallback for backward compatibility or if using old relation
    if not participants:
        participants = Participants.query.filter_by(kegiatan_id=event_id).all()
        
    if not participants:
        return False, "Tidak ada peserta untuk kegiatan ini."
    
    # Mapping email peserta ke user ID (karena Penilaian pakai user_id)
    participant_emails = [p.email for p in participants]
    users = Users.query.filter(Users.email.in_(participant_emails)).all()
    user_map = {u.email: u.id for u in users}
    
    participant_ids = [user_map[p.email] for p in participants if p.email in user_map]

    if not participant_ids:
        return False, "Data user peserta tidak ditemukan."

    # 3. Proses Penilaian (Fuzzifikasi & Agregasi)
    final_scores = []
    
    for uid in participant_ids:
        fuzzy_total_l = 0
        fuzzy_total_m = 0
        fuzzy_total_u = 0
        
        has_score = False
        
        for cid, weight in criteria_weights.items():
            # Ambil rata-rata nilai dari semua penilai untuk kriteria ini
            avg_score = db.session.query(db.func.avg(Penilaian.nilai)).filter_by(
                id_users=uid,
                id_kriteria=cid
            ).scalar()
            
            if avg_score is not None:
                has_score = True
                score = float(avg_score)
                
                # --- FUZZIFIKASI ---
                # Konversi nilai skalar ke Fuzzy Triangular Number (L, M, U)
                # Asumsi range nilai input bisa 1-5 (Likert) atau 1-100
                
                l, m, u = 0, 0, 0
                
                if score <= 5: # Asumsi Skala Likert 1-5
                    if score <= 1:      # Sangat Kurang
                        l, m, u = 1, 1, 2
                    elif score <= 2:    # Kurang
                        l, m, u = 1, 2, 3
                    elif score <= 3:    # Cukup
                        l, m, u = 2, 3, 4
                    elif score <= 4:    # Baik
                        l, m, u = 3, 4, 5
                    else:               # Sangat Baik
                        l, m, u = 4, 5, 5
                else: # Asumsi Skala 0-100
                    # Fuzzifikasi sederhana: (x-5, x, x+5)
                    l = max(0, score - 5)
                    m = score
                    u = min(100, score + 5)
                    
                    # Normalisasi ke skala 0-1 (opsional, tapi biar konsisten dengan bobot)
                    # Disini kita tetap pakai skala asli, nanti hasil akhir juga skala asli.
                
                # --- AGREGASI DENGAN BOBOT ---
                # Fuzzy Score * Bobot (Skalar) = (L*w, M*w, U*w)
                fuzzy_total_l += l * weight
                fuzzy_total_m += m * weight
                fuzzy_total_u += u * weight
        
        if has_score:
            # --- DEFUZZIFIKASI (Center of Area) ---
            # Score = (L + M + U) / 3
            defuzzified_score = (fuzzy_total_l + fuzzy_total_m + fuzzy_total_u) / 3
            
            final_scores.append({
                'user_id': uid,
                'score': defuzzified_score
            })
    
    # 4. Ranking
    final_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 5. Simpan ke Database
    try:
        # Hapus hasil lama untuk event ini
        HasilSeleksi.query.filter_by(event_id=event_id).delete()
        
        # Jika masih ada data lama tanpa event_id untuk user yang sama, hapus juga (opsional, untuk cleanup)
        if final_scores:
             user_ids = [x['user_id'] for x in final_scores]
             HasilSeleksi.query.filter(HasilSeleksi.id_users.in_(user_ids), HasilSeleksi.event_id == None).delete(synchronize_session=False)

        for rank, item in enumerate(final_scores, 1):
            hasil = HasilSeleksi(
                id_users=item['user_id'],
                skor_akhir=item['score'],
                ranking=rank,
                event_id=event_id
            )
            db.session.add(hasil)
            
        db.session.commit()
        return True, "Perhitungan Fuzzy AHP berhasil."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error menyimpan hasil: {str(e)}"
