# ============================================================
#  risk_manager.py — PENGURUS RISIKO + TELEGRAM ALERT
# ============================================================

import logging
from config import MAX_TOTAL_EXPOSURE
from scanner import ArbitrageOpportunity
from telegram_notify import notify_risk_rejected, notify_emergency_stop

logger = logging.getLogger(__name__)


class RiskManager:

    def __init__(self):
        self.deployed      = 0.0
        self.trades_today  = 0
        self.daily_pnl     = 0.0
        self.max_daily_loss = MAX_TOTAL_EXPOSURE * 0.10
        self.is_halted     = False

    def approve(self, opp: ArbitrageOpportunity) -> tuple[bool, str]:
        """Semak sama ada trade boleh dilaksanakan."""

        if self.is_halted:
            reason = "Bot dihentikan — kill switch aktif"
            return False, reason

        if self.daily_pnl < -self.max_daily_loss:
            reason = f"Rugi harian melebihi ${self.max_daily_loss:.2f}"
            self.emergency_stop(reason)
            return False, reason

        if self.deployed + opp.trade_size > MAX_TOTAL_EXPOSURE:
            reason = f"Melebihi had exposure ${MAX_TOTAL_EXPOSURE} USDC"
            notify_risk_rejected(opp.market_question, reason)
            return False, reason

        if opp.expected_profit_usdc < 0.01:
            return False, "Keuntungan terlalu kecil"

        if len(opp.outcomes) > 8:
            reason = f"Terlalu banyak outcomes ({len(opp.outcomes)})"
            notify_risk_rejected(opp.market_question, reason)
            return False, reason

        for o in opp.outcomes:
            if o.yes_price < 0.02:
                reason = f"'{o.name}' terlalu murah — tidak liquid"
                notify_risk_rejected(opp.market_question, reason)
                return False, reason

        return True, "✅ Diluluskan"

    def record_start(self, size: float):
        self.deployed     += size
        self.trades_today += 1

    def record_end(self, size: float, profit: float, success: bool):
        self.deployed -= size
        self.daily_pnl += profit if success else -(size * 0.005)

    def emergency_stop(self, reason: str):
        self.is_halted = True
        notify_emergency_stop(reason)
        logger.critical(f"🚨 EMERGENCY STOP: {reason}")

    def get_status(self) -> dict:
        return {
            "halted":    self.is_halted,
            "deployed":  self.deployed,
            "trades":    self.trades_today,
            "daily_pnl": self.daily_pnl,
            "available": MAX_TOTAL_EXPOSURE - self.deployed
        }
