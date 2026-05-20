"""
contract_analytics.py - Smart Contract Analytics Core Engine
Web3 Python Toolkit by Rizal
Multi-source: Etherscan API + The Graph/GraphQL + Web3.py RPC
"""

import os
import time
import json
import asyncio
import logging
import requests
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from web3 import Web3
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

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
# CONFIG (ganti dengan API key kamu)
# ─────────────────────────────────────────────
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "Your_Etherscan_Api_Here")
INFURA_URL        = os.getenv("INFURA_URL",        "https://mainnet.infura.io/v3/Your_Infure_Key_Here")
TELEGRAM_TOKEN    = os.getenv("TELEGRAM_TOKEN",    "Your_Telegram_Bot_Token_Here")
TELEGRAM_CHAT_ID  = os.getenv("TELEGRAM_CHAT_ID",  "Your_Chat_ID_Here")

# The Graph — subgraph endpoints (contoh Uniswap V3)
GRAPH_ENDPOINTS = {
    "uniswap_v3" : "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
    "aave_v3"    : "https://api.thegraph.com/subgraphs/name/aave/protocol-v3",
    "compound"   : "https://api.thegraph.com/subgraphs/name/graphprotocol/compound-v2",
}


# ─────────────────────────────────────────────
# 1. ETHERSCAN CLIENT
# ─────────────────────────────────────────────
class EtherscanClient:
    BASE = "https://api.etherscan.io/v2/api"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def _get(self, params: dict) -> dict:
        params["apikey"] = self.api_key
        params["chainid"] = 1  # Ethereum mainnet
        try:
            r = self.session.get(self.BASE, params=params, timeout=15)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "0" and data.get("message") != "No transactions found":
                log.warning(f"Etherscan warning: {data.get('result')}")
            return data
        except Exception as e:
            log.error(f"Etherscan error: {e}")
            return {}

    def get_contract_txs(self, address: str, days_back: int = 7) -> list:
        """Ambil semua transaksi ke contract dalam N hari terakhir."""
        start_ts = int((datetime.now() - timedelta(days=days_back)).timestamp())
        data = self._get({
            "module"    : "account",
            "action"    : "txlist",
            "address"   : address,
            "startblock": self._ts_to_block(start_ts),
            "endblock"  : "latest",
            "sort"      : "desc",
        })
        return data.get("result", []) if isinstance(data.get("result"), list) else []

    def get_contract_events(self, address: str, topic0: str = None, days_back: int = 1) -> list:
        """Ambil event logs dari contract."""
        params = {
            "module" : "logs",
            "action" : "getLogs",
            "address": address,
            "fromBlock": "latest",
            "toBlock"  : "latest",
        }
        if topic0:
            params["topic0"] = topic0
        data = self._get(params)
        return data.get("result", []) if isinstance(data.get("result"), list) else []

    def get_contract_abi(self, address: str) -> list:
        """Ambil ABI contract yang verified."""
        data = self._get({
            "module" : "contract",
            "action" : "getabi",
            "address": address,
        })
        result = data.get("result", "[]")
        try:
            return json.loads(result)
        except Exception:
            return []

    def get_contract_info(self, address: str) -> dict:
        """Info dasar contract (name, compiler, dll)."""
        data = self._get({
            "module" : "contract",
            "action" : "getsourcecode",
            "address": address,
        })
        result = data.get("result", [])
        # Etherscan kadang return string error bukan list
        if isinstance(result, list) and len(result) > 0 and isinstance(result[0], dict):
            return result[0]
        return {}

    def _ts_to_block(self, timestamp: int) -> int:
        """Konversi timestamp ke block number via Etherscan."""
        data = self._get({
            "module"   : "block",
            "action"   : "getblocknobytime",
            "timestamp": timestamp,
            "closest"  : "before",
        })
        try:
            return int(data.get("result", 0))
        except Exception:
            return 0


# ─────────────────────────────────────────────
# 2. THE GRAPH CLIENT
# ─────────────────────────────────────────────
class GraphClient:
    def __init__(self, endpoint: str):
        transport = RequestsHTTPTransport(url=endpoint, verify=True, retries=3)
        self.client = Client(transport=transport, fetch_schema_from_transport=False)

    def query(self, gql_query: str, variables: dict = None) -> dict:
        try:
            result = self.client.execute(gql(gql_query), variable_values=variables or {})
            return result
        except Exception as e:
            log.error(f"GraphQL error: {e}")
            return {}

    def get_uniswap_pool_data(self, pool_address: str) -> dict:
        q = """
        query($pool: String!) {
          pool(id: $pool) {
            token0 { symbol decimals }
            token1 { symbol decimals }
            feeTier
            liquidity
            volumeUSD
            txCount
            poolDayData(first: 7, orderBy: date, orderDirection: desc) {
              date volumeUSD txCount feesUSD
            }
          }
        }
        """
        return self.query(q, {"pool": pool_address.lower()})

    def get_aave_reserve_data(self, asset_address: str) -> dict:
        q = """
        query($asset: String!) {
          reserve(id: $asset) {
            symbol
            totalLiquidity
            totalCurrentVariableDebt
            liquidityRate
            variableBorrowRate
            utilizationRate
          }
        }
        """
        return self.query(q, {"asset": asset_address.lower()})


# ─────────────────────────────────────────────
# 3. WEB3 RPC CLIENT
# ─────────────────────────────────────────────
class Web3Client:
    def __init__(self, rpc_url: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if self.w3.is_connected():
            log.info(f"✅ Web3 connected — block #{self.w3.eth.block_number}")
        else:
            log.warning("⚠️  Web3 tidak terkoneksi, cek INFURA_URL")

    def get_contract(self, address: str, abi: list):
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(address),
            abi=abi
        )

    def call_function(self, contract, func_name: str, *args):
        """Panggil read function dari contract."""
        try:
            fn = getattr(contract.functions, func_name)
            return fn(*args).call()
        except Exception as e:
            log.error(f"Contract call error ({func_name}): {e}")
            return None

    def decode_input(self, contract, tx_input: str) -> dict:
        """Decode raw transaction input data."""
        try:
            fn, params = contract.decode_function_input(tx_input)
            return {
                "function": fn.fn_name,
                "params"  : {k: str(v) for k, v in params.items()}
            }
        except Exception:
            return {"function": "unknown", "params": {}}

    def get_current_block(self) -> int:
        return self.w3.eth.block_number


# ─────────────────────────────────────────────
# 4. ABI DECODER
# ─────────────────────────────────────────────
class AbiDecoder:
    """Decode function calls dan events dari raw tx data."""

    def __init__(self, abi: list):
        self.abi = abi
        self.func_map   = {}   # selector → name
        self.event_map  = {}   # topic0   → name
        self._build_maps()

    def _build_maps(self):
        from eth_abi import decode
        from eth_utils import keccak, function_signature_to_4byte_selector, event_abi_to_log_topic

        for item in self.abi:
            if item.get("type") == "function":
                try:
                    inputs = ",".join(i["type"] for i in item.get("inputs", []))
                    sig    = f"{item['name']}({inputs})"
                    sel    = function_signature_to_4byte_selector(sig).hex()
                    self.func_map[sel] = item["name"]
                except Exception:
                    pass
            elif item.get("type") == "event":
                try:
                    topic = event_abi_to_log_topic(item).hex()
                    self.event_map[topic] = item["name"]
                except Exception:
                    pass

    def decode_tx(self, input_data: str) -> str:
        """Return nama fungsi dari input data."""
        if not input_data or input_data == "0x":
            return "ETH Transfer"
        selector = input_data[2:10]
        return self.func_map.get(selector, f"unknown(0x{selector})")

    def decode_event(self, topic0: str) -> str:
        """Return nama event dari topic0."""
        topic = topic0.replace("0x", "")
        return self.event_map.get(topic, f"unknown({topic[:8]})")


# ─────────────────────────────────────────────
# 5. ANALYTICS ENGINE (CORE)
# ─────────────────────────────────────────────
class ContractAnalytics:
    def __init__(self, contract_address: str):
        self.address   = Web3.to_checksum_address(contract_address)
        self.etherscan = EtherscanClient(ETHERSCAN_API_KEY)
        self.web3      = Web3Client(INFURA_URL)

        # Load ABI & init decoder
        self.abi     = self.etherscan.get_contract_abi(self.address)
        self.decoder = AbiDecoder(self.abi) if self.abi else None
        self.contract_info = self.etherscan.get_contract_info(self.address)

        log.info(f"📋 Contract: {self.contract_info.get('ContractName', 'Unknown')} ({self.address})")

    # ── 5a. Usage Pattern Analysis ──────────────────
    def analyze_usage(self, days_back: int = 7) -> dict:
        """Analisis pola penggunaan contract dalam N hari."""
        log.info(f"🔍 Analyzing usage for last {days_back} days...")
        txs = self.etherscan.get_contract_txs(self.address, days_back)

        if not txs:
            return {"error": "No transactions found"}

        func_counter  = Counter()
        caller_set    = set()
        daily_volume  = defaultdict(int)
        failed_txs    = 0
        total_gas     = 0

        for tx in txs:
            # Function call distribution
            func_name = self.decoder.decode_tx(tx.get("input", "0x")) if self.decoder else "unknown"
            func_counter[func_name] += 1

            # Unique callers
            caller_set.add(tx.get("from", "").lower())

            # Daily tx volume
            ts   = int(tx.get("timeStamp", 0))
            date = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            daily_volume[date] += 1

            # Failed txs
            if tx.get("isError") == "1":
                failed_txs += 1

            # Gas usage
            total_gas += int(tx.get("gasUsed", 0))

        return {
            "contract"       : self.address,
            "contract_name"  : self.contract_info.get("ContractName", "Unknown"),
            "period_days"    : days_back,
            "total_txs"      : len(txs),
            "unique_callers" : len(caller_set),
            "failed_txs"     : failed_txs,
            "success_rate"   : round((1 - failed_txs / len(txs)) * 100, 2),
            "avg_gas_used"   : total_gas // len(txs) if txs else 0,
            "top_functions"  : func_counter.most_common(10),
            "daily_volume"   : dict(sorted(daily_volume.items())),
        }

    # ── 5b. Anomaly Detection ────────────────────────
    def detect_anomalies(self, days_back: int = 7) -> list:
        """Deteksi spike aktivitas & pola tidak normal."""
        log.info("🚨 Detecting anomalies...")
        txs = self.etherscan.get_contract_txs(self.address, days_back)

        if not txs:
            return []

        # Hitung tx per jam
        hourly = defaultdict(int)
        for tx in txs:
            ts   = int(tx.get("timeStamp", 0))
            hour = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:00")
            hourly[hour] += 1

        if not hourly:
            return []

        values  = list(hourly.values())
        avg     = sum(values) / len(values)
        std_dev = (sum((v - avg) ** 2 for v in values) / len(values)) ** 0.5
        threshold = avg + (2 * std_dev)  # 2σ rule

        anomalies = []
        for hour, count in hourly.items():
            if count > threshold:
                anomalies.append({
                    "hour"      : hour,
                    "tx_count"  : count,
                    "avg_normal": round(avg, 2),
                    "severity"  : "HIGH" if count > avg * 3 else "MEDIUM",
                })

        return sorted(anomalies, key=lambda x: x["tx_count"], reverse=True)

    # ── 5c. Top Caller Analysis ──────────────────────
    def top_callers(self, days_back: int = 7, top_n: int = 10) -> list:
        """Siapa yang paling sering interact dengan contract."""
        log.info("👤 Analyzing top callers...")
        txs = self.etherscan.get_contract_txs(self.address, days_back)

        caller_data = defaultdict(lambda: {"count": 0, "gas_total": 0, "functions": Counter()})

        for tx in txs:
            caller  = tx.get("from", "").lower()
            func    = self.decoder.decode_tx(tx.get("input", "0x")) if self.decoder else "unknown"
            gas     = int(tx.get("gasUsed", 0))

            caller_data[caller]["count"]     += 1
            caller_data[caller]["gas_total"] += gas
            caller_data[caller]["functions"][func] += 1

        result = []
        for addr, data in caller_data.items():
            result.append({
                "address"       : addr,
                "tx_count"      : data["count"],
                "gas_spent"     : data["gas_total"],
                "top_function"  : data["functions"].most_common(1)[0][0] if data["functions"] else "N/A",
            })

        return sorted(result, key=lambda x: x["tx_count"], reverse=True)[:top_n]

    # ── 5d. Trend Comparison ─────────────────────────
    def trend_comparison(self) -> dict:
        """Bandingkan aktivitas 24h terakhir vs 7 hari sebelumnya."""
        log.info("📈 Comparing trends...")
        txs_24h = self.etherscan.get_contract_txs(self.address, days_back=1)
        txs_7d  = self.etherscan.get_contract_txs(self.address, days_back=7)

        avg_7d = len(txs_7d) / 7 if txs_7d else 0
        change = ((len(txs_24h) - avg_7d) / avg_7d * 100) if avg_7d > 0 else 0

        return {
            "txs_last_24h"     : len(txs_24h),
            "avg_daily_7d"     : round(avg_7d, 1),
            "change_percent"   : round(change, 2),
            "trend"            : "📈 UP" if change > 10 else ("📉 DOWN" if change < -10 else "➡️ STABLE"),
        }

    # ── 5e. Full Report ──────────────────────────────
    def full_report(self, days_back: int = 7) -> dict:
        """Generate full analytics report."""
        log.info("📊 Generating full report...")
        return {
            "timestamp"  : datetime.now().isoformat(),
            "usage"      : self.analyze_usage(days_back),
            "anomalies"  : self.detect_anomalies(days_back),
            "top_callers": self.top_callers(days_back),
            "trend"      : self.trend_comparison(),
        }


# ─────────────────────────────────────────────
# 6. TELEGRAM NOTIFIER
# ─────────────────────────────────────────────
class TelegramNotifier:
    def __init__(self, token: str, chat_id: str):
        self.token   = token
        self.chat_id = chat_id
        self.base    = f"https://api.telegram.org/bot{token}"

    def send(self, message: str):
        try:
            r = requests.post(
                f"{self.base}/sendMessage",
                json={"chat_id": self.chat_id, "text": message, "parse_mode": "Markdown"},
                timeout=10
            )
            if r.status_code == 200:
                log.info("✅ Telegram message sent")
            else:
                log.warning(f"Telegram error: {r.text}")
        except Exception as e:
            log.error(f"Telegram send failed: {e}")

    def send_usage_report(self, report: dict):
        usage  = report.get("usage", {})
        trend  = report.get("trend", {})
        anomaly_count = len(report.get("anomalies", []))

        msg = f"""
📊 *CONTRACT ANALYTICS REPORT*
━━━━━━━━━━━━━━━━━━━━━━
🏷️ *{usage.get('contract_name', 'Unknown')}*
📍 `{usage.get('contract', '')[:20]}...`

📈 *Activity ({usage.get('period_days', 7)}d)*
• Total TXs     : `{usage.get('total_txs', 0):,}`
• Unique Callers: `{usage.get('unique_callers', 0):,}`
• Success Rate  : `{usage.get('success_rate', 0)}%`
• Avg Gas Used  : `{usage.get('avg_gas_used', 0):,}`

⚡ *Trend (24h vs 7d avg)*
• Last 24h  : `{trend.get('txs_last_24h', 0):,}` TXs
• 7d Average: `{trend.get('avg_daily_7d', 0):,}` TXs/day
• Change    : `{trend.get('change_percent', 0)}%` {trend.get('trend', '')}

🚨 *Anomalies Detected*: `{anomaly_count}`

⏰ {report.get('timestamp', '')[:19]}
        """.strip()

        self.send(msg)

    def send_anomaly_alert(self, contract_name: str, anomaly: dict):
        sev_emoji = "🔴" if anomaly["severity"] == "HIGH" else "🟡"
        msg = f"""
{sev_emoji} *ANOMALY ALERT — {contract_name}*
━━━━━━━━━━━━━━━━━━━━━━
🕐 Hour     : `{anomaly['hour']}`
📊 TXs      : `{anomaly['tx_count']}` (avg: {anomaly['avg_normal']})
⚠️ Severity : `{anomaly['severity']}`
        """.strip()
        self.send(msg)


# ─────────────────────────────────────────────
# 7. MAIN MONITOR LOOP
# ─────────────────────────────────────────────
def monitor(contract_address: str, interval_minutes: int = 30):
    """
    Loop utama: jalankan analytics setiap N menit,
    kirim report & anomaly alert ke Telegram.
    """
    analytics = ContractAnalytics(contract_address)
    notifier  = TelegramNotifier(TELEGRAM_TOKEN, 1024188205)

    log.info(f"🚀 Monitoring started — interval: {interval_minutes} min")
    notifier.send(f"🚀 *Contract Analytics Started*\n📍 `{contract_address}`\n⏱️ Interval: {interval_minutes} min")

    while True:
        try:
            report = analytics.full_report(days_back=7)

            # Kirim report ke Telegram
            notifier.send_usage_report(report)

            # Kirim anomaly alert jika ada
            anomalies = report.get("anomalies", [])
            contract_name = report.get("usage", {}).get("contract_name", "Unknown")
            for anomaly in anomalies[:3]:  # max 3 alert per cycle
                notifier.send_anomaly_alert(contract_name, anomaly)

            # Print top functions ke console
            top_funcs = report.get("usage", {}).get("top_functions", [])
            if top_funcs:
                log.info("🔝 Top Functions:")
                for fn, count in top_funcs[:5]:
                    log.info(f"   {fn}: {count} calls")

        except Exception as e:
            log.error(f"Monitor error: {e}")
            notifier.send(f"⚠️ *Monitor Error*\n`{str(e)[:200]}`")

        log.info(f"⏳ Next check in {interval_minutes} minutes...")
        time.sleep(interval_minutes * 60)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    # Contoh: monitor Uniswap V3 Router
    TARGET_CONTRACT = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"

    # Jalankan sekali untuk test
    analytics = ContractAnalytics(TARGET_CONTRACT)
    report    = analytics.full_report(days_back=7)

    print(json.dumps(report, indent=2, default=str))

    # Uncomment untuk mode monitoring loop:
    # monitor(TARGET_CONTRACT, interval_minutes=30)
