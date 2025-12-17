# db/__init__.py

import sqlite3
from utils.config import load_config

# Import the writer thread starter
from .writer import start_db_writer

# Import the enqueue function from db.py
from database import execute as writer_execute



_write_queue_started = False


def init_db_writer():
    """
    Ensure the DB writer thread is started exactly once.
    """
    global _write_queue_started
    if not _write_queue_started:
        start_db_writer()
        _write_queue_started = True
    return _write_queue_started


def execute(sql, params=None):
    """
    Public write API.
    Enqueues SQL for the writer thread.
    """
    if params is None:
        params = ()

    init_db_writer()
    writer_execute(sql, params)


def query(sql, params=None):
    """
    Read-only DB query helper.
    """
    if params is None:
        params = ()

    config = load_config()
    db_path = config["database"]["path"]

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()
