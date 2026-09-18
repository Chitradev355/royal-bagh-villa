from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default="admin")  # admin, manager, staff
    is_active_user = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash or not password:
            return False
        # 1. Primary check using Werkzeug check_password_hash
        try:
            if check_password_hash(self.password_hash, password):
                return True
        except Exception:
            pass

        # 2. Legacy bcrypt hash compatibility ($2a$, $2b$, $2y$)
        if self.password_hash.startswith(('$2a$', '$2b$', '$2y$')):
            try:
                import bcrypt
                if bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8")):
                    # Upgrade to standard Werkzeug hash upon successful verification
                    self.set_password(password)
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    return True
            except Exception:
                return False

        return False

    @property
    def is_active(self):
        return self.is_active_user

    def __repr__(self):
        return f"<Admin {self.username}>"
