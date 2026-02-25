#!/usr/bin/env python3
# ============================================================
#  main.py — BOT UTAMA + LAPORAN TELEGRAM SEJAM
#  Jalankan: python main.py
# ============================================================

import time
import logging
import sys
from datetime import datetime
from config import (
    SCAN_INTERVAL_SECONDS, TRADE_SIZE_USDC,
    DRY_RUN, REPORT_INTERVAL_MINUTES,
    PRIVATE_KEY
)
from scanner import scan_all
from executor import get_client, execute_opportunity
from risk_manager import RiskManager
from telegram_notify import (
    notify_bot_started, notify_opportunity_found,
    notify_hourly_report, notify_bot_stopped
)

# ─── SETUP LOG ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)


def banner():
    logger.info("=" * 50)
    logger.info("  POLYMARKET NEGRISK ARBITRAGE BOT")
    logger.info("=" * 50)
    logger.info(f"  Mod    : {'DRY RUN (Simulasi)' if DRY_RUN else '🔴 LIVE TRADING!'}")
    logger.info(f"  Trade  : ${TRADE_SIZE_USDC} USDC")
    logger.info(f"  Scan   : setiap {SCAN_INTERVAL_SECONDS} saat")
    logger.info(f"  Report : setiap {REPORT_INTERVAL_MINUTES} minit ke Telegram")
    logger.info("=" * 50)


def run():
    banner()

    # Sambung ke Polymarket
    client = None
    if "ISI" not in PRIVATE_KEY and not DRY_RUN:
        client = get_client()

    risk = RiskManager()

    # Kaunter statistik
    scan_count     = 0
    opps_found     = 0
    trades_done    = 0
    trades_success = 0
    session_profit = 0.0
    hour_profit    = 0.0
    last_report    = time.time()

    # Hantar notifikasi bot dimulakan
    notify_bot_started(DRY_RUN, TRADE_SIZE_USDC)
    logger.info("\n🤖 Bot berjalan... (Ctrl+C untuk henti)\n")

    try:
        while True:
            scan_count += 1
            logger.info(f"\n{'─'*45}")
            logger.info(f"  SCAN #{scan_count} | {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"{'─'*45}")

            # ── SCAN ─────────────────────────────────────
            opportunities = scan_all(TRADE_SIZE_USDC)
            opps_found += len(opportunities)

            if not opportunities:
                logger.info("💤 Tiada peluang. Tunggu scan seterusnya...")
            else:
                # Susun ikut profit terbesar dulu
                opportunities.sort(
                    key=lambda x: x.expected_profit_pct, reverse=True
                )

                for opp in opportunities:
                    if risk.is_halted:
                        break

                    # Notifikasi peluang ditemui ke Telegram
                    notify_opportunity_found(
                        opp.market_question, opp.arb_type,
                        opp.total_yes_sum, opp.expected_profit_pct,
                        opp.expected_profit_usdc, opp.outcomes
                    )

                    # Semak risiko
                    approved, reason = risk.approve(opp)
                    logger.info(f"  🛡️  Risk: {reason}")

                    if not approved:
                        continue

                    # Laksana trade
                    risk.record_start(opp.trade_size)
                    trades_done += 1

                    success = execute_opportunity(client, opp)

                    if success:
                        trades_success += 1
                        session_profit += opp.expected_profit_usdc
                        hour_profit    += opp.expected_profit_usdc
                        risk.record_end(opp.trade_size,
                                        opp.expected_profit_usdc, True)
                        logger.info(f"  💰 +${opp.expected_profit_usdc:.4f} USDC")
                    else:
                        risk.record_end(opp.trade_size, 0, False)

                    time.sleep(0.5)

            # ── LAPORAN SEJAM ────────────────────────────
            elapsed_min = (time.time() - last_report) / 60
            if elapsed_min >= REPORT_INTERVAL_MINUTES:
                status = risk.get_status()
                notify_hourly_report(
                    scan_count     = scan_count,
                    opportunities_found = opps_found,
                    trades_executed    = trades_done,
                    trades_success     = trades_success,
                    total_profit       = hour_profit,
                    daily_pnl          = status["daily_pnl"],
                    available_capital  = status["available"],
                    dry_run            = DRY_RUN
                )
                logger.info(f"📊 Laporan sejam dihantar ke Telegram!")
                hour_profit  = 0.0   # Reset pengira profit sejam
                last_report  = time.time()

            # ── STATUS RINGKAS ───────────────────────────
            status = risk.get_status()
            logger.info(f"\n  📈 Sesi: {trades_success}/{trades_done} trade berjaya")
            logger.info(f"  💰 Total profit: ${session_profit:.4f} USDC")
            logger.info(f"  💵 Modal tersedia: ${status['available']:.2f} USDC")
            logger.info(f"\n  ⏳ Scan seterusnya dalam {SCAN_INTERVAL_SECONDS}s...")
            time.sleep(SCAN_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("\n\n👋 Bot dihentikan (Ctrl+C)")
        notify_bot_stopped(session_profit, trades_done, DRY_RUN)
        logger.info(f"\n  Total Profit : ${session_profit:.4f} USDC")
        logger.info(f"  Total Trade  : {trades_done}")
        logger.info(f"  Log disimpan : bot.log")

    except Exception as e:
        logger.critical(f"\n🚨 RALAT KRITIKAL: {e}")
        logger.exception("Stack trace:")
        risk.emergency_stop(str(e))
        sys.exit(1)


if __name__ == "__main__":
    run()
