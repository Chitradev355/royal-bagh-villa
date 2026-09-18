import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "rbv-secret-key-change-in-production-2026")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'royal_bagh.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")

    # Business defaults (editable from admin)
    BUSINESS_NAME = "Royal Bagh Villa"
    BUSINESS_TAGLINE = "Where Every Celebration Becomes a Memory"
    BUSINESS_PHONE = "9762278230"
    BUSINESS_WHATSAPP = "919762278230"
    BUSINESS_EMAIL = "info@royalbaghvilla.com"
    BUSINESS_ADDRESS = "Royal Bagh Villa, Dehradun, Uttarakhand"
    BUSINESS_MAP_URL = "https://maps.google.com/?q=Royal+Bagh+Villa+Dehradun"
    BUSINESS_INSTAGRAM = "https://instagram.com/royalbaghvilla"

    # Razorpay (architecture ready)
    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_ENABLED = False
