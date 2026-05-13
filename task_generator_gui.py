import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import random
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================
class TaskCategory(Enum):
    STUDY = "Учеба"
    SPORT = "Спорт"
    WORK = "Работа"
    HOME = "Дом"
    HOBBY = "Хобби"


# ==================== TASK MODEL ====================
class Task:
    """Модель задачи"""

    def __init__(self, description: str, category: TaskCategory):
        self.description = description
        self.category = category
        self.created_at = datetime.now()

    def to_dict(self):
        return {
            "description": self.description,
            "category": self.category.value,
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data):
        task = cls(data["description"], TaskCategory(data["category"]))
        task.created_at = datetime.fromisoformat(data["created_at"])
        return task

    def __str__(self):
        return f"[{self.category.value}] {self.description}"


# ==================== MAIN APPLICATION ====================
class RandomTaskGenerator:
    """GUI приложение для генерации случайных задач"""

    # Предопределенные задачи
    DEFAULT_TASKS = [
        ("Прочитать статью по программированию", TaskCategory.STUDY),
        ("Сделать домашнее задание", TaskCategory.STUDY),
        ("Посмотреть обучающее видео", TaskCategory.STUDY),
        ("Написать конспект", TaskCategory.STUDY),
        ("Выучить новые слова", TaskCategory.STUDY),

        ("Сделать зарядку", TaskCategory.SPORT),
        ("Пробежка 1 км", TaskCategory.SPORT),
        ("Отжаться 20 раз", TaskCategory.SPORT),
        ("Пойти в спортзал", TaskCategory.SPORT),
        ("Растяжка 15 минут", TaskCategory.SPORT),

        ("Закончить отчет", TaskCategory.WORK),
        ("Ответить на письма", TaskCategory.WORK),
        ("Составить план работы", TaskCategory.WORK),
        ("Провести встречу", TaskCategory.WORK),
        ("Сделать презентацию", TaskCategory.WORK),

        ("Помыть посуду", TaskCategory.HOME),
        ("Убраться в комнате", TaskCategory.HOME),
        ("Приготовить ужин", TaskCategory.HOME),
        ("Постирать белье", TaskCategory.HOME),
        ("Полить цветы", TaskCategory.HOME),

        ("Почитать книгу", TaskCategory.HOBBY),
        ("Нарисовать рисунок", TaskCategory.HOBBY),
        ("Поиграть на гитаре", TaskCategory.HOBBY),
        ("Посмотреть фильм", TaskCategory.HOBBY),
        ("Погулять в парке", TaskCategory.HOBBY),
    ]

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Random Task Generator")
        self.root.geometry("900x650")
        self.root.resizable(True, True)

        # Данные
        self.tasks = []  # Список всех доступных задач
        self.history = []  # История сгенерированных задач
        self.history_file = "tasks_history.json"

        # Загрузка данных
        self.load_tasks()
        self.load_history()

        # Создание интерфейса
        self.setup_ui()

    def setup_ui(self):
        """Создание интерфейса пользователя"""

        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Настройка весов для растягивания
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

        # Заголовок
        title_label = ttk.Label(main_frame, text="Генератор случайных задач",
                                font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, pady=10)

        # Фрейм для текущей задачи
        current_frame = ttk.LabelFrame(main_frame, text="Текущая задача", padding="15")
        current_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        current_frame.columnconfigure(0, weight=1)

        self.current_task_label = ttk.Label(current_frame, text="Нажмите кнопку для генерации",
                                            font=('Arial', 12), wraplength=800)
        self.current_task_label.grid(row=0, column=0, pady=10)

        # Кнопка генерации
        self.generate_btn = ttk.Button(current_frame, text="🎲 Сгенерировать задачу",
                                       command=self.generate_task, width=30)
        self.generate_btn.grid(row=1, column=0, pady=5)

        # Фрейм для фильтрации
        filter_frame = ttk.LabelFrame(main_frame, text="Фильтрация истории", padding="10")
        filter_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(filter_frame, text="Фильтр по типу:").pack(side=tk.LEFT, padx=5)

        self.filter_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                    values=["Все"] + [c.value for c in TaskCategory],
                                    width=15, state="readonly")
        filter_combo.pack(side=tk.LEFT, padx=5)
        filter_combo.bind('<<ComboboxSelected>>', lambda e: self.refresh_history())

        ttk.Button(filter_frame, text="Сбросить фильтр",
                  command=self.reset_filter).pack(side=tk.LEFT, padx=5)

        # Фрейм для истории
        history_frame = ttk.LabelFrame(main_frame, text="История задач", padding="10")
        history_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)

        # Создание списка для истории
        columns = ("№", "Дата", "Тип", "Задача")
        self.history_tree = ttk.Treeview(history_frame, columns=columns,
                                          show="headings", height=15)

        # Настройка колонок
        self.history_tree.heading("№", text="№")
        self.history_tree.heading("Дата", text="Дата и время")
        self.history_tree.heading("Тип", text="Тип")
        self.history_tree.heading("Задача", text="Задача")

        self.history_tree.column("№", width=40, anchor="center")
        self.history_tree.column("Дата", width=150, anchor="center")
        self.history_tree.column("Тип", width=80, anchor="center")
        self.history_tree.column("Задача", width=550)

        # Полосы прокрутки
        vsb = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_tree.yview)
        hsb = ttk.Scrollbar(history_frame, orient="horizontal", command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Размещение таблицы
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # Фрейм для добавления новой задачи
        add_frame = ttk.LabelFrame(main_frame, text="Добавить новую задачу", padding="10")
        add_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=10)
        add_frame.columnconfigure(1, weight=1)

        ttk.Label(add_frame, text="Описание:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.new_task_var = tk.StringVar()
        self.new_task_entry = ttk.Entry(add_frame, textvariable=self.new_task_var, width=50)
        self.new_task_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        ttk.Label(add_frame, text="Тип задачи:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.new_category_var = tk.StringVar(value=TaskCategory.STUDY.value)
        category_combo = ttk.Combobox(add_frame, textvariable=self.new_category_var,
                                       values=[c.value for c in TaskCategory],
                                       width=15, state="readonly")
        category_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        # Кнопки действий
        button_frame = ttk.Frame(add_frame)
        button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="➕ Добавить задачу",
                  command=self.add_custom_task).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️ Очистить историю",
                  command=self.clear_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💾 Сохранить задачи",
                  command=self.save_tasks).pack(side=tk.LEFT, padx=5)

        # Статус бар
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var,
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)

        # Загрузка истории в таблицу
        self.refresh_history()

        # Привязка клавиш
        self.generate_btn.bind('<Return>', lambda e: self.generate_task())
        self.new_task_entry.bind('<Return>', lambda e: self.add_custom_task())

    def load_tasks(self):
        """Загрузка предопределенных задач"""
        for description, category in self.DEFAULT_TASKS:
            self.tasks.append(Task(description, category))
        self.status_var.set(f"Загружено {len(self.tasks)} задач")

    def load_history(self):
        """Загрузка истории из JSON файла"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = [Task.from_dict(task_data) for task_data in data]
                self.status_var.set(f"Загружено {len(self.history)} задач из истории")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить историю: {str(e)}")
                self.history = []
        else:
            self.history = []

    def save_history(self):
        """Сохранение истории в JSON файл"""
        try:
            data = [task.to_dict() for task in self.history]
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить историю: {str(e)}")
            return False

    def save_tasks(self):
        """Сохранение всех задач (предопределенных + пользовательских)"""
        try:
            data = [task.to_dict() for task in self.tasks]
            with open("all_tasks.json", 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", "Задачи успешно сохранены в файл all_tasks.json")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить задачи: {str(e)}")

    def generate_task(self):
        """Генерация случайной задачи"""
        if not self.tasks:
            messagebox.showwarning("Внимание", "Нет доступных задач! Добавьте новые задачи.")
            return

        # Выбор случайной задачи
        task = random.choice(self.tasks)

        # Добавление в историю
        generated_task = Task(task.description, task.category)
        self.history.insert(0, generated_task)  # Добавляем в начало списка

        # Ограничиваем историю 100 записями
        if len(self.history) > 100:
            self.history = self.history[:100]

        # Сохранение в JSON
        self.save_history()

        # Обновление отображения
        self.current_task_label.config(
            text=f"✨ {generated_task} ✨",
            foreground="green"
        )
        self.refresh_history()
        self.status_var.set(f"Сгенерирована задача: {generated_task.description[:50]}...")

        # Анимация цвета
        self.root.after(1500, lambda: self.current_task_label.config(foreground="black"))

    def add_custom_task(self):
        """Добавление пользовательской задачи"""
        description = self.new_task_var.get().strip()

        # Проверка корректности ввода
        if not description:
            messagebox.showerror("Ошибка", "Описание задачи не может быть пустым!")
            return

        if len(description) < 3:
            messagebox.showerror("Ошибка", "Описание должно содержать минимум 3 символа!")
            return

        # Получение категории
        category_str = self.new_category_var.get()
        category = None
        for c in TaskCategory:
            if c.value == category_str:
                category = c
                break

        if not category:
            messagebox.showerror("Ошибка", "Выберите корректную категорию!")
            return

        # Добавление задачи
        new_task = Task(description, category)
        self.tasks.append(new_task)

        # Очистка поля ввода
        self.new_task_var.set("")

        self.status_var.set(f"Добавлена новая задача: {description[:50]}...")
        messagebox.showinfo("Успех", f"Задача добавлена!\n{new_task}")

    def refresh_history(self):
        """Обновление отображения истории с фильтрацией"""
        # Очищаем таблицу
        for item in self.history_tree.get_children():
            self.history_tree.delete(item)

        # Получаем отфильтрованные задачи
        filter_value = self.filter_var.get()
        filtered_history = self.history

        if filter_value != "Все":
            filtered_history = [task for task in self.history
                               if task.category.value == filter_value]

        # Добавляем задачи в таблицу
        for i, task in enumerate(filtered_history, 1):
            date_str = task.created_at.strftime("%Y-%m-%d %H:%M:%S")
            self.history_tree.insert("", "end", values=(
                i, date_str, task.category.value, task.description
            ))

        # Обновляем статус
        total = len(self.history)
        filtered = len(filtered_history)
        if filter_value == "Все":
            self.status_var.set(f"Всего задач в истории: {total}")
        else:
            self.status_var.set(f"Показано {filtered} из {total} задач (фильтр: {filter_value})")

    def reset_filter(self):
        """Сброс фильтра"""
        self.filter_var.set("Все")
        self.refresh_history()

    def clear_history(self):
        """Очистка истории"""
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите очистить всю историю?"):
            self.history = []
            self.save_history()
            self.refresh_history()
            self.current_task_label.config(text="История очищена", foreground="orange")
            self.status_var.set("История успешно очищена")
            self.root.after(2000, lambda: self.current_task_label.config(text="Нажмите кнопку для генерации", foreground="black"))

    def run(self):
        """Запуск приложения"""
        self.root.mainloop()


# ==================== MAIN ====================
if __name__ == "__main__":
    app = RandomTaskGenerator()
    app.run()
