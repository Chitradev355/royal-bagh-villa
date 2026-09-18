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

    # Enable ProxyFix to correctly handle reverse proxies, headers and HTTPS on Render
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Disable strict slashes so both /cafe and /cafe/ return 200 OK
    app.url_map.strict_slashes = False

    from models import db, Admin, BusinessSetting, CMSContent, NavigationItem, CMSEvent, GalleryItem
    from utils.media import format_file_size
    from utils.cms_seeder import seed_cms_defaults

    # Ensure persistent directories exist and initialize database if needed
    persistent_dir = getattr(Config, "PERSISTENT_STORAGE_DIR", None)
    if persistent_dir:
        os.makedirs(persistent_dir, exist_ok=True)
        # If SQLite is configured on persistent disk and file doesn't exist yet, copy seed DB
        persistent_db_file = os.path.join(persistent_dir, "royal_bagh.db")
        seed_db = os.path.join(os.path.dirname(__file__), "instance", "royal_bagh.db")
        if not os.path.exists(persistent_db_file) and os.path.exists(seed_db):
            try:
                import shutil
                shutil.copy2(seed_db, persistent_db_file)
            except Exception:
                pass

    # Ensure upload directories exist
    os.makedirs(app.config.get("UPLOAD_FOLDER", "static/uploads"), exist_ok=True)
    os.makedirs(app.config.get("MEDIA_UPLOAD_FOLDER", "static/uploads/media"), exist_ok=True)

    # Ensure instance directory exists for SQLite
    instance_dir = os.path.join(os.path.dirname(__file__), "instance")
    os.makedirs(instance_dir, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    csrf.init_app(app)
    app.jinja_env.filters['fromjson'] = lambda s: json.loads(s) if s else []
    app.jinja_env.filters['filesize'] = format_file_size
    login_manager.init_app(app)
    login_manager.login_view = "admin_bp.login"
    login_manager.login_message = "Please log in to access the admin panel."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Admin, int(user_id))

    # Inject business settings, CMS helpers and cart into every template
    @app.context_processor
    def inject_globals():
        cart = session.get("cart", [])
        cart_count = sum(item.get("quantity", 1) for item in cart)
        cart_total = sum(item.get("quantity", 1) * item.get("price", 0) for item in cart)

        def get_setting(key, default=""):
            cms_val = CMSContent.get_value("settings", key, "")
            if cms_val:
                return cms_val
            return BusinessSetting.get(key, getattr(Config, key.upper(), default))

        def get_cms(page, key, default=""):
            return CMSContent.get_value(page, key, default)

        def get_nav_items(location="header"):
            items = NavigationItem.query.filter_by(is_visible=True).order_by(NavigationItem.display_order).all()
            if location != "all":
                items = [i for i in items if i.location in (location, "both")]
            return items

        def get_events(limit=None):
            q = CMSEvent.query.filter_by(is_active=True).order_by(CMSEvent.display_order)
            if limit:
                q = q.limit(limit)
            return q.all()

        def get_gallery(category=None, limit=None):
            q = GalleryItem.query
            if category and category != 'all':
                q = q.filter_by(category=category)
            q = q.order_by(GalleryItem.display_order)
            if limit:
                q = q.limit(limit)
            return q.all()

        return {
            "business_name": get_setting("business_name", Config.BUSINESS_NAME),
            "business_tagline": get_setting("business_tagline", Config.BUSINESS_TAGLINE),
            "business_phone": get_setting("business_phone", Config.BUSINESS_PHONE),
            "business_whatsapp": get_setting("business_whatsapp", Config.BUSINESS_WHATSAPP),
            "business_email": get_setting("business_email", Config.BUSINESS_EMAIL),
            "business_address": get_setting("business_address", Config.BUSINESS_ADDRESS),
            "business_map_url": get_setting("business_map_url", Config.BUSINESS_MAP_URL),
            "instagram_url": get_setting("instagram_url", "https://instagram.com/royalbaghvilla"),
            "facebook_url": get_setting("facebook_url", "https://facebook.com/royalbaghvilla"),
            "restaurant_hours": get_setting("restaurant_hours", "11:00 AM – 11:00 PM"),
            "cafe_hours": get_setting("cafe_hours", "8:00 AM – 10:00 PM"),
            "site_title": get_setting("site_title", "Royal Bagh Villa Dehradun | Cafe, Restaurant, Lawn & Events"),
            "site_description": get_setting("site_description", "Royal Bagh Villa, Dehradun — a premium destination for dining and celebrations."),
            "logo_text": get_setting("logo_text", "Royal Bagh Villa"),
            "logo_image": get_setting("logo_image", ""),
            "favicon": get_setting("favicon", ""),
            "footer_tagline": get_setting("footer_tagline", "Where Every Celebration Becomes a Memory"),
            "footer_about": get_setting("footer_about", "A premier destination in Dehradun bringing together fine dining, artisanal cafe moments, grand lawn celebrations, and unforgettable events."),
            "google_analytics_id": get_setting("google_analytics_id", ""),
            "custom_css": get_setting("custom_css", ""),
            "custom_js": get_setting("custom_js", ""),
            "cart_count": cart_count,
            "cart_total": cart_total,
            "cart_items": cart,
            "get_setting": get_setting,
            "get_cms": get_cms,
            "get_nav_items": get_nav_items,
            "get_events": get_events,
            "get_gallery": get_gallery,
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

    # Serve media uploads seamlessly from persistent directory or local static folder
    from flask import send_from_directory

    @app.route('/static/uploads/media/<path:filename>')
    @app.route('/uploads/media/<path:filename>')
    def serve_uploaded_media(filename):
        media_folder = app.config.get("MEDIA_UPLOAD_FOLDER")
        if not os.path.isabs(media_folder):
            media_folder = os.path.join(os.path.dirname(__file__), media_folder)
        return send_from_directory(media_folder, filename)

    # Create tables & initialize CMS defaults
    with app.app_context():
        db.create_all()
        seed_cms_defaults()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)
