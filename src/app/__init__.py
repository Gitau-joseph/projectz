from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv
import os

# -------------------------
# Initialize extensions
# -------------------------
db = SQLAlchemy()
login_manager = LoginManager()

# -------------------------
# Explicitly load .env from your project path
# -------------------------
# Make sure the file is named ".env" (NOT ".env.txt")
DOTENV_PATH = r"C:\Users\hp\Desktop\Gn Joe\src\.env"
loaded = load_dotenv(DOTENV_PATH)
print(f"Loading .env from: {DOTENV_PATH} -> Success: {loaded}")

# Test environment variables immediately
print("Master Address:", os.getenv("BINANCE_MASTER_ADDRESS"))
print("Network:", os.getenv("BINANCE_NETWORK"))

def create_app():
    app = Flask(__name__)

    # -------------------------
    # Security and Configuration
    # -------------------------
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'supersecretkey123')

    # Database
    BASE_DIR = r"C:\Users\hp\Desktop\Gn Joe"
    DB_PATH = os.path.join(BASE_DIR, "platform.db")
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{DB_PATH}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # -------------------------
    # Binance Wallet Settings (from .env)
    # -------------------------
    app.config['BINANCE_MASTER_ADDRESS'] = os.getenv('BINANCE_MASTER_ADDRESS')
    app.config['BINANCE_NETWORK'] = os.getenv('BINANCE_NETWORK', 'TRC20')

    # -------------------------
    # Initialize extensions
    # -------------------------
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'  # updated to your main blueprint

    # -------------------------
    # Register Blueprints
    # -------------------------
    from src.app.routes import main
    from src.app.admin import admin
    app.register_blueprint(main)
    app.register_blueprint(admin)

    # -------------------------
    # Create database tables
    # -------------------------
    with app.app_context():
        db.create_all()
        print(f"? Database initialized at: {DB_PATH}")
        print(f"? Binance Wallet: {app.config['BINANCE_MASTER_ADDRESS']}")
        print(f"? Network: {app.config['BINANCE_NETWORK']}")

    return app