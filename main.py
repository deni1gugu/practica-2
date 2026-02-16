# -*- coding: utf-8 -*-
import os
os.environ['PGCLIENTENCODING'] = 'utf8'
import psycopg2
from tkinter import *
from tkinter import messagebox, ttk

# --- НАСТРОЙКИ ПОДКЛЮЧЕНИЯ ---
DB_PARAMS = {
    "dbname": "RepairServiceDB", 
    "user": "postgres", 
    "password": "Storm_shadow2006", 
    "host": "localhost", 
    "port": "5432"
}

def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_client_encoding('UTF8')
    return conn

class RepairApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("ООО 'Конди' - Информационная система (Полный CRUD)")
        self.geometry("1300x700")
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        toolbar = Frame(self, pady=10, bg="#f5f5f5")
        toolbar.pack(side=TOP, fill=X)

        # 1. ОСНОВНЫЕ ОПЕРАЦИИ С ЗАЯВКАМИ (Таблица Requests)
        Button(toolbar, text="➕ Новая заявка", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
               command=self.open_add_window).pack(side=LEFT, padx=5)
        
        Button(toolbar, text="✏️ Редактировать", bg="#FF9800", fg="white", 
               command=self.open_edit_window).pack(side=LEFT, padx=5)
        
        Button(toolbar, text="💬 Журнал (Комменты)", bg="#9C27B0", fg="white", 
               command=self.open_comments_window).pack(side=LEFT, padx=5)

        # 2. ОТДЕЛЬНЫЕ СТРАНИЦЫ CRUD (Требование преподавателя)
        dict_menu = Menubutton(toolbar, text="📚 Справочники (CRUD)", bg="#607D8B", fg="white", relief=RAISED)
        dict_menu.menu = Menu(dict_menu, tearoff=0)
        dict_menu["menu"] = dict_menu.menu
        
        # CRUD для Roles
        dict_menu.menu.add_command(label="👤 Роли (Roles)", 
            command=lambda: self.open_crud_window("roles", "role_id", "role_name"))
        # CRUD для Statuses
        dict_menu.menu.add_command(label="📊 Статусы (Statuses)", 
            command=lambda: self.open_crud_window("statuses", "status_id", "status_name"))
        # CRUD для Users
        dict_menu.menu.add_command(label="👥 Пользователи (Users)", 
            command=lambda: self.open_crud_window("users", "user_id", "fio"))
        # CRUD для Comments (как отдельная сущность)
        dict_menu.menu.add_command(label="📝 Все записи (Comments)", 
            command=lambda: self.open_crud_window("comments", "comment_id", "message"))
            
        dict_menu.pack(side=LEFT, padx=5)

        Button(toolbar, text="📊 Статистика", bg="#2196F3", fg="white", 
               command=self.show_stats).pack(side=LEFT, padx=5)

        # Поиск
        Label(toolbar, text="  🔍 Поиск:", bg="#f5f5f5").pack(side=LEFT)
        self.search_ent = Entry(toolbar, width=25)
        self.search_ent.pack(side=LEFT, padx=5)
        self.search_ent.bind("<KeyRelease>", lambda e: self.load_data(self.search_ent.get()))

        # Главная таблица (Requests)
        columns = ("id", "date", "type", "model", "client", "phone", "status", "master")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        headers = {"id": "№", "date": "Дата", "type": "Тип", "model": "Модель", 
                   "client": "Клиент", "phone": "Телефон", "status": "Статус", "master": "Мастер"}
        for col, text in headers.items():
            self.tree.heading(col, text=text)
            self.tree.column(col, width=140, anchor=CENTER)
        self.tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

    def load_data(self, search=""):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    query = """
                        SELECT r.request_id, r.start_date, r.equipment_type, r.model, 
                               r.client_fio, r.client_phone,
                               COALESCE(s.status_name, '---'), 
                               COALESCE(m.fio, '---')
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

    # --- УНИВЕРСАЛЬНЫЙ МОДУЛЬ CRUD ДЛЯ ОТДЕЛЬНЫХ СТРАНИЦ ---
    def open_crud_window(self, table, id_col, name_col):
        win = Toplevel(self); win.title(f"Управление: {table}"); win.geometry("500x500")
        f = Frame(win, padx=15, pady=15); f.pack(fill=BOTH, expand=True)
        
        Label(f, text=f"Добавить новую запись в {table}:").pack(anchor=W)
        entry = Entry(f, width=40); entry.pack(fill=X, pady=5)

        t = ttk.Treeview(f, columns=("id", "val"), show='headings')
        t.heading("id", text="ID"); t.heading("val", text="Наименование/Текст")
        t.pack(fill=BOTH, expand=True)

        def refresh():
            for i in t.get_children(): t.delete(i)
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT {id_col}, {name_col} FROM {table} ORDER BY {id_col}")
                    for row in cur.fetchall(): t.insert("", END, values=row)

        def add():
            if not entry.get(): return
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"INSERT INTO {table} ({name_col}) VALUES (%s)", (entry.get(),))
                    conn.commit()
            entry.delete(0, END); refresh()

        def delete():
            sel = t.selection()
            if not sel: return
            if messagebox.askyesno("Подтверждение", "Удалить запись?"):
                with get_db_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(f"DELETE FROM {table} WHERE {id_col} = %s", (t.item(sel)['values'][0],))
                        conn.commit()
                refresh()

        btns = Frame(f); btns.pack(pady=10)
        Button(btns, text="Создать (C)", bg="green", fg="white", command=add).pack(side=LEFT, padx=5)
        Button(btns, text="Удалить (D)", bg="red", fg="white", command=delete).pack(side=LEFT, padx=5)
        refresh()

    # --- ФУНКЦИИ ДЛЯ ЗАЯВОК ---
    def open_add_window(self):
        win = Toplevel(self); win.title("Новая заявка"); f = Frame(win, padx=20, pady=20); f.pack()
        fields = ["Тип", "Модель", "Описание проблемы", "ФИО Клиента", "Телефон"]
        ents = []
        for l in fields:
            Label(f, text=l).pack(anchor=W); e = Entry(f, width=45); e.pack(pady=2); ents.append(e)
        Button(f, text="СОХРАНИТЬ", bg="green", fg="white", command=lambda: self.save_req(ents, win)).pack(pady=15)

    def save_req(self, ents, w):
        v = [e.get() for e in ents]
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""INSERT INTO requests (start_date, equipment_type, model, problem_description, client_fio, client_phone, request_status_id) 
                                   VALUES (CURRENT_DATE, %s, %s, %s, %s, %s, 1)""", (v[0], v[1], v[2], v[3], v[4]))
                    conn.commit()
            w.destroy(); self.load_data()
        except Exception as e: messagebox.showerror("Ошибка", e)

    def open_edit_window(self):
        sel = self.tree.selection()
        if not sel: return
        rid = self.tree.item(sel)['values'][0]
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT problem_description, request_status_id, master_id FROM requests WHERE request_id = %s", (rid,))
                res = cur.fetchone()
        
        win = Toplevel(self); win.title(f"Правка №{rid}"); f = Frame(win, padx=20, pady=20); f.pack()
        Label(f, text="Описание:").pack(); ed = Entry(f, width=40); ed.insert(0, res[0] or ""); ed.pack()
        Label(f, text="ID Статуса:").pack(); es = Entry(f, width=40); es.insert(0, res[1] or "1"); es.pack()
        Label(f, text="ID Мастера:").pack(); em = Entry(f, width=40); em.insert(0, res[2] or ""); em.pack()
        Button(f, text="ОБНОВИТЬ", bg="orange", command=lambda: self.save_edit(rid, ed.get(), es.get(), em.get(), win)).pack(pady=10)

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
        win = Toplevel(self); win.title("Журнал работ"); f = Frame(win, padx=20, pady=20); f.pack()
        txt = Text(f, width=45, height=10); txt.pack()
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT message FROM comments WHERE request_id = %s", (rid,))
                for c in cur.fetchall(): txt.insert(END, f"• {c[0]}\n")
        e_c = Entry(f, width=45); e_c.pack(pady=5)
        Button(f, text="Добавить запись", command=lambda: self.add_comment(rid, e_c.get(), win)).pack()

    def add_comment(self, rid, msg, w):
        if not msg: return
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO comments (request_id, message) VALUES (%s, %s)", (rid, msg)); conn.commit()
        w.destroy()

    def show_stats(self):
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM requests WHERE request_status_id = 3")
                done = cur.fetchone()[0]
                messagebox.showinfo("Статистика", f"Выполнено ремонтов: {done}")

if __name__ == "__main__":
    app = RepairApp()
    app.mainloop()