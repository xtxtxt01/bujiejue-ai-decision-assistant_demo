import sqlite3
import os
from config import DB_PATH


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT,
            nickname TEXT,
            mbti TEXT,
            decision_style TEXT,
            maximizer_tendency TEXT DEFAULT '',
            values_ranking TEXT,
            life_stage TEXT,
            frequent_dilemma_types TEXT,
            self_intro TEXT DEFAULT '',
            theme TEXT DEFAULT 'default',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY,
            uid TEXT NOT NULL,
            title TEXT DEFAULT '',
            dilemma_type TEXT,
            core_conflict TEXT DEFAULT '',
            trigger_event TEXT DEFAULT '',
            main_concern TEXT DEFAULT '',
            status TEXT DEFAULT 'active',
            decision_result TEXT DEFAULT '',
            decision_reason TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP,
            FOREIGN KEY (uid) REFERENCES users(uid)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            card_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (card_id) REFERENCES cards(id)
        );

        CREATE TABLE IF NOT EXISTS memory_facts (
            id TEXT PRIMARY KEY,
            uid TEXT NOT NULL,
            fact_type TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT DEFAULT '',
            source_card_id TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (uid) REFERENCES users(uid)
        );

        CREATE TABLE IF NOT EXISTS decision_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_type TEXT NOT NULL,
            title TEXT NOT NULL,
            background TEXT NOT NULL,
            core_conflict TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            final_choice TEXT NOT NULL,
            turning_point TEXT NOT NULL,
            retrospect TEXT NOT NULL,
            retrospect_score INTEGER NOT NULL,
            retrospect_months INTEGER DEFAULT 3,
            decision_style TEXT DEFAULT '',
            life_stage TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            empathy_count INTEGER DEFAULT 0,
            view_count INTEGER DEFAULT 0,
            is_featured INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CHECK (retrospect_score >= 1 AND retrospect_score <= 10),
            CHECK (duration_days > 0)
        );
    """)
    # 兼容旧数据库：如果 users 表缺少 username 列，重建表
    cols = [row[1] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "username" not in cols:
        conn.executescript("""
            DROP TABLE IF EXISTS users;
            CREATE TABLE users (
                uid TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT,
                nickname TEXT,
                mbti TEXT,
                decision_style TEXT,
                maximizer_tendency TEXT DEFAULT '',
                values_ranking TEXT,
                life_stage TEXT,
                frequent_dilemma_types TEXT,
                self_intro TEXT DEFAULT '',
                theme TEXT DEFAULT 'default',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
    else:
        _migrate_add_column(conn, "users", "maximizer_tendency", "TEXT DEFAULT ''")
        _migrate_add_column(conn, "users", "self_intro", "TEXT DEFAULT ''")
        _migrate_add_column(conn, "users", "theme", "TEXT DEFAULT 'default'")
    _migrate_add_column(conn, "cards", "insight", "TEXT DEFAULT ''")
    _migrate_add_column(conn, "cards", "current_tendency", "TEXT DEFAULT ''")
    _migrate_add_column(conn, "cards", "shared_case_id", "INTEGER DEFAULT NULL")
    _migrate_add_column(conn, "cards", "context_summary", "TEXT DEFAULT ''")
    _migrate_add_column(conn, "cards", "context_summary_length", "INTEGER DEFAULT 0")
    _migrate_add_column(conn, "decision_cases", "source_card_id", "TEXT DEFAULT ''")
    _migrate_add_column(conn, "decision_cases", "is_user_contributed", "INTEGER DEFAULT 0")

    # decision_cases 索引
    conn.executescript("""
        CREATE INDEX IF NOT EXISTS idx_cases_type ON decision_cases(case_type);
        CREATE INDEX IF NOT EXISTS idx_cases_style ON decision_cases(decision_style);
        CREATE INDEX IF NOT EXISTS idx_cases_created ON decision_cases(created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_cases_deleted ON decision_cases(is_deleted);
    """)

    conn.commit()
    conn.close()


def _migrate_add_column(conn, table, column, col_type):
    """安全地给表添加列，已存在则忽略"""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    except sqlite3.OperationalError:
        pass


if __name__ == "__main__":
    init_db()
    print("Database initialized.")


