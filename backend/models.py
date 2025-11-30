<<<<<<< HEAD
from flask_sqlalchemy import SQLAlchemy # type: ignore
=======
from flask_sqlalchemy import SQLAlchemy  # type: ignore
>>>>>>> owen

db = SQLAlchemy()

class Item(db.Model):
    __tablename__ = 'items'

    solanaMint = db.Column(db.String(44), primary_key=True)
    ownerPublicKey = db.Column(db.String(44))
    name = db.Column(db.String(30))
<<<<<<< HEAD
    description = db.Column(db.String(100))
=======
    description = db.Column(db.String(100))
    image_filename = db.Column(db.String(255))  # store uploaded image filename

>>>>>>> owen
