from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta, date, timezone

from models import (db, Admin, FoodOrder, OrderItem, MenuCategory, MenuItem,
                    BanquetBooking, LawnBooking, Room, RoomBooking, Enquiry, BusinessSetting)
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
    ('about_text', 'About Text'),
]


@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_view():
    if request.method == 'POST':
        for key, label in SETTINGS_FIELDS:
            value = request.form.get(key, '')
            BusinessSetting.set(key, value, label)
        flash('Settings saved successfully.', 'success')
        return redirect(url_for('admin_bp.settings_view'))

    settings = {key: BusinessSetting.get(key, getattr(Config, key.upper(), ''))
                for key, _ in SETTINGS_FIELDS}
    return render_template('admin/settings.html', settings=settings, fields=SETTINGS_FIELDS)
