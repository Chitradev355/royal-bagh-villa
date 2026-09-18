from datetime import datetime, timezone
from models import db


class MenuCategory(db.Model):
    __tablename__ = "menu_categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    section = db.Column(db.String(50), nullable=False)  # breakfast, light, main, sides, sweet, drinks, cafe
    display_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    items = db.relationship("MenuItem", backref="category", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MenuCategory {self.name}>"


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("menu_categories.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(500), default="")
    is_veg = db.Column(db.Boolean, default=True)
    is_spicy = db.Column(db.Boolean, default=False)
    is_available = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else "",
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "image_url": self.image_url,
            "is_veg": self.is_veg,
            "is_spicy": self.is_spicy,
            "is_available": self.is_available,
            "is_featured": self.is_featured,
        }

    def __repr__(self):
        return f"<MenuItem {self.name}>"
