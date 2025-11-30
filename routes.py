from flask import Flask, request, jsonify, session, render_template, redirect, g
import subprocess
import json
import os
import base64
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from models import db, Item, User, JourneyStamp

load_dotenv()

BRANDS = [
    "Nike",
    "Adidas",
    "Gucci",
    "North Face"
]

UPLOAD_FOLDER = 'backend/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

JOURNEY_EVENTS = [
    "worn",
    "washed",
    "repaired",
    "bought",
    "sold",
    "store_visit",
    "brand_drop",
    "limited_time",
    "brand_challenge"
]


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def setup_routes(app: Flask):
    app.secret_key = "dev_secret_key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.before_request
    def load_user_points():
        wallet_pk = session.get("wallet_public_key")
        g.wallet = wallet_pk
        g.total_points = 0
        if wallet_pk:
            g.total_points = JourneyStamp.query.filter_by(user_wallet=wallet_pk).count()

    # ---------------------------------------------------------
    # Home
    # ---------------------------------------------------------
    @app.route("/")
    def home():
        wallet_pk = session.get("wallet_public_key")
        return render_template("index.html", wallet_public_key=wallet_pk)

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
            return render_template("add_item.html", wallet_public_key=wallet_pk, brands=BRANDS)

        name = request.form.get("name")
        image_file = request.files.get("image")
        image_filename = None
        image_MIME = None
        description = request.form.get("description")
        brand = request.form.get("brand")
        price = request.form.get("price", type=float)

        if not name:
            return jsonify({"error": "Missing name"}), 400
        if not brand or brand not in BRANDS:
            return jsonify({"error": "Invalid or missing brand"}), 400

        if image_file and allowed_file(image_file.filename):
            image_MIME = secure_filename(image_file.filename)
            image_filename = f"{wallet_pk}_{image_MIME}"

        # Mint NFT via Node script
        try:
            result = subprocess.run(
                ["node", "static/js/mint_nft.js", wallet_pk, name, description, brand],
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
                image_filename=image_filename,
                image_MIME=image_MIME,
                image_data=image_file.read() if image_file else None,
                description=description,
                brand=brand,
                price=price
            )
            db.session.add(new_item)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("DB error:", e)
            return jsonify({"success": False, "error": "Database error"}), 500

        return jsonify({"success": True, "solana_mint": mint_address})

    # ---------------------------------------------------------
    # View Items
    # ---------------------------------------------------------
    @app.route("/my_items")
    def my_items():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return redirect("/")

        items = Item.query.filter_by(ownerPublicKey=wallet_pk).all()
        for item in items:
            item.total_points = JourneyStamp.query.filter_by(item_mint=item.solanaMint).count()
            item.image_data_base64 = base64.b64encode(item.image_data).decode('utf-8') if item.image_data else None

        return render_template(
            "my_items.html",
            items=items,
            wallet_public_key=wallet_pk,
            total_items=len(items),
            limit=6
        )

    @app.route("/all_items")
    def all_items():
        wallet_pk = session.get("wallet_public_key")
        items = Item.query.all()
        for item in items:
            item.total_points = JourneyStamp.query.filter_by(item_mint=item.solanaMint).count()
            item.image_data_base64 = base64.b64encode(item.image_data).decode('utf-8') if item.image_data else None

        return render_template(
            "all_items.html",
            items=items,
            wallet_public_key=wallet_pk,
            total_items=len(items),
            limit=6
        )

    @app.route("/item/<mint_address>")
    def item_page(mint_address):
        wallet_pk = session.get("wallet_public_key")
        item = Item.query.get(mint_address)
        if not item:
            return "Item not found", 404

        stamps = JourneyStamp.query.filter_by(item_mint=mint_address).order_by(JourneyStamp.timestamp.desc()).all()
        item_points = JourneyStamp.query.filter_by(item_mint=mint_address, user_wallet=wallet_pk).count() if wallet_pk else 0

        from sqlalchemy import func
        user_points = (
            JourneyStamp.query
            .with_entities(JourneyStamp.user_wallet, func.count(JourneyStamp.id).label("points"))
            .filter_by(item_mint=mint_address)
            .group_by(JourneyStamp.user_wallet)
            .all()
        )

        item.image_data_base64 = base64.b64encode(item.image_data).decode('utf-8') if item.image_data else None

        return render_template(
            "item.html",
            item=item,
            stamps=stamps,
            wallet_public_key=wallet_pk,
            item_points=item_points,
            journey_events=JOURNEY_EVENTS,
            user_points=user_points,
            is_owner=item.ownerPublicKey == wallet_pk
        )

    # ---------------------------------------------------------
    # Add Journey Stamp
    # ---------------------------------------------------------
    @app.route("/add_stamp", methods=["POST"])
    def add_stamp():
        data = request.json
        wallet = data.get("wallet")
        item_mint = data.get("item_mint")
        event = data.get("event")

        if event not in JOURNEY_EVENTS:
            return jsonify({"error": "Invalid event"}), 400

        user = User.query.get(wallet)
        if not user:
            user = User(wallet=wallet, loyalty_points=0)
            db.session.add(user)

        item = Item.query.get(item_mint)
        if not item:
            return jsonify({"error": "Item not found"}), 404

        stamp = JourneyStamp(item_mint=item_mint, user_wallet=wallet, event=event)
        db.session.add(stamp)

        user.loyalty_points += 1

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500

        return jsonify({
            "message": f"Journey stamp '{event}' added!",
            "loyalty_points": user.loyalty_points
        })

    # ---------------------------------------------------------
    # Update Item
    # ---------------------------------------------------------
    @app.route("/update_item", methods=["POST"])
    def update_item():
        item_mint = request.form.get('item_mint')
        description = request.form.get('description')
        price = request.form.get('price', type=float)

        item = Item.query.filter_by(solanaMint=item_mint).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404

        item.description = description
        item.price = price
        db.session.commit()
        return jsonify({"status": "success", "message": "Item Modified"})

    # ---------------------------------------------------------
    # Purchase Item (adds bought/sold journeys)
    # ---------------------------------------------------------
    @app.route("/purchase_item", methods=["POST"])
    def purchase_item():
        data = request.json
        buyer_wallet = data.get('wallet')
        item_mint = data.get('item_mint')

        item = Item.query.filter_by(solanaMint=item_mint).first()
        if not item:
            return jsonify({"error": "Item not found"}), 404

        seller_wallet = item.ownerPublicKey

        # Transfer ownership
        item.ownerPublicKey = buyer_wallet
        item.price = 0

        # Ensure buyer exists
        buyer = User.query.get(buyer_wallet)
        if not buyer:
            buyer = User(wallet=buyer_wallet, loyalty_points=0)
            db.session.add(buyer)
        buyer.loyalty_points += 1

        # Ensure seller exists
        seller = User.query.get(seller_wallet)
        if not seller:
            seller = User(wallet=seller_wallet, loyalty_points=0)
            db.session.add(seller)
        seller.loyalty_points += 1

        # Add Journey Stamps
        buy_stamp = JourneyStamp(item_mint=item_mint, user_wallet=buyer_wallet, event="bought")
        sell_stamp = JourneyStamp(item_mint=item_mint, user_wallet=seller_wallet, event="sold")
        db.session.add(buy_stamp)
        db.session.add(sell_stamp)

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500

        return jsonify({"status": "success", "message": "Item purchased and journey stamps added"})

    # ---------------------------------------------------------
    # Leaderboard
    # ---------------------------------------------------------
    @app.route("/leaderboard")
    def leaderboard():
        wallet_pk = session.get("wallet_public_key")
        from sqlalchemy import desc
        top_users = User.query.order_by(desc(User.loyalty_points)).limit(20).all()
        return render_template(
            "leaderboard.html",
            users=top_users,
            wallet_public_key=wallet_pk
        )
