import random
import string
from datetime import datetime, timezone
from models import db


def generate_banquet_id():
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=6))
    return f"RBV-BNQ-{code}"


class BanquetBooking(db.Model):
    __tablename__ = "banquet_bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True, nullable=False, default=generate_banquet_id)
    event_type = db.Column(db.String(50), nullable=False)
    event_date = db.Column(db.Date, nullable=False)
    event_time = db.Column(db.String(50), default="")
    guest_count = db.Column(db.Integer, nullable=False)
    veg_nonveg = db.Column(db.String(20), default="veg")  # veg, nonveg, both
    food_package = db.Column(db.String(100), default="")
    decoration_requirements = db.Column(db.Text, default="")
    additional_requirements = db.Column(db.Text, default="")
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), default="")
    estimated_quote = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="enquiry_received")
    admin_notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    STATUS_FLOW = ["enquiry_received", "under_review", "quote_sent", "confirmed", "completed"]

    STATUS_LABELS = {
        "enquiry_received": "Enquiry Received",
        "under_review": "Under Review",
        "quote_sent": "Quote Sent",
        "confirmed": "Confirmed",
        "completed": "Completed",
    }

    def get_status_index(self):
        if self.status in self.STATUS_FLOW:
            return self.STATUS_FLOW.index(self.status)
        return -1

    def get_status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status.replace("_", " ").title())

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "event_type": self.event_type,
            "event_date": self.event_date.isoformat() if self.event_date else "",
            "event_time": self.event_time,
            "guest_count": self.guest_count,
            "veg_nonveg": self.veg_nonveg,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "status": self.status,
            "status_label": self.get_status_label(),
            "estimated_quote": self.estimated_quote,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }

    def __repr__(self):
        return f"<BanquetBooking {self.booking_id}>"
