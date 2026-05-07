import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def price_history_chart(prices: pd.DataFrame, symbol: str):
    if prices.empty:
        return None
    df = prices.copy()
    df["price_date"] = pd.to_datetime(df["price_date"])
    fig = px.line(df, x="price_date", y="close_price", title=f"Historia kursu: {symbol}", markers=True)
    fig.update_layout(xaxis_title="Data", yaxis_title="Cena zamknięcia")
    return fig


def portfolio_value_chart(summary: pd.DataFrame):
    if summary.empty or "current_value" not in summary.columns:
        return None
    df = summary.dropna(subset=["current_value"]).copy()
    if df.empty:
        return None
    fig = px.bar(df, x="symbol", y="current_value", title="Aktualna wartość pozycji w portfelu")
    fig.update_layout(xaxis_title="Walor", yaxis_title="Wartość")
    return fig


def profit_chart(summary: pd.DataFrame):
    if summary.empty or "total_result" not in summary.columns:
        return None
    df = summary.dropna(subset=["total_result"]).copy()
    if df.empty:
        return None
    fig = px.bar(df, x="symbol", y="total_result", title="Wynik inwestycji według walorów")
    fig.update_layout(xaxis_title="Walor", yaxis_title="Zysk / strata")
    return fig


def price_with_average_chart(prices: pd.DataFrame, symbol: str, average_buy_price: float):
    if prices.empty:
        return None
    df = prices.copy()
    df["price_date"] = pd.to_datetime(df["price_date"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["price_date"], y=df["close_price"], mode="lines+markers", name="Kurs"))
    if average_buy_price > 0:
        fig.add_hline(y=average_buy_price, line_dash="dash", annotation_text="Średnia cena zakupu")
    fig.update_layout(title=f"Kurs {symbol} względem średniej ceny zakupu", xaxis_title="Data", yaxis_title="Cena")
    return fig
