"""
graph_client.py - The Graph / GraphQL Client
Web3 Python Toolkit by Rizal
Query on-chain data dari Uniswap V3, Aave V3, Compound via subgraph
"""

import logging
import requests
from datetime import datetime, timedelta

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
# SUBGRAPH ENDPOINTS
# ─────────────────────────────────────────────
ENDPOINTS = {
    "uniswap_v2" : "https://api.studio.thegraph.com/query/48211/uniswap-v2/version/latest",
    "uniswap_v3" : "https://api.studio.thegraph.com/query/48211/uniswap-v3/version/latest",
    "aave_v3"    : "https://api.studio.thegraph.com/query/48211/aave-v3/version/latest",
    "compound"   : "https://api.studio.thegraph.com/query/48211/compound-v2/version/latest",
    "curve"      : "https://api.studio.thegraph.com/query/48211/curve/version/latest",
}


# ─────────────────────────────────────────────
# BASE GRAPH CLIENT
# ─────────────────────────────────────────────
class GraphClient:
    """Base client untuk query The Graph via plain HTTP (tanpa gql library)."""

    def __init__(self, protocol: str = "uniswap_v3"):
        if protocol not in ENDPOINTS:
            raise ValueError(f"Protocol '{protocol}' tidak tersedia. Pilih: {list(ENDPOINTS.keys())}")
        self.protocol = protocol
        self.endpoint = ENDPOINTS[protocol]
        self.session  = requests.Session()
        log.info(f"📡 GraphClient initialized — {protocol}")

    def query(self, gql_query: str, variables: dict = None) -> dict:
        """Kirim GraphQL query ke subgraph."""
        payload = {"query": gql_query}
        if variables:
            payload["variables"] = variables

        try:
            r = self.session.post(
                self.endpoint,
                json=payload,
                timeout=20,
                headers={"Content-Type": "application/json"}
            )
            r.raise_for_status()
            data = r.json()

            if "errors" in data:
                log.warning(f"GraphQL errors: {data['errors']}")
                return {}

            return data.get("data", {})

        except requests.exceptions.Timeout:
            log.error("GraphQL request timeout")
            return {}
        except Exception as e:
            log.error(f"GraphQL error: {e}")
            return {}

    def switch_protocol(self, protocol: str):
        """Ganti protocol/subgraph."""
        if protocol not in ENDPOINTS:
            log.error(f"Protocol '{protocol}' tidak tersedia.")
            return
        self.protocol = protocol
        self.endpoint = ENDPOINTS[protocol]
        log.info(f"🔄 Switched to {protocol}")


# ─────────────────────────────────────────────
# UNISWAP CLIENT
# ─────────────────────────────────────────────
class UniswapGraphClient(GraphClient):

    def __init__(self, version: str = "v3"):
        protocol = f"uniswap_{version}"
        super().__init__(protocol)

    # ── Pool Data ────────────────────────────
    def get_pool(self, pool_address: str) -> dict:
        """Ambil data lengkap satu pool."""
        q = """
        query($pool: String!) {
          pool(id: $pool) {
            id
            token0 { symbol name decimals }
            token1 { symbol name decimals }
            feeTier
            liquidity
            volumeUSD
            txCount
            totalValueLockedUSD
            poolDayData(first: 7, orderBy: date, orderDirection: desc) {
              date
              volumeUSD
              txCount
              feesUSD
              open
              close
            }
          }
        }
        """
        result = self.query(q, {"pool": pool_address.lower()})
        return result.get("pool", {})

    # ── Top Pools ────────────────────────────
    def get_top_pools(self, limit: int = 10) -> list:
        """Ambil top pools berdasarkan volume."""
        q = """
        query($limit: Int!) {
          pools(
            first: $limit,
            orderBy: volumeUSD,
            orderDirection: desc
          ) {
            id
            token0 { symbol }
            token1 { symbol }
            feeTier
            volumeUSD
            txCount
            totalValueLockedUSD
          }
        }
        """
        result = self.query(q, {"limit": limit})
        return result.get("pools", [])

    # ── Pool Swaps ───────────────────────────
    def get_pool_swaps(self, pool_address: str, limit: int = 50) -> list:
        """Ambil recent swaps dari sebuah pool."""
        q = """
        query($pool: String!, $limit: Int!) {
          swaps(
            first: $limit,
            orderBy: timestamp,
            orderDirection: desc,
            where: { pool: $pool }
          ) {
            id
            timestamp
            sender
            recipient
            amount0
            amount1
            amountUSD
            transaction { id }
          }
        }
        """
        result = self.query(q, {"pool": pool_address.lower(), "limit": limit})
        return result.get("swaps", [])

    # ── Token Data ───────────────────────────
    def get_token(self, token_address: str) -> dict:
        """Ambil data token dari Uniswap."""
        q = """
        query($token: String!) {
          token(id: $token) {
            id
            symbol
            name
            decimals
            volumeUSD
            txCount
            totalValueLockedUSD
            tokenDayData(first: 7, orderBy: date, orderDirection: desc) {
              date
              volumeUSD
              priceUSD
              open
              close
            }
          }
        }
        """
        result = self.query(q, {"token": token_address.lower()})
        return result.get("token", {})

    # ── Protocol Stats ───────────────────────
    def get_protocol_stats(self) -> dict:
        """Ambil statistik keseluruhan Uniswap."""
        q = """
        {
          factories(first: 1) {
            poolCount
            txCount
            totalVolumeUSD
            totalValueLockedUSD
          }
        }
        """
        result = self.query(q)
        factories = result.get("factories", [])
        return factories[0] if factories else {}

    # ── Pool Day Data ────────────────────────
    def get_pool_daily_stats(self, pool_address: str, days: int = 7) -> list:
        """Ambil statistik harian pool."""
        since = int((datetime.now() - timedelta(days=days)).timestamp())
        q = """
        query($pool: String!, $since: Int!) {
          poolDayDatas(
            orderBy: date,
            orderDirection: desc,
            where: { pool: $pool, date_gt: $since }
          ) {
            date
            volumeUSD
            txCount
            feesUSD
            tvlUSD
            open
            close
            high
            low
          }
        }
        """
        result = self.query(q, {"pool": pool_address.lower(), "since": since})
        return result.get("poolDayDatas", [])


# ─────────────────────────────────────────────
# AAVE CLIENT
# ─────────────────────────────────────────────
class AaveGraphClient(GraphClient):

    def __init__(self):
        super().__init__("aave_v3")

    def get_reserve(self, asset_address: str) -> dict:
        """Ambil data reserve/lending pool aset tertentu."""
        q = """
        query($asset: String!) {
          reserve(id: $asset) {
            id
            symbol
            name
            decimals
            totalLiquidity
            totalCurrentVariableDebt
            totalCurrentStableDebt
            liquidityRate
            variableBorrowRate
            stableBorrowRate
            utilizationRate
            availableLiquidity
            price { priceInEth }
          }
        }
        """
        result = self.query(q, {"asset": asset_address.lower()})
        return result.get("reserve", {})

    def get_top_reserves(self, limit: int = 10) -> list:
        """Ambil top reserves berdasarkan total liquidity."""
        q = """
        query($limit: Int!) {
          reserves(
            first: $limit,
            orderBy: totalLiquidity,
            orderDirection: desc
          ) {
            id
            symbol
            totalLiquidity
            totalCurrentVariableDebt
            utilizationRate
            liquidityRate
            variableBorrowRate
          }
        }
        """
        result = self.query(q, {"limit": limit})
        return result.get("reserves", [])

    def get_user_positions(self, user_address: str) -> dict:
        """Ambil posisi lending/borrowing user."""
        q = """
        query($user: String!) {
          user(id: $user) {
            id
            borrowedReservesCount
            collateralReserve: reserves(where: { currentATokenBalance_gt: "0" }) {
              reserve { symbol }
              currentATokenBalance
              currentTotalDebt
            }
          }
        }
        """
        result = self.query(q, {"user": user_address.lower()})
        return result.get("user", {})


# ─────────────────────────────────────────────
# COMPOUND CLIENT
# ─────────────────────────────────────────────
class CompoundGraphClient(GraphClient):

    def __init__(self):
        super().__init__("compound")

    def get_markets(self, limit: int = 10) -> list:
        """Ambil semua market Compound."""
        q = """
        query($limit: Int!) {
          markets(first: $limit, orderBy: totalSupplyUsd, orderDirection: desc) {
            id
            symbol
            name
            totalSupplyUsd
            totalBorrowsUsd
            supplyRate
            borrowRate
            utilizationRate
            underlyingAddress
            underlyingSymbol
          }
        }
        """
        result = self.query(q, {"limit": limit})
        return result.get("markets", [])


# ─────────────────────────────────────────────
# FORMATTER — untuk Telegram output
# ─────────────────────────────────────────────
class GraphFormatter:
    """Format data dari The Graph jadi pesan Telegram yang rapi."""

    @staticmethod
    def pool_summary(pool: dict) -> str:
        if not pool:
            return "❌ Pool tidak ditemukan"
        t0  = pool.get("token0", {}).get("symbol", "?")
        t1  = pool.get("token1", {}).get("symbol", "?")
        fee = int(pool.get("feeTier", 0)) / 10000
        vol = float(pool.get("volumeUSD", 0))
        tvl = float(pool.get("totalValueLockedUSD", 0))
        txs = pool.get("txCount", 0)

        return f"""
🏊 *Pool: {t0}/{t1} ({fee}%)*
━━━━━━━━━━━━━━━━━━━━━━
💰 Volume USD : `${vol:,.0f}`
🔒 TVL        : `${tvl:,.0f}`
📊 TX Count   : `{txs:,}`
        """.strip()

    @staticmethod
    def top_pools_summary(pools: list) -> str:
        if not pools:
            return "❌ Tidak ada data pool"
        lines = ["🏆 *Top Pools by Volume*\n━━━━━━━━━━━━━━━━━━━━━━"]
        for i, p in enumerate(pools, 1):
            t0  = p.get("token0", {}).get("symbol", "?")
            t1  = p.get("token1", {}).get("symbol", "?")
            vol = float(p.get("volumeUSD", 0))
            tvl = float(p.get("totalValueLockedUSD", 0))
            lines.append(f"{i}. *{t0}/{t1}*\n   Vol: `${vol:,.0f}` | TVL: `${tvl:,.0f}`")
        return "\n".join(lines)

    @staticmethod
    def protocol_stats_summary(stats: dict) -> str:
        if not stats:
            return "❌ Tidak ada data protokol"
        return f"""
📊 *Uniswap Protocol Stats*
━━━━━━━━━━━━━━━━━━━━━━
🏊 Total Pools  : `{int(stats.get('poolCount', 0)):,}`
📋 Total TXs    : `{int(stats.get('txCount', 0)):,}`
💰 Total Volume : `${float(stats.get('totalVolumeUSD', 0)):,.0f}`
🔒 Total TVL    : `${float(stats.get('totalValueLockedUSD', 0)):,.0f}`
        """.strip()

    @staticmethod
    def aave_reserve_summary(reserve: dict) -> str:
        if not reserve:
            return "❌ Reserve tidak ditemukan"
        util  = float(reserve.get("utilizationRate", 0)) * 100
        liq_r = float(reserve.get("liquidityRate", 0)) * 100
        bor_r = float(reserve.get("variableBorrowRate", 0)) * 100
        return f"""
🏦 *Aave Reserve: {reserve.get('symbol', '?')}*
━━━━━━━━━━━━━━━━━━━━━━
📈 Utilization  : `{util:.2f}%`
💵 Supply APY   : `{liq_r:.2f}%`
💸 Borrow APY   : `{bor_r:.2f}%`
        """.strip()


# ─────────────────────────────────────────────
# ENTRY POINT — test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 50)
    print("🧪 Testing GraphClient...")
    print("=" * 50)

    # Test Uniswap V3
    uni = UniswapGraphClient("v3")

    print("\n📊 Protocol Stats:")
    stats = uni.get_protocol_stats()
    print(GraphFormatter.protocol_stats_summary(stats))

    print("\n🏆 Top 5 Pools:")
    pools = uni.get_top_pools(limit=5)
    print(GraphFormatter.top_pools_summary(pools))

    # Test Aave
    print("\n🏦 Aave Top Reserves:")
    aave     = AaveGraphClient()
    reserves = aave.get_top_reserves(limit=5)
    for r in reserves:
        util = float(r.get("utilizationRate", 0)) * 100
        print(f"  {r.get('symbol','?'):8} | Util: {util:.1f}%")

    print("\n✅ GraphClient test selesai!")