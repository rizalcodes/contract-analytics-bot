# 🔗 On-Chain Analytics — Web3 Python Toolkit

> Smart contract analytics engine with real-time Telegram alerts, multi-source data (Etherscan + The Graph + Web3.py), ABI decoding, and anomaly detection.

![Python](https://img.shields.io/badge/Python-3.12+-blue?style=flat-square&logo=python)
![Web3](https://img.shields.io/badge/Web3.py-6.x-orange?style=flat-square)
![Telegram](https://img.shields.io/badge/Telegram-Bot-26A5E4?style=flat-square&logo=telegram)
![Etherscan](https://img.shields.io/badge/Etherscan-V2_API-21325B?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 📦 Modules

| File | Description |
|------|-------------|
| `contract_analytics.py` | Core engine — usage patterns, anomaly detection, trend analysis |
| `analytics_bot.py` | Telegram bot with interactive commands |
| `graph_client.py` | The Graph / GraphQL client (Uniswap, Aave, Compound) |
| `abi_decoder.py` | Decode raw TX input data & event logs |
| `config.py` | Centralized API key & settings management |

---

## ✨ Features

- 📊 **Usage Pattern Analysis** — track which functions are called most, daily TX volume, unique callers
- 🚨 **Anomaly Detection** — auto-detect activity spikes using 2σ statistical rule
- 📈 **Trend Comparison** — compare 24h activity vs 7-day average
- 👤 **Top Caller Ranking** — see who interacts with a contract most
- 🤖 **Telegram Bot** — real-time alerts & interactive commands
- 🔍 **ABI Decoder** — decode ERC20, Uniswap V2 function calls & events
- 🌐 **Multi-Source** — Etherscan V2 API + The Graph + Web3.py RPC

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install web3 requests gql[requests] eth-abi eth-utils
```

### 2. Set environment variables

```powershell
# Windows PowerShell
$env:ETHERSCAN_API_KEY = "your_etherscan_api_key"
$env:INFURA_URL        = "https://mainnet.infura.io/v3/your_infura_key"
$env:TELEGRAM_TOKEN    = "your_telegram_bot_token"
$env:TELEGRAM_CHAT_ID  = "your_chat_id"
```

```bash
# Linux / Mac
export ETHERSCAN_API_KEY="your_etherscan_api_key"
export INFURA_URL="https://mainnet.infura.io/v3/your_infura_key"
export TELEGRAM_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

### 3. Verify config

```bash
python config.py
# Output: ✅ Semua config OK!
```

### 4. Run analytics (one-time)

```python
from contract_analytics import ContractAnalytics

analytics = ContractAnalytics("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D")
report    = analytics.full_report(days_back=7)
print(report)
```

### 5. Run Telegram bot

```bash
python analytics_bot.py
```

---

## 🤖 Telegram Bot Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/analyze <address>` | Analyze any contract address |
| `/preset` | List available preset contracts |
| `/use <name>` | Use a preset (uniswap_v2, uniswap_v3, aave_v3, compound) |
| `/report [days]` | Full analytics report (default: 7 days) |
| `/top [n]` | Top N callers (default: 10) |
| `/trend` | Compare 24h vs 7d trend |
| `/alert on/off` | Toggle real-time anomaly alerts |
| `/status` | Show current monitoring status |

### Example

```
/use uniswap_v2
/report 3
/top 5
/alert on
```

---

## 📊 Sample Output

```
📊 CONTRACT ANALYTICS REPORT
━━━━━━━━━━━━━━━━━━━━━━
🏷️ UniswapV2Router02
📍 0x7a250d5630...

📈 Activity (7d)
• Total TXs      : 10,000
• Unique Callers : 2,145
• Success Rate   : 96.54%
• Avg Gas Used   : 154,037

⚡ Trend (24h vs 7d avg)
• Last 24h   : 10,000 TXs
• 7d Average : 1,428 TXs/day
• Change     : +600% 📈 UP

🔝 Top Functions
• swapExactETHForTokensSupportingFeeOnTransferTokens → 3,066
• swapExactTokensForETHSupportingFeeOnTransferTokens → 2,153
• swapExactETHForTokens → 1,642
```

---

## 🗂️ Preset Contracts

| Name | Contract | Network |
|------|----------|---------|
| `uniswap_v2` | Uniswap V2 Router | Ethereum |
| `uniswap_v3` | Uniswap V3 Router | Ethereum |
| `aave_v3` | Aave V3 Pool | Ethereum |
| `compound` | Compound V2 | Ethereum |

---

## 🔧 API Keys

| Service | Get Key | Free Tier |
|---------|---------|-----------|
| Etherscan | [etherscan.io/apis](https://etherscan.io/apis) | 5 req/sec |
| Infura | [infura.io](https://infura.io) | 100K req/day |
| Telegram Bot | [@BotFather](https://t.me/BotFather) | Free |

---

## 📁 Project Structure

```
web3-python-toolkit/
├── on-chain-analytics/
│   ├── contract_analytics.py   # Core engine
│   ├── analytics_bot.py        # Telegram bot
│   ├── graph_client.py         # The Graph client
│   ├── abi_decoder.py          # ABI decoder
│   └── config.py               # Configuration
├── wallet_tracker.py
├── multi_wallet_tracker.py
├── etherscan_tracker.py
├── token_tracker.py
├── gas_tracker.py
├── nft_tracker.py
├── whale_alert.py
├── defi_tracker.py
├── price_alert.py
├── contract_reader.py
└── README.md
```

---

## 🛠️ Built With

- [Web3.py](https://web3py.readthedocs.io/) — Ethereum interaction
- [Etherscan API V2](https://docs.etherscan.io/) — On-chain data
- [The Graph](https://thegraph.com/) — Protocol subgraphs
- [python-telegram-bot](https://python-telegram-bot.org/) — Telegram integration
- [eth-abi](https://eth-abi.readthedocs.io/) — ABI encoding/decoding

---

## 👤 Author

**Rizal** — [@rizalcodes](https://github.com/rizalcodes)

> Building Web3 tools with Python 🐍⛓️

---

## 📄 License

MIT License — free to use, modify, and distribute.
