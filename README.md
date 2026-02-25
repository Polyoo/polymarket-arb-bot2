# 🤖 Polymarket NegRisk Arbitrage Bot

Bot arbitrage automatik untuk pasaran **fee-free** di Polymarket.
Strategi: NegRisk Long/Short Arbitrage pada pasaran politik & sukan.

## 📁 Struktur Fail

```
polymarket_arb_bot/
├── main.py              ← Jalankan ini
├── scanner.py           ← Cari peluang arbitrage
├── executor.py          ← Hantar order ke Polymarket
├── risk_manager.py      ← Kawal risiko & modal
├── telegram_notify.py   ← Notifikasi Telegram
├── config.example.py    ← Template config (copy → config.py)
└── requirements.txt     ← Library Python
```

## ⚙️ Setup

```bash
# 1. Clone repo
git clone https://github.com/USERNAME/polymarket_arb_bot.git
cd polymarket_arb_bot

# 2. Install library
pip install -r requirements.txt

# 3. Setup config
cp config.example.py config.py
# Edit config.py — isi API keys anda

# 4. Jalankan bot
python main.py
```

## 🔑 Cara Dapat Keys

- **Polymarket API**: polymarket.com → Profile → Settings → API Keys
- **Private Key**: Phantom/Metamask → Export Private Key
- **Telegram Token**: Cari @BotFather → /newbot
- **Telegram Chat ID**: Cari @userinfobot → /start

## ⚠️ Penting

- Mula dengan `DRY_RUN = True` dalam config.py
- `config.py` ada dalam `.gitignore` — API keys anda selamat
- Mula dengan modal kecil ($10-20 USDC)
