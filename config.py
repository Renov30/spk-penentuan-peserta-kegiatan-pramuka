# config.py
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-12345"
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:rahasia@localhost:3306/fuzzy_ahp_skripsi_2"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
