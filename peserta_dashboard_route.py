# Peserta Dashboard Route
from datetime import datetime
from flask import app, render_template
from flask_login import current_user, login_required
from app.models import Criteria, Event, HasilSeleksi, Participants, Penilaian, ParticipantKegiatan


@app.route('/peserta/dashboard')
@login_required
def peserta_dashboard():
    """Dashboard for participants showing scores and rankings for all registered activities"""
    
    # Get current user's participant record
    participant = Participants.query.filter_by(email=current_user.email).first()
    
    # Get all registered activities for this participant
    registered_activities = []
    if participant:
        registered_activities = Event.query.join(
            ParticipantKegiatan,
            Event.id_kegiatan == ParticipantKegiatan.c.kegiatan_id
        ).filter(
            ParticipantKegiatan.c.participant_id == participant.id
        ).all()
    
    # Calculate scores for each activity
    activity_scores = []
    for event in registered_activities:
        # Get all criteria for this event
        criteria_list = Criteria.query.filter_by(event_id=event.id_kegiatan).all()
        
        # Calculate total score
        total_score = 0
        has_scores = False
        
        for criterion in criteria_list:
            penilaian = Penilaian.query.filter_by(
                id_users=current_user.id,
                id_kriteria=criterion.id_kriteria
            ).first()
            
            if penilaian:
                # Calculate weighted score
                weighted_score = penilaian.nilai * (criterion.bobot / 100)
                total_score += weighted_score
                has_scores = True
        
        # Get ranking from HasilSeleksi table
        hasil = HasilSeleksi.query.filter_by(
            id_users=current_user.id,
            id_kegiatan=event.id_kegiatan
        ).first()
        
        activity_scores.append({
            'event': event,
            'final_score': round(total_score, 2) if has_scores else None,
            'ranking': hasil.ranking if hasil else None,
            'has_scores': has_scores
        })
    
    # Check if any selection period has ended
    is_selection_ended = any(
        event.periode_seleksi_selesai and event.periode_seleksi_selesai < datetime.now()
        for event in registered_activities
    )
    
    # Determine status
    status_seleksi = 'Terdaftar' if registered_activities else 'Belum ada status'
    
    return render_template(
        'peserta/dashboard.html',
        biodata=participant,
        registered_activities=registered_activities,
        activity_scores=activity_scores,
        is_selection_ended=is_selection_ended,
        status_seleksi=status_seleksi
    )
