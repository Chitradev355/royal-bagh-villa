import os
from flask import Flask
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

from models import db, Admin, MenuCategory, MenuItem, FoodOrder, OrderItem, BanquetBooking, LawnBooking, Room, RoomBooking, Enquiry, BusinessSetting

# Minimal app setup for seeding
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///royal_bagh.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def seed():
    with app.app_context():
        # Create all tables
        db.create_all()

        # Check if admin already exists
        if Admin.query.filter_by(username='admin').first():
            print("Database already seeded.")
            return

        print("Seeding database...")

        # 1. Admin
        admin = Admin(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            name='Royal Bagh Villa Admin',
            role='superadmin'
        )
        db.session.add(admin)

        # 2. Settings
        settings_data = [
            ('business_name', 'Royal Bagh Villa', 'Business Name'),
            ('tagline', 'Luxury Hospitality', 'Tagline'),
            ('phone_primary', '+91 9876543210', 'Primary Phone'),
            ('whatsapp_number', '+91 9876543210', 'WhatsApp Number'),
            ('email_address', 'info@royalbaghvilla.com', 'Email Address'),
            ('address_text', '123 Heritage Lane, City', 'Address'),
        ]
        for key, value, label in settings_data:
            s = BusinessSetting(key=key, value=value, label=label)
            db.session.add(s)

        # 3. Menu Categories
        categories = [
            ('Coffee', 'coffee', 'Freshly brewed coffee', 'cafe', 1),
            ('Tea & Beverages', 'tea-beverages', 'Refreshing teas', 'cafe', 2),
            ('Breakfast', 'breakfast', 'Start your day', 'breakfast', 1),
            ('Indian Main Course', 'indian-main', 'Authentic Indian curries', 'main', 1),
            ('Desserts', 'desserts', 'Sweet endings', 'sweet', 1)
        ]
        
        cats = {}
        for name, slug, desc, sec, order in categories:
            c = MenuCategory(name=name, slug=slug, description=desc, section=sec, display_order=order, is_active=True)
            db.session.add(c)
            cats[slug] = c
            
        db.session.flush()

        # 4. Menu Items
        items = [
            (cats['coffee'].id, 'Cappuccino', 'Rich espresso with steamed milk foam.', 150.0, True, False, True),
            (cats['tea-beverages'].id, 'Masala Chai', 'Traditional Indian spiced tea.', 90.0, True, False, False),
            (cats['breakfast'].id, 'Paneer Paratha', 'Stuffed flatbread with cottage cheese, served with curd.', 180.0, True, False, True),
            (cats['indian-main'].id, 'Butter Chicken', 'Tender chicken in a rich, creamy tomato gravy.', 450.0, False, False, True),
            (cats['indian-main'].id, 'Dal Makhani', 'Slow-cooked black lentils with butter and cream.', 320.0, True, False, True),
            (cats['desserts'].id, 'Gulab Jamun', 'Deep-fried milk dumplings soaked in sugar syrup.', 120.0, True, False, False)
        ]

        for cat_id, name, desc, price, veg, spicy, feat in items:
            img = f"https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&q=80" # Placeholder
            m = MenuItem(category_id=cat_id, name=name, description=desc, price=price, image_url=img, is_veg=veg, is_spicy=spicy, is_featured=feat)
            db.session.add(m)

        # 5. Rooms
        rooms = [
            ('Royal Suite', 'royal-suite', 'Spacious luxury suite with premium amenities.', 4999.0, 4),
            ('Premium Room', 'premium-room', 'Elegant room with a view.', 2999.0, 3),
            ('Standard Room', 'standard-room', 'Comfortable stay.', 1499.0, 2)
        ]
        
        for name, slug, desc, price, max_g in rooms:
            r = Room(name=name, slug=slug, description=desc, price_per_night=price, max_guests=max_g, amenities_json='["Wi-Fi", "AC", "TV"]', images_json='["https://images.unsplash.com/photo-1578683010236-d716f9a3f461?w=800"]')
            db.session.add(r)

        # Final commit
        db.session.commit()
        print("Database seeding completed successfully.")

if __name__ == '__main__':
    seed()
