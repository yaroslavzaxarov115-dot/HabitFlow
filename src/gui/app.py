import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from src.logic import HabitManager
import matplotlib
matplotlib.use("TkAgg")

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class HabitFlowApp:
    # главное окно HabitFlow
    def __init__(self, root):
        self.root = root
        self.root.title("HabitFlow - трекер привычек")
        self.root.geometry("1100x650")

        self.manager = HabitManager()
        self.dark_mode = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Создаёт все виджеты."""
        # --- Верхняя панель ---
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Новая привычка:").pack(side="left", padx=5)

        self.new_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.new_var, width=30)
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", lambda e: self.on_add())

        ttk.Button(top, text="Добавить", command=self.on_add).pack(side="left", padx=5)

        self.theme_btn = ttk.Button(top, text=" Тема", command=self.toggle_theme)
        self.theme_btn.pack(side="right", padx=5)
        self.show_btn = ttk.Button(top, text=" Показать", command=self.show_all_panels)
        self.show_btn.pack(side="right", padx=5)
        self.show_btn.pack_forget()  # скрыта по умолчанию

        # --- Центр: две колонки ---
        center = ttk.Frame(self.root)
        center.pack(fill="both", expand=True, padx=10, pady=10)

        # Левая часть — таблица
        left = ttk.Frame(center)
        left.pack(side="left", fill="both", expand=True)

        columns = ("num", "name", "streak", "percent", "total", "last")
        self.tree = ttk.Treeview(left, columns=columns, show="headings", height=15)

        self.tree.heading("num", text="№")
        self.tree.heading("name", text="Привычка")
        self.tree.heading("streak", text="Серия")
        self.tree.heading("percent", text="За месяц")
        self.tree.heading("total", text="Всего")
        self.tree.heading("last", text="Последняя")

        self.tree.column("num", width=50, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("streak", width=70, anchor="center")
        self.tree.column("percent", width=80, anchor="center")
        self.tree.column("total", width=70, anchor="center")
        self.tree.column("last", width=110, anchor="center")

        self.tree.pack(fill="both", expand=True)

        # Привязки
        self.tree.bind("<Double-1>", lambda e: self.on_mark())
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Контекстное меню
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="  Отметить", command=self.on_mark)
        self.context_menu.add_command(label="  Статистика", command=self.on_stats)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="  Удалить", command=self.on_delete)

        # Правая часть — календарь + график
        self.right_panel = ttk.Frame(center, width=320)
        self.right_panel.pack(side="right", fill="y", padx=(10, 0))
        self.right_panel.pack_propagate(False)

        # Календарь (сверху)
        self.calendar_frame = ttk.Frame(self.right_panel)
        self.calendar_frame.pack(fill="x")

        # График (снизу)
        self.chart_frame = tk.Frame(self.right_panel, height=250)
        self.chart_frame.pack(fill="x", side="bottom")
        self.chart_frame.pack_propagate(False)

        # Заголовок графика + крестик
        chart_header = ttk.Frame(self.chart_frame)
        chart_header.pack(fill="x")

        ttk.Label(
            chart_header,
            text=" Прогресс",
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=5)
        self.chart_frame.pack_forget()

        ttk.Button(
            chart_header,
            text="×",
            width=3,
            command=self.hide_chart
        ).pack(side="right", padx=5)

        # Настройка графика
        self.fig = Figure(figsize=(3, 2), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.ax.clear()
        self.ax.axis("off")
        self.canvas.draw()

        # --- Нижняя панель ---
        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(fill="x")

        ttk.Button(bottom, text="Отметить", command=self.on_mark).pack(side="left", padx=5)
        ttk.Button(bottom, text="Статистика", command=self.on_stats).pack(side="left", padx=5)
        ttk.Button(bottom, text="Удалить", command=self.on_delete).pack(side="left", padx=5)
        ttk.Button(bottom, text="Обновить", command=self.refresh).pack(side="left", padx=5)
        ttk.Button(bottom, text="Выход", command=self.root.quit).pack(side="right", padx=5)

    def refresh(self):
        # перегружаем таблицу из базы данных
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.manager.load()

        for number, habit in enumerate(self.manager.get_all(), start=1):
            last = habit.last_mark_date or "-"
            self.tree.insert("", "end", iid=str(habit.id), values=(
                number,
                habit.name,
                f"{habit.streak} дн.",
                f"{habit.percent_month}%",
                habit.total_marks,
                last,
            ))

        # Если что-то выделено — обновим календарь и график
        habit_id = self._selected_id()
        if habit_id is not None:
            self.draw_calendar(habit_id)
            self.draw_chart(habit_id)

    def _selected_id(self):
        # возвращает id выделенной привычки или ничего
        selected = self.tree.selection()
        if not selected:
            return None
        return int(selected[0])

    def _show_context_menu(self, event):
        # показывает меню на ПКМ
        row_id = self.tree.identify_row(event.y)
        if row_id:
            self.tree.selection_set(row_id)
            self.context_menu.post(event.x_root, event.y_root)

    def _on_select(self, event):
        """Реакция на выбор привычки в таблице."""
        habit_id = self._selected_id()
        if habit_id is not None:
            self.draw_calendar(habit_id)
            self.draw_chart(habit_id)
        self.chart_frame.pack(fill="x", side="bottom")

    def draw_calendar(self, habit_id):
        """Рисует календарь текущего месяца для привычки."""
        # Очищаем старый календарь
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        habit = self.manager.get_habit(habit_id)
        if habit is None:
            return

        # Заголовок с названием месяца
        today = datetime.now()
        month_name = habit._month_name(today.year, today.month)
        # Заголовок календаря + крестик
        header = ttk.Frame(self.calendar_frame)
        header.pack(fill="x", pady=10)

        ttk.Label(
            header,
            text=f"📅 {month_name}",
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=10)

        ttk.Button(
            header,
            text="×",
            width=3,
            command=self.hide_calendar
        ).pack(side="right", padx=5)

        # Сетка
        grid = ttk.Frame(self.calendar_frame)
        grid.pack()

        # Заголовки дней недели
        days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        for col, day in enumerate(days):
            ttk.Label(grid, text=day, width=4, anchor="center").grid(row=0, column=col, padx=1, pady=1)

        # Определяем первый день месяца и его день недели
        first_day = datetime(today.year, today.month, 1)
        first_weekday = first_day.weekday()  # 0 = Пн, 6 = Вс

        # Количество дней в месяце
        days_in_month = habit._days_in_month(today.year, today.month)

        # Список отметок этого месяца
        marks_set = set(habit._marks_in_month(today.year, today.month))

        # Рисуем дни
        row = 1
        col = first_weekday
        for day in range(1, days_in_month + 1):
            date_str = f"{today.year}-{today.month:02d}-{day:02d}"

            # Определяем цвет
            if day > today.day:
                color = "#e0e0e0"  # будущее
            elif date_str in marks_set:
                color = "#4caf50"  # отмечено (зелёный)
            else:
                color = "#f0f0f0"  # пропуск (светло-серый)

            lbl = tk.Label(
                grid,
                text=str(day),
                width=4, height=2,
                bg=color,
                relief="ridge",
                borderwidth=1
            )
            lbl.grid(row=row, column=col, padx=1, pady=1)

            col += 1
            if col > 6:
                col = 0
                row += 1

    def hide_calendar(self):
        """Скрывает календарь."""
        self.calendar_frame.pack_forget()
        self.show_btn.pack(side="right", padx=5)
        self.show_btn.configure(text=" Показать")

    def hide_chart(self):
        """Скрывает график."""
        self.chart_frame.pack_forget()
        self.show_btn.pack(side="right", padx=5)
        self.show_btn.configure(text=" Показать")

    def show_all_panels(self):
        """Показывает скрытые панели."""
        self.calendar_frame.pack(fill="x")
        self.chart_frame.pack(fill="x", side="bottom")
        self.show_btn.pack_forget()

    def draw_chart(self, habit_id):
        """Рисует график прогресса за текущий месяц."""
        habit = self.manager.get_habit(habit_id)
        if habit is None:
            return

        today = datetime.now()
        year, month = today.year, today.month
        days_in_month = habit._days_in_month(year, month)
        marks_set = set(habit._marks_in_month(year, month))

        # Строим накопительную кривую
        days = list(range(1, days_in_month + 1))
        cumulative = []
        count = 0
        for day in days:
            date_str = f"{year}-{month:02d}-{day:02d}"
            if date_str in marks_set:
                count += 1
            cumulative.append(count)

        # Рисуем линию
        self.ax.clear()
        self.ax.plot(days, cumulative, marker="o", color="#4caf50", linewidth=2)
        # Цвет текста по теме
        color = "white" if self.dark_mode else "black"

        self.ax.set_title(f"{habit.name} — прогресс за месяц", fontsize=10, color=color)
        self.ax.set_xlabel("День", fontsize=8, color=color)
        self.ax.set_ylabel("Отметок", fontsize=8, color=color)
        self.ax.grid(True, alpha=0.3, color=color)
        self.ax.tick_params(labelsize=8, colors=color)

        self.fig.tight_layout()
        self.canvas.draw()

    def on_add(self):
        # добавляет привычку
        name = self.new_var.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введи название")
            return
        self.manager.add_habit(name)
        self.new_var.set("")
        self.refresh()

    def on_mark(self):
        # отмечает выделенную привычку
        habit_id = self._selected_id()
        if habit_id is None:
            messagebox.showwarning("Ошибка", "Выберите привычку в таблице")
            return

        if self.manager.mark_habit(habit_id):
            self.refresh()
        else:
            messagebox.showinfo("Уже отмечено", "эта привычка уже отмечена сегодня")

    def on_delete(self):
        # удаляет выделенную привычку
        habit_id = self._selected_id()
        if habit_id is None:
            messagebox.showwarning("Ошибка", "Выбери привычку")
            return
        if messagebox.askyesno("Удаление", "Точно удалить привычку?"):
            self.manager.delete_habit(habit_id)
            self.refresh()

    def on_stats(self):
        """Открывает окно со статистикой привычки."""
        habit_id = self._selected_id()
        if habit_id is None:
            messagebox.showwarning("Ошибка", "Выбери привычку")
            return

        stats = self.manager.get_stats(habit_id)
        if stats is None:
            return

        # Создаём новое окно
        win = tk.Toplevel(self.root)
        win.title(f"Статистика: {stats['name']}")
        win.geometry("500x500")
        # Фон окна в зависимости от темы
        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        win.configure(bg=bg)

        # --- Сводка сверху ---
        summary = ttk.Frame(win, padding=15)
        summary.pack(fill="x")

        ttk.Label(
            summary,
            text=f"Всего отметок: {stats['total']}",
            font=("Arial", 12)
        ).pack(anchor="w")

        ttk.Label(
            summary,
            text=f"Лучшая серия: {stats['best']} дн.",
            font=("Arial", 12)
        ).pack(anchor="w")

        # --- Таблица месяцев ---
        frame = ttk.Frame(win, padding=10)
        frame.pack(fill="both", expand=True)

        columns = ("month", "count", "percent", "streak")
        tree = ttk.Treeview(frame, columns=columns, show="headings", height=12)

        tree.heading("month", text="Месяц")
        tree.heading("count", text="Отметок")
        tree.heading("percent", text="Процент")
        tree.heading("streak", text="Серия")

        tree.column("month", width=150)
        tree.column("count", width=80, anchor="center")
        tree.column("percent", width=80, anchor="center")
        tree.column("streak", width=80, anchor="center")

        # Скроллбар
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Заполняем месяцами
        for m in stats["months"]:
            tree.insert("", "end", values=(
                m["name"],
                m["count"],
                f"{m['percent']}%",
                f"{m['streak']} дн.",
            ))

        # --- Кнопка Закрыть ---

        btn_frame = tk.Frame(win, bg=bg)
        btn_frame.pack(fill="x", pady=10)

        ttk.Button(btn_frame, text="Закрыть", command=win.destroy).pack()

    def toggle_theme(self):
        # переключает светлую-темную тему
        self.dark_mode = not self.dark_mode
        style = ttk.Style()

        if self.dark_mode:
            style.theme_use("clam")
            style.configure("Treeview",
                            background="#2b2b2b",
                            foreground="white",
                            fieldbackground="#2b2b2b")
            style.configure("Treeview.Heading",
                            background="#3c3c3c",
                            foreground="white")
            style.configure("TFrame", background="#1e1e1e")
            style.configure("TLabel", background="#1e1e1e", foreground="white")
            style.configure("TButton", background="#3c3c3c", foreground="white")
            style.configure("TCheckbutton", background="#1e1e1e", foreground="white")
            self.root.configure(bg="#1e1e1e")
            self.theme_btn.configure(text="Тема")
        else:
            style.theme_use("vista")
            self.root.configure(bg="SystemButtonFace")
            self.theme_btn.configure(text="Тема")

        style.configure("TButton", padding=4)
        style.configure("TreeView", rowheight=25)

    # Обновить фон графика
        bg = "#1e1e1e" if self.dark_mode else "#f0f0f0"
        self.fig.set_facecolor(bg)
        self.canvas.get_tk_widget().configure(bg=bg)
        self.canvas.draw()
        # Перерисовать график с новыми цветами
        habit_id = self._selected_id()
        if habit_id is not None:
            self.draw_chart(habit_id)