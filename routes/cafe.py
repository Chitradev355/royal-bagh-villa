from flask import Blueprint, render_template
from models import db, MenuItem, MenuCategory

cafe_bp = Blueprint('cafe_bp', __name__)

@cafe_bp.route('/')
def index():
    cafe_items = MenuItem.query.join(MenuCategory).filter(
        MenuCategory.section == 'cafe',
        MenuItem.is_available == True
    ).all()
    return render_template('cafe.html', cafe_items=cafe_items)
