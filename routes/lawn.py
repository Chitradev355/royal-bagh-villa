from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db, LawnBooking
from datetime import datetime, date

lawn_bp = Blueprint('lawn_bp', __name__)


@lawn_bp.route('/')
def index():
    return render_template('lawn.html')


@lawn_bp.route('/book', methods=['GET', 'POST'])
def book():
    today = date.today().isoformat()
    if request.method == 'POST':
        event_type = request.form.get('event_type', '').strip()
        event_date_str = request.form.get('event_date', '')
        event_time = request.form.get('event_time', '')
        guest_count = request.form.get('guest_count', '0')
        veg_nonveg = request.form.get('veg_nonveg', 'Vegetarian')
        food_package = request.form.get('food_package', '')
        decoration_requirements = request.form.get('decoration_requirements', '')
        additional_requirements = request.form.get('additional_requirements', '')
        customer_name = request.form.get('customer_name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()

        if not event_type or not event_date_str or not customer_name or not phone:
            flash('Please fill in all required fields.', 'error')
            return render_template('lawn_booking.html', today=today)

        try:
            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('lawn_booking.html', today=today)

        guest_int = int(guest_count) if guest_count.isdigit() else 0
        estimated_quote = guest_int * 1250.0

        booking = LawnBooking(
            event_type=event_type,
            event_date=event_date,
            event_time=event_time,
            guest_count=guest_int,
            veg_nonveg=veg_nonveg,
            food_package=food_package,
            decoration_requirements=decoration_requirements,
            additional_requirements=additional_requirements,
            customer_name=customer_name,
            phone=phone,
            email=email,
            estimated_quote=estimated_quote,
        )
        db.session.add(booking)
        db.session.commit()

        flash(f'Lawn booking enquiry submitted! Your Reference ID: {booking.booking_id}', 'success')
        return redirect(url_for('booking_bp.check_status'))

    return render_template('lawn_booking.html', today=today)
