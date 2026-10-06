from datetime import datetime, timedelta
from collections import defaultdict         # для группировки отметок по месяцам

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
        return self._streak_in_month(*self.current_month)


    @property
    def last_mark_date(self):       # дата последней отметки
        return max(self.marks) if self.marks else None

    def __repr__(self):
        return (
            f"Habit(id={self.id}, name='{self.name}',"
            f"streak={self.streak}, total={self.total_marks})"
        )

    @property
    def best_streak(self):
        if not self.marks:
            return 0

        dates = sorted([datetime.strptime(d, "%Y-%m-%d") for d in self.marks])

        best = 1
        current = 1

        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current +=1
                best = max(best, current)
            else:
                current =1
        return best

    @property
    def current_month(self):
        today = datetime.now()
        return (today.year, today.month)

    @property
    def percent_month(self):
        return self._percent_in_month(*self.current_month)

    @property
    def months_stats(self):
        """Список месяцев с данными. Свежие сверху."""
        if not self.marks:
            return []

        # Группируем отметки по (год, месяц)
        by_month = defaultdict(list)
        for d in self.marks:
            date = datetime.strptime(d, "%Y-%m-%d")
            by_month[(date.year, date.month)].append(d)

        result = []
        for (year, month) in sorted(by_month.keys(), reverse=True):
            result.append({
                "name": self._month_name(year, month),
                "count": len(by_month[(year, month)]),
                "percent": self._percent_in_month(year, month),
                "streak": self._streak_in_month(year, month),
            })
        return result


    def _marks_in_month(self, year, month):
        return [
            d for d in self.marks
            if datetime.strptime(d, "%Y-%m-%d").year == year
            and datetime.strptime(d, "%Y-%m-%d").month == month
        ]

    def _streak_in_month(self, year, month):
        """Серия в конкретном месяце."""
        marks = self._marks_in_month(year, month)
        if not marks:
            return 0

        dates = sorted(
            [datetime.strptime(d, "%Y-%m-%d") for d in marks],
            reverse=True
        )

        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        is_current = (year == today.year and month == today.month)

        if is_current and (today - dates[0]).days > 1:
            return 0

        streak = 1
        for i in range(len(dates) - 1):
            if (dates[i] - dates[i + 1]).days == 1:
                streak += 1
            else:
                break
        return streak

    def _percent_in_month(self, year, month):
        """Процент выполнения в месяце."""
        count = len(self._marks_in_month(year, month))
        days = self._days_in_month(year, month)
        return min(round(count / days * 100), 100)

    @staticmethod
    def _days_in_month(year, month):
        """Сколько дней в месяце."""
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        return (next_month - datetime(year, month, 1)).days

    @staticmethod
    def _month_name(year, month):
        """Название месяца: 'Октябрь 2026'."""
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        return f"{months[month - 1]} {year}"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
            "marks": self.marks,
            "streak": self.streak,
            "percent_month": self.percent_month,
            "total_marks": self.total_marks,
            "best_streak": self.best_streak
        }

if __name__ == "__main__":
    print("тестирование класса Habit ... \n")
    today = datetime.now()

    # тест 1
    h1 = Habit(1, "бег", "2026-09-01")
    print("тест 1 (пустая): ", h1)
    print(f" streak={h1.streak}, percent={h1.percent_month}%\n")

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
    print(f"   percent={h5.percent_month}% (ожидается 50) \n")

    # тест 6
    print("тест 6 (to_dict): ", h2.to_dict())