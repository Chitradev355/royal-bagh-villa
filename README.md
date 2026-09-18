# Royal Bagh Villa — Luxury Hospitality & Event Platform with Full CMS

A production-ready Flask web platform and database-driven Content Management System (CMS) for **Royal Bagh Villa**, Dehradun's premier destination for fine dining, artisanal cafe culture, weddings, receptions, and luxury celebrations.

---

## Architecture & Capabilities

- **Public Website**: High-performance, responsive luxury design showcasing the Cafe, Restaurant, Sprawling Lawn, Banquet Hall, Celebrations, and Photo/Video Gallery.
- **Full Database-Driven CMS**: Update hero headings, subtitles, images, videos, descriptions, packages, prices, and SEO directly through the Admin Panel without touching code or redeploying.
- **Central Media Library**: Upload, preview, organize, and delete photos and videos with a single-click Media Picker across all CMS editors.
- **Persistent Production Storage**: Supports Render Persistent Disks (`/var/data`) for SQLite and uploads, as well as optional Cloudinary CDN storage.
- **Online Food & Event Ordering**: Real-time cart management, status tracking, and table/takeaway order workflows.
- **Booking & Enquiry Funnels**: Complete lead management for weddings, birthdays, anniversaries, corporate events, and lawn/banquet reservations.
- **Production-Grade Security**: Flask-WTF CSRF protection, Werkzeug password hashing, secure session cookies, file validation, and Render `ProxyFix` reverse-proxy support.

---

## Local Development in VS Code (Quickstart)

Follow these exact steps to clone, configure, run, and develop this project locally on your machine.

### 1. Clone GitHub Repository
Open your terminal (or Command Prompt / PowerShell / Git Bash) and run:
```bash
git clone https://github.com/Chitradev355/royal-bagh-villa.git
cd royal-bagh-villa
```

### 2. Open in VS Code
Open the repository folder in Visual Studio Code:
```bash
code .
```
*(Alternatively, launch VS Code and use **File > Open Folder...** to select the `royal-bagh-villa` folder.)*

### 3. Create Python Virtual Environment
Open the integrated terminal in VS Code (`Ctrl + ~` or **Terminal > New Terminal**):

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts scripts, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`)*

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Requirements
Install all dependencies inside your virtual environment:
```bash
pip install -r requirements.txt
```

### 5. Configure `.env`
Copy `.env.example` to create your local `.env` configuration:

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**On macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` in VS Code and verify or customize settings. (Defaults work immediately out-of-the-box for local development).

### 6. Initialize / Use Database
The project includes a pre-seeded SQLite database with complete luxury website content and an admin account.

To inspect or re-seed default CMS content at any time:
```bash
python -c "from app import app; from utils.cms_seeder import seed_cms_defaults; app.app_context().push(); seed_cms_defaults()"
```

### 7. Run Locally
Start the Flask development server:
```bash
python app.py
```
The server will start at: `http://127.0.0.1:5000`

### 8. Access Public Website
Open your browser and visit:
- **Homepage**: [http://127.0.0.1:5000](http://127.0.0.1:5000)
- **Cafe**: [http://127.0.0.1:5000/cafe](http://127.0.0.1:5000/cafe)
- **Restaurant**: [http://127.0.0.1:5000/restaurant](http://127.0.0.1:5000/restaurant)
- **Banquet Hall**: [http://127.0.0.1:5000/banquet](http://127.0.0.1:5000/banquet)
- **Celebration Lawn**: [http://127.0.0.1:5000/lawn](http://127.0.0.1:5000/lawn)
- **Events & Parties**: [http://127.0.0.1:5000/events](http://127.0.0.1:5000/events)
- **Gallery**: [http://127.0.0.1:5000/gallery](http://127.0.0.1:5000/gallery)
- **Contact Us**: [http://127.0.0.1:5000/contact](http://127.0.0.1:5000/contact)

### 9. Access Admin Panel
- **Admin Login URL**: [http://127.0.0.1:5000/admin/login](http://127.0.0.1:5000/admin/login)
- **Default Username**: `admin`
- **Default Password**: Defined in your `.env` (or default `admin123`)

Inside the admin dashboard, you have full control to edit pages, menu items, prices, uploaded photos/videos, venue packages, and website settings.

### 10. Run Tests
Run the comprehensive test suite to verify all public customer routes, protected admin CMS endpoints, CSRF protection, and upload validation:
```bash
python test_all_pages.py
```

### 11. Make Changes in VS Code
You can edit HTML templates in `templates/`, CSS/JS in `static/`, routes in `routes/`, or models in `models/`. VS Code provides syntax highlighting, linting, and Git integration.

### 12. Git Add / Commit / Push
When ready to save your work:
```bash
git status
git add .
git commit -m "Your descriptive commit message"
git push origin main
```

### 13. Deploy to Render
Render automatically detects pushes to the `main` branch and deploys the application.

#### Build & Start Commands on Render:
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

#### Recommended Render Environment Variables:
| Variable | Value / Description |
|---|---|
| `SECRET_KEY` | Generate a 64-char random hex key |
| `ADMIN_USERNAME` | Production superadmin username |
| `ADMIN_PASSWORD` | Production superadmin password |
| `DATA_DIR` | `/var/data` (if using Render Persistent Disk) |
| `CLOUDINARY_URL` | *(Optional)* Cloudinary CDN URL for cloud uploads |

#### Making Database & Uploads 100% Persistent on Render:
1. In Render Dashboard, go to your Web Service > **Disks** > **Add Disk**.
2. Mount Path: `/var/data`
3. Size: 1 GB or larger.
4. Set Environment Variable: `DATA_DIR=/var/data`
5. The application will automatically store both `royal_bagh.db` and uploaded photos/videos inside `/var/data`, ensuring all CMS edits and media survive server restarts and code deployments!

---

## Project Structure

```
royal-bagh-villa/
├── app.py                     # Flask application factory, ProxyFix & media routes
├── config.py                  # Environment config, database URI & storage paths
├── requirements.txt           # Python dependencies (Flask, SQLAlchemy, Pillow, etc.)
├── .python-version            # Python runtime version pin (3.13)
├── .env.example               # Environment variables template (no secrets)
├── .gitignore                 # Git ignore rules (ignoring .env, caches, venv)
├── README.md                  # Complete documentation and developer guide
├── test_all_pages.py          # Regression test suite covering routes, CSRF, & auth
├── instance/
│   └── royal_bagh.db          # Pre-seeded SQLite database with initial CMS data
├── models/
│   ├── __init__.py            # SQLAlchemy db instance export
│   ├── cms.py                 # CMS models (CMSContent, MediaFile, CMSEvent, etc.)
│   ├── user.py                # Admin model with Werkzeug password hashing
│   ├── menu.py                # Food & drink menu categories and items
│   ├── booking.py             # Lawn, banquet, and room bookings
│   ├── order.py               # Online food orders and order items
│   └── enquiry.py             # Customer event inquiries and leads
├── routes/
│   ├── __init__.py            # Route package
│   ├── main.py                # Public customer pages (Home, About, Gallery, Contact)
│   ├── cafe.py                # Cafe menu & dining experience
│   ├── restaurant.py          # Fine dining restaurant & cuisine
│   ├── banquet.py             # Banquet hall showcase & booking form
│   ├── lawn.py                # Celebration lawn showcase & booking form
│   ├── rooms.py               # Stay / rooms showcase
│   ├── order.py               # Cart & checkout workflow
│   ├── booking.py             # Booking status checker
│   ├── api.py                 # Public JSON endpoints
│   └── admin.py               # Complete CMS admin routes (40+ management endpoints)
├── templates/
│   ├── base.html              # Base layout with luxury navigation & footer
│   ├── index.html             # Homepage powered by CMS hero, sections & events
│   ├── cafe.html              # Cafe page
│   ├── restaurant.html        # Restaurant page
│   ├── banquet.html           # Banquet hall page
│   ├── lawn.html              # Lawn page
│   ├── events.html            # Dynamic events showcase
│   ├── gallery.html           # Photo & video gallery
│   ├── about.html             # About story & amenities
│   ├── contact.html           # Contact info & map
│   ├── admin/                 # Dedicated CMS Admin Dashboard templates
│   │   ├── base_admin.html    # Admin layout & navigation
│   │   ├── login.html         # Secure login with CSRF token
│   │   ├── dashboard.html     # High-level KPIs, bookings & orders
│   │   ├── media.html         # Central Media Library (drag-and-drop uploader)
│   │   ├── cms_home.html      # Hero title, subtitle, video, buttons & badges
│   │   ├── cms_pages.html     # Tabbed content editor for all website pages
│   │   ├── cms_venues.html    # Capacity, pricing (₹1,250/plate), features
│   │   ├── cms_events.html    # Weddings, Birthdays, Anniversaries, Corporate
│   │   ├── cms_gallery.html   # Visual portfolio manager with category tags
│   │   ├── cms_navigation.html# Dynamic header/footer navigation items
│   │   ├── menu.html          # Food & beverage categories, prices, veg tags
│   │   ├── banquet_bookings.html # Banquet lead tracking & status
│   │   ├── lawn_bookings.html # Lawn lead tracking & status
│   │   ├── enquiries.html     # General customer enquiries
│   │   ├── settings.html      # Business details, SEO, logo & analytics
│   │   └── components/
│   │       └── media_picker_modal.html # Modal for reusable media selection
│   └── components/            # Reusable frontend UI components
├── static/
│   ├── css/
│   │   └── style.css          # Custom luxury styling and animations
│   ├── js/
│   │   ├── main.js            # Frontend interactions, sliders & mobile nav
│   │   ├── admin.js           # Admin UI, modal triggers & dynamic forms
│   │   └── cart.js            # Customer cart operations
│   └── uploads/               # Local upload directory fallback
│       └── media/             # Uploaded photos and videos
└── utils/
    ├── __init__.py
    ├── cms_seeder.py          # Automated database seeder & admin self-healer
    └── media.py               # Media upload validation, persistent disk & Cloudinary
```

---

## License

All rights reserved © Royal Bagh Villa, Dehradun.
