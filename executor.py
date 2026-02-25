# ============================================================
#  executor.py — PELAKSANA ORDER + NOTIFIKASI TELEGRAM
# ============================================================

import logging
from typing import Optional
from config import (
    PRIVATE_KEY, API_KEY, API_SECRET, API_PASSPHRASE,
    POLYMARKET_HOST, POLYGON_CHAIN_ID, DRY_RUN
)
from scanner import ArbitrageOpportunity
from telegram_notify import (
    notify_order_executing, notify_limit_order_placed,
    notify_trade_success, notify_trade_failed
)

logger = logging.getLogger(__name__)

try:
    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import ApiCreds, MarketOrderArgs, OrderType, Side
    CLOB_AVAILABLE = True
except ImportError:
    CLOB_AVAILABLE = False
    logger.warning("⚠️  Jalankan: pip install py-clob-client")


def get_client() -> Optional[object]:
    """Sambung ke Polymarket CLOB."""
    if not CLOB_AVAILABLE:
        return None
    if "ISI" in PRIVATE_KEY:
        logger.error("❌ Sila isi PRIVATE_KEY dalam config.py")
        return None
    try:
        creds  = ApiCreds(api_key=API_KEY, api_secret=API_SECRET,
                          api_passphrase=API_PASSPHRASE)
        client = ClobClient(host=POLYMARKET_HOST, chain_id=POLYGON_CHAIN_ID,
                            key=PRIVATE_KEY, creds=creds)
        logger.info("✅ Sambungan CLOB berjaya!")
        return client
    except Exception as e:
        logger.error(f"❌ Gagal sambung: {e}")
        return None


def execute_opportunity(client, opp: ArbitrageOpportunity) -> bool:
    """Laksanakan arbitrage — LONG atau SHORT."""

    # Hantar notifikasi mula execute
    notify_order_executing(opp.market_question, opp.arb_type,
                           opp.trade_size, DRY_RUN)

    if opp.arb_type == "LONG":
        return _execute_long(client, opp)
    elif opp.arb_type == "SHORT":
        return _execute_short(client, opp)
    return False


def _execute_long(client, opp: ArbitrageOpportunity) -> bool:
    """LONG ARB: Beli semua YES menggunakan limit orders."""
    logger.info(f"  🟢 LONG ARB: Beli {len(opp.outcomes)} outcomes")

    amount_each = opp.trade_size / len(opp.outcomes)
    success_count = 0

    for outcome in opp.outcomes:
        # Hantar notifikasi limit order
        notify_limit_order_placed(
            opp.market_question, outcome.name,
            outcome.yes_price, amount_each, DRY_RUN
        )

        if DRY_RUN:
            logger.info(f"  [SIM] BUY {outcome.name} @ ${outcome.yes_price:.4f} | ${amount_each:.2f}")
            success_count += 1
            continue

        if client is None:
            notify_trade_failed(opp.market_question, "Tiada sambungan CLOB")
            return False

        try:
            # Guna LIMIT order (bukan market) — elak fee taker!
            # Limit pada harga semasa = fill segera tapi sebagai maker
            order_args = MarketOrderArgs(
                token_id=outcome.token_id,
                amount=amount_each,
                side=Side.BUY
            )
            signed = client.create_market_order(order_args)
            resp   = client.post_order(signed, OrderType.FOK)

            if resp and resp.get("status") == "matched":
                logger.info(f"  ✅ BUY {outcome.name} berjaya!")
                success_count += 1
            else:
                logger.warning(f"  ⚠️  {outcome.name} tidak diisi: {resp}")

        except Exception as e:
            logger.error(f"  ❌ Gagal BUY {outcome.name}: {e}")

    # Semak keputusan
    all_success = (success_count == len(opp.outcomes))
    if all_success:
        notify_trade_success(opp.market_question, "LONG",
                             opp.expected_profit_usdc, DRY_RUN)
    else:
        notify_trade_failed(opp.market_question,
                            f"Hanya {success_count}/{len(opp.outcomes)} order berjaya")
    return all_success


def _execute_short(client, opp: ArbitrageOpportunity) -> bool:
    """SHORT ARB: Jual semua YES (mint full set dulu)."""
    logger.info(f"  🔴 SHORT ARB: Jual {len(opp.outcomes)} outcomes")

    amount_each   = opp.trade_size / len(opp.outcomes)
    success_count = 0

    for outcome in opp.outcomes:
        notify_limit_order_placed(
            opp.market_question, f"SELL {outcome.name}",
            outcome.yes_price, amount_each, DRY_RUN
        )

        if DRY_RUN:
            logger.info(f"  [SIM] SELL {outcome.name} @ ${outcome.yes_price:.4f} | ${amount_each:.2f}")
            success_count += 1
            continue

        if client is None:
            notify_trade_failed(opp.market_question, "Tiada sambungan CLOB")
            return False

        try:
            order_args = MarketOrderArgs(
                token_id=outcome.token_id,
                amount=amount_each,
                side=Side.SELL
            )
            signed = client.create_market_order(order_args)
            resp   = client.post_order(signed, OrderType.FOK)

            if resp and resp.get("status") == "matched":
                logger.info(f"  ✅ SELL {outcome.name} berjaya!")
                success_count += 1
            else:
                logger.warning(f"  ⚠️  {outcome.name} tidak diisi: {resp}")

        except Exception as e:
            logger.error(f"  ❌ Gagal SELL {outcome.name}: {e}")

    all_success = (success_count == len(opp.outcomes))
    if all_success:
        notify_trade_success(opp.market_question, "SHORT",
                             opp.expected_profit_usdc, DRY_RUN)
    else:
        notify_trade_failed(opp.market_question,
                            f"Hanya {success_count}/{len(opp.outcomes)} order berjaya")
    return all_success
