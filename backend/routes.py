from flask import Flask, render_template, request, jsonify, session, redirect
import uuid
import os
import requests
from werkzeug.utils import secure_filename
from backend.models import ITEMS

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def setup_routes(app: Flask):
    app.secret_key = "dev_secret_key"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

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

    # ==== /add serves the form (GET) and handles submission (POST) ====
    @app.route("/add", methods=["GET", "POST"])
    def add_item():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return redirect("/connect_wallet")

        if request.method == "POST":
            try:
                name = request.form.get("name")
                description = request.form.get("description")
                file = request.files.get("image_file")

                if not (name and file):
                    return jsonify({"success": False, "error": "Missing fields"}), 400

                filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file.save(file_path)
                file_url = request.host_url + f"{file_path}"

                # Create backend item
                item_id = str(uuid.uuid4())
                ITEMS[item_id] = {
                    "name": name,
                    "description": description,
                    "image_url": file_url,
                    "solana_mint": None,
                    "owner_wallet_public_key": wallet_pk
                }

                # Mint NFT via Helius Devnet
                HELIUS_API_KEY = "fe0bc47c-01af-4911-8ce8-c4228a92882e"
                mint_data = {
                    "name": name,
                    "symbol": "FASHION",
                    "description": description,
                    "image": file_url,
                    "owner": wallet_pk,
                    "attributes": [{"trait_type": "Category", "value": "Clothing"}]
                }

                response = requests.post(
                    f"https://devnet.helius-rpc.com/?api-key={HELIUS_API_KEY}",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "mintNFT",
                        "params": [mint_data]
                    },
                )

                if response.status_code != 200:
                    return jsonify({"success": False, "error": f"HTTP {response.status_code}"}), 400

                result = response.json()
                mint_address = result.get("result")
                if not mint_address:
                    return jsonify({"success": False, "error": "Helius mint failed"}), 400

                ITEMS[item_id]["solana_mint"] = mint_address

                return jsonify({
                    "success": True,
                    "item_id": item_id,
                    "mint_address": mint_address,
                    "explorer_url": f"https://explorer.solana.com/address/{mint_address}?cluster=devnet"
                })

            except Exception as e:
                return jsonify({"success": False, "error": str(e)}), 500

        # GET request → show the form
        return render_template("add_item.html", wallet_public_key=wallet_pk)

    @app.route("/update_mint/<item_id>", methods=["POST"])
    def update_mint(item_id):
        item = ITEMS.get(item_id)
        if not item:
            return "Item not found", 404
        mint_address = request.json.get("mint_address")
        item["solana_mint"] = mint_address
        return jsonify({"status": "ok"})

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
