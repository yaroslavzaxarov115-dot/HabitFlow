"""
Модуль работы с базой данных SQLite.

Этот файл — ЕДИНСТВЕННОЕ место в проекте, где есть SQL-запросы.
"""

import sqlite3
import os
from datetime import datetime

# УДАЛЯЕМ БАЗУ ПРИ КАЖДОМ ЗАПУСКЕ 
_db_check = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "test_habits.db"
)
if os.path.exists(_db_check):
    os.remove(_db_check)
    print(f"[HACK] Удалил старую базу: {_db_check}")
#конец удаления


class Database:
    """
    Класс для работы с базой данных SQLite.
    """

    def __init__(self, db_path=None):
        """
        Конструктор.
        Если db_path не указан — используется data/habits.db в корне проекта.
        """
        if db_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, "data", "habits.db")

        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._create_tables()

    def _connect(self):
        """Открывает соединение с базой."""
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        """Создает таблицы, если их нет."""
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS marks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                FOREIGN KEY (habit_id) REFERENCES habits(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        conn.close()

    # ============================================================
    #                    ОПЕРАЦИИ С ПРИВЫЧКАМИ
    # ============================================================

    def add_habit(self, name):
        """Добавляет привычку, возвращает её ID."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO habits (name, created_at) VALUES (?, ?)",
            (name, datetime.now().strftime("%Y-%m-%d"))
        )
        habit_id = cur.lastrowid
        conn.commit()
        conn.close()
        return habit_id

    def get_all_habits(self):
        """Возвращает список всех привычек [(id, name, created_at), ...]."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT id, name, created_at FROM habits ORDER BY id")
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_habit(self, habit_id):
        """Возвращает одну привычку по ID."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, created_at FROM habits WHERE id=?",
            (habit_id,)
        )
        row = cur.fetchone()
        conn.close()
        return row

    def delete_habit(self, habit_id):
        """Удаляет привычку и все её отметки."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("DELETE FROM marks WHERE habit_id=?", (habit_id,))
        cur.execute("DELETE FROM habits WHERE id=?", (habit_id,))
        conn.commit()
        conn.close()

    # ============================================================
    #                     ОПЕРАЦИИ С ОТМЕТКАМИ
    # ============================================================

    def add_mark(self, habit_id, date=None):
        """
        Добавляет отметку. Если на эту дату уже есть — возвращает False.
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = self._connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT id FROM marks WHERE habit_id=? AND date=?",
            (habit_id, date)
        )
        if cur.fetchone():
            conn.close()
            return False

        cur.execute(
            "INSERT INTO marks (habit_id, date) VALUES (?, ?)",
            (habit_id, date)
        )
        conn.commit()
        conn.close()
        return True

    def get_marks(self, habit_id):
        """Возвращает список дат отметок (по убыванию)."""
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "SELECT date FROM marks WHERE habit_id=? ORDER BY date DESC",
            (habit_id,)
        )
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def count_marks(self, habit_id, days=None):
        """Считает количество отметок (за всё время или за N дней)."""
        conn = self._connect()
        cur = conn.cursor()

        if days is None:
            cur.execute("SELECT COUNT(*) FROM marks WHERE habit_id=?", (habit_id,))
        else:
            cur.execute(
                "SELECT COUNT(*) FROM marks WHERE habit_id=? AND date >= date('now', ?)",
                (habit_id, f"-{days} days")
            )

        count = cur.fetchone()[0]
        conn.close()
        return count

    # Тестовый блок — срабатывает только при запуске файла напрямую.
if __name__ == "__main__":
    print("Тестирование класса Database...")

    project_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(project_root)
    test_db_path = os.path.join(project_root, "data", "test_habits.db")

    print(f"База будет создана тут: {test_db_path}")

    db = Database(test_db_path)

    # Проверка структуры
    conn = sqlite3.connect(test_db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(marks)")
    print("\nСтолбцы в таблице marks:")
    for row in cur.fetchall():
        print("  ", row)
    conn.close()

    # Тесты
    hid = db.add_habit("Тестовая привычка")
    print(f"\nСоздана привычка с id={hid}")
    print(f"Все привычки: {db.get_all_habits()}")

    result = db.add_mark(hid)
    print(f"Отметка добавлена: {result}")

    result = db.add_mark(hid)
    print(f"Повторная отметка: {result}")

    print(f"Всего отметок: {db.count_marks(hid)}")
    print("\nТест завершен.")