from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, FoodOrder, OrderItem

order_bp = Blueprint('order_bp', __name__)


@order_bp.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    # Compute derived values for each item
    for item in cart_items:
        item['unit_price'] = item.get('price', 0)
        item['subtotal'] = item.get('price', 0) * item.get('quantity', 1)

    subtotal = sum(i.get('subtotal', 0) for i in cart_items)
    taxes = round(subtotal * 0.05, 2)
    total = round(subtotal + taxes, 2)

    return render_template('cart.html', subtotal=subtotal, taxes=taxes, total=total)


@order_bp.route('/checkout')
def checkout():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('restaurant_bp.index'))

    for item in cart_items:
        item['unit_price'] = item.get('price', 0)
        item['subtotal'] = item.get('price', 0) * item.get('quantity', 1)

    subtotal = sum(i.get('subtotal', 0) for i in cart_items)
    taxes = round(subtotal * 0.05, 2)
    total = round(subtotal + taxes, 2)

    return render_template('checkout.html', subtotal=subtotal, taxes=taxes, total=total)


@order_bp.route('/place', methods=['POST'])
def place_order():
    cart_items = session.get('cart', [])
    if not cart_items:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('restaurant_bp.index'))

    customer_name = request.form.get('customer_name', '').strip()
    customer_phone = request.form.get('customer_phone', '').strip()
    customer_email = request.form.get('customer_email', '').strip()
    order_type = request.form.get('order_type', 'dine_in')
    room_number = request.form.get('room_number', '').strip()
    table_number = request.form.get('table_number', '').strip()
    notes = request.form.get('notes', '').strip()
    payment_mode = request.form.get('payment_mode', 'pay_at_venue')

    if not customer_name or not customer_phone:
        flash('Please provide your name and phone number.', 'error')
        return redirect(url_for('order_bp.checkout'))

    total_amount = sum(item['price'] * item['quantity'] for item in cart_items)

    new_order = FoodOrder(
        customer_name=customer_name,
        customer_phone=customer_phone,
        customer_email=customer_email,
        order_type=order_type,
        room_number=room_number,
        table_number=table_number,
        notes=notes,
        total_amount=total_amount,
        payment_mode=payment_mode,
    )
    db.session.add(new_order)
    db.session.flush()

    for item in cart_items:
        order_item = OrderItem(
            order_id=new_order.id,
            menu_item_id=item['item_id'],
            quantity=item['quantity'],
            unit_price=item['price'],
            subtotal=item['price'] * item['quantity'],
        )
        db.session.add(order_item)

    db.session.commit()
    session['cart'] = []

    flash(f'Order placed successfully! Your Order ID: {new_order.order_id}', 'success')
    return redirect(url_for('order_bp.tracking', order_id=new_order.order_id))


@order_bp.route('/tracking/<order_id>')
def tracking(order_id):
    order = FoodOrder.query.filter_by(order_id=order_id).first_or_404()
    return render_template('order_tracking.html', order=order)
