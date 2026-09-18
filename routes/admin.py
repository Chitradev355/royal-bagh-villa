from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, date, timezone

from models import (db, Admin, FoodOrder, OrderItem, MenuCategory, MenuItem,
                    BanquetBooking, LawnBooking, Room, RoomBooking, Enquiry, BusinessSetting,
                    CMSContent, MediaFile, CMSEvent, GalleryItem, NavigationItem)
from utils.media import save_uploaded_media, delete_media_file
from config import Config

admin_bp = Blueprint('admin_bp', __name__)


# ── Auth ────────────────────────────────────────────────────────────────────

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_bp.dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            login_user(admin)
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/') and not next_page.startswith('//'):
                return redirect(next_page)
            return redirect(url_for('admin_bp.dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('admin/login.html')


@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('admin_bp.login'))


# ── Dashboard ────────────────────────────────────────────────────────────────

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    next_week = today + timedelta(days=7)

    today_orders = FoodOrder.query.filter(
        db.func.date(FoodOrder.created_at) == today
    ).all()
    today_revenue = sum(o.total_amount for o in today_orders if o.status != 'cancelled')

    banquet_upcoming = BanquetBooking.query.filter(
        BanquetBooking.event_date >= today,
        BanquetBooking.event_date <= next_week,
        BanquetBooking.status != 'cancelled'
    ).all()
    lawn_upcoming = LawnBooking.query.filter(
        LawnBooking.event_date >= today,
        LawnBooking.event_date <= next_week,
        LawnBooking.status != 'cancelled'
    ).all()

    available_rooms = Room.query.filter_by(is_available=True).count()
    new_enquiries = Enquiry.query.filter_by(status='new').count()

    stats = {
        'today_orders': len(today_orders),
        'today_revenue': today_revenue,
        'upcoming_events': len(banquet_upcoming) + len(lawn_upcoming),
        'available_rooms': available_rooms,
        'new_enquiries': new_enquiries,
    }

    recent_orders = FoodOrder.query.order_by(FoodOrder.created_at.desc()).limit(10).all()
    upcoming_events = banquet_upcoming + lawn_upcoming

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_orders=recent_orders,
                           upcoming_events=upcoming_events)


# ── Orders ───────────────────────────────────────────────────────────────────

@admin_bp.route('/orders')
@login_required
def orders():
    status_filter = request.args.get('status', '')
    q = FoodOrder.query.order_by(FoodOrder.created_at.desc())
    if status_filter:
        q = q.filter_by(status=status_filter)
    all_orders = q.all()
    return render_template('admin/orders.html', orders=all_orders, status_filter=status_filter)


@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@login_required
def update_order_status(order_id):
    order = db.session.get(FoodOrder, order_id)
    if not order:
        return jsonify({'error': 'Not found'}), 404
    new_status = request.form.get('status') or request.json.get('status', '')
    if new_status in FoodOrder.STATUS_FLOW + ['cancelled']:
        order.status = new_status
        db.session.commit()
        return jsonify({'success': True, 'status': new_status})
    return jsonify({'error': 'Invalid status'}), 400


# ── Menu ─────────────────────────────────────────────────────────────────────

@admin_bp.route('/menu')
@login_required
def menu():
    categories = MenuCategory.query.order_by(MenuCategory.section, MenuCategory.display_order).all()
    items = MenuItem.query.order_by(MenuItem.category_id, MenuItem.display_order).all()
    return render_template('admin/menu.html', categories=categories, items=items)


@admin_bp.route('/menu/category', methods=['POST'])
@login_required
def save_category():
    cat_id = request.form.get('id')
    name = request.form.get('name', '').strip()
    slug = request.form.get('slug', '').strip()
    section = request.form.get('section', 'main')
    description = request.form.get('description', '')
    display_order = int(request.form.get('display_order', 0))

    if 'image_file' in request.files and request.files['image_file'].filename:
        media, err = save_uploaded_media(request.files['image_file'], category='restaurant', title=name)
        if media:
            image_url = media.file_url

    if cat_id:
        cat = db.session.get(MenuCategory, int(cat_id))
        if cat:
            cat.name = name; cat.slug = slug; cat.section = section
            cat.description = description; cat.display_order = display_order
    else:
        cat = MenuCategory(name=name, slug=slug, section=section,
                           description=description, display_order=display_order)
        db.session.add(cat)
    db.session.commit()
    flash('Category saved.', 'success')
    return redirect(url_for('admin_bp.menu'))


@admin_bp.route('/menu/category/<int:cat_id>/delete', methods=['POST'])
@login_required
def delete_category(cat_id):
    cat = db.session.get(MenuCategory, cat_id)
    if cat:
        db.session.delete(cat)
        db.session.commit()
        flash('Category deleted.', 'success')
    return redirect(url_for('admin_bp.menu'))


@admin_bp.route('/menu/item', methods=['POST'])
@login_required
def save_item():
    item_id = request.form.get('id')
    category_id = int(request.form.get('category_id', 0))
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '')
    price = float(request.form.get('price', 0))
    image_url = request.form.get('image_url', '')
    is_veg = request.form.get('is_veg') == '1'
    is_spicy = request.form.get('is_spicy') == '1'
    is_available = request.form.get('is_available') == '1'
    is_featured = request.form.get('is_featured') == '1'
    display_order = int(request.form.get('display_order', 0))

    if item_id:
        item = db.session.get(MenuItem, int(item_id))
        if item:
            item.category_id = category_id; item.name = name
            item.description = description; item.price = price
            item.image_url = image_url; item.is_veg = is_veg
            item.is_spicy = is_spicy; item.is_available = is_available
            item.is_featured = is_featured; item.display_order = display_order
    else:
        item = MenuItem(category_id=category_id, name=name, description=description,
                        price=price, image_url=image_url, is_veg=is_veg,
                        is_spicy=is_spicy, is_available=is_available,
                        is_featured=is_featured, display_order=display_order)
        db.session.add(item)
    db.session.commit()
    flash('Menu item saved.', 'success')
    return redirect(url_for('admin_bp.menu'))


@admin_bp.route('/menu/item/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_item(item_id):
    item = db.session.get(MenuItem, item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted.', 'success')
    return redirect(url_for('admin_bp.menu'))


@admin_bp.route('/menu/item/<int:item_id>/toggle', methods=['POST'])
@login_required
def toggle_item(item_id):
    field = request.json.get('field', 'is_available')
    item = db.session.get(MenuItem, item_id)
    if not item:
        return jsonify({'error': 'Not found'}), 404
    if field == 'is_available':
        item.is_available = not item.is_available
    elif field == 'is_featured':
        item.is_featured = not item.is_featured
    db.session.commit()
    return jsonify({'success': True, 'value': getattr(item, field)})


# ── Banquet Bookings ─────────────────────────────────────────────────────────

@admin_bp.route('/banquet')
@login_required
def banquet_bookings():
    status_filter = request.args.get('status', '')
    q = BanquetBooking.query.order_by(BanquetBooking.created_at.desc())
    if status_filter:
        q = q.filter_by(status=status_filter)
    bookings = q.all()
    return render_template('admin/banquet_bookings.html', bookings=bookings, status_filter=status_filter)


@admin_bp.route('/banquet/<int:booking_id>/status', methods=['POST'])
@login_required
def update_banquet_status(booking_id):
    booking = db.session.get(BanquetBooking, booking_id)
    if not booking:
        return jsonify({'error': 'Not found'}), 404
    new_status = request.form.get('status') or (request.json or {}).get('status', '')
    if new_status in BanquetBooking.STATUS_FLOW:
        booking.status = new_status
        db.session.commit()
    flash('Booking status updated.', 'success')
    return redirect(url_for('admin_bp.banquet_bookings'))


@admin_bp.route('/banquet/<int:booking_id>/quote', methods=['POST'])
@login_required
def update_banquet_quote(booking_id):
    booking = db.session.get(BanquetBooking, booking_id)
    if booking:
        booking.estimated_quote = float(request.form.get('quote', 0))
        booking.admin_notes = request.form.get('admin_notes', '')
        db.session.commit()
        flash('Quote updated.', 'success')
    return redirect(url_for('admin_bp.banquet_bookings'))


# ── Lawn Bookings ─────────────────────────────────────────────────────────────

@admin_bp.route('/lawn')
@login_required
def lawn_bookings():
    status_filter = request.args.get('status', '')
    q = LawnBooking.query.order_by(LawnBooking.created_at.desc())
    if status_filter:
        q = q.filter_by(status=status_filter)
    bookings = q.all()
    return render_template('admin/lawn_bookings.html', bookings=bookings, status_filter=status_filter)


@admin_bp.route('/lawn/<int:booking_id>/status', methods=['POST'])
@login_required
def update_lawn_status(booking_id):
    booking = db.session.get(LawnBooking, booking_id)
    if booking:
        new_status = request.form.get('status', '')
        if new_status in LawnBooking.STATUS_FLOW:
            booking.status = new_status
            db.session.commit()
    flash('Booking status updated.', 'success')
    return redirect(url_for('admin_bp.lawn_bookings'))


# ── Room Management ───────────────────────────────────────────────────────────

@admin_bp.route('/rooms')
@login_required
def rooms_manage():
    rooms = Room.query.order_by(Room.display_order).all()
    return render_template('admin/rooms_manage.html', rooms=rooms)


@admin_bp.route('/rooms/save', methods=['POST'])
@login_required
def save_room():
    room_id = request.form.get('id')
    name = request.form.get('name', '').strip()
    slug = request.form.get('slug', '').strip()
    description = request.form.get('description', '')
    price_per_night = float(request.form.get('price_per_night', 0))
    max_guests = int(request.form.get('max_guests', 2))
    amenities_raw = request.form.get('amenities', '')
    images_raw = request.form.get('images', '')
    is_available = request.form.get('is_available') == '1'
    display_order = int(request.form.get('display_order', 0))

    amenities = [a.strip() for a in amenities_raw.split(',') if a.strip()]
    images = [i.strip() for i in images_raw.split(',') if i.strip()]

    if room_id:
        room = db.session.get(Room, int(room_id))
        if room:
            room.name = name; room.slug = slug; room.description = description
            room.price_per_night = price_per_night; room.max_guests = max_guests
            room.amenities = amenities; room.images = images
            room.is_available = is_available; room.display_order = display_order
    else:
        room = Room(name=name, slug=slug, description=description,
                    price_per_night=price_per_night, max_guests=max_guests,
                    is_available=is_available, display_order=display_order)
        room.amenities = amenities
        room.images = images
        db.session.add(room)
    db.session.commit()
    flash('Room saved.', 'success')
    return redirect(url_for('admin_bp.rooms_manage'))


@admin_bp.route('/rooms/<int:room_id>/delete', methods=['POST'])
@login_required
def delete_room(room_id):
    room = db.session.get(Room, room_id)
    if room:
        db.session.delete(room)
        db.session.commit()
        flash('Room deleted.', 'success')
    return redirect(url_for('admin_bp.rooms_manage'))


@admin_bp.route('/room-bookings')
@login_required
def room_bookings():
    status_filter = request.args.get('status', '')
    q = RoomBooking.query.order_by(RoomBooking.created_at.desc())
    if status_filter:
        q = q.filter_by(status=status_filter)
    bookings = q.all()
    return render_template('admin/room_bookings.html', bookings=bookings, status_filter=status_filter)


@admin_bp.route('/room-bookings/<int:booking_id>/status', methods=['POST'])
@login_required
def update_room_booking_status(booking_id):
    booking = db.session.get(RoomBooking, booking_id)
    if booking:
        new_status = request.form.get('status', '')
        if new_status in RoomBooking.STATUS_FLOW + ['cancelled']:
            booking.status = new_status
            db.session.commit()
    flash('Room booking status updated.', 'success')
    return redirect(url_for('admin_bp.room_bookings'))


# ── Enquiries ─────────────────────────────────────────────────────────────────

@admin_bp.route('/enquiries')
@login_required
def enquiries():
    status_filter = request.args.get('status', '')
    q = Enquiry.query.order_by(Enquiry.created_at.desc())
    if status_filter:
        q = q.filter_by(status=status_filter)
    all_enquiries = q.all()
    return render_template('admin/enquiries.html', enquiries=all_enquiries, status_filter=status_filter)


@admin_bp.route('/enquiries/<int:enquiry_id>/status', methods=['POST'])
@login_required
def update_enquiry_status(enquiry_id):
    enquiry = db.session.get(Enquiry, enquiry_id)
    if enquiry:
        enquiry.status = request.form.get('status', 'read')
        enquiry.admin_notes = request.form.get('admin_notes', enquiry.admin_notes)
        db.session.commit()
    flash('Enquiry updated.', 'success')
    return redirect(url_for('admin_bp.enquiries'))


# ── Settings ──────────────────────────────────────────────────────────────────

SETTINGS_FIELDS = [
    ('business_name', 'Business Name'),
    ('business_tagline', 'Tagline'),
    ('business_phone', 'Phone Number'),
    ('business_whatsapp', 'WhatsApp Number'),
    ('business_email', 'Email Address'),
    ('business_address', 'Address'),
    ('business_map_url', 'Google Maps URL'),
    ('restaurant_hours', 'Restaurant Hours'),
    ('cafe_hours', 'Cafe Hours'),
    ('instagram_url', 'Instagram URL'),
    ('facebook_url', 'Facebook URL'),
    ('site_title', 'SEO Title'),
    ('site_description', 'SEO Description'),
    ('logo_text', 'Logo Text'),
    ('logo_image', 'Logo Image URL'),
    ('favicon', 'Favicon URL'),
    ('footer_tagline', 'Footer Tagline'),
    ('footer_about', 'Footer About Text'),
    ('google_analytics_id', 'Google Analytics / Tag ID'),
    ('custom_css', 'Custom CSS'),
    ('custom_js', 'Custom Head Scripts'),
]


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    if request.method == 'POST':
        for key, label in SETTINGS_FIELDS:
            value = request.form.get(key, '')
            BusinessSetting.set(key, value, label)
            CMSContent.set_value('settings', 'general', key, value, 'text', label)

        if 'logo_image_file' in request.files and request.files['logo_image_file'].filename:
            media, err = save_uploaded_media(request.files['logo_image_file'], category='general', title='Website Logo')
            if media:
                BusinessSetting.set('logo_image', media.file_url, 'Logo Image URL')
                CMSContent.set_value('settings', 'general', 'logo_image', media.file_url, 'image', 'Logo Image URL')

        if 'favicon_file' in request.files and request.files['favicon_file'].filename:
            media, err = save_uploaded_media(request.files['favicon_file'], category='general', title='Website Favicon')
            if media:
                BusinessSetting.set('favicon', media.file_url, 'Favicon URL')
                CMSContent.set_value('settings', 'general', 'favicon', media.file_url, 'image', 'Favicon URL')

        flash('Website settings saved successfully.', 'success')
        return redirect(url_for('admin_bp.settings_view'))

    settings = {}
    for key, _ in SETTINGS_FIELDS:
        cms_val = CMSContent.get_value('settings', key, '')
        if cms_val:
            settings[key] = cms_val
        else:
            settings[key] = BusinessSetting.get(key, getattr(Config, key.upper(), ''))

    media_items = MediaFile.query.order_by(MediaFile.created_at.desc()).limit(20).all()
    return render_template('admin/settings.html', settings=settings, fields=SETTINGS_FIELDS, media_items=media_items)


# ?? Media Library ?????????????????????????????????????????????????????????????

@admin_bp.route('/media')
@login_required
def media_library():
    category_filter = request.args.get('category', '')
    type_filter = request.args.get('type', '')
    q = MediaFile.query.order_by(MediaFile.created_at.desc())
    if category_filter:
        q = q.filter_by(category=category_filter)
    if type_filter:
        q = q.filter_by(file_type=type_filter)
    media_items = q.all()
    categories = ['hero', 'cafe', 'restaurant', 'banquet', 'lawn', 'events', 'gallery', 'general']
    return render_template('admin/media.html', media_items=media_items, categories=categories,
                           category_filter=category_filter, type_filter=type_filter)


@admin_bp.route('/media/upload', methods=['POST'])
@login_required
def media_upload():
    if 'file' not in request.files:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': 'No file part'}), 400
        flash('No file selected.', 'error')
        return redirect(url_for('admin_bp.media_library'))

    file = request.files['file']
    category = request.form.get('category', 'general')
    title = request.form.get('title', '').strip()
    alt_text = request.form.get('alt_text', '').strip()

    media, error = save_uploaded_media(file, category=category, title=title, alt_text=alt_text)
    if error:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
            return jsonify({'success': False, 'error': error}), 400
        flash(error, 'error')
        return redirect(url_for('admin_bp.media_library'))

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json:
        return jsonify({'success': True, 'media': media.to_dict()})

    flash('Media uploaded successfully!', 'success')
    return redirect(url_for('admin_bp.media_library'))


@admin_bp.route('/media/<int:media_id>/delete', methods=['POST'])
@login_required
def media_delete(media_id):
    success, error = delete_media_file(media_id)
    if not success:
        flash(error or 'Failed to delete media', 'error')
    else:
        flash('Media file deleted.', 'success')
    return redirect(url_for('admin_bp.media_library'))


@admin_bp.route('/media/api/picker')
@login_required
def media_picker_api():
    category = request.args.get('category', '')
    media_type = request.args.get('type', '')
    q = MediaFile.query.order_by(MediaFile.created_at.desc())
    if category:
        q = q.filter_by(category=category)
    if media_type:
        q = q.filter_by(file_type=media_type)
    items = q.limit(60).all()
    return jsonify({'media': [m.to_dict() for m in items]})


# ?? Homepage CMS ??????????????????????????????????????????????????????????????

@admin_bp.route('/cms/home', methods=['GET', 'POST'])
@login_required
def cms_home():
    if request.method == 'POST':
        fields = [
            ('hero', 'badge', request.form.get('hero_badge', ''), 'text', 'Hero Badge'),
            ('hero', 'title', request.form.get('hero_title', ''), 'html', 'Hero Title'),
            ('hero', 'subtitle', request.form.get('hero_subtitle', ''), 'text', 'Hero Subtitle'),
            ('hero', 'tagline', request.form.get('hero_tagline', ''), 'text', 'Hero Tagline'),
            ('hero', 'image', request.form.get('hero_image', ''), 'image', 'Hero Background Image'),
            ('hero', 'video_url', request.form.get('hero_video_url', ''), 'video', 'Hero Background Video'),
            ('hero', 'cta_primary_text', request.form.get('cta_primary_text', ''), 'text', 'CTA Primary Text'),
            ('hero', 'cta_primary_link', request.form.get('cta_primary_link', ''), 'text', 'CTA Primary Link'),
            ('hero', 'cta_whatsapp_text', request.form.get('cta_whatsapp_text', ''), 'text', 'WhatsApp CTA Text'),
            ('intro', 'badge', request.form.get('intro_badge', ''), 'text', 'Intro Badge'),
            ('intro', 'title', request.form.get('intro_title', ''), 'html', 'Intro Title'),
            ('intro', 'text', request.form.get('intro_text', ''), 'text', 'Intro Description'),
            ('offers', 'badge', request.form.get('offers_badge', ''), 'text', 'Offers Badge'),
            ('offers', 'title', request.form.get('offers_title', ''), 'text', 'Offers Title'),
            ('offers', 'text', request.form.get('offers_text', ''), 'text', 'Offers Details'),
        ]
        for section, key, val, c_type, label in fields:
            CMSContent.set_value('home', section, key, val, c_type, label)

        if 'hero_image_file' in request.files and request.files['hero_image_file'].filename:
            media, err = save_uploaded_media(request.files['hero_image_file'], category='hero', title='Homepage Hero Image')
            if media:
                CMSContent.set_value('home', 'hero', 'image', media.file_url, 'image', 'Hero Background Image')

        if 'hero_video_file' in request.files and request.files['hero_video_file'].filename:
            media, err = save_uploaded_media(request.files['hero_video_file'], category='hero', title='Homepage Hero Video')
            if media:
                CMSContent.set_value('home', 'hero', 'video_url', media.file_url, 'video', 'Hero Background Video')

        flash('Homepage content saved successfully.', 'success')
        return redirect(url_for('admin_bp.cms_home'))

    contents = {c.key: c.value for c in CMSContent.query.filter_by(page='home').all()}
    media_items = MediaFile.query.order_by(MediaFile.created_at.desc()).limit(30).all()
    return render_template('admin/cms_home.html', contents=contents, media_items=media_items)


# ?? Pages CMS ?????????????????????????????????????????????????????????????????

@admin_bp.route('/cms/pages', methods=['GET', 'POST'])
@login_required
def cms_pages():
    active_page = request.args.get('page', 'about')
    supported_pages = ['about', 'cafe', 'restaurant', 'banquet', 'lawn', 'events', 'gallery', 'contact']
    if active_page not in supported_pages:
        active_page = 'about'

    if request.method == 'POST':
        target_page = request.form.get('target_page', active_page)
        for form_key in request.form:
            if form_key.startswith('field_'):
                key_name = form_key[6:]
                val = request.form.get(form_key, '')
                section = request.form.get(f'section_{key_name}', 'content')
                c_type = request.form.get(f'type_{key_name}', 'text')
                label = request.form.get(f'label_{key_name}', key_name.replace('_', ' ').title())
                CMSContent.set_value(target_page, section, key_name, val, c_type, label)

        for file_key in request.files:
            file_obj = request.files[file_key]
            if file_obj and file_obj.filename:
                clean_key = file_key.replace('_file', '')
                media, err = save_uploaded_media(file_obj, category=target_page, title=f"{target_page.title()} {clean_key}")
                if media:
                    section = 'hero' if 'hero' in clean_key else 'content'
                    CMSContent.set_value(target_page, section, clean_key, media.file_url, media.file_type)

        flash(f'{target_page.title()} page content updated successfully.', 'success')
        return redirect(url_for('admin_bp.cms_pages', page=target_page))

    contents = {c.key: c.value for c in CMSContent.query.filter_by(page=active_page).all()}
    all_pages_summary = {p: CMSContent.query.filter_by(page=p).count() for p in supported_pages}
    media_items = MediaFile.query.order_by(MediaFile.created_at.desc()).limit(30).all()

    return render_template('admin/cms_pages.html', active_page=active_page, supported_pages=supported_pages,
                           contents=contents, all_pages_summary=all_pages_summary, media_items=media_items)


# ?? Venues CMS (Banquet & Lawn) ???????????????????????????????????????????????

@admin_bp.route('/cms/venues', methods=['GET', 'POST'])
@login_required
def cms_venues():
    venue = request.args.get('venue', 'banquet')
    if venue not in ['banquet', 'lawn']:
        venue = 'banquet'

    if request.method == 'POST':
        target_venue = request.form.get('venue', venue)
        keys = ['capacity', 'pricing', 'pricing_note', 'description', 'features', 'hero_image', 'video_url', 'offers']
        for k in keys:
            val = request.form.get(k, '')
            CMSContent.set_value(target_venue, 'details', k, val, 'text', f"{target_venue.title()} {k.title()}")

        if 'venue_image_file' in request.files and request.files['venue_image_file'].filename:
            media, err = save_uploaded_media(request.files['venue_image_file'], category=target_venue, title=f"{target_venue.title()} Main Image")
            if media:
                CMSContent.set_value(target_venue, 'hero', 'image', media.file_url, 'image', f"{target_venue.title()} Hero Image")

        if 'venue_video_file' in request.files and request.files['venue_video_file'].filename:
            media, err = save_uploaded_media(request.files['venue_video_file'], category=target_venue, title=f"{target_venue.title()} Video Tour")
            if media:
                CMSContent.set_value(target_venue, 'details', 'video_url', media.file_url, 'video', f"{target_venue.title()} Video Tour")

        flash(f'{target_venue.title()} details updated.', 'success')
        return redirect(url_for('admin_bp.cms_venues', venue=target_venue))

    contents = {c.key: c.value for c in CMSContent.query.filter_by(page=venue).all()}
    media_items = MediaFile.query.filter_by(category=venue).order_by(MediaFile.created_at.desc()).all()
    if not media_items:
        media_items = MediaFile.query.order_by(MediaFile.created_at.desc()).limit(20).all()

    return render_template('admin/cms_venues.html', venue=venue, contents=contents, media_items=media_items)


# ?? Events CMS ????????????????????????????????????????????????????????????????

@admin_bp.route('/cms/events')
@login_required
def cms_events():
    events_list = CMSEvent.query.order_by(CMSEvent.display_order).all()
    categories = ['wedding', 'birthday', 'engagement', 'anniversary', 'corporate', 'party', 'kitty', 'other']
    return render_template('admin/cms_events.html', events=events_list, categories=categories)


@admin_bp.route('/cms/events/save', methods=['POST'])
@login_required
def save_cms_event():
    event_id = request.form.get('id')
    title = request.form.get('title', '').strip()
    slug = request.form.get('slug', '').strip() or title.lower().replace(' ', '-').replace('&', 'and')
    category = request.form.get('category', 'other')
    short_description = request.form.get('short_description', '')
    full_description = request.form.get('full_description', '')
    cover_image = request.form.get('cover_image', '')
    video_url = request.form.get('video_url', '')
    features_raw = request.form.get('features', '')
    cta_label = request.form.get('cta_label', 'Plan Event')
    cta_link = request.form.get('cta_link', '#enquiry')
    display_order = int(request.form.get('display_order', 0))
    is_active = request.form.get('is_active') == '1'

    if 'cover_image_file' in request.files and request.files['cover_image_file'].filename:
        media, err = save_uploaded_media(request.files['cover_image_file'], category='events', title=title)
        if media:
            cover_image = media.file_url

    if 'video_file' in request.files and request.files['video_file'].filename:
        media, err = save_uploaded_media(request.files['video_file'], category='events', title=f"{title} Video")
        if media:
            video_url = media.file_url

    if event_id:
        ev = db.session.get(CMSEvent, int(event_id))
        if ev:
            ev.title = title
            ev.slug = slug
            ev.category = category
            ev.short_description = short_description
            ev.full_description = full_description
            if cover_image:
                ev.cover_image = cover_image
            ev.video_url = video_url
            ev.features = features_raw
            ev.cta_label = cta_label
            ev.cta_link = cta_link
            ev.display_order = display_order
            ev.is_active = is_active
    else:
        ev = CMSEvent(
            title=title, slug=slug, category=category, short_description=short_description,
            full_description=full_description, cover_image=cover_image, video_url=video_url,
            cta_label=cta_label, cta_link=cta_link, display_order=display_order, is_active=is_active
        )
        ev.features = features_raw
        db.session.add(ev)

    db.session.commit()
    flash('Event saved successfully.', 'success')
    return redirect(url_for('admin_bp.cms_events'))


@admin_bp.route('/cms/events/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_cms_event(event_id):
    ev = db.session.get(CMSEvent, event_id)
    if ev:
        db.session.delete(ev)
        db.session.commit()
        flash('Event deleted.', 'success')
    return redirect(url_for('admin_bp.cms_events'))


@admin_bp.route('/cms/events/<int:event_id>/toggle', methods=['POST'])
@login_required
def toggle_cms_event(event_id):
    ev = db.session.get(CMSEvent, event_id)
    if not ev:
        return jsonify({'error': 'Not found'}), 404
    ev.is_active = not ev.is_active
    db.session.commit()
    return jsonify({'success': True, 'is_active': ev.is_active})


# ?? Gallery CMS ???????????????????????????????????????????????????????????????

@admin_bp.route('/cms/gallery')
@login_required
def cms_gallery():
    category_filter = request.args.get('category', '')
    q = GalleryItem.query.order_by(GalleryItem.display_order)
    if category_filter:
        q = q.filter_by(category=category_filter)
    items = q.all()
    categories = ['all', 'lawn', 'banquet', 'cafe', 'restaurant', 'events', 'property', 'food']
    return render_template('admin/cms_gallery.html', items=items, categories=categories, category_filter=category_filter)


@admin_bp.route('/cms/gallery/save', methods=['POST'])
@login_required
def save_gallery_item():
    item_id = request.form.get('id')
    title = request.form.get('title', '').strip()
    caption = request.form.get('caption', '').strip()
    media_url = request.form.get('media_url', '').strip()
    media_type = request.form.get('media_type', 'image')
    category = request.form.get('category', 'all')
    display_order = int(request.form.get('display_order', 0))
    is_featured = request.form.get('is_featured') == '1'

    if 'media_file' in request.files and request.files['media_file'].filename:
        media, err = save_uploaded_media(request.files['media_file'], category='gallery', title=title or 'Gallery Upload')
        if media:
            media_url = media.file_url
            media_type = media.file_type

    if item_id:
        item = db.session.get(GalleryItem, int(item_id))
        if item:
            item.title = title; item.caption = caption; item.category = category
            item.media_type = media_type; item.display_order = display_order
            item.is_featured = is_featured
            if media_url:
                item.media_url = media_url
    else:
        if not media_url:
            flash('Please provide an image/video URL or upload a file.', 'error')
            return redirect(url_for('admin_bp.cms_gallery'))
        item = GalleryItem(title=title, caption=caption, media_url=media_url, media_type=media_type,
                           category=category, display_order=display_order, is_featured=is_featured)
        db.session.add(item)

    db.session.commit()
    flash('Gallery item saved.', 'success')
    return redirect(url_for('admin_bp.cms_gallery'))


@admin_bp.route('/cms/gallery/<int:item_id>/delete', methods=['POST'])
@login_required
def delete_gallery_item(item_id):
    item = db.session.get(GalleryItem, item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Gallery item removed.', 'success')
    return redirect(url_for('admin_bp.cms_gallery'))


# ?? Navigation CMS ????????????????????????????????????????????????????????????

@admin_bp.route('/cms/navigation')
@login_required
def cms_navigation():
    nav_items = NavigationItem.query.order_by(NavigationItem.display_order).all()
    return render_template('admin/cms_navigation.html', nav_items=nav_items)


@admin_bp.route('/cms/navigation/save', methods=['POST'])
@login_required
def save_nav_item():
    nav_id = request.form.get('id')
    label = request.form.get('label', '').strip()
    url = request.form.get('url', '').strip()
    location = request.form.get('location', 'header')
    display_order = int(request.form.get('display_order', 0))
    is_visible = request.form.get('is_visible') == '1'
    is_external = request.form.get('is_external') == '1'
    target = '_blank' if is_external else '_self'

    if nav_id:
        nav = db.session.get(NavigationItem, int(nav_id))
        if nav:
            nav.label = label; nav.url = url; nav.location = location
            nav.display_order = display_order; nav.is_visible = is_visible
            nav.is_external = is_external; nav.target = target
    else:
        nav = NavigationItem(label=label, url=url, location=location, display_order=display_order,
                             is_visible=is_visible, is_external=is_external, target=target)
        db.session.add(nav)

    db.session.commit()
    flash('Navigation link saved.', 'success')
    return redirect(url_for('admin_bp.cms_navigation'))


@admin_bp.route('/cms/navigation/<int:nav_id>/delete', methods=['POST'])
@login_required
def delete_nav_item(nav_id):
    nav = db.session.get(NavigationItem, nav_id)
    if nav:
        db.session.delete(nav)
        db.session.commit()
        flash('Navigation item deleted.', 'success')
    return redirect(url_for('admin_bp.cms_navigation'))


@admin_bp.route('/cms/navigation/<int:nav_id>/toggle', methods=['POST'])
@login_required
def toggle_nav_item(nav_id):
    nav = db.session.get(NavigationItem, nav_id)
    if not nav:
        return jsonify({'error': 'Not found'}), 404
    nav.is_visible = not nav.is_visible
    db.session.commit()
    return jsonify({'success': True, 'is_visible': nav.is_visible})


# ?? Backup & Restore ??????????????????????????????????????????????????????????

@admin_bp.route('/backup/export')
@login_required
def export_backup():
    data = {
        'exported_at': datetime.now(timezone.utc).isoformat(),
        'cms_contents': [
            {'page': c.page, 'section': c.section, 'key': c.key, 'value': c.value, 'content_type': c.content_type, 'label': c.label}
            for c in CMSContent.query.all()
        ],
        'events': [e.to_dict() for e in CMSEvent.query.all()],
        'gallery': [g.to_dict() for g in GalleryItem.query.all()],
        'navigation': [n.to_dict() for n in NavigationItem.query.all()],
        'menu_categories': [{'name': mc.name, 'slug': mc.slug, 'section': mc.section, 'description': mc.description, 'display_order': mc.display_order} for mc in MenuCategory.query.all()],
        'menu_items': [mi.to_dict() for mi in MenuItem.query.all()],
        'business_settings': [{'key': bs.key, 'value': bs.value, 'label': bs.label} for bs in BusinessSetting.query.all()]
    }
    response = jsonify(data)
    response.headers['Content-Disposition'] = f'attachment; filename=royal_bagh_cms_backup_{date.today().isoformat()}.json'
    return response


@admin_bp.route('/backup/import', methods=['POST'])
@login_required
def import_backup():
    if 'backup_file' not in request.files:
        flash('No backup file selected.', 'error')
        return redirect(url_for('admin_bp.settings_view'))

    file = request.files['backup_file']
    try:
        import json
        data = json.load(file)
        if 'cms_contents' in data:
            for c in data['cms_contents']:
                CMSContent.set_value(c['page'], c['section'], c['key'], c['value'], c.get('content_type', 'text'), c.get('label', ''))

        if 'navigation' in data:
            for n in data['navigation']:
                nav = NavigationItem.query.filter_by(label=n['label']).first()
                if not nav:
                    nav = NavigationItem(label=n['label'], url=n['url'])
                    db.session.add(nav)
                nav.url = n['url']
                nav.location = n.get('location', 'header')
                nav.display_order = n.get('display_order', 0)
                nav.is_visible = n.get('is_visible', True)
            db.session.commit()

        if 'business_settings' in data:
            for bs in data['business_settings']:
                BusinessSetting.set(bs['key'], bs['value'], bs.get('label', ''))

        flash('Backup data successfully restored!', 'success')
    except Exception as e:
        flash(f'Failed to restore backup: {str(e)}', 'error')

    return redirect(url_for('admin_bp.settings_view'))
