# -*- coding: utf-8 -*-
import os
os.environ['PGCLIENTENCODING'] = 'utf8'

import psycopg2
from tkinter import *
from tkinter import messagebox, ttk

# --- НАСТРОЙКИ БАЗЫ ДАННЫХ ---
DB_PARAMS = {
    "dbname": "RepairServiceDB", 
    "user": "postgres",
    "password": "Storm_shadow2006",
    "host": "localhost",
    "port": "5432"
}

try:
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_client_encoding('UTF8')
    cursor = conn.cursor()
except Exception as e:
    print(f"Ошибка: {e}")

class RepairApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("ООО 'Конди' - Учет заявок")
        self.geometry("1100x600")
        self.user_id = 1 # Текущий пользователь
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        toolbar = Frame(self, pady=10)
        toolbar.pack(side=TOP, fill=X)

        Button(toolbar, text="+ Новая заявка", bg="#4CAF50", fg="white", command=self.open_add_window).pack(side=LEFT, padx=5)
        Button(toolbar, text="✏️ Редактировать", bg="#FF9800", command=self.open_edit_window).pack(side=LEFT, padx=5)
        Button(toolbar, text="📊 Статистика", command=self.show_stats).pack(side=LEFT, padx=5)

        Label(toolbar, text=" Поиск:").pack(side=LEFT)
        self.search_ent = Entry(toolbar)
        self.search_ent.pack(side=LEFT, padx=5)
        self.search_ent.bind("<KeyRelease>", lambda e: self.load_data(self.search_ent.get()))

        # ОБНОВЛЕННЫЕ КОЛОНКИ (Добавили Мастера)
        columns = ("id", "date", "type", "model", "status", "master")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        
        headers = {"id": "№", "date": "Дата", "type": "Тип", "model": "Модель", "status": "Статус", "master": "Мастер"}
        for col, text in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=150)
            
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def load_data(self, search=""):
        for i in self.tree.get_children(): self.tree.delete(i)
        
        # SQL ЗАПРОС С JOIN (чтобы видеть имена, а не ID как на скриншоте)
        query = """
            SELECT r.request_id, r.start_date, r.equipment_type, r.model, 
                   COALESCE(s.status_name, 'Новая'), 
                   COALESCE(m.fio, 'Не назначен')
            FROM requests r
            LEFT JOIN statuses s ON r.request_status_id = s.status_id
            LEFT JOIN users m ON r.master_id = m.user_id
        """
        if search:
            query += f" WHERE r.model ILIKE '%{search}%' OR r.equipment_type ILIKE '%{search}%'"
        
        query += " ORDER BY r.request_id DESC"
        
        try:
            cursor.execute(query)
            for row in cursor.fetchall():
                self.tree.insert("", END, values=row)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    # Окна добавления и редактирования
    def open_add_window(self):
        win = Toplevel(self); f = Frame(win, padx=20, pady=20); f.pack()
        Label(f, text="Тип:").pack(); e_t = Entry(f); e_t.pack()
        Label(f, text="Модель:").pack(); e_m = Entry(f); e_m.pack()
        Button(f, text="ОК", command=lambda: self.save_req(e_t.get(), e_m.get(), win)).pack(pady=10)

    def save_req(self, t, m, w):
        cursor.execute("INSERT INTO requests (start_date, equipment_type, model, request_status_id, client_id) VALUES (CURRENT_DATE, %s, %s, 1, %s)", (t, m, self.user_id))
        conn.commit(); w.destroy(); self.load_data()

    def open_edit_window(self):
        sel = self.tree.selection()
        if not sel: return
        val = self.tree.item(sel)['values']
        win = Toplevel(self); f = Frame(win, padx=20, pady=20); f.pack()
        Label(f, text="ID Статуса:").pack(); e_s = Entry(f); e_s.pack()
        Label(f, text="ID Мастера:").pack(); e_m = Entry(f); e_m.pack()
        Button(f, text="Сохранить", command=lambda: self.save_upd(val[0], e_s.get(), e_m.get(), win)).pack(pady=10)

    def save_upd(self, rid, s, m, w):
        cursor.execute("UPDATE requests SET request_status_id = %s, master_id = %s WHERE request_id = %s", (s, m, rid))
        conn.commit(); w.destroy(); self.load_data()

    def show_stats(self):
        cursor.execute("SELECT COUNT(*) FROM requests")
        total = cursor.fetchone()[0]
        messagebox.showinfo("Статистика", f"Всего заявок в системе: {total}")

if __name__ == "__main__":
    app = RepairApp()
    app.mainloop()