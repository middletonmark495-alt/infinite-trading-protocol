"""
Paper trading engine — tracks positions and P&L without touching real funds.
Also used as the order interface for live trading (swap in a real broker client).
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

import config as cfg

log = logging.getLogger(__name__)


@dataclass
class Position:
    id: str
    symbol: str
    side: str            # "long" | "short"
    entry_price: float
    quantity: float      # units held
    stop_loss: float
    take_profit: float
    opened_at: str
    source: str = "coinbase"   # coinbase | dexscreener | alpaca
    closed: bool = False
    exit_price: Optional[float] = None
    closed_at: Optional[str] = None
    pnl: float = 0.0
    pnl_pct: float = 0.0


class PaperTrader:
    def __init__(self, starting_capital: float = None):
        self.capital = starting_capital or cfg.STARTING_CAPITAL
        self.initial_capital = self.capital
        self.positions: dict[str, Position] = {}
        self.closed_trades: list[Position] = []
        log.info("Paper trader initialised — capital: $%.2f", self.capital)

    # ── Order management ──────────────────────────────────────────────────────

    def open_long(self, symbol: str, price: float, source: str = "coinbase") -> Optional[Position]:
        if len(self._open_positions()) >= cfg.MAX_OPEN_POSITIONS:
            log.info("Max open positions (%d) reached — skip %s", cfg.MAX_OPEN_POSITIONS, symbol)
            return None
        if any(p.symbol == symbol for p in self._open_positions()):
            log.debug("Already long %s — skip", symbol)
            return None

        risk_amount = self.capital * (cfg.RISK_PER_TRADE_PCT / 100)
        stop_loss   = price * (1 - cfg.STOP_LOSS_PCT / 100)
        take_profit = price * (1 + cfg.TAKE_PROFIT_PCT / 100)
        risk_per_unit = price - stop_loss
        quantity = risk_amount / risk_per_unit if risk_per_unit > 0 else 0

        if quantity <= 0 or price * quantity > self.capital:
            log.warning("Insufficient capital to open %s", symbol)
            return None

        pos = Position(
            id=str(uuid.uuid4())[:8],
            symbol=symbol,
            side="long",
            entry_price=price,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
            opened_at=datetime.now(timezone.utc).isoformat(),
            source=source,
        )
        self.positions[pos.id] = pos
        cost = price * quantity
        self.capital -= cost
        log.info(
            "[OPEN LONG] %s @ $%.6f  qty=%.4f  SL=$%.6f  TP=$%.6f  cost=$%.2f  capital_remaining=$%.2f",
            symbol, price, quantity, stop_loss, take_profit, cost, self.capital,
        )
        return pos

    def close_position(self, position_id: str, price: float, reason: str = "manual") -> Optional[Position]:
        pos = self.positions.get(position_id)
        if not pos or pos.closed:
            return None

        gross = price * pos.quantity
        cost  = pos.entry_price * pos.quantity
        pos.pnl = gross - cost
        pos.pnl_pct = ((price - pos.entry_price) / pos.entry_price) * 100
        pos.exit_price = price
        pos.closed_at = datetime.now(timezone.utc).isoformat()
        pos.closed = True
        self.capital += gross
        self.closed_trades.append(pos)
        del self.positions[position_id]

        emoji = "✅" if pos.pnl >= 0 else "❌"
        log.info(
            "%s [CLOSE] %s @ $%.6f  pnl=$%.2f (%.2f%%)  reason=%s  capital=$%.2f",
            emoji, pos.symbol, price, pos.pnl, pos.pnl_pct, reason, self.capital,
        )
        return pos

    def check_exits(self, symbol: str, current_price: float) -> list:
        """Check SL/TP for all open positions in `symbol`. Returns list of closed positions."""
        closed = []
        for pos in list(self._open_positions()):
            if pos.symbol != symbol:
                continue
            if current_price <= pos.stop_loss:
                closed.append(self.close_position(pos.id, current_price, "stop_loss"))
            elif current_price >= pos.take_profit:
                closed.append(self.close_position(pos.id, current_price, "take_profit"))
        return [c for c in closed if c]

    # ── Stats ─────────────────────────────────────────────────────────────────

    def _open_positions(self) -> list:
        return [p for p in self.positions.values() if not p.closed]

    def stats(self) -> dict:
        trades = self.closed_trades
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "capital": round(self.capital, 2),
                "open_positions": len(self._open_positions()),
            }
        wins  = [t for t in trades if t.pnl > 0]
        losses = [t for t in trades if t.pnl <= 0]
        gross_profit = sum(t.pnl for t in wins)
        gross_loss   = abs(sum(t.pnl for t in losses))
        total_pnl    = sum(t.pnl for t in trades)
        return {
            "total_trades": len(trades),
            "win_rate": round(len(wins) / len(trades) * 100, 1),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round((self.capital - self.initial_capital) / self.initial_capital * 100, 2),
            "avg_win":  round(gross_profit / len(wins), 2)   if wins   else 0.0,
            "avg_loss": round(gross_loss   / len(losses), 2) if losses else 0.0,
            "profit_factor": round(gross_profit / gross_loss, 2) if gross_loss > 0 else float("inf"),
            "capital": round(self.capital, 2),
            "open_positions": len(self._open_positions()),
        }

    def print_stats(self):
        s = self.stats()
        log.info("=" * 55)
        log.info("  PAPER TRADING SUMMARY")
        log.info("  Capital:        $%.2f  (started: $%.2f)", s["capital"], self.initial_capital)
        log.info("  Total P&L:      $%.2f  (%.2f%%)", s["total_pnl"], s["total_pnl_pct"])
        log.info("  Trades:         %d  |  Win rate: %.1f%%", s["total_trades"], s["win_rate"])
        log.info("  Avg Win:        $%.2f  |  Avg Loss: $%.2f", s["avg_win"], s["avg_loss"])
        log.info("  Profit Factor:  %.2f", s["profit_factor"])
        log.info("  Open positions: %d", s["open_positions"])
        log.info("=" * 55)
