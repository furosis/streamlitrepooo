import sqlite3
import json
from pathlib import Path
from typing import Optional, Dict, Any

DB_PATH = Path(__file__).parent / "data" / "app.db"


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            symbol TEXT NOT NULL,
            transaction_type TEXT NOT NULL CHECK(transaction_type IN ('KUPNO', 'SPRZEDAŻ')),
            quantity REAL NOT NULL CHECK(quantity > 0),
            price REAL NOT NULL CHECK(price >= 0),
            fee REAL NOT NULL DEFAULT 0 CHECK(fee >= 0),
            transaction_date TEXT NOT NULL,
            note TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS market_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            price_date TEXT NOT NULL,
            close_price REAL NOT NULL CHECK(close_price >= 0),
            source TEXT NOT NULL DEFAULT 'manual',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(symbol, price_date)
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            symbol TEXT,
            content TEXT NOT NULL,
            metrics_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )

    conn.commit()
    conn.close()


def fetch_dataframe(query: str, params: tuple = ()):  # lazy import keeps database module lightweight
    import pandas as pd

    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def execute(query: str, params: tuple = ()):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    conn.close()
    return last_id


def execute_many(query: str, params_list):
    conn = get_connection()
    cur = conn.cursor()
    cur.executemany(query, params_list)
    conn.commit()
    conn.close()


def add_transaction(user_id: int, symbol: str, transaction_type: str, quantity: float, price: float, fee: float, transaction_date: str, note: str = ""):
    symbol = symbol.strip().upper()
    return execute(
        """
        INSERT INTO transactions (user_id, symbol, transaction_type, quantity, price, fee, transaction_date, note)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (user_id, symbol, transaction_type, quantity, price, fee, transaction_date, note),
    )


def update_transaction(transaction_id: int, user_id: int, symbol: str, transaction_type: str, quantity: float, price: float, fee: float, transaction_date: str, note: str = ""):
    symbol = symbol.strip().upper()
    execute(
        """
        UPDATE transactions
        SET symbol=?, transaction_type=?, quantity=?, price=?, fee=?, transaction_date=?, note=?
        WHERE id=? AND user_id=?
        """,
        (symbol, transaction_type, quantity, price, fee, transaction_date, note, transaction_id, user_id),
    )


def delete_transaction(transaction_id: int, user_id: int):
    execute("DELETE FROM transactions WHERE id=? AND user_id=?", (transaction_id, user_id))


def get_user_transactions(user_id: int, symbol: Optional[str] = None):
    if symbol:
        return fetch_dataframe(
            """
            SELECT id, symbol, transaction_type, quantity, price, fee, transaction_date, note, created_at
            FROM transactions
            WHERE user_id=? AND symbol=?
            ORDER BY transaction_date ASC, id ASC
            """,
            (user_id, symbol.upper()),
        )
    return fetch_dataframe(
        """
        SELECT id, symbol, transaction_type, quantity, price, fee, transaction_date, note, created_at
        FROM transactions
        WHERE user_id=?
        ORDER BY transaction_date ASC, id ASC
        """,
        (user_id,),
    )


def get_symbols_for_user(user_id: int):
    df = fetch_dataframe(
        "SELECT DISTINCT symbol FROM transactions WHERE user_id=? ORDER BY symbol ASC",
        (user_id,),
    )
    return df["symbol"].tolist() if not df.empty else []


def upsert_market_prices(symbol: str, rows, source: str = "manual"):
    symbol = symbol.strip().upper()
    params = [(symbol, str(row["price_date"]), float(row["close_price"]), source) for _, row in rows.iterrows()]
    execute_many(
        """
        INSERT INTO market_prices (symbol, price_date, close_price, source)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(symbol, price_date)
        DO UPDATE SET close_price=excluded.close_price, source=excluded.source
        """,
        params,
    )


def get_market_prices(symbol: str):
    return fetch_dataframe(
        """
        SELECT price_date, close_price, source
        FROM market_prices
        WHERE symbol=?
        ORDER BY price_date ASC
        """,
        (symbol.upper(),),
    )


def get_latest_price(symbol: str) -> Optional[float]:
    df = fetch_dataframe(
        """
        SELECT close_price
        FROM market_prices
        WHERE symbol=?
        ORDER BY price_date DESC
        LIMIT 1
        """,
        (symbol.upper(),),
    )
    if df.empty:
        return None
    return float(df.iloc[0]["close_price"])


def save_report(user_id: int, title: str, symbol: Optional[str], content: str, metrics: Optional[Dict[str, Any]] = None):
    return execute(
        """
        INSERT INTO reports (user_id, title, symbol, content, metrics_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, title, symbol, content, json.dumps(metrics or {}, ensure_ascii=False)),
    )


def get_reports(user_id: int):
    return fetch_dataframe(
        """
        SELECT id, title, symbol, content, metrics_json, created_at
        FROM reports
        WHERE user_id=?
        ORDER BY created_at DESC
        """,
        (user_id,),
    )


def delete_report(report_id: int, user_id: int):
    execute("DELETE FROM reports WHERE id=? AND user_id=?", (report_id, user_id))
