import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import datetime
import os
import statistics

DB_PATH = "school.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    created = not os.path.exists(DB_PATH)
    conn = get_conn()
    cur = conn.cursor()

    # users table (FIXED: Changed PRIMARY PRIMARY KEY to PRIMARY KEY)
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )
    """
    )

    # students table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY,
        first_name TEXT,
        last_name TEXT,
        dob TEXT,
        admission_no TEXT UNIQUE,
        class TEXT,
        section TEXT,
        guardian_name TEXT,
        phone TEXT,
        created_at TEXT
    )
    """
    )

    # attendance table
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY,
        student_id INTEGER,
        date TEXT,
        status TEXT,
        marked_by INTEGER,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """
    )

    # fees/payments tables
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS fees (
        id INTEGER PRIMARY KEY,
        student_id INTEGER,
        description TEXT,
        amount REAL,
        due_date TEXT,
        status TEXT,
        created_at TEXT,
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """
    )

    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        fee_id INTEGER,
        student_id INTEGER,
        amount REAL,
        method TEXT,
        tx_ref TEXT,
        paid_at TEXT,
        FOREIGN KEY(fee_id) REFERENCES fees(id),
        FOREIGN KEY(student_id) REFERENCES students(id)
    )
    """
    )

    # exams placeholder (old structure)
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS exams (
        id INTEGER PRIMARY KEY,
        title TEXT,
        start_date TEXT,
        end_date TEXT
    )
    """
    )

    # Exam Schedule (detailed schedule)
    cur.execute(
        """
    CREATE TABLE IF NOT EXISTS exam_schedule (
        id INTEGER PRIMARY KEY,
        exam_title TEXT NOT NULL,
        class TEXT,
        subject TEXT,
        exam_date TEXT,
        start_time TEXT,
        end_time TEXT,
        room TEXT
    )
    """
    )

    conn.commit()

    # insert default admin if none exists
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            ("admin", "admin", "admin"),
        )
        conn.commit()

    # insert sample students if none
    cur.execute("SELECT COUNT(*) FROM students")
    if cur.fetchone()[0] == 0:
        now = datetime.datetime.now().isoformat()
        sample = [
            ("Aisha", "Khan", "2012-05-11", "ADM001", "Grade 1", "A", "Mrs Khan", "9999999999", now),
            ("Ravi", "Patel", "2011-09-20", "ADM002", "Grade 2", "B", "Mr Patel", "8888888888", now),
            ("Maya", "Singh", "2010-03-05", "ADM003", "Grade 3", "A", "Mrs Singh", "7777777777", now),
        ]
        cur.executemany(
            "INSERT INTO students (first_name,last_name,dob,admission_no,class,section,guardian_name,phone,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
            sample,
        )
        conn.commit()

    conn.close()


def fmt_date(dt=None):
    if dt is None:
        dt = datetime.date.today()
    if isinstance(dt, datetime.datetime):
        dt = dt.date()
    return dt.isoformat()


class SchoolApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("School Management System — Tkinter")
        self.geometry("1000x650")
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.current_user = None

        # initialize DB
        init_db()

        # build login screen
        self._build_login()

    def _build_login(self):
        for w in self.winfo_children():
            w.destroy()

        frame = ttk.Frame(self, padding=20)
        frame.pack(expand=True)

        title = ttk.Label(frame, text="School Management System", font=("Helvetica", 18, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 10))

        ttk.Label(frame, text="Username").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        username_entry = ttk.Entry(frame)
        username_entry.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        username_entry.insert(0, "admin")

        ttk.Label(frame, text="Password").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        password_entry = ttk.Entry(frame, show="*")
        password_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        password_entry.insert(0, "admin")

        def on_login():
            user = username_entry.get().strip()
            pwd = password_entry.get().strip()
            conn = get_conn()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, pwd))
            row = cur.fetchone()
            conn.close()
            if row:
                self.current_user = dict(row)
                self._build_main_ui()
            else:
                messagebox.showerror("Login failed", "Invalid username or password")

        login_btn = ttk.Button(frame, text="Login", command=on_login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=10)

    def _build_main_ui(self):
        for w in self.winfo_children():
            w.destroy()

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)

        # sidebar
        sidebar = ttk.Frame(container, width=200, relief="ridge")
        sidebar.pack(side="left", fill="y")

        header = ttk.Label(sidebar, text="SchoolMS", font=("Helvetica", 14, "bold"))
        header.pack(padx=10, pady=(10, 20))

        # menu buttons
        buttons = [
            ("Dashboard", self._show_dashboard),
            ("Students", self._show_students),
            ("Attendance", self._show_attendance),
            ("Exams", self._show_exams),
            ("Fees", self._show_fees),
            ("Settings", self._show_settings),
            ("Logout", self._logout),
        ]

        for (label, cmd) in buttons:
            b = ttk.Button(sidebar, text=label, command=cmd)
            b.pack(fill="x", padx=10, pady=6)

        # main content area
        self.content = ttk.Frame(container)
        self.content.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # default view
        self._show_dashboard()

    def _show_dashboard(self):
        self._clear_content()
        ttk.Label(self.content, text="Dashboard", font=("Helvetica", 16, "bold")).pack(anchor="w")

        frame = ttk.Frame(self.content)
        frame.pack(fill="x", pady=10)

        # KPIs
        kpi_frame = ttk.Frame(frame)
        kpi_frame.pack(fill="x")
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM students")
        total_students = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fees WHERE status='paid'")
        paid_fees_count = cur.fetchone()[0]
        # avg attendance (last 30 days) calculation
        cur.execute("SELECT date, status FROM attendance WHERE date >= ?", (fmt_date(datetime.date.today() - datetime.timedelta(days=30)),))
        rows = cur.fetchall()
        perc = 0
        if rows:
            statuses = [1 if r["status"] == "Present" else 0 for r in rows]
            perc = round(sum(statuses) / len(statuses) * 100, 1)
        conn.close()

        kp = ttk.Frame(kpi_frame, relief="groove", padding=10)
        kp.pack(side="left", padx=6, pady=6)
        ttk.Label(kp, text="Total Students", font=("Helvetica", 12)).pack()
        ttk.Label(kp, text=str(total_students), font=("Helvetica", 18, "bold")).pack()

        kp2 = ttk.Frame(kpi_frame, relief="groove", padding=10)
        kp2.pack(side="left", padx=6, pady=6)
        ttk.Label(kp2, text="Avg Attendance (30d)", font=("Helvetica", 12)).pack()
        ttk.Label(kp2, text=f"{perc}%", font=("Helvetica", 18, "bold")).pack()

        kp3 = ttk.Frame(kpi_frame, relief="groove", padding=10)
        kp3.pack(side="left", padx=6, pady=6)
        ttk.Label(kp3, text="Fees Recorded (paid rows)", font=("Helvetica", 12)).pack()
        ttk.Label(kp3, text=str(paid_fees_count), font=("Helvetica", 18, "bold")).pack()

        # attendance trend chart
        trend_frame = ttk.Frame(self.content)
        trend_frame.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(trend_frame, text="Attendance Trend (last 6 months)", font=("Helvetica", 12)).pack(anchor="w")
        canvas = tk.Canvas(trend_frame, height=180, bg="white", bd=0, highlightthickness=0)
        canvas.pack(fill="x", pady=8)

        # compute monthly percent from attendance table
        conn = get_conn()
        cur = conn.cursor()
        today = datetime.date.today()
        months = []
        for i in range(5, -1, -1):  # last 6 months
            m = (today.replace(day=1) - datetime.timedelta(days=i * 30)).replace(day=1)
            months.append(m)
        points = []
        for m in months:
            start = m.isoformat()
            # next month start calculation
            try:
                next_month = (m.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
            except Exception:
                next_month = (m + datetime.timedelta(days=31)).replace(day=1)
            cur.execute("SELECT status FROM attendance WHERE date >= ? AND date < ?", (start, next_month.isoformat()))
            rs = cur.fetchall()
            if not rs:
                points.append(None)
            else:
                vals = [1 if r["status"] == "Present" else 0 for r in rs]
                points.append(round(sum(vals) / len(vals) * 100, 1))
        conn.close()

        # draw bars on canvas
        w = canvas.winfo_reqwidth() or 800
        bar_w = 60
        gap = 12
        x = 20
        maxh = 120
        for idx, val in enumerate(points):
            label_month = months[idx].strftime("%b")
            if val is None:
                h = 6
                canvas.create_rectangle(x, 150 - h, x + bar_w, 150, fill="#ddd", outline="#ddd")
                canvas.create_text(x + bar_w / 2, 160, text=label_month)
            else:
                h = max(6, int((val / 100.0) * maxh))
                canvas.create_rectangle(x, 150 - h, x + bar_w, 150, fill="#60A5FA", outline="")
                canvas.create_text(x + bar_w / 2, 150 - h - 8, text=f"{val}%", font=("", 9))
                canvas.create_text(x + bar_w / 2, 160, text=label_month)
            x += bar_w + gap

    def _show_students(self):
        self._clear_content()
        header = ttk.Label(self.content, text="Students", font=("Helvetica", 16, "bold"))
        header.pack(anchor="w")

        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill="x", pady=6)
        search_var = tk.StringVar()

        ttk.Label(toolbar, text="Search:").pack(side="left", padx=(0, 6))
        search_entry = ttk.Entry(toolbar, textvariable=search_var)
        search_entry.pack(side="left", padx=(0, 6))

        def reload_tree(*_):
            q = search_var.get().strip().lower()
            for r in self.tree.get_children():
                self.tree.delete(r)
            conn = get_conn()
            cur = conn.cursor()
            if q:
                cur.execute(
                    "SELECT * FROM students WHERE lower(first_name)||' '||lower(last_name) LIKE ? OR lower(admission_no) LIKE ?",
                    (f"%{q}%", f"%{q}%"),
                )
            else:
                cur.execute("SELECT * FROM students ORDER BY id DESC")
            for row in cur.fetchall():
                self.tree.insert("", "end", iid=row["id"], values=(row["admission_no"], row["first_name"], row["last_name"], row["class"], row["section"]))
            conn.close()

        ttk.Button(toolbar, text="Add Student", command=self._add_student_dialog).pack(side="right")
        ttk.Button(toolbar, text="Edit Selected", command=lambda: self._edit_student()).pack(side="right", padx=(0, 6))
        ttk.Button(toolbar, text="Delete Selected", command=lambda: self._delete_student()).pack(side="right", padx=(0, 6))
        search_entry.bind("<KeyRelease>", reload_tree)

        # treeview
        cols = ("admission_no", "first", "last", "class", "section")
        self.tree = ttk.Treeview(self.content, columns=cols, show="headings", selectmode="browse", height=18)
        self.tree.heading("admission_no", text="Adm No")
        self.tree.heading("first", text="First Name")
        self.tree.heading("last", text="Last Name")
        self.tree.heading("class", text="Class")
        self.tree.heading("section", text="Section")
        self.tree.pack(fill="both", expand=True, pady=6)

        reload_tree()

    def _add_student_dialog(self):
        dlg = StudentDialog(self, title="Add Student")
        self.wait_window(dlg.top)
        if dlg.result:
            s = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            now = datetime.datetime.now().isoformat()
            try:
                cur.execute(
                    "INSERT INTO students (first_name,last_name,dob,admission_no,class,section,guardian_name,phone,created_at) VALUES (?,?,?,?,?,?,?,?,?)",
                    (s["first"], s["last"], s["dob"], s["adm"], s["class"], s["section"], s["guardian"], s["phone"], now),
                )
                conn.commit()
                messagebox.showinfo("Success", "Student added")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Admission number must be unique")
            finally:
                conn.close()
            self._show_students()

    def _edit_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a student to edit")
            return
        sid = int(sel[0])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM students WHERE id=?", (sid,))
        row = cur.fetchone()
        conn.close()
        if not row:
            messagebox.showerror("Error", "Student not found")
            return
        dlg = StudentDialog(self, title="Edit Student", payload=row)
        self.wait_window(dlg.top)
        if dlg.result:
            s = dlg.result
            conn = get_conn()
            cur = conn.cursor()
            try:
                cur.execute(
                    "UPDATE students SET first_name=?, last_name=?, dob=?, admission_no=?, class=?, section=?, guardian_name=?, phone=? WHERE id=?",
                    (s["first"], s["last"], s["dob"], s["adm"], s["class"], s["section"], s["guardian"], s["phone"], sid),
                )
                conn.commit()
                messagebox.showinfo("Success", "Student updated")
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Admission number must be unique")
            finally:
                conn.close()
            self._show_students()

    def _delete_student(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select a student to delete")
            return
        if not messagebox.askyesno("Confirm", "Delete selected student? This cannot be undone."):
            return
        sid = int(sel[0])
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id=?", (sid,))
        conn.commit()
        conn.close()
        self._show_students()

    def _show_attendance(self):
        self._clear_content()
        ttk.Label(self.content, text="Attendance", font=("Helvetica", 16, "bold")).pack(anchor="w")
        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill="x", pady=6)
        cls_var = tk.StringVar(value="All Classes")
        ttk.Label(toolbar, text="Class:").pack(side="left")
        ttk.Entry(toolbar, textvariable=cls_var, width=20).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Load Students", command=lambda: load_students_for_attendance(cls_var.get())).pack(side="left", padx=6)

        frame = ttk.Frame(self.content)
        frame.pack(fill="both", expand=True, pady=8)

        tree = ttk.Treeview(frame, columns=("name", "class", "status"), show="headings", height=18)
        tree.heading("name", text="Student")
        tree.heading("class", text="Class")
        tree.heading("status", text="Status")
        tree.pack(side="left", fill="both", expand=True)

        # controls
        ctrl = ttk.Frame(frame)
        ctrl.pack(side="left", fill="y", padx=8)
        ttk.Button(ctrl, text="Present", command=lambda: mark_selected("Present")).pack(fill="x", pady=4)
        ttk.Button(ctrl, text="Absent", command=lambda: mark_selected("Absent")).pack(fill="x", pady=4)
        ttk.Button(ctrl, text="Refresh", command=lambda: load_students_for_attendance(cls_var.get())).pack(fill="x", pady=8)
        ttk.Button(ctrl, text="Recent Attendance (7d)", command=self._show_recent_attendance).pack(fill="x", pady=4)

        def load_students_for_attendance(classfilter):
            for r in tree.get_children():
                tree.delete(r)
            conn = get_conn()
            cur = conn.cursor()
            if classfilter and classfilter != "All Classes":
                cur.execute("SELECT * FROM students WHERE class LIKE ? ORDER BY id", (f"%{classfilter}%",))
            else:
                cur.execute("SELECT * FROM students ORDER BY id")
            for row in cur.fetchall():
                tree.insert("", "end", iid=row["id"], values=(f"{row['first_name']} {row['last_name']}", row["class"], ""))
            conn.close()

        def mark_selected(status):
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("No selection", "Select a student to mark")
                return
            sid = int(sel[0])
            date = fmt_date()
            conn = get_conn()
            cur = conn.cursor()
            # check if already marked today
            cur.execute("SELECT id FROM attendance WHERE student_id=? AND date=?", (sid, date))
            if cur.fetchone():
                # update
                cur.execute("UPDATE attendance SET status=?, marked_by=? WHERE student_id=? AND date=?", (status, self.current_user["id"], sid, date))
            else:
                cur.execute("INSERT INTO attendance (student_id,date,status,marked_by) VALUES (?,?,?,?)", (sid, date, status, self.current_user["id"]))
            conn.commit()
            conn.close()
            load_students_for_attendance(classfilter=cls_var.get())
            messagebox.showinfo("Marked", f"Marked {status} for student")

        # initially load
        load_students_for_attendance("All Classes")

    def _show_recent_attendance(self):
        # show a small dialog with recent attendance
        dlg = tk.Toplevel(self)
        dlg.title("Recent Attendance (7 days)")
        dlg.geometry("500x400")
        tree = ttk.Treeview(dlg, columns=("student", "date", "status"), show="headings")
        tree.heading("student", text="Student")
        tree.heading("date", text="Date")
        tree.heading("status", text="Status")
        tree.pack(fill="both", expand=True)
        conn = get_conn()
        cur = conn.cursor()
        d0 = fmt_date(datetime.date.today() - datetime.timedelta(days=7))
        cur.execute(
            "SELECT a.date, a.status, s.first_name || ' ' || s.last_name AS student FROM attendance a JOIN students s ON s.id=a.student_id WHERE a.date >= ? ORDER BY a.date DESC",
            (d0,),
        )
        for row in cur.fetchall():
            tree.insert("", "end", values=(row["student"], row["date"], row["status"]))
        conn.close()

    def _show_fees(self):
        self._clear_content()
        ttk.Label(self.content, text="Fees & Payments", font=("Helvetica", 16, "bold")).pack(anchor="w")

        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill="x", pady=6)
        ttk.Button(toolbar, text="New Invoice", command=self._create_invoice).pack(side="right")
        ttk.Button(toolbar, text="Record Payment", command=self._record_payment).pack(side="right", padx=6)

        # recent payments treeview
        tree = ttk.Treeview(self.content, columns=("student", "amount", "paid_at", "method"), show="headings", height=16)
        tree.heading("student", text="Student")
        tree.heading("amount", text="Amount")
        tree.heading("paid_at", text="Paid At")
        tree.heading("method", text="Method")
        tree.pack(fill="both", expand=True, pady=6)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT p.amount, p.paid_at, p.method, s.first_name || ' ' || s.last_name AS student FROM payments p JOIN students s ON s.id=p.student_id ORDER BY p.paid_at DESC LIMIT 50"
        )
        for row in cur.fetchall():
            tree.insert("", "end", values=(row["student"], f"${row['amount']:.2f}", row["paid_at"], row["method"]))
        conn.close()

    def _create_invoice(self):
        # ask for student admission number and amount
        adm = simpledialog.askstring("Invoice", "Enter student admission number (e.g. ADM001):", parent=self)
        if not adm:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, first_name || ' ' || last_name AS name FROM students WHERE admission_no=?", (adm.strip(),))
        row = cur.fetchone()
        if not row:
            messagebox.showerror("Not found", "Student admission number not found")
            conn.close()
            return
        sid = row["id"]
        amt = simpledialog.askfloat("Amount", "Enter amount", parent=self, minvalue=0.0)
        if amt is None:
            conn.close()
            return
        desc = simpledialog.askstring("Description", "Invoice description", parent=self) or "Tuition"
        due = simpledialog.askstring("Due date (YYYY-MM-DD)", "Enter due date", initialvalue=fmt_date(), parent=self)
        now = datetime.datetime.now().isoformat()
        cur.execute("INSERT INTO fees (student_id, description, amount, due_date, status, created_at) VALUES (?,?,?,?,?,?)", (sid, desc, amt, due, "pending", now))
        conn.commit()
        conn.close()
        messagebox.showinfo("Invoice created", f"Invoice for {row['name']} created")

        self._show_fees()

    def _record_payment(self):
        adm = simpledialog.askstring("Payment", "Enter student admission number:", parent=self)
        if not adm:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, first_name || ' ' || last_name AS name FROM students WHERE admission_no=?", (adm.strip(),))
        row = cur.fetchone()
        if not row:
            messagebox.showerror("Not found", "Student admission number not found")
            conn.close()
            return
        sid = row["id"]
        amt = simpledialog.askfloat("Amount", "Enter amount", parent=self, minvalue=0.0)
        if amt is None:
            conn.close()
            return
        method = simpledialog.askstring("Method", "Payment method (cash/card/online)", parent=self) or "cash"
        tx = simpledialog.askstring("Transaction ref", "Transaction reference (optional)", parent=self) or ""
        paid_at = datetime.datetime.now().isoformat()
        # Link to fee if any pending fee exists (take oldest)
        cur.execute("SELECT id FROM fees WHERE student_id=? AND status!='paid' ORDER BY id LIMIT 1", (sid,))
        fee_row = cur.fetchone()
        fee_id = fee_row["id"] if fee_row else None
        cur.execute("INSERT INTO payments (fee_id, student_id, amount, method, tx_ref, paid_at) VALUES (?,?,?,?,?,?)", (fee_id, sid, amt, method, tx, paid_at))
        if fee_id:
            cur.execute("UPDATE fees SET status='paid' WHERE id=?", (fee_id,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Payment recorded", f"Payment of ${amt:.2f} recorded for {row['name']}")
        self._show_fees()

    def _show_exams(self):
        self._clear_content()
        ttk.Label(self.content, text="Exam Schedule", font=("Helvetica", 16, "bold")).pack(anchor="w")

        toolbar = ttk.Frame(self.content)
        toolbar.pack(fill="x", pady=6)
        # Added Delete Button
        ttk.Button(toolbar, text="Delete Selected Exam", command=self._delete_exam_schedule).pack(side="right", padx=6)
        ttk.Button(toolbar, text="Add New Exam Schedule", command=self._add_exam_schedule).pack(side="right")
        ttk.Button(toolbar, text="Refresh List", command=self._show_exams).pack(side="right", padx=6)


        # Treeview for displaying the exam schedules
        cols = ("title", "class", "subject", "date", "start_time", "end_time", "room")
        self.exam_tree = ttk.Treeview(self.content, columns=cols, show="headings", selectmode="browse", height=18)
        self.exam_tree.heading("title", text="Exam Title")
        self.exam_tree.heading("class", text="Class")
        self.exam_tree.heading("subject", text="Subject")
        self.exam_tree.heading("date", text="Date")
        self.exam_tree.heading("start_time", text="Start Time")
        self.exam_tree.heading("end_time", text="End Time")
        self.exam_tree.heading("room", text="Room")
        self.exam_tree.pack(fill="both", expand=True, pady=6)

        self._load_exam_schedules()

    def _load_exam_schedules(self):
        for r in self.exam_tree.get_children():
            self.exam_tree.delete(r)

        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM exam_schedule ORDER BY exam_date, start_time")
        for row in cur.fetchall():
            self.exam_tree.insert("", "end", iid=row["id"], values=(
                row["exam_title"], row["class"], row["subject"], row["exam_date"], row["start_time"], row["end_time"], row["room"]
            ))
        conn.close()

    def _add_exam_schedule(self):
        # Use simpledialog to get exam details
        title = simpledialog.askstring("Exam Title", "Enter Exam Title:", parent=self)
        if not title: return

        class_name = simpledialog.askstring("Class", "Enter Class (e.g., Grade 1):", parent=self)
        if not class_name: return

        subject = simpledialog.askstring("Subject", "Enter Subject:", parent=self)
        if not subject: return

        date = simpledialog.askstring("Exam Date (YYYY-MM-DD)", "Enter Exam Date (YYYY-MM-DD):", parent=self, initialvalue=fmt_date())
        if not date: return

        start_time = simpledialog.askstring("Start Time (HH:MM)", "Enter Start Time (e.g., 09:00):", parent=self)
        if not start_time: return

        end_time = simpledialog.askstring("End Time (HH:MM)", "Enter End Time (e.g., 12:00):", parent=self)
        if not end_time: return

        room = simpledialog.askstring("Room/Hall", "Enter Room/Hall Number:", parent=self) or ""

        # Insert into database
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO exam_schedule (exam_title, class, subject, exam_date, start_time, end_time, room) VALUES (?,?,?,?,?,?,?)",
                (title, class_name, subject, date, start_time, end_time, room)
            )
            conn.commit()
            messagebox.showinfo("Success", "Exam schedule added successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add exam schedule: {e}")
        finally:
            conn.close()

        self._load_exam_schedules() # Refresh the list

    # Delete exam schedule
    def _delete_exam_schedule(self):
        sel = self.exam_tree.selection()
        if not sel:
            messagebox.showwarning("No selection", "Select an exam schedule to delete.")
            return

        exam_id = int(sel[0])

        if not messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected exam schedule?"):
            return

        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM exam_schedule WHERE id=?", (exam_id,))
            conn.commit()
            messagebox.showinfo("Success", "Exam schedule deleted successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete exam schedule: {e}")
        finally:
            conn.close()

        self._load_exam_schedules() # Refresh the list

    def _show_settings(self):
        self._clear_content()
        ttk.Label(self.content, text="Settings", font=("Helvetica", 16, "bold")).pack(anchor="w")
        ttk.Label(self.content, text="Change admin password or add users", font=("Helvetica", 11)).pack(anchor="w", pady=8)

        frm = ttk.Frame(self.content)
        frm.pack(anchor="w", pady=6)

        ttk.Button(frm, text="Change password", command=self._change_password).pack(side="left", padx=6)
        ttk.Button(frm, text="Add user", command=self._add_user).pack(side="left", padx=6)

    def _change_password(self):
        new = simpledialog.askstring("New password", "Enter new password:", parent=self, show="*")
        if not new:
            return
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=? WHERE id=?", (new, self.current_user["id"]))
        conn.commit()
        conn.close()
        messagebox.showinfo("Changed", "Password updated")

    def _add_user(self):
        u = simpledialog.askstring("Username", "Enter username:", parent=self)
        if not u:
            return
        p = simpledialog.askstring("Password", "Enter password:", parent=self, show="*")
        if p is None:
            return
        role = simpledialog.askstring("Role", "Role (admin/teacher/accountant):", parent=self, initialvalue="teacher")
        conn = get_conn()
        cur = conn.cursor()
        try:
            cur.execute("INSERT INTO users (username,password,role) VALUES (?,?,?)", (u, p, role or "teacher"))
            conn.commit()
            messagebox.showinfo("Added", "User added")
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")
        finally:
            conn.close()

    def _logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.current_user = None
            self._build_login()

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()


# Student add / edit dialog class
class StudentDialog:
    def __init__(self, parent, title="Student", payload=None):
        self.top = tk.Toplevel(parent)
        self.top.transient(parent)
        self.top.grab_set()
        self.top.title(title)
        self.result = None

        frm = ttk.Frame(self.top, padding=10)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="First name").grid(row=0, column=0, sticky="e")
        self.e_first = ttk.Entry(frm)
        self.e_first.grid(row=0, column=1, padx=6, pady=4)

        ttk.Label(frm, text="Last name").grid(row=1, column=0, sticky="e")
        self.e_last = ttk.Entry(frm)
        self.e_last.grid(row=1, column=1, padx=6, pady=4)

        ttk.Label(frm, text="DOB (YYYY-MM-DD)").grid(row=2, column=0, sticky="e")
        self.e_dob = ttk.Entry(frm)
        self.e_dob.grid(row=2, column=1, padx=6, pady=4)

        ttk.Label(frm, text="Admission No").grid(row=3, column=0, sticky="e")
        self.e_adm = ttk.Entry(frm)
        self.e_adm.grid(row=3, column=1, padx=6, pady=4)

        ttk.Label(frm, text="Class").grid(row=4, column=0, sticky="e")
        self.e_class = ttk.Entry(frm)
        self.e_class.grid(row=4, column=1, padx=6, pady=4)

        ttk.Label(frm, text="Section").grid(row=5, column=0, sticky="e")
        self.e_section = ttk.Entry(frm)
        self.e_section.grid(row=5, column=1, padx=6, pady=4)

        ttk.Label(frm, text="Guardian").grid(row=6, column=0, sticky="e")
        self.e_guardian = ttk.Entry(frm)
        self.e_guardian.grid(row=6, column=1, padx=6, pady=4)

        ttk.Label(frm, text="Phone").grid(row=7, column=0, sticky="e")
        self.e_phone = ttk.Entry(frm)
        self.e_phone.grid(row=7, column=1, padx=6, pady=4)

        if payload:
            # payload is sqlite3.Row
            self.e_first.insert(0, payload["first_name"])
            self.e_last.insert(0, payload["last_name"])
            self.e_dob.insert(0, payload["dob"])
            self.e_adm.insert(0, payload["admission_no"])
            self.e_class.insert(0, payload["class"])
            self.e_section.insert(0, payload["section"])
            self.e_guardian.insert(0, payload["guardian_name"])
            self.e_phone.insert(0, payload["phone"])

        btn = ttk.Button(frm, text="Save", command=self._on_save)
        btn.grid(row=8, column=0, columnspan=2, pady=8)

    def _on_save(self):
        a = self.e_first.get().strip()
        b = self.e_last.get().strip()
        adm = self.e_adm.get().strip()
        if not (a and adm):
            messagebox.showerror("Validation", "First name and Admission No are required")
            return
        self.result = {
            "first": a,
            "last": b,
            "dob": self.e_dob.get().strip(),
            "adm": adm,
            "class": self.e_class.get().strip(),
            "section": self.e_section.get().strip(),
            "guardian": self.e_guardian.get().strip(),
            "phone": self.e_phone.get().strip(),
        }
        self.top.destroy()


if __name__ == "__main__":
    app = SchoolApp()
    app.mainloop()