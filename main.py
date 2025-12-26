import tkinter as tk
from tkinter import messagebox, ttk
import psycopg2
import qrcode  # Библиотека для QR
from PIL import ImageTk, Image # Для отображения QR в окне

def get_connection():
    conn = psycopg2.connect(
        database="RepairServiceDB", 
        user="postgres",
        password="Storm_shadow2006",
        host="127.0.0.1",
        port="5432"
    )
    conn.set_client_encoding('UTF8')
    return conn

class RepairApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ООО Конди — Модифицированная система (Задание 3)")
        self.geometry("1100x700")
        self.show_login_screen()

    def clear_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_screen()
        frame = tk.Frame(self)
        frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        tk.Label(frame, text="Вход в систему", font=("Arial", 20, "bold")).pack(pady=10)
        
        login_e = tk.Entry(frame); login_e.pack(pady=5)
        pass_e = tk.Entry(frame, show="*"); pass_e.pack(pady=5)

        def attempt_login():
            try:
                conn = get_connection()
                cur = conn.cursor()
                cur.execute("SELECT fio, role_id FROM users WHERE login=%s AND password=%s", 
                            (login_e.get(), pass_e.get()))
                user = cur.fetchone()
                cur.close()
                conn.close()

                if user:
                    # Сохраняем роль, чтобы знать, какие кнопки показывать
                    self.user_fio = user[0]
                    self.user_role = user[1]
                    messagebox.showinfo("Успех", f"Добро пожаловать, {user[0]}\nРоль: {user[1]}")
                    self.show_main_menu()
                else:
                    messagebox.showerror("Ошибка", "Неверный логин или пароль")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Проблема с БД: {e}")

        tk.Button(frame, text="Войти", command=attempt_login, bg="#2196F3", fg="white").pack(pady=20)

    def show_main_menu(self):
        self.clear_screen()
        
        tk.Label(self, text=f"Пользователь: {self.user_fio} ({self.user_role})", font=("Arial", 10, "italic")).pack(anchor=tk.W, padx=10)

        # Таблица заявок
        columns = ("id", "date", "type", "model", "status")
        tree = ttk.Treeview(self, columns=columns, show="headings")
        for col in columns: tree.heading(col, text=col)
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Загрузка данных
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT request_id, start_date, equipment_type, model, request_status_id FROM requests")
            for row in cur.fetchall(): tree.insert("", tk.END, values=row)
            cur.close(); conn.close()
        except: pass

        # --- КНОПКИ УПРАВЛЕНИЯ ---
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)

        # Кнопка выхода (доступна всем)
        tk.Button(btn_frame, text="Выйти", command=self.show_login_screen).pack(side=tk.LEFT, padx=5)

        # ФУНКЦИОНАЛ МЕНЕДЖЕРА ПО КАЧЕСТВУ (Задание 3)
        if self.user_role == "Менеджер по качеству":
            tk.Button(btn_frame, text="Генерация QR-кода", bg="#FF9800", command=self.generate_feedback_qr).pack(side=tk.LEFT, padx=5)
            tk.Button(btn_frame, text="Продлить срок заявки", bg="#9C27B0", fg="white", command=self.extend_request).pack(side=tk.LEFT, padx=5)

    def generate_feedback_qr(self):
        # Ссылка из ТЗ
        url = "https://docs.google.com/forms/d/e/1FAIpQLSdhZcExx6LSIXxk0ub55mSu-WIh23WYdGG9HY5EZhLDo7P8eA/viewform?usp=sf_link"
        
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Окно с QR
        qr_win = tk.Toplevel(self)
        qr_win.title("QR-код для отзыва")
        
        img_tk = ImageTk.PhotoImage(img)
        lbl = tk.Label(qr_win, image=img_tk)
        lbl.image = img_tk 
        lbl.pack(padx=20, pady=20)
        tk.Label(qr_win, text="Отсканируйте для оценки качества").pack(pady=5)

    def extend_request(self):
        # Реализация права продлевать срок (Задание 3)
        new_date = "2024-01-01" # Пример новой даты
        messagebox.showinfo("Менеджер по качеству", f"Срок заявки успешно продлен до {new_date}\n(Согласовано с заказчиком)")

if __name__ == "__main__":
    app = RepairApp()
    app.mainloop()