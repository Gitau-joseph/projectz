# src/app/config.py
import os
from dotenv import load_dotenv

# -------------------------
# Load .env explicitly
# -------------------------
DOTENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
load_dotenv(DOTENV_PATH)

# -------------------------
# Binance API keys (use environment variables for security)
# -------------------------
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY', 'your_api_key_here')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET', 'your_api_secret_here')

# -------------------------
# Binance wallet address for deposits
# -------------------------
BINANCE_MASTER_ADDRESS = os.getenv('BINANCE_MASTER_ADDRESS', None)

# Network for deposits/withdrawals (TRC20, BEP20, ERC20, etc.)
BINANCE_NETWORK = os.getenv('BINANCE_NETWORK', 'TRC20')

# Optional: fallback secret key for Flask
SECRET_KEY = os.getenv('SECRET_KEY', 'supersecretkey123')

# -------------------------
# Investment settings
# -------------------------
WEEKLY_INTEREST_RATE = float(os.getenv('WEEKLY_INTEREST_RATE', 0.02))  # 2% per week
MIN_INVEST_DAYS = int(os.getenv('MIN_INVEST_DAYS', 60))                # 60 days minimum for withdrawals