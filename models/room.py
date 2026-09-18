import json
import random
import string
from datetime import datetime, timezone
from models import db


def generate_room_booking_id():
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=6))
    return f"RBV-ROM-{code}"


class Room(db.Model):
    __tablename__ = "rooms"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    price_per_night = db.Column(db.Float, nullable=False)
    max_guests = db.Column(db.Integer, default=2)
    amenities_json = db.Column(db.Text, default="[]")
    images_json = db.Column(db.Text, default="[]")
    is_available = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    bookings = db.relationship("RoomBooking", backref="room", lazy="dynamic")

    @property
    def amenities(self):
        try:
            return json.loads(self.amenities_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @amenities.setter
    def amenities(self, value):
        self.amenities_json = json.dumps(value)

    @property
    def images(self):
        try:
            return json.loads(self.images_json)
        except (json.JSONDecodeError, TypeError):
            return []

    @images.setter
    def images(self, value):
        self.images_json = json.dumps(value)

    def amenities_list(self):
        return self.amenities

    def images_list(self):
        return self.images

    def is_available_for_dates(self, check_in, check_out):
        """Check if room is available for given date range."""
        if not self.is_available:
            return False
        conflicting = RoomBooking.query.filter(
            RoomBooking.room_id == self.id,
            RoomBooking.status.in_(["confirmed", "checked_in"]),
            RoomBooking.check_in < check_out,
            RoomBooking.check_out > check_in,
        ).first()
        return conflicting is None

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "price_per_night": self.price_per_night,
            "max_guests": self.max_guests,
            "amenities": self.amenities,
            "images": self.images,
            "is_available": self.is_available,
        }

    def __repr__(self):
        return f"<Room {self.name}>"


class RoomBooking(db.Model):
    __tablename__ = "room_bookings"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.String(20), unique=True, nullable=False, default=generate_room_booking_id)
    room_id = db.Column(db.Integer, db.ForeignKey("rooms.id"), nullable=False)
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    guest_count = db.Column(db.Integer, default=1)
    customer_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), default="")
    total_amount = db.Column(db.Float, default=0)
    payment_mode = db.Column(db.String(20), default="pay_at_venue")
    payment_status = db.Column(db.String(20), default="pending")
    status = db.Column(db.String(20), default="pending")  # pending, confirmed, checked_in, checked_out, cancelled
    special_requests = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    STATUS_FLOW = ["pending", "confirmed", "checked_in", "checked_out"]

    def get_status_index(self):
        if self.status in self.STATUS_FLOW:
            return self.STATUS_FLOW.index(self.status)
        return -1

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "room_name": self.room.name if self.room else "",
            "check_in": self.check_in.isoformat() if self.check_in else "",
            "check_out": self.check_out.isoformat() if self.check_out else "",
            "guest_count": self.guest_count,
            "customer_name": self.customer_name,
            "phone": self.phone,
            "status": self.status,
            "total_amount": self.total_amount,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }

    def __repr__(self):
        return f"<RoomBooking {self.booking_id}>"
