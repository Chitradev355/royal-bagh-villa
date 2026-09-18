import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Production SECRET_KEY from environment, with stable fallback for existing sessions
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.environ.get("FLASK_SECRET_KEY")
    if not SECRET_KEY:
        secret_file = os.path.join(BASE_DIR, "instance", ".secret_key")
        if os.path.exists(secret_file):
            try:
                with open(secret_file, "r", encoding="utf-8") as f:
                    SECRET_KEY = f.read().strip()
            except Exception:
                SECRET_KEY = "rbv-secret-key-change-in-production-2026"
        else:
            SECRET_KEY = "rbv-secret-key-change-in-production-2026"

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'royal_bagh.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 64 * 1024 * 1024))  # 64 MB max upload for media
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
    MEDIA_UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "media")

    # Session & Cookie security over HTTPS / Render
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("RENDER") == "true" or os.environ.get("SESSION_COOKIE_SECURE", "false").lower() in ("true", "1")
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    REMEMBER_COOKIE_SAMESITE = "Lax"

    # Flask-WTF CSRF Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_CHECK_DEFAULT = True
    WTF_CSRF_TIME_LIMIT = 3600 * 12  # 12-hour CSRF token validity

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
