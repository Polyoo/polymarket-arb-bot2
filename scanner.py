# ============================================================
#  scanner.py — PENGIMBAS PELUANG NEGRISK (FEE-FREE SAHAJA)
#  Hanya scan pasaran politik, sukan jangka panjang — tiada fee!
# ============================================================

import requests
import logging
from dataclasses import dataclass, field
from typing import List, Optional
from config import GAMMA_API_URL, MIN_PROFIT_THRESHOLD

logger = logging.getLogger(__name__)


@dataclass
class Outcome:
    name: str
    token_id: str
    yes_price: float
    no_price: float


@dataclass
class ArbitrageOpportunity:
    market_id: str
    market_question: str
    arb_type: str
    outcomes: List[Outcome]
    total_yes_sum: float
    expected_profit_pct: float
    expected_profit_usdc: float
    trade_size: float


# ─── KATEGORI PASARAN FEE-FREE ─────────────────────────────
# Crypto 5-min & 15-min ADA FEE sehingga 3.15%
# Semua lain BEBAS FEE sepenuhnya
FEE_MARKET_KEYWORDS = [
    "will bitcoin", "will btc", "will eth", "will ethereum",
    "will sol", "will solana", "will bnb",
    "15-minute", "5-minute", "hourly", "daily high",
    "end of day", "eod price"
]


def is_fee_market(question: str) -> bool:
    """Semak sama ada pasaran ini ada fee (crypto short-term)."""
    question_lower = question.lower()
    return any(kw in question_lower for kw in FEE_MARKET_KEYWORDS)


def fetch_negrisk_markets() -> List[dict]:
    """Ambil semua pasaran NegRisk aktif."""
    logger.info("📡 Mengambil pasaran NegRisk dari Gamma API...")
    all_markets = []
    offset = 0

    while True:
        try:
            params = {
                "active": "true",
                "closed": "false",
                "neg_risk": "true",
                "order": "volumeNum",
                "ascending": "false",
                "offset": offset,
                "limit": 100
            }
            r = requests.get(f"{GAMMA_API_URL}/markets", params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            if not data:
                break
            all_markets.extend(data)
            if len(data) < 100:
                break
            offset += 100
        except Exception as e:
            logger.error(f"❌ Gagal ambil pasaran: {e}")
            break

    # Tapis keluar pasaran crypto berbayar
    fee_free = [m for m in all_markets if not is_fee_market(m.get("question", ""))]
    logger.info(f"✅ {len(fee_free)} pasaran fee-free dijumpai (dari {len(all_markets)} jumlah)")
    return fee_free


def scan_for_arbitrage(market_id: str, question: str,
                        trade_size: float) -> Optional[ArbitrageOpportunity]:
    """Semak satu pasaran untuk peluang arbitrage."""
    try:
        r = requests.get(f"{GAMMA_API_URL}/markets/{market_id}", timeout=10)
        r.raise_for_status()
        data = r.json()

        tokens = data.get("tokens", [])
        if len(tokens) < 2:
            return None

        outcomes = []
        for t in tokens:
            price = float(t.get("price", 0))
            if price <= 0.01 or price >= 0.99:
                continue
            outcomes.append(Outcome(
                name=t.get("outcome", "?"),
                token_id=t.get("token_id", ""),
                yes_price=price,
                no_price=round(1.0 - price, 6)
            ))

        if len(outcomes) < 2:
            return None

        total = sum(o.yes_price for o in outcomes)

        # LONG ARB → jumlah < $1.00 (beli semua YES)
        if total < 1.0:
            net_profit = (1.0 - total)      # Fee-free = tiada tolak fee!
            if net_profit >= MIN_PROFIT_THRESHOLD:
                return ArbitrageOpportunity(
                    market_id=market_id,
                    market_question=question,
                    arb_type="LONG",
                    outcomes=outcomes,
                    total_yes_sum=round(total, 6),
                    expected_profit_pct=net_profit,
                    expected_profit_usdc=net_profit * trade_size,
                    trade_size=trade_size
                )

        # SHORT ARB → jumlah > $1.00 (jual semua YES)
        elif total > 1.0:
            net_profit = total - 1.0
            if net_profit >= MIN_PROFIT_THRESHOLD:
                return ArbitrageOpportunity(
                    market_id=market_id,
                    market_question=question,
                    arb_type="SHORT",
                    outcomes=outcomes,
                    total_yes_sum=round(total, 6),
                    expected_profit_pct=net_profit,
                    expected_profit_usdc=net_profit * trade_size,
                    trade_size=trade_size
                )

    except Exception as e:
        logger.debug(f"Skip {market_id}: {e}")

    return None


def scan_all(trade_size: float) -> List[ArbitrageOpportunity]:
    """Scan semua pasaran fee-free dan kembalikan peluang."""
    logger.info(f"\n🔍 MULA SCAN | Threshold: {MIN_PROFIT_THRESHOLD*100:.1f}% | Trade: ${trade_size}")
    markets = fetch_negrisk_markets()
    found   = []

    for i, m in enumerate(markets):
        mid      = m.get("id", "")
        question = m.get("question", "")
        if not mid:
            continue

        opp = scan_for_arbitrage(mid, question, trade_size)
        if opp:
            found.append(opp)
            logger.info(f"  🎯 [{opp.arb_type}] {question[:50]}... | "
                        f"Spread: {opp.expected_profit_pct*100:.2f}% | "
                        f"+${opp.expected_profit_usdc:.4f}")

        if (i + 1) % 50 == 0:
            logger.info(f"  ... {i+1}/{len(markets)} pasaran diimbas")

    logger.info(f"✅ Scan selesai: {len(found)} peluang dari {len(markets)} pasaran")
    return found
