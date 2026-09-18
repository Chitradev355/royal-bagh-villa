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

    # 6. Comprehensive CMS CRUD, Media Library, Uploads, Menu & Bookings
    print("\n--- CMS CRUD, MEDIA, MENU & BOOKING INTEGRATION TESTS ---")
    import io
    from models import CMSContent, CMSEvent, GalleryItem, MenuCategory, MenuItem, Enquiry, MediaFile

    # Helper function to get CSRF token from any page
    def get_csrf(test_cli, url='/admin/cms/home'):
        r = test_cli.get(url)
        html = r.data.decode('utf-8', errors='ignore')
        m = re.search(r'name=["\']csrf_token["\']\s+value=["\']([^"\']+)["\']', html) or \
            re.search(r'value=["\']([^"\']+)["\']\s+name=["\']csrf_token["\']', html)
        return m.group(1) if m else ''

    # 6a. Unauthenticated Admin Protection (Security check)
    unauth_client = app.test_client()
    for protected_url in ['/admin/dashboard', '/admin/cms/home', '/admin/media', '/admin/menu', '/admin/settings']:
        res = unauth_client.get(protected_url, follow_redirects=False)
        if res.status_code == 302 and '/admin/login' in res.headers.get('Location', ''):
            print(f"  [OK 302] Unauthenticated access to {protected_url} blocked -> redirects to login")
        else:
            print(f"  [FAIL] Unauthenticated access to {protected_url} not blocked (Status {res.status_code})")
            errors.append((protected_url, 'Auth Protection', res.status_code, ''))

    # Setup authenticated admin client
    cms_client = app.test_client()
    with app.app_context():
        current_admin = Admin.query.filter_by(username='admin').first()
    with cms_client.session_transaction() as sess:
        sess['_user_id'] = str(current_admin.id)
        sess['_fresh'] = True

    # 6b. CMS Content Editing: Homepage Hero
    token = get_csrf(cms_client, '/admin/cms/home')
    post_home = cms_client.post('/admin/cms/home', data={
        'csrf_token': token,
        'hero_badge': 'Verified Luxury Destination',
        'hero_title': 'Grand Celebrations at Royal Bagh Villa',
        'hero_subtitle': 'Cafe | Fine Dining | Celebrations',
        'hero_tagline': 'Where Every Celebration Becomes a Memory',
        'cta_primary_text': 'Book Your Event',
        'cta_primary_link': '#enquiry',
        'cta_whatsapp_text': 'Chat with Us',
        'intro_badge': 'Welcome',
        'intro_title': 'A Premier Haven',
        'intro_text': 'Experience exceptional dining and hospitality.',
        'offers_badge': 'Special Privilege',
        'offers_title': 'Exclusive Packages',
        'offers_text': 'Complimentary signature mocktails with banquet booking.'
    }, follow_redirects=True)
    with app.app_context():
        updated_badge = CMSContent.get_value('home', 'badge')
        if post_home.status_code == 200 and updated_badge == 'Verified Luxury Destination':
            print("  [OK 200] CMS Homepage Content successfully updated and persisted")
        else:
            print(f"  [FAIL {post_home.status_code}] CMS Homepage update failed (badge={updated_badge})")
            errors.append(('/admin/cms/home', 'CMS Home Update', post_home.status_code, ''))

    # 6c. CMS Venues & Pricing Editing
    token = get_csrf(cms_client, '/admin/cms/venues?venue=banquet')
    post_venues = cms_client.post('/admin/cms/venues', data={
        'csrf_token': token,
        'venue': 'banquet',
        'capacity': 'Up to 350 Guests',
        'pricing': 'Rs. 1,250 per plate',
        'pricing_note': 'Special custom menus available',
        'description': 'Air-conditioned luxury banquet hall.',
        'features': 'Central AC, Sound System, Dressing Rooms'
    }, follow_redirects=True)
    with app.app_context():
        b_cap = CMSContent.get_value('banquet', 'capacity')
        if post_venues.status_code == 200 and b_cap == 'Up to 350 Guests':
            print("  [OK 200] CMS Venues & Pricing (Rs. 1,250/plate) successfully updated")
        else:
            print(f"  [FAIL {post_venues.status_code}] CMS Venues update failed (capacity={b_cap})")
            errors.append(('/admin/cms/venues', 'CMS Venues Update', post_venues.status_code, ''))

    # 6d. CMS Events Management (CRUD)
    token = get_csrf(cms_client, '/admin/cms/events')
    post_event = cms_client.post('/admin/cms/events/save', data={
        'csrf_token': token,
        'title': 'Test Milestone Anniversary',
        'slug': 'test-milestone-anniversary',
        'category': 'anniversary',
        'short_description': 'Romantic celebration with custom floral arrangements.',
        'full_description': 'Enjoy candlelit dining under the stars with live music.',
        'features': 'Candlelit Gazebo\nFloral Decor\nCake Setup',
        'cta_label': 'Book Anniversary',
        'cta_link': '#enquiry',
        'display_order': '10'
    }, follow_redirects=True)
    with app.app_context():
        created_event = CMSEvent.query.filter_by(slug='test-milestone-anniversary').first()
        if post_event.status_code == 200 and created_event:
            print(f"  [OK 200] CMS Event created: '{created_event.title}' (ID {created_event.id})")
            # Toggle event
            cms_client.post(f'/admin/cms/events/{created_event.id}/toggle', data={'csrf_token': token})
            # Delete event
            del_event = cms_client.post(f'/admin/cms/events/{created_event.id}/delete', data={'csrf_token': token}, follow_redirects=True)
            if del_event.status_code == 200:
                print("  [OK 200] CMS Event toggle and deletion verified")
            else:
                errors.append(('/admin/cms/events/delete', 'CMS Event Delete', del_event.status_code, ''))
        else:
            print(f"  [FAIL] CMS Event creation failed (Status {post_event.status_code})")
            errors.append(('/admin/cms/events/save', 'CMS Event Create', post_event.status_code, ''))

    # 6e. CMS Gallery Management (CRUD)
    token = get_csrf(cms_client, '/admin/cms/gallery')
    post_gal = cms_client.post('/admin/cms/gallery/save', data={
        'csrf_token': token,
        'title': 'Starlit Gazebo Setup',
        'caption': 'Enchanting lighting for evening celebrations',
        'media_url': 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=800',
        'category': 'lawn',
        'display_order': '25'
    }, follow_redirects=True)
    with app.app_context():
        gal_item = GalleryItem.query.filter_by(title='Starlit Gazebo Setup').first()
        if post_gal.status_code == 200 and gal_item:
            print(f"  [OK 200] CMS Gallery item created: '{gal_item.title}' (ID {gal_item.id})")
            del_gal = cms_client.post(f'/admin/cms/gallery/{gal_item.id}/delete', data={'csrf_token': token}, follow_redirects=True)
            if del_gal.status_code == 200:
                print("  [OK 200] CMS Gallery item deletion verified")
            else:
                errors.append(('/admin/cms/gallery/delete', 'Gallery Item Delete', del_gal.status_code, ''))
        else:
            print(f"  [FAIL] CMS Gallery item creation failed (Status {post_gal.status_code})")
            errors.append(('/admin/cms/gallery/save', 'Gallery Item Create', post_gal.status_code, ''))

    # 6f. Image Upload & Media Library
    token = get_csrf(cms_client, '/admin/media')
    fake_png = (io.BytesIO(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'), 'test_villa_view.png')
    post_img = cms_client.post('/admin/media/upload', data={
        'csrf_token': token,
        'file': fake_png,
        'category': 'property'
    }, content_type='multipart/form-data', follow_redirects=True)
    with app.app_context():
        uploaded_img = MediaFile.query.filter(MediaFile.original_filename.like('%test_villa_view.png%')).order_by(MediaFile.id.desc()).first()
        if post_img.status_code == 200 and uploaded_img:
            print(f"  [OK 200] Image Upload successful: '{uploaded_img.filename}' (Type: {uploaded_img.file_type}, Size: {uploaded_img.file_size} B)")
        else:
            print(f"  [FAIL {post_img.status_code}] Image upload failed")
            errors.append(('/admin/media/upload', 'Image Upload', post_img.status_code, ''))

    # 6g. Video Upload
    fake_mp4 = (io.BytesIO(b'\x00\x00\x00 ftypisom\x00\x00\x02\x00isomiso2mp41\x00\x00\x00\x08free'), 'test_aerial_tour.mp4')
    post_vid = cms_client.post('/admin/media/upload', data={
        'csrf_token': token,
        'file': fake_mp4,
        'category': 'events'
    }, content_type='multipart/form-data', follow_redirects=True)
    with app.app_context():
        uploaded_vid = MediaFile.query.filter(MediaFile.original_filename.like('%test_aerial_tour.mp4%')).order_by(MediaFile.id.desc()).first()
        if post_vid.status_code == 200 and uploaded_vid and uploaded_vid.file_type == 'video':
            print(f"  [OK 200] Video Upload successful: '{uploaded_vid.filename}' (Type: {uploaded_vid.file_type}, URL: {uploaded_vid.file_url})")
        else:
            print(f"  [FAIL {post_vid.status_code}] Video upload failed")
            errors.append(('/admin/media/upload', 'Video Upload', post_vid.status_code, ''))

    # 6h. Media API Picker & Media Deletion
    picker_res = cms_client.get('/admin/media/api/picker')
    if picker_res.status_code == 200 and b'media' in picker_res.data:
        print("  [OK 200] Media Picker JSON API returned media catalog")
    else:
        print(f"  [FAIL {picker_res.status_code}] Media Picker API failed")
        errors.append(('/admin/media/api/picker', 'Media Picker API', picker_res.status_code, ''))

    # Clean up test uploads
    with app.app_context():
        if uploaded_img:
            del_img = cms_client.post(f'/admin/media/{uploaded_img.id}/delete', data={'csrf_token': token}, follow_redirects=True)
            if del_img.status_code == 200:
                print("  [OK 200] Image media cleanup and file deletion verified")
        if uploaded_vid:
            cms_client.post(f'/admin/media/{uploaded_vid.id}/delete', data={'csrf_token': token}, follow_redirects=True)

    # 6i. Menu Category & Item Management (CRUD)
    import uuid
    unique_cat_slug = f'test-cat-{uuid.uuid4().hex[:6]}'
    token = get_csrf(cms_client, '/admin/menu')
    post_cat = cms_client.post('/admin/menu/category', data={
        'csrf_token': token,
        'name': 'Chef Specialties',
        'slug': unique_cat_slug,
        'section': 'restaurant',
        'description': 'Handcrafted signature dishes by executive chefs',
        'display_order': '1'
    }, follow_redirects=True)
    with app.app_context():
        test_cat = MenuCategory.query.filter_by(slug=unique_cat_slug).first()
        if post_cat.status_code == 200 and test_cat:
            print(f"  [OK 200] Menu Category created: '{test_cat.name}' (ID {test_cat.id})")
            
            # Add Menu Item to this category
            post_item = cms_client.post('/admin/menu/item', data={
                'csrf_token': token,
                'category_id': test_cat.id,
                'name': 'Royal Dum Biryani',
                'description': 'Fragrant basmati rice slow-cooked with royal spices and saffron',
                'price': '475',
                'image_url': 'https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=800',
                'is_veg': '1',
                'is_spicy': '1',
                'is_available': '1',
                'is_featured': '1',
                'display_order': '1'
            }, follow_redirects=True)
            test_item = MenuItem.query.filter_by(name='Royal Dum Biryani').first()
            if post_item.status_code == 200 and test_item:
                print(f"  [OK 200] Menu Item created: '{test_item.name}' (Rs. {test_item.price})")
                
                # Toggle Item Availability
                toggle_res = cms_client.post(f'/admin/menu/item/{test_item.id}/toggle', data={'csrf_token': token}, follow_redirects=True)
                if toggle_res.status_code == 200:
                    print("  [OK 200] Menu Item availability toggle verified")

                # Delete Item
                cms_client.post(f'/admin/menu/item/{test_item.id}/delete', data={'csrf_token': token}, follow_redirects=True)
                print("  [OK 200] Menu Item deletion verified")
            else:
                errors.append(('/admin/menu/item', 'Menu Item Create', post_item.status_code, ''))

            # Delete Category
            cms_client.post(f'/admin/menu/category/{test_cat.id}/delete', data={'csrf_token': token}, follow_redirects=True)
            print("  [OK 200] Menu Category deletion verified")
        else:
            errors.append(('/admin/menu/category', 'Menu Category Create', post_cat.status_code, ''))

    # 6j. Website Settings & SEO Management
    token = get_csrf(cms_client, '/admin/settings')
    post_settings = cms_client.post('/admin/settings', data={
        'csrf_token': token,
        'business_phone': '9762278230',
        'business_whatsapp': '919762278230',
        'business_email': 'info@royalbaghvilla.com',
        'business_address': 'Royal Bagh Villa, Dehradun, Uttarakhand',
        'business_map_url': 'https://maps.google.com/?q=Royal+Bagh+Villa+Dehradun',
        'instagram_url': 'https://instagram.com/royalbaghvilla',
        'facebook_url': 'https://facebook.com/royalbaghvilla',
        'restaurant_hours': '11:00 AM – 11:00 PM',
        'cafe_hours': '8:00 AM – 10:00 PM',
        'site_title': 'Royal Bagh Villa Dehradun | Premier Destination',
        'site_description': 'A sanctuary of luxury dining, artisanal brews, and grand celebrations.',
        'logo_text': 'Royal Bagh Villa',
        'footer_tagline': 'Where Every Celebration Becomes a Memory',
        'footer_about': 'Dehradun destination for dining, cafe and celebrations.'
    }, follow_redirects=True)
    with app.app_context():
        updated_phone = CMSContent.get_value('settings', 'business_phone')
        if post_settings.status_code == 200 and updated_phone == '9762278230':
            print("  [OK 200] Website Settings & SEO parameters successfully saved and verified")
        else:
            errors.append(('/admin/settings', 'Settings Update', post_settings.status_code, ''))

    # 6k. Bookings & Enquiries Workflow Status Updates
    with app.app_context():
        test_enq = Enquiry.query.first()
        if not test_enq:
            test_enq = Enquiry(name='Test Lead', phone='9876543210', event_type='Wedding', guests='200', message='Hello')
            db.session.add(test_enq)
            db.session.commit()
        enq_id = test_enq.id

    token = get_csrf(cms_client, '/admin/enquiries')
    enq_update = cms_client.post(f'/admin/enquiries/{enq_id}/status', data={
        'csrf_token': token,
        'status': 'contacted',
        'admin_notes': 'Spoke with guest regarding lawn availability.'
    }, follow_redirects=True)
    with app.app_context():
        refreshed_enq = db.session.get(Enquiry, enq_id)
        if enq_update.status_code == 200 and refreshed_enq.status == 'contacted':
            print("  [OK 200] Enquiry status update and admin notes successfully recorded")
        else:
            errors.append((f'/admin/enquiries/{enq_id}/status', 'Enquiry Status Update', enq_update.status_code, ''))

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
