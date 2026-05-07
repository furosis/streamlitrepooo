from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import pandas as pd


@dataclass
class InvestmentMetrics:
    symbol: str
    owned_quantity: float
    total_buy_quantity: float
    total_sell_quantity: float
    invested_value: float
    sold_value: float
    fees_total: float
    average_buy_price: float
    current_price: Optional[float]
    current_value: Optional[float]
    unrealized_profit: Optional[float]
    realized_profit: float
    total_result: Optional[float]
    return_rate_percent: Optional[float]
    first_buy_price: Optional[float]
    change_vs_first_buy_percent: Optional[float]

    def as_dict(self) -> Dict[str, Any]:
        return self.__dict__.copy()


def calculate_metrics(transactions: pd.DataFrame, symbol: str, current_price: Optional[float] = None) -> InvestmentMetrics:
    symbol = symbol.upper()
    if transactions.empty:
        return InvestmentMetrics(symbol, 0, 0, 0, 0, 0, 0, 0, current_price, None, None, 0, None, None, None, None)

    df = transactions.copy()
    df["transaction_type"] = df["transaction_type"].str.upper()
    buys = df[df["transaction_type"] == "KUPNO"]
    sells = df[df["transaction_type"] == "SPRZEDAŻ"]

    total_buy_quantity = float(buys["quantity"].sum()) if not buys.empty else 0.0
    total_sell_quantity = float(sells["quantity"].sum()) if not sells.empty else 0.0
    owned_quantity = total_buy_quantity - total_sell_quantity

    invested_value = float((buys["quantity"] * buys["price"]).sum()) if not buys.empty else 0.0
    sold_value = float((sells["quantity"] * sells["price"]).sum()) if not sells.empty else 0.0
    fees_total = float(df["fee"].sum()) if "fee" in df.columns else 0.0

    average_buy_price = invested_value / total_buy_quantity if total_buy_quantity > 0 else 0.0
    avg_cost_of_sold = average_buy_price * total_sell_quantity
    realized_profit = sold_value - avg_cost_of_sold - float(sells["fee"].sum() if not sells.empty else 0.0)

    current_value = None
    unrealized_profit = None
    total_result = None
    return_rate_percent = None
    change_vs_first_buy_percent = None

    first_buy_price = None
    if not buys.empty:
        buys_sorted = buys.sort_values(["transaction_date", "id"])
        first_buy_price = float(buys_sorted.iloc[0]["price"])

    if current_price is not None:
        current_value = owned_quantity * float(current_price)
        remaining_cost = average_buy_price * owned_quantity
        unrealized_profit = current_value - remaining_cost
        total_result = realized_profit + unrealized_profit
        capital_base = invested_value + fees_total
        if capital_base > 0:
            return_rate_percent = (total_result / capital_base) * 100
        if first_buy_price and first_buy_price > 0:
            change_vs_first_buy_percent = ((float(current_price) - first_buy_price) / first_buy_price) * 100

    return InvestmentMetrics(
        symbol=symbol,
        owned_quantity=owned_quantity,
        total_buy_quantity=total_buy_quantity,
        total_sell_quantity=total_sell_quantity,
        invested_value=invested_value,
        sold_value=sold_value,
        fees_total=fees_total,
        average_buy_price=average_buy_price,
        current_price=current_price,
        current_value=current_value,
        unrealized_profit=unrealized_profit,
        realized_profit=realized_profit,
        total_result=total_result,
        return_rate_percent=return_rate_percent,
        first_buy_price=first_buy_price,
        change_vs_first_buy_percent=change_vs_first_buy_percent,
    )


def build_portfolio_summary(transactions: pd.DataFrame, latest_prices: Dict[str, Optional[float]]) -> pd.DataFrame:
    if transactions.empty:
        return pd.DataFrame()
    rows = []
    for symbol in sorted(transactions["symbol"].unique()):
        t = transactions[transactions["symbol"] == symbol]
        metrics = calculate_metrics(t, symbol, latest_prices.get(symbol))
        rows.append(metrics.as_dict())
    df = pd.DataFrame(rows)
    if not df.empty:
        display_cols = [
            "symbol",
            "owned_quantity",
            "average_buy_price",
            "current_price",
            "current_value",
            "unrealized_profit",
            "realized_profit",
            "total_result",
            "return_rate_percent",
        ]
        df = df[display_cols]
    return df


def generate_demo_prices(symbol: str, start_date, end_date, start_price: float = 100.0) -> pd.DataFrame:
    import numpy as np

    dates = pd.date_range(start=start_date, end=end_date, freq="D")
    if len(dates) == 0:
        return pd.DataFrame(columns=["price_date", "close_price"])
    seed = sum(ord(c) for c in symbol.upper()) % 10_000
    rng = np.random.default_rng(seed)
    changes = rng.normal(loc=0.0008, scale=0.018, size=len(dates))
    prices = [float(start_price)]
    for change in changes[1:]:
        prices.append(max(0.01, prices[-1] * (1 + change)))
    return pd.DataFrame({"price_date": dates.strftime("%Y-%m-%d"), "close_price": [round(p, 2) for p in prices]})
