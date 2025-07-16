import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3, calendar
from datetime import datetime, timedelta
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

def init_profile_db():
    with sqlite3.connect("habits.db") as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS profile (
            id INTEGER PRIMARY KEY, name TEXT, age INTEGER, height REAL, weight REAL, phone TEXT, address TEXT)''')

def get_profile():
    with sqlite3.connect("habits.db") as conn:
        return conn.execute("SELECT name, age, height, weight, phone, address FROM profile WHERE id=1").fetchone()

def save_profile(name, age, height, weight, phone, address):
    with sqlite3.connect("habits.db") as conn:
        conn.execute("INSERT OR REPLACE INTO profile (id, name, age, height, weight, phone, address) VALUES (1,?,?,?,?,?,?)",
                     (name, age, height, weight, phone, address))

class HabitTrackerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HABIT TRACKER APPLICATION")
        self.state('zoom')
        self.configure(bg="#e7f1fb")
        self.selected_date = datetime.now().strftime("%Y-%m-%d")
        self.placeholder_active = False
        self.dark_mode = False
        self.profile_display_frame = None
        self.details_year, self.details_month = datetime.now().year, datetime.now().month
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11), padding=5, background="#469ed0", foreground="white")
        style.configure("TLabel", font=("Segoe UI", 11), background="#e7f1fb")
        style.configure("Card.TFrame", background="white", relief="raised", borderwidth=1)
        style.configure("Nav.TFrame", background="#469ed0")
        style.configure("StatusCard.TFrame", background="white", relief="flat", borderwidth=0)
        style.configure("ProfileCard.TFrame", background="white", relief="raised", borderwidth=1)
        self.init_db()
        self.create_widgets()

    def init_db(self):
        with sqlite3.connect("habits.db") as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL)''')
            conn.execute('''CREATE TABLE IF NOT EXISTS habit_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT, habit_id INTEGER, date TEXT, status TEXT DEFAULT 'Not Completed')''')
        init_profile_db()

    def create_widgets(self):
        nav_frame = ttk.Frame(self, style="Nav.TFrame", width=170)
        nav_frame.pack(side="left", fill="y")
        tk.Label(nav_frame, text="🌟", bg="#469ed0", fg="white", font=("Segoe UI", 32)).pack(pady=15)
        for txt, cmd in [("Home", self.create_home), ("Habits Details", self.create_habits_details), ("Settings", self.create_settings_section)]:
            ttk.Button(nav_frame, text=txt, width=20, command=cmd).pack(pady=10)
        self.main_frame = tk.Frame(self, bg="#e7f1fb")
        self.main_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        self.create_home()

    def set_dark_mode(self, enabled):
        self.dark_mode = enabled
        bg, fg = ("#23272e", "#f1c40f") if enabled else ("#e7f1fb", "#469ed0")
        card_bg = "#23272e" if enabled else "white"
        label_fg, text_fg, text_bg = (fg, fg, "#23272e") if enabled else (fg, "#2d87f0", "#fafcff")
        self.configure(bg=bg); self.main_frame.configure(bg=bg)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 11), padding=5, background=fg, foreground="white")
        style.configure("TLabel", font=("Segoe UI", 11), background=card_bg, foreground=label_fg)
        style.configure("Card.TFrame", background=card_bg)
        style.configure("Nav.TFrame", background=fg)
        style.configure("StatusCard.TFrame", background=card_bg)
        style.configure("ProfileCard.TFrame", background=card_bg)
        style.configure("TEntry", fieldbackground=card_bg, foreground=label_fg)
        style.configure("TCheckbutton", background=card_bg, foreground=label_fg)
        style.map('TButton', background=[('active', fg)])
        def deep_update(widget):
            for child in widget.winfo_children():
                if isinstance(child, ttk.Frame):
                    style_name = child.winfo_class()
                    if "TFrame" in style_name: child.configure(style=f"{style_name}")
                elif isinstance(child, tk.Label): child.configure(bg=card_bg, fg=label_fg)
                elif isinstance(child, tk.Entry): child.configure(bg=card_bg, fg=label_fg, insertbackground=label_fg)
                elif isinstance(child, tk.Text): child.configure(bg=text_bg, fg=text_fg, insertbackground=text_fg)
                elif isinstance(child, tk.Frame): child.configure(bg=card_bg)
                elif isinstance(child, tk.Canvas): child.configure(bg=card_bg)
                elif isinstance(child, tk.Button): child.configure(bg=fg, fg="white", activebackground=label_fg)
                deep_update(child)
        deep_update(self.main_frame)
        if self.profile_display_frame: deep_update(self.profile_display_frame)

    def clear_main_frame(self): [w.destroy() for w in self.main_frame.winfo_children()]

    # =============== HOMEPAGE SECTION ===============
    def create_home(self):
        self.clear_main_frame()
        top_frame = ttk.Frame(self.main_frame, style="Card.TFrame")
        top_frame.pack(fill="x", pady=12, padx=10)
        self.habit_entry = ttk.Entry(top_frame, width=40, font=("Segoe UI", 12), foreground="gray")
        self.placeholder_text = "Track a new productive habit..."
        self.habit_entry.insert(0, self.placeholder_text); self.placeholder_active = True
        self.habit_entry.bind("<FocusIn>", self.clear_placeholder)
        self.habit_entry.bind("<FocusOut>", self.restore_placeholder)
        self.habit_entry.pack(side="left", padx=10, pady=10)
        ttk.Button(top_frame, text="Add to Dashboard", command=self.add_habit).pack(side="left", padx=10, pady=10)
        middle_frame = tk.Frame(self.main_frame, bg="#e7f1fb")
        middle_frame.pack(fill="both", expand=True, pady=10)
        middle_frame.columnconfigure(0, weight=1); middle_frame.columnconfigure(1, weight=1); middle_frame.rowconfigure(0, weight=1)
        habit_card = ttk.Frame(middle_frame, style="Card.TFrame")
        habit_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=0)
        habit_card.pack_propagate(False); habit_card.config(width=600, height=550)
        tk.Label(habit_card, text="Today's Habits", font=("Segoe UI", 16, "bold"), bg="white", fg="#469ed0").pack(pady=12)
        canvas = tk.Canvas(habit_card, bg="white", borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(habit_card, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg="white")
        scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((20, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.habit_buttons_frame = scroll_frame
        chart_card = ttk.Frame(middle_frame, style="Card.TFrame")
        chart_card.grid(row=0, column=1, sticky="nsew", padx=(10,0), pady=0)
        chart_card.pack_propagate(False)
        chart_card.config(width=600, height=550)
        tk.Label(chart_card, text="Today's Completion Pie", bg="white", font=("Segoe UI", 20, "bold"), fg="#53ba83").pack(pady=12)
        self.pie_canvas = tk.Frame(chart_card, bg="white")
        self.pie_canvas.pack(pady=3, padx=5, fill="both", expand=True)
        tk.Label(chart_card, text="Weekly Progress Bar", bg="white", font=("Segoe UI", 20, "bold"), fg="#469ed0").pack(pady=16)
        self.bar_canvas = tk.Frame(chart_card, bg="white")
        self.bar_canvas.pack(pady=3, padx=5, fill="both", expand=True)
        bottom_frame = ttk.Frame(self.main_frame, style="StatusCard.TFrame")
        bottom_frame.pack(fill="x", pady=18, padx=10)
        self.streak_label = tk.Label(bottom_frame, text="🔥Daily Streak: 0", bg="white", font=("Montserrat", 22, "bold"),
            fg="#ff8c42", width=20, height=2, anchor="w", padx=30)
        self.streak_label.pack(side="left", padx=30, pady=10, expand=True, fill="both")
        self.completion_label = tk.Label(bottom_frame, text="📊 Success Rate: 0.0%", bg="white", font=("Montserrat", 22, "bold"),
            fg="#2d87f0", width=20, height=2, anchor="e", padx=30)
        self.completion_label.pack(side="right", padx=30, pady=10, expand=True, fill="both")
        self.load_today_habits(); self.draw_pie_chart(); self.draw_bar_chart()

    def clear_placeholder(self, event):
        if self.placeholder_active:
            self.habit_entry.delete(0, tk.END)
            self.habit_entry.config(foreground="black")
            self.placeholder_active = False
    def restore_placeholder(self, event):
        if not self.habit_entry.get():
            self.habit_entry.insert(0, self.placeholder_text)
            self.habit_entry.config(foreground="gray")
            self.placeholder_active = True

    def add_habit(self):
        habit = self.habit_entry.get().strip()
        if habit == "" or (self.placeholder_active and habit == self.placeholder_text):
            messagebox.showwarning("Input Needed", "Please enter a habit to add."); return
        with sqlite3.connect("habits.db") as conn:
            conn.execute("INSERT INTO habits (name) VALUES (?)", (habit,))
        self.habit_entry.delete(0, tk.END)
        self.restore_placeholder(None)
        self.load_today_habits(); self.draw_pie_chart(); self.draw_bar_chart()

    def load_today_habits(self):
        [w.destroy() for w in self.habit_buttons_frame.winfo_children()]
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect("habits.db") as conn:
            habits = conn.execute("SELECT id, name FROM habits").fetchall()
            for habit_id, name in habits:
                result = conn.execute("SELECT status FROM habit_status WHERE habit_id=? AND date=?", (habit_id, today)).fetchone()
                status = result[0] if result else "Not Completed"
                row = tk.Frame(self.habit_buttons_frame, bg="white")
                row.pack(fill="x", pady=4, padx=3)
                ttk.Button(row, text=name, width=24, style="TButton", command=lambda hid=habit_id: self.toggle_status(hid)).pack(side="left", padx=(0, 8))
                tk.Label(row, text=status, bg="white",
                    fg="#53ba83" if status == "Completed" else "#e74c3c", font=("Segoe UI", 11, "bold"), width=14, anchor="w").pack(side="left", padx=(5, 8))
                ttk.Button(row, text="Delete", width=7, command=lambda hid=habit_id: self.delete_habit(hid)).pack(side="left", padx=(8, 8))
        self.update_stats()

    def toggle_status(self, habit_id):
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect("habits.db") as conn:
            result = conn.execute("SELECT status FROM habit_status WHERE habit_id=? AND date=?", (habit_id, today)).fetchone()
            if result:
                new_status = "Completed" if result[0] != "Completed" else "Not Completed"
                conn.execute("UPDATE habit_status SET status=? WHERE habit_id=? AND date=?", (new_status, habit_id, today))
            else:
                conn.execute("INSERT INTO habit_status (habit_id, date, status) VALUES (?, ?, ?)", (habit_id, today, "Completed"))
        self.load_today_habits(); self.draw_pie_chart(); self.draw_bar_chart()

    def delete_habit(self, habit_id):
        if messagebox.askyesno("Delete Habit", "Are you sure you want to delete this habit and all its data?"):
            with sqlite3.connect("habits.db") as conn:
                conn.execute("DELETE FROM habits WHERE id=?", (habit_id,))
                conn.execute("DELETE FROM habit_status WHERE habit_id=?", (habit_id,))
            self.load_today_habits(); self.draw_pie_chart(); self.draw_bar_chart()

    def update_stats(self):
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect("habits.db") as conn:
            total = conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM habit_status WHERE date=? AND status='Completed'", (today,)).fetchone()[0]
        self.streak_label.config(text=f"🔥Daily Streak: {self.calculate_streak()}")
        self.completion_label.config(text=f"📊 Success Rate: {(completed/total*100) if total else 0.0:.1f}%")

    def calculate_streak(self):
        with sqlite3.connect("habits.db") as conn:
            habits_count = conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
            if not habits_count: return 0
            streak, day = 0, datetime.now()
            while True:
                date_str = day.strftime("%Y-%m-%d")
                completed = conn.execute("SELECT COUNT(*) FROM habit_status WHERE date=? AND status='Completed'", (date_str,)).fetchone()[0]
                if completed == habits_count: streak += 1; day -= timedelta(days=1)
                else: break
        return streak

    def draw_pie_chart(self):
        [w.destroy() for w in self.pie_canvas.winfo_children()]
        today = datetime.now().strftime("%Y-%m-%d")
        with sqlite3.connect("habits.db") as conn:
            total = conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
            completed = conn.execute("SELECT COUNT(*) FROM habit_status WHERE date=? AND status='Completed'", (today,)).fetchone()[0]
        not_completed = total - completed if total else 0
        values = [completed, not_completed]
        fig, ax = plt.subplots(figsize=(4, 2.2))
        if sum(values) > 0:
            ax.pie(values, labels=["Completed", "Not Completed"], autopct="%1.0f%%", colors=["#53ba83", "#d03333"], startangle=90)
        else:
            ax.pie([1], labels=["No Data"], colors=["#cccccc"], startangle=90)
        ax.axis("equal"); plt.tight_layout()
        FigureCanvasTkAgg(fig, master=self.pie_canvas).get_tk_widget().pack()
        plt.close(fig)

    def draw_bar_chart(self):
        [w.destroy() for w in self.bar_canvas.winfo_children()]
        today = datetime.now()
        dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(6, -1, -1)]
        with sqlite3.connect("habits.db") as conn:
            total = conn.execute("SELECT COUNT(*) FROM habits").fetchone()[0]
            completed_list = [(conn.execute("SELECT COUNT(*) FROM habit_status WHERE date=? AND status='Completed'", (d,)).fetchone()[0]/total*100) if total else 0 for d in dates]
        fig, ax = plt.subplots(figsize=(3, 2.2))
        ax.bar(range(7), completed_list, color="#28aed3")
        ax.set_ylim(0, 100)
        ax.set_xticks(range(7))
        ax.set_xticklabels([(today - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)], fontsize=9)
        ax.set_ylabel("Completion (%)"); plt.tight_layout()
        FigureCanvasTkAgg(fig, master=self.bar_canvas).get_tk_widget().pack()
        plt.close(fig)

    # =============== HABITS DETAILS SECTION ===============
    def create_habits_details(self):
        self.clear_main_frame()
        detail_card = ttk.Frame(self.main_frame, style="Card.TFrame")
        detail_card.pack(pady=20, padx=30, ipadx=40, ipady=30, fill="y")
        tk.Label(detail_card, text="📅 Habit Details", font=("Segoe UI", 20, "bold"), bg="white", fg="#2d87f0").pack(pady=(0, 20))
        cal_control_frame = tk.Frame(detail_card, bg="white"); cal_control_frame.pack()
        ttk.Button(cal_control_frame, text="◀", width=3, command=self.prev_month).pack(side="left", padx=10)
        self.cal_month_label = tk.Label(cal_control_frame, text="", font=("Segoe UI", 14, "bold"), bg="white", fg="#2d87f0")
        self.cal_month_label.pack(side="left", padx=6)
        ttk.Button(cal_control_frame, text="▶", width=3, command=self.next_month).pack(side="left", padx=10)
        self.cal_frame = tk.Frame(detail_card, bg="white"); self.cal_frame.pack()
        self.draw_calendar(self.cal_frame, self.details_year, self.details_month)
        self.details_status_frame = tk.Frame(detail_card, bg="white")
        self.details_status_frame.pack(pady=20, fill="x", padx=10)
        now = datetime.now(); self.load_details_for_date(now.year, now.month, now.day)

    def prev_month(self):
        self.details_year, self.details_month = (self.details_year - 1, 12) if self.details_month == 1 else (self.details_year, self.details_month - 1)
        self.refresh_calendar()

    def next_month(self):
        self.details_year, self.details_month = (self.details_year + 1, 1) if self.details_month == 12 else (self.details_year, self.details_month + 1)
        self.refresh_calendar()

    def refresh_calendar(self):
        [w.destroy() for w in self.cal_frame.winfo_children()]
        self.draw_calendar(self.cal_frame, self.details_year, self.details_month)
        self.cal_month_label.config(text=f"{calendar.month_name[self.details_month]} {self.details_year}")

    def draw_calendar(self, parent, year, month):
        if hasattr(self, "cal_month_label"):
            self.cal_month_label.config(text=f"{calendar.month_name[month]} {year}")
        cal = calendar.monthcalendar(year, month)
        days_frame = tk.Frame(parent, bg="white"); days_frame.pack()
        [tk.Label(days_frame, text=day, font=("Segoe UI", 11, "bold"), bg="white", fg="#469ed0", width=8).grid(row=0, column=idx)
            for idx, day in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])]
        for r, week in enumerate(cal):
            for c, day in enumerate(week):
                if day == 0:
                    tk.Label(days_frame, text="", bg="white", width=6).grid(row=r+1, column=c)
                else:
                    ttk.Button(days_frame, text=str(day), width=7, command=lambda d=day: self.load_details_for_date(year, month, d)).grid(row=r+1, column=c, padx=4, pady=4)

    def load_details_for_date(self, year, month, day):
        [w.destroy() for w in self.details_status_frame.winfo_children()]
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        with sqlite3.connect("habits.db") as conn:
            habits = conn.execute("SELECT name, id FROM habits").fetchall()
            tk.Label(self.details_status_frame, text=f"Habits on {date_str}:", font=("Segoe UI", 15, "bold"), bg="white", fg="#2d87f0").pack(anchor="w")
            for name, hid in habits:
                result = conn.execute("SELECT status FROM habit_status WHERE habit_id=? AND date=?", (hid, date_str)).fetchone()
                status = result[0] if result else "Not Completed"
                fg = "#53ba83" if status == "Completed" else "#e74c3c"
                tk.Label(self.details_status_frame, text=f"  - {name}: {status}", bg="white", fg=fg, font=("Segoe UI", 12, "bold"), anchor="w", justify="left").pack(anchor="w")

    # =============== SETTINGS & PROFILE SECTION ===============
    def create_profile_section(self): self.create_settings_section()
    def create_settings_section(self):
        self.clear_main_frame()
        card = ttk.Frame(self.main_frame, style="ProfileCard.TFrame")
        card.pack(pady=30, padx=120, ipadx=40, ipady=30, fill="both", expand=True)
        profile_section = tk.LabelFrame(card, text="👤 Your Profile", bg="white", fg="#2d87f0", font=("Segoe UI", 17, "bold"),
            bd=2, relief="groove", padx=14, pady=10)
        profile_section.pack(fill="x", padx=10, pady=(0,30))
        data = get_profile() or ["", "", "", "", "", ""]
        labels = ["Name:", "Age:", "Height (cm):", "Weight (kg):", "Phone Number:", "Address:"]
        self.profile_vars = []
        for i, label in enumerate(labels):
            tk.Label(profile_section, text=label, bg="white", font=("Segoe UI", 13, "bold"), anchor="e").grid(row=i, column=0, sticky="e", pady=6, padx=6)
            var = tk.StringVar(value=str(data[i]) if data[i] is not None else "")
            ttk.Entry(profile_section, textvariable=var, width=28, font=("Segoe UI", 12)).grid(row=i, column=1, pady=6, padx=6, sticky="w")
            self.profile_vars.append(var)
        ttk.Button(profile_section, text="Save Profile", command=self.save_profile_action).grid(row=len(labels), column=0, columnspan=2, pady=12)
        if self.profile_display_frame: self.profile_display_frame.destroy()
        self.profile_display_frame = tk.Frame(card, bg="white"); self.profile_display_frame.pack(fill="x", padx=10)
        profile = get_profile()
        if profile and any(profile):
            tk.Label(self.profile_display_frame, text="Profile Details:", font=("Segoe UI", 13, "bold"), anchor="w", bg="white", fg="#2d87f0").pack(anchor="w")
            for i, label in enumerate(["Name", "Age", "Height (cm)", "Weight (kg)", "Phone", "Address"]):
                value = profile[i] if profile and profile[i] is not None else ""
                tk.Label(self.profile_display_frame, text=f"{label}: {value}", anchor="w", bg="white", font=("Segoe UI", 12)).pack(anchor="w")
        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=18)
        tk.Label(card, text="⚙️ Settings", font=("Segoe UI", 20, "bold"), bg="white", fg="#2d87f0").pack(anchor="w", pady=(0,8), padx=10)
        dark_var = tk.BooleanVar(value=self.dark_mode)
        ttk.Checkbutton(card, text="Enable Dark Mode", variable=dark_var, command=lambda: self.set_dark_mode(dark_var.get())).pack(anchor="w", pady=8, padx=14)
        def reset_habits():
            if messagebox.askyesno("Reset All Habits", "Are you sure you want to delete all habits and their statuses? This cannot be undone."):
                with sqlite3.connect("habits.db") as conn:
                    conn.execute("DELETE FROM habits"); conn.execute("DELETE FROM habit_status")
                self.load_today_habits(); messagebox.showinfo("Reset Complete", "All habits have been deleted.")
        ttk.Button(card, text="Reset All Habits", command=reset_habits).pack(anchor="w", pady=12, padx=14)
        ttk.Separator(card, orient="horizontal").pack(fill="x", pady=18)
        tk.Label(card, text="ℹ️ About Us", font=("Segoe UI", 20, "bold"), bg="white", fg="#2d87f0").pack(anchor="w", pady=(0, 10), padx=10)
        about_text = (
            "Momentum - Daily Habit Architect\n"
            "Version 1.0\n\n"
            "This application helps you track, build, and maintain daily productive habits.\n"
            "Developed by Chirag Meher.\n\n"
            "Contact: chiragmeher06@example.com\n"
        )
        tk.Label(card, text=about_text, bg="white", fg="#444", font=("Segoe UI", 13), justify="left").pack(anchor="w", padx=10)

    def save_profile_action(self):
        vals = [v.get() for v in self.profile_vars]
        try:
            save_profile(vals[0], int(vals[1]), float(vals[2]), float(vals[3]), vals[4], vals[5])
            messagebox.showinfo("Profile Saved", "Your profile has been saved successfully!")
            [v.set("") for v in self.profile_vars]
            if self.profile_display_frame:
                [w.destroy() for w in self.profile_display_frame.winfo_children()]
            profile = get_profile()
            tk.Label(self.profile_display_frame, text="Profile Details:", font=("Segoe UI", 13, "bold"), anchor="w", bg="white", fg="#2d87f0").pack(anchor="w")
            for i, label in enumerate(["Name", "Age", "Height (cm)", "Weight (kg)", "Phone", "Address"]):
                value = profile[i] if profile and profile[i] is not None else ""
                tk.Label(self.profile_display_frame, text=f"{label}: {value}", anchor="w", bg="white", font=("Segoe UI", 12)).pack(anchor="w")
            if self.dark_mode: self.set_dark_mode(True)
        except Exception as e:
            messagebox.showerror("Invalid Entry", "Please check your input values.\n" + str(e))

if __name__ == "__main__":
    app = HabitTrackerApp()
    app.mainloop()