from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import db, MenuItem, Enquiry
from datetime import datetime

main_bp = Blueprint('main_bp', __name__)


@main_bp.route('/')
def index():
    featured_items = MenuItem.query.filter_by(is_featured=True, is_available=True).limit(4).all()
    return render_template('index.html', featured_items=featured_items)


@main_bp.route('/enquiry', methods=['POST'])
def enquiry():
    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    event_type = request.form.get('event_type', '').strip()
    event_date = request.form.get('event_date', '').strip()
    guests = request.form.get('guests', '').strip()
    message = request.form.get('message', '').strip()

    if not name or not phone:
        flash('Please provide your name and phone number to send an enquiry.', 'error')
        return redirect(url_for('main_bp.index') + '#enquiry')

    subject = f"Enquiry for {event_type or 'Celebration'} on {event_date or 'TBD'} ({guests or 'TBD'} guests)"
    full_message = (
        f"Event Type: {event_type}\n"
        f"Event Date: {event_date}\n"
        f"Guests: {guests}\n\n"
        f"Notes/Requirements:\n{message}"
    )

    new_enquiry = Enquiry(
        name=name,
        phone=phone,
        subject=subject,
        message=full_message,
        enquiry_type=f"Event: {event_type}" if event_type else "General Event",
    )
    db.session.add(new_enquiry)
    db.session.commit()

    flash('Thank you! Your celebration enquiry has been received. Our team will contact you shortly.', 'success')
    return redirect(url_for('main_bp.index') + '#enquiry')


@main_bp.route('/events')
def events():
    return render_template('events.html')


@main_bp.route('/gallery')
def gallery():
    return render_template('gallery.html')


@main_bp.route('/about')
def about():
    return render_template('about.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        enquiry_type = request.form.get('enquiry_type', 'general')

        if not name or not phone:
            flash('Please provide your name and phone number.', 'error')
            return redirect(url_for('main_bp.contact'))

        new_enquiry = Enquiry(
            name=name,
            phone=phone,
            email=email,
            subject=subject or "General Contact Enquiry",
            message=message,
            enquiry_type=enquiry_type,
        )
        db.session.add(new_enquiry)
        db.session.commit()

        flash('Thank you for contacting Royal Bagh Villa. We will get back to you shortly.', 'success')
        return redirect(url_for('main_bp.contact'))

    return render_template('contact.html')


@main_bp.route('/parking')
def parking():
    return redirect(url_for('main_bp.index') + '#parking')
