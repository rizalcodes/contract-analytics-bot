# 🤖 Rizal Crypto Bot — All-in-One Web3 Analytics Bot

> The ultimate all-in-one crypto Telegram bot — monitor smart contracts, track portfolios, detect MEV, find DeFi yields, sniff tokens, track whales, NFT floors, gas prices, arbitrage opportunities, DAO governance & cross-chain bridges. All in one bot, powered by Python.

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram)
![Ethereum](https://img.shields.io/badge/Ethereum-Mainnet-627EEA?style=flat-square&logo=ethereum)
![Web3](https://img.shields.io/badge/Web3.py-Powered-F16822?style=flat-square)
![Etherscan](https://img.shields.io/badge/Etherscan-API-21325B?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🔍 What is This?

**Rizal Crypto Bot** is a production-ready, all-in-one Web3 analytics Telegram bot built entirely in Python. It consolidates 11 powerful DeFi modules into a single bot with subscription management, admin dashboard, and real-time background monitoring — all without any framework overhead.

This is the centerpiece of the **Web3 Python Toolkit** by [@rizalcodes](https://github.com/rizalcodes).

---

## ✨ Modules (11 Total)

| # | Module | Description |
|---|--------|-------------|
| 1 | 📊 **Contract Analytics** | Analyze any Ethereum smart contract — usage patterns, top callers, trend, anomaly detection |
| 2 | 💼 **Portfolio Tracker** | Full wallet portfolio — ETH balance, token holdings, NFT inventory with USD valuation |
| 3 | 🎯 **MEV Detector** | Scan blocks for sandwich attacks & arbitrage bots in real-time |
| 4 | 💰 **DeFi Yield Aggregator** | Best APY opportunities from Aave, Compound, Curve & Uniswap via DeFi Llama |
| 5 | 🔍 **Token Sniffer** | Full honeypot & rug pull safety analysis — buy/sell tax, LP lock, holder distribution |
| 6 | 🐋 **Whale Tracker** | Track whale wallets & get instant alerts on large on-chain moves |
| 7 | 🖼️ **NFT Floor Tracker** | OpenSea floor prices, sales volume, top collections & price change alerts |
| 8 | ⛽ **Gas Price Predictor** | Real-time gas prices with TX cost estimates & low/high gas alerts |
| 9 | 🔄 **Arbitrage Scanner** | Cross-DEX arbitrage opportunities across 6 DEXes with profit calculation |
| 10 | 🏛️ **DAO Governance Tracker** | Track proposals & voting across Uniswap, Aave, Compound, MakerDAO, Gitcoin |
| 11 | 🌉 **Cross-Chain Bridge Monitor** | Bridge token prices, routes & alerts via CoinGecko + LI.FI |

---

## 🚀 Quick Start

### 1. Clone the repo

    git clone https://github.com/rizalcodes/contract-analytics-bot.git
    cd contract-analytics-bot

### 2. Install dependencies

    pip install requests web3

### 3. Configure credentials

Open `analytic_bot.py` and set your keys:

    TELEGRAM_TOKEN    = "your_telegram_bot_token"
    ADMIN_CHAT_ID     = "your_telegram_chat_id"
    ETHERSCAN_API_KEY = "your_etherscan_api_key"
    INFURA_URL        = "https://mainnet.infura.io/v3/your_infura_key"
    OPENSEA_API_KEY   = "your_opensea_api_key"

### 4. Run the bot

    python analytic_bot.py

---

## 🤖 Telegram Commands (80+ Commands)

### 🆓 Free Commands
| Command | Description |
|---------|-------------|
| `/start` | Welcome & subscription status |
| `/plans` | View subscription plans |
| `/subscribe <plan>` | Subscribe (basic/pro/premium) |
| `/confirm <tx_hash>` | Confirm USDT payment |
| `/status` | Check your subscription |
| `/renew` | Renew current plan |

### 💼 Portfolio Tracker
| Command | Description |
|---------|-------------|
| `/track <address>` | Full portfolio analysis |
| `/watch <address>` | Add wallet to watchlist |
| `/watchlist` | View watchlist |
| `/unwatch <address>` | Remove from watchlist |
| `/refresh` | Refresh all watchlist wallets |

### 📊 Contract Analytics
| Command | Description |
|---------|-------------|
| `/analyze <address>` | Analyze smart contract |
| `/preset` | List preset contracts |
| `/use <name>` | Use preset contract |
| `/report [days]` | Full analytics report |
| `/top [n]` | Top N callers |
| `/trend` | 24h vs 7d trend |
| `/alert on/off` | Toggle anomaly alerts |

### 🎯 MEV Detector
| Command | Description |
|---------|-------------|
| `/mev [block]` | Scan block for MEV |
| `/mev_latest` | Scan latest block |
| `/mev_monitor on/off` | Auto monitor |
| `/mev_bots` | Known MEV bot list |

### 💰 DeFi Yield Aggregator
| Command | Description |
|---------|-------------|
| `/yield` | Best yield opportunities |
| `/yield_stable` | Stablecoin yields |
| `/yield_aave` | Aave V3 rates |
| `/yield_compound` | Compound rates |
| `/yield_curve` | Curve pools |
| `/yield_uni` | Uniswap V3 pools |
| `/yield_summary` | Market overview |
| `/yield_alert on/off` | APY spike alerts |

### 🔍 Token Sniffer
| Command | Description |
|---------|-------------|
| `/sniff <address>` | Full token safety analysis |
| `/quick <address>` | Quick honeypot check |

### 🐋 Whale Tracker
| Command | Description |
|---------|-------------|
| `/whale_add <address>` | Add wallet to track |
| `/whale_remove <address>` | Remove wallet |
| `/whale_list` | Show tracked wallets |
| `/whale_check <address>` | Manual wallet check |
| `/whale_monitor on/off` | Auto monitor |
| `/whale_whales` | Known whale addresses |
| `/whale_alert on/off` | Toggle alerts |

### 🖼️ NFT Floor Tracker
| Command | Description |
|---------|-------------|
| `/nft_floor <slug>` | Get floor price |
| `/nft_add <slug>` | Add collection |
| `/nft_remove <slug>` | Remove collection |
| `/nft_list` | Show tracked collections |
| `/nft_sales <slug>` | Recent sales |
| `/nft_top` | Top collections by volume |
| `/nft_search <name>` | Search collection |
| `/nft_monitor on/off` | Auto monitor |
| `/nft_known` | Known collection slugs |

### ⛽ Gas Price Predictor
| Command | Description |
|---------|-------------|
| `/gas` | Full gas report + TX estimates |
| `/gas_fast` | Quick gas check |
| `/gas_estimate [gwei]` | TX cost at custom Gwei |
| `/gas_trend` | Gas trend analysis |
| `/gas_history` | Session history |
| `/gas_monitor on/off` | Auto monitor |
| `/gas_threshold low/high <gwei>` | Set alert thresholds |

### 🔄 Arbitrage Scanner
| Command | Description |
|---------|-------------|
| `/arb_scan` | Scan all tokens across 6 DEXes |
| `/arb_token <symbol>` | Scan specific token |
| `/arb_top` | Top 5 opportunities |
| `/arb_pairs` | Tracked token pairs |
| `/arb_monitor on/off` | Auto monitor |
| `/arb_stats` | Scanner statistics |
| `/arb_settings` | Current configuration |

### 🏛️ DAO Governance Tracker
| Command | Description |
|---------|-------------|
| `/gov_proposals <dao>` | Active proposals |
| `/gov_proposal <id>` | Proposal detail + voters |
| `/gov_add <dao>` | Add DAO to watchlist |
| `/gov_remove <dao>` | Remove DAO |
| `/gov_list` | Watched DAOs |
| `/gov_summary <dao>` | DAO overview & stats |
| `/gov_daos` | All available DAOs |
| `/gov_monitor on/off` | Auto monitor |
| `/gov_top` | All active proposals by urgency |

### 🌉 Cross-Chain Bridge Monitor
| Command | Description |
|---------|-------------|
| `/bridge_info <bridge>` | Bridge token stats |
| `/bridge_add <bridge>` | Add to watchlist |
| `/bridge_remove <bridge>` | Remove from watchlist |
| `/bridge_list` | Watched bridges |
| `/bridge_tvl` | All bridges by market cap |
| `/bridge_route <from> <to>` | Available routes |
| `/bridge_monitor on/off` | Auto price monitor |
| `/bridge_bridges` | All available bridges |
| `/bridge_chains` | Supported chains |

### 👑 Admin Commands
| Command | Description |
|---------|-------------|
| `/admin_list` | All subscribers |
| `/admin_stats` | Revenue dashboard |
| `/admin_approve <chat_id>` | Approve payment |
| `/admin_reject <chat_id>` | Reject payment |
| `/admin_revoke <chat_id>` | Cancel subscription |
| `/admin_extend <chat_id> <days>` | Extend subscription |

---

## 💎 Subscription Plans

| Plan | Price | Contracts | Features |
|------|-------|-----------|----------|
| Basic | $10/mo | 1 | Contract monitoring, anomaly detection, 7d trend |
| Pro | $25/mo | 5 | All Basic + top callers, 24h vs 7d trend, priority support |
| Premium | $50/mo | Unlimited | All Pro + custom thresholds, ABI decoder, VIP support |

Payment via **USDT TRC20** — automated activation within 1 hour.

---

## 🏗️ Architecture

    analytic_bot.py (All-in-One)
    ├── SubscriberDB          → JSON-based subscription management
    ├── PriceClient           → CoinGecko price oracle
    ├── PortfolioAnalyzer     → ETH + token + NFT portfolio
    │   └── PortfolioEtherscan  → Etherscan v2 API
    ├── MEVAnalyzer           → Block-level MEV detection
    ├── YieldAggregator       → DeFi Llama yield pools
    ├── BridgeCoinGeckoClient → Bridge token price data
    ├── BridgeLiFiClient      → Bridge routes & connections
    ├── BridgeMonitorEngine   → Cross-chain bridge core
    └── AnalyticsBot          → Main bot (11 modules, 80+ commands)
        ├── _background()         → Subscription expiry checker
        ├── _mev_background()     → MEV block monitor
        ├── _whale_background()   → Whale move detector
        ├── _nft_background()     → NFT floor alert loop
        ├── _gas_background()     → Gas price alert loop
        ├── _arb_background()     → Arbitrage scan loop
        ├── _gov_background()     → Governance proposal monitor
        └── _bridge_background()  → Bridge token price monitor

    External modules (imported):
    ├── contract_analytics.py   → ContractAnalytics, TelegramNotifier
    ├── token_sniffer.py        → TokenAnalyzer
    ├── whale_wallet_copier.py  → WhaleTracker
    ├── nft_floor_tracker.py    → NFTFloorTracker
    ├── gas_price_predictor.py  → GasPredictor
    ├── arbitrage_scanner.py    → ArbitrageEngine
    └── dao_governance_tracker.py → GovernanceAnalyzer

---

## 📡 Data Sources

| Source | Used For | Auth |
|--------|----------|------|
| [Etherscan API v2](https://etherscan.io/apis) | Contract data, TX history, token balances | API Key |
| [Infura](https://infura.io) | Web3 RPC — ETH balance, block data | Project URL |
| [CoinGecko API](https://www.coingecko.com/api) | ETH & token prices, bridge token data | Free |
| [DeFi Llama Yields](https://yields.llama.fi) | APY & TVL data | Free |
| [OpenSea API](https://docs.opensea.io) | NFT floor prices & sales | API Key |
| [Snapshot GraphQL](https://docs.snapshot.org) | Off-chain governance proposals | Free |
| [LI.FI API](https://docs.li.fi) | Bridge routes & connections | Free |

---

## 🔧 Requirements

    pip install requests web3

Optional (for full module support):

    pip install python-telegram-bot  # if using async version

---

## ⚙️ Configuration

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | BotFather token |
| `ADMIN_CHAT_ID` | Your Telegram chat ID |
| `ETHERSCAN_API_KEY` | Etherscan API key |
| `INFURA_URL` | Infura mainnet endpoint |
| `OPENSEA_API_KEY` | OpenSea API key |
| `USDT_TRC20` | Your USDT payment address |

---

## 🚨 Background Monitors

The bot runs 8 parallel background threads:

| Thread | Interval | Function |
|--------|----------|----------|
| Subscription checker | 1 hour | Expire & notify expiring subs |
| MEV monitor | 12 sec | Scan new blocks for MEV |
| Whale monitor | 15 sec | Detect large wallet moves |
| NFT monitor | 5 min | Floor price change alerts |
| Gas monitor | 60 sec | Low/high gas alerts |
| Arbitrage monitor | 2 min | Scan DEX price gaps |
| Governance monitor | 5 min | New proposal & deadline alerts |
| Bridge monitor | 5 min | Bridge token price alerts |

---

## ⚠️ Disclaimer

> **This bot is for informational and educational purposes only. Nothing here constitutes financial advice. Always do your own research before making any DeFi or investment decisions.**

---

## 👤 Author

**Rizal** — [@rizalcodes](https://github.com/rizalcodes)

> Building Web3 tools with Python 🐍⛓️
> Follow on X: [@ClipXDaily](https://x.com/ClipXDaily)

---

## 📄 License

MIT License — free to use, modify, and distribute.
