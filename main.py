import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sqlite3
import csv
import math
from datetime import datetime
from PIL import Image, ImageTk


# ================= DATABASE & CONFIGURATION =================
def init_db():
    conn = sqlite3.connect("attendance_system.db")
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS staff (
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, username TEXT UNIQUE, 
        password TEXT, status TEXT, approved INTEGER DEFAULT 0)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS system_config (
        key TEXT PRIMARY KEY, value TEXT)""")
    cursor.execute("""CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, staff_id INTEGER, timestamp TEXT, 
        date TEXT, session TEXT, term_week INTEGER, UNIQUE(staff_id, date, session))""")

    cursor.execute("SELECT * FROM admin WHERE id=1")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO admin (username, password) VALUES ('admin', 'admin123')")

    cursor.execute("INSERT OR IGNORE INTO system_config VALUES ('term_start', ?)",
                   (datetime.now().strftime("%Y-%m-%d"),))
    cursor.execute("INSERT OR IGNORE INTO system_config VALUES ('late_time', '08:30')")
    conn.commit()
    return conn, cursor


conn, cursor = init_db()


def get_config(key):
    cursor.execute("SELECT value FROM system_config WHERE key=?", (key,))
    res = cursor.fetchone()
    return res[0] if res else ""


def get_term_week():
    start_date_str = get_config('term_start')
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    delta = datetime.now() - start_date
    return max(1, math.ceil((delta.days + 1) / 7))


# ================= GUI UTILITIES =================
def clear():
    for w in root.winfo_children(): w.destroy()


def load_asset(path, size):
    # This logic helps the EXE find images bundled inside it [cite: 4]
    if hasattr(sys, '_MEIPASS'):
        path = os.path.join(sys._MEIPASS, path)

    if os.path.exists(path):
        try:
            img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except:
            return None
    return None


def card(title, subtitle=""):
    wrapper = tk.Frame(root, bg="#f4f7f6")
    wrapper.pack(fill="both", expand=True)

    # Safe Background Load
    flier = load_asset("org_flier.png", (1150, 800))
    if flier:
        lbl = tk.Label(wrapper, image=flier)
        lbl.image = flier
        lbl.place(x=0, y=0, relwidth=1, relheight=1)

    frame = tk.Frame(wrapper, bg="white", bd=0, padx=40, pady=20)
    frame.place(relx=0.5, rely=0.5, anchor="center", width=1050, height=720)

    logo = load_asset("logo.png", (70, 70))
    if logo:
        l_lbl = tk.Label(frame, image=logo, bg="white")
        l_lbl.image = logo
        l_lbl.pack()

    tk.Label(frame, text=title, bg="white", font=("Helvetica", 24, "bold"), fg="#2c3e50").pack()
    tk.Label(frame, text=subtitle, bg="white", font=("Helvetica", 10, "italic"), fg="#7f8c8d").pack(pady=(0, 10))

    # REPLACEMENT FOR BROKEN SEPARATOR: A solid thin frame
    # Replace the Separator line in your card() function with this:
    line = tk.Frame(frame, bg="#bdc3c7", height=2)  # Solid grey line
    line.pack(fill="x", padx=100, pady=5)

    return frame

# ================= LOGIN SCREENS (PROFESSIONAL LABELS) =================
def admin_login_ui():
    clear()
    frame = card("ADMIN ACCESS", "Enter Secure Credentials")
    box = tk.Frame(frame, bg="white", pady=20)
    box.pack()

    tk.Label(box, text="Username", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
    u = tk.Entry(box, width=35, font=("Arial", 11), bd=2, relief="groove")
    u.pack(pady=(5, 15))

    tk.Label(box, text="Password", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
    p = tk.Entry(box, show="*", width=35, font=("Arial", 11), bd=2, relief="groove")
    p.pack(pady=(5, 20))

    def auth():
        if cursor.execute("SELECT * FROM admin WHERE username=? AND password=?", (u.get(), p.get())).fetchone():
            admin_dashboard()
        else:
            messagebox.showerror("Error", "Invalid Credentials")

    tk.Button(frame, text="LOGIN", bg="#2c3e50", fg="white", width=25, height=2, command=auth).pack()
    tk.Button(frame, text="BACK", command=main_menu, bd=0, bg="white", fg="grey").pack(pady=10)


def staff_login_ui():
    clear()
    frame = card("STAFF PORTAL", "Authentication Required")
    box = tk.Frame(frame, bg="white", pady=20)
    box.pack()

    tk.Label(box, text="Username", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
    u = tk.Entry(box, width=35, font=("Arial", 11), bd=2, relief="groove")
    u.pack(pady=(5, 15))

    tk.Label(box, text="Password", bg="white", font=("Arial", 10, "bold")).pack(anchor="w")
    p = tk.Entry(box, show="*", width=35, font=("Arial", 11), bd=2, relief="groove")
    p.pack(pady=(5, 20))

    def log():
        res = cursor.execute("SELECT id, approved, name FROM staff WHERE username=? AND password=?",
                             (u.get(), p.get())).fetchone()
        if res and res[1] == 1:
            staff_terminal(res[0], res[2])
        elif res:
            messagebox.showwarning("Pending", "Awaiting Admin Approval")
        else:
            messagebox.showerror("Error", "Invalid Details")

    tk.Button(frame, text="ENTER", bg="#16a085", fg="white", width=25, height=2, command=log).pack()
    tk.Button(frame, text="BACK", command=staff_portal, bd=0, bg="white", fg="grey").pack(pady=10)


import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sqlite3
import csv
import math
from datetime import datetime
from PIL import Image, ImageTk


# --- HELPERS ---
def export_to_csv(columns, rows, filename):
    """Restored Export Functionality"""
    if not rows:
        messagebox.showwarning("Empty", "No data to export.")
        return
    path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=filename)
    if path:
        try:
            with open(path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                writer.writerows(rows)
            messagebox.showinfo("Success", f"Report saved to {path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")


# --- UPDATED LOG VIEWS ---

def view_logs(period):
    """Daily and Weekly Logs with Fixed Linking"""
    clear()
    limit = get_config('late_time')
    frame = card(f"{period.upper()} ATTENDANCE", f"Late threshold: {limit}")

    cols = ("NAME", "DATE", "CLOCK IN (AM)", "CLOCK OUT (PM)", "STATUS")
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center")
    tree.pack(fill="both", expand=True, pady=10)
    tree.tag_configure('late', foreground='red')

    days = 0 if period == "daily" else 7

    # NEW GROUPING QUERY: Links AM and PM to the same row for each person per day
    query = """
        SELECT s.name, a.date, 
               MAX(CASE WHEN a.session = 'AM' THEN a.timestamp END) AS am_time,
               MAX(CASE WHEN a.session = 'PM' THEN a.timestamp END) AS pm_time
        FROM staff s 
        JOIN attendance a ON s.id = a.staff_id
        WHERE a.date >= date('now', ?)
        GROUP BY s.name, a.date
        ORDER BY a.date DESC
    """
    cursor.execute(query, (f"-{days} days",))
    data = cursor.fetchall()

    formatted_data = []
    for r in data:
        am_val = r[2] if r[2] else ""
        # Status logic: Checks AM time against late threshold
        status = "LATE" if am_val and am_val[:5] > limit else ("ON TIME" if am_val else "MISSING AM")

        row_vals = (r[0], r[1], am_val if am_val else "---", r[3] if r[3] else "---", status)
        tree.insert("", "end", values=row_vals, tags=('late' if status == "LATE" else ''))
        formatted_data.append(row_vals)

    # Restored Buttons
    btn_f = tk.Frame(frame, bg="white")
    btn_f.pack(pady=10)
    tk.Button(btn_f, text="EXPORT TO CSV", bg="#27ae60", fg="white", width=20,
              command=lambda: export_to_csv(cols, formatted_data, f"{period}_logs.csv")).grid(row=0, column=0, padx=10)
    tk.Button(btn_f, text="BACK", bg="#34495e", fg="white", width=20, command=admin_dashboard).grid(row=0, column=1,
                                                                                                    padx=10)


def view_termly_audit():
    """Termly Audit with Week Tracking and Linking Fix"""
    clear()
    frame = card("TERMLY AUDIT", "Review All Weeks")
    cols = ("WEEK", "NAME", "DATE", "AM", "PM")
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center")
    tree.pack(fill="both", expand=True, pady=10)

    # NEW GROUPING QUERY: Combines sessions by week and name
    query = """
        SELECT a.term_week, s.name, a.date, 
               MAX(CASE WHEN a.session = 'AM' THEN a.timestamp END) AS am_time,
               MAX(CASE WHEN a.session = 'PM' THEN a.timestamp END) AS pm_time
        FROM staff s 
        JOIN attendance a ON s.id = a.staff_id
        GROUP BY s.name, a.date
        ORDER BY a.term_week DESC, a.date DESC
    """
    cursor.execute(query)
    rows = cursor.fetchall()

    formatted_audit = []
    for r in rows:
        row_vals = (f"Wk {r[0]}", r[1], r[2], r[3] if r[3] else "---", r[4] if r[4] else "---")
        tree.insert("", "end", values=row_vals)
        formatted_audit.append(row_vals)

    # Restored Audit Export button
    btn_f = tk.Frame(frame, bg="white")
    btn_f.pack(pady=10)
    tk.Button(btn_f, text="EXPORT AUDIT", bg="#27ae60", fg="white", width=20,
              command=lambda: export_to_csv(cols, formatted_audit, "termly_audit.csv")).grid(row=0, column=0, padx=10)
    tk.Button(btn_f, text="BACK", bg="#34495e", fg="white", width=20, command=admin_dashboard).grid(row=0, column=1,
                                                                                                    padx=10)
# ================= SETTINGS (LATE TIME) =================
def settings_view():
    clear()
    frame = card("ORG SETTINGS", "Configure Term & Policy")
    box = tk.Frame(frame, bg="white", pady=30)
    box.pack()

    tk.Label(box, text="Term Start Date (YYYY-MM-DD):", bg="white", font=("Arial", 10, "bold")).grid(row=0, column=0,
                                                                                                     pady=10,
                                                                                                     sticky="w")
    term_ent = tk.Entry(box, width=25);
    term_ent.grid(row=0, column=1);
    term_ent.insert(0, get_config('term_start'))

    tk.Label(box, text="Late After (HH:MM 24hr):", bg="white", font=("Arial", 10, "bold")).grid(row=1, column=0,
                                                                                                pady=10, sticky="w")
    late_ent = tk.Entry(box, width=25);
    late_ent.grid(row=1, column=1);
    late_ent.insert(0, get_config('late_time'))

    def save():
        cursor.execute("UPDATE system_config SET value=? WHERE key='term_start'", (term_ent.get(),))
        cursor.execute("UPDATE system_config SET value=? WHERE key='late_time'", (late_ent.get(),))
        conn.commit();
        messagebox.showinfo("Done", "Settings Updated.");
        admin_dashboard()

    tk.Button(frame, text="SAVE", bg="#27ae60", fg="white", width=20, command=save).pack(pady=10)
    tk.Button(frame, text="BACK", command=admin_dashboard).pack()


# ================= REST OF GUI (RETAINED) =================
def admin_dashboard():
    clear();
    frame = card("ADMIN CONTROL CENTER")
    grid = tk.Frame(frame, bg="white");
    grid.pack(expand=True)
    items = [
        ("DAILY LOGS", lambda: view_logs("daily"), "#2c3e50"),
        ("WEEKLY LOGS", lambda: view_logs("weekly"), "#2c3e50"),
        ("TERMLY AUDIT", view_termly_audit, "#16a085"),
        ("APPROVAL GATEWAY", staff_approval_view, "#2980b9"),
        ("STAFF MANAGEMENT", staff_management_view, "#34495e"),
        ("ORG SETTINGS", settings_view, "#d35400"),
        ("LOGOUT", main_menu, "#c0392b")
    ]
    for i, (txt, cmd, clr) in enumerate(items):
        tk.Button(grid, text=txt, width=32, height=2, bg=clr, fg="white", font=("Arial", 10, "bold"), command=cmd).grid(
            row=i // 2, column=i % 2, padx=15, pady=10)


# ================= 4. APPROVAL GATEWAY (WITH CORRECTED IMPORT) =================
def staff_approval_view():
    clear()
    frame = card("APPROVAL GATEWAY", "Bulk authorize pending staff or import via CSV.")

    cols = ("ID", "NAME", "USERNAME", "POSITION")
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center")
    tree.pack(fill="both", expand=True, pady=10)

    def refresh():
        for i in tree.get_children(): tree.delete(i)
        cursor.execute("SELECT id, name, username, status FROM staff WHERE approved=0")
        for r in cursor.fetchall(): tree.insert("", "end", values=r)

    def approve_all():
        cursor.execute("UPDATE staff SET approved=1 WHERE approved=0")
        conn.commit()
        refresh()
        messagebox.showinfo("Success", "All staff authorized.")

    def import_csv():
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            try:
                with open(file_path, mode='r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    # Expected headers: name, username, password, status
                    for row in reader:
                        cursor.execute("""
                            INSERT OR IGNORE INTO staff (name, username, password, status, approved) 
                            VALUES (?, ?, ?, ?, 0)
                        """, (row['name'], row['username'], row['password'], row['status']))
                conn.commit()
                refresh()
                messagebox.showinfo("Success", "Staff imported successfully.")
            except Exception as e:
                messagebox.showerror("Import Error",
                                     f"Ensure CSV has headers: name, username, password, status\nError: {e}")

    # Layout for Buttons
    btn_f = tk.Frame(frame, bg="white")
    btn_f.pack(pady=10)

    # IMPORT BUTTON ADDED HERE
    tk.Button(btn_f, text="IMPORT CSV", bg="#2980b9", fg="white", width=20, font=("Arial", 10, "bold"),
              command=import_csv).grid(row=0, column=0, padx=10)

    tk.Button(btn_f, text="APPROVE ALL", bg="#27ae60", fg="white", width=20, font=("Arial", 10, "bold"),
              command=approve_all).grid(row=0, column=1, padx=10)

    tk.Button(btn_f, text="BACK", bg="#34495e", fg="white", width=20, font=("Arial", 10, "bold"),
              command=admin_dashboard).grid(row=0, column=2, padx=10)

    refresh()


def staff_management_view():
    clear()
    frame = card("STAFF DIRECTORY")
    # 1. Add PASSWORD to columns
    cols = ("ID", "NAME", "USERNAME", "PASSWORD", "POSITION")
    tree = ttk.Treeview(frame, columns=cols, show="headings")
    for c in cols:
        tree.heading(c, text=c)
        tree.column(c, anchor="center")
    tree.pack(fill="both", expand=True, pady=10)

    # 2. Select PASSWORD from the database
    cursor.execute("SELECT id, name, username, password, status FROM staff WHERE approved=1")
    for r in cursor.fetchall():
        tree.insert("", "end", values=r)

    tk.Button(frame, text="BACK", bg="#34495e", fg="white", command=admin_dashboard).pack(pady=10)

def main_menu():
    clear();
    frame = card("ORGANIZATION ATTENDANCE", "v5.3 Enterprise Edition")
    tk.Button(frame, text="ADMIN LOGIN", width=40, height=3, bg="#2c3e50", fg="white", font=("Arial", 14, "bold"),
              command=admin_login_ui).pack(pady=20)
    tk.Button(frame, text="STAFF ACCESS", width=40, height=3, bg="#16a085", fg="white", font=("Arial", 14, "bold"),
              command=staff_portal).pack(pady=20)


def staff_portal():
    clear();
    frame = card("STAFF PORTAL")
    tk.Button(frame, text="LOGIN", width=35, height=3, bg="#16a085", fg="white", command=staff_login_ui).pack(pady=10)
    tk.Button(frame, text="REGISTER", width=35, height=3, bg="#2980b9", fg="white", command=staff_reg_ui).pack(pady=10)
    tk.Button(frame, text="BACK", command=main_menu).pack()


def staff_terminal(sid, name):
    clear()
    frame = card(f"TERMINAL: {name.upper()}")
    now = datetime.now()
    # Identifies session based on current hour [cite: 43]
    sess = "AM" if now.hour < 12 else "PM"

    tk.Label(frame, text=now.strftime('%H:%M:%S'), font=("Courier", 60, "bold"), bg="white").pack(pady=40)

    def rec():
        try:
            # The back-end now simply inserts the current session (AM or PM)
            # If AM is missing, this PM entry still succeeds because of the UNIQUE(staff_id, date, session) constraint.
            cursor.execute("INSERT INTO attendance (staff_id, timestamp, date, session, term_week) VALUES (?,?,?,?,?)",
                           (sid, now.strftime("%H:%M:%S"), now.strftime("%Y-%m-%d"), sess, get_term_week()))
            conn.commit()
            messagebox.showinfo("Done", f"{sess} Clocked Successfully.")
            main_menu()
        except sqlite3.IntegrityError:
            # This only triggers if they try to clock the SAME session twice (e.g., clocking PM twice)
            messagebox.showerror("Denied", f"You have already clocked {sess} for today.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    # GUI remains unchanged as requested
    tk.Button(frame, text=f"CLOCK {sess}", width=30, height=2, bg="#2c3e50", fg="white", command=rec).pack()
    tk.Button(frame, text="EXIT", command=main_menu).pack()


def staff_reg_ui():
    clear();
    frame = card("REGISTRATION");
    box = tk.Frame(frame, bg="white");
    box.pack(pady=10)
    lbls = ["Name", "Pos", "User", "Pass"];
    ents = []
    for l in lbls:
        tk.Label(box, text=l, bg="white").pack();
        e = tk.Entry(box, width=30);
        e.pack();
        ents.append(e)

    def reg():
        try:
            cursor.execute("INSERT INTO staff (name, status, username, password, approved) VALUES (?,?,?,?,0)",
                           (ents[0].get(), ents[1].get(), ents[2].get(), ents[3].get()))
            conn.commit();
            messagebox.showinfo("Pending", "Awaiting Approval.");
            main_menu()
        except:
            messagebox.showerror("Error", "User exists.")

    tk.Button(frame, text="REGISTER", command=reg).pack();
    tk.Button(frame, text="BACK", command=staff_portal).pack()


root = tk.Tk();
root.title("Attendance Enterprise Pro");
root.geometry("1150x800");
main_menu();
root.mainloop()