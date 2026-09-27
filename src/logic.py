from src.database import Database
from src.models import Habit

class HabitManager:     # управление привычками, загрузка, создание отметки и статистика
    def __init__(self, db=None):
        self.db = db if db is not None else Database()
        self.habits = []
        self.load()

    def load(self):     # загрузка привычки из базы данных и создаёт привычку
        self.habits = []
        rows = self.db.get_all_habits()

        for habit_id, name, created_at in rows:
            marks = self.db.get_marks(habit_id)
            habit = Habit(
                id = habit_id,
                name = name,
                created_at = created_at,
                marks=marks
            )
            self.habits.append(habit)

    def add_habit(self, name):      # добавляет привычку, возвращает её или ничего
        name = name.strip()
        if not name:
            return None

        habit_id = self.db.add_habit(name)
        habit = Habit(
            id=habit_id,
            name=name,
            created_at=self._today(),
            marks=[]
        )
        self.habits.append(habit)
        return habit

    def delete_habit(self, habit_id):       # удаляет привычку из базы данных и из памяти
        self.db.delete_habit(habit_id)
        self.habits = [h for h in self.habits if h.id != habit_id]
        return True

    def mark_habit(self, habit_id):         # Отмечает выполнение сегодня. (если отмечено ничего не делаем
        success = self.db.add_mark(habit_id)
        if not success:
            return False
        habit = self.get_habit(habit_id)
        if habit:
            today = self._today()
            if today not in habit.marks:
                habit.marks.append(today)
        return True

    def get_habit(self, habit_id):      # находит привычку по id или None
        for h in self.habits:
            if h.id == habit_id:
                return h
        return None

    def get_all(self):      # возращает список всех привычек
        return self.habits

    def get_stats(self, habit_id):      # статистика по привычке (словарь) или None
        habit = self.get_habit(habit_id)
        if habit is None:
            return None
        return {
            "name": habit.name,
            "streak": habit.streak,
            "percent": habit.percent_30_days,
            "total": habit.total_marks,
            "last_mark": habit.last_mark_date,
        }

    @staticmethod
    def _today():       # сегодняшняя дата YYYY-MM-DD
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")

if __name__ == "__main__":
    # удаляем тестовую базу данных перед запуском
    import os
    test_db = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "test_logic.db"
    )
    if os.path.exists(test_db):
        os.remove(test_db)

    print("Тестирование HabitMagager... \n")

    db = Database(test_db)
    manager = HabitManager(db)

    # тест 1 добавить
    print("тест 1 добавление...")
    h = manager.add_habit("бег")
    print(f"Добавлено: {h}")
    print(f"Всего: {len(manager.get_all())}\n")

    # test 2 second
    print("тест 2. вторая привычка...")
    manager.add_habit("чтение")
    print(f"Всего {len(manager.get_all())}")
    for habit in manager.get_all():
        print(f"    {habit}")
    print()

    # test 3 None name
    print("тест 3. пустое имя...")
    result = manager.add_habit("    ")
    print(f"Результат: {result}  (ожидается None) \n")

    # test 4 mark
    print("тест 4. отметка...")
    print(f"Отметка: {manager.mark_habit(1)}  (ожидается True)")
    print(f"Порторная: {manager.mark_habit(1)} (ожидается false)")
    print(f"серия: {manager.get_habit(1)}\n")

    # test 5 status
    print("тест 5 статистика...")
    manager.delete_habit(1)
    print(f"Осталось: {len(manager.get_all())}")
    for habit in manager.get_all():
        print(f"    {habit}")

    print("\nВсе тесты завершены.")