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

def get_db_connection():
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_client_encoding('UTF8')
    return conn

class RepairApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("ООО 'Конди' - Система управления ремонтами")
        self.geometry("1250x700")
        self.current_user_id = 1 
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        # Панель управления
        toolbar = Frame(self, pady=10, bg="#f5f5f5")
        toolbar.pack(side=TOP, fill=X)

        Button(toolbar, text="➕ Создать заявку", bg="#4CAF50", fg="white", font=("Arial", 9, "bold"),
               command=self.open_add_window).pack(side=LEFT, padx=5)
        
        Button(toolbar, text="✏️ Редактировать / Назначить", bg="#FF9800", fg="white", 
               command=self.open_edit_window).pack(side=LEFT, padx=5)
        
        Button(toolbar, text="💬 Журнал работ (Комменты)", bg="#9C27B0", fg="white", 
               command=self.open_comments_window).pack(side=LEFT, padx=5)
        
        Button(toolbar, text="📊 Статистика", bg="#2196F3", fg="white", 
               command=self.show_stats).pack(side=LEFT, padx=5)

        # Универсальный поиск (п. 2.3)
        Label(toolbar, text="  🔍 Поиск:", bg="#f5f5f5").pack(side=LEFT)
        self.search_ent = Entry(toolbar, width=25)
        self.search_ent.pack(side=LEFT, padx=5)
        self.search_ent.bind("<KeyRelease>", lambda e: self.load_data(self.search_ent.get()))

        # Таблица со всеми полями из ТЗ (п. 2.1, 2.3, 2.4)
        columns = ("id", "date", "type", "model", "client", "phone", "status", "master")
        self.tree = ttk.Treeview(self, columns=columns, show='headings')
        
        headers = {
            "id": "№", "date": "Дата", "type": "Тип", "model": "Модель", 
            "client": "ФИО Клиента", "phone": "Телефон", "status": "Статус", "master": "Мастер"
        }
        
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
                               COALESCE(s.status_name, 'Новая'), 
                               COALESCE(m.fio, 'Не назначен')
                        FROM requests r
                        LEFT JOIN statuses s ON r.request_status_id = s.status_id
                        LEFT JOIN users m ON r.master_id = m.user_id
                    """
                    if search:
                        if search.isdigit():
                            query += f" WHERE r.request_id = {search}"
                        else:
                            query += f" WHERE r.model ILIKE '%{search}%' OR r.client_fio ILIKE '%{search}%' OR r.client_phone ILIKE '%{search}%'"
                    
                    query += " ORDER BY r.request_id DESC"
                    cur.execute(query)
                    for row in cur.fetchall():
                        self.tree.insert("", END, values=row)
        except Exception as e:
            print(f"Ошибка загрузки: {e}")

    def open_add_window(self):
        """Пункт 2.1: Добавление заявок со всеми параметрами"""
        win = Toplevel(self); win.title("Новая заявка (ООО 'Конди')"); f = Frame(win, padx=20, pady=20); f.pack()
        
        labels = ["Тип оборудования:", "Модель устройства:", "Описание проблемы:", "ФИО заказчика:", "Номер телефона:"]
        self.add_entries = []
        for lab in labels:
            Label(f, text=lab).pack(anchor=W)
            e = Entry(f, width=45); e.pack(pady=5); self.add_entries.append(e)
            
        Button(f, text="ЗАРЕГИСТРИРОВАТЬ", bg="#4CAF50", fg="white", font=("Arial", 10, "bold"),
               command=lambda: self.save_req(win)).pack(pady=20)

    def save_req(self, w):
        v = [e.get() for e in self.add_entries]
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO requests (start_date, equipment_type, model, problem_description, client_fio, client_phone, request_status_id) 
                        VALUES (CURRENT_DATE, %s, %s, %s, %s, %s, 1)
                    """, (v[0], v[1], v[2], v[3], v[4]))
                    conn.commit()
            w.destroy(); self.load_data()
            messagebox.showinfo("Успех", "Заявка успешно добавлена!")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def open_edit_window(self):
        """Пункт 2.2 и 2.4: Редактирование и Назначение ответственного"""
        sel = self.tree.selection()
        if not sel: 
            messagebox.showwarning("Внимание", "Выберите заявку!")
            return
        rid = self.tree.item(sel)['values'][0]
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT problem_description, request_status_id, master_id FROM requests WHERE request_id = %s", (rid,))
                curr = cur.fetchone()

        win = Toplevel(self); win.title(f"Редактирование №{rid}"); f = Frame(win, padx=20, pady=20); f.pack()
        
        Label(f, text="Описание проблемы (п. 2.2):").pack(anchor=W)
        e_d = Entry(f, width=45); e_d.insert(0, curr[0] or ""); e_d.pack(pady=5)
        
        Label(f, text="Статус ID (1-Новая, 2-В работе, 3-Завершена):").pack(anchor=W)
        e_s = Entry(f, width=45); e_s.insert(0, curr[1] or "1"); e_s.pack(pady=5)
        
        Label(f, text="ID Мастера (Назначить ответственного п. 2.4):").pack(anchor=W)
        e_m = Entry(f, width=45); e_m.insert(0, curr[2] or ""); e_m.pack(pady=5)
        
        Button(f, text="ОБНОВИТЬ ДАННЫЕ", bg="#FF9800", fg="white", 
               command=lambda: self.save_edit(rid, e_d.get(), e_s.get(), e_m.get(), win)).pack(pady=15)

    def save_edit(self, rid, d, s, m, w):
        try:
            m_id = m if m.strip() else None
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("UPDATE requests SET problem_description=%s, request_status_id=%s, master_id=%s WHERE request_id=%s", (d, s, m_id, rid))
                    conn.commit()
            
            # Уведомление о завершении (п. 2.4)
            if str(s) == "3":
                messagebox.showinfo("Уведомление", f"Заявка №{rid} переведена в статус 'Завершена'!")
            
            w.destroy(); self.load_data()
        except Exception as e:
            messagebox.showerror("Ошибка", e)

    def open_comments_window(self):
        """Пункт 2.4: Комментарии специалиста и комплектующие"""
        sel = self.tree.selection()
        if not sel: return
        rid = self.tree.item(sel)['values'][0]
        
        win = Toplevel(self); win.title(f"Журнал работ по №{rid}"); f = Frame(win, padx=20, pady=20); f.pack()
        
        Label(f, text="История работ / Комплектующие:", font=("Arial", 10, "bold")).pack(anchor=W)
        txt = Text(f, width=50, height=10, bg="#f9f9f9"); txt.pack(pady=5)
        
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT created_at, message FROM comments WHERE request_id = %s ORDER BY created_at", (rid,))
                for date, msg in cur.fetchall():
                    txt.insert(END, f"[{date.strftime('%d.%m %H:%M')}] {msg}\n")
        txt.config(state=DISABLED)
        
        Label(f, text="Добавить запись (ход работы / запчасти):").pack(anchor=W, pady=(10,0))
        e_c = Entry(f, width=50); e_c.pack(pady=5)
        Button(f, text="Добавить в журнал", command=lambda: self.add_comment(rid, e_c.get(), win)).pack(pady=10)

    def add_comment(self, rid, msg, w):
        if not msg: return
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO comments (request_id, message) VALUES (%s, %s)", (rid, msg))
                    conn.commit()
            w.destroy(); messagebox.showinfo("Успех", "Запись добавлена в журнал")
        except Exception as e:
            messagebox.showerror("Ошибка", e)

    def show_stats(self):
        """Пункт 2.5: Статистика работы"""
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM requests WHERE request_status_id::text IN ('3', 'Завершена')")
                    done = cur.fetchone()[0]
                    cur.execute("SELECT COUNT(*) FROM requests")
                    total = cur.fetchone()[0]
                    messagebox.showinfo("Статистика отдела", f"📊 Всего заявок: {total}\n✅ Выполнено: {done}")
        except Exception as e:
            messagebox.showerror("Ошибка", e)

if __name__ == "__main__":
    app = RepairApp()
    app.mainloop()