import sys
from app import app
from models import db, Admin, Room

def test_all():
    print("=" * 60)
    print("ROYAL BAGH VILLA — COMPREHENSIVE ROUTE VERIFICATION")
    print("=" * 60)

    client = app.test_client()

    with app.app_context():
        # Get a room slug for testing
        room = Room.query.first()
        room_slug = room.slug if room else "royal-suite"

    # 1. Test Public Customer Pages
    public_pages = [
        ('/', 'Homepage'),
        ('/cafe', 'Cafe Page'),
        ('/restaurant', 'Restaurant Page'),
        ('/events', 'Events Page'),
        ('/gallery', 'Gallery Page'),
        ('/about', 'About Page'),
        ('/lawn', 'Lawn Page'),
        ('/lawn/book', 'Lawn Booking Form'),
        ('/banquet', 'Banquet Page'),
        ('/banquet/book', 'Banquet Booking Form'),
        ('/stay', 'Stay / Rooms Page'),
        (f'/stay/{room_slug}', 'Room Detail Page'),
        (f'/stay/book/{room_slug}', 'Room Booking Form'),
        ('/check-status', 'Check Status Page'),
        ('/contact', 'Contact Page'),
        ('/order/cart', 'Cart Page'),
        ('/admin/login', 'Admin Login Page'),
    ]

    errors = []

    print("\n--- PUBLIC PAGES ---")
    for path, name in public_pages:
        try:
            res = client.get(path)
            if res.status_code == 200:
                print(f"  [OK 200] {name:25s} -> {path}")
            else:
                print(f"  [FAIL {res.status_code}] {name:25s} -> {path}")
                errors.append((path, name, res.status_code, res.data[:300].decode('utf-8', errors='ignore')))
        except Exception as e:
            print(f"  [EXCEPTION] {name:25s} -> {path}: {e}")
            errors.append((path, name, 'EXCEPTION', str(e)))

    # 2. Test Admin Authentication and Protected Pages
    print("\n--- ADMIN PROTECTED PAGES ---")
    with app.app_context():
        admin = Admin.query.filter_by(username='admin').first()
        if not admin:
            print("Admin user not found. Creating test admin...")
            admin = Admin(username='admin', name='Admin', role='superadmin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()

    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin.id)
        sess['_fresh'] = True

    admin_pages = [
        ('/admin/dashboard', 'Admin Dashboard'),
        ('/admin/orders', 'Admin Orders'),
        ('/admin/menu', 'Admin Menu'),
        ('/admin/banquet', 'Admin Banquet Bookings'),
        ('/admin/lawn', 'Admin Lawn Bookings'),
        ('/admin/rooms', 'Admin Rooms'),
        ('/admin/room-bookings', 'Admin Room Bookings'),
        ('/admin/enquiries', 'Admin Enquiries'),
        ('/admin/settings', 'Admin Settings'),
        ('/admin/media', 'Admin Media Library'),
        ('/admin/media/api/picker', 'Admin Media API Picker'),
        ('/admin/cms/home', 'Admin CMS Home'),
        ('/admin/cms/pages', 'Admin CMS Pages'),
        ('/admin/cms/venues', 'Admin CMS Venues'),
        ('/admin/cms/events', 'Admin CMS Events'),
        ('/admin/cms/gallery', 'Admin CMS Gallery'),
        ('/admin/cms/navigation', 'Admin CMS Navigation'),
        ('/admin/backup/export', 'Admin Backup Export'),
    ]

    for path, name in admin_pages:
        try:
            res = client.get(path)
            if res.status_code == 200:
                print(f"  [OK 200] {name:25s} -> {path}")
            else:
                print(f"  [FAIL {res.status_code}] {name:25s} -> {path}")
                errors.append((path, name, res.status_code, res.data[:300].decode('utf-8', errors='ignore')))
        except Exception as e:
            print(f"  [EXCEPTION] {name:25s} -> {path}: {e}")
            errors.append((path, name, 'EXCEPTION', str(e)))

    # 3. Test Form Submissions (Enquiry, Cart, etc.)
    print("\n--- FORM & ACTION WORKFLOWS ---")
    
    # Test Enquiry Submission
    enquiry_res = client.post('/enquiry', data={
        'name': 'Test Guest',
        'phone': '9876543210',
        'event_type': 'Wedding / Reception',
        'event_date': '2026-11-20',
        'guests': '250',
        'message': 'Looking for banquet and lawn celebration package.'
    }, follow_redirects=True)
    if enquiry_res.status_code == 200:
        print("  [OK 200] Event Enquiry Submission -> /enquiry")
    else:
        print(f"  [FAIL {enquiry_res.status_code}] Event Enquiry Submission")
        errors.append(('/enquiry', 'Enquiry Submission', enquiry_res.status_code, ''))

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"FAILED: {len(errors)} page(s) failed.")
        for path, name, code, snippet in errors:
            print(f"  - {name} ({path}): {code}\n    {snippet[:200]}")
        sys.exit(1)
    else:
        print("ALL PAGES AND FLOWS RETURNED HTTP 200! ZERO JINJA ERRORS!")
        print("=" * 60)

if __name__ == '__main__':
    test_all()
