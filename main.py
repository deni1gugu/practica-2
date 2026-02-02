# -*- coding: utf-8 -*-
import os
os.environ['PGCLIENTENCODING'] = 'utf8'
import psycopg2
from tkinter import *
from tkinter import messagebox, ttk

# Настройки подключения
DB_PARAMS = {
    "dbname": "RepairServiceDB", 
    "user": "postgres", 
    "password": "Storm_shadow2006", 
    "host": "localhost", "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_client_encoding('UTF8')
    return conn

class RepairApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("ООО 'Конди' - Полная информационная система")
        self.geometry("1300x700")
        self.current_user_id = 1 
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        toolbar = Frame(self, pady=10, bg="#f0f0f0")
        toolbar.pack(side=TOP, fill=X)

        # Основные кнопки по ТЗ
        Button(toolbar, text="➕ Новая заявка", bg="#4CAF50", fg="white", command=self.open_add_window).pack(side=LEFT, padx=5)
        Button(toolbar, text="✏️ Редактировать", bg="#FF9800", fg="white", command=self.open_edit_window).pack(side=LEFT, padx=5)
        Button(toolbar, text="💬 Комментарии", bg="#9C27B0", fg="white", command=self.open_comments_window).pack(side=LEFT, padx=5)
        
        # Кнопка для ОТДЕЛЬНЫХ СТРАНИЦ (CRUD таблиц)
        crud_btn = Menubutton(toolbar, text="📚 Справочники (CRUD)", bg="#607D8B", fg="white", relief=RAISED)
        crud_btn.menu = Menu(crud_btn, tearoff=0)
        crud_btn["menu"] = crud_btn.menu
        crud_btn.menu.add_command(label="Управление статусами", command=lambda: self.open_crud_window("statuses", "status_id", "status_name"))
        crud_btn.menu.add_command(label="Управление ролями", command=lambda: self.open_crud_window("roles", "role_id", "role_name"))
        crud_btn.menu.add_command(label="Список пользователей", command=lambda: self.open_crud_window("users", "user_id", "fio"))
        crud_btn.pack(side=LEFT, padx=5)

        Button(toolbar, text="📊 Статистика", bg="#2196F3", fg="white", command=self.show_stats).pack(side=LEFT, padx=5)

        # Поиск (п. 2.3)
        Label(toolbar, text=" Поиск:", bg="#f0f0f0").pack(side=LEFT, padx=5)
        self.search_ent = Entry(toolbar)
        self.search_ent.pack(side=LEFT, padx=5)
        self.search_ent.bind("<KeyRelease>", lambda e: self.load_data(self.search_ent.get()))

        # Главная таблица (всё по п. 2.1)
        cols = ("id", "date", "type", "model", "client", "phone", "status", "master")
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        heads = {"id": "№", "date": "Дата", "type": "Тип", "model": "Модель", "client": "Клиент", "phone": "Телефон", "status": "Статус", "master": "Мастер"}
        for c, t in heads.items():
            self.tree.heading(c, text=t)
            self.tree.column(c, width=130, anchor=CENTER)
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def load_data(self, search=""):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT r.request_id, r.start_date, r.equipment_type, r.model, 
                               r.client_fio, r.client_phone,
                               COALESCE(s.status_name, 'Новая'), COALESCE(m.fio, '---')
                        FROM requests r
                        LEFT JOIN statuses s ON r.request_status_id = s.status_id
                        LEFT JOIN users m ON r.master_id = m.user_id
                    """
                    if search:
                        query += f" WHERE r.model ILIKE '%{search}%' OR r.client_fio ILIKE '%{search}%'"
                    query += " ORDER BY r.request_id DESC"
                    cur.execute(query)
                    for row in cur.fetchall(): self.tree.insert("", END, values=row)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    # --- CRUD ОКНО ДЛЯ ОТДЕЛЬНЫХ СТРАНИЦ ---
    def open_crud_window(self, table, id_col, name_col):
        win = Toplevel(self); win.title(f"CRUD: {table}"); win.geometry("450x450")
        f = Frame(win, padx=10, pady=10); f.pack(fill=BOTH)
        
        Label(f, text=f"Управление таблицей {table}", font=("Arial", 12, "bold")).pack(pady=5)
        entry = Entry(f); entry.pack(fill=X, pady=5)

        t = ttk.Treeview(f, columns=("id", "name"), show='headings', height=10)
        t.heading("id", text="ID"); t.heading("name", text="Значение")
        t.pack(fill=BOTH)

        def refresh():
            for i in t.get_children(): t.delete(i)
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT {id_col}, {name_col} FROM {table} ORDER BY {id_col}")
                    for r in cur.fetchall(): t.insert("", END, values=r)

        def add():
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"INSERT INTO {table} ({name_col}) VALUES (%s)", (entry.get(),))
                    conn.commit()
            refresh(); entry.delete(0, END)

        def delete():
            sel = t.selection()
            if not sel: return
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"DELETE FROM {table} WHERE {id_col} = %s", (t.item(sel)['values'][0],))
                    conn.commit()
            refresh()

        btns = Frame(f); btns.pack(pady=10)
        Button(btns, text="Добавить", bg="green", fg="white", command=add).pack(side=LEFT, padx=5)
        Button(btns, text="Удалить", bg="red", fg="white", command=delete).pack(side=LEFT, padx=5)
        refresh()

    # --- СТАНДАРТНЫЕ ФУНКЦИИ ПО ТЗ ---
    def open_add_window(self):
        win = Toplevel(self); win.title("Новая заявка"); f = Frame(win, padx=20, pady=20); f.pack()
        fields = ["Тип", "Модель", "Описание", "ФИО Клиента", "Телефон"]
        ents = []
        for lab in fields:
            Label(f, text=lab).pack(anchor=W); e = Entry(f, width=40); e.pack(pady=2); ents.append(e)
        Button(f, text="Сохранить", bg="green", fg="white", command=lambda: self.save_req(ents, win)).pack(pady=10)

    def save_req(self, ents, w):
        v = [e.get() for e in ents]
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO requests (start_date, equipment_type, model, problem_description, client_fio, client_phone, request_status_id) VALUES (CURRENT_DATE, %s, %s, %s, %s, %s, 1)", (v[0], v[1], v[2], v[3], v[4]))
                conn.commit()
        w.destroy(); self.load_data()

    def open_edit_window(self):
        sel = self.tree.selection()
        if not sel: return
        rid = self.tree.item(sel)['values'][0]
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT problem_description, request_status_id, master_id FROM requests WHERE request_id = %s", (rid,))
                curr = cur.fetchone()
        win = Toplevel(self); win.title(f"Правка №{rid}"); f = Frame(win, padx=20, pady=20); f.pack()
        Label(f, text="Описание:").pack(); e_d = Entry(f, width=40); e_d.insert(0, curr[0] or ""); e_d.pack()
        Label(f, text="ID Статуса:").pack(); e_s = Entry(f, width=40); e_s.insert(0, curr[1] or "1"); e_s.pack()
        Label(f, text="ID Мастера:").pack(); e_m = Entry(f, width=40); e_m.insert(0, curr[2] or ""); e_m.pack()
        Button(f, text="Обновить", bg="orange", command=lambda: self.save_edit(rid, e_d.get(), e_s.get(), e_m.get(), win)).pack(pady=10)

    def save_edit(self, rid, d, s, m, w):
        m_id = m if m.strip() else None
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("UPDATE requests SET problem_description=%s, request_status_id=%s, master_id=%s WHERE request_id=%s", (d, s, m_id, rid))
                conn.commit()
        w.destroy(); self.load_data()

    def open_comments_window(self):
        sel = self.tree.selection()
        if not sel: return
        rid = self.tree.item(sel)['values'][0]
        win = Toplevel(self); f = Frame(win, padx=20, pady=20); f.pack()
        txt = Text(f, width=40, height=10); txt.pack()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT message FROM comments WHERE request_id = %s", (rid,))
                for c in cur.fetchall(): txt.insert(END, f"• {c[0]}\n")
        e_c = Entry(f, width=40); e_c.pack(); Button(f, text="Добавить", command=lambda: self.add_comment(rid, e_c.get(), win)).pack()

    def add_comment(self, rid, msg, w):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO comments (request_id, message) VALUES (%s, %s)", (rid, msg)); conn.commit()
        w.destroy()

    def show_stats(self):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM requests WHERE request_status_id::text IN ('3', 'Завершена')")
                done = cur.fetchone()[0]
                messagebox.showinfo("Статистика", f"Выполнено заявок: {done}")

if __name__ == "__main__":
    app = RepairApp()
    app.mainloop()