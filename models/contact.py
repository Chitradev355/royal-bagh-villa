from datetime import datetime, timezone
from models import db


class Enquiry(db.Model):
    __tablename__ = "enquiries"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), default="")
    subject = db.Column(db.String(200), default="")
    message = db.Column(db.Text, default="")
    enquiry_type = db.Column(db.String(50), default="general")  # general, cafe, restaurant, banquet, lawn, stay
    status = db.Column(db.String(20), default="new")  # new, read, responded, closed
    admin_notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "phone": self.phone,
            "email": self.email,
            "subject": self.subject,
            "message": self.message,
            "enquiry_type": self.enquiry_type,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }

    def __repr__(self):
        return f"<Enquiry {self.name}>"


class BusinessSetting(db.Model):
    __tablename__ = "business_settings"

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, default="")
    label = db.Column(db.String(200), default="")  # Human-readable label for admin UI

    @staticmethod
    def get(key, default=""):
        setting = BusinessSetting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value, label=""):
        setting = BusinessSetting.query.filter_by(key=key).first()
        if setting:
            setting.value = value
        else:
            setting = BusinessSetting(key=key, value=value, label=label)
            db.session.add(setting)
        db.session.commit()

    def __repr__(self):
        return f"<BusinessSetting {self.key}>"
