from flask import Blueprint, render_template, request, redirect, url_for
from models import FoodOrder, BanquetBooking, LawnBooking, RoomBooking

booking_bp = Blueprint('booking_bp', __name__)

@booking_bp.route('/', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        
        # Check Food Order
        order = FoodOrder.query.filter((FoodOrder.order_id == query) | (FoodOrder.customer_phone == query)).first()
        if order:
            return redirect(url_for('booking_bp.result', type='food', id=order.order_id))
            
        # Check Banquet
        banquet = BanquetBooking.query.filter((BanquetBooking.booking_id == query) | (BanquetBooking.phone == query)).first()
        if banquet:
            return redirect(url_for('booking_bp.result', type='banquet', id=banquet.booking_id))
            
        # Check Lawn
        lawn = LawnBooking.query.filter((LawnBooking.booking_id == query) | (LawnBooking.phone == query)).first()
        if lawn:
            return redirect(url_for('booking_bp.result', type='lawn', id=lawn.booking_id))
            
        # Check Room
        room = RoomBooking.query.filter((RoomBooking.booking_id == query) | (RoomBooking.phone == query)).first()
        if room:
            return redirect(url_for('booking_bp.result', type='room', id=room.booking_id))
            
        return render_template('check_status.html', error="No booking found with that ID or Phone number.")
        
    return render_template('check_status.html')

@booking_bp.route('/result')
def result():
    b_type = request.args.get('type')
    b_id = request.args.get('id')
    
    booking_details = None
    
    if b_type == 'food':
        booking_details = FoodOrder.query.filter_by(order_id=b_id).first()
    elif b_type == 'banquet':
        booking_details = BanquetBooking.query.filter_by(booking_id=b_id).first()
    elif b_type == 'lawn':
        booking_details = LawnBooking.query.filter_by(booking_id=b_id).first()
    elif b_type == 'room':
        booking_details = RoomBooking.query.filter_by(booking_id=b_id).first()
        
    if not booking_details:
        return redirect(url_for('booking_bp.check_status'))
        
    return render_template('check_status.html', result=booking_details, type=b_type)
