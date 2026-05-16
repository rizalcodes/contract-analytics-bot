"""
config.py - Centralized Configuration
Web3 Python Toolkit by Rizal
Semua API key & settings ada di sini
"""

import os

# ─────────────────────────────────────────────
# API KEYS — set via environment variable
# Jangan pernah hardcode di sini!
# ─────────────────────────────────────────────
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "Your_Etherscan_Api_Key_Here")
INFURA_URL        = os.getenv("INFURA_URL",        "https://mainnet.infura.io/v3/Your_Infura_Api_Key_Here")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN",    "Your_Bot_token_Here")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID",  "Your_Chat_ID_Here")

# ─────────────────────────────────────────────
# NETWORK CONFIG
# ─────────────────────────────────────────────
CHAIN_ID   = 1        # 1 = Ethereum mainnet, 137 = Polygon, 56 = BSC
DAYS_BACK  = 7        # default periode analisis
TOP_N      = 10       # default top callers
ALERT_INTERVAL_MIN = 30   # interval auto alert (menit)

# ─────────────────────────────────────────────
# PRESET CONTRACTS
# ─────────────────────────────────────────────
PRESET_CONTRACTS = {
    "uniswap_v2" : "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "uniswap_v3" : "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "aave_v3"    : "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "compound"   : "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
}

# ─────────────────────────────────────────────
# THE GRAPH ENDPOINTS
# ─────────────────────────────────────────────
GRAPH_ENDPOINTS = {
    "uniswap_v3" : "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
    "aave_v3"    : "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
    "compound"   : "https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2",
}

# ─────────────────────────────────────────────
# ANOMALY DETECTION SETTINGS
# ─────────────────────────────────────────────
ANOMALY_SIGMA     = 2.0   # threshold standar deviasi (2σ = 95%)
ANOMALY_MAX_ALERT = 3     # max alert per cycle biar tidak spam

# ─────────────────────────────────────────────
# VALIDATE — cek key yang wajib ada
# ─────────────────────────────────────────────
def validate():
    missing = []
    if not ETHERSCAN_API_KEY: missing.append("AW8AJ3TQV79VTM1WM9KY7W9H5ICZZ1WUYT")
    if not INFURA_URL:         missing.append("https://mainnet.infura.io/v3/e1576449bd6142eba99fd3cc4f3fe7b3")
    if not TELEGRAM_TOKEN:     missing.append("8660442841:AAEOXjIzvJA3xSKh0DHi_V9jLXeEshO2L2k")

    if missing:
        print("⚠️  Environment variables belum di-set:")
        for m in missing:
            print(f"   - {m}")
        print("\nCara set di PowerShell:")
        print('   $env:ETHERSCAN_API_KEY = "AW8AJ3TQV79VTM1WM9KY7W9H5ICZZ1WUYT"')
        print('   $env:INFURA_URL        = "https://mainnet.infura.io/v3/e1576449bd6142eba99fd3cc4f3fe7b3"')
        print('   $env:TELEGRAM_TOKEN    = "8660442841:AAEOXjIzvJA3xSKh0DHi_V9jLXeEshO2L2k"')
        return False
    return True


if __name__ == "__main__":
    if validate():
        print("✅ Semua config OK!")
    else:
        print("\n❌ Config belum lengkap.")
