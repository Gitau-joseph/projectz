from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# ------------------------------------------------
# Load environment variables (.env works locally AND on Render)
# ------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)
print(f"[INIT] Loaded .env from: {ENV_PATH}")

# ------------------------------------------------
# Initialize extensions
# ------------------------------------------------
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # ------------------------------------------------
    # SECRET KEY
    # ------------------------------------------------
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback-secret-key")

    # ------------------------------------------------
    # DATABASE (works locally + Render)
    # ------------------------------------------------
    db_path = os.path.join(BASE_DIR, "platform.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # ------------------------------------------------
    # BINANCE WALLET SETTINGS
    # ------------------------------------------------
    app.config["BINANCE_MASTER_ADDRESS"] = os.getenv("BINANCE_MASTER_ADDRESS")
    app.config["BINANCE_NETWORK"] = os.getenv("BINANCE_NETWORK", "TRC20")

    # ------------------------------------------------
    # Initialize Flask extensions
    # ------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    # ------------------------------------------------
    # Register blueprints (MATCHED to your structure)
    # ------------------------------------------------
    from src.app.routes import main
    from src.app.admin import admin

    app.register_blueprint(main)
    app.register_blueprint(admin)

    # ------------------------------------------------
    # Create database tables
    # ------------------------------------------------
    with app.app_context():
        db.create_all()
        print("[INIT] Database initialized:", db_path)
        print("[INIT] Master Wallet:", app.config["BINANCE_MASTER_ADDRESS"])
        print("[INIT] Network:", app.config["BINANCE_NETWORK"])

    return app

