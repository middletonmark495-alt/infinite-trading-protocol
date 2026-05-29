#!/usr/bin/env python3
"""
bank.py  —  ITP Banker CLI
Run it. Do what you gotta do.

    python bank.py           # interactive REPL
    python bank.py balance   # one-shot command
    python bank.py price BTC-USD
    python bank.py buy BTC-USD 100
"""

import os
import sys
from typing import Optional

# ── load .env ─────────────────────────────────────────────────────────────────
_env_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _, _v = _line.partition("=")
                os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(__file__))
from coinbase import CoinbaseAdvancedClient  # noqa: E402

_client = CoinbaseAdvancedClient()


# ── formatting ────────────────────────────────────────────────────────────────

def _usd(v) -> str:
    return f"${float(v):,.2f}"

def _pct(v) -> str:
    f = float(v)
    return f"+{f:.2f}%" if f >= 0 else f"{f:.2f}%"


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_balance(_args):
    accounts = _client.list_accounts()
    if not accounts:
        print("No accounts (check API keys in .env).")
        return
    rows = []
    for a in accounts:
        avail = float(a.get("available_balance", {}).get("value", 0))
        hold  = float(a.get("hold", {}).get("value", 0))
        if avail + hold == 0:
            continue
        rows.append((a.get("currency", ""), avail, hold))
    if not rows:
        print("All balances are zero.")
        return
    print(f"\n{'CURRENCY':<12} {'AVAILABLE':>20} {'ON HOLD':>20}")
    print("─" * 54)
    for cur, avail, hold in rows:
        print(f"{cur:<12} {avail:>20.8f} {hold:>20.8f}")
    print()


def cmd_price(args):
    if not args:
        print("Usage: price <PAIR>  e.g.  price BTC-USD")
        return
    pair    = args[0].upper()
    product = _client.get_product(pair)
    if not product:
        print(f"Product not found: {pair}")
        return
    p    = product.get("price")
    ch   = product.get("price_percentage_change_24h")
    vol  = product.get("volume_24h")
    high = product.get("price_24h_high") or product.get("high_52_week")
    low  = product.get("price_24h_low")  or product.get("low_52_week")

    print(f"\n{pair}")
    if p:    print(f"  Price  : {_usd(p)}")
    if ch:   print(f"  24h    : {_pct(ch)}")
    if high: print(f"  High   : {_usd(high)}")
    if low:  print(f"  Low    : {_usd(low)}")
    if vol:
        try:
            print(f"  Volume : {float(vol):,.2f}")
        except ValueError:
            pass
    print()


def cmd_buy(args):
    if len(args) < 2:
        print("Usage: buy <PAIR> <USD>  e.g.  buy BTC-USD 100")
        return
    pair, usd = args[0].upper(), args[1]
    confirm = input(f"  Market BUY {_usd(usd)} of {pair}? [y/N] ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return
    result = _client.create_market_order(pair, "BUY", quote_size=str(usd))
    _print_order_result(result)


def cmd_sell(args):
    if len(args) < 2:
        print("Usage: sell <PAIR> <AMOUNT>  e.g.  sell ETH-USD 0.1")
        return
    pair, amount = args[0].upper(), args[1]
    confirm = input(f"  Market SELL {amount} {pair}? [y/N] ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return
    result = _client.create_market_order(pair, "SELL", base_size=str(amount))
    _print_order_result(result)


def cmd_limit(args):
    if len(args) < 4:
        print("Usage: limit <buy|sell> <PAIR> <SIZE> <PRICE>")
        print("  e.g. limit buy BTC-USD 0.001 60000")
        return
    side, pair, size, lp = args[0].upper(), args[1].upper(), args[2], args[3]
    confirm = input(f"  Limit {side} {size} {pair} @ {_usd(lp)}? [y/N] ").strip().lower()
    if confirm != "y":
        print("  Cancelled.")
        return
    result = _client.create_limit_order_gtc(pair, side, size, lp)
    _print_order_result(result)


def cmd_orders(args):
    status = args[0].upper() if args else "OPEN"
    orders = _client.list_orders(order_status=status, limit=25)
    if not orders:
        print(f"No {status.lower()} orders.")
        return
    print(f"\n{'ORDER ID':<38} {'PAIR':<12} {'SIDE':<5} {'SIZE':>14} {'PRICE':>14} {'STATUS'}")
    print("─" * 95)
    for o in orders:
        oid   = o.get("order_id", "")[:36]
        pair  = o.get("product_id", "")
        side  = o.get("side", "")
        stat  = o.get("status", "")
        cfg   = o.get("order_configuration", {})
        size, lp = "─", "MKT"
        for v in cfg.values():
            if isinstance(v, dict):
                size = v.get("base_size") or v.get("quote_size") or "─"
                lp   = v.get("limit_price") or "MKT"
        print(f"{oid:<38} {pair:<12} {side:<5} {str(size):>14} {str(lp):>14}  {stat}")
    print()


def cmd_cancel(args):
    if not args:
        print("Usage: cancel <ORDER_ID> [ORDER_ID ...]")
        return
    result = _client.cancel_orders(args)
    if result:
        results = result.get("results", [result])
        for r in results if isinstance(results, list) else [results]:
            oid     = r.get("order_id", "")
            success = r.get("success", False)
            print(f"  {oid}  →  {'cancelled' if success else 'FAILED: ' + str(r.get('failure_reason', ''))}")
    else:
        print("Cancel failed.")


def cmd_fills(args):
    pair  = args[0].upper() if args else None
    fills = _client.list_fills(product_id=pair, limit=20)
    if not fills:
        print("No fills found.")
        return
    print(f"\n{'PAIR':<12} {'SIDE':<5} {'SIZE':>16} {'PRICE':>14} {'TIME'}")
    print("─" * 65)
    for f in fills:
        pair_ = f.get("product_id", "")
        side  = f.get("side", "")
        size  = f.get("size", "0")
        price = f.get("price", "0")
        ts    = f.get("trade_time", "")[:19].replace("T", " ")
        try:
            print(f"{pair_:<12} {side:<5} {float(size):>16.8f} {float(price):>14.2f}  {ts}")
        except ValueError:
            print(f"{pair_:<12} {side:<5} {size:>16} {price:>14}  {ts}")
    print()


def cmd_fees(_args):
    summary = _client.get_transaction_summary()
    if not summary:
        print("Could not fetch fee info (check API keys).")
        return
    tier = summary.get("fee_tier", {})
    vol  = summary.get("total_volume", {})
    print(f"\n  Tier      : {tier.get('pricing_tier', 'N/A')}")
    try:
        print(f"  Taker     : {float(tier.get('taker_fee_rate', 0)) * 100:.4f}%")
        print(f"  Maker     : {float(tier.get('maker_fee_rate', 0)) * 100:.4f}%")
    except (ValueError, TypeError):
        pass
    try:
        print(f"  30d vol   : {_usd(vol.get('value', 0))}")
    except (ValueError, TypeError):
        pass
    print()


def cmd_help(_args):
    print("""
  balance                              show all account balances
  price  <PAIR>                        e.g.  price BTC-USD
  buy    <PAIR> <USD>                  market buy   e.g.  buy BTC-USD 100
  sell   <PAIR> <AMOUNT>               market sell  e.g.  sell ETH-USD 0.1
  limit  <buy|sell> <PAIR> <SIZE> <PRICE>   GTC limit order
  orders [OPEN|FILLED|CANCELLED]       list orders  (default: OPEN)
  cancel <ORDER_ID> [...]              cancel one or more orders
  fills  [PAIR]                        recent trade fills
  fees                                 fee tier and 30-day volume
  help                                 this list
  quit                                 exit
""")


# ── plumbing ──────────────────────────────────────────────────────────────────

def _print_order_result(result: Optional[dict]) -> None:
    if not result:
        print("  Order failed — check API keys and account balance.")
        return
    sr = result.get("success_response") or result
    oid = sr.get("order_id", "")
    if oid:
        print(f"  Order placed: {oid}")
    else:
        er = result.get("error_response", {})
        print(f"  Order failed: {er.get('message') or er.get('error') or result}")


COMMANDS = {
    "balance": cmd_balance,
    "price":   cmd_price,
    "buy":     cmd_buy,
    "sell":    cmd_sell,
    "limit":   cmd_limit,
    "orders":  cmd_orders,
    "cancel":  cmd_cancel,
    "fills":   cmd_fills,
    "fees":    cmd_fees,
    "help":    cmd_help,
    "?":       cmd_help,
}


# ── entry point ───────────────────────────────────────────────────────────────

def main(argv: list) -> None:
    if argv:
        cmd = argv[0].lower()
        fn  = COMMANDS.get(cmd)
        if fn:
            fn(argv[1:])
        else:
            print(f"Unknown command: {cmd}")
            cmd_help([])
        return

    # REPL
    print("ITP Banker  —  type 'help' for commands, 'quit' to exit\n")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        parts = line.split()
        cmd   = parts[0].lower()
        if cmd in ("quit", "exit", "q"):
            break
        fn = COMMANDS.get(cmd)
        if fn:
            fn(parts[1:])
        else:
            print(f"Unknown: {cmd}  (type 'help')")


if __name__ == "__main__":
    main(sys.argv[1:])
