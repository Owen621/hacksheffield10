from flask import Flask, render_template, request, jsonify, session, redirect
import uuid
from solders.keypair import Keypair
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

    # ----------------------------
    # ADD ITEM + "mint NFT" (dev/test, no real blockchain call)
    # ----------------------------
    @app.route("/add", methods=["GET", "POST"])
    def add_item():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return redirect("/connect_wallet")

        if request.method == "POST":
            data = request.get_json()
            if not data:
                return jsonify({"success": False, "error": "Missing JSON body"}), 400

            name = data.get("name")
            description = data.get("description")

            if not name:
                return jsonify({"success": False, "error": "Missing name"}), 400

            # Save item in backend
            item_id = str(uuid.uuid4())
            ITEMS[item_id] = {
                "name": name,
                "description": description,
                "solana_mint": None,
                "owner_wallet_public_key": wallet_pk
            }

            try:
                # Generate a new Keypair (mint pubkey)
                mint_account = Keypair()
                mint_pubkey = str(mint_account.pubkey())

                ITEMS[item_id]["solana_mint"] = mint_pubkey

                return jsonify({
                    "success": True,
                    "item_id": item_id,
                    "mint_address": mint_pubkey,
                    "explorer_url": f"https://explorer.solana.com/address/{mint_pubkey}?cluster=devnet"
                })

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        # GET → show form
        return render_template("add_item.html", wallet_public_key=wallet_pk)

    # ----------------------------
    # Item pages
    # ----------------------------
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
