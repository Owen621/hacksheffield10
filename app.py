from flask import Flask
from backend.routes import setup_routes

app = Flask(__name__)
app.secret_key = "dev_secret_key"  # needed for session

setup_routes(app)

if __name__ == "__main__":
    app.run(debug=True)
