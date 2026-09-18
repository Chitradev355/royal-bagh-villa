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

    # 4. Test CSRF Protection & Admin Authentication Flow
    print("\n--- CSRF & ADMIN AUTHENTICATION REGRESSION TESTS ---")
    import re
    auth_client = app.test_client()

    # A. GET /admin/login loads form & generates valid CSRF token
    login_page_res = auth_client.get('/admin/login')
    if login_page_res.status_code == 200:
        html_text = login_page_res.data.decode('utf-8')
        match = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html_text) or \
                re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html_text)
        if match and len(match.group(1)) > 10:
            csrf_token = match.group(1)
            print(f"  [OK 200] GET /admin/login renders form with CSRF token: {csrf_token[:15]}...")
        else:
            print("  [FAIL] CSRF token missing or invalid in login form HTML")
            errors.append(('/admin/login', 'CSRF Token in Login HTML', 'MISSING', ''))
    else:
        print(f"  [FAIL {login_page_res.status_code}] GET /admin/login")
        errors.append(('/admin/login', 'GET /admin/login', login_page_res.status_code, ''))

    # B. POST /admin/login WITHOUT CSRF token must return 400 Bad Request
    no_csrf_client = app.test_client()
    bad_req_res = no_csrf_client.post('/admin/login', data={'username': 'admin', 'password': 'wrongpassword'})
    if bad_req_res.status_code == 400:
        print("  [OK 400] POST /admin/login without CSRF token correctly rejected (CSRF protection active)")
    else:
        print(f"  [FAIL {bad_req_res.status_code}] Expected 400 without CSRF token")
        errors.append(('/admin/login', 'CSRF Protection Enforcement', bad_req_res.status_code, ''))

    # C. POST /admin/login WITH invalid credentials and valid CSRF token
    invalid_login_res = auth_client.post('/admin/login', data={
        'csrf_token': csrf_token,
        'username': 'admin',
        'password': 'wrong_password_test'
    }, follow_redirects=True)
    if invalid_login_res.status_code == 200 and "Invalid username or password" in invalid_login_res.data.decode('utf-8'):
        print("  [OK 200] POST /admin/login with invalid credentials returns expected flash error")
    else:
        print(f"  [FAIL {invalid_login_res.status_code}] Invalid login did not display error flash message")
        errors.append(('/admin/login', 'Invalid Login Handling', invalid_login_res.status_code, ''))

    # D. POST /admin/login WITH valid credentials and valid CSRF token
    login_page_res2 = auth_client.get('/admin/login')
    html_text2 = login_page_res2.data.decode('utf-8')
    match2 = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html_text2) or \
             re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html_text2)
    csrf_token2 = match2.group(1)

    login_success_res = auth_client.post('/admin/login', data={
        'csrf_token': csrf_token2,
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=False)
    if login_success_res.status_code == 302 and '/admin/dashboard' in login_success_res.headers.get('Location', ''):
        print("  [OK 302] POST /admin/login with valid credentials successfully redirects to dashboard")
    else:
        print(f"  [FAIL {login_success_res.status_code}] Successful login redirect failed")
        errors.append(('/admin/login', 'Valid Login Redirect', login_success_res.status_code, ''))

    # E. Access dashboard with authenticated session
    dash_res = auth_client.get('/admin/dashboard')
    if dash_res.status_code == 200:
        print("  [OK 200] Authenticated session successfully accessed /admin/dashboard")
    else:
        print(f"  [FAIL {dash_res.status_code}] Access to dashboard failed after login")
        errors.append(('/admin/dashboard', 'Authenticated Dashboard Access', dash_res.status_code, ''))

    # F. Logout
    logout_res = auth_client.get('/admin/logout', follow_redirects=False)
    if logout_res.status_code == 302 and '/admin/login' in logout_res.headers.get('Location', ''):
        print("  [OK 302] GET /admin/logout successfully redirects to /admin/login")
    else:
        print(f"  [FAIL {logout_res.status_code}] Logout redirect failed")
        errors.append(('/admin/logout', 'Admin Logout', logout_res.status_code, ''))

    # G. Dashboard blocked after logout
    dash_blocked = auth_client.get('/admin/dashboard', follow_redirects=False)
    if dash_blocked.status_code == 302 and '/admin/login' in dash_blocked.headers.get('Location', ''):
        print("  [OK 302] Accessing /admin/dashboard after logout correctly redirects to /admin/login")
    else:
        print(f"  [FAIL {dash_blocked.status_code}] Dashboard was not blocked after logout")
        errors.append(('/admin/dashboard', 'Post-Logout Dashboard Block', dash_blocked.status_code, ''))

    # H. Verify HTTPS Reverse Proxy / ProxyFix login on Render
    proxy_client = app.test_client()
    proxy_res = proxy_client.get('/admin/login', environ_base={
        'HTTP_X_FORWARDED_PROTO': 'https',
        'HTTP_X_FORWARDED_HOST': 'royalbagh.com'
    })
    if proxy_res.status_code == 200:
        html_proxy = proxy_res.data.decode('utf-8')
        match_proxy = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html_proxy) or \
                      re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html_proxy)
        if match_proxy:
            proxy_csrf = match_proxy.group(1)
            proxy_post = proxy_client.post('/admin/login', data={
                'csrf_token': proxy_csrf,
                'username': 'admin',
                'password': 'admin123'
            }, environ_base={
                'HTTP_X_FORWARDED_PROTO': 'https',
                'HTTP_X_FORWARDED_HOST': 'royalbagh.com',
                'HTTP_REFERER': 'https://royalbagh.com/admin/login'
            }, follow_redirects=False)
            if proxy_post.status_code == 302:
                print("  [OK 302] HTTPS reverse proxy (X-Forwarded-Proto/Host) login succeeds (ProxyFix verified)")
            else:
                print(f"  [FAIL {proxy_post.status_code}] HTTPS reverse proxy login failed")
                errors.append(('/admin/login', 'HTTPS Proxy Login', proxy_post.status_code, ''))

    # 5. Test Password Integrity & Invalid Salt Safety
    print("\n--- PASSWORD INTEGRITY & INVALID SALT SAFETY TESTS ---")
    with app.app_context():
        test_admin = Admin.query.filter_by(username='admin').first()
        original_hash = test_admin.password_hash

        # 5a. Corrupt / invalid salt hash test
        test_admin.password_hash = "$2a$invalid_salt_corrupted_value"
        try:
            result = test_admin.check_password("admin123")
            if result is False:
                print("  [OK] Corrupt hash check_password safely returns False without raising ValueError: Invalid salt")
            else:
                print("  [FAIL] Corrupt hash check_password returned True unexpectedly")
                errors.append(('password_check', 'Corrupt Hash', 'UNEXPECTED_TRUE', ''))
        except ValueError as e:
            print(f"  [FAIL] check_password raised ValueError: {e}")
            errors.append(('password_check', 'Corrupt Hash', 'VALUE_ERROR', str(e)))

        # 5b. Corrupt hash during login request returns 200 with flash error instead of 500
        db.session.commit()
    
    corrupt_login_client = app.test_client()
    c_page = corrupt_login_client.get('/admin/login')
    c_html = c_page.data.decode('utf-8')
    c_csrf = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', c_html).group(1)
    c_resp = corrupt_login_client.post('/admin/login', data={
        'csrf_token': c_csrf,
        'username': 'admin',
        'password': 'admin123'
    }, follow_redirects=True)
    if c_resp.status_code == 200 and "Invalid username or password" in c_resp.data.decode('utf-8'):
        print("  [OK 200] Corrupt hash during login safely flashes error without 500 server crash")
    else:
        print(f"  [FAIL {c_resp.status_code}] Corrupt hash login caused failure or crash")
        errors.append(('/admin/login', 'Corrupt Hash Login Safety', c_resp.status_code, ''))

    # 5c. Seeder self-healing test: repairs corrupt hash
    from utils.cms_seeder import seed_cms_defaults
    with app.app_context():
        seed_cms_defaults()
        healed_admin = Admin.query.filter_by(username='admin').first()
        if healed_admin.password_hash.startswith(('scrypt:', 'pbkdf2:')) and healed_admin.check_password('admin123'):
            print("  [OK] Superadmin seeder successfully detected and repaired corrupt hash with valid Werkzeug hash")
        else:
            print("  [FAIL] Seeder failed to heal corrupt admin password hash")
            errors.append(('seeder', 'Heal Corrupt Hash', 'HEAL_FAILED', ''))

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
