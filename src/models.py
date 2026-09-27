from datetime import datetime, timedelta

class Habit:        # модель привычки, данные + вычисление привычки
    def __init__(self, id, name, created_at, marks=None):

        self.id = id
        self.name = name
        self.created_at = created_at
        self.marks = marks if marks is not None else []

    @property
    def total_marks(self):
         # всего отметок
        return len(self.marks)

    @property
    def streak(self):
        # текущая серия
        if not self.marks:
                return 0

        dates = sorted(
            [datetime.strptime(d, "%Y-%m-%d") for d in self.marks],
            reverse=True
        )

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if (today - dates[0]).days > 1:
            return 0

        streak = 1
        for i in range(len(dates) - 1):
            if (dates[i] - dates[i + 1]).days ==1:
                streak +=1
            else:
                break
        return streak

    @property
    def percent_30_days(self):          # процент выполнения за последние 30 дней
        if not self.marks:
            return 0

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        border = today - timedelta(days=30)

        recent = [
            d for d in self.marks
            if datetime.strptime(d, "%Y-%m-%d") >= border
        ]
        return min(round((len(recent) / 30) * 100), 100)

    @property
    def last_mark_date(self):       # дата последней отметки
        return max(self.marks) if self.marks else None

    def __repr__(self):
        return (
            f"Habit(id={self.id}, name='{self.name}',"
            f"streak={self.streak}, total={self.total_marks})"
        )

    def to_dick(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "marks": self.marks,
            "streak": self.streak,
            "percent_30_days": self.percent_30_days,
            "total_marks": self.total_marks,
        }

if __name__ == "__main__":
    print("тестирование класса Habit ... \n")
    today = datetime.now()

    # тест 1
    h1 = Habit(1, "бег", "2026-09-01")
    print("тест 1 (пустая): ", h1)
    print(f" streak={h1.streak}, percent={h1.percent_30_days}%\n")

    # тест 2
    d1 = (today - timedelta(days=2)).strftime("%Y-%m-%d")
    d2 = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    d3 = today.strftime("%Y-%m-%d")
    h2 = Habit(2, "чтение", "2026-09-01", marks=[d3, d2, d1])
    print("тест 2 (3 подрят): ", h2)
    print(f" streak={h2.streak} (ожидается 3) \n")

    # тест 3
    d_old = (today - timedelta(days=10)).strftime("%Y-%m-%d")
    h3 = Habit(3, "зарядка", "2026-09-01", marks=[d3, d2, d_old])
    print("тест 3 (с разрывом): ", h3)
    print(f"  streak={h3.streak} (ожидается 2)")

    # тест 4
    d_5 = (today - timedelta(days=5)).strftime("%Y-%m-%d")
    d_6 = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    h4 = Habit(4, "медитация", "2026-09-01", marks=[d_5, d_6])
    print("тест 4 (старая серия): ", h4)
    print(f"  streak={h4.streak}  (ожидается 0)")

    # тест 5
    marks_15 = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(15)]
    h5 = Habit(5, "вода", "2026-09-01", marks=marks_15)
    print("тест 5 (процент): ", h5)
    print(f"   percent={h5.percent_30_days}% (ожидается 50) \n")

    # тест 6
    print("тест 6 (to_dict): ", h2.to_dick())