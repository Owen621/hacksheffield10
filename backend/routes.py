<<<<<<< HEAD
from flask import render_template, request, redirect # type: ignore
from backend.models import db, Item
import uuid
=======
from flask import Flask, request, jsonify, session, render_template, redirect, url_for
import subprocess
import json
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from backend.models import db, Item
>>>>>>> owen

load_dotenv()

UPLOAD_FOLDER = 'backend/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def setup_routes(app: Flask):
    app.secret_key = "dev_secret_key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # ---------------------------------------------------------
    # Home
    # ---------------------------------------------------------
    @app.route("/")
    def home():
        wallet_pk = session.get("wallet_public_key")
        return render_template("index.html", wallet_public_key=wallet_pk)

<<<<<<< HEAD
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
=======
    # ---------------------------------------------------------
    # Connect / Disconnect Wallet
    # ---------------------------------------------------------
    @app.route("/connect_wallet", methods=["POST"])
    def connect_wallet():
        data = request.get_json()
        wallet = data.get("wallet_public_key")
        if not wallet:
            return jsonify({"error": "No wallet provided"}), 400
        session["wallet_public_key"] = wallet
        return jsonify({"status": "ok"})

    @app.route("/disconnect_wallet", methods=["POST"])
    def disconnect_wallet():
        session.pop("wallet_public_key", None)
        return jsonify({"status": "ok"})


    # ---------------------------------------------------------
    # Add item
    # ---------------------------------------------------------
    @app.route("/add", methods=["GET", "POST"])
    def add_item():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            if request.method == "GET":
                return redirect("/")
            return jsonify({"error": "Connect your wallet"}), 400

        if request.method == "GET":
            return render_template("add_item.html", wallet_public_key=wallet_pk)

        # POST: form data
        name = request.form.get("name")
        description = request.form.get("description")
        image_file = request.files.get("image")
        image_filename = None

        if not name:
            return jsonify({"error": "Missing name"}), 400

        # Save image if provided
        if image_file and allowed_file(image_file.filename):
            filename = f"{wallet_pk}_{secure_filename(image_file.filename)}"
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(file_path)
            image_filename = filename

        # Mint NFT via Node script
        try:
            result = subprocess.run(
                ["node", "backend/mint_nft.js", wallet_pk, name, description],
                capture_output=True,
                text=True,
                check=True
            )
            mint_data = json.loads(result.stdout)
            mint_address = mint_data.get("mint_address")
            if not mint_address:
                return jsonify({"success": False, "error": "Mint script did not return mint address"}), 500
        except Exception as e:
            print("Minting failed:", e)
            return jsonify({"success": False, "error": "Minting NFT failed"}), 500

        # Save to DB
        try:
            new_item = Item(
                solanaMint=mint_address,
                ownerPublicKey=wallet_pk,
                name=name,
                description=description,
                image_filename=image_filename
            )
            db.session.add(new_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("DB error:", e)
            return jsonify({"success": False, "error": "Database error"}), 500

        return jsonify({"success": True, "solana_mint": mint_address})



    # ---------------------------------------------------------
    # My Items
    # ---------------------------------------------------------
    @app.route("/my_items")
    def my_items():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return redirect("/")
        items = Item.query.filter_by(ownerPublicKey=wallet_pk).all()
        return render_template("my_items.html", items=items, wallet_public_key=wallet_pk)


    # ---------------------------------------------------------
    # All Items
    # ---------------------------------------------------------
    @app.route("/all_items")
    def all_items():
        wallet_pk = session.get("wallet_public_key")
        items = Item.query.all()
        return render_template("all_items.html", items=items, wallet_public_key=wallet_pk)


    # ---------------------------------------------------------
    # View single item
    # ---------------------------------------------------------
    @app.route("/item/<mint>")
    def item_page(mint):
        item = Item.query.filter_by(solanaMint=mint).first()
        if not item:
            return "Item not found", 404
        return render_template("item.html", item=item)
>>>>>>> owen
