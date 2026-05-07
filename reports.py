from __future__ import annotations

from datetime import datetime
from typing import Optional

from calculations import InvestmentMetrics


def money(value: Optional[float]) -> str:
    if value is None:
        return "brak danych"
    return f"{value:,.2f} zł".replace(",", " ").replace(".", ",")


def number(value: Optional[float]) -> str:
    if value is None:
        return "brak danych"
    return f"{value:,.4f}".replace(",", " ").replace(".", ",")


def percent(value: Optional[float]) -> str:
    if value is None:
        return "brak danych"
    return f"{value:.2f}%".replace(".", ",")


def build_investment_report(metrics: InvestmentMetrics, note: str = "") -> str:
    created = datetime.now().strftime("%Y-%m-%d %H:%M")
    result_comment = ""
    if metrics.total_result is None:
        result_comment = "Nie można obliczyć pełnego wyniku, ponieważ nie podano aktualnego kursu lub nie ma danych historycznych."
    elif metrics.total_result > 0:
        result_comment = "Analiza wskazuje dodatni wynik inwestycji przy przyjętym kursie."
    elif metrics.total_result < 0:
        result_comment = "Analiza wskazuje stratę przy przyjętym kursie."
    else:
        result_comment = "Analiza wskazuje wynik neutralny przy przyjętym kursie."

    lines = [
        f"# Raport inwestycji: {metrics.symbol}",
        f"Data wygenerowania: {created}",
        "",
        "## Podsumowanie pozycji",
        f"- Liczba posiadanych jednostek: {number(metrics.owned_quantity)}",
        f"- Łączna liczba kupionych jednostek: {number(metrics.total_buy_quantity)}",
        f"- Łączna liczba sprzedanych jednostek: {number(metrics.total_sell_quantity)}",
        f"- Średnia cena zakupu: {money(metrics.average_buy_price)}",
        f"- Aktualny / przyjęty kurs: {money(metrics.current_price)}",
        f"- Aktualna wartość pozycji: {money(metrics.current_value)}",
        "",
        "## Wynik inwestycji",
        f"- Wartość zakupów: {money(metrics.invested_value)}",
        f"- Wartość sprzedaży: {money(metrics.sold_value)}",
        f"- Suma opłat/prowizji: {money(metrics.fees_total)}",
        f"- Zysk/strata zrealizowana: {money(metrics.realized_profit)}",
        f"- Zysk/strata niezrealizowana: {money(metrics.unrealized_profit)}",
        f"- Wynik całkowity: {money(metrics.total_result)}",
        f"- Stopa zwrotu: {percent(metrics.return_rate_percent)}",
        "",
        "## Porównanie historyczne",
        f"- Cena pierwszego zakupu: {money(metrics.first_buy_price)}",
        f"- Zmiana względem pierwszego zakupu: {percent(metrics.change_vs_first_buy_percent)}",
        "",
        "## Wniosek",
        result_comment,
    ]
    if note.strip():
        lines.extend(["", "## Notatka użytkownika", note.strip()])
    lines.extend([
        "",
        "Uwaga: aplikacja ma charakter informacyjny i edukacyjny. Wyniki nie stanowią rekomendacji inwestycyjnej ani doradztwa finansowego.",
    ])
    return "\n".join(lines)
