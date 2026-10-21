"""Durable intent before broker write, plus a process-lifetime OS lock."""
import json
import os
import sqlite3
from pathlib import Path


class FileLock:
    def __init__(self, path):
        self.path, self.handle = Path(path), None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        self.handle = os.fdopen(fd, 'r+b')
        try:
            if os.name == 'nt':
                import msvcrt
                if os.fstat(fd).st_size == 0:
                    self.handle.write(b'0')
                    self.handle.flush()
                self.handle.seek(0)
                msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def __exit__(self, *_):
        if self.handle is not None:
            self.handle.close()
            self.handle = None


class Journal:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = FileLock(str(self.path) + '.lock')
        self.db = None

    def __enter__(self):
        self.lock.__enter__()
        try:
            self.db = sqlite3.connect(self.path, timeout=0, isolation_level=None)
            os.chmod(self.path, 0o600)
            self.db.execute('PRAGMA synchronous=FULL')
            self.db.execute('CREATE TABLE IF NOT EXISTS journal (id INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
            return self
        except BaseException:
            self.__exit__(None, None, None)
            raise

    def load(self):
        row = self.db.execute('SELECT payload FROM journal WHERE id=1').fetchone()
        return json.loads(row[0]) if row else None

    def save(self, payload):
        value = json.dumps(payload, default=str, allow_nan=False, sort_keys=True)
        self.db.execute('INSERT INTO journal VALUES (1, ?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',
                        (value,))

    def __exit__(self, *_):
        if self.db is not None:
            self.db.close()
            self.db = None
        self.lock.__exit__(None, None, None)
