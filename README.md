Real-Time Market Discrepancy & Arbitrage Engine

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Architecture](https://img.shields.io/badge/Architecture-Event--Driven-success)
![Focus](https://img.shields.io/badge/Domain-Quantitative%20Finance%20%2F%20Arbitrage-orange)
![License](https://img.shields.io/badge/License-Proprietary-red)

An automated quantitative data pipeline built in Python that monitors live derivative sports markets, calculates multi-book market consensus medians, isolates retail pricing inefficiencies on DraftKings and FanDuel, and dispatches real-time actionable trade alerts via asynchronous Discord webhooks.

---

🏗 Pipeline Architecture

[The Odds API Feed]
│
▼
[REST Ingestion & Serialization]
│
▼
[Market Registry Aggregator]
(Normalizes asymmetric two-way pricing across all US market makers)
│
▼
[Quantitative Consensus Engine]
(Calculates median lines: BetMGM, Caesars, BetRivers, Bovada)
│
▼
[Discrepancy & Variance Filter] ───► Threshold: >= 3.5 Units (CLV Edge)
│
▼
[Discord Webhook Dispatcher] ───► Real-Time Mobile Trade Execution Alerts

---

## ⚡ Core Engineering & Quantitative Features

* **Multi-Book Consensus Modeling:** Eliminates binary assumption bias by aggregating line distributions across all active market makers, dynamically calculating the true market median (`statistics.median`).
* **Asymmetric Vig Normalization:** Maps complex two-way derivative markets (Over and Under prices) simultaneously, ensuring signals account for asymmetric juice and hold percentages.
* **Closing Line Value (CLV) Capture:** Identifies stale lines on retail books (DraftKings/FanDuel) that have lagged behind syndicate market steam, locking in positive expected value (+EV).
* **Quota-Optimized Ingestion:** Structures bulk market payloads to query complete game sets simultaneously, preserving API rate-limiting budgets while monitoring dozens of concurrent events.
* **Event-Driven Alerting:** Automatically delivers clean, actionable execution directives (`BET OVER/UNDER ON [BOOK]`) directly to mobile devices via webhook dispatch.

---

## 🛠 Tech Stack

* **Language:** Python 3.9+
* **Data Processing & Analytics:** `statistics`, `json`
* **Networking & Protocols:** `requests` (REST API client, HTTP connection pooling)
* **External Integrations:** [The Odds API](https://the-odds-api.com/), Discord Webhook API
* **Execution Runtime:** Google Colab, Cloud Functions, or Local Daemon

---

## 🚀 Installation & Local Execution

### 1. Clone the Repository
```bash
git clone https://github.com/YSL2720/realtime-odds-arbitrage-engine.git
cd realtime-odds-arbitrage-engine
```
## 2. Install dependencies
```bash
pip install requests
```
## 3. Configure Credentials
Set your API keys as environment variables:
```bash
export ODDS_API_KEY="your_api_key_here"
export DISCORD_WEBHOOK_URL="your_webhook_url_here"
```
(Or input them directly into the configuration block of main.py for testing).

## 4. Execute the scanner
```bash
python main.py
```
## 📊 Sample Output Signal
```bash
🎯 HIGH-CONVICTION BET FOUND
Player: Trevor Lawrence (Player Pass Yds)
Matchup: Houston Texans @ Jacksonville Jaguars

📊 Market Consensus: 228.5 Yards (across 5 books)
• DraftKings: 221.5 (Over -113 | Under -115)
• FanDuel: 228.5 (Over -113 | Under -113)

🚀 ACTION: 👉 BET OVER ON DRAFTKINGS (221.5 @ -113)
💡 Why: DraftKings is 7.0 yds BELOW market consensus (228.5)!
--------------------------------------
```





