# cli.py

import argparse
import logging
import sys
from pathlib import Path

from bot.logging_config import setup_logging
from bot.client import BinanceFuturesClient, BinanceAPIError
from bot.orders import OrderService
from bot.validators import (
    validate_symbol,
    validate_side,
    validate_order_type,
    validate_quantity,
    validate_price,
    ValidationError,
)


logger = logging.getLogger(__name__)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Simplified Binance Futures Testnet trading bot (USDT-M).",
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Trading pair symbol, e.g., BTCUSDT",
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=["BUY", "SELL", "buy", "sell"],
        help="Order side: BUY or SELL",
    )
    parser.add_argument(
        "--type",
        dest="order_type",
        required=True,
        choices=["MARKET", "LIMIT", "market", "limit"],
        help="Order type: MARKET or LIMIT",
    )
    parser.add_argument(
        "--quantity",
        required=True,
        help="Order quantity (float)",
    )
    parser.add_argument(
        "--price",
        required=False,
        help="Order price (required for LIMIT orders)",
    )
    parser.add_argument(
        "--log-file",
        default="logs/trading_bot.log",
        help="Path to log file (default: logs/trading_bot.log)",
    )
    return parser.parse_args(argv)


def print_order_summary(
    symbol: str,
    side: str,
    order_type: str,
    quantity: float,
    price: float | None,
):
    print("=== Order Request Summary ===")
    print(f"Symbol     : {symbol}")
    print(f"Side       : {side}")
    print(f"Type       : {order_type}")
    print(f"Quantity   : {quantity}")
    if order_type == "LIMIT":
        print(f"Price      : {price}")
    print("=============================")


def print_order_response(response: dict):
    print("\n=== Order Response ===")
    print(f"Order ID      : {response.get('orderId')}")
    print(f"Status        : {response.get('status')}")
    print(f"Symbol        : {response.get('symbol')}")
    print(f"Side          : {response.get('side')}")
    print(f"Type          : {response.get('type')}")
    print(f"Executed Qty  : {response.get('executedQty')}")
    avg_price = response.get("avgPrice") or response.get("avgPrice", "N/A")
    print(f"Avg Price     : {avg_price if avg_price not in (None, '') else 'N/A'}")
    print("=======================")


def main(argv=None) -> int:
    args = parse_args(argv)
    setup_logging(args.log_file)

    try:
        symbol = validate_symbol(args.symbol)
        side = validate_side(args.side)
        order_type = validate_order_type(args.order_type)
        quantity = validate_quantity(args.quantity)
        price = validate_price(args.price)

        if order_type == "LIMIT" and price is None:
            raise ValidationError("price is required for LIMIT orders")

    except ValidationError as e:
        logger.error("Input validation error: %s", e)
        print(f"Input validation error: {e}")
        return 1

    print_order_summary(symbol, side, order_type, quantity, price)

    try:
        client = BinanceFuturesClient()
        service = OrderService(client)
        response = service.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
        )
        print_order_response(response)
        print("\nOrder placement: SUCCESS")
        return 0
    except BinanceAPIError as e:
        print("\nOrder placement: FAILED")
        print(f"Reason: {e}")
        return 2
    except Exception as e:
        logger.exception("Unexpected error")
        print("\nOrder placement: FAILED")
        print(f"Unexpected error: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())

