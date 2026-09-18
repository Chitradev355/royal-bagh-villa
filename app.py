import json
import os
from flask import Flask, session
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from config import Config
from models import db, Admin, BusinessSetting

login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Disable strict slashes so both /cafe and /cafe/ return 200 OK
    app.url_map.strict_slashes = False

    # Ensure upload directory exists
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/uploads"), exist_ok=True)

    # Ensure instance directory exists for SQLite
    instance_dir = os.path.join(os.path.dirname(__file__), "instance")
    os.makedirs(instance_dir, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    app.jinja_env.filters['fromjson'] = lambda s: json.loads(s) if s else []
    login_manager.init_app(app)
    login_manager.login_view = "admin_bp.login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Admin, int(user_id))

    # Inject business settings and cart into every template
    @app.context_processor
    def inject_globals():
        cart = session.get("cart", [])
        cart_count = sum(item.get("quantity", 1) for item in cart)
        cart_total = sum(item.get("quantity", 1) * item.get("price", 0) for item in cart)

        def get_setting(key, default=""):
            return BusinessSetting.get(key, default)

        return {
            "business_name": get_setting("business_name", Config.BUSINESS_NAME),
            "business_tagline": get_setting("business_tagline", Config.BUSINESS_TAGLINE),
            "business_phone": get_setting("business_phone", Config.BUSINESS_PHONE),
            "business_whatsapp": get_setting("business_whatsapp", Config.BUSINESS_WHATSAPP),
            "business_email": get_setting("business_email", Config.BUSINESS_EMAIL),
            "business_address": get_setting("business_address", Config.BUSINESS_ADDRESS),
            "business_map_url": get_setting("business_map_url", Config.BUSINESS_MAP_URL),
            "instagram_url": get_setting("instagram_url", "https://instagram.com/royalbaghvilla"),
            "restaurant_hours": get_setting("restaurant_hours", "11:00 AM – 11:00 PM"),
            "cafe_hours": get_setting("cafe_hours", "8:00 AM – 10:00 PM"),
            "cart_count": cart_count,
            "cart_total": cart_total,
            "cart_items": cart,
            "get_setting": get_setting,
        }

    # Register blueprints
    from routes.main import main_bp
    from routes.cafe import cafe_bp
    from routes.restaurant import restaurant_bp
    from routes.order import order_bp
    from routes.banquet import banquet_bp
    from routes.lawn import lawn_bp
    from routes.rooms import rooms_bp
    from routes.booking import booking_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    # Exempt public enquiry and API from CSRF restrictions for robust client interaction
    csrf.exempt(main_bp)
    csrf.exempt(api_bp)

    app.register_blueprint(main_bp)
    app.register_blueprint(cafe_bp, url_prefix="/cafe")
    app.register_blueprint(restaurant_bp, url_prefix="/restaurant")
    app.register_blueprint(order_bp, url_prefix="/order")
    app.register_blueprint(banquet_bp, url_prefix="/banquet")
    app.register_blueprint(lawn_bp, url_prefix="/lawn")
    app.register_blueprint(rooms_bp, url_prefix="/stay")
    app.register_blueprint(booking_bp, url_prefix="/check-status")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
