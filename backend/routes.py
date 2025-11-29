from flask import render_template, request, redirect
import uuid
from backend.models import ITEMS

def setup_routes(app):

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/add", methods=["GET", "POST"])
    def add_item():
        if request.method == "POST":
            item_id = str(uuid.uuid4())
            ITEMS[item_id] = {
                "name": request.form["name"],
                "description": request.form["description"],
                "history": ["Created"]
            }
            return redirect(f"/item/{item_id}")
        return render_template("add_item.html")

    @app.route("/item/<item_id>")
    def item_page(item_id):
        item = ITEMS.get(item_id)
        return render_template("item.html", item=item, item_id=item_id)