from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from models.user import Admin
from models.menu import MenuCategory, MenuItem
from models.order import FoodOrder, OrderItem
from models.banquet import BanquetBooking
from models.lawn import LawnBooking
from models.room import Room, RoomBooking
from models.contact import Enquiry, BusinessSetting
