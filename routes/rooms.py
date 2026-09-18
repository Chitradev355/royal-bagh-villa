from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db, Room, RoomBooking
from datetime import datetime, date

rooms_bp = Blueprint('rooms_bp', __name__)


@rooms_bp.route('/')
def index():
    rooms = Room.query.order_by(Room.display_order).all()
    today = date.today().isoformat()
    return render_template('rooms.html', rooms=rooms, today=today)


@rooms_bp.route('/<slug>')
def room_detail(slug):
    room = Room.query.filter_by(slug=slug).first_or_404()
    today = date.today().isoformat()
    return render_template('room_detail.html', room=room, today=today)


@rooms_bp.route('/book/<slug>', methods=['GET', 'POST'])
def book(slug):
    room = Room.query.filter_by(slug=slug).first_or_404()
    today = date.today().isoformat()

    if request.method == 'POST':
        check_in_str = request.form.get('check_in', '')
        check_out_str = request.form.get('check_out', '')
        guest_count = request.form.get('guest_count', '1')
        customer_name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        special_requests = request.form.get('special_requests', '').strip()
        payment_mode = request.form.get('payment_mode', 'pay_at_venue')

        if not customer_name or not phone or not check_in_str or not check_out_str:
            flash('Please fill in all required fields.', 'error')
            return render_template('room_booking.html', room=room, today=today)

        try:
            check_in = datetime.strptime(check_in_str, '%Y-%m-%d').date()
            check_out = datetime.strptime(check_out_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('room_booking.html', room=room, today=today)

        if check_out <= check_in:
            flash('Check-out must be after check-in.', 'error')
            return render_template('room_booking.html', room=room, today=today)

        days = (check_out - check_in).days
        total_amount = room.price_per_night * days

        booking = RoomBooking(
            room_id=room.id,
            check_in=check_in,
            check_out=check_out,
            guest_count=int(guest_count) if guest_count.isdigit() else 1,
            customer_name=customer_name,
            phone=phone,
            email=email,
            special_requests=special_requests,
            payment_mode=payment_mode,
            total_amount=total_amount,
        )
        db.session.add(booking)
        db.session.commit()

        flash(f'Room booked successfully! Your Booking ID: {booking.booking_id}', 'success')
        return redirect(url_for('booking_bp.check_status'))

    return render_template('room_booking.html', room=room, today=today)
