# app/models.py
from app import db
from sqlalchemy.dialects.mysql import ENUM
from flask_login import UserMixin
from datetime import datetime
from flask_login import current_user
from slugify import slugify


# Access to table users
class Users(db.Model, UserMixin):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=True)
    nama_lengkap = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    jenis_kelamin = db.Column(
        ENUM("laki-laki", "perempuan", name="jenis_kelamin"),
        nullable=False,
        default="laki-laki",
    )
    usia = db.Column(db.String(255), nullable=False, default="0")
    foto = db.Column(db.String(255), nullable=False, default="img/default-user.png")
    nomor_hp = db.Column(db.String(255), nullable=False, default="")
    level = db.Column(
        ENUM("admin", "penilai", "peserta", name="user_level"), nullable=False
    )
    reset_token = db.Column(db.String(255), nullable=False, default="")
    token_exp = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )
    login_method = db.Column(db.String(100), nullable=False, default="manual")
    sidebar_state = db.Column(db.String(10), nullable=False, default="expanded")
    status = db.Column(
        ENUM("aktif", "non-aktif", name="user_status"),
        nullable=False,
        default="aktif",
        server_default="aktif",
    )
    news = db.relationship("News", backref="author", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nama_lengkap": self.nama_lengkap,
            "email": self.email,
            "username": self.username,
            "jenis_kelamin": self.jenis_kelamin or "",
            "usia": self.usia or 0,
            "nomor_hp": self.nomor_hp or "",
            "level": self.level,
            "status": self.status,
            "foto": self.foto,
        }


# Access to table tb_event_evaluator
class EventEvaluator(db.Model):
    __tablename__ = "tb_event_evaluator"
    event_id = db.Column(
        db.Integer, db.ForeignKey("tb_kegiatan.id_kegiatan"), primary_key=True
    )
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), primary_key=True)

    # Relationship
    kegiatan = db.relationship(
        "Event", backref=db.backref("assigned_evaluators", lazy=True)
    )
    evaluator = db.relationship(
        "Users", backref=db.backref("events_assigned", lazy=True)
    )


# Access to table tb_participant_kegiatan
tb_participant_kegiatan = db.Table(
    "tb_participant_kegiatan",
    db.Column(
        "participant_id", db.Integer, db.ForeignKey("participants.id"), primary_key=True
    ),
    db.Column(
        "kegiatan_id",
        db.Integer,
        db.ForeignKey("tb_kegiatan.id_kegiatan"),
        primary_key=True,
    ),
)


# Access to table tb_kegiatan
class Event(db.Model):
    __tablename__ = "tb_kegiatan"
    id_kegiatan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    jenis_kegiatan = db.Column(
        db.Enum("Siaga", "Penggalang", "Penegak", "Pandega", "Penegak dan Pandega"),
        nullable=False,
    )
    nama_kegiatan = db.Column(db.String(255), nullable=False)
    waktu_pelaksanaan_dimulai = db.Column(db.Date, nullable=False)
    waktu_pelaksanaan_selesai = db.Column(db.Date, nullable=False)
    tempat_pelaksanaan = db.Column(db.String(100), nullable=False)
    skala_kegiatan = db.Column(
        db.Enum("Ranting", "Cabang", "Daerah", "Nasional", "Internasional"),
        nullable=False,
    )
    kwartir_penyelenggara = db.Column(db.String(255), nullable=False)
    mulai = db.Column(db.Date, nullable=False)
    selesai = db.Column(db.Date, nullable=False)
    tanggal_tes = db.Column(db.String(255), nullable=True)
    tempat_tes = db.Column(db.String(100), nullable=True)
    kuota = db.relationship(
        "Kuota", backref="event", lazy=True, cascade="all, delete-orphan"
    )
    kriteria = db.relationship(
        "Criteria", backref="event", lazy=True, cascade="all, delete-orphan"
    )

    # Relationship with Evaluators
    evaluators = db.relationship(
        "Users",
        secondary="tb_event_evaluator",
        lazy="subquery",
        backref=db.backref("assigned_events", lazy=True),
    )


# Access to table tb_kuota
class Kuota(db.Model):
    __tablename__ = "tb_kuota"
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("tb_kegiatan.id_kegiatan"),
        nullable=False,
        unique=True,
    )
    putra = db.Column(db.Integer, default=0)
    putri = db.Column(db.Integer, default=0)


# Access to table tb_evaluator_criteria
EvaluatorCriteria = db.Table(
    "tb_evaluator_criteria",
    db.Column(
        "criteria_id",
        db.Integer,
        db.ForeignKey("tb_kriteria.id_kriteria"),
        primary_key=True,
    ),
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
)


# Access to table tb_kriteria
class Criteria(db.Model):
    __tablename__ = "tb_kriteria"
    id_kriteria = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(
        db.Integer, db.ForeignKey("tb_kegiatan.id_kegiatan"), nullable=False
    )
    nama_kriteria = db.Column(db.String(255), nullable=False)
    aspek = db.Column(db.String(255), nullable=True)
    bobot = db.Column(db.Float, nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    jenis_kriteria = db.Column(db.String(255), nullable=False)
    jumlah_soal = db.Column(db.Integer, nullable=True)

    # Relationship with Evaluators
    evaluators = db.relationship(
        "Users",
        secondary=EvaluatorCriteria,
        lazy="subquery",
        backref=db.backref("assigned_criteria", lazy=True),
    )


# Access to table tb_pairwise_comparison (untuk menyimpan matriks perbandingan AHP)
class PairwiseComparison(db.Model):
    __tablename__ = "tb_pairwise_comparison"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(
        db.Integer, db.ForeignKey("tb_kegiatan.id_kegiatan"), nullable=False
    )
    criteria_i_id = db.Column(
        db.Integer, db.ForeignKey("tb_kriteria.id_kriteria"), nullable=False
    )
    criteria_j_id = db.Column(
        db.Integer, db.ForeignKey("tb_kriteria.id_kriteria"), nullable=False
    )
    comparison_value = db.Column(db.Float, nullable=False)  # Nilai perbandingan 1-9
    fuzzy_l = db.Column(db.Float, nullable=True)  # Lower bound TFN
    fuzzy_m = db.Column(db.Float, nullable=True)  # Middle bound TFN
    fuzzy_u = db.Column(db.Float, nullable=True)  # Upper bound TFN
    created_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )

    # Relationship
    event = db.relationship("Event", backref="pairwise_comparisons")
    criteria_i = db.relationship("Criteria", foreign_keys=[criteria_i_id])
    criteria_j = db.relationship("Criteria", foreign_keys=[criteria_j_id])


# Access to table tb_ahp_results (untuk menyimpan hasil perhitungan AHP)
class AHPResults(db.Model):
    __tablename__ = "tb_ahp_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(
        db.Integer,
        db.ForeignKey("tb_kegiatan.id_kegiatan"),
        nullable=False,
        unique=True,
    )
    lambda_max = db.Column(db.Float, nullable=True)
    ci = db.Column(db.Float, nullable=True)  # Consistency Index
    cr = db.Column(db.Float, nullable=True)  # Consistency Ratio
    is_consistent = db.Column(db.Boolean, default=False)
    eigenvector_json = db.Column(db.Text, nullable=True)  # JSON array eigenvector
    weights_json = db.Column(db.Text, nullable=True)  # JSON object weights
    pairwise_matrix_json = db.Column(db.Text, nullable=True)  # JSON matrix
    calculated_at = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )

    # Relationship
    event = db.relationship("Event", backref="ahp_results")


# Access to table notifications
class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_read = db.Column(db.Boolean, default=False)
    message = db.Column(db.String(255))


# Access to table participants
class Participants(db.Model):
    __tablename__ = "participants"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nama_lengkap = db.Column(db.String(100), nullable=True)
    tanggal_lahir = db.Column(db.Date, nullable=False)
    alamat_tinggal = db.Column(db.String(255), nullable=False)
    golongan = db.Column(
        db.Enum("siaga", "penggalang", "penegak", "pandega", name="golongan_enum"),
        nullable=False,
    )
    tingkatan = db.Column(
        db.Enum(
            "siaga mula",
            "siaga tata",
            "siaga bantu",
            "siaga garuda",
            "penggalang ramu",
            "penggalang rakit",
            "penggalang terap",
            "penggalang garuda",
            "penegak bantara",
            "penegak laksana",
            "penegak garuda",
            "pandega",
            "pandega garuda",
            name="tingkatan_enum",
        ),
        nullable=False,
    )
    asal_gudep = db.Column(db.String(100), nullable=False)
    asal_kwarran = db.Column(db.String(100), nullable=False)
    asal_kwarcab = db.Column(db.String(100), nullable=False)
    asal_kwarda = db.Column(db.String(100), nullable=False)
    usia = db.Column(db.Integer, nullable=False)
    jenis_kelamin = db.Column(
        db.Enum("laki-laki", "perempuan", name="jenis_kelamin_enum"), nullable=False
    )
    email = db.Column(db.String(255), nullable=False)
    nomor_hp = db.Column(db.String(100), nullable=False)
    foto = db.Column(db.String(100), nullable=False)
    kegiatan_id = db.Column(
        db.Integer, db.ForeignKey("tb_kegiatan.id_kegiatan"), nullable=True
    )
    level = db.Column(
        db.String(50), nullable=False, default="peserta", server_default="peserta"
    )
    kegiatan = db.relationship("Event", backref="peserta_list", lazy=True)
    registered_activities = db.relationship(
        "Event",
        secondary=tb_participant_kegiatan,
        backref=db.backref("registered_participants", lazy="dynamic"),
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Participants {self.nama_lengkap}>"


# Access to table himpunan_kriteria
class HimpunanKriteria(db.Model):
    __tablename__ = "himpunan_kriteria"
    id_himpunan = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_kriteria = db.Column(
        db.Integer, db.ForeignKey("tb_kriteria.id_kriteria"), nullable=False
    )
    nama_himpunan = db.Column(db.String(255), nullable=False)
    nilai_himpunan = db.Column(db.Float, nullable=False)


# Access to table tb_penilaian
class Penilaian(db.Model):
    __tablename__ = "tb_penilaian"
    id_penilaian = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_users = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )  # Peserta
    evaluator_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=True
    )  # Penilai
    id_kriteria = db.Column(
        db.Integer, db.ForeignKey("tb_kriteria.id_kriteria"), nullable=False
    )
    nilai = db.Column(db.Float, nullable=False)


# Access to table tb_hasil_seleksi
class HasilSeleksi(db.Model):
    __tablename__ = "tb_hasil_seleksi"
    id_hasil = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_users = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skor_akhir = db.Column(db.Float, nullable=False)
    ranking = db.Column(db.Integer, nullable=False)
    event_id = db.Column(
        db.Integer, db.ForeignKey("tb_kegiatan.id_kegiatan"), nullable=True
    )

    event = db.relationship("Event", backref="hasil_seleksi")


# Access to table tb_log_aktivitas
class LogAktivitas(db.Model):
    __tablename__ = "tb_log_aktivitas"
    id_log = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    aktivitas = db.Column(db.Text, nullable=False)
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, server_default=db.func.current_timestamp())

    user = db.relationship("Users", backref="logs")


# Access to table tb_informasi
class Informasi(db.Model):
    __tablename__ = "tb_informasi"
    id_informasi = db.Column(db.Integer, primary_key=True, autoincrement=True)
    judul = db.Column(db.String(255), nullable=False)
    isi = db.Column(db.Text, nullable=False)
    tanggal = db.Column(db.Date, server_default=db.func.current_date())


# Access to table tb_arsip_seleksi (untuk menyimpan arsip laporan seleksi)
class ArsipSeleksi(db.Model):
    __tablename__ = "tb_arsip_seleksi"
    id_arsip = db.Column(db.Integer, primary_key=True, autoincrement=True)
    event_id = db.Column(
        db.Integer, db.ForeignKey("tb_kegiatan.id_kegiatan"), nullable=False
    )
    nama_arsip = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(500), nullable=True)
    file_type = db.Column(db.String(50), nullable=False, default="pdf")
    tanggal_arsip = db.Column(
        db.DateTime, default=db.func.current_timestamp(), nullable=False
    )
    dibuat_oleh = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    status = db.Column(db.String(20), nullable=False, default="aktif")

    # Relationship
    event = db.relationship("Event", backref="arsip_seleksi")
    pembuat = db.relationship(
        "Users",
        foreign_keys=[dibuat_oleh],
        backref=db.backref("arsip_yang_dibuat", lazy="dynamic"),
        lazy="joined",
    )


# Access to table settings
class Settings(db.Model):
    __tablename__ = "settings"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(255), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    category = db.Column(
        db.String(100), nullable=False, default="general"
    )  # email, sms, app, logo, language
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "key": self.key,
            "value": self.value,
            "category": self.category,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


# Access to table tb_news
class News(db.Model):
    __tablename__ = "tb_news"
    id_news = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    excerpt = db.Column(db.Text)
    thumbnail = db.Column(
        db.String(255), nullable=False, default="images/default-news.jpg"
    )
    status = db.Column(
        ENUM("draft", "published", "archived", name="news_status"), default="draft"
    )
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
    published_at = db.Column(db.DateTime)


# Access to table comment_like
class CommentLike(db.Model):
    __tablename__ = "comment_like"

    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(
        db.Integer, db.ForeignKey("news_comment.id", ondelete="CASCADE"), nullable=False
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔐 UNIQUE: 1 USER HANYA BISA LIKE 1X
    __table_args__ = (
        db.UniqueConstraint("comment_id", "user_id", name="uq_comment_user_like"),
    )

    def __repr__(self):
        return f"<CommentLike comment_id={self.comment_id} user_id={self.user_id}>"


# Access to table news_comment
class Comment(db.Model):
    __tablename__ = "news_comment"  # nama tabel di database

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    news_id = db.Column(db.Integer, db.ForeignKey("tb_news.id_news"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("news_comment.id"), nullable=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    is_deleted = db.Column(db.Boolean, default=False, nullable=False)
    is_approved = db.Column(db.Boolean, default=True, nullable=False)
    likes = db.Column(db.Integer, default=0)

    # Relationship opsional
    news = db.relationship("News", backref=db.backref("news_comment", lazy="dynamic"))
    user = db.relationship("Users", backref=db.backref("news_comment", lazy="dynamic"))
    parent = db.relationship("Comment", remote_side=[id], backref="replies")
    likes_rel = db.relationship(
        "CommentLike", backref="comment", cascade="all, delete-orphan", lazy="dynamic"
    )

    def to_dict(self, depth=1):
        data = {
            "id": self.id,
            "parent_id": self.parent_id,
            "content": self.content,
            "user": {
                "id": self.user.id,
                "nama_lengkap": self.user.nama_lengkap,
                "foto": self.user.foto if self.user and self.user.foto else None,
            },
            "created_at": self.created_at.strftime("%d %B %Y"),
            "likes": self.likes,
            "reply_count": Comment.query.filter_by(
                parent_id=self.id, is_deleted=False, is_approved=True
            ).count(),
            "is_owner": (
                current_user.is_authenticated and self.user_id == current_user.id
            ),
        }

        # 🔁 OPSIONAL (REKOMENDASI): STATUS LIKE USER
        if current_user.is_authenticated:
            data["is_liked"] = (
                self.likes_rel.filter_by(user_id=current_user.id).first() is not None
            )
        else:
            data["is_liked"] = False

        # Batasi kedalaman reply (keamanan & performa)
        if depth > 0:
            data["replies"] = [
                reply.to_dict(depth - 1)
                for reply in self.replies
                if not reply.is_deleted and reply.is_approved
            ]
        return data

    def __repr__(self):
        return f"<Comment id={self.id} news_id={self.news_id} user_id={self.user_id}>"
