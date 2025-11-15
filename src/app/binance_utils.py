# src/app/binance_utils.py
from binance.client import Client
from .config import BINANCE_API_KEY, BINANCE_API_SECRET, BINANCE_NETWORK

# Initialize Binance client
client = Client(BINANCE_API_KEY, BINANCE_API_SECRET)

def get_balance(asset="USDT"):
    """Get the available balance of a specific asset."""
    info = client.get_asset_balance(asset)
    if info:
        return float(info['free'])
    return 0.0

def get_deposit_address(asset="USDT", network=None):
    """Get deposit address for the platform wallet."""
    if network is None:
        network = BINANCE_NETWORK
    info = client.get_deposit_address(asset=asset, network=network)
    return info['address']

def withdraw(asset="USDT", amount=0.0, address=None, network=None):
    """Withdraw to a specified address (e.g., user withdrawal)."""
    if network is None:
        network = BINANCE_NETWORK
    result = client.withdraw(asset=asset, address=address, amount=amount, network=network)
    return result
