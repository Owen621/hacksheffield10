from flask import Flask # type: ignore
from backend.routes import setup_routes
from dotenv import load_dotenv
from backend.models import db

load_dotenv()  

app = Flask(
    __name__,
    template_folder="backend/templates",
    static_folder="backend/static"
)
app.secret_key = "dev_secret_key"

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restyle.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

setup_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
