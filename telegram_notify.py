# ============================================================
#  telegram_notify.py — MODUL NOTIFIKASI TELEGRAM
#  Semua notifikasi bot dihantar melalui fail ini
# ============================================================

import requests
import logging
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

# Emoji untuk setiap jenis mesej
EMOJI = {
    "start":     "🤖",
    "scan":      "🔍",
    "found":     "🎯",
    "buy":       "🟢",
    "sell":      "🔴",
    "limit":     "📌",
    "profit":    "💰",
    "loss":      "❌",
    "report":    "📊",
    "warning":   "⚠️",
    "stop":      "🛑",
    "dryrun":    "🔵",
}


def send_telegram(message: str, silent: bool = False) -> bool:
    """
    Hantar mesej ke Telegram.
    silent=True = notifikasi tanpa bunyi (untuk update biasa)
    """
    if TELEGRAM_BOT_TOKEN == "ISI_TOKEN_BOT_TELEGRAM_ANDA":
        logger.warning("Telegram belum dikonfigurasikan dalam config.py")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_notification": silent
        }
        response = requests.post(url, json=payload, timeout=10)
        return response.status_code == 200

    except Exception as e:
        logger.warning(f"Gagal hantar Telegram: {e}")
        return False


# ─── NOTIFIKASI SPESIFIK ───────────────────────────────────

def notify_bot_started(dry_run: bool, trade_size: float):
    msg = (
        f"{EMOJI['start']} <b>BOT POLYMARKET DIMULAKAN</b>\n"
        f"{'━' * 28}\n"
        f"📋 Mod      : {'🔵 DRY RUN (Simulasi)' if dry_run else '🔴 LIVE TRADING'}\n"
        f"💵 Saiz Trade: <b>${trade_size:.2f} USDC</b>\n"
        f"⏰ Masa     : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"{'━' * 28}\n"
        f"{'⚠️ Tiada duit sebenar digunakan' if dry_run else '⚡ Bot sedang trading secara LIVE!'}"
    )
    send_telegram(msg)


def notify_opportunity_found(question: str, arb_type: str,
                              total_sum: float, profit_pct: float,
                              profit_usdc: float, outcomes: list):
    outcome_lines = "\n".join(
        [f"   • {o.name}: <b>${o.yes_price:.4f}</b>" for o in outcomes]
    )
    msg = (
        f"{EMOJI['found']} <b>PELUANG ARBITRAGE DITEMUI!</b>\n"
        f"{'━' * 28}\n"
        f"📌 <b>{question[:55]}...</b>\n"
        f"📊 Jenis    : <b>{arb_type} ARB</b>\n"
        f"🧮 Jumlah YES: <b>${total_sum:.4f}</b>\n"
        f"📈 Keuntungan: <b>{profit_pct*100:.2f}%</b> = <b>${profit_usdc:.4f} USDC</b>\n"
        f"{'━' * 28}\n"
        f"<b>Outcomes:</b>\n{outcome_lines}"
    )
    send_telegram(msg)


def notify_order_executing(question: str, arb_type: str,
                            trade_size: float, dry_run: bool):
    emoji = EMOJI['dryrun'] if dry_run else EMOJI['buy']
    mode  = "[SIMULASI]" if dry_run else "[LIVE]"
    msg = (
        f"{emoji} <b>{mode} MELAKSANA ORDER</b>\n"
        f"{'━' * 28}\n"
        f"📌 {question[:55]}...\n"
        f"📊 Jenis   : <b>{arb_type} Arbitrage</b>\n"
        f"💵 Saiz    : <b>${trade_size:.2f} USDC</b>\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    send_telegram(msg)


def notify_limit_order_placed(question: str, outcome_name: str,
                               price: float, amount: float, dry_run: bool):
    emoji = EMOJI['dryrun'] if dry_run else EMOJI['limit']
    mode  = "[SIMULASI]" if dry_run else "[LIVE]"
    msg = (
        f"{emoji} <b>{mode} LIMIT ORDER DILETAKKAN</b>\n"
        f"{'━' * 28}\n"
        f"📌 {question[:50]}...\n"
        f"🎯 Outcome : <b>{outcome_name}</b>\n"
        f"💲 Harga   : <b>${price:.4f}</b>\n"
        f"💵 Jumlah  : <b>${amount:.2f} USDC</b>\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
        f"{'━' * 28}\n"
        f"⏳ Menunggu order untuk diisi..."
    )
    send_telegram(msg)


def notify_trade_success(question: str, arb_type: str,
                          profit_usdc: float, dry_run: bool):
    emoji = EMOJI['dryrun'] if dry_run else EMOJI['profit']
    mode  = "[SIMULASI]" if dry_run else ""
    msg = (
        f"{emoji} <b>{mode} TRADE BERJAYA! ✅</b>\n"
        f"{'━' * 28}\n"
        f"📌 {question[:55]}...\n"
        f"📊 Jenis   : <b>{arb_type} Arbitrage</b>\n"
        f"💰 Keuntungan: <b>+${profit_usdc:.4f} USDC</b>\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    send_telegram(msg)


def notify_trade_failed(question: str, reason: str):
    msg = (
        f"{EMOJI['loss']} <b>TRADE GAGAL</b>\n"
        f"{'━' * 28}\n"
        f"📌 {question[:55]}...\n"
        f"❌ Sebab   : {reason}\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    send_telegram(msg)


def notify_risk_rejected(question: str, reason: str):
    msg = (
        f"{EMOJI['warning']} <b>TRADE DITOLAK OLEH RISK MANAGER</b>\n"
        f"{'━' * 28}\n"
        f"📌 {question[:55]}...\n"
        f"🛡️  Sebab  : {reason}\n"
        f"⏰ {datetime.now().strftime('%H:%M:%S')}"
    )
    send_telegram(msg, silent=True)


def notify_hourly_report(scan_count: int, opportunities_found: int,
                          trades_executed: int, trades_success: int,
                          total_profit: float, daily_pnl: float,
                          available_capital: float, dry_run: bool):
    win_rate = (trades_success / trades_executed * 100) if trades_executed > 0 else 0
    mode     = "🔵 DRY RUN" if dry_run else "🔴 LIVE"

    msg = (
        f"{EMOJI['report']} <b>LAPORAN SEJAM — {datetime.now().strftime('%H:%M %d/%m')}</b>\n"
        f"{'━' * 28}\n"
        f"📋 Mod          : <b>{mode}</b>\n"
        f"{'━' * 28}\n"
        f"🔍 Jumlah Scan   : <b>{scan_count}</b>\n"
        f"🎯 Peluang Jumpa : <b>{opportunities_found}</b>\n"
        f"⚡ Trade Buat    : <b>{trades_executed}</b>\n"
        f"✅ Trade Berjaya : <b>{trades_success}</b>\n"
        f"📊 Win Rate      : <b>{win_rate:.1f}%</b>\n"
        f"{'━' * 28}\n"
        f"💰 Profit Sejam  : <b>${total_profit:.4f} USDC</b>\n"
        f"📈 P&L Hari Ini  : <b>${daily_pnl:.4f} USDC</b>\n"
        f"💵 Modal Tersedia: <b>${available_capital:.2f} USDC</b>\n"
        f"{'━' * 28}\n"
        f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )
    send_telegram(msg)


def notify_emergency_stop(reason: str):
    msg = (
        f"{EMOJI['stop']} <b>⚠️ BOT DIHENTIKAN KECEMASAN!</b>\n"
        f"{'━' * 28}\n"
        f"❌ Sebab: <b>{reason}</b>\n"
        f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n"
        f"{'━' * 28}\n"
        f"Sila semak bot anda segera!"
    )
    send_telegram(msg)


def notify_bot_stopped(total_profit: float, total_trades: int, dry_run: bool):
    mode = "🔵 DRY RUN" if dry_run else "🔴 LIVE"
    msg = (
        f"{EMOJI['stop']} <b>BOT DIHENTIKAN</b>\n"
        f"{'━' * 28}\n"
        f"📋 Mod       : <b>{mode}</b>\n"
        f"⚡ Total Trade: <b>{total_trades}</b>\n"
        f"💰 Total Profit: <b>${total_profit:.4f} USDC</b>\n"
        f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
    )
    send_telegram(msg)
