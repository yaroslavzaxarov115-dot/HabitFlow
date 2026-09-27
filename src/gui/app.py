import tkinter as tk
from tkinter import ttk, messagebox
from src.logic import HabitManager

class HabitFlowApp:
    # главное окно HabitFlow
    def __init__(self, root):
        self.root = root
        self.root.title("HabitFlow - трекер привычек")
        self.root.geometry("750x520")

        self.manager = HabitManager()
        self.dark_mode = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        # создание виджетов
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Новая привычка: ").pack(side="left", padx=5)

        self.new_var = tk.StringVar()
        entry = ttk.Entry(top, textvariable=self.new_var, width=30)
        entry.pack(side="left", padx=5)
        entry.bind("<Return>", lambda e: self.on_add())

        ttk.Button(top, text="Добавить", command=self.on_add).pack(side="left", padx=5)
        self.theme_btn = ttk.Button(top, text="Тема", command=self.toggle_there)
        self.theme_btn.pack(side="right", padx=5)

        # таблица с привычками
        columns = ("id", "name", "streak", "percent", "total", "last")
        self.tree = ttk.Treeview(self.root, columns=columns, show="headings", height=15)

        self.tree.heading("id", text="№")
        self.tree.heading("name", text="Привычка")
        self.tree.heading("streak", text="Серия")
        self.tree.heading("percent", text="30 дней")
        self.tree.heading("total", text="Всего")
        self.tree.heading("last", text="Последняя")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("streak", width=80, anchor="center")
        self.tree.column("percent", width=80, anchor="center")
        self.tree.column("total", width=80, anchor="center")
        self.tree.column("last", width=120, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        # двойной клик по строке = отменить
        self.tree.bind("<Double-1>", lambda e: self.on_mark())
        self.tree.bind("<Button-3>", self._show_context_menu)

        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Отметить выполнение", command=self.on_mark)
        self.context_menu.add_command(label="Статистика", command=self.on_stats)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.on_delete)

        bottom = ttk.Frame(self.root, padding=10)
        bottom.pack(fill="x")

        ttk.Button(bottom, text="Отменить", command=self.on_mark).pack(side="left", padx=5)
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
                f"{habit.percent_30_days}%",
                habit.total_marks,
                last,
            ))

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
        # показывает статистику привычки
        habit_id = self._selected_id()
        if habit_id is None:
            messagebox.showwarning("Ошибка", "Выберите привычку")
            return

        stats = self.manager.get_stats(habit_id)
        if stats is None:
            return

        text = (
            f"Привычка: {stats['name']}\n\n"
            f"Серия: {stats['streak']}дн.\n"
            f"Прочент за 30 дней: {stats['percent']}%\n"
            f"Всего отметок: {stats['total']}\n"
            f"Последняя отметка: {stats['last_mark'] or '-'}"
        )
        messagebox.showinfo("Статистика", text)

    def toggle_there(self):
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