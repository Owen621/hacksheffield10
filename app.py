from flask import Flask
from backend.routes import setup_routes
from dotenv import load_dotenv
load_dotenv()  
app = Flask(
    __name__,
    template_folder="backend/templates",
    static_folder="backend/static"
)
app.secret_key = "dev_secret_key"

setup_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
