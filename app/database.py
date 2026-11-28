import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "strix_shortener.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    # Enable WAL mode for high concurrency
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def _hash_pwd(password: str) -> str:
    salt = "strix_salt_protect_2026_"
    return hashlib.sha256((salt + password).encode()).hexdigest()

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # 2. URLs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS urls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT NULL,
        short_code TEXT UNIQUE NOT NULL,
        long_url TEXT NOT NULL,
        custom_alias INTEGER DEFAULT 0,
        password_hash TEXT DEFAULT NULL,
        expires_at TEXT DEFAULT NULL,
        transit_mode TEXT DEFAULT 'direct', -- 'direct' or 'safe_transit'
        clicks_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    );
    """)
    
    # Check if user_id column exists in urls (for backward compatibility)
    cursor.execute("PRAGMA table_info(urls);")
    columns = [row["name"] for row in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE urls ADD COLUMN user_id INTEGER DEFAULT NULL REFERENCES users(id) ON DELETE SET NULL;")

    # 3. Clicks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clicks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url_id INTEGER NOT NULL,
        clicked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ip_address TEXT,
        referrer TEXT,
        user_agent TEXT,
        device_type TEXT,
        browser TEXT,
        os TEXT,
        country TEXT,
        FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_code ON urls(short_code);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_urls_user ON urls(user_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_url_id ON clicks(url_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clicks_date ON clicks(clicked_at);")
    
    # Seed or migrate default admin credentials
    admin_email = "ohad@strixshort.com"
    admin_pwd = _hash_pwd("106210hlwfireStrix")
    cursor.execute("SELECT id, email FROM users WHERE is_admin = 1 LIMIT 1")
    existing_admin = cursor.fetchone()
    if not existing_admin:
        cursor.execute("""
            INSERT OR IGNORE INTO users (email, password_hash, full_name, is_admin)
            VALUES (?, ?, ?, 1)
        """, (admin_email, admin_pwd, "System Administrator"))
    elif existing_admin["email"] == "admin@strixshort.com":
        cursor.execute("""
            UPDATE users SET email = ?, password_hash = ? WHERE id = ?
        """, (admin_email, admin_pwd, existing_admin["id"]))
        
    conn.commit()
    conn.close()

# ----------------- User Management -----------------

def create_user(email: str, password_hash: str, full_name: str, is_admin: int = 0) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (email, password_hash, full_name, is_admin)
            VALUES (?, ?, ?, ?)
        """, (email.strip().lower(), password_hash, full_name.strip(), is_admin))
        user_id = cursor.lastrowid
        conn.commit()
        cursor.execute("SELECT id, email, full_name, is_admin, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        conn.close()
        return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, full_name, is_admin, created_at FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_users() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT u.id, u.email, u.full_name, u.is_admin, u.created_at,
               COUNT(urls.id) as link_count,
               COALESCE(SUM(urls.clicks_count), 0) as total_clicks
        FROM users u
        LEFT JOIN urls ON urls.user_id = u.id
        GROUP BY u.id
        ORDER BY u.created_at DESC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# ----------------- URL Management -----------------

def create_url(
    short_code: str,
    long_url: str,
    custom_alias: bool = False,
    password_hash: Optional[str] = None,
    expires_at: Optional[str] = None,
    transit_mode: str = "direct",
    user_id: Optional[int] = None
) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO urls (short_code, long_url, custom_alias, password_hash, expires_at, transit_mode, user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (short_code, long_url, 1 if custom_alias else 0, password_hash, expires_at, transit_mode, user_id))
    url_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM urls WHERE id = ?", (url_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_url_by_code(short_code: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM urls WHERE short_code = ?", (short_code,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_user_urls(user_id: int) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM urls 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    """, (user_id,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_all_urls(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT urls.*, users.email as owner_email, users.full_name as owner_name
        FROM urls
        LEFT JOIN users ON urls.user_id = users.id
        ORDER BY urls.created_at DESC
        LIMIT ? OFFSET ?
    """, (limit, offset))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def delete_url(url_id: int, user_id: Optional[int] = None, is_admin: bool = False) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    if is_admin:
        cursor.execute("DELETE FROM urls WHERE id = ?", (url_id,))
    elif user_id:
        cursor.execute("DELETE FROM urls WHERE id = ? AND user_id = ?", (url_id, user_id))
    else:
        conn.close()
        return False
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def toggle_url_status(url_id: int, user_id: Optional[int] = None, is_admin: bool = False) -> Optional[int]:
    conn = get_connection()
    cursor = conn.cursor()
    if is_admin:
        cursor.execute("SELECT is_active FROM urls WHERE id = ?", (url_id,))
    elif user_id:
        cursor.execute("SELECT is_active FROM urls WHERE id = ? AND user_id = ?", (url_id, user_id))
    else:
        conn.close()
        return None
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
    new_status = 0 if row["is_active"] == 1 else 1
    cursor.execute("UPDATE urls SET is_active = ? WHERE id = ?", (new_status, url_id))
    conn.commit()
    conn.close()
    return new_status

# ----------------- Analytics & Tracking -----------------

def record_click(url_id: int, ip: str, referrer: str, user_agent: str, device: str, browser: str, os_name: str, country: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE urls SET clicks_count = clicks_count + 1 WHERE id = ?", (url_id,))
    cursor.execute("""
        INSERT INTO clicks (url_id, ip_address, referrer, user_agent, device_type, browser, os, country)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (url_id, ip, referrer, user_agent, device, browser, os_name, country))
    conn.commit()
    conn.close()

def get_url_analytics(url_id: int) -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM urls WHERE id = ?", (url_id,))
    url_info = cursor.fetchone()
    if not url_info:
        conn.close()
        return {}
    
    cursor.execute("""
        SELECT COALESCE(device_type, 'Desktop') as device, COUNT(*) as count 
        FROM clicks WHERE url_id = ? 
        GROUP BY device_type ORDER BY count DESC
    """, (url_id,))
    devices = [{"device": r["device"], "count": r["count"]} for r in cursor.fetchall()]
    
    cursor.execute("""
        SELECT COALESCE(browser, 'Unknown') as browser, COUNT(*) as count 
        FROM clicks WHERE url_id = ? 
        GROUP BY browser ORDER BY count DESC LIMIT 5
    """, (url_id,))
    browsers = [{"browser": r["browser"], "count": r["count"]} for r in cursor.fetchall()]
    
    cursor.execute("""
        SELECT COALESCE(os, 'Unknown') as os_name, COUNT(*) as count 
        FROM clicks WHERE url_id = ? 
        GROUP BY os ORDER BY count DESC LIMIT 5
    """, (url_id,))
    operating_systems = [{"os": r["os_name"], "count": r["count"]} for r in cursor.fetchall()]
    
    cursor.execute("""
        SELECT CASE 
            WHEN referrer IS NULL OR referrer = '' THEN 'Direct / Email' 
            ELSE referrer 
        END as source, COUNT(*) as count 
        FROM clicks WHERE url_id = ? 
        GROUP BY source ORDER BY count DESC LIMIT 6
    """, (url_id,))
    referrers = [{"source": r["source"], "count": r["count"]} for r in cursor.fetchall()]
    
    cursor.execute("""
        SELECT clicked_at, country, device_type, browser, referrer 
        FROM clicks WHERE url_id = ? 
        ORDER BY clicked_at DESC LIMIT 10
    """, (url_id,))
    recent_clicks = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return {
        "url": dict(url_info),
        "devices": devices,
        "browsers": browsers,
        "operating_systems": operating_systems,
        "referrers": referrers,
        "recent_clicks": recent_clicks
    }

def get_platform_stats() -> Dict[str, int]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_links, COALESCE(SUM(clicks_count), 0) as total_clicks FROM urls")
    row = cursor.fetchone()
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    u_row = cursor.fetchone()
    conn.close()
    return {
        "total_links": row["total_links"] if row else 0,
        "total_clicks": row["total_clicks"] if row else 0,
        "total_users": u_row["total_users"] if u_row else 0
    }

def get_admin_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()["total_users"]
    
    cursor.execute("SELECT COUNT(*) as total_links, COALESCE(SUM(clicks_count), 0) as total_clicks FROM urls")
    link_data = cursor.fetchone()
    
    cursor.execute("SELECT COUNT(*) as active_links FROM urls WHERE is_active = 1")
    active_links = cursor.fetchone()["active_links"]
    
    cursor.execute("SELECT COUNT(*) as clicks_today FROM clicks WHERE DATE(clicked_at) = DATE('now')")
    clicks_today = cursor.fetchone()["clicks_today"]
    
    conn.close()
    return {
        "total_users": total_users,
        "total_links": link_data["total_links"] if link_data else 0,
        "total_clicks": link_data["total_clicks"] if link_data else 0,
        "active_links": active_links,
        "clicks_today": clicks_today
    }
