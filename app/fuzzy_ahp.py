"""
Modul untuk perhitungan SPK menggunakan metode Fuzzy AHP lengkap sesuai PDF.
Implementasi lengkap dengan:
1. Matriks perbandingan berpasangan AHP
2. Fuzzifikasi matriks menggunakan TFN
3. Sintesis Fuzzy (Fuzzy Synthetic Extent)
4. Perbandingan probabilitas V(M2 >= M1)
5. Defuzzifikasi ordinat d'(Ai)
"""
from app import db
from app.models import Penilaian, Criteria, HasilSeleksi, Users, Participants, Event, PairwiseComparison, AHPResults
from app.ahp_calculator import AHPCalculator, FuzzyAHPCalculator, TFN_SCALE, get_tfn_reciprocal
import pandas as pd
import numpy as np
import json
from typing import Dict, List, Tuple, Optional

def calculate_ahp_weights(event_id: int, pairwise_matrix: Optional[np.ndarray] = None) -> Tuple[bool, str, Dict]:
    """
    Menghitung bobot kriteria menggunakan AHP lengkap
    
    Args:
        event_id: ID kegiatan
        pairwise_matrix: Matriks perbandingan berpasangan (opsional, jika None akan ambil dari DB)
    
    Returns:
        Tuple (success, message, results_dict)
    """
    # Ambil kriteria
    criterias = Criteria.query.filter_by(event_id=event_id).order_by(Criteria.id_kriteria).all()
    if not criterias:
        return False, "Tidak ada kriteria untuk kegiatan ini.", {}
    
    criteria_names = [c.nama_kriteria for c in criterias]
    criteria_ids = [c.id_kriteria for c in criterias]
    n = len(criterias)
    
    # Jika matriks tidak diberikan, ambil dari database
    if pairwise_matrix is None:
        pairwise_matrix = get_pairwise_matrix_from_db(event_id, criteria_ids)
        if pairwise_matrix is None:
            return False, "Matriks perbandingan berpasangan belum diinput.", {}
    
    # Inisialisasi AHP Calculator
    ahp = AHPCalculator(criteria_names)
    ahp.set_pairwise_matrix(pairwise_matrix)
    
    # Hitung eigenvector
    eigenvector = ahp.calculate_eigenvector()
    
    # Hitung lambda max
    lambda_max = ahp.calculate_lambda_max()
    
    # Uji konsistensi
    ci, cr, is_consistent = ahp.check_consistency()
    
    # Hitung bobot
    weights = ahp.calculate_weights()
    
    # Simpan hasil ke database
    try:
        # Hapus hasil lama
        AHPResults.query.filter_by(event_id=event_id).delete()
        
        # Simpan hasil baru
        ahp_result = AHPResults(
            event_id=event_id,
            lambda_max=float(lambda_max),
            ci=float(ci),
            cr=float(cr),
            is_consistent=is_consistent,
            eigenvector_json=json.dumps(eigenvector.tolist()),
            weights_json=json.dumps(weights),
            pairwise_matrix_json=json.dumps(pairwise_matrix.tolist())
        )
        db.session.add(ahp_result)
        
        # Update bobot di tabel Criteria
        for i, criteria in enumerate(criterias):
            criteria.bobot = float(weights[criteria_names[i]])
        
        db.session.commit()
        
        results = {
            'lambda_max': float(lambda_max),
            'ci': float(ci),
            'cr': float(cr),
            'is_consistent': is_consistent,
            'eigenvector': eigenvector.tolist(),
            'weights': weights
        }
        
        return True, "Perhitungan AHP berhasil.", results
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error menyimpan hasil AHP: {str(e)}", {}


def calculate_fuzzy_ahp_weights(event_id: int, pairwise_matrix: Optional[np.ndarray] = None) -> Tuple[bool, str, Dict]:
    """
    Menghitung bobot kriteria menggunakan Fuzzy AHP lengkap sesuai PDF
    
    Args:
        event_id: ID kegiatan
        pairwise_matrix: Matriks perbandingan berpasangan (opsional)
    
    Returns:
        Tuple (success, message, results_dict)
    """
    # Ambil kriteria
    criterias = Criteria.query.filter_by(event_id=event_id).order_by(Criteria.id_kriteria).all()
    if not criterias:
        return False, "Tidak ada kriteria untuk kegiatan ini.", {}
    
    criteria_names = [c.nama_kriteria for c in criterias]
    criteria_ids = [c.id_kriteria for c in criterias]
    n = len(criterias)
    
    # Jika matriks tidak diberikan, ambil dari database
    if pairwise_matrix is None:
        pairwise_matrix = get_pairwise_matrix_from_db(event_id, criteria_ids)
        if pairwise_matrix is None:
            return False, "Matriks perbandingan berpasangan belum diinput.", {}
    
    # Inisialisasi Fuzzy AHP Calculator
    fuzzy_ahp = FuzzyAHPCalculator(criteria_names)
    fuzzy_ahp.set_fuzzy_pairwise_matrix(pairwise_matrix)
    
    # Hitung Fuzzy Synthetic Extent
    synthetic_extents = fuzzy_ahp.calculate_fuzzy_synthetic_extent()
    
    # Hitung bobot fuzzy
    fuzzy_weights = fuzzy_ahp.calculate_fuzzy_weights()
    
    # Simpan hasil dan update bobot
    try:
        # Update bobot di tabel Criteria (gunakan normalized weights)
        for criteria in criterias:
            if criteria.nama_kriteria in fuzzy_weights:
                criteria.bobot = float(fuzzy_weights[criteria.nama_kriteria])
        
        db.session.commit()
        
        results = {
            'fuzzy_synthetic_extent': synthetic_extents,
            'fuzzy_weights': fuzzy_ahp.fuzzy_weights,
            'normalized_weights': fuzzy_weights
        }
        
        return True, "Perhitungan Fuzzy AHP berhasil.", results
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error menyimpan hasil Fuzzy AHP: {str(e)}", {}


def get_pairwise_matrix_from_db(event_id: int, criteria_ids: List[int]) -> Optional[np.ndarray]:
    """
    Ambil matriks perbandingan berpasangan dari database
    
    Args:
        event_id: ID kegiatan
        criteria_ids: List ID kriteria (dalam urutan)
    
    Returns:
        Matriks numpy atau None jika tidak ada
    """
    comparisons = PairwiseComparison.query.filter_by(event_id=event_id).all()
    if not comparisons:
        return None
    
    n = len(criteria_ids)
    matrix = np.ones((n, n))
    
    # Buat mapping ID ke index
    id_to_index = {criteria_ids[i]: i for i in range(n)}
    
    # Isi matriks dari database
    for comp in comparisons:
        i_idx = id_to_index.get(comp.criteria_i_id)
        j_idx = id_to_index.get(comp.criteria_j_id)
        
        if i_idx is not None and j_idx is not None:
            matrix[i_idx, j_idx] = comp.comparison_value
            # Set nilai kebalikan
            if comp.comparison_value > 0:
                matrix[j_idx, i_idx] = 1.0 / comp.comparison_value
    
    return matrix


def save_pairwise_matrix(event_id: int, criteria_ids: List[int], matrix: np.ndarray) -> Tuple[bool, str]:
    """
    Simpan matriks perbandingan berpasangan ke database
    
    Args:
        event_id: ID kegiatan
        criteria_ids: List ID kriteria
        matrix: Matriks perbandingan n x n
    
    Returns:
        Tuple (success, message)
    """
    try:
        # Hapus data lama
        PairwiseComparison.query.filter_by(event_id=event_id).delete()
        
        n = len(criteria_ids)
        if matrix.shape != (n, n):
            return False, f"Ukuran matriks tidak sesuai. Harus {n}x{n}"
        
        # Simpan matriks ke database
        for i in range(n):
            for j in range(n):
                if i != j:  # Skip diagonal (selalu 1)
                    value = matrix[i, j]
                    
                    # Konversi ke TFN
                    if value >= 1:
                        tfn = TFN_SCALE.get(max(1, min(9, round(value))), (1, 1, 1))
                    else:
                        reciprocal_value = 1.0 / value
                        tfn = get_tfn_reciprocal(TFN_SCALE.get(max(1, min(9, round(reciprocal_value))), (1, 1, 1)))
                    
                    comp = PairwiseComparison(
                        event_id=event_id,
                        criteria_i_id=criteria_ids[i],
                        criteria_j_id=criteria_ids[j],
                        comparison_value=float(value),
                        fuzzy_l=float(tfn[0]),
                        fuzzy_m=float(tfn[1]),
                        fuzzy_u=float(tfn[2])
                    )
                    db.session.add(comp)
        
        db.session.commit()
        return True, "Matriks perbandingan berpasangan berhasil disimpan."
        
    except Exception as e:
        db.session.rollback()
        return False, f"Error menyimpan matriks: {str(e)}"


def fuzzify_score(score: float, scale_type: str = 'auto') -> Tuple[float, float, float]:
    """
    Fuzzifikasi nilai penilaian peserta ke TFN
    (Ini untuk nilai penilaian, bukan matriks perbandingan)
    
    Args:
        score: Nilai tegas
        scale_type: 'likert' untuk 1-5, 'numeric' untuk 0-100, 'auto' untuk deteksi otomatis
    
    Returns:
        Tuple (l, m, u) untuk TFN
    """
    if scale_type == 'auto':
        scale_type = 'likert' if score <= 5 else 'numeric'
    
    if scale_type == 'likert':
        # Skala Likert 1-5
        if score <= 1:
            return (1, 1, 2)
        elif score <= 2:
            return (1, 2, 3)
        elif score <= 3:
            return (2, 3, 4)
        elif score <= 4:
            return (3, 4, 5)
        else:
            return (4, 5, 5)
    else:
        # Skala 0-100
        l = max(0, score - 5)
        m = score
        u = min(100, score + 5)
        return (l, m, u)


def calculate_spk(event_id: int, use_fuzzy_ahp: bool = True) -> Tuple[bool, str]:
    """
    Menghitung SPK menggunakan metode Fuzzy AHP lengkap sesuai PDF.
    
    Langkah-langkah:
    1. Hitung bobot kriteria menggunakan Fuzzy AHP (jika belum)
    2. Ambil data penilaian peserta
    3. Fuzzifikasi nilai penilaian peserta
    4. Agregasi nilai fuzzy dengan bobot fuzzy dari AHP
    5. Defuzzifikasi untuk mendapatkan nilai akhir
    6. Ranking peserta
    7. Simpan hasil ke database
    
    Args:
        event_id: ID kegiatan
        use_fuzzy_ahp: Gunakan Fuzzy AHP untuk bobot (True) atau AHP biasa (False)
    
    Returns:
        Tuple (success, message)
    """
    # 1. Ambil Kriteria
    criterias = Criteria.query.filter_by(event_id=event_id).order_by(Criteria.id_kriteria).all()
    if not criterias:
        return False, "Tidak ada kriteria untuk kegiatan ini."
    
    # 2. Hitung atau ambil bobot kriteria menggunakan Fuzzy AHP
    criteria_ids = [c.id_kriteria for c in criterias]
    pairwise_matrix = get_pairwise_matrix_from_db(event_id, criteria_ids)
    
    if pairwise_matrix is not None:
        # Gunakan Fuzzy AHP jika diminta
        if use_fuzzy_ahp:
            success, msg, _ = calculate_fuzzy_ahp_weights(event_id, pairwise_matrix)
        else:
            success, msg, _ = calculate_ahp_weights(event_id, pairwise_matrix)
        
        if not success:
            return False, f"Error menghitung bobot: {msg}"
    
    # Ambil bobot yang sudah ada (dari database)
    total_bobot = sum(c.bobot for c in criterias)
    if total_bobot == 0:
        return False, "Bobot kriteria belum dihitung. Silakan input matriks perbandingan berpasangan terlebih dahulu."
    
    criteria_weights = {c.id_kriteria: (c.bobot / total_bobot if total_bobot > 0 else 0) for c in criterias}
    
    # 3. Ambil Peserta
    event = Event.query.get(event_id)
    if not event:
        return False, "Kegiatan tidak ditemukan."
    
    participants = event.registered_participants.all()
    if not participants:
        participants = Participants.query.filter_by(kegiatan_id=event_id).all()
    
    if not participants:
        return False, "Tidak ada peserta untuk kegiatan ini."
    
    # Mapping email peserta ke user ID
    participant_emails = [p.email for p in participants]
    users = Users.query.filter(Users.email.in_(participant_emails)).all()
    user_map = {u.email: u.id for u in users}
    participant_ids = [user_map[p.email] for p in participants if p.email in user_map]
    
    if not participant_ids:
        return False, "Data user peserta tidak ditemukan."
    
    # 4. Proses Penilaian (Fuzzifikasi & Agregasi)
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
                
                # Fuzzifikasi nilai penilaian
                l, m, u = fuzzify_score(score)
                
                # Agregasi dengan bobot
                fuzzy_total_l += l * weight
                fuzzy_total_m += m * weight
                fuzzy_total_u += u * weight
        if has_score:
            # Defuzzifikasi menggunakan Center of Area
            defuzzified_score = (fuzzy_total_l + fuzzy_total_m + fuzzy_total_u) / 3
            
            final_scores.append({
                'user_id': uid,
                'score': defuzzified_score
            })
    
    # 5. Ranking
    final_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # 6. Simpan ke Database
    try:
        # Hapus hasil lama
        HasilSeleksi.query.filter_by(event_id=event_id).delete()
        
        if final_scores:
            user_ids = [x['user_id'] for x in final_scores]
            HasilSeleksi.query.filter(
                HasilSeleksi.id_users.in_(user_ids), 
                HasilSeleksi.event_id == None
            ).delete(synchronize_session=False)
        
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
