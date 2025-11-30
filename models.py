from flask_sqlalchemy import SQLAlchemy  # type: ignore
import uuid


db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = "items"

    solanaMint = db.Column(db.String(44), primary_key=True)
    ownerPublicKey = db.Column(db.String(44))
    name = db.Column(db.String(30))
    description = db.Column(db.String(100))
    image_filename = db.Column(db.String(255))
    image_MIME = db.Column(db.Text)
    image_data = db.Column(db.LargeBinary)
    brand = db.Column(db.String(50))

class User(db.Model):
    __tablename__ = "users"

    wallet = db.Column(db.String(44), primary_key=True)  # Phantom public key
    loyalty_points = db.Column(db.Integer, default=0)


class JourneyStamp(db.Model):
    __tablename__ = "journey_stamps"

    id = db.Column(db.Integer, primary_key=True)
    item_mint = db.Column(db.String(44), db.ForeignKey("items.solanaMint"))
    user_wallet = db.Column(db.String(44), db.ForeignKey("users.wallet"))
    event = db.Column(db.String(50))  
    timestamp = db.Column(db.DateTime, default=db.func.now())
