"""
analytic_bot.py - Contract Analytics + Subscription Bot
Web3 Python Toolkit by Rizal
All-in-one: analytics commands + subscription/payment management
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
    ca = importlib.import_module("contract-analytics")
    ContractAnalytics = ca.ContractAnalytics
    TelegramNotifier  = ca.TelegramNotifier
    log.info("✅ contract-analytics imported")
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
        self.analytics     = {}   # chat_id → ContractAnalytics
        self.active_contract = {}  # chat_id → address
        self.alert_enabled = {}   # chat_id → bool
        self.monitor_thread = None

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
        has_sub  = self.db.is_active(chat_id)

        msg = """
🤖 *Contract Analytics Bot*
━━━━━━━━━━━━━━━━━━━━━━

🆓 *Free Commands:*
/start — Welcome & status
/plans — See subscription plans
/subscribe `<plan>` — Subscribe (basic/pro/premium)
/confirm `<tx_hash>` — Confirm USDT payment
/status — Check your subscription
/renew — Renew current plan

📊 *Analytics Commands* _(subscribers only)_:
/analyze `<address>` — Analyze any contract
/preset — List preset contracts
/use `<name>` — Use preset contract
/report `[days]` — Full analytics report
/top `[n]` — Top N callers
/trend — 24h vs 7d trend
/alert `<on/off>` — Toggle anomaly alerts
        """.strip()

        if is_admin:
            msg += """

👑 *Admin Commands:*
/admin_list — All subscribers
/admin_stats — Revenue dashboard
/admin_approve `<id>` — Approve payment
/admin_reject `<id>` — Reject payment
/admin_revoke `<id>` — Cancel subscription
/admin_extend `<id> <days>` — Extend subscription"""

        self.send(chat_id, msg)

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

        # Analytics (subscribers only)
        elif command == "/analyze":  self.cmd_analyze(chat_id, args)
        elif command == "/preset":   self.cmd_preset(chat_id)
        elif command == "/use":      self.cmd_use(chat_id, args)
        elif command == "/report":   self.cmd_report(chat_id, args)
        elif command == "/top":      self.cmd_top(chat_id, args)
        elif command == "/trend":    self.cmd_trend(chat_id)
        elif command == "/alert":    self.cmd_alert(chat_id, args)

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
        self.send(ADMIN_CHAT_ID, "🤖 *Analytics + Subscription Bot Online!*\n\nUse /admin_list to manage subscribers.")
        threading.Thread(target=self._background, daemon=True).start()

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