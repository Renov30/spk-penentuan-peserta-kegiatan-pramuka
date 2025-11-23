from app import db
from app.models import Penilaian, Criteria, HasilSeleksi, Users, Participants
import pandas as pd
import numpy as np

def calculate_spk(event_id):
    """
    Menghitung SPK menggunakan metode Fuzzy AHP / Simple Additive Weighting (SAW) dengan bobot dari AHP.
    Karena struktur database sudah memiliki bobot di tabel Criteria, kita asumsikan bobot sudah dihitung (atau diinput manual).
    Fungsi ini akan:
    1. Mengambil semua nilai penilaian untuk event tersebut.
    2. Melakukan rata-rata nilai jika ada banyak penilai.
    3. Normalisasi nilai (jika diperlukan, tergantung range nilai).
    4. Mengalikan dengan bobot kriteria.
    5. Menjumlahkan hasil untuk mendapatkan skor akhir.
    6. Menyimpan hasil ke tabel HasilSeleksi.
    """
    
    # 1. Ambil Kriteria dan Bobot
    criterias = Criteria.query.filter_by(event_id=event_id).all()
    if not criterias:
        return False, "Tidak ada kriteria untuk kegiatan ini."
    
    criteria_weights = {c.id_kriteria: c.bobot for c in criterias}
    criteria_types = {c.id_kriteria: c.jenis_kriteria for c in criterias} # Benefit or Cost (asumsi benefit semua untuk seleksi)

    # 2. Ambil Peserta yang mengikuti kegiatan ini
    participants = Participants.query.filter_by(kegiatan_id=event_id).all()
    if not participants:
        return False, "Tidak ada peserta untuk kegiatan ini."
    
    participant_emails = [p.email for p in participants]
    users = Users.query.filter(Users.email.in_(participant_emails)).all()
    user_map = {u.email: u.id for u in users}
    
    participant_ids = [user_map[p.email] for p in participants if p.email in user_map]

    if not participant_ids:
        return False, "Data user peserta tidak ditemukan."

    # 3. Ambil Penilaian
    # Kita perlu rata-rata nilai dari semua penilai untuk setiap peserta dan kriteria
    # Query: Select id_users, id_kriteria, AVG(nilai) from Penilaian where id_users in participant_ids group by id_users, id_kriteria
    
    scores = {} # {user_id: {criteria_id: score}}
    
    for uid in participant_ids:
        scores[uid] = {}
        for cid in criteria_weights.keys():
            # Ambil rata-rata nilai dari semua penilai
            avg_score = db.session.query(db.func.avg(Penilaian.nilai)).filter_by(
                id_users=uid,
                id_kriteria=cid
            ).scalar()
            
            scores[uid][cid] = float(avg_score) if avg_score else 0.0

    # 4. Perhitungan SAW (Simple Additive Weighting)
    # Karena input nilai sudah berupa angka (dari fuzzy set atau input langsung), kita bisa langsung kali bobot.
    # Asumsi: Nilai sudah dalam skala yang sama (misal 1-5 atau 0-100). Jika beda, perlu normalisasi.
    # Untuk simplifikasi, kita asumsikan range nilai konsisten (misal 0-100).
    
    final_scores = []
    
    for uid, user_scores in scores.items():
        total_score = 0
        for cid, score in user_scores.items():
            weight = criteria_weights.get(cid, 0)
            # Normalisasi sederhana: score / max_score (jika max 100) -> score / 100
            # Atau jika bobot dalam persen (total 100), langsung kali.
            # Asumsi bobot total = 1 (atau 100).
            
            total_score += score * weight
            
        final_scores.append({
            'user_id': uid,
            'score': total_score
        })
    
    # 5. Ranking
    final_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 6. Simpan ke Database
    try:
        # Hapus hasil lama untuk event ini (opsional, atau update)
        # Karena HasilSeleksi tidak ada event_id, kita hapus berdasarkan user_id yang ikut event ini
        HasilSeleksi.query.filter(HasilSeleksi.id_users.in_(participant_ids)).delete(synchronize_session=False)
        
        for rank, item in enumerate(final_scores, 1):
            hasil = HasilSeleksi(
                id_users=item['user_id'],
                skor_akhir=item['score'],
                ranking=rank
            )
            db.session.add(hasil)
            
        db.session.commit()
        return True, "Perhitungan SPK berhasil."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error menyimpan hasil: {str(e)}"
