import json
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

from auth import create_user, authenticate, change_username, change_password
from database import (
    init_db,
    add_transaction,
    update_transaction,
    delete_transaction,
    get_user_transactions,
    get_symbols_for_user,
    upsert_market_prices,
    get_market_prices,
    get_latest_price,
    save_report,
    get_reports,
    delete_report,
)
from calculations import calculate_metrics, build_portfolio_summary, generate_demo_prices
from charts import price_history_chart, portfolio_value_chart, profit_chart, price_with_average_chart
from reports import build_investment_report, money, number, percent

APP_TITLE = "Aplikacja wspomagająca inwestycje giełdowe"


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_css():
    st.markdown(
        """
        <style>
        .main .block-container {padding-top: 1.4rem;}
        .app-header {
            padding: 1.2rem 1.4rem;
            border-radius: 18px;
            background: linear-gradient(135deg, #0b1f3a 0%, #123c69 100%);
            color: white;
            margin-bottom: 1.2rem;
        }
        .app-header h1 {margin: 0; font-size: 2rem;}
        .app-header p {margin: .4rem 0 0 0; opacity: .92;}
        .metric-card {
            padding: 1rem;
            border: 1px solid #e7eaf0;
            border-radius: 16px;
            background: #ffffff;
            box-shadow: 0 3px 12px rgba(15, 23, 42, 0.06);
        }
        .small-muted {font-size: .88rem; color: #667085;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def header(subtitle: str = "System do analizy portfela, transakcji, raportów i danych historycznych."):
    st.markdown(
        f"""
        <div class="app-header">
            <h1>{APP_TITLE}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def format_df_money(df: pd.DataFrame, cols):
    out = df.copy()
    for col in cols:
        if col in out.columns:
            out[col] = out[col].apply(lambda x: money(x) if pd.notna(x) else "brak danych")
    return out


def require_login():
    if "user" not in st.session_state:
        st.session_state.user = None
    return st.session_state.user is not None


def login_page():
    header("Zaloguj się lub utwórz konto, aby zapisywać własne transakcje i raporty.")
    tab_login, tab_register = st.tabs(["Logowanie", "Rejestracja"])

    with tab_login:
        with st.form("login_form"):
            username = st.text_input("Nazwa użytkownika")
            password = st.text_input("Hasło", type="password")
            submitted = st.form_submit_button("Zaloguj")
            if submitted:
                user = authenticate(username, password)
                if user:
                    st.session_state.user = user
                    st.success("Zalogowano pomyślnie.")
                    st.rerun()
                else:
                    st.error("Nieprawidłowa nazwa użytkownika lub hasło.")

    with tab_register:
        with st.form("register_form"):
            username = st.text_input("Nazwa użytkownika", key="reg_username")
            password = st.text_input("Hasło", type="password", key="reg_password")
            password2 = st.text_input("Powtórz hasło", type="password", key="reg_password2")
            submitted = st.form_submit_button("Utwórz konto")
            if submitted:
                if password != password2:
                    st.error("Hasła nie są takie same.")
                else:
                    try:
                        user_id = create_user(username, password)
                        st.session_state.user = {"id": user_id, "username": username.strip()}
                        st.success("Konto zostało utworzone.")
                        st.rerun()
                    except ValueError as exc:
                        st.error(str(exc))


def sidebar_menu():
    user = st.session_state.user
    st.sidebar.title("📊 Menu")
    st.sidebar.caption(f"Zalogowano jako: **{user['username']}**")
    page = st.sidebar.radio(
        "Wybierz widok",
        [
            "Dashboard",
            "Transakcje",
            "Analiza inwestycji",
            "Dane historyczne",
            "Raporty",
            "Profil",
            "O projekcie",
        ],
    )
    st.sidebar.divider()
    if st.sidebar.button("Wyloguj"):
        st.session_state.user = None
        st.rerun()
    return page


def page_dashboard(user_id: int):
    header("Dashboard portfela użytkownika — podsumowanie pozycji, wartości i wyniku.")
    transactions = get_user_transactions(user_id)
    symbols = get_symbols_for_user(user_id)

    if transactions.empty:
        st.info("Nie dodano jeszcze żadnych transakcji. Zacznij od zakładki „Transakcje”.")
        return

    latest_prices = {symbol: get_latest_price(symbol) for symbol in symbols}
    summary = build_portfolio_summary(transactions, latest_prices)

    total_value = summary["current_value"].dropna().sum() if "current_value" in summary else 0
    total_result = summary["total_result"].dropna().sum() if "total_result" in summary else 0
    instruments_count = len(symbols)
    reports_count = len(get_reports(user_id))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Liczba walorów", instruments_count)
    c2.metric("Wartość portfela", money(total_value))
    c3.metric("Wynik łączny", money(total_result))
    c4.metric("Zapisane raporty", reports_count)

    st.subheader("Podsumowanie portfela")
    display = format_df_money(summary, ["average_buy_price", "current_price", "current_value", "unrealized_profit", "realized_profit", "total_result"])
    display = display.rename(
        columns={
            "symbol": "Walor",
            "owned_quantity": "Posiadane jednostki",
            "average_buy_price": "Średnia cena zakupu",
            "current_price": "Aktualny kurs",
            "current_value": "Aktualna wartość",
            "unrealized_profit": "Zysk/strata niezrealizowana",
            "realized_profit": "Zysk/strata zrealizowana",
            "total_result": "Wynik całkowity",
            "return_rate_percent": "Stopa zwrotu %",
        }
    )
    if "Stopa zwrotu %" in display:
        display["Stopa zwrotu %"] = summary["return_rate_percent"].apply(lambda x: percent(x) if pd.notna(x) else "brak danych")
    st.dataframe(display, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        fig = portfolio_value_chart(summary)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Brak aktualnych kursów. Dodaj dane historyczne, aby zobaczyć wykres wartości.")
    with c2:
        fig = profit_chart(summary)
        if fig:
            st.plotly_chart(fig, use_container_width=True)


def page_transactions(user_id: int):
    header("Rejestr transakcji — dodawanie, przegląd, edycja i usuwanie operacji.")

    with st.expander("➕ Dodaj nową transakcję", expanded=True):
        with st.form("add_transaction_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            symbol = c1.text_input("Symbol waloru", placeholder="np. PKO, KGH, ALE")
            transaction_type = c2.selectbox("Typ transakcji", ["KUPNO", "SPRZEDAŻ"])
            transaction_date = c3.date_input("Data transakcji", value=date.today())

            c4, c5, c6 = st.columns(3)
            quantity = c4.number_input("Liczba jednostek", min_value=0.0001, step=1.0, format="%.4f")
            price = c5.number_input("Cena jednostkowa", min_value=0.0, step=0.01, format="%.2f")
            fee = c6.number_input("Prowizja / opłata", min_value=0.0, step=0.01, format="%.2f")
            note = st.text_area("Notatka", placeholder="Opcjonalnie")
            submitted = st.form_submit_button("Zapisz transakcję")
            if submitted:
                if not symbol.strip():
                    st.error("Podaj symbol waloru.")
                elif price <= 0:
                    st.error("Cena musi być większa od 0.")
                else:
                    add_transaction(user_id, symbol, transaction_type, quantity, price, fee, str(transaction_date), note)
                    st.success("Transakcja została zapisana.")
                    st.rerun()

    st.subheader("Historia transakcji")
    transactions = get_user_transactions(user_id)
    if transactions.empty:
        st.info("Brak zapisanych transakcji.")
        return

    symbols = ["Wszystkie"] + sorted(transactions["symbol"].unique().tolist())
    selected = st.selectbox("Filtruj po walorze", symbols)
    filtered = transactions if selected == "Wszystkie" else transactions[transactions["symbol"] == selected]

    display = filtered.copy()
    display = display.rename(
        columns={
            "id": "ID",
            "symbol": "Walor",
            "transaction_type": "Typ",
            "quantity": "Liczba",
            "price": "Cena",
            "fee": "Prowizja",
            "transaction_date": "Data",
            "note": "Notatka",
        }
    )
    st.dataframe(display[["ID", "Walor", "Typ", "Liczba", "Cena", "Prowizja", "Data", "Notatka"]], use_container_width=True, hide_index=True)

    with st.expander("✏️ Edytuj lub usuń transakcję"):
        transaction_ids = filtered["id"].tolist()
        selected_id = st.selectbox("Wybierz ID transakcji", transaction_ids)
        row = filtered[filtered["id"] == selected_id].iloc[0]

        with st.form("edit_transaction_form"):
            c1, c2, c3 = st.columns(3)
            new_symbol = c1.text_input("Symbol", value=row["symbol"])
            new_type = c2.selectbox("Typ", ["KUPNO", "SPRZEDAŻ"], index=0 if row["transaction_type"] == "KUPNO" else 1)
            new_date = c3.date_input("Data", value=pd.to_datetime(row["transaction_date"]).date())
            c4, c5, c6 = st.columns(3)
            new_quantity = c4.number_input("Liczba jednostek", value=float(row["quantity"]), min_value=0.0001, step=1.0, format="%.4f")
            new_price = c5.number_input("Cena", value=float(row["price"]), min_value=0.0, step=0.01, format="%.2f")
            new_fee = c6.number_input("Prowizja", value=float(row["fee"]), min_value=0.0, step=0.01, format="%.2f")
            new_note = st.text_area("Notatka", value=row["note"] or "")
            c_save, c_delete = st.columns(2)
            save_clicked = c_save.form_submit_button("Zapisz zmiany")
            delete_clicked = c_delete.form_submit_button("Usuń transakcję")

            if save_clicked:
                update_transaction(selected_id, user_id, new_symbol, new_type, new_quantity, new_price, new_fee, str(new_date), new_note)
                st.success("Transakcja została zaktualizowana.")
                st.rerun()
            if delete_clicked:
                delete_transaction(selected_id, user_id)
                st.warning("Transakcja została usunięta.")
                st.rerun()

    csv = filtered.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Pobierz transakcje CSV", csv, "transakcje.csv", "text/csv")


def page_analysis(user_id: int):
    header("Analiza inwestycji — średnia cena zakupu, zysk/strata, raport i wykres.")
    symbols = get_symbols_for_user(user_id)
    if not symbols:
        st.info("Najpierw dodaj transakcję w zakładce „Transakcje”.")
        return

    c1, c2 = st.columns([1, 1])
    symbol = c1.selectbox("Wybierz walor", symbols)
    latest = get_latest_price(symbol)
    default_price = float(latest) if latest else 0.0
    manual_price = c2.number_input(
        "Aktualny / zakładany kurs sprzedaży",
        min_value=0.0,
        value=default_price,
        step=0.01,
        format="%.2f",
        help="Możesz wpisać aktualny kurs albo hipotetyczną cenę sprzedaży.",
    )
    current_price = manual_price if manual_price > 0 else latest

    transactions = get_user_transactions(user_id, symbol)
    metrics = calculate_metrics(transactions, symbol, current_price)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Średnia cena zakupu", money(metrics.average_buy_price))
    c2.metric("Posiadane jednostki", number(metrics.owned_quantity))
    c3.metric("Wartość pozycji", money(metrics.current_value))
    c4.metric("Wynik całkowity", money(metrics.total_result))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Zysk/strata zrealizowana", money(metrics.realized_profit))
    c6.metric("Zysk/strata niezrealizowana", money(metrics.unrealized_profit))
    c7.metric("Stopa zwrotu", percent(metrics.return_rate_percent))
    c8.metric("Zmiana od pierwszego zakupu", percent(metrics.change_vs_first_buy_percent))

    prices = get_market_prices(symbol)
    fig = price_with_average_chart(prices, symbol, metrics.average_buy_price)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Brak danych historycznych dla wybranego waloru. Dodaj je w zakładce „Dane historyczne”.")

    st.subheader("Raport z analizy")
    note = st.text_area("Notatka do raportu", placeholder="Opcjonalny komentarz użytkownika")
    report_text = build_investment_report(metrics, note)
    st.markdown(report_text)

    c1, c2 = st.columns(2)
    if c1.button("💾 Zapisz raport do historii"):
        title = f"Raport {symbol} — {date.today().isoformat()}"
        save_report(user_id, title, symbol, report_text, metrics.as_dict())
        st.success("Raport został zapisany.")
    c2.download_button("⬇️ Pobierz raport TXT/MD", report_text.encode("utf-8"), f"raport_{symbol}.md", "text/markdown")


def page_market_data(user_id: int):
    header("Dane historyczne — ręczne dodawanie, import CSV i dane demonstracyjne.")
    symbols = get_symbols_for_user(user_id)
    typed_symbol = st.text_input("Symbol waloru", value=symbols[0] if symbols else "", placeholder="np. PKO")
    symbol = typed_symbol.strip().upper()

    if not symbol:
        st.info("Podaj symbol waloru, dla którego chcesz dodać dane historyczne.")
        return

    tab_manual, tab_csv, tab_demo, tab_preview = st.tabs(["Dodaj ręcznie", "Import CSV", "Wygeneruj demo", "Podgląd danych"])

    with tab_manual:
        with st.form("manual_price_form"):
            c1, c2 = st.columns(2)
            price_date = c1.date_input("Data notowania", value=date.today())
            close_price = c2.number_input("Cena zamknięcia", min_value=0.0, step=0.01, format="%.2f")
            submitted = st.form_submit_button("Zapisz notowanie")
            if submitted:
                if close_price <= 0:
                    st.error("Cena musi być większa od 0.")
                else:
                    df = pd.DataFrame([{"price_date": str(price_date), "close_price": close_price}])
                    upsert_market_prices(symbol, df, "manual")
                    st.success("Notowanie zostało zapisane.")
                    st.rerun()

    with tab_csv:
        st.write("CSV powinien mieć kolumny: `price_date`, `close_price`. Przykład daty: `2026-03-15`.")
        file = st.file_uploader("Wgraj plik CSV", type=["csv"])
        if file is not None:
            try:
                df = pd.read_csv(file)
                required = {"price_date", "close_price"}
                if not required.issubset(df.columns):
                    st.error("Plik musi zawierać kolumny price_date oraz close_price.")
                else:
                    df = df[["price_date", "close_price"]].copy()
                    df["price_date"] = pd.to_datetime(df["price_date"]).dt.strftime("%Y-%m-%d")
                    df["close_price"] = pd.to_numeric(df["close_price"], errors="coerce")
                    df = df.dropna()
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    if st.button("Zaimportuj dane CSV"):
                        upsert_market_prices(symbol, df, "csv")
                        st.success(f"Zaimportowano {len(df)} rekordów.")
                        st.rerun()
            except Exception as exc:
                st.error(f"Nie udało się odczytać CSV: {exc}")

    with tab_demo:
        st.write("Generator tworzy przykładowe dane historyczne do testów i prezentacji projektu.")
        c1, c2, c3 = st.columns(3)
        start = c1.date_input("Data początkowa", value=date.today() - timedelta(days=60), key="demo_start")
        end = c2.date_input("Data końcowa", value=date.today(), key="demo_end")
        start_price = c3.number_input("Cena startowa", min_value=0.01, value=100.0, step=1.0)
        if st.button("Wygeneruj i zapisz dane demo"):
            demo = generate_demo_prices(symbol, start, end, start_price)
            upsert_market_prices(symbol, demo, "demo")
            st.success(f"Wygenerowano {len(demo)} rekordów danych demo.")
            st.rerun()

    with tab_preview:
        prices = get_market_prices(symbol)
        if prices.empty:
            st.info("Brak danych historycznych dla tego waloru.")
        else:
            st.dataframe(prices, use_container_width=True, hide_index=True)
            fig = price_history_chart(prices, symbol)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
            csv = prices.to_csv(index=False).encode("utf-8-sig")
            st.download_button("⬇️ Pobierz dane historyczne CSV", csv, f"dane_historyczne_{symbol}.csv", "text/csv")


def page_reports(user_id: int):
    header("Historia raportów — przegląd, pobieranie i usuwanie zapisanych analiz.")
    reports = get_reports(user_id)
    if reports.empty:
        st.info("Brak zapisanych raportów. Wygeneruj raport w zakładce „Analiza inwestycji”.")
        return

    display = reports[["id", "title", "symbol", "created_at"]].rename(
        columns={"id": "ID", "title": "Tytuł", "symbol": "Walor", "created_at": "Data utworzenia"}
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    selected_id = st.selectbox("Wybierz raport", reports["id"].tolist())
    row = reports[reports["id"] == selected_id].iloc[0]
    st.subheader(row["title"])
    st.markdown(row["content"])

    c1, c2 = st.columns(2)
    c1.download_button("⬇️ Pobierz raport", row["content"].encode("utf-8"), f"raport_{selected_id}.md", "text/markdown")
    if c2.button("🗑️ Usuń raport"):
        delete_report(int(selected_id), user_id)
        st.warning("Raport został usunięty.")
        st.rerun()


def page_profile(user_id: int):
    header("Profil użytkownika — zmiana nazwy użytkownika i hasła.")
    user = st.session_state.user

    with st.form("username_form"):
        new_username = st.text_input("Nowa nazwa użytkownika", value=user["username"])
        submitted = st.form_submit_button("Zmień nazwę")
        if submitted:
            try:
                change_username(user_id, new_username)
                st.session_state.user["username"] = new_username.strip()
                st.success("Nazwa użytkownika została zmieniona.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    with st.form("password_form"):
        old_password = st.text_input("Obecne hasło", type="password")
        new_password = st.text_input("Nowe hasło", type="password")
        new_password2 = st.text_input("Powtórz nowe hasło", type="password")
        submitted = st.form_submit_button("Zmień hasło")
        if submitted:
            if new_password != new_password2:
                st.error("Nowe hasła nie są takie same.")
            else:
                try:
                    change_password(user_id, old_password, new_password)
                    st.success("Hasło zostało zmienione.")
                except ValueError as exc:
                    st.error(str(exc))


def page_about():
    header("Informacje o projekcie i zgodność ze specyfikacją SRS.")
    st.markdown(
        """
        Aplikacja została przygotowana jako prototyp systemu wspomagającego analizę inwestycji giełdowych.

        **Zakres funkcjonalny:**
        - rejestracja i logowanie użytkownika,
        - zarządzanie transakcjami kupna i sprzedaży,
        - przegląd portfela inwestycyjnego,
        - dodawanie i import danych historycznych,
        - obliczanie średniej ceny zakupu, wartości pozycji oraz zysku lub straty,
        - generowanie raportów i zapis historii raportów,
        - prezentacja danych w tabelach i na wykresach,
        - eksport danych do plików CSV oraz raportów Markdown/TXT.

        **Technologie:** Python, Streamlit, SQLite, pandas, Plotly.

        System ma charakter edukacyjny i informacyjny. Nie wykonuje rzeczywistych transakcji giełdowych i nie stanowi doradztwa inwestycyjnego.
        """
    )


def main():
    inject_css()
    init_db()
    if not require_login():
        login_page()
        return

    page = sidebar_menu()
    user_id = st.session_state.user["id"]

    if page == "Dashboard":
        page_dashboard(user_id)
    elif page == "Transakcje":
        page_transactions(user_id)
    elif page == "Analiza inwestycji":
        page_analysis(user_id)
    elif page == "Dane historyczne":
        page_market_data(user_id)
    elif page == "Raporty":
        page_reports(user_id)
    elif page == "Profil":
        page_profile(user_id)
    elif page == "O projekcie":
        page_about()


if __name__ == "__main__":
    main()
