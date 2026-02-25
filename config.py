# ============================================================
#  config.py — TETAPAN BOT
#  ISI SEMUA NILAI DI BAWAH SEBELUM JALANKAN BOT
# ============================================================

# ─── POLYMARKET API ────────────────────────────────────────
PRIVATE_KEY    = "0xISI_PRIVATE_KEY_ANDA"
API_KEY        = "ISI_API_KEY_ANDA"
API_SECRET     = "ISI_API_SECRET_ANDA"
API_PASSPHRASE = "ISI_PASSPHRASE_ANDA"

# ─── TELEGRAM ──────────────────────────────────────────────
# Cara dapat: Cari @BotFather di Telegram → /newbot
TELEGRAM_BOT_TOKEN = "ISI_TOKEN_BOT_TELEGRAM_ANDA"
# Cara dapat Chat ID: Cari @userinfobot di Telegram → /start
TELEGRAM_CHAT_ID   = "ISI_CHAT_ID_ANDA"

# ─── TETAPAN TRADING ───────────────────────────────────────
TRADE_SIZE_USDC       = 10.0    # USDC per trade (mula kecil!)
MIN_PROFIT_THRESHOLD  = 0.03    # Minimum 3% profit
MAX_TOTAL_EXPOSURE    = 100.0   # Maksimum USDC dalam trade aktif
SCAN_INTERVAL_SECONDS = 30      # Scan setiap 30 saat

# ─── MOD ───────────────────────────────────────────────────
# True = Simulasi sahaja (SELAMAT, tiada duit sebenar)
# False = LIVE trading (pastikan bot berfungsi dulu!)
DRY_RUN = True

# ─── LAPORAN TELEGRAM ──────────────────────────────────────
REPORT_INTERVAL_MINUTES = 60   # Hantar laporan profit setiap 60 minit

# ─── URL API (JANGAN UBAH) ─────────────────────────────────
POLYMARKET_HOST  = "https://clob.polymarket.com"
GAMMA_API_URL    = "https://gamma-api.polymarket.com"
POLYGON_CHAIN_ID = 137
