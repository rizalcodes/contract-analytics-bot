"""
abi_decoder.py - Smart Contract ABI Decoder
Web3 Python Toolkit by Rizal
Decode function calls & events dari raw transaction data
"""

import json
import logging
import requests
from web3 import Web3
from eth_utils import (
    function_signature_to_4byte_selector,
    event_abi_to_log_topic,
    to_hex,
)
from eth_abi import decode as abi_decode

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
# COMMON ABI FRAGMENTS
# Fungsi & event umum yang sering muncul di kontrak ERC20/DeFi
# ─────────────────────────────────────────────
ERC20_ABI = [
    {"type":"function","name":"transfer","inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"type":"bool"}]},
    {"type":"function","name":"transferFrom","inputs":[{"name":"from","type":"address"},{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"type":"bool"}]},
    {"type":"function","name":"approve","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"type":"bool"}]},
    {"type":"function","name":"balanceOf","inputs":[{"name":"account","type":"address"}],"outputs":[{"type":"uint256"}]},
    {"type":"function","name":"allowance","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"type":"uint256"}]},
    {"type":"event","name":"Transfer","inputs":[{"name":"from","type":"address","indexed":True},{"name":"to","type":"address","indexed":True},{"name":"value","type":"uint256","indexed":False}]},
    {"type":"event","name":"Approval","inputs":[{"name":"owner","type":"address","indexed":True},{"name":"spender","type":"address","indexed":True},{"name":"value","type":"uint256","indexed":False}]},
]

UNISWAP_V2_ABI = [
    {"type":"function","name":"swapExactTokensForTokens","inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}]},
    {"type":"function","name":"swapExactETHForTokens","inputs":[{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}]},
    {"type":"function","name":"swapExactTokensForETH","inputs":[{"name":"amountIn","type":"uint256"},{"name":"amountOutMin","type":"uint256"},{"name":"path","type":"address[]"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}]},
    {"type":"function","name":"addLiquidity","inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"amountADesired","type":"uint256"},{"name":"amountBDesired","type":"uint256"},{"name":"amountAMin","type":"uint256"},{"name":"amountBMin","type":"uint256"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}]},
    {"type":"function","name":"removeLiquidity","inputs":[{"name":"tokenA","type":"address"},{"name":"tokenB","type":"address"},{"name":"liquidity","type":"uint256"},{"name":"amountAMin","type":"uint256"},{"name":"amountBMin","type":"uint256"},{"name":"to","type":"address"},{"name":"deadline","type":"uint256"}]},
    {"type":"event","name":"Swap","inputs":[{"name":"sender","type":"address","indexed":True},{"name":"amount0In","type":"uint256","indexed":False},{"name":"amount1In","type":"uint256","indexed":False},{"name":"amount0Out","type":"uint256","indexed":False},{"name":"amount1Out","type":"uint256","indexed":False},{"name":"to","type":"address","indexed":True}]},
]


# ─────────────────────────────────────────────
# ABI DECODER CLASS
# ─────────────────────────────────────────────
class AbiDecoder:
    """
    Decode raw transaction input data & event logs
    menggunakan ABI dari Etherscan atau manual input.
    """

    def __init__(self, abi: list = None):
        self.func_map  = {}  # selector (4 bytes hex) → {name, inputs}
        self.event_map = {}  # topic0 (32 bytes hex)  → {name, inputs}

        # Load default ABI fragments
        self._load_abi(ERC20_ABI)
        self._load_abi(UNISWAP_V2_ABI)

        # Load custom ABI jika ada
        if abi:
            self._load_abi(abi)

        log.info(f"✅ AbiDecoder ready — {len(self.func_map)} functions, {len(self.event_map)} events")

    def _load_abi(self, abi: list):
        """Parse ABI dan build lookup maps."""
        for item in abi:
            try:
                if item.get("type") == "function":
                    inputs   = ",".join(i["type"] for i in item.get("inputs", []))
                    sig      = f"{item['name']}({inputs})"
                    selector = function_signature_to_4byte_selector(sig).hex()
                    self.func_map[selector] = {
                        "name"   : item["name"],
                        "inputs" : item.get("inputs", []),
                        "sig"    : sig,
                    }

                elif item.get("type") == "event":
                    topic = event_abi_to_log_topic(item).hex()
                    self.event_map[topic] = {
                        "name"   : item["name"],
                        "inputs" : item.get("inputs", []),
                    }
            except Exception as e:
                log.debug(f"ABI parse skip: {e}")

    def load_from_etherscan(self, address: str, api_key: str) -> bool:
        """Fetch & load ABI langsung dari Etherscan."""
        try:
            r = requests.get(
                "https://api.etherscan.io/v2/api",
                params={
                    "module" : "contract",
                    "action" : "getabi",
                    "address": address,
                    "chainid": 1,
                    "apikey" : api_key,
                },
                timeout=15
            )
            data   = r.json()
            result = data.get("result", "[]")
            abi    = json.loads(result)
            if isinstance(abi, list):
                self._load_abi(abi)
                log.info(f"✅ Loaded ABI from Etherscan for {address[:10]}...")
                return True
        except Exception as e:
            log.error(f"Failed to load ABI from Etherscan: {e}")
        return False

    # ─────────────────────────────────────────
    # DECODE FUNCTION CALL
    # ─────────────────────────────────────────
    def decode_input(self, input_data: str) -> dict:
        """
        Decode raw transaction input data.
        Return: {function, selector, params, signature}
        """
        if not input_data or input_data in ("0x", ""):
            return {
                "function" : "ETH Transfer",
                "selector" : None,
                "params"   : {},
                "signature": None,
            }

        # Ambil 4 byte selector
        raw      = input_data.replace("0x", "")
        selector = raw[:8].lower()
        calldata = raw[8:]

        if selector not in self.func_map:
            return {
                "function" : f"unknown",
                "selector" : f"0x{selector}",
                "params"   : {},
                "signature": None,
            }

        fn = self.func_map[selector]

        # Decode params
        params = {}
        try:
            types  = [i["type"] for i in fn["inputs"]]
            names  = [i["name"] for i in fn["inputs"]]
            values = abi_decode(types, bytes.fromhex(calldata))
            for name, val in zip(names, values):
                params[name] = self._format_value(val)
        except Exception as e:
            log.debug(f"Param decode error: {e}")

        return {
            "function" : fn["name"],
            "selector" : f"0x{selector}",
            "params"   : params,
            "signature": fn["sig"],
        }

    # ─────────────────────────────────────────
    # DECODE EVENT LOG
    # ─────────────────────────────────────────
    def decode_log(self, log_entry: dict) -> dict:
        """
        Decode event log dari transaction receipt.
        log_entry: {topics: [...], data: "0x..."}
        Return: {event, params}
        """
        topics = log_entry.get("topics", [])
        if not topics:
            return {"event": "unknown", "params": {}}

        topic0 = topics[0].replace("0x", "").lower()

        if topic0 not in self.event_map:
            return {
                "event" : f"unknown",
                "topic0": f"0x{topic0}",
                "params": {},
            }

        ev = self.event_map[topic0]

        # Pisahkan indexed vs non-indexed inputs
        indexed     = [i for i in ev["inputs"] if i.get("indexed")]
        non_indexed = [i for i in ev["inputs"] if not i.get("indexed")]

        params = {}

        # Decode indexed params dari topics[1:]
        try:
            for i, inp in enumerate(indexed):
                if i + 1 < len(topics):
                    raw = bytes.fromhex(topics[i + 1].replace("0x", ""))
                    val = abi_decode([inp["type"]], raw)[0]
                    params[inp["name"]] = self._format_value(val)
        except Exception as e:
            log.debug(f"Indexed decode error: {e}")

        # Decode non-indexed params dari data
        try:
            data = log_entry.get("data", "0x").replace("0x", "")
            if data and non_indexed:
                types  = [i["type"] for i in non_indexed]
                names  = [i["name"] for i in non_indexed]
                values = abi_decode(types, bytes.fromhex(data))
                for name, val in zip(names, values):
                    params[name] = self._format_value(val)
        except Exception as e:
            log.debug(f"Non-indexed decode error: {e}")

        return {
            "event" : ev["name"],
            "topic0": f"0x{topic0[:8]}...",
            "params": params,
        }

    # ─────────────────────────────────────────
    # BATCH DECODE
    # ─────────────────────────────────────────
    def decode_transactions(self, txs: list) -> list:
        """Decode list of transactions sekaligus."""
        results = []
        for tx in txs:
            decoded = self.decode_input(tx.get("input", "0x"))
            results.append({
                "hash"     : tx.get("hash", ""),
                "from"     : tx.get("from", ""),
                "to"       : tx.get("to", ""),
                "value"    : tx.get("value", "0"),
                "function" : decoded["function"],
                "params"   : decoded["params"],
                "gas_used" : tx.get("gasUsed", 0),
                "timestamp": tx.get("timeStamp", 0),
            })
        return results

    def function_frequency(self, txs: list) -> dict:
        """Hitung frekuensi tiap function call dari list txs."""
        from collections import Counter
        decoded = self.decode_transactions(txs)
        counter = Counter(d["function"] for d in decoded)
        return dict(counter.most_common())

    # ─────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────
    def _format_value(self, val) -> str:
        """Format decoded value jadi string yang readable."""
        if isinstance(val, bytes):
            return val.hex()
        if isinstance(val, (list, tuple)):
            return [self._format_value(v) for v in val]
        return str(val)

    def get_function_name(self, input_data: str) -> str:
        """Shortcut — return hanya nama function."""
        return self.decode_input(input_data)["function"]

    def get_event_name(self, topic0: str) -> str:
        """Shortcut — return hanya nama event."""
        topic = topic0.replace("0x", "").lower()
        ev    = self.event_map.get(topic)
        return ev["name"] if ev else f"unknown(0x{topic[:8]})"

    def list_functions(self) -> list:
        """List semua function yang dikenal decoder."""
        return [v["sig"] for v in self.func_map.values()]

    def list_events(self) -> list:
        """List semua event yang dikenal decoder."""
        return [v["name"] for v in self.event_map.values()]


# ─────────────────────────────────────────────
# ENTRY POINT — test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Testing AbiDecoder...")
    print("=" * 50)

    decoder = AbiDecoder()

    print(f"\n📋 Known functions ({len(decoder.func_map)}):")
    for sig in decoder.list_functions():
        print(f"   {sig}")

    print(f"\n📋 Known events ({len(decoder.event_map)}):")
    for ev in decoder.list_events():
        print(f"   {ev}")

    # Test decode ERC20 transfer
    print("\n🔍 Test decode ERC20 transfer:")
    # transfer(address,uint256) — contoh input data
    test_input = "0xa9059cbb" \
                 "000000000000000000000000ab5801a7d398351b8be11c439e05c5b3259aec9" \
                 "0000000000000000000000000000000000000000000000000de0b6b3a7640000"

    result = decoder.decode_input(test_input)
    print(f"   Function : {result['function']}")
    print(f"   Signature: {result['signature']}")
    for k, v in result["params"].items():
        print(f"   {k}: {v}")

    # Test decode Uniswap swap event
    print("\n🔍 Test get function name:")
    print(f"   {decoder.get_function_name(test_input)}")

    print("\n✅ AbiDecoder test selesai!")