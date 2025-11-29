from flask_sqlalchemy import SQLAlchemy # type: ignore

db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = 'items'

    solanaMint = db.Column(db.String(44), primary_key=True)
    ownerPublicKey = db.Column(db.String(44))
    name = db.Column(db.String(30))
    description = db.Column(db.String(100))