import os
import hashlib
import hmac
import sqlite3
from typing import Optional, Dict

from database import get_connection, execute


def _hash_password(password: str, salt: Optional[bytes] = None) -> str:
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return salt.hex() + ":" + digest.hex()


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        salt_hex, digest_hex = password_hash.split(":")
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def create_user(username: str, password: str):
    username = username.strip()
    if len(username) < 3:
        raise ValueError("Nazwa użytkownika musi mieć minimum 3 znaki.")
    if len(password) < 6:
        raise ValueError("Hasło musi mieć minimum 6 znaków.")
    password_hash = _hash_password(password)
    try:
        user_id = execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        return user_id
    except sqlite3.IntegrityError:
        raise ValueError("Użytkownik o takiej nazwie już istnieje.")


def authenticate(username: str, password: str) -> Optional[Dict]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username=?", (username.strip(),))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    if not _verify_password(password, row["password_hash"]):
        return None
    return {"id": row["id"], "username": row["username"]}


def change_username(user_id: int, new_username: str):
    new_username = new_username.strip()
    if len(new_username) < 3:
        raise ValueError("Nowa nazwa użytkownika musi mieć minimum 3 znaki.")
    try:
        execute("UPDATE users SET username=? WHERE id=?", (new_username, user_id))
    except sqlite3.IntegrityError:
        raise ValueError("Ta nazwa użytkownika jest już zajęta.")


def change_password(user_id: int, old_password: str, new_password: str):
    if len(new_password) < 6:
        raise ValueError("Nowe hasło musi mieć minimum 6 znaków.")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or not _verify_password(old_password, row["password_hash"]):
        raise ValueError("Obecne hasło jest nieprawidłowe.")
    execute("UPDATE users SET password_hash=? WHERE id=?", (_hash_password(new_password), user_id))
