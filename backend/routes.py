from flask import Flask, render_template, request, jsonify, session, redirect
import uuid
from backend.models import ITEMS

def setup_routes(app: Flask):
    app.secret_key = "dev_secret_key"

    @app.route("/")
    def home():
        wallet_pk = session.get("wallet_public_key")
        return render_template("index.html", wallet_public_key=wallet_pk)

    @app.route("/set_wallet", methods=["POST"])
    def set_wallet():
        data = request.get_json()
        wallet_pk = data.get("wallet_public_key")
        if wallet_pk:
            session["wallet_public_key"] = wallet_pk
            return jsonify({"status": "ok"})
        return jsonify({"error": "No wallet provided"}), 400

    @app.route("/add_item", methods=["POST"])
    def add_item():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return jsonify({"success": False, "error": "Wallet not connected"}), 400

        data = request.get_json()
        name = data.get("name")
        description = data.get("description")
        if not name:
            return jsonify({"success": False, "error": "Missing name"}), 400

        item_id = str(uuid.uuid4())
        ITEMS[item_id] = {
            "name": name,
            "description": description,
            "owner_wallet_public_key": wallet_pk,
            "solana_mint": None,  # Will be set by frontend after mint
        }

        return jsonify({
            "success": True,
            "item_id": item_id
        })

    @app.route("/item/<item_id>")
    def item_page(item_id):
        item = ITEMS.get(item_id)
        if not item:
            return "Item not found", 404
        return render_template("item.html", item=item, item_id=item_id)


    @app.route("/my_items")
    def my_items():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return redirect("/connect_wallet")
        owned_items = [i for i in ITEMS.values() if i["owner_wallet_public_key"] == wallet_pk]
        return render_template("my_items.html", items=owned_items)

    @app.route("/all_items")
    def all_items():
        return render_template("all_items.html", items=ITEMS.values())

    @app.route("/connect_wallet")
    def connect_wallet():
        wallet_pk = session.get("wallet_public_key")
        return render_template("connect_wallet.html", wallet_public_key=wallet_pk)

    @app.route("/disconnect_wallet", methods=["POST"])
    def disconnect_wallet():
        session.pop("wallet_public_key", None)
        return jsonify({"status": "ok"})
