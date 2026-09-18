import random
import string
from datetime import datetime, timezone
from models import db


def generate_order_id():
    chars = string.ascii_uppercase + string.digits
    code = "".join(random.choices(chars, k=6))
    return f"RBV-ORD-{code}"


class FoodOrder(db.Model):
    __tablename__ = "food_orders"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(20), unique=True, nullable=False, default=generate_order_id)
    customer_name = db.Column(db.String(120), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    customer_email = db.Column(db.String(120), default="")
    order_type = db.Column(db.String(20), nullable=False)  # dine_in, takeaway, room_delivery
    room_number = db.Column(db.String(20), default="")
    table_number = db.Column(db.String(20), default="")
    status = db.Column(db.String(20), default="placed")  # placed, confirmed, preparing, ready, completed, cancelled
    total_amount = db.Column(db.Float, default=0)
    payment_mode = db.Column(db.String(20), default="pay_at_venue")  # online, advance, pay_at_venue
    payment_status = db.Column(db.String(20), default="pending")  # pending, partial, paid, refunded
    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    items = db.relationship("OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan")

    STATUS_FLOW = ["placed", "confirmed", "preparing", "ready", "completed"]

    def get_status_index(self):
        if self.status in self.STATUS_FLOW:
            return self.STATUS_FLOW.index(self.status)
        return -1

    def to_dict(self):
        return {
            "id": self.id,
            "order_id": self.order_id,
            "customer_name": self.customer_name,
            "customer_phone": self.customer_phone,
            "order_type": self.order_type,
            "status": self.status,
            "total_amount": self.total_amount,
            "payment_mode": self.payment_mode,
            "payment_status": self.payment_status,
            "items": [item.to_dict() for item in self.items],
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }

    def __repr__(self):
        return f"<FoodOrder {self.order_id}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("food_orders.id"), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    special_instructions = db.Column(db.Text, default="")

    menu_item = db.relationship("MenuItem")

    def to_dict(self):
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "item_name": self.menu_item.name if self.menu_item else "",
            "quantity": self.quantity,
            "unit_price": self.unit_price,
            "subtotal": self.subtotal,
            "special_instructions": self.special_instructions,
        }
