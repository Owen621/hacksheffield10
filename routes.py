from flask import Flask, request, jsonify, session, render_template, redirect, url_for, g
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
    "resold",
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
            # Pass brands list to template for dropdown
            return render_template("add_item.html", wallet_public_key=wallet_pk, brands=BRANDS)

        # POST: form data
        name = request.form.get("name")
        image_file = request.files.get("image")
        image_filename = None
        image_MIME = None
        description = request.form.get("description")
        brand = request.form.get("brand")
        price = request.form.get("price")

        # Validation
        if not name:
            return jsonify({"error": "Missing name"}), 400
        if not brand or brand not in BRANDS:
            return jsonify({"error": "Invalid or missing brand"}), 400

        # Save image if provided
        #if image_file and allowed_file(image_file.filename):
            #filename = f"{wallet_pk}_{secure_filename(image_file.filename)}"
            #os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            #file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            #image_file.save(file_path)
            #image_filename = filename
        
        if image_file and allowed_file(image_file.filename):
            image_MIME = secure_filename(image_file.filename)
            image_filename = f"{wallet_pk}_{image_MIME}"
        



        # Mint NFT via Node script (add brand argument if needed)
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
                image_MIME = image_MIME,
                image_data = image_file.read(),
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


    @app.route("/my_items")
    def my_items():
        wallet_pk = session.get("wallet_public_key")
        if not wallet_pk:
            return redirect("/")

        items = Item.query.filter_by(ownerPublicKey=wallet_pk).all()

        # Add total points for each item
        for item in items:
            item.total_points = JourneyStamp.query.filter_by(item_mint=item.solanaMint).count()
            item.image_data_base64 = base64.b64encode(item.image_data).decode('utf-8')

        return render_template(
            "my_items.html",
            items=items,
            wallet_public_key=wallet_pk,
            total_items=len(items),
            limit=6  # default pagination limit
        )



    # All Items
    # ---------------------------------------------------------
    @app.route("/all_items")
    def all_items():
        wallet_pk = session.get("wallet_public_key")
        items = Item.query.all()

        # Compute total points per item by counting related JourneyStamps
        for item in items:
            item.total_points = JourneyStamp.query.filter_by(item_mint=item.solanaMint).count()
            item.image_data_base64 = base64.b64encode(item.image_data).decode('utf-8')


        return render_template(
            "all_items.html",
            items=items,
            wallet_public_key=wallet_pk,
            total_items=len(items),
            limit=6  # default pagination limit
        )



    # ---------------------------------------------------------
    # View single item
    # ---------------------------------------------------------


    @app.route("/item/<mint_address>")
    def item_page(mint_address):
        wallet_pk = session.get("wallet_public_key")

        # Get item
        item = Item.query.get(mint_address)
        if not item:
            return "Item not found", 404

        # All journey stamps for this item
        stamps = JourneyStamp.query.filter_by(item_mint=mint_address).order_by(JourneyStamp.timestamp.desc()).all()

        # Loyalty points for the connected user (specific to this item)
        item_points = 0
        if wallet_pk:
            item_points = JourneyStamp.query.filter_by(item_mint=mint_address, user_wallet=wallet_pk).count()

        # Aggregate loyalty points for all users on this item
        from sqlalchemy import func
        user_points = (
            JourneyStamp.query
            .with_entities(JourneyStamp.user_wallet, func.count(JourneyStamp.id).label("points"))
            .filter_by(item_mint=mint_address)
            .group_by(JourneyStamp.user_wallet)
            .all()
        )

        item.image_data_base64 = base64.b64encode(item.image_data).decode('utf-8')

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


    @app.route("/add_stamp", methods=["POST"])
    def add_stamp():
        data = request.json
        wallet = data.get("wallet")  # Phantom public key
        item_mint = data.get("item_mint")
        event = data.get("event")

        if event not in JOURNEY_EVENTS:
            return jsonify({"error": "Invalid event"}), 400

        # Ensure user exists
        user = User.query.get(wallet)
        if not user:
            user = User(wallet=wallet, loyalty_points=0)
            db.session.add(user)

        # Ensure item exists
        item = Item.query.get(item_mint)
        if not item:
            return jsonify({"error": "Item not found"}), 404

        # Add journey stamp
        stamp = JourneyStamp(item_mint=item_mint, user_wallet=wallet, event=event)
        db.session.add(stamp)

        # Increment loyalty points (1 per stamp)
        user.loyalty_points += 1

        # Commit DB changes first
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return jsonify({"success": False, "error": f"Database error: {str(e)}"}), 500

        # Transfer 1 loyalty token on-chain
        try:
            result = subprocess.run(
                ["node", "static/js/transfer_loyalty_token.js", wallet],
                capture_output=True,
                text=True,
                check=True
            )

            transfer_output = result.stdout
            transfer_data = json.loads(transfer_output)
            if not transfer_data.get("success"):
                print("On-chain loyalty transfer failed:", transfer_data.get("error"))
        except Exception as e:
            print("On-chain loyalty transfer failed:", e)

        return jsonify({
            "message": f"Journey stamp '{event}' added!",
            "loyalty_points": user.loyalty_points
        })
    

        # ---------------------------------------------------------
    # Leaderboard
    # ---------------------------------------------------------
    @app.route("/leaderboard")
    def leaderboard():
        wallet_pk = session.get("wallet_public_key")

        # Query top users by loyalty points, descending order
        from sqlalchemy import desc
        top_users = User.query.order_by(desc(User.loyalty_points)).limit(20).all()  # top 20

        return render_template(
            "leaderboard.html",
            users=top_users,
            wallet_public_key=wallet_pk
        )
