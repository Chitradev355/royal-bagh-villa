from flask import Blueprint, request, jsonify, session
from models import db, MenuItem, MenuCategory, FoodOrder, BanquetBooking, LawnBooking, RoomBooking

api_bp = Blueprint('api_bp', __name__)

@api_bp.route('/menu', methods=['GET'])
def get_menu():
    category_id = request.args.get('category')
    section = request.args.get('section')
    
    query = MenuItem.query.filter_by(is_available=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if section:
        query = query.join(MenuCategory).filter(MenuCategory.section == section)
        
    items = query.all()
    return jsonify([{
        'id': i.id,
        'name': i.name,
        'price': i.price,
        'description': i.description,
        'image_url': i.image_url,
        'is_veg': i.is_veg
    } for i in items])

@api_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    data = request.json
    item_id = data.get('item_id')
    
    item = MenuItem.query.get_or_404(item_id)
    
    if 'cart' not in session:
        session['cart'] = []
        
    cart = session['cart']
    # Check if item exists in cart
    for cart_item in cart:
        if cart_item['item_id'] == item_id:
            cart_item['quantity'] += 1
            session.modified = True
            return jsonify({'success': True, 'cart': cart, 'message': 'Quantity updated'})
            
    # Add new item
    cart.append({
        'item_id': item.id,
        'name': item.name,
        'price': item.price,
        'quantity': 1,
        'image_url': item.image_url,
        'is_veg': item.is_veg
    })
    session.modified = True
    return jsonify({'success': True, 'cart': cart, 'message': 'Item added to cart'})

@api_bp.route('/cart/update', methods=['POST'])
def update_cart():
    data = request.json
    item_id = data.get('item_id')
    quantity = data.get('quantity')
    
    if 'cart' in session:
        cart = session['cart']
        for item in cart:
            if item['item_id'] == item_id:
                if quantity > 0:
                    item['quantity'] = quantity
                else:
                    cart.remove(item)
                session.modified = True
                return jsonify({'success': True, 'cart': cart})
                
    return jsonify({'success': False, 'message': 'Item not found in cart'})

@api_bp.route('/cart/remove/<int:item_id>', methods=['DELETE'])
def remove_from_cart(item_id):
    if 'cart' in session:
        cart = session['cart']
        session['cart'] = [item for item in cart if item['item_id'] != item_id]
        session.modified = True
        return jsonify({'success': True, 'cart': session['cart']})
    return jsonify({'success': False})

@api_bp.route('/cart', methods=['GET'])
def get_cart():
    return jsonify(session.get('cart', []))

@api_bp.route('/cart/clear', methods=['POST'])
def clear_cart():
    session['cart'] = []
    session.modified = True
    return jsonify({'success': True})

@api_bp.route('/order/<order_id>', methods=['GET'])
def get_order_status(order_id):
    order = FoodOrder.query.filter_by(order_id=order_id).first()
    if order:
        return jsonify({'status': order.status, 'total': order.total_amount})
    return jsonify({'error': 'Not found'}), 404

@api_bp.route('/status/<booking_id>', methods=['GET'])
def get_booking_status(booking_id):
    if booking_id.startswith('ORD'):
        obj = FoodOrder.query.filter_by(order_id=booking_id).first()
    elif booking_id.startswith('BNQ'):
        obj = BanquetBooking.query.filter_by(booking_id=booking_id).first()
    elif booking_id.startswith('LWN'):
        obj = LawnBooking.query.filter_by(booking_id=booking_id).first()
    elif booking_id.startswith('RM'):
        obj = RoomBooking.query.filter_by(booking_id=booking_id).first()
    else:
        return jsonify({'error': 'Invalid ID prefix'}), 400
        
    if obj:
        return jsonify({'status': obj.status})
    return jsonify({'error': 'Not found'}), 404

@api_bp.route('/rooms/availability', methods=['GET'])
def check_availability():
    # Placeholder for actual logic
    return jsonify({'available': True})
