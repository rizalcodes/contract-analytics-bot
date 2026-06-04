"""
analytic_bot.py - All-in-One Crypto Bot
Web3 Python Toolkit by Rizal
Contract Analytics + Subscription + Portfolio + MEV + Yield + Token Sniffer + Whale Tracker + NFT Floor Tracker + Gas Price Predictor + Arbitrage Scanner + DAO Governance Tracker + Cross-Chain Bridge Monitor
"""

import os
import sys
import json
import time 
import logging
import requests
import threading
import importlib
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import Counter, defaultdict, deque
from web3 import Web3

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# IMPORT CONTRACT ANALYTICS
# ─────────────────────────────────────────────
try:
    sys.path.insert(0, r"C:\Users\Administrator\Documents\contract_analytics.py")
    ca = importlib.import_module("contract_analytics")
    ContractAnalytics = ca.ContractAnalytics
    TelegramNotifier  = ca.TelegramNotifier
    log.info("✅ contract_analytics imported")
except Exception as e:
    log.warning(f"contract-analytics not found: {e}")
    ContractAnalytics = None
    TelegramNotifier  = None

# ─────────────────────────────────────────────
# IMPORT TOKEN SNIFFER
# ─────────────────────────────────────────────
try:
    ts = importlib.import_module("token_sniffer")
    TokenAnalyzer = ts.TokenAnalyzer
    log.info("✅ token_sniffer imported")
except Exception as e:
    log.warning(f"token_sniffer not found: {e}")
    TokenAnalyzer = None

# ─────────────────────────────────────────────
# IMPORT WHALE TRACKER
# ─────────────────────────────────────────────
try:
    ww = importlib.import_module("whale_wallet_copier")
    WhaleTracker = ww.WhaleTracker
    log.info("✅ whale_wallet_copier imported")
except Exception as e:
    log.warning(f"whale_wallet_copier not found: {e}")
    WhaleTracker = None

# ─────────────────────────────────────────────
# IMPORT NFT FLOOR TRACKER
# ─────────────────────────────────────────────
try:
    nft = importlib.import_module("nft_floor_tracker")
    NFTFloorTracker = nft.NFTFloorTracker
    log.info("✅ nft_floor_tracker imported")
except Exception as e:
    log.warning(f"nft_floor_tracker not found: {e}")
    NFTFloorTracker = None

# ─────────────────────────────────────────────
# IMPORT GAS PRICE PREDICTOR
# ─────────────────────────────────────────────
try:
    gp = importlib.import_module("gas_price_predictor")
    GasPredictor = gp.GasPredictor
    log.info("✅ gas_price_predictor imported")
except Exception as e:
    log.warning(f"gas_price_predictor not found: {e}")
    GasPredictor = None

# ─────────────────────────────────────────────
# IMPORT ARBITRAGE SCANNER
# ─────────────────────────────────────────────
try:
    arb = importlib.import_module("arbitrage_scanner")
    ArbitrageEngine = arb.ArbitrageEngine
    log.info("✅ arbitrage_scanner imported")
except Exception as e:
    log.warning(f"arbitrage_scanner not found: {e}")
    ArbitrageEngine = None

# ─────────────────────────────────────────────
# IMPORT DAO GOVERNANCE TRACKER
# ─────────────────────────────────────────────
try:
    gov = importlib.import_module("dao_governance_tracker")
    GovernanceAnalyzer   = gov.GovernanceAnalyzer
    DAOS                 = gov.DAOS
    POLL_INTERVAL        = gov.POLL_INTERVAL
    DEADLINE_ALERT_HOURS = gov.DEADLINE_ALERT_HOURS
    log.info("✅ dao_governance_tracker imported")
except Exception as e:
    log.warning(f"dao_governance_tracker not found: {e}")
    GovernanceAnalyzer   = None
    DAOS                 = {}
    POLL_INTERVAL        = 300
    DEADLINE_ALERT_HOURS = 24


# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
TELEGRAM_TOKEN    = "Your_Telegram_Bot_Token_Here"
ADMIN_CHAT_ID     = "Your_Chat_ID_Here"
USDT_TRC20        = "TNxivKGm18XCYtgM2TMewNompRnBqfPjFY"
OPENSEA_API_KEY   = "Your_Opensea_Api_Key_Here"
ETHERSCAN_API_KEY = "Your_Etherscan_Api_Here"
INFURA_URL        = "https://mainnet.infura.io/v3/Your_Infure_Key_Here"

PRESET_CONTRACTS = {
    "uniswap_v2" : "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "uniswap_v3" : "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "aave_v3"    : "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "compound"   : "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
}

PLANS = {
    "basic": {
        "name": "Basic", "price": 10, "duration": 30, "contracts": 1,
        "features": ["1 contract monitored", "Daily usage report", "Anomaly detection", "7-day trend analysis"]
    },
    "pro": {
        "name": "Pro", "price": 25, "duration": 30, "contracts": 5,
        "features": ["Up to 5 contracts", "All Basic features", "Top caller ranking", "24h vs 7d trend", "Priority support"]
    },
    "premium": {
        "name": "Premium", "price": 50, "duration": 30, "contracts": 999,
        "features": ["Unlimited contracts", "All Pro features", "Custom alert thresholds", "ABI decoder", "VIP support"]
    }
}

DB_FILE = "subscribers.json"

# ─────────────────────────────────────────────
# MEV CONFIG
# ─────────────────────────────────────────────
KNOWN_MEV_BOTS = {
    "0x00000000003b3cc22af3ae1eac0440bcee416b40": "MEV Bot (Generalized)",
    "0x000000000035b5e5ad9019092c665357240f594d": "MEV Bot (Sandwich)",
    "0xae2fc483527b8ef99eb5d9b44875f005ba1fae13": "Jaredfromsubway.eth",
    "0x6b75d8af000000e20b7a7ddf000ba900b4009a80": "MEV Bot (Arbitrage)",
}

DEX_ROUTERS = {
    "0x7a250d5630b4cf539739df2c5dacb4c659f2488d": "Uniswap V2",
    "0xe592427a0aece92de3edee1f18e0157c05861564": "Uniswap V3",
    "0xd9e1ce17f2641f24ae83637ab66a2cca9c378b9f": "SushiSwap",
    "0x1111111254eeb25477b68fb85ed929f73a960582": "1inch V5",
}

MEV_SELECTORS = {
    "0x7ff36ab5": "swapExactETHForTokens",
    "0x18cbafe5": "swapExactTokensForETH",
    "0x38ed1739": "swapExactTokensForTokens",
    "0xfb3bdb41": "swapETHForExactTokens",
    "0x414bf389": "exactInputSingle (V3)",
}

MIN_GAS_PREMIUM     = 1.5
SANDWICH_WINDOW     = 3
WHALE_POLL_INTERVAL = 15
MAX_WHALE_WALLETS   = 10
NFT_POLL_INTERVAL   = 300
GAS_POLL_INTERVAL   = 60
GAS_LOW_THRESHOLD   = 15
GAS_HIGH_THRESHOLD  = 100
ARB_POLL_INTERVAL   = 120
ARB_MIN_PROFIT      = 5.0
GOV_POLL_INTERVAL   = 300
BRIDGE_POLL_INTERVAL= 300

KNOWN_WHALES = {
    "0xd8da6bf26964af9d7eed9e03e53415d37aa96045": "Vitalik Buterin",
    "0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503": "Binance Whale",
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance Hot Wallet",
    "0x21a31ee1afc51d94c2efccaa2092ad1028285549": "Binance Cold Wallet",
    "0x9696f59e4d72e237be84ffd425dcad154bf96976": "Wintermute",
}

KNOWN_NFT_COLLECTIONS = {
    "boredapeyachtclub"     : "Bored Ape Yacht Club",
    "cryptopunks"           : "CryptoPunks",
    "mutant-ape-yacht-club" : "Mutant Ape Yacht Club",
    "azuki"                 : "Azuki",
    "pudgypenguins"         : "Pudgy Penguins",
    "clonex"                : "Clone X",
    "milady"                : "Milady Maker",
    "degods"                : "DeGods",
}

TX_GAS_UNITS = {
    "ETH Transfer"    : 21000,
    "ERC-20 Transfer" : 65000,
    "Uniswap Swap"    : 150000,
    "NFT Mint"        : 200000,
    "Contract Deploy" : 500000,
}

ARB_TRACKED_TOKENS = {
    "WETH" : "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "USDC" : "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "USDT" : "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "DAI"  : "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    "WBTC" : "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
    "LINK" : "0x514910771AF9Ca656af840dff83E8264EcF986CA",
    "UNI"  : "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
    "AAVE" : "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
    "CRV"  : "0xD533a949740bb3306d119CC777fa900bA034cd52",
    "MKR"  : "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
}

# ─────────────────────────────────────────────
# BRIDGE CONFIG
# ─────────────────────────────────────────────
BRIDGES = {
    "stargate"  : {"name": "Stargate",     "color": "⭐", "token": "STG",  "coingecko": "stargate-finance",  "lifi_key": "stargate", "website": "https://stargate.finance",        "chains": ["Ethereum","BSC","Polygon","Avalanche","Arbitrum","Optimism","Base"],   "description": "Native asset bridge built on LayerZero"},
    "hop"       : {"name": "Hop Protocol", "color": "🐰", "token": "HOP",  "coingecko": "hop-protocol",      "lifi_key": "hop",      "website": "https://hop.exchange",            "chains": ["Ethereum","Polygon","Arbitrum","Optimism","Gnosis","Base"],             "description": "Fast cross-rollup token bridge"},
    "across"    : {"name": "Across",       "color": "🌉", "token": "ACX",  "coingecko": "across-protocol",   "lifi_key": "across",   "website": "https://across.to",               "chains": ["Ethereum","Polygon","Arbitrum","Optimism","Base","ZkSync"],             "description": "Intent-based bridge, fastest UX"},
    "celer"     : {"name": "Celer cBridge","color": "🔵", "token": "CELR", "coingecko": "celer-network",     "lifi_key": "cbridge",  "website": "https://cbridge.celer.network",   "chains": ["Ethereum","BSC","Polygon","Avalanche","Arbitrum","Optimism"],           "description": "Multi-chain liquidity network"},
    "synapse"   : {"name": "Synapse",      "color": "🔴", "token": "SYN",  "coingecko": "synapse-2",         "lifi_key": "synapse",  "website": "https://synapseprotocol.com",     "chains": ["Ethereum","BSC","Polygon","Avalanche","Arbitrum","Optimism"],           "description": "Cross-chain AMM & bridge"},
    "wormhole"  : {"name": "Wormhole",     "color": "🌀", "token": "W",    "coingecko": "wormhole",          "lifi_key": "wormhole", "website": "https://wormhole.com",            "chains": ["Ethereum","BSC","Polygon","Avalanche","Solana","Arbitrum"],             "description": "Generic messaging bridge for many chains"},
    "axelar"    : {"name": "Axelar",       "color": "🔮", "token": "AXL",  "coingecko": "axelar",            "lifi_key": "axelar",   "website": "https://axelar.network",          "chains": ["Ethereum","BSC","Polygon","Avalanche","Cosmos","Arbitrum"],             "description": "Interchain communication protocol"},
    "debridge"  : {"name": "deBridge",     "color": "🟣", "token": "DBR",  "coingecko": "debridge",          "lifi_key": "deBridge", "website": "https://debridge.finance",        "chains": ["Ethereum","BSC","Polygon","Avalanche","Arbitrum","Solana"],             "description": "Zero-TVL intent-based bridge"},
}

BRIDGE_CHAIN_IDS = {
    "Ethereum" : 1,
    "BSC"      : 56,
    "Polygon"  : 137,
    "Avalanche": 43114,
    "Arbitrum" : 42161,
    "Optimism" : 10,
    "Base"     : 8453,
    "Fantom"   : 250,
    "Gnosis"   : 100,
    "ZkSync"   : 324,
}

BRIDGE_TVL_DROP_ALERT = 10.0
BRIDGE_TVL_PUMP_ALERT = 20.0


# ─────────────────────────────────────────────
# PORTFOLIO TRACKER CLASSES
# ─────────────────────────────────────────────
class PriceClient:
    BASE = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session   = requests.Session()
        self._cache    = {}
        self._cache_ts = {}

    def get_eth_price(self) -> float:
        try:
            now = time.time()
            if "eth" in self._cache and now - self._cache_ts.get("eth", 0) < 300:
                return self._cache["eth"]
            r = self.session.get(
                f"{self.BASE}/simple/price",
                params={"ids": "ethereum", "vs_currencies": "usd"},
                timeout=10
            )
            price = r.json().get("ethereum", {}).get("usd", 0)
            self._cache["eth"]    = price
            self._cache_ts["eth"] = now
            return price
        except Exception:
            return 0

    def get_token_price(self, contract_address: str) -> float:
        try:
            r = self.session.get(
                f"{self.BASE}/simple/token_price/ethereum",
                params={"contract_addresses": contract_address.lower(), "vs_currencies": "usd"},
                timeout=10
            )
            return r.json().get(contract_address.lower(), {}).get("usd", 0)
        except Exception:
            return 0


class PortfolioEtherscan:
    BASE = "https://api.etherscan.io/v2/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def _get(self, params: dict) -> dict:
        params["apikey"]  = self.api_key
        params["chainid"] = 1
        try:
            r = self.session.get(self.BASE, params=params, timeout=15)
            return r.json()
        except Exception:
            return {}

    def get_eth_balance(self, address: str) -> float:
        data = self._get({"module": "account", "action": "balance", "address": address, "tag": "latest"})
        try:
            return int(data.get("result", 0)) / 1e18
        except Exception:
            return 0

    def get_token_balances(self, address: str) -> list:
        data = self._get({"module": "account", "action": "tokentx", "address": address, "sort": "desc"})
        txs  = data.get("result", [])
        if not isinstance(txs, list):
            return []
        tokens = {}
        for tx in txs:
            contract = tx.get("contractAddress", "").lower()
            decimals = int(tx.get("tokenDecimal", 18))
            value    = int(tx.get("value", 0))
            if contract not in tokens:
                tokens[contract] = {"symbol": tx.get("tokenSymbol",""), "name": tx.get("tokenName",""), "contract": contract, "decimals": decimals, "balance": 0}
            if tx.get("to","").lower() == address.lower():
                tokens[contract]["balance"] += value
            elif tx.get("from","").lower() == address.lower():
                tokens[contract]["balance"] -= value
        result = []
        for contract, d in tokens.items():
            bal = d["balance"] / (10 ** d["decimals"])
            if bal > 0:
                result.append({**d, "balance": round(bal, 6)})
        return result

    def get_nft_holdings(self, address: str) -> list:
        data = self._get({"module": "account", "action": "tokennfttx", "address": address, "sort": "desc"})
        txs  = data.get("result", [])
        if not isinstance(txs, list):
            return []
        nfts = {}
        for tx in txs:
            key = f"{tx.get('contractAddress','').lower()}_{tx.get('tokenID','')}"
            if tx.get("to","").lower() == address.lower():
                nfts[key] = {"name": tx.get("tokenName",""), "symbol": tx.get("tokenSymbol",""), "token_id": tx.get("tokenID","")}
            elif tx.get("from","").lower() == address.lower() and key in nfts:
                del nfts[key]
        return list(nfts.values())


class PortfolioAnalyzer:
    def __init__(self, etherscan_key: str, infura_url: str):
        self.etherscan = PortfolioEtherscan(etherscan_key)
        self.prices    = PriceClient()
        self.w3        = Web3(Web3.HTTPProvider(infura_url))

    def analyze(self, address: str) -> dict:
        log.info(f"💼 Analyzing portfolio: {address[:10]}...")
        try:
            eth_bal = float(self.w3.eth.get_balance(Web3.to_checksum_address(address))) / 1e18
        except Exception:
            eth_bal = self.etherscan.get_eth_balance(address)
        eth_price   = self.prices.get_eth_price()
        eth_value   = eth_bal * eth_price
        tokens      = self.etherscan.get_token_balances(address)
        token_total = 0
        for t in tokens[:20]:
            price = self.prices.get_token_price(t["contract"])
            t["price_usd"] = price
            t["value_usd"] = round(t["balance"] * price, 2)
            token_total   += t["value_usd"]
        tokens      = sorted(tokens, key=lambda x: x.get("value_usd", 0), reverse=True)
        nfts        = self.etherscan.get_nft_holdings(address)
        total_value = eth_value + token_total
        return {
            "address"  : address,
            "timestamp": datetime.now().isoformat(),
            "eth"      : {"balance": round(eth_bal, 6), "price_usd": eth_price, "value_usd": round(eth_value, 2)},
            "tokens"   : tokens,
            "nfts"     : nfts,
            "summary"  : {
                "total_value_usd": round(total_value, 2),
                "eth_value"      : round(eth_value, 2),
                "token_value"    : round(token_total, 2),
                "nft_count"      : len(nfts),
                "token_count"    : len(tokens),
            }
        }


# ─────────────────────────────────────────────
# SUBSCRIBER DATABASE
# ─────────────────────────────────────────────
class SubscriberDB:
    def __init__(self):
        self.db_file = DB_FILE
        self.data    = self._load()

    def _load(self) -> dict:
        if Path(self.db_file).exists():
            try:
                with open(self.db_file, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"subscribers": {}, "pending": {}, "stats": {"total_revenue": 0, "total_subscribers": 0}}

    def _save(self):
        with open(self.db_file, "w") as f:
            json.dump(self.data, f, indent=2, default=str)

    def add_subscriber(self, chat_id: str, plan: str, username: str = "") -> dict:
        plan_data = PLANS[plan]
        expiry    = datetime.now() + timedelta(days=plan_data["duration"])
        sub = {
            "chat_id": chat_id, "username": username, "plan": plan,
            "started_at": datetime.now().isoformat(),
            "expires_at": expiry.isoformat(), "active": True, "contracts": [],
        }
        self.data["subscribers"][chat_id] = sub
        self.data["stats"]["total_subscribers"] += 1
        self.data["stats"]["total_revenue"]     += plan_data["price"]
        self._save()
        return sub

    def get_subscriber(self, chat_id: str) -> dict:
        return self.data["subscribers"].get(str(chat_id), {})

    def is_active(self, chat_id: str) -> bool:
        sub = self.get_subscriber(str(chat_id))
        if not sub or not sub.get("active"):
            return False
        return datetime.now() < datetime.fromisoformat(sub["expires_at"])

    def is_admin(self, chat_id: str) -> bool:
        return str(chat_id) == str(ADMIN_CHAT_ID)

    def revoke(self, chat_id: str):
        if str(chat_id) in self.data["subscribers"]:
            self.data["subscribers"][str(chat_id)]["active"] = False
            self._save()

    def extend(self, chat_id: str, days: int):
        sub = self.get_subscriber(str(chat_id))
        if sub:
            expiry = datetime.fromisoformat(sub["expires_at"])
            self.data["subscribers"][str(chat_id)]["expires_at"] = (expiry + timedelta(days=days)).isoformat()
            self._save()

    def get_all_active(self) -> list:
        return [s for s in self.data["subscribers"].values()
                if s.get("active") and datetime.now() < datetime.fromisoformat(s["expires_at"])]

    def get_expiring_soon(self, days: int = 3) -> list:
        result = []
        for sub in self.data["subscribers"].values():
            if sub.get("active"):
                delta = datetime.fromisoformat(sub["expires_at"]) - datetime.now()
                if 0 < delta.days <= days:
                    result.append(sub)
        return result

    def expire_old(self) -> list:
        expired = []
        for cid, sub in self.data["subscribers"].items():
            if sub.get("active") and datetime.now() >= datetime.fromisoformat(sub["expires_at"]):
                self.data["subscribers"][cid]["active"] = False
                expired.append(sub)
        if expired: self._save()
        return expired

    def add_pending(self, chat_id: str, plan: str, username: str = ""):
        self.data["pending"][str(chat_id)] = {
            "chat_id": str(chat_id), "username": username, "plan": plan,
            "requested_at": datetime.now().isoformat(), "amount": PLANS[plan]["price"],
        }
        self._save()

    def get_pending(self, chat_id: str) -> dict:
        return self.data["pending"].get(str(chat_id), {})

    def remove_pending(self, chat_id: str):
        self.data["pending"].pop(str(chat_id), None)
        self._save()

    def get_all_pending(self) -> list:
        return list(self.data["pending"].values())

    def get_stats(self) -> dict:
        active = self.get_all_active()
        return {
            "total_subscribers": self.data["stats"]["total_subscribers"],
            "active_now"       : len(active),
            "total_revenue"    : self.data["stats"]["total_revenue"],
            "pending_payments" : len(self.data["pending"]),
        }


# ─────────────────────────────────────────────
# MEV ANALYZER
# ─────────────────────────────────────────────
class MEVAnalyzer:
    def __init__(self, w3: Web3):
        self.w3 = w3

    def scan_block(self, block_number: int) -> dict:
        log.info(f"🎯 MEV scan block #{block_number}...")
        try:
            block = self.w3.eth.get_block(block_number, full_transactions=True)
        except Exception as e:
            return {"error": str(e)}
        txs     = [dict(tx) for tx in block.get("transactions", [])]
        dex_txs = []
        for tx in txs:
            to_addr    = (tx.get("to") or "").lower()
            input_data = tx.get("input", "0x")
            selector   = input_data[:10] if len(input_data) >= 10 else "0x"
            if to_addr in DEX_ROUTERS and selector in MEV_SELECTORS:
                dex_txs.append({
                    "hash"     : tx.get("hash", "").hex() if hasattr(tx.get("hash",""), "hex") else str(tx.get("hash","")),
                    "from"     : (tx.get("from") or "").lower(),
                    "to"       : to_addr,
                    "dex"      : DEX_ROUTERS.get(to_addr, "Unknown"),
                    "function" : MEV_SELECTORS.get(selector, "unknown"),
                    "gas_price": int(tx.get("gasPrice", 0)),
                    "value"    : int(tx.get("value", 0)),
                    "selector" : selector,
                    "index"    : txs.index(tx),
                })
        sandwiches = []
        sender_txs = defaultdict(list)
        for tx in dex_txs:
            sender_txs[tx["from"]].append(tx)
        for sender, stxs in sender_txs.items():
            if len(stxs) >= 2:
                for i in range(len(stxs) - 1):
                    t1, t2 = stxs[i], stxs[i+1]
                    if 1 <= t2["index"] - t1["index"] <= SANDWICH_WINDOW + 1:
                        victims = [t for t in dex_txs if t1["index"] < t["index"] < t2["index"] and t["from"] != sender]
                        if victims:
                            sandwiches.append({
                                "type"        : "SANDWICH",
                                "attacker"    : sender,
                                "front_tx"    : t1["hash"],
                                "back_tx"     : t2["hash"],
                                "victims"     : len(victims),
                                "dex"         : t1["dex"],
                                "is_known_bot": sender in KNOWN_MEV_BOTS,
                                "bot_label"   : KNOWN_MEV_BOTS.get(sender, "Unknown"),
                                "severity"    : "HIGH" if sender in KNOWN_MEV_BOTS else "MEDIUM",
                            })
        arbitrages = []
        for tx in dex_txs:
            if tx["from"] in KNOWN_MEV_BOTS:
                arbitrages.append({
                    "type"     : "ARBITRAGE",
                    "tx_hash"  : tx["hash"],
                    "bot"      : tx["from"],
                    "bot_label": KNOWN_MEV_BOTS[tx["from"]],
                    "dex"      : tx["dex"],
                    "function" : tx["function"],
                    "severity" : "HIGH",
                })
        total = len(sandwiches) + len(arbitrages)
        return {
            "block_number": block_number,
            "timestamp"   : datetime.now().isoformat(),
            "total_txs"   : len(txs),
            "dex_txs"     : len(dex_txs),
            "mev_count"   : total,
            "sandwiches"  : sandwiches,
            "arbitrages"  : arbitrages,
            "summary"     : {
                "sandwich_count" : len(sandwiches),
                "arbitrage_count": len(arbitrages),
                "high_severity"  : sum(1 for m in sandwiches+arbitrages if m.get("severity")=="HIGH"),
            }
        }


# ─────────────────────────────────────────────
# DEFI YIELD AGGREGATOR
# ─────────────────────────────────────────────
class YieldAggregator:
    def __init__(self):
        self.session   = requests.Session()
        self._cache    = []
        self._cache_ts = 0

    def _get_defillama(self, project: str, chain: str = "Ethereum") -> list:
        try:
            r = self.session.get("https://yields.llama.fi/pools", timeout=15)
            pools = r.json().get("data", [])
            results = []
            for pool in pools:
                if project.lower() in pool.get("project","").lower() and pool.get("chain") == chain:
                    apy = float(pool.get("apy", 0))
                    tvl = float(pool.get("tvlUsd", 0))
                    if tvl > 500000 and apy > 0:
                        results.append({
                            "protocol"  : pool.get("project","").replace("-", " ").title(),
                            "asset"     : pool.get("symbol",""),
                            "supply_apy": round(apy, 2),
                            "borrow_apy": round(float(pool.get("apyBorrow") or 0), 2),
                            "tvl_usd"   : round(tvl, 0),
                            "type"      : "lending" if "aave" in project or "compound" in project else "liquidity",
                            "risk"      : "LOW" if "aave" in project or "compound" in project else "MEDIUM",
                        })
            return sorted(results, key=lambda x: x["supply_apy"], reverse=True)[:6]
        except Exception as e:
            log.error(f"DeFi Llama {project} error: {e}")
            return []

    def get_all_yields(self, use_cache: bool = True) -> list:
        now = time.time()
        if use_cache and self._cache and now - self._cache_ts < 600:
            return self._cache
        log.info("🔄 Fetching yield data from DeFi Llama...")
        all_yields = []
        for project in ["aave-v3", "compound", "curve-dex", "uniswap-v3"]:
            all_yields.extend(self._get_defillama(project))
            time.sleep(0.3)
        all_yields     = sorted(all_yields, key=lambda x: x["supply_apy"], reverse=True)
        self._cache    = all_yields
        self._cache_ts = now
        log.info(f"✅ Found {len(all_yields)} yield opportunities")
        return all_yields

    def get_best_yields(self, top_n: int = 10) -> list:
        return self.get_all_yields()[:top_n]

    def get_by_protocol(self, protocol: str) -> list:
        return [y for y in self.get_all_yields() if protocol.lower() in y["protocol"].lower()]

    def get_stable_yields(self) -> list:
        stables = ["USDC", "USDT", "DAI", "FRAX", "BUSD", "LUSD"]
        return [y for y in self.get_all_yields() if any(s in y["asset"].upper() for s in stables)]

    def get_summary(self) -> dict:
        all_yields = self.get_all_yields()
        if not all_yields:
            return {}
        apys = [y["supply_apy"] for y in all_yields]
        return {
            "total"      : len(all_yields),
            "highest_apy": max(apys),
            "lowest_apy" : min(apys),
            "avg_apy"    : round(sum(apys) / len(apys), 2),
            "protocols"  : list(set(y["protocol"] for y in all_yields)),
        }

    def format_yield(self, y: dict, rank: int = 0) -> str:
        rank_str   = f"{rank}. " if rank else "• "
        risk_emoji = "🟢" if y["risk"] == "LOW" else "🟡"
        tvl        = y["tvl_usd"]
        tvl_str    = f"${tvl/1e9:.1f}B" if tvl > 1e9 else f"${tvl/1e6:.1f}M"
        return f"{rank_str}*{y['protocol']}* — {y['asset']}\n   💰 APY: `{y['supply_apy']}%` {risk_emoji} | TVL: `{tvl_str}`"


# ─────────────────────────────────────────────
# BRIDGE CLIENTS (CoinGecko + LI.FI)
# ─────────────────────────────────────────────
class BridgeCoinGeckoClient:
    BASE = "https://api.coingecko.com/api/v3"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept"    : "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; bridge-monitor/3.0)",
        })
        self._cache    = {}
        self._cache_ts = {}

    def get_multi_tokens(self, ids: list) -> dict:
        ids_str = ",".join(ids)
        try:
            r = self.session.get(
                f"{self.BASE}/simple/price",
                params={
                    "ids"                : ids_str,
                    "vs_currencies"      : "usd",
                    "include_market_cap" : "true",
                    "include_24hr_vol"   : "true",
                    "include_24hr_change": "true",
                    "include_7d_change"  : "true",
                },
                timeout=15
            )
            r.raise_for_status()
            data   = r.json()
            result = {}
            for cg_id, vals in data.items():
                result[cg_id] = {
                    "price_usd" : float(vals.get("usd",            0) or 0),
                    "mcap_usd"  : float(vals.get("usd_market_cap", 0) or 0),
                    "vol_24h"   : float(vals.get("usd_24h_vol",    0) or 0),
                    "change_24h": float(vals.get("usd_24h_change", 0) or 0),
                    "change_7d" : float(vals.get("usd_7d_change",  0) or 0),
                }
            return result
        except Exception as e:
            log.error(f"BridgeCoinGecko error: {e}")
            return {}

    def get_token_data(self, coingecko_id: str) -> dict:
        now = time.time()
        if coingecko_id in self._cache and now - self._cache_ts.get(coingecko_id, 0) < 300:
            return self._cache[coingecko_id]
        result = self.get_multi_tokens([coingecko_id])
        data   = result.get(coingecko_id, {})
        if data:
            self._cache[coingecko_id]    = data
            self._cache_ts[coingecko_id] = now
        return data


class BridgeLiFiClient:
    BASE = "https://li.quest/v1"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Accept"    : "application/json",
            "User-Agent": "Mozilla/5.0 (compatible; bridge-monitor/3.0)",
        })
        self._tools_cache    = {}
        self._tools_cache_ts = 0

    def get_tools(self) -> dict:
        now = time.time()
        if self._tools_cache and now - self._tools_cache_ts < 600:
            return self._tools_cache
        try:
            r = self.session.get(f"{self.BASE}/tools", timeout=15)
            r.raise_for_status()
            data = r.json()
            self._tools_cache    = data
            self._tools_cache_ts = now
            return data
        except Exception as e:
            log.error(f"LiFi tools error: {e}")
            return {}

    def get_connections(self, from_chain: int, to_chain: int) -> list:
        try:
            r = self.session.get(
                f"{self.BASE}/connections",
                params={"fromChain": from_chain, "toChain": to_chain},
                timeout=15
            )
            r.raise_for_status()
            return r.json().get("connections", [])
        except Exception as e:
            log.error(f"LiFi connections error: {e}")
            return []

    def find_bridge_tool(self, lifi_key: str) -> dict:
        bridges   = self.get_tools().get("bridges", [])
        key_lower = lifi_key.lower()
        for b in bridges:
            if b.get("key", "").lower() == key_lower or b.get("name", "").lower() == key_lower:
                return b
        return {}


class BridgeMonitorEngine:
    def __init__(self):
        self.coingecko     = BridgeCoinGeckoClient()
        self.lifi          = BridgeLiFiClient()
        self.watchlist     = set()
        self.price_history = defaultdict(list)

    def add_bridge(self, key: str) -> bool:
        if key.lower() not in BRIDGES:
            return False
        self.watchlist.add(key.lower())
        return True

    def remove_bridge(self, key: str):
        self.watchlist.discard(key.lower())

    def get_watched_bridges(self) -> list:
        return list(self.watchlist)

    def get_bridge_info(self, key: str) -> dict:
        key = key.lower()
        if key not in BRIDGES:
            return {}
        b         = BRIDGES[key]
        token     = self.coingecko.get_token_data(b.get("coingecko", ""))
        lifi_tool = self.lifi.find_bridge_tool(b.get("lifi_key", key))
        price     = token.get("price_usd", 0)
        change_24h= token.get("change_24h", 0)
        if price > 0:
            self.price_history[key].append({"price": price, "timestamp": datetime.now().isoformat()})
            if len(self.price_history[key]) > 100:
                self.price_history[key] = self.price_history[key][-100:]
        return {
            "key"           : key,
            "name"          : b["name"],
            "color"         : b["color"],
            "token"         : b["token"],
            "chains"        : b["chains"],
            "website"       : b.get("website", ""),
            "description"   : b.get("description", ""),
            "price_usd"     : price,
            "mcap_usd"      : token.get("mcap_usd", 0),
            "vol_24h_usd"   : token.get("vol_24h", 0),
            "change_24h"    : change_24h,
            "change_7d"     : token.get("change_7d", 0),
            "direction"     : "📈" if change_24h > 0 else "📉" if change_24h < 0 else "➡️",
            "lifi_supported": bool(lifi_tool),
            "timestamp"     : datetime.now().isoformat(),
        }

    def get_all_bridges_overview(self) -> list:
        ids    = [b["coingecko"] for b in BRIDGES.values() if b.get("coingecko")]
        tokens = self.coingecko.get_multi_tokens(ids)
        result = []
        for key, b in BRIDGES.items():
            t    = tokens.get(b.get("coingecko", ""), {})
            mcap = t.get("mcap_usd", 0)
            vol  = t.get("vol_24h", 0)
            chg  = t.get("change_24h", 0)
            result.append({
                "key"    : key,
                "name"   : b["name"],
                "color"  : b["color"],
                "token"  : b["token"],
                "price"  : t.get("price_usd", 0),
                "mcap"   : mcap,
                "vol_24h": vol,
                "change" : chg,
                "chains" : len(b["chains"]),
                "mcap_str": f"${mcap/1e9:.2f}B" if mcap >= 1e9 else f"${mcap/1e6:.1f}M" if mcap >= 1e6 else f"${mcap:,.0f}" if mcap > 0 else "N/A",
                "vol_str" : f"${vol/1e9:.2f}B" if vol >= 1e9 else f"${vol/1e6:.1f}M" if vol >= 1e6 else f"${vol:,.0f}" if vol > 0 else "N/A",
            })
        return sorted(result, key=lambda x: x["mcap"], reverse=True)

    def check_price_alerts(self, key: str, info: dict) -> list:
        alerts = []
        chg    = info.get("change_24h", 0)
        if chg <= -BRIDGE_TVL_DROP_ALERT:
            alerts.append({"type": "PRICE_DROP", "bridge": info["name"], "color": info["color"], "token": info["token"], "change": chg, "severity": "HIGH 🔴" if chg <= -20 else "MEDIUM 🟡"})
        elif chg >= BRIDGE_TVL_PUMP_ALERT:
            alerts.append({"type": "PRICE_PUMP", "bridge": info["name"], "color": info["color"], "token": info["token"], "change": chg, "severity": "HIGH 🟢" if chg >= 50 else "MEDIUM 🟡"})
        return alerts

    def get_bridge_route(self, from_chain: str, to_chain: str) -> list:
        from_id = BRIDGE_CHAIN_IDS.get(from_chain, 0)
        to_id   = BRIDGE_CHAIN_IDS.get(to_chain, 0)
        if not from_id or not to_id:
            return []
        connections = self.lifi.get_connections(from_id, to_id)
        result      = []
        for c in connections[:5]:
            tools = c.get("bridges", []) or c.get("tools", [])
            if tools:
                result.append({"from_chain": from_chain, "to_chain": to_chain, "bridges": tools[:4]})
        return result

    def get_price_trend(self, key: str) -> dict:
        history = self.price_history.get(key, [])
        if len(history) < 2:
            return {"trend": "N/A", "direction": "➡️", "change_pct": 0.0}
        first  = history[0]["price"]
        last   = history[-1]["price"]
        change = round((last - first) / first * 100, 2) if first > 0 else 0.0
        return {
            "trend"     : "RISING" if change > 1 else "FALLING" if change < -1 else "STABLE",
            "direction" : "📈" if change > 1 else "📉" if change < -1 else "➡️",
            "change_pct": change,
        }


# ─────────────────────────────────────────────
# MAIN BOT
# ─────────────────────────────────────────────
class AnalyticsBot:
    def __init__(self):
        self.token   = TELEGRAM_TOKEN
        self.base    = f"https://api.telegram.org/bot{self.token}"
        self.db      = SubscriberDB()
        self.offset  = 0
        self.running = True

        # Analytics state
        self.analytics       = {}
        self.active_contract = {}
        self.alert_enabled   = {}
        self.monitor_thread  = None

        # Portfolio tracker state
        self.portfolio_analyzer = PortfolioAnalyzer(etherscan_key=ETHERSCAN_API_KEY, infura_url=INFURA_URL)
        self.watchlist = {}

        # MEV detector state
        self.mev_w3         = Web3(Web3.HTTPProvider(INFURA_URL))
        self.mev_analyzer   = MEVAnalyzer(self.mev_w3)
        self.mev_monitoring = False
        self.mev_last_block = 0

        # DeFi Yield state
        self.yield_aggregator = YieldAggregator()
        self.yield_alert_on   = False

        # Token Sniffer state
        self.token_analyzer = TokenAnalyzer() if TokenAnalyzer else None

        # Whale Tracker state
        self.whale_tracker    = WhaleTracker() if WhaleTracker else None
        self.whale_monitoring = False

        # NFT Floor Tracker state
        self.nft_tracker    = NFTFloorTracker(OPENSEA_API_KEY) if NFTFloorTracker else None
        self.nft_monitoring = False

        # Gas Price Predictor state
        self.gas_predictor   = GasPredictor(ETHERSCAN_API_KEY, INFURA_URL) if GasPredictor else None
        self.gas_monitoring  = False
        self.gas_low_thresh  = GAS_LOW_THRESHOLD
        self.gas_high_thresh = GAS_HIGH_THRESHOLD

        # Arbitrage Scanner state
        self.arb_engine     = ArbitrageEngine() if ArbitrageEngine else None
        self.arb_monitoring = False

        # DAO Governance Tracker state
        self.gov_analyzer   = GovernanceAnalyzer() if GovernanceAnalyzer else None
        self.gov_monitoring = False

        # Bridge Monitor state
        self.bridge_monitor    = BridgeMonitorEngine()
        self.bridge_monitoring = False

        log.info("🤖 AnalyticsBot (All-in-One) initialized")

    # ─────────────────────────────────────────
    # TELEGRAM HELPERS
    # ─────────────────────────────────────────
    def send(self, chat_id: str, text: str, parse_mode: str = "Markdown"):
        for attempt in range(3):
            try:
                requests.post(
                    f"{self.base}/sendMessage",
                    json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                    timeout=15
                )
                return
            except Exception as e:
                log.error(f"Send error (attempt {attempt+1}): {e}")
                time.sleep(2)

    def get_updates(self) -> list:
        try:
            r = requests.get(
                f"{self.base}/getUpdates",
                params={"offset": self.offset, "timeout": 10},
                timeout=15
            )
            return r.json().get("result", [])
        except Exception:
            return []

    def require_sub(self, chat_id: str) -> bool:
        if self.db.is_admin(chat_id):
            return True
        if self.db.is_active(chat_id):
            return True
        self.send(chat_id, "🔒 *This feature requires an active subscription.*\n\nUse /plans to see pricing or /subscribe to get started!")
        return False

    # ─────────────────────────────────────────
    # FREE COMMANDS
    # ─────────────────────────────────────────
    def cmd_start(self, chat_id: str, username: str):
        if self.db.is_active(chat_id) or self.db.is_admin(chat_id):
            sub  = self.db.get_subscriber(chat_id)
            plan = sub.get("plan", "admin").upper()
            self.send(chat_id, f"👋 *Welcome back, @{username}!*\n\n✅ Plan: *{plan}* — Active\nUse /help to see all available commands.")
        else:
            self.send(chat_id, "👋 *Welcome to Contract Analytics Bot!*\n━━━━━━━━━━━━━━━━━━━━━━\n\nMonitor any Ethereum smart contract in real-time:\n📊 Usage pattern analysis\n🚨 Anomaly detection alerts\n📈 Trend comparison (24h vs 7d)\n👤 Top caller ranking\n🔍 ABI function decoder\n\n━━━━━━━━━━━━━━━━━━━━━━\nUse /plans to see pricing & subscribe!")

    def cmd_help(self, chat_id: str):
        is_admin = self.db.is_admin(chat_id)
        msg = """
🤖 <b>Rizal Crypto Bot — All-in-One</b>
━━━━━━━━━━━━━━━━━━━━━━

🆓 <b>Free Commands:</b>
/start — Welcome &amp; status
/plans — Subscription plans
/subscribe — Subscribe (basic/pro/premium)
/confirm — Confirm payment
/status — Check subscription
/renew — Renew plan

💼 <b>Portfolio Tracker:</b>
/track — Analisis portfolio wallet
/watch — Tambah ke watchlist
/watchlist — Lihat watchlist
/unwatch — Hapus dari watchlist
/refresh — Refresh watchlist

📊 <b>Contract Analytics:</b>
/analyze — Analisis smart contract
/preset — List preset contracts
/use — Gunakan preset
/report — Full analytics report
/top — Top N callers
/trend — 24h vs 7d trend
/alert — Toggle anomaly alerts

🎯 <b>MEV Detector:</b>
/mev — Scan block untuk MEV
/mev_latest — Scan block terbaru
/mev_monitor — Auto monitor MEV
/mev_bots — List known MEV bots

💰 <b>DeFi Yield Aggregator:</b>
/yield — Best yield opportunities
/yield_stable — Stablecoin yields only
/yield_aave — Aave V3 rates
/yield_compound — Compound rates
/yield_curve — Curve pools
/yield_uni — Uniswap V3 pools
/yield_summary — Market overview
/yield_alert — APY spike alerts

🔍 <b>Token Sniffer:</b>
/sniff — Full token safety analysis
/quick — Quick honeypot check

🐋 <b>Whale Tracker:</b>
/whale_add — Add wallet to track
/whale_remove — Remove wallet
/whale_list — Show tracked wallets
/whale_check — Manual check wallet
/whale_monitor — Toggle auto monitor
/whale_whales — Known whale addresses
/whale_alert — Toggle whale alerts

🖼️ <b>NFT Floor Tracker:</b>
/nft_floor — Get floor price
/nft_add — Add collection to watchlist
/nft_remove — Remove collection
/nft_list — Show tracked collections
/nft_sales — Recent sales
/nft_top — Top collections by volume
/nft_search — Search collection
/nft_monitor — Toggle auto monitor
/nft_known — Known collection slugs

⛽ <b>Gas Price Predictor:</b>
/gas — Full gas report + TX cost estimates
/gas_fast — Quick gas check
/gas_estimate — TX cost at custom Gwei
/gas_trend — Gas price trend analysis
/gas_history — Session stats
/gas_monitor — Toggle auto monitor
/gas_threshold — Set alert thresholds

🔄 <b>Arbitrage Scanner:</b>
/arb_scan — Scan all tokens for opportunities
/arb_token — Scan specific token
/arb_top — Top 5 opportunities by profit
/arb_pairs — List tracked token pairs
/arb_monitor — Toggle auto monitor
/arb_stats — Scanner statistics
/arb_settings — Current configuration

🏛️ <b>DAO Governance Tracker:</b>
/gov_proposals — Active proposals per DAO
/gov_proposal — Detail satu proposal
/gov_add — Add DAO ke watchlist
/gov_remove — Remove DAO dari watchlist
/gov_list — Show watched DAOs
/gov_summary — DAO governance overview
/gov_daos — List semua available DAOs
/gov_monitor — Toggle auto monitor
/gov_top — Top active proposals semua DAO

🌉 <b>Cross-Chain Bridge Monitor:</b>
/bridge_info — Bridge token stats &amp; info
/bridge_add — Add bridge to watchlist
/bridge_remove — Remove bridge from watchlist
/bridge_list — Show watched bridges
/bridge_tvl — All bridges overview by mcap
/bridge_route — Available routes between chains
/bridge_monitor — Toggle auto price monitor
/bridge_bridges — List all available bridges
/bridge_chains — List supported chains
        """.strip()

        if is_admin:
            msg += """

👑 <b>Admin Commands:</b>
/admin_list — Semua subscribers
/admin_stats — Revenue dashboard
/admin_approve — Approve payment
/admin_reject — Reject payment
/admin_revoke — Cancel subscription
/admin_extend — Extend subscription"""

        self.send(chat_id, msg, parse_mode="HTML")

    def cmd_plans(self, chat_id: str):
        msg = "💎 *Subscription Plans*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
        for key, plan in PLANS.items():
            features = "\n".join(f"  ✅ {f}" for f in plan["features"])
            msg += f"*{plan['name']} — ${plan['price']}/month*\n{features}\n\n"
        msg += "👉 `/subscribe basic` · `/subscribe pro` · `/subscribe premium`"
        self.send(chat_id, msg)

    def cmd_subscribe(self, chat_id: str, username: str, args: list):
        if self.db.is_active(chat_id):
            self.send(chat_id, "✅ You already have an active subscription!\nUse /status to check details or /renew to extend.")
            return
        if not args:
            self.send(chat_id, "⚠️ Choose a plan:\n`/subscribe basic` — $10/mo\n`/subscribe pro` — $25/mo\n`/subscribe premium` — $50/mo")
            return
        plan = args[0].lower()
        if plan not in PLANS:
            self.send(chat_id, "❌ Invalid plan. Choose: `basic`, `pro`, or `premium`")
            return
        plan_data = PLANS[plan]
        self.db.add_pending(chat_id, plan, username)
        self.send(chat_id, f"💳 *Payment Instructions — {plan_data['name']}*\n━━━━━━━━━━━━━━━━━━━━━━\n\n💰 Amount  : *${plan_data['price']} USDT*\n🌐 Network : *TRC20 (Tron)*\n📋 Address :\n`{USDT_TRC20}`\n\n━━━━━━━━━━━━━━━━━━━━━━\n1️⃣ Send *${plan_data['price']} USDT* via TRC20\n2️⃣ Copy your TX hash/ID after sending\n3️⃣ Send: `/confirm <your_tx_hash>`\n4️⃣ Wait for activation (within 1 hour)\n\n⚠️ TRC20 network only! Other networks = lost funds.")

    def cmd_confirm(self, chat_id: str, username: str, args: list):
        pending = self.db.get_pending(chat_id)
        if not pending:
            self.send(chat_id, "⚠️ No pending subscription. Use `/subscribe <plan>` first.")
            return
        if not args:
            self.send(chat_id, "⚠️ Include TX hash: `/confirm <tx_hash>`")
            return
        tx_hash = args[0]
        plan    = pending["plan"]
        amount  = pending["amount"]
        self.send(chat_id, f"⏳ *Payment submitted!*\n\n📋 Plan    : *{PLANS[plan]['name']}*\n💰 Amount  : *${amount} USDT*\n🔗 TX Hash : `{tx_hash}`\n\nActivation within *1 hour*. You'll get a confirmation message. 🎉")
        self.send(ADMIN_CHAT_ID, f"🔔 *NEW PAYMENT*\n━━━━━━━━━━━━━━━━━━━━━━\n👤 @{username} (`{chat_id}`)\n📋 Plan : *{PLANS[plan]['name']}* (${amount}/mo)\n🔗 TX   : `{tx_hash}`\n\n`/admin_approve {chat_id}` ✅\n`/admin_reject {chat_id}` ❌")

    def cmd_status(self, chat_id: str):
        if self.db.is_admin(chat_id):
            self.send(chat_id, "👑 You are the admin — full access enabled.")
            return
        if not self.db.is_active(chat_id):
            pending = self.db.get_pending(chat_id)
            if pending:
                self.send(chat_id, f"⏳ *{pending['plan'].upper()}* plan pending confirmation.")
            else:
                self.send(chat_id, "❌ No active subscription.\nUse /plans to subscribe!")
            return
        sub       = self.db.get_subscriber(chat_id)
        plan      = PLANS[sub["plan"]]
        expiry    = datetime.fromisoformat(sub["expires_at"])
        days_left = (expiry - datetime.now()).days
        self.send(chat_id, f"📊 *Your Subscription*\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Plan      : *{plan['name']}*\n📅 Expires   : `{expiry.strftime('%Y-%m-%d')}`\n⏳ Days left : *{days_left} days*\n🏷️ Contracts : up to *{plan['contracts']}*\n\nUse /renew to extend anytime!")

    def cmd_renew(self, chat_id: str, username: str):
        sub = self.db.get_subscriber(chat_id)
        if not sub:
            self.send(chat_id, "❌ No subscription found. Use /subscribe to get started!")
            return
        self.cmd_subscribe(chat_id, username, [sub["plan"]])

    # ─────────────────────────────────────────
    # ANALYTICS COMMANDS
    # ─────────────────────────────────────────
    def cmd_analyze(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/analyze 0x...`")
            return
        address = args[0].strip()
        if not address.startswith("0x") or len(address) != 42:
            self.send(chat_id, "❌ Invalid address format.")
            return
        self.send(chat_id, f"🔍 Analyzing `{address}`...\n⏳ Please wait ~30 seconds.")
        try:
            analytics = ContractAnalytics(address)
            self.analytics[chat_id]       = analytics
            self.active_contract[chat_id] = address
            report = analytics.full_report(days_back=7)
            self._send_report(chat_id, report)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_preset(self, chat_id: str):
        if not self.require_sub(chat_id): return
        lines = ["📋 *Preset Contracts:*\n"]
        for name, addr in PRESET_CONTRACTS.items():
            lines.append(f"• `{name}` → `{addr[:10]}...`")
        lines.append("\nUse: `/use <name>`")
        self.send(chat_id, "\n".join(lines))

    def cmd_use(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/use uniswap_v2`")
            return
        name = args[0].lower()
        if name not in PRESET_CONTRACTS:
            self.send(chat_id, f"❌ Unknown preset. Available: {', '.join(f'`{k}`' for k in PRESET_CONTRACTS)}")
            return
        address = PRESET_CONTRACTS[name]
        self.send(chat_id, f"✅ Using *{name}*\n`{address}`\n⏳ Loading...")
        try:
            analytics = ContractAnalytics(address)
            self.analytics[chat_id]       = analytics
            self.active_contract[chat_id] = address
            report = analytics.full_report(days_back=7)
            self._send_report(chat_id, report)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_report(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if chat_id not in self.analytics:
            self.send(chat_id, "⚠️ Use `/analyze` or `/use` first.")
            return
        days = int(args[0]) if args and args[0].isdigit() else 7
        days = max(1, min(days, 30))
        self.send(chat_id, f"📊 Generating {days}d report...")
        try:
            report = self.analytics[chat_id].full_report(days_back=days)
            self._send_report(chat_id, report)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_top(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if chat_id not in self.analytics:
            self.send(chat_id, "⚠️ Use `/analyze` or `/use` first.")
            return
        n = int(args[0]) if args and args[0].isdigit() else 10
        n = max(1, min(n, 20))
        try:
            callers = self.analytics[chat_id].top_callers(days_back=7, top_n=n)
            if not callers:
                self.send(chat_id, "📭 No caller data found.")
                return
            lines = [f"👤 *Top {n} Callers*\n━━━━━━━━━━━━━━━━━━━━━━"]
            for i, c in enumerate(callers, 1):
                addr = c["address"]
                lines.append(f"{i}. `{addr[:6]}...{addr[-4:]}`\n   TXs: `{c['tx_count']}` | Fn: `{c['top_function'][:25]}`")
            self.send(chat_id, "\n".join(lines))
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_trend(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if chat_id not in self.analytics:
            self.send(chat_id, "⚠️ Use `/analyze` or `/use` first.")
            return
        try:
            trend = self.analytics[chat_id].trend_comparison()
            self.send(chat_id, f"📈 *Trend Analysis*\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Last 24h    : `{trend['txs_last_24h']:,}` TXs\n📅 7d Average  : `{trend['avg_daily_7d']:,}` TXs/day\n📉 Change      : `{trend['change_percent']}%`\n🎯 Status      : {trend['trend']}")
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_alert(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            status = "ON ✅" if self.alert_enabled.get(chat_id) else "OFF ❌"
            self.send(chat_id, f"🔔 Auto alert: *{status}*\nUse `/alert on` or `/alert off`")
            return
        if args[0].lower() == "on":
            if chat_id not in self.analytics:
                self.send(chat_id, "⚠️ Use `/analyze` or `/use` first.")
                return
            self.alert_enabled[chat_id] = True
            self.send(chat_id, "✅ *Auto Alert ON* — You'll be notified on anomalies.")
        elif args[0].lower() == "off":
            self.alert_enabled[chat_id] = False
            self.send(chat_id, "❌ *Auto Alert OFF*")

    def _send_report(self, chat_id: str, report: dict):
        usage         = report.get("usage", {})
        trend         = report.get("trend", {})
        anomaly_count = len(report.get("anomalies", []))
        self.send(chat_id, f"📊 *CONTRACT ANALYTICS REPORT*\n━━━━━━━━━━━━━━━━━━━━━━\n🏷️ *{usage.get('contract_name', 'Unknown')}*\n📍 `{usage.get('contract', '')[:20]}...`\n\n📈 *Activity ({usage.get('period_days', 7)}d)*\n- Total TXs     : `{usage.get('total_txs', 0):,}`\n- Unique Callers: `{usage.get('unique_callers', 0):,}`\n- Success Rate  : `{usage.get('success_rate', 0)}%`\n- Avg Gas       : `{usage.get('avg_gas_used', 0):,}`\n\n⚡ *Trend*\n- Last 24h  : `{trend.get('txs_last_24h', 0):,}` TXs\n- 7d Average: `{trend.get('avg_daily_7d', 0):,}` TXs/day\n- Change    : `{trend.get('change_percent', 0)}%` {trend.get('trend', '')}\n\n🚨 *Anomalies* : `{anomaly_count}`")

    # ─────────────────────────────────────────
    # PORTFOLIO TRACKER COMMANDS
    # ─────────────────────────────────────────
    def _send_portfolio_report(self, chat_id: str, data: dict):
        summary = data["summary"]
        eth     = data["eth"]
        tokens  = data["tokens"][:5]
        nfts    = data["nfts"][:3]
        addr    = data["address"]
        msg = f"💼 *PORTFOLIO TRACKER*\n━━━━━━━━━━━━━━━━━━━━━━\n👛 `{addr[:6]}...{addr[-4:]}`\n⏰ {data['timestamp'][:19]}\n\n💰 *Total: ${summary['total_value_usd']:,.2f}*\n━━━━━━━━━━━━━━━━━━━━━━\n🔷 *ETH*\n- Balance : `{eth['balance']} ETH`\n- Price   : `${eth['price_usd']:,.2f}`\n- Value   : `${eth['value_usd']:,.2f}`"
        if tokens:
            msg += "\n\n🪙 *Top Tokens*"
            for t in tokens:
                val = t.get("value_usd", 0)
                msg += f"\n• {t['symbol']}: `{t['balance']}` (~`${val:,.2f}`)" if val > 0 else f"\n• {t['symbol']}: `{t['balance']}`"
        if nfts:
            msg += f"\n\n🖼️ *NFTs ({len(data['nfts'])} total)*"
            for n in nfts:
                msg += f"\n• {n['name']} #{n['token_id']}"
        msg += f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n📊 *Breakdown*\n- ETH    : `${summary['eth_value']:,.2f}`\n- Tokens : `${summary['token_value']:,.2f}` ({summary['token_count']} tokens)\n- NFTs   : `{summary['nft_count']} items`"
        self.send(chat_id, msg)

    def cmd_track(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/track 0x...`")
            return
        address = args[0].strip()
        if not address.startswith("0x") or len(address) != 42:
            self.send(chat_id, "❌ Address tidak valid.")
            return
        self.send(chat_id, f"🔍 Menganalisis portfolio...\n`{address}`\n⏳ Mohon tunggu ~30 detik...")
        try:
            data = self.portfolio_analyzer.analyze(address)
            self._send_portfolio_report(chat_id, data)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_watch(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/watch 0x...`")
            return
        address = args[0].strip()
        if chat_id not in self.watchlist:
            self.watchlist[chat_id] = []
        if address not in self.watchlist[chat_id]:
            self.watchlist[chat_id].append(address)
            self.send(chat_id, f"✅ `{address[:10]}...` ditambahkan ke watchlist!")
        else:
            self.send(chat_id, "⚠️ Address sudah ada di watchlist.")

    def cmd_watchlist(self, chat_id: str):
        if not self.require_sub(chat_id): return
        wl = self.watchlist.get(chat_id, [])
        if not wl:
            self.send(chat_id, "📭 Watchlist kosong.\nGunakan `/watch <address>` untuk menambahkan.")
            return
        lines = ["👀 *Watchlist*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for i, addr in enumerate(wl, 1):
            lines.append(f"{i}. `{addr[:10]}...{addr[-4:]}`")
        self.send(chat_id, "\n".join(lines))

    def cmd_unwatch(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/unwatch 0x...`")
            return
        address = args[0].strip()
        wl = self.watchlist.get(chat_id, [])
        if address in wl:
            wl.remove(address)
            self.watchlist[chat_id] = wl
            self.send(chat_id, f"✅ `{address[:10]}...` dihapus dari watchlist.")
        else:
            self.send(chat_id, "❌ Address tidak ditemukan di watchlist.")

    def cmd_refresh(self, chat_id: str):
        if not self.require_sub(chat_id): return
        wl = self.watchlist.get(chat_id, [])
        if not wl:
            self.send(chat_id, "📭 Watchlist kosong.")
            return
        self.send(chat_id, f"🔄 Refreshing {len(wl)} wallet...")
        for address in wl:
            try:
                data = self.portfolio_analyzer.analyze(address)
                self._send_portfolio_report(chat_id, data)
                time.sleep(2)
            except Exception as e:
                self.send(chat_id, f"❌ Error `{address[:10]}...`: `{str(e)[:100]}`")

    # ─────────────────────────────────────────
    # MEV DETECTOR COMMANDS
    # ─────────────────────────────────────────
    def cmd_mev_scan(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        try:
            block_num = int(args[0]) if args else self.mev_w3.eth.block_number
        except ValueError:
            self.send(chat_id, "❌ Block number harus angka!")
            return
        self.send(chat_id, f"🎯 Scanning block `#{block_num}` untuk MEV...\n⏳ Mohon tunggu ~15 detik...")
        try:
            result = self.mev_analyzer.scan_block(block_num)
            if result.get("error"):
                self.send(chat_id, f"❌ Error: `{result['error']}`")
                return
            summary = result["summary"]
            self.send(chat_id, f"🎯 *MEV SCAN — Block #{block_num}*\n━━━━━━━━━━━━━━━━━━━━━━\n📦 Total TXs   : `{result['total_txs']}`\n🔄 DEX TXs     : `{result['dex_txs']}`\n⚡ MEV Found   : `{result['mev_count']}`\n\n🥪 Sandwiches  : `{summary['sandwich_count']}`\n💱 Arbitrages  : `{summary['arbitrage_count']}`\n🔴 High Risk   : `{summary['high_severity']}`")
            for s in result["sandwiches"][:3]:
                sev   = "🔴" if s["severity"] == "HIGH" else "🟡"
                known = f"\n⚠️ Known: `{s['bot_label']}`" if s["is_known_bot"] else ""
                self.send(chat_id, f"{sev} *SANDWICH ATTACK*\n👤 Attacker: `{s['attacker'][:10]}...`\n🏊 DEX: `{s['dex']}`\n🎯 Victims: `{s['victims']}`{known}")
            for a in result["arbitrages"][:3]:
                self.send(chat_id, f"🔴 *ARBITRAGE — {a['bot_label']}*\n🤖 Bot: `{a['bot'][:10]}...`\n🏊 DEX: `{a['dex']}`\n🔧 Fn: `{a['function']}`")
            if result["mev_count"] == 0:
                self.send(chat_id, "✅ Tidak ada MEV terdeteksi di block ini.")
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_mev_latest(self, chat_id: str):
        if not self.require_sub(chat_id): return
        self.cmd_mev_scan(chat_id, [str(self.mev_w3.eth.block_number)])

    def cmd_mev_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            status = "ON ✅" if self.mev_monitoring else "OFF ❌"
            self.send(chat_id, f"📡 MEV Monitor: *{status}*\nGunakan `/mev_monitor on` atau `/mev_monitor off`")
            return
        if args[0].lower() == "on":
            self.mev_monitoring = True
            self.mev_last_block = self.mev_w3.eth.block_number
            self.send(chat_id, f"✅ *MEV Monitor ON*\nMemantau dari block `#{self.mev_last_block}`")
        elif args[0].lower() == "off":
            self.mev_monitoring = False
            self.send(chat_id, "❌ *MEV Monitor OFF*")

    def cmd_mev_bots(self, chat_id: str):
        if not self.require_sub(chat_id): return
        lines = ["🤖 *Known MEV Bots*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for addr, label in KNOWN_MEV_BOTS.items():
            lines.append(f"• `{addr[:10]}...` — {label}")
        self.send(chat_id, "\n".join(lines))

    # ─────────────────────────────────────────
    # DEFI YIELD COMMANDS
    # ─────────────────────────────────────────
    def cmd_yield(self, chat_id: str, args: list = None):
        if not self.require_sub(chat_id): return
        self.send(chat_id, "🔄 Fetching best yields...\n⏳ Mohon tunggu ~10 detik...")
        try:
            yields = self.yield_aggregator.get_best_yields(10)
            if not yields:
                self.send(chat_id, "❌ Tidak ada data yield tersedia.")
                return
            msg = "💰 *BEST YIELD OPPORTUNITIES*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, y in enumerate(yields, 1):
                msg += self.yield_aggregator.format_yield(y, i) + "\n\n"
            msg += f"🟢 LOW risk  🟡 MEDIUM risk\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_stable(self, chat_id: str):
        if not self.require_sub(chat_id): return
        self.send(chat_id, "🔄 Fetching stablecoin yields...")
        try:
            yields = self.yield_aggregator.get_stable_yields()
            if not yields:
                self.send(chat_id, "❌ Tidak ada data stablecoin yield.")
                return
            msg = "💵 *STABLECOIN YIELDS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, y in enumerate(yields[:8], 1):
                msg += self.yield_aggregator.format_yield(y, i) + "\n\n"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_protocol(self, chat_id: str, protocol: str):
        if not self.require_sub(chat_id): return
        self.send(chat_id, f"🔄 Fetching {protocol} yields...")
        try:
            yields = self.yield_aggregator.get_by_protocol(protocol)
            if not yields:
                self.send(chat_id, f"❌ Tidak ada data untuk {protocol}.")
                return
            msg = f"🏦 *{protocol.upper()} YIELDS*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, y in enumerate(yields[:8], 1):
                msg += self.yield_aggregator.format_yield(y, i) + "\n\n"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_summary(self, chat_id: str):
        if not self.require_sub(chat_id): return
        self.send(chat_id, "🔄 Generating yield summary...")
        try:
            s = self.yield_aggregator.get_summary()
            if not s:
                self.send(chat_id, "❌ Tidak ada data summary.")
                return
            protocols = ", ".join(s["protocols"])
            self.send(chat_id, f"📊 *DEFI YIELD OVERVIEW*\n━━━━━━━━━━━━━━━━━━━━━━\n🏦 Protocols  : `{protocols}`\n📈 Highest APY: `{s['highest_apy']}%`\n📉 Lowest APY : `{s['lowest_apy']}%`\n📊 Average APY: `{s['avg_apy']}%`\n🔢 Total Opps : `{s['total']}`\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_yield_alert(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            status = "ON ✅" if self.yield_alert_on else "OFF ❌"
            self.send(chat_id, f"🔔 APY Alert: *{status}*\nGunakan `/yield_alert on` atau `/yield_alert off`")
            return
        if args[0].lower() == "on":
            self.yield_alert_on = True
            self.send(chat_id, "✅ *APY Alert ON*\nKamu akan dapat notif kalau ada APY spike > 20%!")
        elif args[0].lower() == "off":
            self.yield_alert_on = False
            self.send(chat_id, "❌ *APY Alert OFF*")

    # ─────────────────────────────────────────
    # TOKEN SNIFFER COMMANDS
    # ─────────────────────────────────────────
    def cmd_sniff(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.token_analyzer:
            self.send(chat_id, "❌ Token Sniffer tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/sniff 0x...`")
            return
        address = args[0].strip()
        if not address.startswith("0x") or len(address) != 42:
            self.send(chat_id, "❌ Invalid address format.")
            return
        self.send(chat_id, f"🔍 Analyzing token...\n`{address}`\n⏳ Mohon tunggu ~15 detik...")
        try:
            result  = self.token_analyzer.analyze(address)
            color   = result.get("safety_color", "⚪")
            label   = result.get("safety_label", "UNKNOWN")
            score   = result.get("score", 0)
            name    = result.get("name", "Unknown")
            symbol  = result.get("symbol", "???")
            addr    = result.get("address", "")
            checks  = result.get("checks", {}).get("goplus", {})
            msg = f"{color} *TOKEN SAFETY REPORT*\n━━━━━━━━━━━━━━━━━━━━━━\n🏷️ *{name}* (${symbol})\n📍 `{addr[:10]}...{addr[-6:]}`\n⭐ Safety Score: *{score}/100* — {label}\n\n📊 *Key Metrics:*\n- Honeypot    : `{'YES 🚨' if checks.get('is_honeypot') else 'NO ✅'}`\n- Buy Tax     : `{checks.get('buy_tax', 0):.1f}%`\n- Sell Tax    : `{checks.get('sell_tax', 0):.1f}%`\n- Owner Hold  : `{checks.get('owner_percent', 0):.1f}%`\n- Holders     : `{checks.get('holder_count', 0):,}`\n- LP Locked   : `{'YES ✅' if checks.get('lp_locked') else 'NO ⚠️'}`\n- Verified    : `{'YES ✅' if result.get('checks', {}).get('verified') else 'NO ⚠️'}`"
            issues   = result.get("issues", [])
            warnings = result.get("warnings", [])
            if issues:
                msg += "\n\n🚨 *Issues:*\n" + "\n".join(issues)
            if warnings:
                msg += "\n\n⚠️ *Warnings:*\n" + "\n".join(warnings)
            msg += f"\n\n⏰ {result.get('timestamp', '')[:19]}"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_quick(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.token_analyzer:
            self.send(chat_id, "❌ Token Sniffer tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/quick 0x...`")
            return
        address = args[0].strip()
        self.send(chat_id, f"⚡ Quick checking `{address[:10]}...`")
        try:
            result = self.token_analyzer.quick_check(address)
            if result.get("error"):
                self.send(chat_id, f"❌ Error: `{result['error']}`")
                return
            safe_emoji = "✅" if result["safe"] else "🚨"
            hp_text    = "YES 🚨" if result["is_honeypot"] else "NO ✅"
            self.send(chat_id, f"⚡ *QUICK CHECK*\n━━━━━━━━━━━━━━━━━━━━━━\n🏷️ *{result['name']}* (${result['symbol']})\n{safe_emoji} Status: `{'SAFE' if result['safe'] else 'RISKY/DANGEROUS'}`\n\n- Honeypot : `{hp_text}`\n- Buy Tax  : `{result['buy_tax']:.1f}%`\n- Sell Tax : `{result['sell_tax']:.1f}%`\n- Holders  : `{result['holders']:,}`\n\nUse /sniff for full analysis!")
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    # ─────────────────────────────────────────
    # WHALE TRACKER COMMANDS
    # ─────────────────────────────────────────
    def _format_whale_move(self, move: dict) -> str:
        type_emoji = {"BUY": "🟢", "SELL": "🔴", "SWAP": "🔄", "TRANSFER": "📤", "CONTRACT_CALL": "📋", "DEPLOY": "🚀"}.get(move["type"], "⚪")
        tx_short   = move["tx_hash"][:10] + "..." if move.get("tx_hash") else "N/A"
        msg = f"🐋 *WHALE ALERT*\n━━━━━━━━━━━━━━━━━━━━━━\n👤 *{move['label']}*\n📍 `{move['wallet'][:10]}...{move['wallet'][-4:]}`\n\n{type_emoji} Type     : *{move['type']}*\n🏊 DEX      : `{move['dex']}`\n💰 Value    : `${move['value_usd']:,.2f}` (`{move['value_eth']} ETH`)\n⛽ Gas Price: `{move['gas_price']} Gwei`\n🔗 TX       : `{tx_short}`"
        if move.get("token_received"):
            t = move["token_received"]
            msg += f"\n\n📥 *Received:* `{t['amount']:,} {t['symbol']}`"
        if move.get("token_sent"):
            t = move["token_sent"]
            msg += f"\n📤 *Sent:* `{t['amount']:,} {t['symbol']}`"
        msg += f"\n\n⏰ `{move['timestamp'][:19]}`\n🔍 [View on Etherscan](https://etherscan.io/tx/{move.get('tx_hash','')})"
        return msg

    def cmd_whale_add(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.whale_tracker:
            self.send(chat_id, "❌ Whale Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/whale_add 0x... <optional_label>`")
            return
        address = args[0].strip()
        if not address.startswith("0x") or len(address) != 42:
            self.send(chat_id, "❌ Invalid address format.")
            return
        if len(self.whale_tracker.get_wallets()) >= MAX_WHALE_WALLETS:
            self.send(chat_id, f"❌ Max {MAX_WHALE_WALLETS} wallets reached.")
            return
        label = " ".join(args[1:]) if len(args) > 1 else ""
        self.send(chat_id, f"🔍 Adding wallet...\n`{address}`\n⏳ Fetching balance...")
        try:
            info = self.whale_tracker.add_wallet(address, label)
            self.send(chat_id, f"✅ *Wallet Added!*\n━━━━━━━━━━━━━━━━━━━━━━\n👤 Label   : *{info['label']}*\n📍 Address : `{address[:10]}...{address[-4:]}`\n💰 Balance : `{info['eth_balance']:.4f} ETH` (~`${info['usd_value']:,.2f}`)\n\nYou'll get alerts on every significant move!")
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_whale_remove(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.whale_tracker:
            self.send(chat_id, "❌ Whale Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/whale_remove 0x...`")
            return
        address = args[0].strip().lower()
        if address in self.whale_tracker.wallet_info:
            label = self.whale_tracker.wallet_info[address]["label"]
            self.whale_tracker.remove_wallet(address)
            self.send(chat_id, f"✅ Removed *{label}* from tracking.")
        else:
            self.send(chat_id, "❌ Wallet not found in tracking list.")

    def cmd_whale_list(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.whale_tracker:
            self.send(chat_id, "❌ Whale Tracker tidak tersedia.")
            return
        wallets = self.whale_tracker.get_wallets()
        if not wallets:
            self.send(chat_id, "📭 No wallets tracked.\nUse `/whale_add 0x...` to start tracking.")
            return
        lines = [f"👀 *Tracked Whales ({len(wallets)}/{MAX_WHALE_WALLETS})*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for i, w in enumerate(wallets, 1):
            addr = w["address"]
            lines.append(f"{i}. *{w['label']}*\n   `{addr[:10]}...{addr[-4:]}`\n   💰 `{w['eth_balance']:.4f} ETH` (~`${w['usd_value']:,.2f}`)")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_whale_check(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.whale_tracker:
            self.send(chat_id, "❌ Whale Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/whale_check 0x...`")
            return
        address    = args[0].strip().lower()
        temp_added = False
        if address not in self.whale_tracker.wallet_info:
            self.whale_tracker.add_wallet(address)
            temp_added = True
        self.send(chat_id, f"🔍 Checking `{address[:10]}...` for recent moves...\n⏳ Please wait...")
        try:
            current_block = self.whale_tracker.etherscan.get_latest_block()
            self.whale_tracker.last_block[address] = max(0, current_block - 1000)
            moves = self.whale_tracker.check_wallet(address)
            if not moves:
                self.send(chat_id, "📭 No significant moves found in last ~1000 blocks.")
            else:
                self.send(chat_id, f"📊 Found *{len(moves)}* recent move(s):")
                for move in moves[:5]:
                    self.send(chat_id, self._format_whale_move(move))
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")
        if temp_added:
            self.whale_tracker.remove_wallet(address)

    def cmd_whale_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.whale_tracker:
            self.send(chat_id, "❌ Whale Tracker tidak tersedia.")
            return
        if not args:
            status = "ON ✅" if self.whale_monitoring else "OFF ❌"
            self.send(chat_id, f"📡 Whale Monitor: *{status}*\nGunakan `/whale_monitor on` atau `/whale_monitor off`")
            return
        if args[0].lower() == "on":
            if not self.whale_tracker.get_wallets():
                self.send(chat_id, "⚠️ No wallets tracked. Add one first with `/whale_add 0x...`")
                return
            self.whale_monitoring = True
            self.send(chat_id, f"✅ *Whale Monitor ON*\nScanning every {WHALE_POLL_INTERVAL}s.")
        elif args[0].lower() == "off":
            self.whale_monitoring = False
            self.send(chat_id, "❌ *Whale Monitor OFF*")

    def cmd_whale_whales(self, chat_id: str):
        if not self.require_sub(chat_id): return
        lines = ["🐋 *Known Whale Addresses*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for addr, label in KNOWN_WHALES.items():
            lines.append(f"• *{label}*\n  `{addr[:10]}...{addr[-4:]}`")
        lines.append("\nUse `/whale_add <address>` to track!")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_whale_alert(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            status = "ON ✅" if self.whale_monitoring else "OFF ❌"
            self.send(chat_id, f"🔔 Whale Alert: *{status}*\nGunakan `/whale_alert on` atau `/whale_alert off`")
            return
        if args[0].lower() == "on":
            if not self.whale_tracker or not self.whale_tracker.get_wallets():
                self.send(chat_id, "⚠️ Add wallets first with `/whale_add 0x...`")
                return
            self.whale_monitoring = True
            self.send(chat_id, "✅ *Whale Alert ON*")
        elif args[0].lower() == "off":
            self.whale_monitoring = False
            self.send(chat_id, "❌ *Whale Alert OFF*")

    # ─────────────────────────────────────────
    # NFT FLOOR TRACKER COMMANDS
    # ─────────────────────────────────────────
    def _format_nft_collection(self, data: dict, show_history: bool = False) -> str:
        slug      = data.get("slug", "")
        floor_eth = data.get("floor_eth", 0)
        floor_usd = data.get("floor_usd", 0)
        vol_24h   = data.get("volume_24h_eth", 0)
        vol_7d    = data.get("volume_7d_eth", 0)
        sales_24h = data.get("sales_24h", 0)
        supply    = data.get("supply", 0)
        owners    = data.get("owners", 0)
        mktcap    = data.get("market_cap_eth", 0)
        avg_price = data.get("avg_price_eth", 0)
        unique_pct = round((owners / supply * 100), 1) if supply > 0 else 0
        msg = f"🖼️ *{data.get('name', 'Unknown')}*\n━━━━━━━━━━━━━━━━━━━━━━\n💎 Floor      : `{floor_eth:.4f} ETH` (~`${floor_usd:,.2f}`)\n📊 Vol 24h    : `{vol_24h:.2f} ETH`\n📅 Vol 7d     : `{vol_7d:.2f} ETH`\n🛒 Sales 24h  : `{sales_24h}`\n💰 Avg Price  : `{avg_price:.4f} ETH`\n🏦 Market Cap : `{mktcap:.1f} ETH`\n👥 Owners     : `{owners:,}` / `{supply:,}` ({unique_pct}% unique)"
        if show_history and self.nft_tracker:
            change = self.nft_tracker.get_price_change(slug)
            msg += f"\n\n{change['direction']} Session Change: `{change['change_pct']:+.2f}%`"
        msg += f"\n\n⏰ `{data.get('timestamp', '')[:19]}`"
        return msg

    def _format_nft_alert(self, alert: dict) -> str:
        if alert["type"] == "FLOOR_DROP":
            sev, emoji, title = ("🔴" if alert["severity"] == "HIGH" else "🟡"), "📉", "FLOOR DROP"
        elif alert["type"] == "FLOOR_PUMP":
            sev, emoji, title = "🟢", "📈", "FLOOR PUMP"
        else:
            sev, emoji, title = "🟡", "📊", "VOLUME SPIKE"
        msg = f"{sev} *NFT {title} ALERT* {emoji}\n━━━━━━━━━━━━━━━━━━━━━━\n🖼️ *{alert.get('collection', 'Unknown')}*"
        if alert["type"] in ("FLOOR_DROP", "FLOOR_PUMP"):
            msg += f"\n\n💎 Old Floor : `{alert['old_floor']:.4f} ETH`\n💎 New Floor : `{alert['new_floor']:.4f} ETH`\n📊 Change    : `{alert['change_pct']:+.2f}%`"
        else:
            msg += f"\n\n📊 Old Vol : `{alert['old_vol']:.2f} ETH`\n📊 New Vol : `{alert['new_vol']:.2f} ETH`\n📈 Change  : `{alert['change_pct']:+.2f}%`"
        msg += f"\n\n⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
        return msg

    def cmd_nft_floor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/nft_floor <slug>`")
            return
        slug = args[0].strip().lower()
        self.send(chat_id, f"🔍 Fetching floor price for `{slug}`...\n⏳ Please wait...")
        try:
            data = self.nft_tracker.opensea.get_collection(slug)
            if not data:
                self.send(chat_id, f"❌ Collection `{slug}` not found.\nUse `/nft_known` for valid slugs.")
                return
            self.send(chat_id, self._format_nft_collection(data))
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_nft_add(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/nft_add <slug>`")
            return
        slug = args[0].strip().lower()
        self.send(chat_id, f"🔍 Adding `{slug}`...\n⏳ Please wait...")
        try:
            data = self.nft_tracker.add_collection(slug)
            if data.get("error"):
                self.send(chat_id, f"❌ {data['error']}\nUse `/nft_known` for valid slugs.")
                return
            self.send(chat_id, f"✅ *Added to watchlist!*\n\n" + self._format_nft_collection(data))
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_nft_remove(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/nft_remove <slug>`")
            return
        slug = args[0].strip().lower()
        if slug in self.nft_tracker.watchlist:
            name = self.nft_tracker.watchlist[slug]["name"]
            self.nft_tracker.remove_collection(slug)
            self.send(chat_id, f"✅ *{name}* removed from watchlist.")
        else:
            self.send(chat_id, f"❌ `{slug}` not in watchlist.")

    def cmd_nft_list(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        collections = self.nft_tracker.get_collections()
        if not collections:
            self.send(chat_id, "📭 Watchlist empty.\nUse `/nft_add <slug>` to track collections.")
            return
        lines = [f"👀 *Tracked NFT Collections ({len(collections)})*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for i, c in enumerate(collections, 1):
            change = self.nft_tracker.get_price_change(c["slug"])
            lines.append(f"{i}. *{c['name']}*\n   💎 `{c['floor_eth']:.4f} ETH` {change['direction']} `{change['change_pct']:+.2f}%`")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_nft_sales(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/nft_sales <slug>`")
            return
        slug = args[0].strip().lower()
        self.send(chat_id, f"🔍 Fetching recent sales for `{slug}`...")
        try:
            sales = self.nft_tracker.opensea.get_recent_sales(slug, limit=5)
            if not sales:
                self.send(chat_id, "📭 No recent sales found.")
                return
            msg = f"🛒 *Recent Sales — {slug}*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            for s in sales:
                msg += f"\n• *{s['name']}* — `{s['price_eth']:.4f} ETH` (~`${s['price_usd']:,.2f}`)\n  ⏰ {s['timestamp'][:19] if s['timestamp'] else 'N/A'}\n"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_nft_top(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        self.send(chat_id, "🔍 Fetching top collections...\n⏳ Please wait...")
        try:
            collections = self.nft_tracker.opensea.get_top_collections(10)
            if not collections:
                self.send(chat_id, "❌ No data available.")
                return
            msg = "🏆 *TOP NFT COLLECTIONS — 24h Volume*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            for i, c in enumerate(collections, 1):
                msg += f"{i}. *{c['name']}*\n   💎 Floor: `{c['floor_eth']:.4f} ETH`\n   📊 Vol 24h: `{c['volume_24h_eth']:.2f} ETH` | Sales: `{c['sales_24h']}`\n\n"
            msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_nft_search(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/nft_search <name>`")
            return
        query = " ".join(args).strip().lower().replace(" ", "-")
        self.send(chat_id, f"🔍 Searching `{query}`...")
        slug_variants = [query, query.replace("-", ""), query + "official", query + "-official"]
        found = False
        for slug in slug_variants:
            data = self.nft_tracker.opensea.get_collection(slug)
            if data and data.get("name"):
                self.send(chat_id, f"🔍 *Found!*\n━━━━━━━━━━━━━━━━━━━━━━\n• *{data['name']}*\n  Slug: `{slug}`\n  💎 Floor: `{data['floor_eth']:.4f} ETH`\n  Use: `/nft_add {slug}`")
                found = True
                break
        if not found:
            self.send(chat_id, f"❌ Not found: `{query}`\n\nTry `/nft_known` for valid slugs!")

    def cmd_nft_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.nft_tracker:
            self.send(chat_id, "❌ NFT Tracker tidak tersedia.")
            return
        if not args:
            status = "ON ✅" if self.nft_monitoring else "OFF ❌"
            self.send(chat_id, f"📡 NFT Monitor: *{status}*\nGunakan `/nft_monitor on` atau `/nft_monitor off`")
            return
        if args[0].lower() == "on":
            if not self.nft_tracker.get_collections():
                self.send(chat_id, "⚠️ No collections tracked. Add one first with `/nft_add <slug>`")
                return
            self.nft_monitoring = True
            self.send(chat_id, f"✅ *NFT Monitor ON* — Checking every {NFT_POLL_INTERVAL//60} mins.")
        elif args[0].lower() == "off":
            self.nft_monitoring = False
            self.send(chat_id, "❌ *NFT Monitor OFF*")

    def cmd_nft_known(self, chat_id: str):
        if not self.require_sub(chat_id): return
        lines = ["📋 *Known NFT Collections*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for slug, name in KNOWN_NFT_COLLECTIONS.items():
            lines.append(f"• *{name}*\n  `/nft_add {slug}`")
        self.send(chat_id, "\n\n".join(lines))

    # ─────────────────────────────────────────
    # GAS PRICE PREDICTOR COMMANDS
    # ─────────────────────────────────────────
    def _format_gas_report(self, gas_data: dict, eth_price: float) -> str:
        propose = gas_data.get("propose_gas", 0)
        safe    = gas_data.get("safe_gas", 0)
        fast    = gas_data.get("fast_gas", 0)
        base    = gas_data.get("base_fee", 0)
        source  = gas_data.get("source", "Unknown")
        if propose <= self.gas_low_thresh:
            timing = "🟢 GREAT TIME TO TRANSACT!"
            advice = "Gas is very low. Send now!"
        elif propose <= 30:
            timing = "🟢 Good time to transact"
            advice = "Gas is reasonable."
        elif propose <= 60:
            timing = "🟡 Moderate — consider waiting"
            advice = "Wait if not urgent."
        elif propose <= self.gas_high_thresh:
            timing = "🟠 High gas — wait if possible"
            advice = "Only urgent transactions."
        else:
            timing = "🔴 VERY HIGH GAS — avoid!"
            advice = "Wait for gas to drop."
        msg = f"⛽ *GAS PRICE REPORT*\n━━━━━━━━━━━━━━━━━━━━━━\n🟢 Safe    : `{safe:.1f} Gwei` (~2 min)\n🟡 Standard: `{propose:.1f} Gwei` (~30 sec)\n🔴 Fast    : `{fast:.1f} Gwei` (~15 sec)\n🏗️ Base Fee: `{base:.1f} Gwei`\n\n{timing}\n💡 {advice}"
        msg += "\n\n💸 *TX Cost Estimates:*"
        for tx_type, gas_units in TX_GAS_UNITS.items():
            cost_eth = (propose * gas_units) / 1e9
            cost_usd = cost_eth * eth_price
            msg += f"\n• {tx_type}: `${cost_usd:.4f}` (`{cost_eth:.6f} ETH`)"
        msg += f"\n\n📡 Source: `{source}`\n⏰ `{gas_data.get('timestamp', '')[:19]}`"
        return msg

    def cmd_gas(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.gas_predictor:
            self.send(chat_id, "❌ Gas Predictor tidak tersedia.")
            return
        self.send(chat_id, "⛽ Fetching gas prices...\n⏳ Please wait...")
        try:
            gas_data = self.gas_predictor.fetch()
            if not gas_data:
                self.send(chat_id, "❌ Could not fetch gas data.")
                return
            eth_price = self.gas_predictor.oracle.get_eth_price()
            self.send(chat_id, self._format_gas_report(gas_data, eth_price))
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_gas_fast(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.gas_predictor:
            self.send(chat_id, "❌ Gas Predictor tidak tersedia.")
            return
        try:
            gas_data = self.gas_predictor.fetch()
            if not gas_data:
                self.send(chat_id, "❌ Could not fetch gas data.")
                return
            self.send(chat_id, f"⛽ *Quick Gas Check*\n━━━━━━━━━━━━━━━━━━━━━━\n🟢 Safe    : `{gas_data.get('safe_gas', 0):.1f} Gwei`\n🟡 Standard: `{gas_data.get('propose_gas', 0):.1f} Gwei`\n🔴 Fast    : `{gas_data.get('fast_gas', 0):.1f} Gwei`\n\n⏰ `{datetime.now().strftime('%H:%M:%S')}`")
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_gas_estimate(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gas_predictor:
            self.send(chat_id, "❌ Gas Predictor tidak tersedia.")
            return
        try:
            gas_data  = self.gas_predictor.fetch()
            eth_price = self.gas_predictor.oracle.get_eth_price()
            gwei      = float(args[0]) if args and args[0].replace(".", "").isdigit() else gas_data.get("propose_gas", 30)
            msg       = f"💸 *TX Cost Estimates @ {gwei} Gwei*\n━━━━━━━━━━━━━━━━━━━━━━\n💰 ETH Price: `${eth_price:,.2f}`\n\n"
            for tx_type, gas_units in TX_GAS_UNITS.items():
                cost_eth = (gwei * gas_units) / 1e9
                cost_usd = cost_eth * eth_price
                msg += f"• *{tx_type}*\n  `{gas_units:,}` gas → `${cost_usd:.4f}` (`{cost_eth:.6f} ETH`)\n\n"
            msg += f"⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_gas_trend(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.gas_predictor:
            self.send(chat_id, "❌ Gas Predictor tidak tersedia.")
            return
        if len(self.gas_predictor.history) < 3:
            self.send(chat_id, "🔄 Collecting data...\n⏳ Please wait ~10 seconds...")
            for _ in range(3):
                self.gas_predictor.fetch()
                time.sleep(3)
        trend = self.gas_predictor.get_trend()
        stats = self.gas_predictor.get_history_stats()
        if not stats:
            self.send(chat_id, "❌ Not enough data yet.")
            return
        self.send(chat_id, f"📈 *GAS TREND ANALYSIS*\n━━━━━━━━━━━━━━━━━━━━━━\n{trend['direction']} Trend      : *{trend['trend']}*\n📊 Change     : `{trend['change_pct']:+.2f}%`\n🕐 Recent Avg : `{trend['avg_recent']} Gwei`\n🕐 Older Avg  : `{trend['avg_older']} Gwei`\n\n📉 *Session Stats ({stats['period_min']} readings)*\n• Min : `{stats['min_gwei']} Gwei`\n• Max : `{stats['max_gwei']} Gwei`\n• Avg : `{stats['avg_gwei']} Gwei`\n• Now : `{stats['current']} Gwei`\n\n⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

    def cmd_gas_history(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.gas_predictor:
            self.send(chat_id, "❌ Gas Predictor tidak tersedia.")
            return
        stats = self.gas_predictor.get_history_stats()
        if not stats:
            self.send(chat_id, "📭 No history yet. Use /gas first.")
            return
        recent = list(self.gas_predictor.history)[-5:]
        msg    = f"📊 *Gas Price History*\n━━━━━━━━━━━━━━━━━━━━━━\n📈 Min : `{stats['min_gwei']} Gwei`\n📉 Max : `{stats['max_gwei']} Gwei`\n📊 Avg : `{stats['avg_gwei']} Gwei`\n🔢 Readings: `{stats['readings']}`\n\n*Last 5 Readings:*\n"
        for r in reversed(recent):
            msg += f"• `{r.get('propose_gas', 0):.1f} Gwei` — `{r.get('timestamp', '')[:19]}`\n"
        self.send(chat_id, msg)

    def cmd_gas_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gas_predictor:
            self.send(chat_id, "❌ Gas Predictor tidak tersedia.")
            return
        if not args:
            status = "ON ✅" if self.gas_monitoring else "OFF ❌"
            self.send(chat_id, f"📡 Gas Monitor: *{status}*\nGunakan `/gas_monitor on` atau `/gas_monitor off`\n\n🔔 Alert thresholds:\n• Low  < `{self.gas_low_thresh} Gwei`\n• High > `{self.gas_high_thresh} Gwei`")
            return
        if args[0].lower() == "on":
            self.gas_monitoring = True
            self.send(chat_id, f"✅ *Gas Monitor ON*\nChecking every {GAS_POLL_INTERVAL}s.")
        elif args[0].lower() == "off":
            self.gas_monitoring = False
            self.send(chat_id, "❌ *Gas Monitor OFF*")

    def cmd_gas_threshold(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, f"🔔 *Gas Alert Thresholds*\n━━━━━━━━━━━━━━━━━━━━━━\n🟢 Low  : `{self.gas_low_thresh} Gwei`\n🔴 High : `{self.gas_high_thresh} Gwei`\n\nSet: `/gas_threshold low <gwei>` or `/gas_threshold high <gwei>`")
            return
        if len(args) >= 2 and args[1].isdigit():
            val = int(args[1])
            if args[0].lower() == "low":
                self.gas_low_thresh = val
                self.send(chat_id, f"✅ Low gas threshold set to `{val} Gwei`")
            elif args[0].lower() == "high":
                self.gas_high_thresh = val
                self.send(chat_id, f"✅ High gas threshold set to `{val} Gwei`")
        else:
            self.send(chat_id, "⚠️ Usage: `/gas_threshold low 15` or `/gas_threshold high 100`")

    # ─────────────────────────────────────────
    # ARBITRAGE SCANNER COMMANDS
    # ─────────────────────────────────────────
    def _format_arb_opportunity(self, opp: dict, rank: int = 0) -> str:
        rank_str = f"#{rank} " if rank else ""
        return f"{rank_str}💱 *ARB OPPORTUNITY — {opp['symbol']}*\n━━━━━━━━━━━━━━━━━━━━━━\n🔴 Severity   : {opp['severity']}\n📊 Spread     : `{opp['spread_pct']:.4f}%`\n\n📥 Buy  @ *{opp['buy_dex']}*\n   Price: `${opp['buy_price']:.6f}`\n\n📤 Sell @ *{opp['sell_dex']}*\n   Price: `${opp['sell_price']:.6f}`\n\n💰 *Profit Estimate (${opp['trade_amount']:,} trade):*\n• Gross : `${opp['gross_profit']:,.2f}`\n• Gas   : `${opp['gas_cost']:.2f}`\n• Net   : `${opp['net_profit']:,.2f}` (`{opp['profit_pct']:.4f}%`)\n\n⏰ `{opp['timestamp'][:19]}`"

    def cmd_arb_scan(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.arb_engine:
            self.send(chat_id, "❌ Arbitrage Scanner tidak tersedia.")
            return
        self.send(chat_id, f"🔄 Scanning {len(ARB_TRACKED_TOKENS)} tokens across 6 DEXes...\n⏳ Please wait ~30 seconds...")
        try:
            opportunities = self.arb_engine.scan_all()
            if not opportunities:
                self.send(chat_id, "📭 No arbitrage opportunities found.\nSpread too low or gas cost exceeds profit.\nTry again in a few minutes!")
                return
            stats = self.arb_engine.get_stats()
            self.send(chat_id, f"🔄 *ARBITRAGE SCAN COMPLETE*\n━━━━━━━━━━━━━━━━━━━━━━\n🔢 Tokens scanned : `{len(ARB_TRACKED_TOKENS)}`\n✅ Opportunities  : `{len(opportunities)}`\n🔴 High severity  : `{stats.get('high_severity', 0)}`\n💰 Best profit    : `${stats.get('best_profit', 0):,.2f}`\n\n*Top 3 opportunities:*")
            for i, opp in enumerate(opportunities[:3], 1):
                self.send(chat_id, self._format_arb_opportunity(opp, i))
                time.sleep(0.5)
            if len(opportunities) > 3:
                self.send(chat_id, f"📊 +{len(opportunities)-3} more. Use /arb_top to see all top 5.")
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_arb_token(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.arb_engine:
            self.send(chat_id, "❌ Arbitrage Scanner tidak tersedia.")
            return
        if not args:
            tokens = ", ".join(f"`{s}`" for s in ARB_TRACKED_TOKENS.keys())
            self.send(chat_id, f"⚠️ Usage: `/arb_token <symbol>`\n\nAvailable: {tokens}")
            return
        symbol = args[0].upper()
        if symbol not in ARB_TRACKED_TOKENS:
            tokens = ", ".join(f"`{s}`" for s in ARB_TRACKED_TOKENS.keys())
            self.send(chat_id, f"❌ `{symbol}` not tracked.\n\nAvailable: {tokens}")
            return
        self.send(chat_id, f"🔄 Scanning *{symbol}* across 6 DEXes...\n⏳ Please wait...")
        try:
            opps = self.arb_engine.scan_specific_token(symbol)
            if not opps:
                self.send(chat_id, f"📭 No opportunities for *{symbol}*\nSpread below threshold or net profit < ${ARB_MIN_PROFIT}.\nTry again in a few minutes!")
                return
            self.send(chat_id, f"✅ Found *{len(opps)}* opportunity(ies) for *{symbol}*:")
            for i, opp in enumerate(opps[:3], 1):
                self.send(chat_id, self._format_arb_opportunity(opp, i))
                time.sleep(0.5)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_arb_top(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.arb_engine:
            self.send(chat_id, "❌ Arbitrage Scanner tidak tersedia.")
            return
        if not self.arb_engine.opportunities:
            self.send(chat_id, "📭 No data yet.\nRun `/arb_scan` first!")
            return
        top = self.arb_engine.get_top_opportunities(5)
        self.send(chat_id, f"🏆 *TOP {len(top)} ARBITRAGE OPPORTUNITIES*\n━━━━━━━━━━━━━━━━━━━━━━")
        for i, opp in enumerate(top, 1):
            self.send(chat_id, self._format_arb_opportunity(opp, i))
            time.sleep(0.5)

    def cmd_arb_pairs(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.arb_engine:
            self.send(chat_id, "❌ Arbitrage Scanner tidak tersedia.")
            return
        lines = [f"📋 *Tracked Token Pairs ({len(ARB_TRACKED_TOKENS)})*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for symbol, contract in ARB_TRACKED_TOKENS.items():
            price = self.arb_engine.fetcher.get_token_price_defillama(contract)
            if price == 0:
                price = self.arb_engine.fetcher.get_token_price_coingecko(contract)
            price_str = f"${price:.4f}" if price > 0 else "N/A"
            lines.append(f"• *{symbol}* — `{price_str}`\n  `{contract[:10]}...{contract[-4:]}`")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_arb_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.arb_engine:
            self.send(chat_id, "❌ Arbitrage Scanner tidak tersedia.")
            return
        if not args:
            status = "ON ✅" if self.arb_monitoring else "OFF ❌"
            self.send(chat_id, f"📡 Arb Monitor: *{status}*\nGunakan `/arb_monitor on` atau `/arb_monitor off`\n\n🔔 Alert when net profit > `${ARB_MIN_PROFIT}`")
            return
        if args[0].lower() == "on":
            self.arb_monitoring = True
            self.send(chat_id, f"✅ *Arb Monitor ON*\nScanning every {ARB_POLL_INTERVAL//60} minutes.\n🔔 Alert threshold: net profit > `${ARB_MIN_PROFIT}`")
        elif args[0].lower() == "off":
            self.arb_monitoring = False
            self.send(chat_id, "❌ *Arb Monitor OFF*")

    def cmd_arb_stats(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.arb_engine:
            self.send(chat_id, "❌ Arbitrage Scanner tidak tersedia.")
            return
        stats = self.arb_engine.get_stats()
        self.send(chat_id, f"📊 *ARBITRAGE SCANNER STATS*\n━━━━━━━━━━━━━━━━━━━━━━\n🔢 Total Scans    : `{stats['scan_count']}`\n✅ Total Found    : `{stats['total_found']}`\n📈 Active Opps   : `{stats['active_opps']}`\n💰 Best Profit   : `${stats.get('best_profit', 0):,.2f}`\n📊 Avg Profit    : `${stats.get('avg_profit', 0):,.2f}`\n🔴 High Severity : `{stats.get('high_severity', 0)}`\n\n⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

    def cmd_arb_settings(self, chat_id: str):
        if not self.require_sub(chat_id): return
        tokens = ", ".join(f"`{s}`" for s in ARB_TRACKED_TOKENS.keys())
        self.send(chat_id, f"⚙️ *Arbitrage Scanner Settings*\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Trade Amount   : `$10,000`\n⛽ Gas Cost Est.  : `$15`\n📊 Min Spread     : `0.3%`\n💵 Min Net Profit : `${ARB_MIN_PROFIT}`\n🔄 Scan Interval  : `{ARB_POLL_INTERVAL//60} minutes`\n🔢 Tokens Tracked : `{len(ARB_TRACKED_TOKENS)}`\n\n*Tokens:* {tokens}")

    # ─────────────────────────────────────────
    # DAO GOVERNANCE TRACKER COMMANDS
    # ─────────────────────────────────────────
    def _format_gov_proposal(self, p: dict) -> str:
        state_emoji = {
            "ACTIVE": "🟢", "EXECUTED": "✅", "PASSED": "✅", "SUCCEEDED": "✅",
            "DEFEATED": "❌", "FAILED": "❌", "CANCELED": "⚫", "PENDING": "⏳",
            "QUEUED": "⏳", "CLOSED": "🔵",
        }.get(p.get("state", ""), "⚪")
        msg = f"{p.get('dao_color','🏛️')} *{p.get('dao_name','DAO')} Governance*\n━━━━━━━━━━━━━━━━━━━━━━\n📋 *{p.get('title','Unknown')}*\n\n{state_emoji} Status  : *{p.get('state','?')}*\n📡 Source  : `{p.get('source','?')}`\n👤 Author  : `{p.get('author','?')}`"
        if p.get("vote_breakdown"):
            msg += "\n\n📊 *Vote Breakdown:*"
            for v in p["vote_breakdown"][:4]:
                bar_len = int(v.get("pct", 0) / 10)
                bar     = "█" * bar_len + "░" * (10 - bar_len)
                msg += f"\n• {v['choice'][:15]:15} `{bar}` `{v['pct']:.1f}%`"
        if p.get("leading") and p["leading"].get("choice"):
            msg += f"\n\n🏆 Leading: *{p['leading']['choice']}* (`{p['leading'].get('pct',0):.1f}%`)"
        if p.get("quorum_pct", 0) > 0:
            msg += f"\n🎯 Quorum : `{p['quorum_pct']:.1f}%`"
        if p.get("state") == "ACTIVE":
            if p.get("days_left", 0) > 0:
                msg += f"\n⏰ Ends in : `{p['days_left']}d {p.get('hours_left', 0) % 24}h`"
            elif p.get("hours_left", 0) > 0:
                msg += f"\n⏰ Ends in : `{p['hours_left']}h` ⚠️ ENDING SOON!"
            else:
                msg += "\n⏰ Voting ended"
        if p.get("vote_count", 0) > 0:
            msg += f"\n🗳️ Votes   : `{p['vote_count']:,}`"
        if p.get("snapshot_url"):
            msg += f"\n\n🔗 [View Proposal]({p['snapshot_url']})"
        return msg

    def _format_gov_new_alert(self, p: dict) -> str:
        return (f"🔔 *NEW GOVERNANCE PROPOSAL*\n━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{p.get('dao_color','🏛️')} *{p.get('dao_name','DAO')}* (${p.get('dao_token','?')})\n\n"
                f"📋 *{p.get('title','Unknown')}*\n\n🟢 Status   : *ACTIVE — Voting Open*\n"
                f"👤 Author   : `{p.get('author','?')}`\n"
                f"⏰ Ends in  : `{p.get('days_left',0)}d {p.get('hours_left',0) % 24}h`\n\n"
                f"🔗 [Vote Now]({p.get('snapshot_url','')})")

    def _format_gov_deadline_alert(self, p: dict) -> str:
        return (f"⚠️ *VOTING DEADLINE ALERT*\n━━━━━━━━━━━━━━━━━━━━━━\n"
                f"{p.get('dao_color','🏛️')} *{p.get('dao_name','DAO')}* (${p.get('dao_token','?')})\n\n"
                f"📋 *{p.get('title','Unknown')}*\n\n⏰ Ending in: `{p.get('hours_left',0)}h`\n"
                f"🏆 Currently: *{p.get('leading',{}).get('choice','N/A')}* winning "
                f"(`{p.get('leading',{}).get('pct',0):.1f}%`)\n\n"
                f"🔗 [Vote Now]({p.get('snapshot_url','')})")

    def cmd_gov_proposals(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/gov_proposals <dao>`\n\nAvailable: `uniswap`, `aave`, `compound`, `maker`, `gitcoin`")
            return
        dao_key = args[0].lower()
        if dao_key not in DAOS:
            self.send(chat_id, f"❌ `{dao_key}` not found.\nAvailable: `uniswap`, `aave`, `compound`, `maker`, `gitcoin`")
            return
        dao = DAOS[dao_key]
        self.send(chat_id, f"{dao['color']} Fetching *{dao['name']}* proposals...\n⏳ Please wait...")
        try:
            proposals = self.gov_analyzer.fetch_proposals(dao_key)
            if not proposals:
                self.send(chat_id, f"📭 No proposals found for *{dao['name']}*.")
                return
            active = [p for p in proposals if p["state"] == "ACTIVE"]
            recent = [p for p in proposals if p["state"] != "ACTIVE"][:3]
            self.send(chat_id, f"{dao['color']} *{dao['name']} Proposals*\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Active  : `{len(active)}`\n🔵 Recent  : `{len(recent)}`")
            for p in active[:3]:
                self.send(chat_id, self._format_gov_proposal(p))
                time.sleep(0.5)
            if recent and not active:
                self.send(chat_id, "📋 *Recent Closed Proposals:*")
                for p in recent[:2]:
                    self.send(chat_id, self._format_gov_proposal(p))
                    time.sleep(0.5)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_gov_proposal(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/gov_proposal <proposal_id>`")
            return
        proposal_id = args[0].strip()
        self.send(chat_id, f"🔍 Fetching proposal `{proposal_id[:20]}...`\n⏳ Please wait...")
        try:
            p_raw = self.gov_analyzer.snapshot.get_proposal_detail(proposal_id)
            if not p_raw:
                self.send(chat_id, "❌ Proposal not found.")
                return
            space_id = p_raw.get("space", {}).get("id", "")
            dao      = next((d for d in DAOS.values() if d["snapshot_id"] == space_id), list(DAOS.values())[0])
            p        = self.gov_analyzer.format_proposal_snapshot(p_raw, dao)
            self.send(chat_id, self._format_gov_proposal(p))
            votes = self.gov_analyzer.snapshot.get_votes(proposal_id, limit=5)
            if votes:
                voter_msg = "👥 *Top Voters:*\n━━━━━━━━━━━━━━━━━━━━━━"
                for v in votes[:5]:
                    choice_idx = int(v.get("choice", 1)) - 1
                    choice     = p_raw.get("choices", [])[choice_idx] if choice_idx < len(p_raw.get("choices", [])) else "Unknown"
                    vp         = float(v.get("vp", 0) or 0)
                    voter      = v.get("voter", "")[:10] + "..."
                    voter_msg += f"\n• `{voter}` → *{choice}* (`{vp:,.0f} VP`)"
                self.send(chat_id, voter_msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_gov_add(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/gov_add <dao>`\n\nAvailable: `uniswap`, `aave`, `compound`, `maker`, `gitcoin`")
            return
        dao_key = args[0].lower()
        if self.gov_analyzer.add_dao(dao_key):
            dao = DAOS[dao_key]
            self.send(chat_id, f"✅ *{dao['color']} {dao['name']}* added to watchlist!\n\nYou'll get alerts on new proposals & voting deadlines.")
        else:
            self.send(chat_id, f"❌ `{dao_key}` not found.\nAvailable: `uniswap`, `aave`, `compound`, `maker`, `gitcoin`")

    def cmd_gov_remove(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/gov_remove <dao>`")
            return
        dao_key = args[0].lower()
        if dao_key in self.gov_analyzer.watchlist:
            self.gov_analyzer.remove_dao(dao_key)
            self.send(chat_id, f"✅ *{DAOS[dao_key]['name']}* removed from watchlist.")
        else:
            self.send(chat_id, f"❌ `{dao_key}` not in watchlist.")

    def cmd_gov_list(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        watched = self.gov_analyzer.get_watched_daos()
        if not watched:
            self.send(chat_id, "📭 No DAOs in watchlist.\nUse `/gov_add <dao>` to start tracking.")
            return
        lines = ["👀 *Watched DAOs*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for key in watched:
            dao       = DAOS[key]
            proposals = self.gov_analyzer.cached_proposals.get(key, [])
            active    = sum(1 for p in proposals if p["state"] == "ACTIVE")
            lines.append(f"{dao['color']} *{dao['name']}* (${dao['token']})\n   Active proposals: `{active}`")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_gov_summary(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/gov_summary <dao>`")
            return
        dao_key = args[0].lower()
        if dao_key not in DAOS:
            self.send(chat_id, f"❌ `{dao_key}` not found.")
            return
        self.send(chat_id, f"🔍 Fetching {DAOS[dao_key]['name']} summary...\n⏳ Please wait...")
        try:
            summary     = self.gov_analyzer.get_dao_summary(dao_key)
            space_info  = self.gov_analyzer.snapshot.get_space_info(DAOS[dao_key]["snapshot_id"])
            members     = int(space_info.get("followers", 0) or 0)
            total_props = int(space_info.get("proposalsCount", 0) or 0)
            total_votes = int(space_info.get("votesCount", 0) or 0)
            msg = (f"{summary['dao_color']} *{summary['dao_name']} Governance Summary*\n"
                   f"━━━━━━━━━━━━━━━━━━━━━━\n"
                   f"💎 Token      : *${summary['dao_token']}*\n"
                   f"👥 Followers  : `{members:,}`\n"
                   f"📋 Total Props: `{total_props:,}`\n"
                   f"🗳️ Total Votes: `{total_votes:,}`\n\n"
                   f"📊 *Recent Activity:*\n"
                   f"🟢 Active   : `{summary['active']}`\n"
                   f"✅ Passed   : `{summary['passed']}`\n"
                   f"❌ Failed   : `{summary['failed']}`")
            self.send(chat_id, msg)
            if summary["active_list"]:
                self.send(chat_id, f"🟢 *Active Proposals ({len(summary['active_list'])}):*")
                for p in summary["active_list"][:2]:
                    self.send(chat_id, self._format_gov_proposal(p))
                    time.sleep(0.5)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_gov_daos(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        lines = ["🏛️ *Available DAOs*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for key, dao in DAOS.items():
            lines.append(f"{dao['color']} *{dao['name']}* (${dao['token']})\n  Command: `/gov_add {key}`")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_gov_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        if not args:
            status = "ON ✅" if self.gov_monitoring else "OFF ❌"
            self.send(chat_id, (f"📡 Gov Monitor: *{status}*\n"
                                f"Use `/gov_monitor on` or `/gov_monitor off`\n\n"
                                f"🔔 Alerts for:\n• New proposals\n"
                                f"• Voting deadlines (< {DEADLINE_ALERT_HOURS}h)\n• Quorum reached"))
            return
        if args[0].lower() == "on":
            if not self.gov_analyzer.watchlist:
                self.send(chat_id, "⚠️ No DAOs watched. Add one first with `/gov_add <dao>`")
                return
            self.gov_monitoring = True
            watched = ", ".join(f"`{k}`" for k in self.gov_analyzer.watchlist)
            self.send(chat_id, f"✅ *Gov Monitor ON*\nWatching: {watched}\nChecking every {GOV_POLL_INTERVAL//60} minutes.")
        elif args[0].lower() == "off":
            self.gov_monitoring = False
            self.send(chat_id, "❌ *Gov Monitor OFF*")

    def cmd_gov_top(self, chat_id: str):
        if not self.require_sub(chat_id): return
        if not self.gov_analyzer:
            self.send(chat_id, "❌ DAO Governance Tracker tidak tersedia.")
            return
        self.send(chat_id, "🔍 Fetching top active proposals across all DAOs...\n⏳ Please wait ~20 seconds...")
        try:
            all_active = []
            for dao_key in DAOS.keys():
                proposals = self.gov_analyzer.fetch_proposals(dao_key)
                active    = [p for p in proposals if p["state"] == "ACTIVE"]
                all_active.extend(active)
                time.sleep(0.3)
            if not all_active:
                self.send(chat_id, "📭 No active proposals found across all DAOs.")
                return
            all_active.sort(key=lambda x: x.get("hours_left", 99999))
            self.send(chat_id, f"🏆 *TOP ACTIVE GOVERNANCE PROPOSALS*\n━━━━━━━━━━━━━━━━━━━━━━\n📊 Found `{len(all_active)}` active proposals")
            for p in all_active[:5]:
                self.send(chat_id, self._format_gov_proposal(p))
                time.sleep(0.5)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    # ─────────────────────────────────────────
    # CROSS-CHAIN BRIDGE COMMANDS
    # ─────────────────────────────────────────
    @staticmethod
    def _fmt_bridge(v: float) -> str:
        if v <= 0:   return "N/A"
        if v >= 1e9: return f"${v/1e9:.2f}B"
        if v >= 1e6: return f"${v/1e6:.1f}M"
        if v >= 1e3: return f"${v/1e3:.1f}K"
        return f"${v:,.2f}"

    def _format_bridge_info(self, info: dict) -> str:
        chains    = info.get("chains", [])
        chain_str = " • ".join(chains[:6]) if chains else "Multi-chain"
        price     = info.get("price_usd", 0)
        price_str = f"${price:.4f}" if 0 < price < 1 else f"${price:.2f}" if 0 < price < 1000 else f"${price:,.0f}" if price >= 1000 else "N/A"
        lifi_line = f"\n🔁 LI.FI       : `Supported ✅`" if info.get("lifi_supported") else ""
        return (f"{info['color']} *{info['name']}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"📝 {info.get('description', '')}\n\n"
                f"💎 *Token: ${info['token']}*\n"
                f"💵 Price       : `{price_str}`\n"
                f"📊 Market Cap  : `{self._fmt_bridge(info.get('mcap_usd', 0))}`\n"
                f"📈 Vol 24h     : `{self._fmt_bridge(info.get('vol_24h_usd', 0))}`\n"
                f"{info['direction']} Change 24h  : `{info.get('change_24h', 0):+.2f}%`\n"
                f"📅 Change 7d   : `{info.get('change_7d', 0):+.2f}%`"
                f"{lifi_line}\n\n"
                f"🔗 *Supported Chains ({len(chains)}):*\n"
                f"`{chain_str}`\n\n"
                f"🌐 {info.get('website', '')}\n"
                f"⏰ `{info.get('timestamp','')[:19]}`")

    def _format_bridge_price_alert(self, alert: dict) -> str:
        emoji = "📉" if alert["type"] == "PRICE_DROP" else "📈"
        title = "TOKEN DROP" if alert["type"] == "PRICE_DROP" else "TOKEN PUMP"
        return (f"{alert['color']} *BRIDGE {title} ALERT* {emoji}\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🌉 Bridge   : *{alert['bridge']}*\n"
                f"🪙 Token    : *${alert['token']}*\n"
                f"📊 Change   : `{alert['change']:+.2f}%`\n"
                f"⚡ Severity : {alert['severity']}\n"
                f"\n⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")

    def cmd_bridge_info(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/bridge_info <bridge>`\n\nAvailable: `stargate` `hop` `across` `celer` `synapse` `wormhole` `axelar` `debridge`")
            return
        key = args[0].lower()
        if key not in BRIDGES:
            self.send(chat_id, f"❌ `{key}` not found.\nUse `/bridge_bridges` to see all.")
            return
        b = BRIDGES[key]
        self.send(chat_id, f"{b['color']} Fetching *{b['name']}* data...\n⏳ Please wait...")
        try:
            info = self.bridge_monitor.get_bridge_info(key)
            if not info:
                self.send(chat_id, f"❌ Could not fetch data for *{b['name']}*.")
                return
            self.send(chat_id, self._format_bridge_info(info))
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_bridge_add(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/bridge_add <bridge>`")
            return
        key = args[0].lower()
        if self.bridge_monitor.add_bridge(key):
            b = BRIDGES[key]
            self.send(chat_id, f"✅ *{b['color']} {b['name']}* added to watchlist!\n🪙 Tracking token: *${b['token']}*\n🔔 Alerts on price changes > {BRIDGE_TVL_DROP_ALERT}%")
        else:
            self.send(chat_id, f"❌ `{key}` not found.\nUse `/bridge_bridges` to see all.")

    def cmd_bridge_remove(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            self.send(chat_id, "⚠️ Usage: `/bridge_remove <bridge>`")
            return
        key = args[0].lower()
        if key in self.bridge_monitor.watchlist:
            self.bridge_monitor.remove_bridge(key)
            self.send(chat_id, f"✅ *{BRIDGES[key]['name']}* removed from watchlist.")
        else:
            self.send(chat_id, f"❌ `{key}` not in watchlist.")

    def cmd_bridge_list(self, chat_id: str):
        if not self.require_sub(chat_id): return
        watched = self.bridge_monitor.get_watched_bridges()
        if not watched:
            self.send(chat_id, "📭 No bridges in watchlist.\nUse `/bridge_add <bridge>` to start.")
            return
        lines = [f"👀 *Watched Bridges ({len(watched)})*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for key in watched:
            b     = BRIDGES[key]
            trend = self.bridge_monitor.get_price_trend(key)
            hist  = self.bridge_monitor.price_history.get(key, [])
            price = hist[-1]["price"] if hist else 0
            pstr  = f"${price:.4f}" if 0 < price < 1 else f"${price:.2f}" if price > 0 else "N/A"
            lines.append(f"{b['color']} *{b['name']}* (${b['token']})\n   Price: `{pstr}` {trend['direction']} `{trend['change_pct']:+.2f}%`")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_bridge_tvl(self, chat_id: str):
        if not self.require_sub(chat_id): return
        self.send(chat_id, "🔍 Fetching all bridges overview...\n⏳ Please wait ~10s...")
        try:
            bridges = self.bridge_monitor.get_all_bridges_overview()
            if not bridges:
                self.send(chat_id, "❌ Could not fetch data. Try again later.")
                return
            msg = "🏆 *BRIDGE TOKENS OVERVIEW*\n━━━━━━━━━━━━━━━━━━━━━━\n_(Sorted by Market Cap)_\n\n"
            for i, b in enumerate(bridges, 1):
                e    = "📈" if b["change"] > 0 else "📉" if b["change"] < 0 else "➡️"
                msg += (f"{i}. {b['color']} *{b['name']}* (${b['token']})\n"
                        f"   MCap: `{b['mcap_str']}` | Vol: `{b['vol_str']}`\n"
                        f"   {e} `{b['change']:+.2f}%` | ⛓️ `{b['chains']} chains`\n\n")
            msg += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_bridge_route(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if len(args) < 2:
            chains = " • ".join(BRIDGE_CHAIN_IDS.keys())
            self.send(chat_id, f"⚠️ Usage: `/bridge_route <from> <to>`\n\nChains:\n`{chains}`")
            return
        from_c = args[0].capitalize()
        to_c   = args[1].capitalize()
        if from_c not in BRIDGE_CHAIN_IDS:
            self.send(chat_id, f"❌ `{from_c}` not supported.\nUse `/bridge_chains`.")
            return
        if to_c not in BRIDGE_CHAIN_IDS:
            self.send(chat_id, f"❌ `{to_c}` not supported.\nUse `/bridge_chains`.")
            return
        self.send(chat_id, f"🔍 Finding routes: *{from_c}* → *{to_c}*...\n⏳ Please wait...")
        try:
            routes    = self.bridge_monitor.get_bridge_route(from_c, to_c)
            supported = [b for b in BRIDGES.values() if from_c in b["chains"] and to_c in b["chains"]]
            msg = f"🌉 *Routes: {from_c} → {to_c}*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            if supported:
                msg += f"\n✅ *Bridges that support this route ({len(supported)}):*"
                for b in supported:
                    msg += f"\n{b['color']} {b['name']} — `{b['website']}`"
            if routes:
                msg += f"\n\n🔗 *LI.FI Active Routes ({len(routes)}):*"
                for r in routes[:3]:
                    msg += f"\n• Via: `{' • '.join(r.get('bridges',[])[:4])}`"
            if not supported and not routes:
                msg += "\n\n❌ No direct routes found."
            msg += f"\n\n⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M')}`"
            self.send(chat_id, msg)
        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_bridge_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            status = "ON ✅" if self.bridge_monitoring else "OFF ❌"
            self.send(chat_id, (f"📡 Bridge Monitor: *{status}*\n"
                                f"Use `/bridge_monitor on` or `/bridge_monitor off`\n\n"
                                f"🔔 Monitors bridge token prices.\n"
                                f"Alerts when 24h change > `±{BRIDGE_TVL_DROP_ALERT}%`"))
            return
        if args[0].lower() == "on":
            if not self.bridge_monitor.watchlist:
                self.send(chat_id, "⚠️ No bridges watched.\nUse `/bridge_add <bridge>` first.")
                return
            self.bridge_monitoring = True
            watched = ", ".join(f"`{k}`" for k in self.bridge_monitor.watchlist)
            self.send(chat_id, f"✅ *Bridge Monitor ON*\nTracking: {watched}\nChecks every {BRIDGE_POLL_INTERVAL//60} min.")
        elif args[0].lower() == "off":
            self.bridge_monitoring = False
            self.send(chat_id, "❌ *Bridge Monitor OFF*")

    def cmd_bridge_bridges(self, chat_id: str):
        if not self.require_sub(chat_id): return
        lines = [f"🌉 *Available Bridges ({len(BRIDGES)})*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for key, b in BRIDGES.items():
            chains = " • ".join(b["chains"][:4])
            lines.append(f"{b['color']} *{b['name']}* (${b['token']})\n  Key: `{key}` | Chains: `{chains}`")
        self.send(chat_id, "\n\n".join(lines))

    def cmd_bridge_chains(self, chat_id: str):
        if not self.require_sub(chat_id): return
        lines = [f"⛓️ *Supported Chains ({len(BRIDGE_CHAIN_IDS)})*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for chain, cid in BRIDGE_CHAIN_IDS.items():
            lines.append(f"• *{chain}* — ID: `{cid}`")
        self.send(chat_id, "\n".join(lines))

    # ─────────────────────────────────────────
    # ADMIN COMMANDS
    # ─────────────────────────────────────────
    def cmd_admin_approve(self, chat_id: str, args: list):
        if not self.db.is_admin(chat_id): return
        if not args: self.send(chat_id, "Usage: `/admin_approve <chat_id>`"); return
        target  = args[0]
        pending = self.db.get_pending(target)
        if not pending: self.send(chat_id, f"⚠️ No pending for `{target}`"); return
        sub    = self.db.add_subscriber(target, pending["plan"], pending.get("username",""))
        self.db.remove_pending(target)
        expiry = sub["expires_at"][:10]
        plan   = PLANS[pending["plan"]]
        self.send(target, f"🎉 *Subscription Activated!*\n✅ Plan: *{plan['name']}*\nExpires: `{expiry}`\n\nUse /help to see all commands!")
        self.send(chat_id, f"✅ Approved `{target}` — *{plan['name']}* until `{expiry}`")

    def cmd_admin_reject(self, chat_id: str, args: list):
        if not self.db.is_admin(chat_id): return
        if not args: self.send(chat_id, "Usage: `/admin_reject <chat_id>`"); return
        self.db.remove_pending(args[0])
        self.send(args[0], "❌ Payment could not be verified. Please contact support or resubmit.")
        self.send(chat_id, f"✅ Rejected `{args[0]}`")

    def cmd_admin_revoke(self, chat_id: str, args: list):
        if not self.db.is_admin(chat_id): return
        if not args: self.send(chat_id, "Usage: `/admin_revoke <chat_id>`"); return
        self.db.revoke(args[0])
        self.send(args[0], "⚠️ Your subscription has been cancelled. Contact support.")
        self.send(chat_id, f"✅ Revoked `{args[0]}`")

    def cmd_admin_extend(self, chat_id: str, args: list):
        if not self.db.is_admin(chat_id): return
        if len(args) < 2: self.send(chat_id, "Usage: `/admin_extend <chat_id> <days>`"); return
        try:
            days = int(args[1])
            self.db.extend(args[0], days)
            self.send(args[0], f"🎁 Your subscription extended by *{days} days*!")
            self.send(chat_id, f"✅ Extended `{args[0]}` by {days} days.")
        except ValueError:
            self.send(chat_id, "⚠️ Days must be a number.")

    def cmd_admin_list(self, chat_id: str):
        if not self.db.is_admin(chat_id): return
        stats   = self.db.get_stats()
        active  = self.db.get_all_active()
        pending = self.db.get_all_pending()
        msg = f"📊 *Admin Dashboard*\n━━━━━━━━━━━━━━━━━━━━━━\n✅ Active     : *{stats['active_now']}*\n⏳ Pending    : *{stats['pending_payments']}*\n💰 Revenue    : *${stats['total_revenue']}*\n👥 Total subs : *{stats['total_subscribers']}*\n\n*Active Subscribers:*\n"
        for sub in active[:10]:
            exp = sub["expires_at"][:10]
            msg += f"• @{sub.get('username','?')} ({sub['plan']}) → `{exp}`\n"
        if pending:
            msg += "\n*Pending:*\n"
            for p in pending:
                msg += f"• @{p.get('username','?')} → {p['plan']} (${p['amount']})\n"
        self.send(chat_id, msg.strip())

    def cmd_admin_stats(self, chat_id: str):
        if not self.db.is_admin(chat_id): return
        stats    = self.db.get_stats()
        expiring = self.db.get_expiring_soon(3)
        self.send(chat_id, f"📈 *Revenue Stats*\n━━━━━━━━━━━━━━━━━━━━━━\n💰 Total Revenue  : *${stats['total_revenue']}*\n👥 Total Subs     : *{stats['total_subscribers']}*\n✅ Active Now     : *{stats['active_now']}*\n⏳ Pending        : *{stats['pending_payments']}*\n⚠️ Expiring 3d   : *{len(expiring)}*")

    # ─────────────────────────────────────────
    # BACKGROUND TASKS
    # ─────────────────────────────────────────
    def _background(self):
        while self.running:
            time.sleep(3600)
            try:
                for sub in self.db.expire_old():
                    self.send(sub["chat_id"], f"⚠️ *Subscription Expired*\nYour *{sub['plan'].upper()}* plan has expired.\nUse /renew to continue!")
                for sub in self.db.get_expiring_soon(3):
                    exp = sub["expires_at"][:10]
                    self.send(sub["chat_id"], f"⏰ *Expiring Soon!*\nYour plan expires `{exp}`.\nUse /renew now!")
            except Exception as e:
                log.error(f"Background error: {e}")

    def _mev_background(self):
        while self.running:
            if self.mev_monitoring:
                try:
                    current = self.mev_w3.eth.block_number
                    if current > self.mev_last_block:
                        result = self.mev_analyzer.scan_block(current)
                        if result.get("mev_count", 0) > 0:
                            summary = result["summary"]
                            self.send(ADMIN_CHAT_ID, f"🎯 *MEV DETECTED — Block #{current}*\n🥪 Sandwiches: `{summary['sandwich_count']}`\n💱 Arbitrages: `{summary['arbitrage_count']}`\n🔴 High Risk : `{summary['high_severity']}`")
                        self.mev_last_block = current
                except Exception as e:
                    log.error(f"MEV monitor error: {e}")
            time.sleep(12)

    def _whale_background(self):
        log.info("🐋 Whale monitor loop started")
        while self.running:
            if self.whale_monitoring and self.whale_tracker and self.whale_tracker.get_wallets():
                try:
                    moves = self.whale_tracker.scan_all()
                    for move in moves:
                        if move["value_usd"] >= 10000 or move["type"] in ("BUY", "SELL", "SWAP"):
                            self.send(ADMIN_CHAT_ID, self._format_whale_move(move))
                            time.sleep(1)
                except Exception as e:
                    log.error(f"Whale monitor error: {e}")
            time.sleep(WHALE_POLL_INTERVAL)

    def _nft_background(self):
        log.info("🖼️ NFT monitor loop started")
        while self.running:
            if self.nft_monitoring and self.nft_tracker and self.nft_tracker.get_collections():
                try:
                    alerts = self.nft_tracker.refresh_all()
                    for alert in alerts:
                        self.send(ADMIN_CHAT_ID, self._format_nft_alert(alert))
                        time.sleep(1)
                except Exception as e:
                    log.error(f"NFT monitor error: {e}")
            time.sleep(NFT_POLL_INTERVAL)

    def _gas_background(self):
        log.info("⛽ Gas monitor loop started")
        while self.running:
            try:
                if self.gas_predictor:
                    gas_data = self.gas_predictor.fetch()
                    if gas_data and self.gas_monitoring:
                        propose = gas_data.get("propose_gas", 0)
                        if propose <= self.gas_low_thresh and not self.gas_predictor.alerts.get("low_gas"):
                            self.send(ADMIN_CHAT_ID, f"⛽ *GAS ALERT — LOW*\n━━━━━━━━━━━━━━━━━━━━━━\n🟢 Gas is very low: *{propose:.1f} Gwei*\nGreat time to send transactions!\n\n⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
                            self.gas_predictor.alerts["low_gas"]  = True
                            self.gas_predictor.alerts["high_gas"] = False
                        elif propose >= self.gas_high_thresh and not self.gas_predictor.alerts.get("high_gas"):
                            self.send(ADMIN_CHAT_ID, f"⛽ *GAS ALERT — HIGH*\n━━━━━━━━━━━━━━━━━━━━━━\n🔴 Gas spike: *{propose:.1f} Gwei*\nConsider waiting for gas to drop.\n\n⏰ `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`")
                            self.gas_predictor.alerts["high_gas"] = True
                            self.gas_predictor.alerts["low_gas"]  = False
                        elif self.gas_low_thresh < propose < self.gas_high_thresh:
                            self.gas_predictor.alerts["low_gas"]  = False
                            self.gas_predictor.alerts["high_gas"] = False
            except Exception as e:
                log.error(f"Gas monitor error: {e}")
            time.sleep(GAS_POLL_INTERVAL)

    def _arb_background(self):
        log.info("🔄 Arbitrage monitor loop started")
        while self.running:
            if self.arb_monitoring and self.arb_engine:
                try:
                    opportunities = self.arb_engine.scan_all()
                    high_opps     = [o for o in opportunities if "HIGH" in o["severity"]]
                    if high_opps:
                        self.send(ADMIN_CHAT_ID, f"🚨 *HIGH PROFIT ARB ALERT!*\nFound *{len(high_opps)}* high severity opportunities!")
                        for opp in high_opps[:2]:
                            self.send(ADMIN_CHAT_ID, self._format_arb_opportunity(opp))
                            time.sleep(0.5)
                    elif opportunities:
                        best = opportunities[0]
                        self.send(ADMIN_CHAT_ID, f"💱 *Arb Update* — Best: *{best['symbol']}* `${best['net_profit']:,.2f}` profit\nBuy {best['buy_dex']} → Sell {best['sell_dex']}")
                    log.info(f"✅ Arb scan: {len(opportunities)} opportunities")
                except Exception as e:
                    log.error(f"Arb monitor error: {e}")
            time.sleep(ARB_POLL_INTERVAL)

    def _gov_background(self):
        log.info("🏛️ Governance monitor loop started")
        while self.running:
            if self.gov_monitoring and self.gov_analyzer and self.gov_analyzer.watchlist:
                try:
                    results = self.gov_analyzer.fetch_all_watched()
                    for dao_key, proposals in results.items():
                        new_ones = self.gov_analyzer.check_new_proposals(proposals)
                        for p in new_ones:
                            self.send(ADMIN_CHAT_ID, self._format_gov_new_alert(p))
                            log.info(f"🔔 New proposal alert: {p.get('title','')[:40]}")
                            time.sleep(1)
                        ending = self.gov_analyzer.check_ending_soon(proposals)
                        for p in ending:
                            alert_key = f"deadline_{p.get('id','')}"
                            if alert_key not in self.gov_analyzer.seen_proposals:
                                self.send(ADMIN_CHAT_ID, self._format_gov_deadline_alert(p))
                                self.gov_analyzer.seen_proposals.add(alert_key)
                                log.info(f"⚠️ Deadline alert: {p.get('title','')[:40]}")
                                time.sleep(1)
                    total_checked = sum(len(v) for v in results.values())
                    log.info(f"✅ Gov monitor scan complete — {total_checked} proposals checked")
                except Exception as e:
                    log.error(f"Gov monitor error: {e}")
            time.sleep(GOV_POLL_INTERVAL)

    def _bridge_background(self):
        log.info("🌉 Bridge monitor loop started")
        while self.running:
            if self.bridge_monitoring and self.bridge_monitor.watchlist:
                try:
                    for key in list(self.bridge_monitor.watchlist):
                        info   = self.bridge_monitor.get_bridge_info(key)
                        if not info:
                            continue
                        alerts = self.bridge_monitor.check_price_alerts(key, info)
                        for alert in alerts:
                            self.send(ADMIN_CHAT_ID, self._format_bridge_price_alert(alert))
                            time.sleep(1)
                        time.sleep(1)
                    log.info(f"✅ Bridge monitor scan — {len(self.bridge_monitor.watchlist)} bridges checked")
                except Exception as e:
                    log.error(f"Bridge monitor error: {e}")
            time.sleep(BRIDGE_POLL_INTERVAL)

    # ─────────────────────────────────────────
    # MESSAGE ROUTER
    # ─────────────────────────────────────────
    def handle(self, message: dict):
        text     = message.get("text", "").strip()
        chat_id  = str(message.get("chat", {}).get("id", ""))
        username = message.get("chat", {}).get("username", "user")
        if not text or not chat_id: return

        parts   = text.split()
        command = parts[0].lower()
        args    = parts[1:]
        log.info(f"📨 {command} from @{username} ({chat_id})")

        # Free commands
        if   command in ("/start", "/start@"): self.cmd_start(chat_id, username)
        elif command == "/help":               self.cmd_help(chat_id)
        elif command == "/plans":              self.cmd_plans(chat_id)
        elif command == "/subscribe":          self.cmd_subscribe(chat_id, username, args)
        elif command == "/confirm":            self.cmd_confirm(chat_id, username, args)
        elif command == "/status":             self.cmd_status(chat_id)
        elif command == "/renew":              self.cmd_renew(chat_id, username)

        # Portfolio tracker
        elif command == "/track":     self.cmd_track(chat_id, args)
        elif command == "/watch":     self.cmd_watch(chat_id, args)
        elif command == "/watchlist": self.cmd_watchlist(chat_id)
        elif command == "/unwatch":   self.cmd_unwatch(chat_id, args)
        elif command == "/refresh":   self.cmd_refresh(chat_id)

        # Analytics
        elif command == "/analyze": self.cmd_analyze(chat_id, args)
        elif command == "/preset":  self.cmd_preset(chat_id)
        elif command == "/use":     self.cmd_use(chat_id, args)
        elif command == "/report":  self.cmd_report(chat_id, args)
        elif command == "/top":     self.cmd_top(chat_id, args)
        elif command == "/trend":   self.cmd_trend(chat_id)
        elif command == "/alert":   self.cmd_alert(chat_id, args)

        # MEV detector
        elif command == "/mev":         self.cmd_mev_scan(chat_id, args)
        elif command == "/mev_latest":  self.cmd_mev_latest(chat_id)
        elif command == "/mev_monitor": self.cmd_mev_monitor(chat_id, args)
        elif command == "/mev_bots":    self.cmd_mev_bots(chat_id)

        # DeFi Yield
        elif command == "/yield":          self.cmd_yield(chat_id, args)
        elif command == "/yield_stable":   self.cmd_yield_stable(chat_id)
        elif command == "/yield_aave":     self.cmd_yield_protocol(chat_id, "aave")
        elif command == "/yield_compound": self.cmd_yield_protocol(chat_id, "compound")
        elif command == "/yield_curve":    self.cmd_yield_protocol(chat_id, "curve")
        elif command == "/yield_uni":      self.cmd_yield_protocol(chat_id, "uniswap")
        elif command == "/yield_summary":  self.cmd_yield_summary(chat_id)
        elif command == "/yield_alert":    self.cmd_yield_alert(chat_id, args)

        # Token Sniffer
        elif command == "/sniff": self.cmd_sniff(chat_id, args)
        elif command == "/quick": self.cmd_quick(chat_id, args)

        # Whale Tracker
        elif command == "/whale_add":     self.cmd_whale_add(chat_id, args)
        elif command == "/whale_remove":  self.cmd_whale_remove(chat_id, args)
        elif command == "/whale_list":    self.cmd_whale_list(chat_id)
        elif command == "/whale_check":   self.cmd_whale_check(chat_id, args)
        elif command == "/whale_monitor": self.cmd_whale_monitor(chat_id, args)
        elif command == "/whale_whales":  self.cmd_whale_whales(chat_id)
        elif command == "/whale_alert":   self.cmd_whale_alert(chat_id, args)

        # NFT Floor Tracker
        elif command == "/nft_floor":   self.cmd_nft_floor(chat_id, args)
        elif command == "/nft_add":     self.cmd_nft_add(chat_id, args)
        elif command == "/nft_remove":  self.cmd_nft_remove(chat_id, args)
        elif command == "/nft_list":    self.cmd_nft_list(chat_id)
        elif command == "/nft_sales":   self.cmd_nft_sales(chat_id, args)
        elif command == "/nft_top":     self.cmd_nft_top(chat_id)
        elif command == "/nft_search":  self.cmd_nft_search(chat_id, args)
        elif command == "/nft_monitor": self.cmd_nft_monitor(chat_id, args)
        elif command == "/nft_known":   self.cmd_nft_known(chat_id)

        # Gas Price Predictor
        elif command == "/gas":           self.cmd_gas(chat_id)
        elif command == "/gas_fast":      self.cmd_gas_fast(chat_id)
        elif command == "/gas_estimate":  self.cmd_gas_estimate(chat_id, args)
        elif command == "/gas_trend":     self.cmd_gas_trend(chat_id)
        elif command == "/gas_history":   self.cmd_gas_history(chat_id)
        elif command == "/gas_monitor":   self.cmd_gas_monitor(chat_id, args)
        elif command == "/gas_threshold": self.cmd_gas_threshold(chat_id, args)

        # Arbitrage Scanner
        elif command == "/arb_scan":     self.cmd_arb_scan(chat_id)
        elif command == "/arb_token":    self.cmd_arb_token(chat_id, args)
        elif command == "/arb_top":      self.cmd_arb_top(chat_id)
        elif command == "/arb_pairs":    self.cmd_arb_pairs(chat_id)
        elif command == "/arb_monitor":  self.cmd_arb_monitor(chat_id, args)
        elif command == "/arb_stats":    self.cmd_arb_stats(chat_id)
        elif command == "/arb_settings": self.cmd_arb_settings(chat_id)

        # DAO Governance Tracker
        elif command == "/gov_proposals": self.cmd_gov_proposals(chat_id, args)
        elif command == "/gov_proposal":  self.cmd_gov_proposal(chat_id, args)
        elif command == "/gov_add":       self.cmd_gov_add(chat_id, args)
        elif command == "/gov_remove":    self.cmd_gov_remove(chat_id, args)
        elif command == "/gov_list":      self.cmd_gov_list(chat_id)
        elif command == "/gov_summary":   self.cmd_gov_summary(chat_id, args)
        elif command == "/gov_daos":      self.cmd_gov_daos(chat_id)
        elif command == "/gov_monitor":   self.cmd_gov_monitor(chat_id, args)
        elif command == "/gov_top":       self.cmd_gov_top(chat_id)

        # Cross-Chain Bridge Monitor
        elif command == "/bridge_info":    self.cmd_bridge_info(chat_id, args)
        elif command == "/bridge_add":     self.cmd_bridge_add(chat_id, args)
        elif command == "/bridge_remove":  self.cmd_bridge_remove(chat_id, args)
        elif command == "/bridge_list":    self.cmd_bridge_list(chat_id)
        elif command == "/bridge_tvl":     self.cmd_bridge_tvl(chat_id)
        elif command == "/bridge_route":   self.cmd_bridge_route(chat_id, args)
        elif command == "/bridge_monitor": self.cmd_bridge_monitor(chat_id, args)
        elif command == "/bridge_bridges": self.cmd_bridge_bridges(chat_id)
        elif command == "/bridge_chains":  self.cmd_bridge_chains(chat_id)

        # Admin
        elif command == "/admin_approve": self.cmd_admin_approve(chat_id, args)
        elif command == "/admin_reject":  self.cmd_admin_reject(chat_id, args)
        elif command == "/admin_revoke":  self.cmd_admin_revoke(chat_id, args)
        elif command == "/admin_extend":  self.cmd_admin_extend(chat_id, args)
        elif command == "/admin_list":    self.cmd_admin_list(chat_id)
        elif command == "/admin_stats":   self.cmd_admin_stats(chat_id)

        else:
            self.send(chat_id, "❓ Unknown command. Use /help to see all commands.")

    # ─────────────────────────────────────────
    # MAIN LOOP
    # ─────────────────────────────────────────
    def run(self):
        log.info("🚀 All-in-One Bot started!")
        self.send(ADMIN_CHAT_ID, (
            "🤖 *All-in-One Bot Online!*\n\n"
            "✅ Contract Analytics\n"
            "✅ Portfolio Tracker\n"
            "✅ MEV Detector\n"
            "✅ DeFi Yield\n"
            "✅ Token Sniffer\n"
            "✅ Whale Tracker\n"
            "✅ NFT Floor Tracker\n"
            "✅ Gas Price Predictor\n"
            "✅ Arbitrage Scanner\n"
            "✅ DAO Governance Tracker\n"
            "✅ Cross-Chain Bridge Monitor\n\n"
            "Use /admin_list to manage subscribers."
        ))
        threading.Thread(target=self._background,       daemon=True).start()
        threading.Thread(target=self._mev_background,   daemon=True).start()
        threading.Thread(target=self._whale_background, daemon=True).start()
        threading.Thread(target=self._nft_background,   daemon=True).start()
        threading.Thread(target=self._gas_background,   daemon=True).start()
        threading.Thread(target=self._arb_background,   daemon=True).start()
        threading.Thread(target=self._gov_background,   daemon=True).start()
        threading.Thread(target=self._bridge_background,daemon=True).start()

        while self.running:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.offset = update["update_id"] + 1
                    msg = update.get("message", {})
                    if msg: self.handle(msg)
            except KeyboardInterrupt:
                self.running = False
            except Exception as e:
                log.error(f"Polling error: {e}")
                time.sleep(5)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    bot = AnalyticsBot()
    bot.run()
