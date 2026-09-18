from collections import OrderedDict
from flask import Blueprint, render_template
from models import db, MenuItem, MenuCategory

restaurant_bp = Blueprint('restaurant_bp', __name__)

SECTION_CONFIG = OrderedDict([
    ('breakfast', 'Breakfast'),
    ('light', 'Light & Casual'),
    ('main', 'Main Dining'),
    ('sides', 'Sides'),
    ('sweet', 'Sweet Ending'),
    ('drinks', 'Drinks'),
])


@restaurant_bp.route('/')
def index():
    sections = OrderedDict()
    for key, title in SECTION_CONFIG.items():
        cats = MenuCategory.query.filter_by(
            section=key, is_active=True
        ).order_by(MenuCategory.display_order).all()

        if not cats:
            continue

        # Attach items to each category object so template can iterate
        cat_list = []
        for cat in cats:
            cat.items = MenuItem.query.filter_by(
                category_id=cat.id, is_available=True
            ).order_by(MenuItem.display_order).all()
            cat_list.append(cat)

        sections[key] = {'title': title, 'categories': cat_list}

    return render_template('restaurant.html', sections=sections)


@restaurant_bp.route('/menu/<slug>')
def category_menu(slug):
    category = MenuCategory.query.filter_by(slug=slug).first_or_404()
    items = MenuItem.query.filter_by(category_id=category.id, is_available=True).all()
    # Wrap into the sections format the template expects
    category.items = items
    sections = OrderedDict()
    sections[category.section] = {
        'title': category.name,
        'categories': [category],
    }
    return render_template('restaurant.html', sections=sections)
