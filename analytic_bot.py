"""
analytic_bot.py - Contract Analytics + Subscription + Portfolio Tracker + MEV Detector + DeFi Yield Bot
Web3 Python Toolkit by Rizal
All-in-one: analytics + subscription + portfolio + MEV + yield aggregator
"""

import os
import sys
import json
import time
import logging
import requests
import threading
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter
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
    import importlib
    import sys
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
# CONFIG
# ─────────────────────────────────────────────
TELEGRAM_TOKEN   = "8660442841:AAE1oCT6WkyhVdE9eC46I-YOD-FNBjeomYY"
ADMIN_CHAT_ID    = "1024188205"   # Rizal — admin only
USDT_TRC20       = "TNxivKGm18XCYtgM2TMewNompRnBqfPjFY"

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

MIN_GAS_PREMIUM = 1.5
SANDWICH_WINDOW = 3


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
            self._cache["eth"] = price
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
            eth_bal   = float(self.w3.eth.get_balance(Web3.to_checksum_address(address))) / 1e18
        except Exception:
            eth_bal   = self.etherscan.get_eth_balance(address)
        eth_price = self.prices.get_eth_price()
        eth_value = eth_bal * eth_price

        tokens = self.etherscan.get_token_balances(address)
        token_total = 0
        for t in tokens[:20]:
            price = self.prices.get_token_price(t["contract"])
            t["price_usd"] = price
            t["value_usd"] = round(t["balance"] * price, 2)
            token_total += t["value_usd"]
        tokens = sorted(tokens, key=lambda x: x.get("value_usd", 0), reverse=True)

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
        plan_data  = PLANS[plan]
        expiry     = datetime.now() + timedelta(days=plan_data["duration"])
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

        txs        = [dict(tx) for tx in block.get("transactions", [])]
        dex_txs    = []

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

        # Detect sandwiches
        sandwiches = []
        from collections import defaultdict
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

        # Detect known bot arbitrage
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
    """Aggregate & rank yields dari Aave, Compound, Curve, Uniswap V3."""

    def __init__(self):
        self.session   = requests.Session()
        self._cache    = []
        self._cache_ts = 0

    def _get_defillama(self, project: str, chain: str = "Ethereum") -> list:
        """Generic fetch dari DeFi Llama yields API."""
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
# MAIN BOT
# ─────────────────────────────────────────────
class AnalyticsBot:
    def __init__(self):
        self.token    = TELEGRAM_TOKEN
        self.base     = f"https://api.telegram.org/bot{self.token}"
        self.db       = SubscriberDB()
        self.offset   = 0
        self.running  = True

        # Analytics state per user
        self.analytics        = {}
        self.active_contract  = {}
        self.alert_enabled    = {}
        self.monitor_thread   = None

        # Portfolio tracker state
        self.portfolio_analyzer = PortfolioAnalyzer(
            etherscan_key=os.getenv("ETHERSCAN_API_KEY", "AW8AJ3TQV79VTM1WM9KY7W9H5ICZZ1WUYT"),
            infura_url=os.getenv("INFURA_URL", "https://mainnet.infura.io/v3/e1576449bd6142eba99fd3cc4f3fe7b3")
        )
        self.watchlist = {}  # chat_id → [addresses]

        # MEV detector state
        self.mev_w3       = Web3(Web3.HTTPProvider(os.getenv("INFURA_URL", "https://mainnet.infura.io/v3/e1576449bd6142eba99fd3cc4f3fe7b3")))
        self.mev_analyzer = MEVAnalyzer(self.mev_w3)
        self.mev_monitoring = False
        self.mev_last_block = 0

        # DeFi Yield Aggregator state
        self.yield_aggregator = YieldAggregator()
        self.yield_alert_on   = False

        log.info("🤖 AnalyticsBot (All-in-One) initialized")

    # ─────────────────────────────────────────
    # TELEGRAM HELPERS
    # ─────────────────────────────────────────
    def send(self, chat_id: str, text: str, parse_mode: str = "Markdown"):
        try:
            r = requests.post(
                f"{self.base}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
                timeout=10
            )
            return r.json()
        except Exception as e:
            log.error(f"Send error: {e}")

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
        """Check if user has active subscription. Admin always passes."""
        if self.db.is_admin(chat_id):
            return True
        if self.db.is_active(chat_id):
            return True
        self.send(chat_id, "🔒 *This feature requires an active subscription.*\n\nUse /plans to see pricing or /subscribe to get started!")
        return False

    # ─────────────────────────────────────────
    # USER COMMANDS — FREE
    # ─────────────────────────────────────────
    def cmd_start(self, chat_id: str, username: str):
        if self.db.is_active(chat_id) or self.db.is_admin(chat_id):
            sub  = self.db.get_subscriber(chat_id)
            plan = sub.get("plan", "admin").upper()
            self.send(chat_id, f"""
👋 *Welcome back, @{username}!*

✅ Plan: *{plan}* — Active
Use /help to see all available commands.
            """.strip())
        else:
            self.send(chat_id, f"""
👋 *Welcome to Contract Analytics Bot!*
━━━━━━━━━━━━━━━━━━━━━━

Monitor any Ethereum smart contract in real-time:
📊 Usage pattern analysis
🚨 Anomaly detection alerts
📈 Trend comparison (24h vs 7d)
👤 Top caller ranking
🔍 ABI function decoder

━━━━━━━━━━━━━━━━━━━━━━
Use /plans to see pricing & subscribe!
            """.strip())

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

💼 <b>Portfolio Tracker</b> (subscribers only):
/track — Analisis portfolio wallet
/watch — Tambah ke watchlist
/watchlist — Lihat watchlist
/unwatch — Hapus dari watchlist
/refresh — Refresh watchlist

📊 <b>Contract Analytics</b> (subscribers only):
/analyze — Analisis smart contract
/preset — List preset contracts
/use — Gunakan preset
/report — Full analytics report
/top — Top N callers
/trend — 24h vs 7d trend
/alert — Toggle anomaly alerts

🎯 <b>MEV Detector</b> (subscribers only):
/mev — Scan block untuk MEV
/mev_latest — Scan block terbaru
/mev_monitor — Auto monitor MEV
/mev_bots — List known MEV bots

💰 <b>DeFi Yield Aggregator</b> (subscribers only):
/yield — Best yield opportunities
/yield_stable — Stablecoin yields only
/yield_aave — Aave V3 rates
/yield_compound — Compound rates
/yield_curve — Curve pools
/yield_uni — Uniswap V3 pools
/yield_summary — Market overview
/yield_alert — APY spike alerts
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
        self.send(chat_id, f"""
💳 *Payment Instructions — {plan_data['name']}*
━━━━━━━━━━━━━━━━━━━━━━

💰 Amount  : *${plan_data['price']} USDT*
🌐 Network : *TRC20 (Tron)*
📋 Address :
`{USDT_TRC20}`

━━━━━━━━━━━━━━━━━━━━━━
1️⃣ Send *${plan_data['price']} USDT* via TRC20
2️⃣ Copy your TX hash/ID after sending
3️⃣ Send: `/confirm <your_tx_hash>`
4️⃣ Wait for activation (within 1 hour)

⚠️ TRC20 network only! Other networks = lost funds.
        """.strip())

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

        self.send(chat_id, f"""
⏳ *Payment submitted!*

📋 Plan    : *{PLANS[plan]['name']}*
💰 Amount  : *${amount} USDT*
🔗 TX Hash : `{tx_hash}`

Activation within *1 hour*. You'll get a confirmation message. 🎉
        """.strip())

        self.send(ADMIN_CHAT_ID, f"""
🔔 *NEW PAYMENT*
━━━━━━━━━━━━━━━━━━━━━━
👤 @{username} (`{chat_id}`)
📋 Plan : *{PLANS[plan]['name']}* (${amount}/mo)
🔗 TX   : `{tx_hash}`

`/admin_approve {chat_id}` ✅
`/admin_reject {chat_id}` ❌
        """.strip())

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

        self.send(chat_id, f"""
📊 *Your Subscription*
━━━━━━━━━━━━━━━━━━━━━━
✅ Plan      : *{plan['name']}*
📅 Expires   : `{expiry.strftime('%Y-%m-%d')}`
⏳ Days left : *{days_left} days*
🏷️ Contracts : up to *{plan['contracts']}*

Use /renew to extend anytime!
        """.strip())

    def cmd_renew(self, chat_id: str, username: str):
        sub = self.db.get_subscriber(chat_id)
        if not sub:
            self.send(chat_id, "❌ No subscription found. Use /subscribe to get started!")
            return
        self.cmd_subscribe(chat_id, username, [sub["plan"]])

    # ─────────────────────────────────────────
    # ANALYTICS COMMANDS — SUBSCRIBERS ONLY
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
            self.analytics[chat_id]      = analytics
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
            self.send(chat_id, f"""
📈 *Trend Analysis*
━━━━━━━━━━━━━━━━━━━━━━
📊 Last 24h    : `{trend['txs_last_24h']:,}` TXs
📅 7d Average  : `{trend['avg_daily_7d']:,}` TXs/day
📉 Change      : `{trend['change_percent']}%`
🎯 Status      : {trend['trend']}
            """.strip())
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
        usage = report.get("usage", {})
        trend = report.get("trend", {})
        anomaly_count = len(report.get("anomalies", []))
        self.send(chat_id, f"""
📊 *CONTRACT ANALYTICS REPORT*
━━━━━━━━━━━━━━━━━━━━━━
🏷️ *{usage.get('contract_name', 'Unknown')}*
📍 `{usage.get('contract', '')[:20]}...`

📈 *Activity ({usage.get('period_days', 7)}d)*
• Total TXs     : `{usage.get('total_txs', 0):,}`
• Unique Callers: `{usage.get('unique_callers', 0):,}`
• Success Rate  : `{usage.get('success_rate', 0)}%`
• Avg Gas       : `{usage.get('avg_gas_used', 0):,}`

⚡ *Trend*
• Last 24h  : `{trend.get('txs_last_24h', 0):,}` TXs
• 7d Average: `{trend.get('avg_daily_7d', 0):,}` TXs/day
• Change    : `{trend.get('change_percent', 0)}%` {trend.get('trend', '')}

🚨 *Anomalies* : `{anomaly_count}`
        """.strip())

    # ─────────────────────────────────────────
    # PORTFOLIO TRACKER COMMANDS
    # ─────────────────────────────────────────
    def _send_portfolio_report(self, chat_id: str, data: dict):
        summary = data["summary"]
        eth     = data["eth"]
        tokens  = data["tokens"][:5]
        nfts    = data["nfts"][:3]
        addr    = data["address"]

        msg = f"""
💼 *PORTFOLIO TRACKER*
━━━━━━━━━━━━━━━━━━━━━━
👛 `{addr[:6]}...{addr[-4:]}`
⏰ {data['timestamp'][:19]}

💰 *Total: ${summary['total_value_usd']:,.2f}*
━━━━━━━━━━━━━━━━━━━━━━
🔷 *ETH*
• Balance : `{eth['balance']} ETH`
• Price   : `${eth['price_usd']:,.2f}`
• Value   : `${eth['value_usd']:,.2f}`
        """.strip()

        if tokens:
            msg += "\n\n🪙 *Top Tokens*"
            for t in tokens:
                val = t.get("value_usd", 0)
                if val > 0:
                    msg += f"\n• {t['symbol']}: `{t['balance']}` (~`${val:,.2f}`)"
                else:
                    msg += f"\n• {t['symbol']}: `{t['balance']}`"

        if nfts:
            msg += f"\n\n🖼️ *NFTs ({len(data['nfts'])} total)*"
            for n in nfts:
                msg += f"\n• {n['name']} #{n['token_id']}"

        msg += f"""

━━━━━━━━━━━━━━━━━━━━━━
📊 *Breakdown*
• ETH    : `${summary['eth_value']:,.2f}`
• Tokens : `${summary['token_value']:,.2f}` ({summary['token_count']} tokens)
• NFTs   : `{summary['nft_count']} items`
        """
        self.send(chat_id, msg.strip())

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
            self.send(chat_id, f"✅ `{address[:10]}...` ditambahkan ke watchlist!\nAuto-refresh setiap 60 menit.")
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
            msg = f"""
🎯 *MEV SCAN — Block #{block_num}*
━━━━━━━━━━━━━━━━━━━━━━
📦 Total TXs   : `{result['total_txs']}`
🔄 DEX TXs     : `{result['dex_txs']}`
⚡ MEV Found   : `{result['mev_count']}`

🥪 Sandwiches  : `{summary['sandwich_count']}`
💱 Arbitrages  : `{summary['arbitrage_count']}`
🔴 High Risk   : `{summary['high_severity']}`
            """.strip()
            self.send(chat_id, msg)

            # Detail sandwiches
            for s in result["sandwiches"][:3]:
                sev = "🔴" if s["severity"] == "HIGH" else "🟡"
                known = f"\n⚠️ Known: `{s['bot_label']}`" if s["is_known_bot"] else ""
                self.send(chat_id, f"""
{sev} *SANDWICH ATTACK*
👤 Attacker: `{s['attacker'][:10]}...`
🏊 DEX: `{s['dex']}`
🎯 Victims: `{s['victims']}`{known}
                """.strip())

            # Detail arbitrages
            for a in result["arbitrages"][:3]:
                self.send(chat_id, f"""
🔴 *ARBITRAGE — {a['bot_label']}*
🤖 Bot: `{a['bot'][:10]}...`
🏊 DEX: `{a['dex']}`
🔧 Fn: `{a['function']}`
                """.strip())

            if result["mev_count"] == 0:
                self.send(chat_id, "✅ Tidak ada MEV terdeteksi di block ini.")

        except Exception as e:
            self.send(chat_id, f"❌ Error: `{str(e)[:200]}`")

    def cmd_mev_latest(self, chat_id: str):
        if not self.require_sub(chat_id): return
        block_num = self.mev_w3.eth.block_number
        self.cmd_mev_scan(chat_id, [str(block_num)])

    def cmd_mev_monitor(self, chat_id: str, args: list):
        if not self.require_sub(chat_id): return
        if not args:
            status = "ON ✅" if self.mev_monitoring else "OFF ❌"
            self.send(chat_id, f"📡 MEV Monitor: *{status}*\nGunakan `/mev_monitor on` atau `/mev_monitor off`")
            return

        if args[0].lower() == "on":
            self.mev_monitoring  = True
            self.mev_last_block  = self.mev_w3.eth.block_number
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
            self.send(chat_id, f"""
📊 *DEFI YIELD OVERVIEW*
━━━━━━━━━━━━━━━━━━━━━━
🏦 Protocols  : `{protocols}`
📈 Highest APY: `{s['highest_apy']}%`
📉 Lowest APY : `{s['lowest_apy']}%`
📊 Average APY: `{s['avg_apy']}%`
🔢 Total Opps : `{s['total']}`
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """.strip())
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
    # ADMIN COMMANDS
    # ─────────────────────────────────────────
    def cmd_admin_approve(self, chat_id: str, args: list):
        if not self.db.is_admin(chat_id): return
        if not args: self.send(chat_id, "Usage: `/admin_approve <chat_id>`"); return
        target  = args[0]
        pending = self.db.get_pending(target)
        if not pending: self.send(chat_id, f"⚠️ No pending for `{target}`"); return
        sub   = self.db.add_subscriber(target, pending["plan"], pending.get("username",""))
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
        msg = f"""
📊 *Admin Dashboard*
━━━━━━━━━━━━━━━━━━━━━━
✅ Active     : *{stats['active_now']}*
⏳ Pending    : *{stats['pending_payments']}*
💰 Revenue    : *${stats['total_revenue']}*
👥 Total subs : *{stats['total_subscribers']}*

*Active Subscribers:*
"""
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
        self.send(chat_id, f"""
📈 *Revenue Stats*
━━━━━━━━━━━━━━━━━━━━━━
💰 Total Revenue  : *${stats['total_revenue']}*
👥 Total Subs     : *{stats['total_subscribers']}*
✅ Active Now     : *{stats['active_now']}*
⏳ Pending        : *{stats['pending_payments']}*
⚠️ Expiring 3d   : *{len(expiring)}*
        """.strip())

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
        """Background thread untuk auto MEV monitoring."""
        while self.running:
            if self.mev_monitoring:
                try:
                    current = self.mev_w3.eth.block_number
                    if current > self.mev_last_block:
                        result = self.mev_analyzer.scan_block(current)
                        if result.get("mev_count", 0) > 0:
                            summary = result["summary"]
                            self.send(ADMIN_CHAT_ID, f"""
🎯 *MEV DETECTED — Block #{current}*
🥪 Sandwiches: `{summary['sandwich_count']}`
💱 Arbitrages: `{summary['arbitrage_count']}`
🔴 High Risk : `{summary['high_severity']}`
                            """.strip())
                        self.mev_last_block = current
                except Exception as e:
                    log.error(f"MEV monitor error: {e}")
            time.sleep(12)  # ~1 Ethereum block

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

        # Portfolio tracker (subscribers only)
        elif command == "/track":      self.cmd_track(chat_id, args)
        elif command == "/watch":      self.cmd_watch(chat_id, args)
        elif command == "/watchlist":  self.cmd_watchlist(chat_id)
        elif command == "/unwatch":    self.cmd_unwatch(chat_id, args)
        elif command == "/refresh":    self.cmd_refresh(chat_id)

        # Analytics (subscribers only)
        elif command == "/analyze":  self.cmd_analyze(chat_id, args)
        elif command == "/preset":   self.cmd_preset(chat_id)
        elif command == "/use":      self.cmd_use(chat_id, args)
        elif command == "/report":   self.cmd_report(chat_id, args)
        elif command == "/top":      self.cmd_top(chat_id, args)
        elif command == "/trend":    self.cmd_trend(chat_id)
        elif command == "/alert":    self.cmd_alert(chat_id, args)

        # MEV detector (subscribers only)
        elif command == "/mev":          self.cmd_mev_scan(chat_id, args)
        elif command == "/mev_latest":   self.cmd_mev_latest(chat_id)
        elif command == "/mev_monitor":  self.cmd_mev_monitor(chat_id, args)
        elif command == "/mev_bots":     self.cmd_mev_bots(chat_id)

        # DeFi Yield (subscribers only)
        elif command == "/yield":          self.cmd_yield(chat_id, args)
        elif command == "/yield_stable":   self.cmd_yield_stable(chat_id)
        elif command == "/yield_aave":     self.cmd_yield_protocol(chat_id, "aave")
        elif command == "/yield_compound": self.cmd_yield_protocol(chat_id, "compound")
        elif command == "/yield_curve":    self.cmd_yield_protocol(chat_id, "curve")
        elif command == "/yield_uni":      self.cmd_yield_protocol(chat_id, "uniswap")
        elif command == "/yield_summary":  self.cmd_yield_summary(chat_id)
        elif command == "/yield_alert":    self.cmd_yield_alert(chat_id, args)

        # Admin only
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
        self.send(ADMIN_CHAT_ID, "🤖 *Analytics + Subscription + Portfolio + MEV Bot Online!*\n\nUse /admin_list to manage subscribers.")
        threading.Thread(target=self._background, daemon=True).start()
        threading.Thread(target=self._mev_background, daemon=True).start()

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