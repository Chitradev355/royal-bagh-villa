import json
import os
from models import db, Admin, CMSContent, CMSEvent, GalleryItem, NavigationItem

def seed_cms_defaults():
    # 0. Ensure Superadmin account exists and has a valid password hash
    admin_user = Admin.query.first()
    if admin_user is None:
        admin_user = Admin(
            username=os.environ.get('ADMIN_USERNAME', 'admin'),
            name='Royal Bagh Villa Admin',
            role='superadmin'
        )
        admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin_user)
        db.session.commit()
    else:
        # Check if the existing admin's password hash is corrupt or invalid
        is_invalid_or_corrupt = False
        if not admin_user.password_hash:
            is_invalid_or_corrupt = True
        elif not admin_user.password_hash.startswith(('scrypt:', 'pbkdf2:')):
            # Not a standard Werkzeug hash — test if it's a valid legacy bcrypt hash or corrupt
            try:
                import bcrypt
                bcrypt.checkpw(b"probe_salt", admin_user.password_hash.encode("utf-8"))
            except ValueError:
                # Malformed salt or 'Invalid salt' error
                is_invalid_or_corrupt = True
            except Exception:
                is_invalid_or_corrupt = True

        if is_invalid_or_corrupt:
            admin_user.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            db.session.commit()

    # 1. Navigation items
    if NavigationItem.query.count() == 0:
        nav_items = [
            ('Home', '/', 1),
            ('Cafe', '/cafe', 2),
            ('Restaurant', '/restaurant', 3),
            ('Events', '/events', 4),
            ('Banquet', '/banquet', 5),
            ('Lawn', '/lawn', 6),
            ('Gallery', '/gallery', 7),
            ('About', '/about', 8),
            ('Contact', '/contact', 9),
        ]
        for label, url, order in nav_items:
            nav = NavigationItem(label=label, url=url, display_order=order, is_visible=True)
            db.session.add(nav)

    # 2. CMS Events
    if CMSEvent.query.count() == 0:
        events_data = [
            {
                'title': 'Weddings & Receptions',
                'slug': 'weddings-receptions',
                'category': 'wedding',
                'short_description': 'Opulent open-lawn or banquet stages with grand dining spreads, fairy lights, and regal ambiance.',
                'full_description': 'Royal Bagh Villa offers an enchanting setting for your dream wedding. From traditional Haldi and Mehendi rituals to grand Sangeet and wedding receptions, our dedicated event team manages decor, gourmet multi-cuisine catering, stage setup, and seamless guest hospitality.',
                'cover_image': 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=800&q=80',
                'features': ['Capacity: 50 to 500+ Guests', 'Lawn & Indoor Banquet Combination', 'Dedicated Dressing Suites', 'Multi-Cuisine Catering', 'Valet Parking for 25+ Cars'],
                'cta_label': 'Plan Your Wedding',
                'cta_link': '#enquiry',
                'display_order': 1
            },
            {
                'title': 'Birthday Celebrations',
                'slug': 'birthday-celebrations',
                'category': 'birthday',
                'short_description': 'Customized themes, music, cake cutting, dynamic lighting, and gourmet catering for memorable birthdays.',
                'full_description': 'Celebrate your birthday or surprise a loved one with an unforgettable party at Royal Bagh Villa with personalized styling, cake cutting stages, and live food counters.',
                'cover_image': 'https://images.unsplash.com/photo-1464349095431-e9a21285b5f3?w=800&q=80',
                'features': ['Custom Birthday Themes & Styling', 'Cake Cutting Stages', 'DJ & Sound System Setup', 'Kids & Adult Menu Packages', 'Indoor and Outdoor Options'],
                'cta_label': 'Book Birthday Party',
                'cta_link': '#enquiry',
                'display_order': 2
            },
            {
                'title': 'Kitty Parties & High Teas',
                'slug': 'kitty-parties',
                'category': 'kitty',
                'short_description': 'Sophisticated private cafe & restaurant setups with artisanal high tea, appetizers, and warm conversations.',
                'full_description': 'Host your friends and social circles in our stylish private dining sections or shaded open cafe gardens with artisanal high teas, appetizers, and dedicated butler service.',
                'cover_image': 'https://images.unsplash.com/photo-1543007630-9710e4a00a20?w=800&q=80',
                'features': ['Exclusive Private Dining Space', 'Artisanal High Tea & Mocktails', 'Customized Starters', 'Relaxed Cozy Seating', 'Photo Booth & Selfie Corners'],
                'cta_label': 'Plan Kitty Party',
                'cta_link': '#enquiry',
                'display_order': 3
            },
            {
                'title': 'Anniversary Celebrations',
                'slug': 'anniversary-celebrations',
                'category': 'anniversary',
                'short_description': 'Intimate candlelit dinners or banquet gatherings to celebrate love and lifelong milestones.',
                'full_description': 'Honor another year of love with romantic candlelit dinners under the stars, or gather family and friends for an anniversary celebration complete with live music, floral arches, and personalized dining menus.',
                'cover_image': 'https://images.unsplash.com/photo-1529636798458-92182e662485?w=800&q=80',
                'features': ['Candlelit Gazebo Setups', 'Floral Centerpieces & Decor', 'Personalized Anniversary Cakes', 'Romantic Background Music', 'Custom Chef Degustation Menus'],
                'cta_label': 'Celebrate Anniversary',
                'cta_link': '#enquiry',
                'display_order': 4
            },
            {
                'title': 'Corporate Events & Meets',
                'slug': 'corporate-events',
                'category': 'corporate',
                'short_description': 'Professional conferences, annual company meets, awards nights, and team celebrations with full AV support.',
                'full_description': 'Impress your colleagues, clients, and partners at Royal Bagh Villa. Our air-conditioned banquet hall is equipped with modern audiovisual facilities, high-speed Wi-Fi, presentation screens, and formal luncheon or dinner catering.',
                'cover_image': 'https://images.unsplash.com/photo-1511578314322-379afb476865?w=800&q=80',
                'features': ['High-Definition Projectors & Screens', 'Wireless Microphones & Podiums', 'Executive High Tea & Buffet Menus', 'Quiet Professional Atmosphere', 'Ample Parking Space'],
                'cta_label': 'Organize Conference',
                'cta_link': '#enquiry',
                'display_order': 5
            },
            {
                'title': 'Cocktail & Private Parties',
                'slug': 'private-parties',
                'category': 'party',
                'short_description': 'Exclusive reservation of spaces with complete privacy, vibrant music, and personalized menus.',
                'full_description': 'Whether celebrating a promotion, retirement, reunion, or an energetic cocktail evening, reserve Royal Bagh Villa for a private gathering with mood lighting, barbeque grills, mocktails, and culinary spreads.',
                'cover_image': 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=800&q=80',
                'features': ['Private Venue Reservation', 'Live Grills & Barbeque Stations', 'Custom Bar & Mocktail Counters', 'Vibrant Party Sound & Lights', 'Security & Dedicated Service Staff'],
                'cta_label': 'Book Private Party',
                'cta_link': '#enquiry',
                'display_order': 6
            }
        ]
        for ed in events_data:
            ev = CMSEvent(
                title=ed['title'],
                slug=ed['slug'],
                category=ed['category'],
                short_description=ed['short_description'],
                full_description=ed['full_description'],
                cover_image=ed['cover_image'],
                cta_label=ed['cta_label'],
                cta_link=ed['cta_link'],
                display_order=ed['display_order'],
                is_active=True
            )
            ev.features = ed['features']
            db.session.add(ev)

    # 3. Gallery Items
    if GalleryItem.query.count() == 0:
        gallery_data = [
            ('Grand Celebration Lawn', 'Lush manicured grass and starlit open-sky venue for receptions and parties.', 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=900&q=80', 'lawn', 1),
            ('Artisanal Coffee & Conversations', 'Cozy aesthetic seating and freshly brewed specialty coffees.', 'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=900&q=80', 'cafe', 2),
            ('Gourmet Platter & Dining', 'Fresh regional and international dishes prepared by master chefs.', 'https://images.unsplash.com/photo-1544025162-d76694265947?w=900&q=80', 'restaurant', 3),
            ('Banquet Hall Evening Gala', 'Crystal chandeliers and regal banquet styling for celebratory milestones.', 'https://images.unsplash.com/photo-1511578314322-379afb476865?w=900&q=80', 'banquet', 4),
            ('Open-Sky Wedding Setup', 'Floral arches, fairy light canopies, and celebratory seating.', 'https://images.unsplash.com/photo-1464366400600-7168b8af9bc3?w=900&q=80', 'events', 5),
            ('Artisanal Brew & Bakery', 'Handcrafted desserts and seasonal beverage concoctions.', 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=900&q=80', 'cafe', 6),
            ('Royal Dining Ambience', 'Warm gold and wood interiors designed for fine family dining.', 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=900&q=80', 'restaurant', 7),
            ('Scenic Mountain View Property', 'Nestled amidst Dehradun landscapes with serene mountain breezes.', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=900&q=80', 'property', 8)
        ]
        for title, caption, url, cat, order in gallery_data:
            g = GalleryItem(title=title, caption=caption, media_url=url, category=cat, display_order=order, is_featured=True)
            db.session.add(g)

    # 4. CMS Page Contents
    cms_defaults = [
        # Homepage
        ('home', 'hero', 'badge', "Dehradun's Premier Destination", 'text', 'Hero Badge'),
        ('home', 'hero', 'title', "Where Every Celebration <br class='hidden sm:inline'><span class='text-[#C9A96E] italic font-normal'>Becomes a Memory.</span>", 'html', 'Hero Main Title'),
        ('home', 'hero', 'subtitle', 'Cafe ? Restaurant ? Events ? Celebrations', 'text', 'Hero Subtitle'),
        ('home', 'hero', 'tagline', 'A premium destination in Dehradun for dining, celebrations, weddings, parties and unforgettable moments.', 'text', 'Hero Tagline Description'),
        ('home', 'hero', 'image', 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=1920&q=85', 'image', 'Hero Background Image'),
        ('home', 'hero', 'video_url', '', 'video', 'Hero Background Video (Optional)'),
        ('home', 'hero', 'cta_primary_text', 'Check Availability', 'text', 'Hero Primary Button Text'),
        ('home', 'hero', 'cta_primary_link', '#enquiry', 'text', 'Hero Primary Button Link'),
        ('home', 'hero', 'cta_whatsapp_text', 'WhatsApp Us', 'text', 'Hero WhatsApp Button Text'),
        ('home', 'intro', 'badge', 'Welcome Experience', 'text', 'Intro Section Badge'),
        ('home', 'intro', 'title', "More Than a Destination. <br><span class='text-[#C9A96E] italic font-normal'>It's Your Celebration.</span>", 'html', 'Intro Section Title'),
        ('home', 'intro', 'text', 'Royal Bagh Villa seamlessly brings together handcrafted cafe culture, fine multi-cuisine dining, sophisticated banquet spaces, and a grand open-air lawn under one premier destination in Dehradun.', 'text', 'Intro Section Description'),
        ('home', 'offers', 'badge', 'Special Privileges', 'text', 'Special Offer Badge'),
        ('home', 'offers', 'title', 'Bespoke Celebration Packages', 'text', 'Special Offer Title'),
        ('home', 'offers', 'text', 'Book your upcoming wedding, kitty party, or milestone celebration with us to unlock special banquet packages, complimentary signature welcome drinks, and customized lighting.', 'text', 'Special Offer Details'),

        # About Page
        ('about', 'hero', 'title', "Welcome to <span class='text-[#C9A96E] italic font-normal'>Royal Bagh Villa</span>", 'html', 'About Hero Title'),
        ('about', 'hero', 'subtitle', 'A sanctuary of taste, architectural grace, and celebratory joy in Dehradun.', 'text', 'About Hero Subtitle'),
        ('about', 'hero', 'image', 'https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1600&q=80', 'image', 'About Hero Image'),
        ('about', 'story', 'title', 'Where Every Celebration Becomes a Memory.', 'text', 'Our Story Title'),
        ('about', 'story', 'text_1', 'Royal Bagh Villa is designed as an all-encompassing luxury hospitality destination in Dehradun where guests can dine, celebrate, gather and create memorable experiences.', 'text', 'Our Story Paragraph 1'),
        ('about', 'story', 'text_2', 'Whether enjoying artisanal single-origin coffee in our quiet cafe corners, bringing loved ones together for an exquisite multi-course dinner, or celebrating grand wedding functions across our sprawling lawn and indoor banquet hall, our commitment remains uncompromising: timeless hospitality and effortless elegance.', 'text', 'Our Story Paragraph 2'),
        ('about', 'story', 'image', 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=900&q=80', 'image', 'About Story Image'),
        ('about', 'highlights', 'location', 'Scenic Valley Ambience in Dehradun', 'text', 'Location Highlight'),
        ('about', 'highlights', 'parking', '25+ Cars Convenient Parking', 'text', 'Parking Highlight'),

        # Cafe Page
        ('cafe', 'hero', 'title', "Artisanal Brews & <span class='text-[#C9A96E] italic font-normal'>Cozy Corners</span>", 'html', 'Cafe Hero Title'),
        ('cafe', 'hero', 'subtitle', "Sip, savor, and unwind in Dehradun's most aesthetic cafe ambiance.", 'text', 'Cafe Hero Subtitle'),
        ('cafe', 'hero', 'image', 'https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=1600&q=80', 'image', 'Cafe Hero Image'),
        ('cafe', 'content', 'hours', '8:00 AM ? 10:00 PM', 'text', 'Cafe Hours'),
        ('cafe', 'content', 'description', 'From rich velvety espressos to freshly baked delicacies and comforting shakes, our cafe provides a quiet retreat for book lovers, digital nomads, and casual brunch get-togethers.', 'text', 'Cafe Description'),

        # Restaurant Page
        ('restaurant', 'hero', 'title', "Culinary Mastery & <span class='text-[#C9A96E] italic font-normal'>Regal Flavors</span>", 'html', 'Restaurant Hero Title'),
        ('restaurant', 'hero', 'subtitle', 'An unforgettable dining experience crafted with passion, tradition, and seasonal freshness.', 'text', 'Restaurant Hero Subtitle'),
        ('restaurant', 'hero', 'image', 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=1600&q=80', 'image', 'Restaurant Hero Image'),
        ('restaurant', 'content', 'hours', '11:00 AM ? 11:00 PM', 'text', 'Restaurant Hours'),
        ('restaurant', 'content', 'description', 'Our master chefs bring together authentic Indian heritage curries, tandoori specialties, oriental delicacies, and continental classics in an atmosphere of warmth and understated luxury.', 'text', 'Restaurant Description'),

        # Banquet Page
        ('banquet', 'hero', 'title', "Regal Indoor <span class='text-[#C9A96E] italic font-normal'>Banquet Hall</span>", 'html', 'Banquet Hero Title'),
        ('banquet', 'hero', 'subtitle', 'Air-conditioned grandeur with bespoke chandeliers, audio-visual excellence, and tailored banquet spreads.', 'text', 'Banquet Hero Subtitle'),
        ('banquet', 'hero', 'image', 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=1600&q=80', 'image', 'Banquet Hero Image'),
        ('banquet', 'details', 'capacity', 'Up to 300 Guests', 'text', 'Banquet Capacity'),
        ('banquet', 'details', 'pricing', '?1,250 per plate', 'text', 'Banquet Starting Price'),
        ('banquet', 'details', 'pricing_note', 'Price depends on selected menu & package', 'text', 'Banquet Pricing Note'),
        ('banquet', 'details', 'description', 'Designed to host high-profile receptions, conferences, sangeet functions, and intimate anniversaries, our Banquet Hall blends state-of-the-art climate control with regal aesthetics.', 'text', 'Banquet Description'),
        ('banquet', 'details', 'features', 'Central Air Conditioning, Ambient Mood Lighting, Stage & Sound Setup, Dedicated Dining Area, Private Dressing Room', 'text', 'Banquet Features'),

        # Lawn Page
        ('lawn', 'hero', 'title', "Sprawling Open-Air <span class='text-[#C9A96E] italic font-normal'>Luxury Lawn</span>", 'html', 'Lawn Hero Title'),
        ('lawn', 'hero', 'subtitle', 'Celebrate beneath the Dehradun sky with manicured lawns, fairy lights, and open-sky stages.', 'text', 'Lawn Hero Subtitle'),
        ('lawn', 'hero', 'image', 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=1600&q=80', 'image', 'Lawn Hero Image'),
        ('lawn', 'details', 'capacity', '50 to 500+ Guests', 'text', 'Lawn Capacity'),
        ('lawn', 'details', 'pricing', 'Starting from ?1,250 / plate', 'text', 'Lawn Starting Price'),
        ('lawn', 'details', 'pricing_note', 'Customized catering & theme decor available', 'text', 'Lawn Pricing Note'),
        ('lawn', 'details', 'description', 'Surrounded by tranquil green vistas, our open lawn delivers pure open-air magic for grand wedding receptions, vibrant cocktail sundowners, and milestone festivities.', 'text', 'Lawn Description'),
        ('lawn', 'details', 'features', 'Manicured Green Turf, Night Illuminations & Fairy Lights, Live Food Stations, Weather-Proof Mandap Setup, Ample Valet Parking', 'text', 'Lawn Features'),

        # Events Page
        ('events', 'hero', 'title', "Celebrate It <span class='text-[#C9A96E] italic font-normal'>Your Way.</span>", 'html', 'Events Hero Title'),
        ('events', 'hero', 'subtitle', "From intimate birthday parties to grand wedding receptions, Royal Bagh Villa is Dehradun's premier destination for unforgettable moments.", 'text', 'Events Hero Subtitle'),
        ('events', 'hero', 'image', 'https://images.unsplash.com/photo-1519225421980-715cb0215aed?w=1600&q=80', 'image', 'Events Hero Image'),

        # Gallery Page
        ('gallery', 'hero', 'title', "Moments at <span class='text-[#C9A96E] italic font-normal'>Royal Bagh</span>", 'html', 'Gallery Hero Title'),
        ('gallery', 'hero', 'subtitle', 'Experience the architectural grandeur, lush green grounds, culinary perfection, and festive celebrations.', 'text', 'Gallery Hero Subtitle'),
        ('gallery', 'hero', 'image', 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=1600&q=80', 'image', 'Gallery Hero Image'),

        # Contact Page
        ('contact', 'hero', 'title', "Connect with <span class='text-[#C9A96E] italic font-normal'>Royal Bagh Villa</span>", 'html', 'Contact Hero Title'),
        ('contact', 'hero', 'subtitle', 'We would love to host your next celebration, dinner, or quiet coffee moment.', 'text', 'Contact Hero Subtitle'),
        ('contact', 'hero', 'image', 'https://images.unsplash.com/photo-1519167758481-83f550bb49b3?w=1600&q=80', 'image', 'Contact Hero Image'),

        # Website Settings & SEO
        ('settings', 'general', 'site_title', 'Royal Bagh Villa Dehradun | Cafe, Restaurant, Lawn & Events', 'text', 'SEO Site Title'),
        ('settings', 'general', 'site_description', 'Royal Bagh Villa, Dehradun ? a premium destination for cafe, restaurant, weddings, receptions, birthdays, events and celebrations.', 'text', 'SEO Meta Description'),
        ('settings', 'general', 'logo_text', 'Royal Bagh Villa', 'text', 'Website Logo Text'),
        ('settings', 'general', 'logo_image', '', 'image', 'Website Logo Image (Optional)'),
        ('settings', 'general', 'favicon', '', 'image', 'Website Favicon (Optional)'),
        ('settings', 'general', 'business_phone', '9762278230', 'text', 'Primary Phone Number'),
        ('settings', 'general', 'business_whatsapp', '919762278230', 'text', 'WhatsApp Number'),
        ('settings', 'general', 'business_email', 'info@royalbaghvilla.com', 'text', 'Email Address'),
        ('settings', 'general', 'business_address', 'Royal Bagh Villa, Dehradun, Uttarakhand', 'text', 'Physical Address'),
        ('settings', 'general', 'business_map_url', 'https://maps.google.com/?q=Royal+Bagh+Villa+Dehradun', 'text', 'Google Maps Link'),
        ('settings', 'general', 'instagram_url', 'https://instagram.com/royalbaghvilla', 'text', 'Instagram URL'),
        ('settings', 'general', 'facebook_url', 'https://facebook.com/royalbaghvilla', 'text', 'Facebook URL'),
        ('settings', 'general', 'restaurant_hours', '11:00 AM ? 11:00 PM', 'text', 'Restaurant Hours'),
        ('settings', 'general', 'cafe_hours', '8:00 AM ? 10:00 PM', 'text', 'Cafe Hours'),
        ('settings', 'general', 'footer_tagline', 'Where Every Celebration Becomes a Memory', 'text', 'Footer Tagline'),
        ('settings', 'general', 'footer_about', 'A premier destination in Dehradun bringing together fine dining, artisanal cafe moments, grand lawn celebrations, and unforgettable events.', 'text', 'Footer About Text'),
        ('settings', 'general', 'google_analytics_id', '', 'text', 'Google Analytics / Tag ID'),
        ('settings', 'general', 'custom_css', '', 'text', 'Custom CSS (Optional)'),
        ('settings', 'general', 'custom_js', '', 'text', 'Custom Head Scripts (Optional)')
    ]

    for page, section, key, val, c_type, label in cms_defaults:
        existing = CMSContent.query.filter_by(page=page, section=section, key=key).first()
        if not existing:
            db.session.add(CMSContent(page=page, section=section, key=key, value=val, content_type=c_type, label=label))
    db.session.commit()
    print("CMS defaults successfully seeded.")
