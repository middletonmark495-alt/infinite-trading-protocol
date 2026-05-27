"""
Outbound alert sender — Discord webhook and Telegram bot.
Silently skips if not configured.
"""
import logging
import requests
import config as cfg

log = logging.getLogger(__name__)


def _discord(message: str):
    if not cfg.DISCORD_WEBHOOK_URL:
        return
    try:
        requests.post(cfg.DISCORD_WEBHOOK_URL, json={"content": message}, timeout=5)
    except Exception as e:
        log.warning("Discord alert failed: %s", e)


def _telegram(message: str):
    if not cfg.TELEGRAM_BOT_TOKEN or not cfg.TELEGRAM_ALERT_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{cfg.TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": cfg.TELEGRAM_ALERT_CHAT_ID, "text": message, "parse_mode": "Markdown"},
            timeout=5,
        )
    except Exception as e:
        log.warning("Telegram alert failed: %s", e)


def send(message: str):
    """Broadcast to all configured channels."""
    _discord(message)
    _telegram(message)


def trade_opened(symbol: str, side: str, price: float, qty: float, sl: float, tp: float, reason: str):
    msg = (
        f"🚀 *TRADE OPEN* `{symbol}`\n"
        f"Side: {side.upper()}  |  Price: `${price:.6f}`\n"
        f"Qty: `{qty:.4f}`  |  SL: `${sl:.6f}`  |  TP: `${tp:.6f}`\n"
        f"Reason: _{reason}_"
    )
    log.info(msg.replace("*", "").replace("`", "").replace("_", ""))
    send(msg)


def trade_closed(symbol: str, exit_price: float, pnl: float, pnl_pct: float, reason: str):
    icon = "✅" if pnl >= 0 else "❌"
    msg = (
        f"{icon} *TRADE CLOSE* `{symbol}`\n"
        f"Exit: `${exit_price:.6f}`  |  P&L: `${pnl:+.2f}` (`{pnl_pct:+.2f}%`)\n"
        f"Reason: _{reason}_"
    )
    log.info(msg.replace("*", "").replace("`", "").replace("_", ""))
    send(msg)


def meme_alert(symbol: str, chain: str, price: float, chg_1h: float, liq: float, url: str, reason: str):
    msg = (
        f"🔥 *MEME COIN SIGNAL* `{symbol}` [{chain}]\n"
        f"Price: `${price:.8f}`  |  1h: `{chg_1h:+.1f}%`\n"
        f"Liquidity: `${liq:,.0f}`\n"
        f"Signal: _{reason}_\n"
        f"{url}"
    )
    log.info("MEME SIGNAL: %s %s +%.1f%% liq=$%.0f", symbol, chain, chg_1h, liq)
    send(msg)


def stats_report(stats: dict):
    msg = (
        f"📊 *BOT STATS*\n"
        f"Capital: `${stats['capital']:,.2f}`  |  P&L: `${stats['total_pnl']:+.2f}` (`{stats['total_pnl_pct']:+.2f}%`)\n"
        f"Trades: `{stats['total_trades']}`  |  Win rate: `{stats['win_rate']:.1f}%`\n"
        f"Profit factor: `{stats['profit_factor']}`  |  Open: `{stats['open_positions']}`"
    )
    send(msg)
