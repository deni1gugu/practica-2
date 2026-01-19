# -*- coding: utf-8 -*-
import os

# Исправление ошибки кодировки 0xc2 для Windows
os.environ['PGCLIENTENCODING'] = 'utf8'

import psycopg2
from tkinter import *
from tkinter import messagebox, ttk

# --- НАСТРОЙКИ БАЗЫ ДАННЫХ ---
DB_PARAMS = {
    "dbname": "RepairServiceDB",  # ЗАМЕНИ НА СВОЕ
    "user": "postgres",
    "password": "Storm_shadow2006", # ЗАМЕНИ НА СВОЙ
    "host": "localhost",
    "port": "5432"
}

try:
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_client_encoding('UTF8')
    cursor = conn.cursor()
    print("Подключение к БД успешно!")
except Exception as e:
    print(f"Ошибка подключения: {e}")

class RepairApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("ИС 'Ремонт техники' - Задание 2-3")
        self.geometry("1000x600")
        
        # ID текущего пользователя (для Задания 3)
        self.current_user_id = 1 
        
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Верхняя панель
        toolbar = Frame(self, pady=10, bg="#eeeeee")
        toolbar.pack(side=TOP, fill=X)

        # Кнопки CRUD
        Button(toolbar, text="➕ Создать", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
               command=self.open_add_window).pack(side=LEFT, padx=5)
        
        Button(toolbar, text="✏️ Редактировать", bg="#FF9800", fg="white", font=("Arial", 9, "bold"),
               command=self.open_edit_window).pack(side=LEFT, padx=5)
        
        Button(toolbar, text="🔄 Обновить", command=self.load_data).pack(side=LEFT, padx=5)

        # Поиск
        Label(toolbar, text="  Поиск (модель):", bg="#eeeeee").pack(side=LEFT)
        self.search_entry = Entry(toolbar)
        self.search_entry.pack(side=LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self.load_data(self.search_entry.get()))

        # Таблица
        self.tree = ttk.Treeview(self, columns=("id", "date", "type", "model", "status"), show='headings')
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Дата начала")
        self.tree.heading("type", text="Тип техники")
        self.tree.heading("model", text="Модель")
        self.tree.heading("status", text="Статус (ID)")
        
        # Настройка колонок
        self.tree.column("id", width=50, anchor=CENTER)
        self.tree.column("status", width=80, anchor=CENTER)
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def load_data(self, search_query=""):
        for i in self.tree.get_children():
            self.tree.delete(i)
        try:
            if search_query:
                cursor.execute("SELECT request_id, start_date, equipment_type, model, request_status_id FROM requests WHERE model ILIKE %s", (f'%{search_query}%',))
            else:
                cursor.execute("SELECT request_id, start_date, equipment_type, model, request_status_id FROM requests ORDER BY request_id DESC")
            
            for row in cursor.fetchall():
                self.tree.insert("", END, values=row)
        except Exception as e:
            print(f"Ошибка загрузки данных: {e}")

    # --- ОКНО СОЗДАНИЯ (INSERT) ---
    def open_add_window(self):
        self.add_win = Toplevel(self)
        self.add_win.title("Новая заявка")
        self.add_win.geometry("350x420")

        frame = Frame(self.add_win, padx=20, pady=20)
        frame.pack(fill=BOTH)

        Label(frame, text="Тип оборудования:").pack(anchor=W)
        self.ent_type = Entry(frame, width=35)
        self.ent_type.pack(pady=5)

        Label(frame, text="Модель:").pack(anchor=W)
        self.ent_model = Entry(frame, width=35)
        self.ent_model.pack(pady=5)

        Label(frame, text="Описание проблемы:").pack(anchor=W)
        self.ent_desc = Text(frame, width=30, height=5)
        self.ent_desc.pack(pady=5)

        Button(frame, text="СОХРАНИТЬ", bg="#2196F3", fg="white", font=("Arial", 10, "bold"),
               command=self.save_new_request).pack(pady=15)

    def save_new_request(self):
        v_type = self.ent_type.get().strip()
        v_model = self.ent_model.get().strip()
        v_desc = self.ent_desc.get("1.0", END).strip()

        if not v_type or not v_model:
            messagebox.showwarning("Внимание", "Заполните тип и модель!")
            return

        try:
            sql = """INSERT INTO requests (start_date, equipment_type, model, problem_description, request_status_id, client_id) 
                     VALUES (CURRENT_DATE, %s, %s, %s, 1, %s)"""
            cursor.execute(sql, (v_type, v_model, v_desc, self.current_user_id))
            conn.commit()
            messagebox.showinfo("Успех", "Заявка добавлена!")
            self.add_win.destroy()
            self.load_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    # --- ОКНО РЕДАКТИРОВАНИЯ (UPDATE) ---
    def open_edit_window(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите строку для редактирования!")
            return
        
        values = self.tree.item(selected)['values']
        req_id = values[0]

        self.edit_win = Toplevel(self)
        self.edit_win.title(f"Редактирование №{req_id}")
        self.edit_win.geometry("350x250")

        frame = Frame(self.edit_win, padx=20, pady=20)
        frame.pack(fill=BOTH)

        Label(frame, text="Изменить статус (ID):").pack(anchor=W)
        self.upd_status = Entry(frame, width=35)
        self.upd_status.insert(0, values[4]) # Статус из таблицы
        self.upd_status.pack(pady=5)

        Label(frame, text="Изменить модель:").pack(anchor=W)
        self.upd_model = Entry(frame, width=35)
        self.upd_model.insert(0, values[3]) # Модель из таблицы
        self.upd_model.pack(pady=5)

        Button(frame, text="ОБНОВИТЬ ДАННЫЕ", bg="#FF9800", fg="white", font=("Arial", 10, "bold"),
               command=lambda: self.save_update(req_id)).pack(pady=15)

    def save_update(self, req_id):
        n_status = self.upd_status.get().strip()
        n_model = self.upd_model.get().strip()

        try:
            sql = "UPDATE requests SET request_status_id = %s, model = %s WHERE request_id = %s"
            cursor.execute(sql, (n_status, n_model, req_id))
            conn.commit()
            messagebox.showinfo("Успех", "Данные обновлены!")
            self.edit_win.destroy()
            self.load_data()
        except Exception as e:
            conn.rollback()
            messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")

if __name__ == "__main__":
    app = RepairApp()
    app.mainloop()