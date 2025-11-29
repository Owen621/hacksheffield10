from flask import render_template, request, redirect # type: ignore
from backend.models import db, Item
import uuid

def setup_routes(app):

    @app.route("/")
    def home():
        return render_template("index.html")

    #@app.route("/add", methods=["GET", "POST"])
    #def add_item():
        #if request.method == "POST":
            #item_id = str(uuid.uuid4())
            #ITEMS[item_id] = {
                #"name": request.form["name"],
                #"description": request.form["description"],
                #"history": ["Created"]
            #}
            #return redirect(f"/item/{item_id}")
        #return render_template("add_item.html")

    @app.route("/add-item", methods=["GET", "POST"])
    def add_item():
        if request.method == "GET":
            return render_template('add_item.html')

        elif request.method == "POST":
            name = request.form.get("name")
            description = request.form.get("description")
            item = Item(solanaMint = uuid.uuid1(), ownerPublicKey = uuid.uuid1(), name = name, description = description)

            db.session.add(item)
            db.session.commit()
            return redirect('/items/{solanaMint}')


    @app.route("/items")
    def items_search():
        items = Item.query.all()
        return render_template('item_search.html', items=items)

    @app.route("/items/<item_id>")
    def item_page(item_id):
        item = Items.get(item_id)
        return render_template("item.html", item=item, item_id=item_id)