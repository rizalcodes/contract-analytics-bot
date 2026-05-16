"""
analytics_bot.py - Telegram Bot for Smart Contract Analytics
Web3 Python Toolkit by Rizal
Commands: /analyze, /report, /alert, /top, /trend, /help
"""

import os
import time
import logging
import requests
import threading
from datetime import datetime
from contract_analytics import ContractAnalytics, TelegramNotifier

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
# CONFIG
# ─────────────────────────────────────────────
TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN",   "8660442841:AAEOXjIzvJA3xSKh0DHi_V9jLXeEshO2L2k")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "1024188205")

# Default contracts yang bisa langsung dianalisis
PRESET_CONTRACTS = {
    "uniswap_v2" : "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "uniswap_v3" : "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "aave_v3"    : "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "compound"   : "0xc3d688B66703497DAA19211EEdff47f25384cdc3",
}

HELP_TEXT = """
🤖 *Contract Analytics Bot*
━━━━━━━━━━━━━━━━━━━━━━

📋 *Commands:*

/analyze `<address>` — Analisis contract address
/preset — List contract preset yang tersedia
/use `<name>` — Gunakan preset contract
/report `[days]` — Full report (default: 7 hari)
/top `[n]` — Top N callers (default: 10)
/trend — Bandingkan trend 24h vs 7d
/alert `<on/off>` — Toggle auto alert anomaly
/status — Status monitoring sekarang
/help — Tampilkan bantuan ini

📌 *Contoh:*
/analyze 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D
/use uniswap_v2
/report 3
/top 5
/alert on
""".strip()


# ─────────────────────────────────────────────
# BOT CLASS
# ─────────────────────────────────────────────
class AnalyticsBot:
    def __init__(self):
        self.token       = TELEGRAM_TOKEN
        self.chat_id     = TELEGRAM_CHAT_ID
        self.base        = f"https://api.telegram.org/bot{self.token}"
        self.notifier    = TelegramNotifier(self.token, self.chat_id)
        self.offset      = 0

        # State
        self.active_contract  = None   # address yang sedang dimonitor
        self.analytics        = None   # ContractAnalytics instance
        self.alert_enabled    = False  # auto alert toggle
        self.monitor_thread   = None   # background monitor thread
        self.running          = True

        log.info("🤖 Analytics Bot initialized")

    # ─────────────────────────────────────────
    # TELEGRAM API HELPERS
    # ─────────────────────────────────────────
    def send(self, text: str, parse_mode: str = "Markdown"):
        try:
            r = requests.post(
                f"{self.base}/sendMessage",
                json={
                    "chat_id"   : self.chat_id,
                    "text"      : text,
                    "parse_mode": parse_mode,
                },
                timeout=10
            )
            return r.json()
        except Exception as e:
            log.error(f"Send error: {e}")

    def get_updates(self) -> list:
        try:
            r = requests.get(
                f"{self.base}/getUpdates",
                params={"offset": self.offset, "timeout": 30},
                timeout=35
            )
            data = r.json()
            return data.get("result", [])
        except Exception as e:
            log.error(f"getUpdates error: {e}")
            return []

    # ─────────────────────────────────────────
    # COMMAND HANDLERS
    # ─────────────────────────────────────────
    def cmd_help(self, args: list):
        self.send(HELP_TEXT)

    def cmd_analyze(self, args: list):
        if not args:
            self.send("⚠️ Masukkan contract address!\nContoh: `/analyze 0x7a250d...`")
            return

        address = args[0].strip()
        if not address.startswith("0x") or len(address) != 42:
            self.send("❌ Address tidak valid. Harus format `0x...` (42 karakter)")
            return

        self.send(f"🔍 Menganalisis contract...\n`{address}`\n\n⏳ Mohon tunggu ~30 detik...")

        try:
            self.analytics       = ContractAnalytics(address)
            self.active_contract = address
            report = self.analytics.full_report(days_back=7)
            self.notifier.send_usage_report(report)

            # Kirim anomaly jika ada
            anomalies = report.get("anomalies", [])
            if anomalies:
                for a in anomalies[:3]:
                    name = report.get("usage", {}).get("contract_name", "Unknown")
                    self.notifier.send_anomaly_alert(name, a)
            else:
                self.send("✅ *Tidak ada anomali terdeteksi*")

        except Exception as e:
            self.send(f"❌ Error saat analisis:\n`{str(e)[:200]}`")
            log.error(f"analyze error: {e}")

    def cmd_preset(self, args: list):
        lines = ["📋 *Preset Contracts:*\n"]
        for name, addr in PRESET_CONTRACTS.items():
            lines.append(f"• `{name}` → `{addr[:10]}...`")
        lines.append("\nGunakan: `/use <name>`")
        self.send("\n".join(lines))

    def cmd_use(self, args: list):
        if not args:
            self.send("⚠️ Contoh: `/use uniswap_v2`")
            return

        name = args[0].lower().strip()
        if name not in PRESET_CONTRACTS:
            available = ", ".join(f"`{k}`" for k in PRESET_CONTRACTS)
            self.send(f"❌ Preset tidak ditemukan.\nTersedia: {available}")
            return

        address = PRESET_CONTRACTS[name]
        self.send(f"✅ Menggunakan preset *{name}*\n`{address}`\n\n⏳ Memuat analisis...")

        try:
            self.analytics       = ContractAnalytics(address)
            self.active_contract = address
            report = self.analytics.full_report(days_back=7)
            self.notifier.send_usage_report(report)
        except Exception as e:
            self.send(f"❌ Error: `{str(e)[:200]}`")

    def cmd_report(self, args: list):
        if not self.analytics:
            self.send("⚠️ Belum ada contract yang dianalisis.\nGunakan `/analyze <address>` atau `/use <name>` dulu.")
            return

        days = 7
        if args:
            try:
                days = int(args[0])
                days = max(1, min(days, 30))  # clamp 1-30
            except ValueError:
                pass

        self.send(f"📊 Generating report {days} hari terakhir...")
        try:
            report = self.analytics.full_report(days_back=days)
            self.notifier.send_usage_report(report)
        except Exception as e:
            self.send(f"❌ Error: `{str(e)[:200]}`")

    def cmd_top(self, args: list):
        if not self.analytics:
            self.send("⚠️ Gunakan `/analyze` atau `/use` dulu.")
            return

        n = 10
        if args:
            try:
                n = int(args[0])
                n = max(1, min(n, 20))
            except ValueError:
                pass

        self.send(f"👤 Mengambil top {n} callers...")
        try:
            callers = self.analytics.top_callers(days_back=7, top_n=n)
            if not callers:
                self.send("📭 Tidak ada data caller ditemukan.")
                return

            lines = [f"👤 *Top {n} Callers*\n━━━━━━━━━━━━━━━━━━━━━━"]
            for i, c in enumerate(callers, 1):
                addr     = c["address"]
                short    = f"{addr[:6]}...{addr[-4:]}"
                lines.append(
                    f"{i}. `{short}`\n"
                    f"   TXs: `{c['tx_count']}` | Gas: `{c['gas_spent']:,}`\n"
                    f"   Fn: `{c['top_function'][:30]}`"
                )
            self.send("\n".join(lines))
        except Exception as e:
            self.send(f"❌ Error: `{str(e)[:200]}`")

    def cmd_trend(self, args: list):
        if not self.analytics:
            self.send("⚠️ Gunakan `/analyze` atau `/use` dulu.")
            return

        self.send("📈 Menganalisis trend...")
        try:
            trend = self.analytics.trend_comparison()
            msg = f"""
📈 *TREND ANALYSIS*
━━━━━━━━━━━━━━━━━━━━━━
📊 Last 24h    : `{trend['txs_last_24h']:,}` TXs
📅 7d Average  : `{trend['avg_daily_7d']:,}` TXs/day
📉 Change      : `{trend['change_percent']}%`
🎯 Status      : {trend['trend']}
            """.strip()
            self.send(msg)
        except Exception as e:
            self.send(f"❌ Error: `{str(e)[:200]}`")

    def cmd_alert(self, args: list):
        if not args:
            status = "ON ✅" if self.alert_enabled else "OFF ❌"
            self.send(f"🔔 Auto alert sekarang: *{status}*\nGunakan `/alert on` atau `/alert off`")
            return

        action = args[0].lower()
        if action == "on":
            if not self.analytics:
                self.send("⚠️ Aktifkan dulu contract dengan `/analyze` atau `/use`.")
                return
            self.alert_enabled = True
            self._start_monitor_thread()
            self.send("✅ *Auto Alert ON*\nKamu akan mendapat notifikasi saat ada anomali.")
        elif action == "off":
            self.alert_enabled = False
            self.send("❌ *Auto Alert OFF*\nMonitoring dihentikan.")
        else:
            self.send("⚠️ Gunakan `/alert on` atau `/alert off`")

    def cmd_status(self, args: list):
        contract_str = f"`{self.active_contract}`" if self.active_contract else "❌ Belum dipilih"
        alert_str    = "✅ ON" if self.alert_enabled else "❌ OFF"
        msg = f"""
📡 *Bot Status*
━━━━━━━━━━━━━━━━━━━━━━
🏷️ Contract   : {contract_str}
🔔 Auto Alert : {alert_str}
⏰ Uptime     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """.strip()
        self.send(msg)

    # ─────────────────────────────────────────
    # BACKGROUND MONITOR (AUTO ALERT)
    # ─────────────────────────────────────────
    def _start_monitor_thread(self):
        if self.monitor_thread and self.monitor_thread.is_alive():
            return  # sudah jalan

        def monitor_loop():
            log.info("🔔 Background monitor started")
            while self.alert_enabled and self.running:
                try:
                    anomalies = self.analytics.detect_anomalies(days_back=1)
                    name = self.analytics.contract_info.get("ContractName", "Unknown")
                    for a in anomalies[:3]:
                        self.notifier.send_anomaly_alert(name, a)
                    if not anomalies:
                        log.info("✅ No anomalies detected")
                except Exception as e:
                    log.error(f"Monitor error: {e}")
                time.sleep(30 * 60)  # check setiap 30 menit

        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()

    # ─────────────────────────────────────────
    # MESSAGE ROUTER
    # ─────────────────────────────────────────
    def handle_message(self, message: dict):
        text = message.get("text", "").strip()
        if not text or not text.startswith("/"):
            return

        parts   = text.split()
        command = parts[0].lower().replace(f"@{self.token.split(':')[0]}", "")
        args    = parts[1:]

        log.info(f"📨 Command: {command} {args}")

        routes = {
            "/help"    : self.cmd_help,
            "/analyze" : self.cmd_analyze,
            "/preset"  : self.cmd_preset,
            "/use"     : self.cmd_use,
            "/report"  : self.cmd_report,
            "/top"     : self.cmd_top,
            "/trend"   : self.cmd_trend,
            "/alert"   : self.cmd_alert,
            "/status"  : self.cmd_status,
            "/start"   : self.cmd_help,
        }

        handler = routes.get(command)
        if handler:
            handler(args)
        else:
            self.send(f"❓ Command tidak dikenal: `{command}`\nKetik /help untuk bantuan.")

    # ─────────────────────────────────────────
    # MAIN POLLING LOOP
    # ─────────────────────────────────────────
    def run(self):
        log.info("🚀 Bot polling started...")
        self.send("🤖 *Contract Analytics Bot Online!*\nKetik /help untuk melihat commands.")

        while self.running:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.offset = update["update_id"] + 1
                    message = update.get("message", {})
                    if message:
                        self.handle_message(message)
            except KeyboardInterrupt:
                log.info("🛑 Bot stopped by user")
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