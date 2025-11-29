from flask import Flask, request, jsonify, session, render_template, redirect
import uuid
import subprocess
import json
from backend.models import ITEMS
import os
from dotenv import load_dotenv

# Load .env into os.environ
load_dotenv()

def setup_routes(app: Flask):
    app.secret_key = "dev_secret_key"

    # --- Home page ---
    @app.route("/")
    def home():
        wallet_pk = session.get("wallet_public_key")
        return render_template("index.html", wallet_public_key=wallet_pk)

    # --- Disconnect wallet ---
    @app.route("/disconnect_wallet", methods=["POST"])
    def disconnect_wallet():
        session.pop("wallet_public_key", None)
        return jsonify({"status": "ok"})

    # --- Connect wallet ---
    @app.route("/connect_wallet", methods=["POST"])
    def connect_wallet():
        data = request.get_json()
        wallet_pk = data.get("wallet_public_key")
        if wallet_pk:
            session["wallet_public_key"] = wallet_pk
            return jsonify({"status": "ok"})
        return jsonify({"error": "No wallet provided"}), 400

    # --- Add item (GET renders form, POST mints NFT) ---
    @app.route("/add", methods=["GET", "POST"])
    def add_item():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            if request.method == "GET":
                return redirect("/connect_wallet")
            return jsonify({"error": "Connect your wallet"}), 400

        if request.method == "GET":
            return render_template("add_item.html", wallet_public_key=wallet_pk)

        # --- POST: mint NFT ---
        data = request.get_json()
        name = data.get("name")
        description = data.get("description")
        if not name:
            return jsonify({"error": "Missing name"}), 400

        item_id = str(uuid.uuid4())
        ITEMS[item_id] = {
            "name": name,
            "description": description,
            "solana_mint": None,
            "owner_wallet_public_key": wallet_pk
        }

        # --- Mint NFT using master wallet ---
        try:
            result = subprocess.run(
                ["node", "backend/mint_nft.js", wallet_pk],
                capture_output=True,
                text=True,
                check=True,
                env={**os.environ}  # Pass all current env vars including MASTER_WALLET_SECRET
            )

            # Debug output
            print("Node stdout:", result.stdout)
            print("Node stderr:", result.stderr)

            mint_data = json.loads(result.stdout)
            ITEMS[item_id]["solana_mint"] = mint_data.get("mint_address")

        except Exception as e:
            print("Minting failed:", e)
            ITEMS[item_id]["solana_mint"] = None

        return jsonify({
            "success": True,
            "item_id": item_id,
            "solana_mint": ITEMS[item_id]["solana_mint"]
        })

    # --- View single item ---
    @app.route("/item/<item_id>")
    def item_page(item_id):
        item = ITEMS.get(item_id)
        if not item:
            return "Item not found", 404
        return render_template("item.html", item=item, item_id=item_id)

    # --- All items ---
    @app.route("/all_items")
    def all_items():
        wallet_pk = session.get("wallet_public_key")
        return render_template("all_items.html", items=ITEMS.values(), wallet_public_key=wallet_pk)

    # --- My items ---
    @app.route("/my_items")
    def my_items():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return redirect("/connect_wallet")
        owned_items = [
            dict(id=iid, **item)
            for iid, item in ITEMS.items()
            if item["owner_wallet_public_key"] == wallet_pk
        ]
        return render_template("my_items.html", items=owned_items, wallet_public_key=wallet_pk)
