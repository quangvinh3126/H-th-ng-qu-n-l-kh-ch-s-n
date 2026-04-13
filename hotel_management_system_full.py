import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
from collections import defaultdict

try:
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure
    MATPLOTLIB_OK = True
except Exception:
    MATPLOTLIB_OK = False

DB_NAME = "hotel.db"
DATE_FMT = "%Y-%m-%d"


def today_str() -> str:
    return date.today().strftime(DATE_FMT)


class DatabaseManager:
    def __init__(self, db_name: str = DB_NAME):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()
        self.seed_data()

    def execute(self, sql: str, params=(), commit: bool = False):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        if commit:
            self.conn.commit()
        return cur

    def executemany(self, sql: str, seq_of_params, commit: bool = False):
        cur = self.conn.cursor()
        cur.executemany(sql, seq_of_params)
        if commit:
            self.conn.commit()
        return cur

    def create_tables(self):
        self.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin', 'reception')),
                full_name TEXT NOT NULL
            )
            """,
            commit=True,
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS room_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type_name TEXT UNIQUE NOT NULL,
                price_per_night REAL NOT NULL CHECK(price_per_night >= 0),
                capacity INTEGER NOT NULL CHECK(capacity > 0),
                description TEXT
            )
            """,
            commit=True,
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_number TEXT UNIQUE NOT NULL,
                room_type_id INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available'
                    CHECK(status IN ('Available', 'Occupied', 'Cleaning', 'Maintenance')),
                note TEXT,
                FOREIGN KEY(room_type_id) REFERENCES room_types(id)
            )
            """,
            commit=True,
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                cccd TEXT UNIQUE,
                email TEXT,
                address TEXT
            )
            """,
            commit=True,
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT UNIQUE NOT NULL,
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                unit TEXT NOT NULL DEFAULT 'Lần'
            )
            """,
            commit=True,
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_code TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                room_id INTEGER NOT NULL,
                checkin_date TEXT NOT NULL,
                checkout_date TEXT NOT NULL,
                actual_checkout_date TEXT,
                guests_count INTEGER NOT NULL CHECK(guests_count > 0),
                status TEXT NOT NULL DEFAULT 'Reserved'
                    CHECK(status IN ('Reserved', 'Checked-in', 'Checked-out', 'Cancelled')),
                room_price REAL NOT NULL CHECK(room_price >= 0),
                note TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY(customer_id) REFERENCES customers(id),
                FOREIGN KEY(room_id) REFERENCES rooms(id)
            )
            """,
            commit=True,
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS booking_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL,
                service_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                unit_price REAL NOT NULL CHECK(unit_price >= 0),
                created_at TEXT NOT NULL,
                FOREIGN KEY(booking_id) REFERENCES bookings(id),
                FOREIGN KEY(service_id) REFERENCES services(id)
            )
            """,
            commit=True,
        )

        self.execute(
            """
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER UNIQUE NOT NULL,
                room_total REAL NOT NULL,
                service_total REAL NOT NULL,
                grand_total REAL NOT NULL,
                payment_method TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(booking_id) REFERENCES bookings(id)
            )
            """,
            commit=True,
        )

    def seed_data(self):
        users = self.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if users == 0:
            self.executemany(
                "INSERT INTO users(username, password, role, full_name) VALUES (?, ?, ?, ?)",
                [
                    ("admin", "admin123", "admin", "Quản trị viên"),
                    ("reception", "reception123", "reception", "Lễ tân"),
                ],
                commit=True,
            )

        room_types = self.execute("SELECT COUNT(*) AS c FROM room_types").fetchone()["c"]
        if room_types == 0:
            self.executemany(
                "INSERT INTO room_types(type_name, price_per_night, capacity, description) VALUES (?, ?, ?, ?)",
                [
                    ("Phòng đơn", 350000, 1, "Phòng tiêu chuẩn cho 1 khách"),
                    ("Phòng đôi", 550000, 2, "Phòng tiêu chuẩn cho 2 khách"),
                    ("VIP", 1200000, 4, "Phòng cao cấp"),
                ],
                commit=True,
            )

        rooms = self.execute("SELECT COUNT(*) AS c FROM rooms").fetchone()["c"]
        if rooms == 0:
            type_rows = self.execute("SELECT id, type_name FROM room_types").fetchall()
            type_map = {r["type_name"]: r["id"] for r in type_rows}
            self.executemany(
                "INSERT INTO rooms(room_number, room_type_id, status, note) VALUES (?, ?, ?, ?)",
                [
                    ("101", type_map["Phòng đơn"], "Available", "Tầng 1"),
                    ("102", type_map["Phòng đơn"], "Available", "Tầng 1"),
                    ("201", type_map["Phòng đôi"], "Available", "Tầng 2"),
                    ("202", type_map["Phòng đôi"], "Cleaning", "Đang dọn phòng"),
                    ("301", type_map["VIP"], "Available", "Tầng 3"),
                ],
                commit=True,
            )

        services = self.execute("SELECT COUNT(*) AS c FROM services").fetchone()["c"]
        if services == 0:
            self.executemany(
                "INSERT INTO services(service_name, unit_price, unit) VALUES (?, ?, ?)",
                [
                    ("Nước uống", 15000, "Chai"),
                    ("Giặt là", 50000, "Lần"),
                    ("Ăn sáng", 80000, "Suất"),
                ],
                commit=True,
            )

    def authenticate(self, username: str, password: str):
        row = self.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username.strip(), password.strip()),
        ).fetchone()
        return row

    def get_room_types(self):
        return self.execute("SELECT * FROM room_types ORDER BY id DESC").fetchall()

    def add_room_type(self, type_name: str, price: float, capacity: int, description: str):
        self.execute(
            "INSERT INTO room_types(type_name, price_per_night, capacity, description) VALUES (?, ?, ?, ?)",
            (type_name.strip(), price, capacity, description.strip()),
            commit=True,
        )

    def delete_room_type(self, room_type_id: int):
        used_room = self.execute(
            "SELECT 1 FROM rooms WHERE room_type_id=? LIMIT 1",
            (room_type_id,),
        ).fetchone()
        if used_room:
            raise ValueError("Không thể xóa loại phòng vì đang có phòng thuộc loại này.")
        self.execute("DELETE FROM room_types WHERE id=?", (room_type_id,), commit=True)

    def get_rooms(self):
        return self.execute(
            """
            SELECT r.id, r.room_number, rt.type_name, rt.price_per_night, rt.capacity, r.status, COALESCE(r.note, '') AS note
            FROM rooms r
            JOIN room_types rt ON r.room_type_id = rt.id
            ORDER BY r.room_number
            """
        ).fetchall()

    def add_room(self, room_number: str, room_type_id: int, status: str, note: str):
        self.execute(
            "INSERT INTO rooms(room_number, room_type_id, status, note) VALUES (?, ?, ?, ?)",
            (room_number.strip(), room_type_id, status, note.strip()),
            commit=True,
        )

    def delete_room(self, room_id: int):
        active_booking = self.execute(
            "SELECT 1 FROM bookings WHERE room_id=? AND status IN ('Reserved', 'Checked-in') LIMIT 1",
            (room_id,),
        ).fetchone()
        if active_booking:
            raise ValueError("Không thể xóa phòng vì đang có booking hoạt động.")
        self.execute("DELETE FROM rooms WHERE id=?", (room_id,), commit=True)

    def update_room_status(self, room_id: int, status: str):
        self.execute("UPDATE rooms SET status=? WHERE id=?", (status, room_id), commit=True)

    def get_customers(self):
        return self.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()

    def add_customer(self, full_name: str, phone: str, cccd: str, email: str, address: str):
        self.execute(
            "INSERT INTO customers(full_name, phone, cccd, email, address) VALUES (?, ?, ?, ?, ?)",
            (full_name.strip(), phone.strip(), cccd.strip(), email.strip(), address.strip()),
            commit=True,
        )

    def delete_customer(self, customer_id: int):
        active_booking = self.execute(
            "SELECT 1 FROM bookings WHERE customer_id=? AND status IN ('Reserved', 'Checked-in') LIMIT 1",
            (customer_id,),
        ).fetchone()
        if active_booking:
            raise ValueError("Không thể xóa khách hàng vì đang có booking hoạt động.")
        self.execute("DELETE FROM customers WHERE id=?", (customer_id,), commit=True)

    def get_services(self):
        return self.execute("SELECT * FROM services ORDER BY id DESC").fetchall()

    def add_service(self, service_name: str, unit_price: float, unit: str):
        self.execute(
            "INSERT INTO services(service_name, unit_price, unit) VALUES (?, ?, ?)",
            (service_name.strip(), unit_price, unit.strip()),
            commit=True,
        )

    def get_available_rooms(self):
        return self.execute(
            """
            SELECT r.id, r.room_number, rt.type_name, rt.price_per_night, rt.capacity
            FROM rooms r
            JOIN room_types rt ON rt.id = r.room_type_id
            WHERE r.status='Available'
            ORDER BY r.room_number
            """
        ).fetchall()

    def get_active_bookings(self):
        return self.execute(
            """
            SELECT b.id, b.booking_code, c.full_name AS customer_name, r.room_number,
                   b.checkin_date, b.checkout_date, b.status, b.room_price, b.guests_count
            FROM bookings b
            JOIN customers c ON c.id = b.customer_id
            JOIN rooms r ON r.id = b.room_id
            WHERE b.status IN ('Reserved', 'Checked-in')
            ORDER BY b.id DESC
            """
        ).fetchall()

    def create_booking(self, customer_id: int, room_id: int, checkin_date: str, checkout_date: str, guests_count: int, note: str):
        room = self.execute(
            """
            SELECT r.id, r.status, rt.price_per_night, rt.capacity
            FROM rooms r JOIN room_types rt ON r.room_type_id = rt.id
            WHERE r.id=?
            """,
            (room_id,),
        ).fetchone()
        if room is None:
            raise ValueError("Không tìm thấy phòng.")
        if room["status"] != "Available":
            raise ValueError("Phòng hiện không trống.")
        if guests_count > room["capacity"]:
            raise ValueError("Số khách vượt quá sức chứa của phòng.")

        start = datetime.strptime(checkin_date, DATE_FMT).date()
        end = datetime.strptime(checkout_date, DATE_FMT).date()
        if end <= start:
            raise ValueError("Ngày trả phòng phải sau ngày nhận phòng.")

        booking_code = f"BK{datetime.now().strftime('%Y%m%d%H%M%S')}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute(
            """
            INSERT INTO bookings(
                booking_code, customer_id, room_id, checkin_date, checkout_date,
                guests_count, status, room_price, note, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'Reserved', ?, ?, ?)
            """,
            (booking_code, customer_id, room_id, checkin_date, checkout_date, guests_count, room["price_per_night"], note.strip(), now),
            commit=True,
        )
        self.update_room_status(room_id, "Occupied")
        return booking_code

    def checkin_booking(self, booking_id: int):
        booking = self.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not booking:
            raise ValueError("Không tìm thấy phiếu đặt phòng.")
        if booking["status"] != "Reserved":
            raise ValueError("Chỉ phiếu ở trạng thái Reserved mới được nhận phòng.")
        self.execute("UPDATE bookings SET status='Checked-in' WHERE id=?", (booking_id,), commit=True)

    def add_service_to_booking(self, booking_id: int, service_id: int, quantity: int):
        if quantity <= 0:
            raise ValueError("Số lượng phải lớn hơn 0.")
        booking = self.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not booking:
            raise ValueError("Không tìm thấy booking.")
        if booking["status"] not in ("Reserved", "Checked-in"):
            raise ValueError("Chỉ có thể thêm dịch vụ cho booking đang hoạt động.")
        service = self.execute("SELECT * FROM services WHERE id=?", (service_id,)).fetchone()
        if not service:
            raise ValueError("Không tìm thấy dịch vụ.")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute(
            "INSERT INTO booking_services(booking_id, service_id, quantity, unit_price, created_at) VALUES (?, ?, ?, ?, ?)",
            (booking_id, service_id, quantity, service["unit_price"], now),
            commit=True,
        )

    def calculate_invoice(self, booking_id: int):
        booking = self.execute(
            """
            SELECT b.*, c.full_name AS customer_name, c.phone, r.room_number
            FROM bookings b
            JOIN customers c ON b.customer_id = c.id
            JOIN rooms r ON b.room_id = r.id
            WHERE b.id=?
            """,
            (booking_id,),
        ).fetchone()
        if not booking:
            raise ValueError("Không tìm thấy booking.")

        start = datetime.strptime(booking["checkin_date"], DATE_FMT).date()
        end_str = booking["actual_checkout_date"] or booking["checkout_date"]
        end = datetime.strptime(end_str, DATE_FMT).date()
        nights = max((end - start).days, 1)
        room_total = nights * booking["room_price"]

        service_rows = self.execute(
            """
            SELECT bs.quantity, bs.unit_price, s.service_name
            FROM booking_services bs
            JOIN services s ON s.id = bs.service_id
            WHERE bs.booking_id=?
            """,
            (booking_id,),
        ).fetchall()
        service_total = sum(r["quantity"] * r["unit_price"] for r in service_rows)

        return {
            "booking": booking,
            "nights": nights,
            "room_total": room_total,
            "service_rows": service_rows,
            "service_total": service_total,
            "grand_total": room_total + service_total,
        }

    def checkout_booking(self, booking_id: int, payment_method: str):
        booking = self.execute("SELECT * FROM bookings WHERE id=?", (booking_id,)).fetchone()
        if not booking:
            raise ValueError("Không tìm thấy booking.")
        if booking["status"] == "Checked-out":
            raise ValueError("Booking này đã trả phòng.")

        actual_checkout = today_str()
        self.execute(
            "UPDATE bookings SET status='Checked-out', actual_checkout_date=? WHERE id=?",
            (actual_checkout, booking_id),
            commit=True,
        )

        invoice = self.calculate_invoice(booking_id)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.execute(
            """
            INSERT OR REPLACE INTO invoices(booking_id, room_total, service_total, grand_total, payment_method, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                booking_id,
                invoice["room_total"],
                invoice["service_total"],
                invoice["grand_total"],
                payment_method,
                now,
            ),
            commit=True,
        )

        self.update_room_status(booking["room_id"], "Cleaning")
        return self.calculate_invoice(booking_id)

    def get_invoice_by_booking(self, booking_id: int):
        return self.execute(
            "SELECT * FROM invoices WHERE booking_id=?",
            (booking_id,),
        ).fetchone()

    def get_dashboard_stats(self):
        stats = {}
        stats["total_rooms"] = self.execute("SELECT COUNT(*) c FROM rooms").fetchone()["c"]
        stats["available_rooms"] = self.execute("SELECT COUNT(*) c FROM rooms WHERE status='Available'").fetchone()["c"]
        stats["occupied_rooms"] = self.execute("SELECT COUNT(*) c FROM rooms WHERE status='Occupied'").fetchone()["c"]
        stats["cleaning_rooms"] = self.execute("SELECT COUNT(*) c FROM rooms WHERE status='Cleaning'").fetchone()["c"]
        stats["total_customers"] = self.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]
        stats["active_bookings"] = self.execute("SELECT COUNT(*) c FROM bookings WHERE status IN ('Reserved','Checked-in')").fetchone()["c"]
        stats["revenue"] = self.execute("SELECT COALESCE(SUM(grand_total), 0) c FROM invoices").fetchone()["c"]
        return stats

    def get_monthly_revenue(self):
        rows = self.execute(
            """
            SELECT substr(created_at, 1, 7) AS month_key, SUM(grand_total) AS revenue
            FROM invoices
            GROUP BY substr(created_at, 1, 7)
            ORDER BY month_key
            """
        ).fetchall()
        return rows


class LoginWindow(tk.Tk):
    def __init__(self, db: DatabaseManager):
        super().__init__()
        self.db = db
        self.title("Đăng nhập hệ thống quản lý khách sạn")
        self.geometry("450x280")
        self.configure(bg="#f5f7fb")
        self.resizable(False, False)
        self._build_ui()

    def _build_ui(self):
        wrapper = tk.Frame(self, bg="white", bd=1, relief="solid")
        wrapper.place(relx=0.5, rely=0.5, anchor="center", width=360, height=210)

        tk.Label(wrapper, text="HOTEL MANAGEMENT", font=("Arial", 16, "bold"), bg="white", fg="#0f172a").pack(pady=(20, 5))
        tk.Label(wrapper, text="Đăng nhập để tiếp tục", font=("Arial", 10), bg="white", fg="#64748b").pack(pady=(0, 15))

        form = tk.Frame(wrapper, bg="white")
        form.pack(padx=25, fill="x")

        tk.Label(form, text="Tên đăng nhập", bg="white").grid(row=0, column=0, sticky="w", pady=5)
        self.username_entry = ttk.Entry(form)
        self.username_entry.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        tk.Label(form, text="Mật khẩu", bg="white").grid(row=2, column=0, sticky="w", pady=5)
        self.password_entry = ttk.Entry(form, show="*")
        self.password_entry.grid(row=3, column=0, sticky="ew")

        form.columnconfigure(0, weight=1)

        ttk.Button(wrapper, text="Đăng nhập", command=self.login).pack(pady=16)
        hint = "Tài khoản mẫu: admin/admin123 | reception/reception123"
        tk.Label(wrapper, text=hint, bg="white", fg="#475569", font=("Arial", 8)).pack(pady=(0, 8))

        self.username_entry.focus_set()
        self.bind("<Return>", lambda e: self.login())

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Thiếu dữ liệu", "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
            return
        user = self.db.authenticate(username, password)
        if not user:
            messagebox.showerror("Đăng nhập thất bại", "Sai tên đăng nhập hoặc mật khẩu.")
            return
        self.destroy()
        app = HotelManagementApp(self.db, user)
        app.mainloop()


class HotelManagementApp(tk.Tk):
    def __init__(self, db: DatabaseManager, user):
        super().__init__()
        self.db = db
        self.user = user
        self.title("Hệ thống quản lý khách sạn")
        self.geometry("1280x760")
        self.minsize(1150, 680)
        self.configure(bg="#eef2ff")
        self.selected_booking_id = None
        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        top = tk.Frame(self, bg="#0f172a", height=60)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text="HỆ THỐNG QUẢN LÝ KHÁCH SẠN", fg="white", bg="#0f172a", font=("Arial", 18, "bold")).pack(side="left", padx=16)
        user_text = f"{self.user['full_name']} | Vai trò: {self.user['role']}"
        tk.Label(top, text=user_text, fg="#cbd5e1", bg="#0f172a", font=("Arial", 11)).pack(side="right", padx=16)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_dashboard = ttk.Frame(self.notebook)
        self.tab_room_types = ttk.Frame(self.notebook)
        self.tab_rooms = ttk.Frame(self.notebook)
        self.tab_customers = ttk.Frame(self.notebook)
        self.tab_services = ttk.Frame(self.notebook)
        self.tab_booking = ttk.Frame(self.notebook)
        self.tab_checkout = ttk.Frame(self.notebook)
        self.tab_revenue = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_dashboard, text="Tổng quan")
        self.notebook.add(self.tab_room_types, text="Loại phòng")
        self.notebook.add(self.tab_rooms, text="Phòng")
        self.notebook.add(self.tab_customers, text="Khách hàng")
        self.notebook.add(self.tab_services, text="Dịch vụ")
        self.notebook.add(self.tab_booking, text="Đặt/Nhận phòng")
        self.notebook.add(self.tab_checkout, text="Trả phòng/Hóa đơn")
        self.notebook.add(self.tab_revenue, text="Thống kê")

        self._build_dashboard_tab()
        self._build_room_types_tab()
        self._build_rooms_tab()
        self._build_customers_tab()
        self._build_services_tab()
        self._build_booking_tab()
        self._build_checkout_tab()
        self._build_revenue_tab()

        if self.user["role"] != "admin":
            self.notebook.tab(self.tab_room_types, state="hidden")
            self.notebook.tab(self.tab_services, state="hidden")

    def _info_card(self, parent, title, variable, row, col):
        card = tk.Frame(parent, bg="white", bd=1, relief="solid")
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        tk.Label(card, text=title, bg="white", fg="#475569", font=("Arial", 11)).pack(anchor="w", padx=14, pady=(12, 4))
        tk.Label(card, textvariable=variable, bg="white", fg="#0f172a", font=("Arial", 20, "bold")).pack(anchor="w", padx=14, pady=(0, 12))

    def _build_dashboard_tab(self):
        for i in range(4):
            self.tab_dashboard.columnconfigure(i, weight=1)

        self.var_total_rooms = tk.StringVar(value="0")
        self.var_available = tk.StringVar(value="0")
        self.var_occupied = tk.StringVar(value="0")
        self.var_cleaning = tk.StringVar(value="0")
        self.var_customers = tk.StringVar(value="0")
        self.var_active_bookings = tk.StringVar(value="0")
        self.var_revenue = tk.StringVar(value="0 đ")

        self._info_card(self.tab_dashboard, "Tổng số phòng", self.var_total_rooms, 0, 0)
        self._info_card(self.tab_dashboard, "Phòng trống", self.var_available, 0, 1)
        self._info_card(self.tab_dashboard, "Phòng đang dùng", self.var_occupied, 0, 2)
        self._info_card(self.tab_dashboard, "Phòng đang dọn", self.var_cleaning, 0, 3)
        self._info_card(self.tab_dashboard, "Khách hàng", self.var_customers, 1, 0)
        self._info_card(self.tab_dashboard, "Booking hoạt động", self.var_active_bookings, 1, 1)
        self._info_card(self.tab_dashboard, "Doanh thu", self.var_revenue, 1, 2)

        help_box = tk.LabelFrame(self.tab_dashboard, text="Gợi ý sử dụng")
        help_box.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=10, pady=10)
        help_text = (
            "1. Tạo loại phòng → thêm phòng.\n"
            "2. Thêm khách hàng.\n"
            "3. Tạo booking ở tab Đặt/Nhận phòng.\n"
            "4. Có thể thêm dịch vụ cho booking.\n"
            "5. Trả phòng ở tab Trả phòng/Hóa đơn để sinh hóa đơn và doanh thu."
        )
        tk.Label(help_box, text=help_text, justify="left", padx=10, pady=10).pack(anchor="w")

    def _build_room_types_tab(self):
        form = tk.LabelFrame(self.tab_room_types, text="Thêm loại phòng")
        form.pack(fill="x", padx=10, pady=10)

        self.rt_name = ttk.Entry(form)
        self.rt_price = ttk.Entry(form)
        self.rt_capacity = ttk.Entry(form)
        self.rt_desc = ttk.Entry(form)

        labels = ["Tên loại phòng", "Giá / đêm", "Sức chứa", "Mô tả"]
        entries = [self.rt_name, self.rt_price, self.rt_capacity, self.rt_desc]
        for i, (lb, en) in enumerate(zip(labels, entries)):
            tk.Label(form, text=lb).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            en.grid(row=1, column=i, padx=6, pady=6, sticky="ew")
            form.columnconfigure(i, weight=1)

        ttk.Button(form, text="Thêm loại phòng", command=self.add_room_type).grid(row=1, column=4, padx=8)

        delete_box = tk.LabelFrame(self.tab_room_types, text="Xóa loại phòng")
        delete_box.pack(fill="x", padx=10, pady=(0, 10))
        self.delete_room_type_id = ttk.Entry(delete_box)
        tk.Label(delete_box, text="ID loại phòng").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.delete_room_type_id.grid(row=1, column=0, padx=6, pady=6)
        ttk.Button(delete_box, text="Xóa loại phòng", command=self.delete_room_type).grid(row=1, column=1, padx=8)

        self.room_types_tree = self._make_tree(
            self.tab_room_types,
            ["ID", "Tên loại", "Giá/đêm", "Sức chứa", "Mô tả"],
        )
        self.room_types_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_rooms_tab(self):
        form = tk.LabelFrame(self.tab_rooms, text="Thêm phòng")
        form.pack(fill="x", padx=10, pady=10)

        self.room_number_entry = ttk.Entry(form)
        self.room_type_combo = ttk.Combobox(form, state="readonly")
        self.room_status_combo = ttk.Combobox(form, state="readonly", values=["Available", "Occupied", "Cleaning", "Maintenance"])
        self.room_note_entry = ttk.Entry(form)
        self.room_status_combo.set("Available")

        controls = [
            ("Số phòng", self.room_number_entry),
            ("Loại phòng", self.room_type_combo),
            ("Trạng thái", self.room_status_combo),
            ("Ghi chú", self.room_note_entry),
        ]
        for i, (lb, widget) in enumerate(controls):
            tk.Label(form, text=lb).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            widget.grid(row=1, column=i, padx=6, pady=6, sticky="ew")
            form.columnconfigure(i, weight=1)
        ttk.Button(form, text="Thêm phòng", command=self.add_room).grid(row=1, column=4, padx=8)

        delete_box = tk.LabelFrame(self.tab_rooms, text="Xóa phòng")
        delete_box.pack(fill="x", padx=10, pady=(0, 10))
        self.delete_room_id = ttk.Entry(delete_box)
        tk.Label(delete_box, text="ID phòng").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.delete_room_id.grid(row=1, column=0, padx=6, pady=6)
        ttk.Button(delete_box, text="Xóa phòng", command=self.delete_room).grid(row=1, column=1, padx=8)

        status_box = tk.LabelFrame(self.tab_rooms, text="Đổi trạng thái phòng")
        status_box.pack(fill="x", padx=10, pady=(0, 10))
        self.room_update_id = ttk.Entry(status_box)
        self.room_update_status = ttk.Combobox(status_box, state="readonly", values=["Available", "Occupied", "Cleaning", "Maintenance"])
        tk.Label(status_box, text="ID phòng").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.room_update_id.grid(row=1, column=0, padx=6, pady=6)
        tk.Label(status_box, text="Trạng thái mới").grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.room_update_status.grid(row=1, column=1, padx=6, pady=6)
        ttk.Button(status_box, text="Cập nhật", command=self.update_room_status).grid(row=1, column=2, padx=8)

        self.rooms_tree = self._make_tree(
            self.tab_rooms,
            ["ID", "Số phòng", "Loại phòng", "Giá/đêm", "Sức chứa", "Trạng thái", "Ghi chú"],
        )
        self.rooms_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_customers_tab(self):
        form = tk.LabelFrame(self.tab_customers, text="Thêm khách hàng")
        form.pack(fill="x", padx=10, pady=10)

        self.cus_name = ttk.Entry(form)
        self.cus_phone = ttk.Entry(form)
        self.cus_cccd = ttk.Entry(form)
        self.cus_email = ttk.Entry(form)
        self.cus_address = ttk.Entry(form)

        widgets = [
            ("Họ tên", self.cus_name),
            ("SĐT", self.cus_phone),
            ("CCCD", self.cus_cccd),
            ("Email", self.cus_email),
            ("Địa chỉ", self.cus_address),
        ]
        for i, (lb, widget) in enumerate(widgets):
            tk.Label(form, text=lb).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            widget.grid(row=1, column=i, padx=6, pady=6, sticky="ew")
            form.columnconfigure(i, weight=1)
        ttk.Button(form, text="Thêm khách hàng", command=self.add_customer).grid(row=1, column=5, padx=8)

        delete_box = tk.LabelFrame(self.tab_customers, text="Xóa khách hàng")
        delete_box.pack(fill="x", padx=10, pady=(0, 10))
        self.delete_customer_id = ttk.Entry(delete_box)
        tk.Label(delete_box, text="ID khách hàng").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.delete_customer_id.grid(row=1, column=0, padx=6, pady=6)
        ttk.Button(delete_box, text="Xóa khách hàng", command=self.delete_customer).grid(row=1, column=1, padx=8)

        self.customers_tree = self._make_tree(
            self.tab_customers,
            ["ID", "Họ tên", "SĐT", "CCCD", "Email", "Địa chỉ"],
        )
        self.customers_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_services_tab(self):
        form = tk.LabelFrame(self.tab_services, text="Quản lý dịch vụ")
        form.pack(fill="x", padx=10, pady=10)

        self.service_name = ttk.Entry(form)
        self.service_price = ttk.Entry(form)
        self.service_unit = ttk.Entry(form)

        items = [
            ("Tên dịch vụ", self.service_name),
            ("Đơn giá", self.service_price),
            ("Đơn vị", self.service_unit),
        ]
        for i, (lb, widget) in enumerate(items):
            tk.Label(form, text=lb).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            widget.grid(row=1, column=i, padx=6, pady=6, sticky="ew")
            form.columnconfigure(i, weight=1)
        ttk.Button(form, text="Thêm dịch vụ", command=self.add_service).grid(row=1, column=3, padx=8)

        self.services_tree = self._make_tree(
            self.tab_services,
            ["ID", "Tên dịch vụ", "Đơn giá", "Đơn vị"],
        )
        self.services_tree.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_booking_tab(self):
        outer = tk.Frame(self.tab_booking)
        outer.pack(fill="both", expand=True, padx=10, pady=10)

        top_form = tk.LabelFrame(outer, text="Tạo phiếu đặt phòng")
        top_form.pack(fill="x")

        self.booking_customer_combo = ttk.Combobox(top_form, state="readonly")
        self.booking_room_combo = ttk.Combobox(top_form, state="readonly")
        self.booking_checkin = ttk.Entry(top_form)
        self.booking_checkout = ttk.Entry(top_form)
        self.booking_guest_count = ttk.Entry(top_form)
        self.booking_note = ttk.Entry(top_form)
        self.booking_checkin.insert(0, today_str())
        self.booking_checkout.insert(0, today_str())
        self.booking_guest_count.insert(0, "1")

        controls = [
            ("Khách hàng", self.booking_customer_combo),
            ("Phòng trống", self.booking_room_combo),
            ("Ngày nhận", self.booking_checkin),
            ("Ngày trả", self.booking_checkout),
            ("Số khách", self.booking_guest_count),
            ("Ghi chú", self.booking_note),
        ]
        for i, (lb, widget) in enumerate(controls):
            tk.Label(top_form, text=lb).grid(row=0, column=i, padx=6, pady=6, sticky="w")
            widget.grid(row=1, column=i, padx=6, pady=6, sticky="ew")
            top_form.columnconfigure(i, weight=1)
        ttk.Button(top_form, text="Tạo booking", command=self.create_booking).grid(row=1, column=6, padx=8)

        mid = tk.Frame(outer)
        mid.pack(fill="x", pady=8)

        checkin_box = tk.LabelFrame(mid, text="Nhận phòng")
        checkin_box.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.checkin_booking_id = ttk.Entry(checkin_box)
        tk.Label(checkin_box, text="ID booking").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.checkin_booking_id.grid(row=1, column=0, padx=6, pady=6)
        ttk.Button(checkin_box, text="Check-in", command=self.checkin_booking).grid(row=1, column=1, padx=8)

        service_box = tk.LabelFrame(mid, text="Thêm dịch vụ vào booking")
        service_box.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.add_service_booking_id = ttk.Entry(service_box)
        self.add_service_combo = ttk.Combobox(service_box, state="readonly")
        self.add_service_quantity = ttk.Entry(service_box)
        self.add_service_quantity.insert(0, "1")
        tk.Label(service_box, text="ID booking").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.add_service_booking_id.grid(row=1, column=0, padx=6, pady=6)
        tk.Label(service_box, text="Dịch vụ").grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.add_service_combo.grid(row=1, column=1, padx=6, pady=6)
        tk.Label(service_box, text="Số lượng").grid(row=0, column=2, padx=6, pady=6, sticky="w")
        self.add_service_quantity.grid(row=1, column=2, padx=6, pady=6)
        ttk.Button(service_box, text="Thêm", command=self.add_service_to_booking).grid(row=1, column=3, padx=8)

        self.bookings_tree = self._make_tree(
            outer,
            ["ID", "Mã booking", "Khách hàng", "Phòng", "Ngày nhận", "Ngày trả", "Trạng thái", "Giá phòng", "Số khách"],
        )
        self.bookings_tree.pack(fill="both", expand=True, pady=(8, 0))

    def _build_checkout_tab(self):
        top = tk.Frame(self.tab_checkout)
        top.pack(fill="x", padx=10, pady=10)

        left = tk.LabelFrame(top, text="Trả phòng")
        left.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.checkout_booking_id = ttk.Entry(left)
        self.checkout_payment = ttk.Combobox(left, state="readonly", values=["Tiền mặt", "Chuyển khoản", "Thẻ"])
        self.checkout_payment.set("Tiền mặt")
        tk.Label(left, text="ID booking").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.checkout_booking_id.grid(row=1, column=0, padx=6, pady=6)
        tk.Label(left, text="Phương thức thanh toán").grid(row=0, column=1, padx=6, pady=6, sticky="w")
        self.checkout_payment.grid(row=1, column=1, padx=6, pady=6)
        ttk.Button(left, text="Trả phòng & lập hóa đơn", command=self.checkout_booking).grid(row=1, column=2, padx=8)

        right = tk.LabelFrame(top, text="Xem hóa đơn theo booking")
        right.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.invoice_booking_id = ttk.Entry(right)
        tk.Label(right, text="ID booking").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.invoice_booking_id.grid(row=1, column=0, padx=6, pady=6)
        ttk.Button(right, text="Hiển thị hóa đơn", command=self.show_invoice_by_booking).grid(row=1, column=1, padx=8)

        self.invoice_text = tk.Text(self.tab_checkout, height=28, font=("Consolas", 11))
        self.invoice_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _build_revenue_tab(self):
        wrapper = tk.Frame(self.tab_revenue)
        wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        top = tk.Frame(wrapper)
        top.pack(fill="x")
        ttk.Button(top, text="Làm mới thống kê", command=self.refresh_revenue_chart).pack(side="left")
        note = "Nếu chưa có biểu đồ, hãy cài: pip install matplotlib"
        tk.Label(top, text=note, fg="#475569").pack(side="left", padx=12)

        self.revenue_tree = self._make_tree(wrapper, ["Tháng", "Doanh thu"])
        self.revenue_tree.pack(fill="both", expand=True, pady=10)

        self.chart_holder = tk.Frame(wrapper, bg="white", bd=1, relief="solid")
        self.chart_holder.pack(fill="both", expand=True)

    def _make_tree(self, parent, headings):
        frame = tk.Frame(parent)
        tree = ttk.Treeview(frame, show="headings")
        tree["columns"] = headings
        for h in headings:
            tree.heading(h, text=h)
            tree.column(h, width=120, anchor="center")
        yscroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=yscroll.set)
        tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        return frame

    def _clear_tree_frame(self, tree_frame):
        tree_widget = tree_frame.winfo_children()[0]
        for item in tree_widget.get_children():
            tree_widget.delete(item)
        return tree_widget

    def add_room_type(self):
        try:
            self.db.add_room_type(
                self.rt_name.get(),
                float(self.rt_price.get()),
                int(self.rt_capacity.get()),
                self.rt_desc.get(),
            )
            messagebox.showinfo("Thành công", "Đã thêm loại phòng.")
            self.rt_name.delete(0, tk.END)
            self.rt_price.delete(0, tk.END)
            self.rt_capacity.delete(0, tk.END)
            self.rt_desc.delete(0, tk.END)
            self.refresh_room_types()
            self.refresh_room_type_combo()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def add_room(self):
        try:
            room_type_value = self.room_type_combo.get()
            if not room_type_value:
                raise ValueError("Vui lòng chọn loại phòng.")
            room_type_id = int(room_type_value.split(" - ")[0])
            self.db.add_room(
                self.room_number_entry.get(),
                room_type_id,
                self.room_status_combo.get(),
                self.room_note_entry.get(),
            )
            messagebox.showinfo("Thành công", "Đã thêm phòng.")
            self.room_number_entry.delete(0, tk.END)
            self.room_note_entry.delete(0, tk.END)
            self.room_status_combo.set("Available")
            self.refresh_rooms()
            self.refresh_available_room_combo()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def update_room_status(self):
        try:
            room_id = int(self.room_update_id.get())
            status = self.room_update_status.get()
            if not status:
                raise ValueError("Vui lòng chọn trạng thái mới.")
            self.db.update_room_status(room_id, status)
            messagebox.showinfo("Thành công", "Đã cập nhật trạng thái phòng.")
            self.refresh_rooms()
            self.refresh_available_room_combo()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def add_customer(self):
        try:
            self.db.add_customer(
                self.cus_name.get(),
                self.cus_phone.get(),
                self.cus_cccd.get(),
                self.cus_email.get(),
                self.cus_address.get(),
            )
            messagebox.showinfo("Thành công", "Đã thêm khách hàng.")
            for widget in [self.cus_name, self.cus_phone, self.cus_cccd, self.cus_email, self.cus_address]:
                widget.delete(0, tk.END)
            self.refresh_customers()
            self.refresh_customer_combo()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete_room_type(self):
        try:
            room_type_id = int(self.delete_room_type_id.get())
            if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa loại phòng ID {room_type_id}?"):
                return
            self.db.delete_room_type(room_type_id)
            messagebox.showinfo("Thành công", "Đã xóa loại phòng.")
            self.delete_room_type_id.delete(0, tk.END)
            self.refresh_room_types()
            self.refresh_room_type_combo()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete_room(self):
        try:
            room_id = int(self.delete_room_id.get())
            if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa phòng ID {room_id}?"):
                return
            self.db.delete_room(room_id)
            messagebox.showinfo("Thành công", "Đã xóa phòng.")
            self.delete_room_id.delete(0, tk.END)
            self.refresh_rooms()
            self.refresh_available_room_combo()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def delete_customer(self):
        try:
            customer_id = int(self.delete_customer_id.get())
            if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa khách hàng ID {customer_id}?"):
                return
            self.db.delete_customer(customer_id)
            messagebox.showinfo("Thành công", "Đã xóa khách hàng.")
            self.delete_customer_id.delete(0, tk.END)
            self.refresh_customers()
            self.refresh_customer_combo()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def add_service(self):
        try:
            self.db.add_service(
                self.service_name.get(),
                float(self.service_price.get()),
                self.service_unit.get() or "Lần",
            )
            messagebox.showinfo("Thành công", "Đã thêm dịch vụ.")
            self.service_name.delete(0, tk.END)
            self.service_price.delete(0, tk.END)
            self.service_unit.delete(0, tk.END)
            self.refresh_services()
            self.refresh_service_combo()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def create_booking(self):
        try:
            customer_value = self.booking_customer_combo.get()
            room_value = self.booking_room_combo.get()
            if not customer_value or not room_value:
                raise ValueError("Vui lòng chọn khách hàng và phòng.")
            customer_id = int(customer_value.split(" - ")[0])
            room_id = int(room_value.split(" - ")[0])
            booking_code = self.db.create_booking(
                customer_id,
                room_id,
                self.booking_checkin.get().strip(),
                self.booking_checkout.get().strip(),
                int(self.booking_guest_count.get()),
                self.booking_note.get(),
            )
            messagebox.showinfo("Thành công", f"Đã tạo booking: {booking_code}")
            self.booking_note.delete(0, tk.END)
            self.refresh_bookings()
            self.refresh_available_room_combo()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def checkin_booking(self):
        try:
            booking_id = int(self.checkin_booking_id.get())
            self.db.checkin_booking(booking_id)
            messagebox.showinfo("Thành công", "Khách đã nhận phòng.")
            self.refresh_bookings()
            self.refresh_dashboard()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def add_service_to_booking(self):
        try:
            booking_id = int(self.add_service_booking_id.get())
            service_value = self.add_service_combo.get()
            if not service_value:
                raise ValueError("Vui lòng chọn dịch vụ.")
            service_id = int(service_value.split(" - ")[0])
            quantity = int(self.add_service_quantity.get())
            self.db.add_service_to_booking(booking_id, service_id, quantity)
            messagebox.showinfo("Thành công", "Đã thêm dịch vụ vào booking.")
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def checkout_booking(self):
        try:
            booking_id = int(self.checkout_booking_id.get())
            payment_method = self.checkout_payment.get()
            result = self.db.checkout_booking(booking_id, payment_method)
            self.render_invoice(result, payment_method)
            messagebox.showinfo("Thành công", "Đã trả phòng và tạo hóa đơn.")
            self.refresh_all()
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def show_invoice_by_booking(self):
        try:
            booking_id = int(self.invoice_booking_id.get())
            result = self.db.calculate_invoice(booking_id)
            invoice = self.db.get_invoice_by_booking(booking_id)
            payment_method = invoice["payment_method"] if invoice else "Chưa thanh toán"
            self.render_invoice(result, payment_method)
        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

    def render_invoice(self, invoice_data, payment_method: str):
        booking = invoice_data["booking"]
        lines = []
        lines.append("=" * 60)
        lines.append("                HOA DON THANH TOAN KHACH SAN")
        lines.append("=" * 60)
        lines.append(f"Ma booking      : {booking['booking_code']}")
        lines.append(f"Khach hang      : {booking['customer_name']}")
        lines.append(f"So dien thoai   : {booking['phone']}")
        lines.append(f"Phong           : {booking['room_number']}")
        lines.append(f"Ngay nhan phong : {booking['checkin_date']}")
        lines.append(f"Ngay tra phong  : {booking['actual_checkout_date'] or booking['checkout_date']}")
        lines.append(f"So dem          : {invoice_data['nights']}")
        lines.append("-" * 60)
        lines.append(f"Tien phong      : {invoice_data['room_total']:,.0f} VND")
        lines.append("Dich vu phat sinh:")
        if invoice_data["service_rows"]:
            for item in invoice_data["service_rows"]:
                amount = item['quantity'] * item['unit_price']
                lines.append(f"  - {item['service_name']}: {item['quantity']} x {item['unit_price']:,.0f} = {amount:,.0f} VND")
        else:
            lines.append("  - Khong co")
        lines.append(f"Tong tien dich vu: {invoice_data['service_total']:,.0f} VND")
        lines.append("-" * 60)
        lines.append(f"THANH TIEN      : {invoice_data['grand_total']:,.0f} VND")
        lines.append(f"Thanh toan      : {payment_method}")
        lines.append(f"Ngay in         : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=" * 60)

        self.invoice_text.delete("1.0", tk.END)
        self.invoice_text.insert(tk.END, "\n".join(lines))

    def refresh_dashboard(self):
        stats = self.db.get_dashboard_stats()
        self.var_total_rooms.set(str(stats["total_rooms"]))
        self.var_available.set(str(stats["available_rooms"]))
        self.var_occupied.set(str(stats["occupied_rooms"]))
        self.var_cleaning.set(str(stats["cleaning_rooms"]))
        self.var_customers.set(str(stats["total_customers"]))
        self.var_active_bookings.set(str(stats["active_bookings"]))
        self.var_revenue.set(f"{stats['revenue']:,.0f} đ")

    def refresh_room_types(self):
        tree = self._clear_tree_frame(self.room_types_tree)
        for r in self.db.get_room_types():
            tree.insert("", tk.END, values=(r["id"], r["type_name"], f"{r['price_per_night']:,.0f}", r["capacity"], r["description"] or ""))

    def refresh_room_type_combo(self):
        room_types = self.db.get_room_types()
        values = [f"{r['id']} - {r['type_name']} ({r['price_per_night']:,.0f} đ)" for r in room_types]
        self.room_type_combo["values"] = values
        if values:
            self.room_type_combo.set(values[0])

    def refresh_rooms(self):
        tree = self._clear_tree_frame(self.rooms_tree)
        for r in self.db.get_rooms():
            tree.insert("", tk.END, values=(r["id"], r["room_number"], r["type_name"], f"{r['price_per_night']:,.0f}", r["capacity"], r["status"], r["note"]))

    def refresh_customers(self):
        tree = self._clear_tree_frame(self.customers_tree)
        for r in self.db.get_customers():
            tree.insert("", tk.END, values=(r["id"], r["full_name"], r["phone"], r["cccd"] or "", r["email"] or "", r["address"] or ""))

    def refresh_customer_combo(self):
        customers = self.db.get_customers()
        values = [f"{r['id']} - {r['full_name']} - {r['phone']}" for r in customers]
        self.booking_customer_combo["values"] = values
        if values:
            self.booking_customer_combo.set(values[0])

    def refresh_services(self):
        tree = self._clear_tree_frame(self.services_tree)
        for r in self.db.get_services():
            tree.insert("", tk.END, values=(r["id"], r["service_name"], f"{r['unit_price']:,.0f}", r["unit"]))

    def refresh_service_combo(self):
        services = self.db.get_services()
        values = [f"{r['id']} - {r['service_name']} ({r['unit_price']:,.0f} đ/{r['unit']})" for r in services]
        self.add_service_combo["values"] = values
        if values:
            self.add_service_combo.set(values[0])

    def refresh_available_room_combo(self):
        rooms = self.db.get_available_rooms()
        values = [f"{r['id']} - Phòng {r['room_number']} - {r['type_name']} - {r['price_per_night']:,.0f} đ" for r in rooms]
        self.booking_room_combo["values"] = values
        if values:
            self.booking_room_combo.set(values[0])
        else:
            self.booking_room_combo.set("")

    def refresh_bookings(self):
        tree = self._clear_tree_frame(self.bookings_tree)
        for r in self.db.get_active_bookings():
            tree.insert("", tk.END, values=(r["id"], r["booking_code"], r["customer_name"], r["room_number"], r["checkin_date"], r["checkout_date"], r["status"], f"{r['room_price']:,.0f}", r["guests_count"]))

    def refresh_revenue_chart(self):
        tree = self._clear_tree_frame(self.revenue_tree)
        rows = self.db.get_monthly_revenue()
        for r in rows:
            tree.insert("", tk.END, values=(r["month_key"], f"{r['revenue']:,.0f} đ"))

        for widget in self.chart_holder.winfo_children():
            widget.destroy()

        if not MATPLOTLIB_OK:
            tk.Label(self.chart_holder, text="Chưa có matplotlib nên chưa hiển thị được biểu đồ.\nCài bằng lệnh: pip install matplotlib", bg="white", fg="#334155", font=("Arial", 12)).pack(expand=True)
            return

        labels = [r["month_key"] for r in rows]
        values = [r["revenue"] for r in rows]
        if not labels:
            tk.Label(self.chart_holder, text="Chưa có dữ liệu doanh thu để vẽ biểu đồ.", bg="white", fg="#334155", font=("Arial", 12)).pack(expand=True)
            return

        fig = Figure(figsize=(7, 3.5), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(labels, values, marker="o")
        ax.set_title("Doanh thu theo tháng")
        ax.set_xlabel("Tháng")
        ax.set_ylabel("Doanh thu")
        ax.tick_params(axis='x', rotation=20)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.chart_holder)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_room_types()
        self.refresh_room_type_combo()
        self.refresh_rooms()
        self.refresh_customers()
        self.refresh_customer_combo()
        self.refresh_services()
        self.refresh_service_combo()
        self.refresh_available_room_combo()
        self.refresh_bookings()
        self.refresh_revenue_chart()


def main():
    db = DatabaseManager()
    app = LoginWindow(db)
    app.mainloop()


if __name__ == "__main__":
    main()
