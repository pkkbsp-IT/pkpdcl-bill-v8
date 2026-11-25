# PKPDCL BILL CALCULATOR - VERSION 8.1 (CLEAN & STABLE)

import os
import re
import sys
import sqlite3
import html
import traceback
from datetime import datetime, timedelta
from urllib.parse import urlencode

from kivy.app import App
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.utils import platform
from kivy.graphics import Color, Rectangle
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserListView

NAVY = (0.07, 0.17, 0.32, 1)
BLUE = (0.10, 0.31, 0.58, 1)
GREEN = (0.10, 0.48, 0.31, 1)
BG = (0.94, 0.96, 0.99, 1)
CARD_BG = (1, 1, 1, 1)
DARK = (0.08, 0.13, 0.21, 1)
MUTED = (0.38, 0.43, 0.50, 1)
WHITE = (1, 1, 1, 1)
POPUP_TEXT = (0.96, 0.98, 1, 1)

COMPANY_NAME = "PRAMOD KASHYAP POWER DISTRIBUTION CORPORATION LIMITED"
UPI_ID = "9009203060@ptsbi"
UPI_PAYEE_NAME = "PKPDCL"
ADMIN_USER = "pramod"
ADMIN_PASSWORD = "3891"
PAYMENT_DAYS = 10


def find_logo():
    candidates = []
    try:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pkpdcl_logo.png"))
    except Exception:
        pass
    candidates.extend([
        os.path.join(os.getcwd(), "pkpdcl_logo.png"),
        "/storage/emulated/0/Download/pkpdcl_logo.png",
        "/storage/emulated/0/Pictures/pkpdcl_logo.png",
    ])
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.path.getsize(candidate) > 0:
            return candidate
    return None


def payment_due_date(bill_date_text):
    try:
        d = datetime.strptime(bill_date_text, "%d-%m-%Y").date()
        return (d + timedelta(days=PAYMENT_DAYS)).strftime("%d-%m-%Y")
    except Exception:
        return "-"


def format_billing_month(month_text):
    raw = str(month_text or "").strip()
    try:
        dt = datetime.strptime(raw, "%Y-%m")
        return dt.strftime("%b-%Y").upper()
    except Exception:
        return raw.upper() if raw else "-"


def create_upi_qr(amount, consumer_no, bill_month, output_path):
    try:
        import qrcode
        params = {
            "pa": UPI_ID.strip(),
            "pn": UPI_PAYEE_NAME,
            "am": f"{float(amount):.2f}",
            "cu": "INR",
            "tn": f"Bill {consumer_no} {bill_month}",
        }
        qrcode.make("upi://pay?" + urlencode(params)).save(output_path)
        return output_path
    except Exception:
        return None


def money(value):
    try:
        return f"Rs. {float(value):,.2f}"
    except Exception:
        return "Rs. 0.00"


def energy_charge(units):
    if units < 0:
        raise ValueError("Units cannot be negative.")
    if units <= 100:
        rate = 4.10
    elif units <= 200:
        rate = 4.20
    elif units <= 400:
        rate = 5.60
    elif units <= 600:
        rate = 6.60
    else:
        rate = 8.30
    return round(float(units) * rate, 2), rate


def make_button(text, color=BLUE, text_color=WHITE, height=44):
    return Button(
        text=text,
        size_hint_y=None,
        height=dp(height),
        background_normal="",
        background_color=color,
        color=text_color,
        font_size="13sp",
        bold=True,
    )


def make_label(text, size=13, color=DARK, bold=False, height=30, wrap=False):
    lbl = Label(
        text=str(text),
        size_hint_y=None,
        height=dp(height),
        color=color,
        font_size=f"{size}sp",
        bold=bold,
        halign="left",
        valign="middle",
    )
    if wrap:
        lbl.bind(size=lbl.setter("text_size"))
    return lbl


def show_message(title, message):
    try:
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        label = Label(
            text=str(message),
            color=POPUP_TEXT,
            font_size="13sp",
            halign="center",
            valign="middle",
        )
        label.bind(size=label.setter("text_size"))
        content.add_widget(label)
        button = make_button("OK", GREEN, height=44)
        content.add_widget(button)
        popup = Popup(title=str(title), content=content, size_hint=(0.92, 0.52))
        button.bind(on_press=popup.dismiss)
        popup.open()
        return popup
    except Exception:
        return None


def output_folder(app, subfolder):
    candidates = []
    if platform == "android":
        candidates.append("/storage/emulated/0/Download/PKPDCL/" + subfolder)
    candidates.append(os.path.join(app.user_data_dir, subfolder))
    for folder in candidates:
        try:
            os.makedirs(folder, exist_ok=True)
            test = os.path.join(folder, ".pkpdcl_write_test")
            with open(test, "w") as f:
                f.write("ok")
            os.remove(test)
            return folder
        except Exception:
            continue
    raise OSError("Cannot create a writable output folder.")


def android_file_intent(path):
    from jnius import autoclass

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    Uri = autoclass("android.net.Uri")
    File = autoclass("java.io.File")
    activity = getattr(PythonActivity, "mActivity", None)
    if activity is None:
        raise RuntimeError("Android activity not available.")

    file_obj = File(os.path.abspath(path))
    uri = None

    try:
        package = str(activity.getPackageName())
        providers = [
            "androidx.core.content.FileProvider",
            "android.support.v4.content.FileProvider",
        ]
        for provider_name in providers:
            try:
                FileProvider = autoclass(provider_name)
            except Exception:
                continue
            for authority in (
                package + ".provider",
                package + ".fileprovider",
                package + ".files",
            ):
                try:
                    uri = FileProvider.getUriForFile(activity, authority, file_obj)
                    if uri is not None:
                        break
                except Exception:
                    pass
            if uri is not None:
                break
    except Exception:
        pass

    view_uri = uri if uri is not None else Uri.fromFile(file_obj)
    intent = Intent(Intent.ACTION_VIEW)
    intent.setDataAndType(view_uri, "application/pdf")
    intent.addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
    intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
    try:
        activity.startActivity(intent)
    except Exception:
        try:
            StrictMode = autoclass("android.os.StrictMode")
            Builder = autoclass("android.os.StrictMode$VmPolicy$Builder")
            StrictMode.setVmPolicy(Builder().build())
        except Exception:
            pass
        fallback = Intent(Intent.ACTION_VIEW)
        fallback.setDataAndType(Uri.fromFile(file_obj), "application/pdf")
        fallback.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(fallback)


def android_text_intent(message, whatsapp_only=False):
    from jnius import autoclass

    clean_text = str(message or "").strip()
    if not clean_text:
        raise ValueError("Bill summary text is empty.")

    PythonActivity = autoclass("org.kivy.android.PythonActivity")
    Intent = autoclass("android.content.Intent")
    activity = getattr(PythonActivity, "mActivity", None)
    if activity is None:
        raise RuntimeError("Android activity not available.")

    send_intent = Intent(Intent.ACTION_SEND)
    send_intent.setType("text/plain")
    send_intent.putExtra(Intent.EXTRA_TEXT, clean_text)
    send_intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)

    if whatsapp_only:
        for pkg in ("com.whatsapp", "com.whatsapp.w4b"):
            try:
                wa_intent = Intent(send_intent)
                wa_intent.setPackage(pkg)
                activity.startActivity(wa_intent)
                return "whatsapp"
            except Exception:
                continue

    try:
        chooser = Intent.createChooser(send_intent, "Share Bill Text")
        chooser.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        activity.startActivity(chooser)
        return "chooser"
    except Exception:
        activity.startActivity(send_intent)
        return "direct"


def open_pdf_external(path):
    if not path or not os.path.isfile(path):
        raise FileNotFoundError("PDF file not found. Generate the bill PDF first.")
    if platform == "android":
        android_file_intent(path)
    else:
        import webbrowser
        webbrowser.open("file://" + os.path.abspath(path))


class Database:
    def __init__(self, path):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_tables()

    def create_tables(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS consumers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, consumer_no TEXT, mobile TEXT,
                meter_no TEXT, address TEXT, updated_at TEXT
            )
        """)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                consumer_id INTEGER NOT NULL, bill_month TEXT NOT NULL,
                bill_date TEXT, old_reading REAL, new_reading REAL,
                units REAL, rate REAL, energy REAL, fixed REAL, duty REAL,
                cess REAL, other REAL, arrears REAL, rebate REAL,
                adjustment REAL, gross REAL, total REAL,
                status TEXT DEFAULT 'Unpaid',
                UNIQUE(consumer_id, bill_month),
                FOREIGN KEY(consumer_id) REFERENCES consumers(id)
            )
        """)
        self.conn.commit()
        self.ensure_schema_compatibility()

    def ensure_schema_compatibility(self):
        consumer_columns = {
            "name": "TEXT", "consumer_no": "TEXT", "mobile": "TEXT",
            "meter_no": "TEXT", "address": "TEXT", "updated_at": "TEXT"
        }
        bill_columns = {
            "consumer_id": "INTEGER", "bill_month": "TEXT",
            "bill_date": "TEXT", "old_reading": "REAL", "new_reading": "REAL",
            "units": "REAL", "rate": "REAL", "energy": "REAL", "fixed": "REAL",
            "duty": "REAL", "cess": "REAL", "other": "REAL", "arrears": "REAL",
            "rebate": "REAL", "adjustment": "REAL", "gross": "REAL",
            "total": "REAL", "status": "TEXT DEFAULT 'Unpaid'"
        }
        for table, columns in (("consumers", consumer_columns), ("bills", bill_columns)):
            existing = {row[1] for row in self.conn.execute(f"PRAGMA table_info({table})")}
            for column, definition in columns.items():
                if column not in existing:
                    self.conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        self.conn.execute("""
            DELETE FROM bills
            WHERE id NOT IN (
                SELECT MAX(id) FROM bills
                GROUP BY consumer_id, bill_month
            )
        """)
        self.conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_bills_consumer_month
            ON bills(consumer_id, bill_month)
        """)
        self.conn.commit()

    def all_consumers(self, query=""):
        q = f"%{query.strip()}%"
        return self.conn.execute("""
            SELECT * FROM consumers
            WHERE name LIKE ? OR consumer_no LIKE ?
               OR mobile LIKE ? OR meter_no LIKE ?
            ORDER BY name COLLATE NOCASE
        """, (q, q, q, q)).fetchall()

    def get_consumer(self, cid):
        return self.conn.execute("SELECT * FROM consumers WHERE id=?", (cid,)).fetchone()

    def save_consumer(self, data, cid=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        values = (
            data["name"].strip(),
            data.get("consumer_no", "").strip(),
            data.get("mobile", "").strip(),
            data.get("meter_no", "").strip(),
            data.get("address", "").strip(),
            now,
        )
        if not values[0]:
            raise ValueError("Consumer name is required.")
        if cid:
            self.conn.execute("""
                UPDATE consumers SET name=?, consumer_no=?, mobile=?,
                meter_no=?, address=?, updated_at=? WHERE id=?
            """, values + (cid,))
        else:
            self.conn.execute("""
                INSERT INTO consumers
                (name, consumer_no, mobile, meter_no, address, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, values)
        self.conn.commit()

    def import_consumer_rows(self, rows):
        added = updated = skipped = 0
        cur = self.conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for row in rows:
            name = str(row.get("name") or "").strip()
            if not name:
                skipped += 1
                continue
            bp = str(row.get("consumer_no") or "").strip()
            mobile = str(row.get("mobile") or "").strip()
            meter = str(row.get("meter_no") or "").strip()
            address = str(row.get("address") or "").strip()
            existing = None
            if bp:
                existing = cur.execute(
                    "SELECT id FROM consumers WHERE consumer_no=? LIMIT 1", (bp,)
                ).fetchone()
            if existing:
                cur.execute("""
                    UPDATE consumers SET name=?, mobile=?, meter_no=?, address=?, updated_at=?
                    WHERE id=?
                """, (name, mobile, meter, address, now, existing["id"]))
                updated += 1
            else:
                cur.execute("""
                    INSERT INTO consumers
                    (name, consumer_no, mobile, meter_no, address, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, bp, mobile, meter, address, now))
                added += 1
        self.conn.commit()
        return added, updated, skipped

    def previous_reading(self, cid, before_month=None):
        row = self.conn.execute("""
            SELECT new_reading FROM bills
            WHERE consumer_id=?
            ORDER BY bill_month DESC, id DESC LIMIT 1
        """, (cid,)).fetchone()
        return float(row["new_reading"]) if row and row["new_reading"] is not None else 0.0

    def save_bill(self, cid, bill_month, bill, status="Unpaid"):
        values = (
            cid, str(bill_month), bill.get("date", ""),
            float(bill.get("old", 0)), float(bill.get("new", 0)),
            float(bill.get("units", 0)), float(bill.get("rate", 0)),
            float(bill.get("energy", 0)), float(bill.get("fixed", 0)),
            float(bill.get("duty", 0)), float(bill.get("cess", 0)),
            float(bill.get("other", 0)), float(bill.get("arrears", 0)),
            float(bill.get("rebate", 0)), float(bill.get("adjustment", 0)),
            float(bill.get("gross", 0)), float(bill.get("total", 0)), status,
        )
        try:
            self.conn.execute("""
                INSERT INTO bills (
                    consumer_id, bill_month, bill_date, old_reading, new_reading,
                    units, rate, energy, fixed, duty, cess, other, arrears,
                    rebate, adjustment, gross, total, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(consumer_id, bill_month) DO UPDATE SET
                    bill_date=excluded.bill_date, old_reading=excluded.old_reading,
                    new_reading=excluded.new_reading, units=excluded.units,
                    rate=excluded.rate, energy=excluded.energy, fixed=excluded.fixed,
                    duty=excluded.duty, cess=excluded.cess, other=excluded.other,
                    arrears=excluded.arrears, rebate=excluded.rebate,
                    adjustment=excluded.adjustment, gross=excluded.gross,
                    total=excluded.total, status=excluded.status
            """, values)
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def bill_history(self, cid):
        return self.conn.execute("""
            SELECT * FROM bills WHERE consumer_id=?
            ORDER BY bill_month DESC, id DESC
        """, (cid,)).fetchall()

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(22), spacing=dp(9))
        self.add_widget(root)

        logo_path = find_logo()
        if logo_path and os.path.isfile(logo_path):
            try:
                logo = Image(
                    source=logo_path,
                    size_hint_y=None,
                    height=dp(150),
                    allow_stretch=True,
                    keep_ratio=True,
                )
                root.add_widget(logo)
            except Exception:
                pass

        root.add_widget(make_label("SPOT BILLING APP V8.1", 16, BLUE, True, 30))
        root.add_widget(make_label(COMPANY_NAME, 9, MUTED, True, 35, wrap=True))

        self.username = TextInput(
            hint_text="Employee ID", multiline=False, size_hint_y=None, height=dp(48)
        )
        self.password = TextInput(
            hint_text="Password", password=True, multiline=False, size_hint_y=None, height=dp(48)
        )
        root.add_widget(self.username)
        root.add_widget(self.password)

        login = make_button("LOGIN", GREEN, height=50)
        login.bind(on_press=self.check_login)
        root.add_widget(login)
        root.add_widget(make_label(f"DEMO: {ADMIN_USER} / {ADMIN_PASSWORD}", 10, MUTED, False, 25))

    def check_login(self, *_):
        try:
            if self.username.text.strip() == ADMIN_USER and self.password.text == ADMIN_PASSWORD:
                self.manager.current = "home"
            else:
                show_message("Failed", "Invalid Credentials.")
        except Exception as e:
            show_message("Login Error", f"{e}\n{traceback.format_exc()[-250:]}")


class HomeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(7))
        self.add_widget(root)
        root.add_widget(make_label("PKPDCL DASHBOARD", 20, NAVY, True, 42))
        root.add_widget(make_label("Consumers | Print | Ledger", 11, MUTED, False, 25))

        self.search = TextInput(
            hint_text="Search Name / BP No. / Mobile / Meter",
            multiline=False,
            size_hint_y=None,
            height=dp(46),
            font_size="14sp",
        )
        self.search.bind(text=lambda *_: self.refresh_list())
        root.add_widget(self.search)

        actions = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(92))
        for caption, callback, color in [
            ("+ ADD CONSUMER", self.open_new, GREEN),
            ("EXPORT CONSUMERS", self.export_excel, BLUE),
            ("IMPORT EXCEL", self.import_excel, BLUE),
            ("EXPORT BILL HISTORY", self.export_bills, BLUE),
        ]:
            b = make_button(caption, color)
            b.bind(on_press=lambda _, fn=callback: fn())
            actions.add_widget(b)
        root.add_widget(actions)

        self.count = make_label("Consumers: 0", 12, MUTED, True, 25)
        root.add_widget(self.count)
        scroll = ScrollView()
        self.list_box = BoxLayout(
            orientation="vertical", spacing=dp(8), size_hint_y=None, padding=[0, 0, 0, dp(8)]
        )
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

    def on_enter(self, *_):
        try:
            self.refresh_list()
        except Exception as e:
            show_message("Dashboard Error", f"{e}\n{traceback.format_exc()[-250:]}")

    def _make_card(self):
        card = BoxLayout(
            orientation="vertical", size_hint_y=None, height=dp(116), padding=dp(8), spacing=dp(2)
        )
        with card.canvas.before:
            Color(*CARD_BG)
            rect = Rectangle(pos=card.pos, size=card.size)
        card.bind(
            pos=lambda inst, val: setattr(rect, "pos", val),
            size=lambda inst, val: setattr(rect, "size", val),
        )
        return card

    def refresh_list(self):
        try:
            app = App.get_running_app()
            rows = app.db.all_consumers(self.search.text if hasattr(self, "search") else "")
            self.list_box.clear_widgets()
            self.count.text = f"Consumers Found: {len(rows)}"
            for row in rows:
                card = self._make_card()
                card.add_widget(make_label(row["name"], 14, NAVY, True, 24))
                card.add_widget(make_label(
                    f"BP ID: {row['consumer_no'] or '-'} | Mobile: {row['mobile'] or '-'}",
                    10, DARK, False, 20
                ))
                card.add_widget(make_label(
                    f"Meter: {row['meter_no'] or '-'} | {row['address'] or '-'}",
                    10, MUTED, False, 20
                ))
                buttons = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(5))
                for caption, fn, color in [
                    ("MAKE BILL", lambda cid=row["id"]: self.open_bill(cid), GREEN),
                    ("HISTORY", lambda cid=row["id"]: self.open_history(cid), BLUE),
                    ("EDIT", lambda cid=row["id"]: self.open_edit(cid), (0.45, 0.52, 0.62, 1)),
                ]:
                    b = make_button(caption, color, height=32)
                    b.bind(on_press=lambda _, f=fn: f())
                    buttons.add_widget(b)
                card.add_widget(buttons)
                self.list_box.add_widget(card)
        except Exception as e:
            self.count.text = f"List error: {e}"

    def open_new(self):
        App.get_running_app().consumer_screen.load_consumer(None)
        self.manager.current = "consumer"

    def open_edit(self, cid):
        App.get_running_app().consumer_screen.load_consumer(cid)
        self.manager.current = "consumer"

    def open_bill(self, cid):
        app = App.get_running_app()
        row = app.db.get_consumer(cid)
        if row:
            app.bill_screen.load_consumer(dict(row), cid)
            self.manager.current = "bill"

    def open_history(self, cid):
        row = App.get_running_app().db.get_consumer(cid)
        if not row:
            return
        try:
            history = App.get_running_app().db.bill_history(cid)
            box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
            scroll = ScrollView()
            listing = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
            listing.bind(minimum_height=listing.setter("height"))
            if not history:
                listing.add_widget(make_label("No history.", 13, POPUP_TEXT, False, 40))
            for bill in history:
                listing.add_widget(make_label(
                    f"M: {bill['bill_month'] or '-'} | [{bill['status'] or 'Unpaid'}] | "
                    f"{float(bill['units'] or 0):g}u | {money(bill['total'] or 0)}",
                    13, POPUP_TEXT, False, 36
                ))
            scroll.add_widget(listing)
            box.add_widget(scroll)
            close = make_button("CLOSE", GREEN, height=44)
            box.add_widget(close)
            popup = Popup(title=f"History - {row['name']}", content=box, size_hint=(0.94, 0.72))
            close.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            show_message("Ledger Error", f"Could not load bill history:\n{e}")

    def export_excel(self):
        try:
            from openpyxl import Workbook
            rows = App.get_running_app().db.all_consumers()
            folder = output_folder(App.get_running_app(), "exports")
            path = os.path.join(folder, f"Consumers_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
            wb = Workbook()
            ws = wb.active
            ws.title = "Consumers"
            ws.append(["Name", "Consumer No", "Mobile", "Meter No", "Address"])
            for r in rows:
                ws.append([r["name"], r["consumer_no"], r["mobile"], r["meter_no"], r["address"]])
            wb.save(path)
            show_message("Exported", f"Saved successfully:\n{path}")
        except Exception as e:
            show_message("Error", str(e))

    def export_bills(self):
        try:
            from openpyxl import Workbook
            db = App.get_running_app().db
            rows = db.conn.execute("""
                SELECT c.name, c.consumer_no, b.* FROM bills b
                JOIN consumers c ON c.id=b.consumer_id
                ORDER BY c.name, b.bill_month
            """).fetchall()
            folder = output_folder(App.get_running_app(), "exports")
            path = os.path.join(folder, f"BillLedger_{datetime.now():%Y%m%d_%H%M%S}.xlsx")
            wb = Workbook()
            ws = wb.active
            ws.title = "Bill Ledger"
            ws.append(["Name", "BP No", "Month", "Date", "Units", "Gross", "Net Payable", "Status"])
            for r in rows:
                ws.append([
                    r["name"], r["consumer_no"], r["bill_month"], r["bill_date"],
                    r["units"], r["gross"], r["total"], r["status"]
                ])
            wb.save(path)
            show_message("Exported", f"Saved successfully:\n{path}")
        except Exception as e:
            show_message("Error", str(e))

    def _start_dir(self):
        for candidate in (
            "/storage/emulated/0/Download",
            "/storage/emulated/0",
            App.get_running_app().user_data_dir,
            os.getcwd(),
        ):
            if candidate and os.path.isdir(candidate):
                return candidate
        return os.getcwd()

    def import_excel(self):
        try:
            chooser = FileChooserListView(
                path=self._start_dir(), filters=["*.xlsx", "*.xlsm"]
            )
            layout = BoxLayout(orientation="vertical", spacing=dp(6), padding=dp(8))
            layout.add_widget(chooser)
            buttons = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(6))
            popup = Popup(title="Select Consumer Excel File", content=layout, size_hint=(0.95, 0.85))
            cancel = make_button("CANCEL", (0.55, 0.60, 0.68))
            load = make_button("IMPORT SELECTED", GREEN)
            buttons.add_widget(cancel)
            buttons.add_widget(load)
            layout.add_widget(buttons)
            cancel.bind(on_press=popup.dismiss)

            def do_import(*_):
                if not chooser.selection:
                    show_message("Select File", "Please select an Excel file first.")
                    return
                path = chooser.selection[0]
                try:
                    from openpyxl import load_workbook
                    wb = load_workbook(path, read_only=True, data_only=True)
                    ws = wb.active
                    first_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None) or ()
                    headings = [str(v or "").strip().lower().replace("_", " ") for v in first_row]
                    aliases = {
                        "name": ["name", "consumer name"],
                        "consumer_no": [
                            "consumer no", "consumer number", "bp no",
                            "bp number", "consumer / bp number"
                        ],
                        "mobile": ["mobile", "mobile number", "phone"],
                        "meter_no": ["meter no", "meter number"],
                        "address": ["address", "service address"],
                    }
                    colmap = {}
                    for key, names in aliases.items():
                        for idx, heading in enumerate(headings):
                            if heading in names:
                                colmap[key] = idx
                                break
                    if "name" not in colmap:
                        raise ValueError("Excel first row must contain a Name or Consumer Name heading.")
                    rows = []
                    for values in ws.iter_rows(min_row=2, values_only=True):
                        if not values or all(v is None or str(v).strip() == "" for v in values):
                            continue
                        item = {}
                        for key in aliases:
                            idx = colmap.get(key)
                            item[key] = values[idx] if idx is not None and idx < len(values) else ""
                        rows.append(item)
                    wb.close()
                    added, updated, skipped = App.get_running_app().db.import_consumer_rows(rows)
                    popup.dismiss()
                    self.refresh_list()
                    show_message(
                        "Import Complete",
                        f"Added: {added}\nUpdated: {updated}\nSkipped: {skipped}"
                    )
                except Exception as e:
                    show_message("Import Error", str(e))

            load.bind(on_press=do_import)
            popup.open()
        except Exception as e:
            show_message("Import Error", str(e))


class ConsumerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.consumer_id = None
        root = BoxLayout(orientation="vertical", padding=dp(13), spacing=dp(8))
        self.add_widget(root)
        root.add_widget(make_label("CONSUMER REGISTRATION", 19, NAVY, True, 42))
        self.fields = {}
        for key, hint in [
            ("name", "Consumer Name *"),
            ("consumer_no", "Consumer / BP Number"),
            ("mobile", "Mobile Number"),
            ("meter_no", "Meter Number"),
            ("address", "Service Address"),
        ]:
            field = TextInput(
                hint_text=hint,
                multiline=(key == "address"),
                size_hint_y=None,
                height=dp(78 if key == "address" else 47),
                font_size="14sp",
                padding=dp(9),
            )
            self.fields[key] = field
            root.add_widget(field)
        save = make_button("SAVE CONSUMER", GREEN, height=50)
        save.bind(on_press=self.save)
        root.add_widget(save)
        back = make_button("BACK", (0.55, 0.60, 0.68))
        back.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(back)
        self.status = make_label("", 11, MUTED, False, 30)
        root.add_widget(self.status)

    def load_consumer(self, cid):
        self.consumer_id = cid
        row = App.get_running_app().db.get_consumer(cid) if cid else None
        for key, field in self.fields.items():
            field.text = (row[key] or "") if row else ""
        self.status.text = "Editing record." if row else "New consumer."

    def save(self, *_):
        try:
            data = {k: v.text for k, v in self.fields.items()}
            App.get_running_app().db.save_consumer(data, self.consumer_id)
            self.manager.current = "home"
        except Exception as e:
            self.status.text = str(e)


class BillScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.consumer = None
        self.consumer_id = None
        self.current_bill = None
        self.saved_pdf_path = None
        root = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(6))
        self.add_widget(root)
        top = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(5))
        back = make_button("< BACK", (0.82, 0.87, 0.93, 1), NAVY, 40)
        back.size_hint_x = 0.28
        back.bind(on_press=lambda *_: setattr(self.manager, "current", "home"))
        top.add_widget(back)
        top.add_widget(make_label("SPOT CALCULATOR", 17, NAVY, True, 42))
        root.add_widget(top)
        self.consumer_label = make_label("Consumer: -", 12, BLUE, True, 30)
        root.add_widget(self.consumer_label)

        scroll = ScrollView()
        form = BoxLayout(
            orientation="vertical", spacing=dp(5), size_hint_y=None, padding=[0, 0, 0, dp(8)]
        )
        form.bind(minimum_height=form.setter("height"))
        scroll.add_widget(form)
        root.add_widget(scroll)

        self.fields = {}
        month = datetime.now().strftime("%Y-%m")
        entries = [
            ("month", "Bill Cycle (YYYY-MM)", month),
            ("old", "Previous Reading", "0"),
            ("new", "Current Reading", ""),
            ("fixed", "Fixed Charge (Rs.)", "0"),
            ("duty", "Elec. Duty (Rs.)", "0"),
            ("cess", "Cess (Rs.)", "0"),
            ("other", "Other (Rs.)", "0"),
            ("arrears", "Arrears (Rs.)", "0"),
            ("rebate", "Rebate (Rs.)", "0"),
            ("adjustment", "Adj (+/- Rs.)", "0"),
        ]
        for key, hint, default in entries:
            form.add_widget(make_label(hint, 11, MUTED, True, 20))
            field = TextInput(
                text=default,
                hint_text=hint,
                multiline=False,
                input_filter=None,
                size_hint_y=None,
                height=dp(41),
                font_size="14sp",
                padding=dp(8),
            )
            self.fields[key] = field
            form.add_widget(field)

        calc = make_button("COMPUTE", GREEN, height=47)
        calc.bind(on_press=self.calculate)
        form.add_widget(calc)
        self.result = make_label("NET PAYABLE: Rs. 0.00", 18, GREEN, True, 38)
        form.add_widget(self.result)
        self.breakdown = make_label("", 11, DARK, False, 100, wrap=True)
        self.breakdown.valign = "top"
        form.add_widget(self.breakdown)

        actions = GridLayout(cols=2, size_hint_y=None, height=dp(136), spacing=dp(6))
        for caption, fn, color in [
            ("SAVE BILL LEDGER", self.save_history, GREEN),
            ("GENERATE PDF", self.save_pdf, BLUE),
            ("PREVIEW PDF", self.preview_pdf, BLUE),
            ("PRINT BILL", self.print_pdf, GREEN),
            ("WHATSAPP TEXT", self.share_whatsapp, (0.07, 0.65, 0.25, 1)),
            ("VIEW LEDGER", self.view_history, (0.45, 0.52, 0.62, 1)),
        ]:
            b = make_button(caption, color, height=40)
            b.bind(on_press=lambda _, f=fn: f())
            actions.add_widget(b)
        form.add_widget(actions)
        self.status = make_label("", 10, MUTED, False, 30)
        form.add_widget(self.status)

    def load_consumer(self, consumer, cid):
        self.consumer = consumer
        self.consumer_id = cid
        self.current_bill = None
        self.saved_pdf_path = None
        self.consumer_label.text = f"Consumer: {consumer['name']} | BP ID: {consumer['consumer_no'] or '-'}"
        month = datetime.now().strftime("%Y-%m")
        previous = App.get_running_app().db.previous_reading(cid, before_month=month)
        self.fields["old"].text = f"{previous:g}"
        self.fields["new"].text = ""
        self.fields["month"].text = month
        for key in self.fields:
            if key not in ("old", "new", "month"):
                self.fields[key].text = "0"
        self.result.text = "NET PAYABLE: Rs. 0.00"
        self.breakdown.text = ""
        self.status.text = f"Previous reading: {previous:g}"

    def num(self, key, negative=False, allow_blank=True):
        raw = self.fields[key].text.strip()
        if raw == "":
            if not allow_blank:
                label_map = {
                    "old": "Previous Reading",
                    "new": "Current Reading",
                }
                raise ValueError(f"Enter {label_map.get(key, key)}.")
            return 0.0
        try:
            value = float(raw)
        except Exception:
            raise ValueError(f"Enter a valid number for {key}.")
        if not negative and value < 0:
            raise ValueError(f"{key} cannot be negative.")
        return value

    def calculate(self, *_):
        try:
            if not self.consumer:
                raise ValueError("Select a consumer first.")
            month = self.fields["month"].text.strip()
            if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
                raise ValueError("Bill cycle must be YYYY-MM.")
            old = self.num("old", allow_blank=False)
            new = self.num("new", allow_blank=False)
            if new < old:
                raise ValueError("Current reading cannot be less than previous reading.")
            units = new - old
            energy, rate = energy_charge(units)
            vals = {
                k: self.num(k, k == "adjustment", allow_blank=True)
                for k in ["fixed", "duty", "cess", "other", "arrears", "rebate", "adjustment"]
            }
            gross = round(energy + sum(v for k, v in vals.items() if k != "rebate"), 2)
            total = round(gross - vals["rebate"], 2)
            if total < 0:
                raise ValueError("Net payable cannot be negative. Check rebate and charges.")
            self.current_bill = {
                "name": self.consumer["name"],
                "consumer": self.consumer["consumer_no"] or "-",
                "mobile": self.consumer["mobile"] or "-",
                "meter": self.consumer["meter_no"] or "-",
                "address": self.consumer["address"] or "-",
                "date": datetime.now().strftime("%d-%m-%Y"),
                "month": month,
                "old": old,
                "new": new,
                "units": units,
                "rate": rate,
                "energy": energy,
                **vals,
                "gross": gross,
                "total": total,
                "status": "Unpaid",
            }
            self.saved_pdf_path = None
            self.result.text = f"NET PAYABLE: {money(total)}"
            self.breakdown.text = (
                f"Cycle: {month} | Units: {units:g} | Rate: Rs.{rate:.2f}/u\n"
                f"Energy: {money(energy)} | Gross: {money(gross)}"
            )
            self.status.text = "Calculated."
        except Exception as e:
            self.status.text = f"Error: {e}"

    def save_history(self, *_):
        if not self.current_bill:
            self.status.text = "Calculate bill first."
            return
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        content.add_widget(make_label("Select Payment Status:", 14, POPUP_TEXT, True, 32))
        btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(45))
        popup = Popup(title="Save Bill", content=content, size_hint=(0.88, 0.38))

        def save_status(st):
            try:
                db = App.get_running_app().db
                db.save_bill(
                    self.consumer_id, self.current_bill["month"], self.current_bill, status=st
                )
                self.current_bill["status"] = st
                self.saved_pdf_path = None
                self.status.text = f"Bill saved. Payment status: {st}"
                popup.dismiss()
                show_message("Success", f"Bill saved/updated as {st}.")
            except Exception as e:
                popup.dismiss()
                show_message("Save Error", str(e))

        btn_p = make_button("PAID", GREEN)
        btn_p.bind(on_press=lambda *_: save_status("Paid"))
        btn_u = make_button("UNPAID", (0.8, 0.2, 0.2, 1))
        btn_u.bind(on_press=lambda *_: save_status("Unpaid"))
        btn_layout.add_widget(btn_p)
        btn_layout.add_widget(btn_u)
        content.add_widget(btn_layout)
        popup.open()

    def view_history(self, *_):
        if not self.consumer_id:
            show_message("Ledger", "Please select a consumer first.")
            return
        try:
            rows = App.get_running_app().db.bill_history(self.consumer_id)
            box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
            scroll = ScrollView()
            listing = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
            listing.bind(minimum_height=listing.setter("height"))
            if not rows:
                listing.add_widget(make_label("No history.", 13, POPUP_TEXT, False, 40))
            for r in rows:
                month = r["bill_month"] or "-"
                status = r["status"] or "Unpaid"
                units = float(r["units"] or 0)
                total = float(r["total"] or 0)
                listing.add_widget(make_label(
                    f"{month} | {status} | {units:g}u | {money(total)}",
                    13, POPUP_TEXT, False, 36
                ))
            scroll.add_widget(listing)
            box.add_widget(scroll)
            close = make_button("CLOSE", GREEN, height=44)
            box.add_widget(close)
            popup = Popup(title="Ledger History", content=box, size_hint=(0.94, 0.72))
            close.bind(on_press=popup.dismiss)
            popup.open()
        except Exception as e:
            show_message("Ledger Error", f"Could not load bill history:\n{e}")

    def save_pdf(self, *_):
        bill = self.current_bill
        if not bill:
            self.status.text = "Calculate bill first."
            return None
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib import colors
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as PDFImage
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.enums import TA_CENTER
            from reportlab.lib.units import mm

            folder = output_folder(App.get_running_app(), "bills")
            safe_no = re.sub(r"[^A-Za-z0-9_-]", "", bill["consumer"]) or "consumer"
            safe_month = re.sub(r"[^0-9-]", "", bill["month"])
            path = os.path.join(folder, f"Bill_{safe_no}_{safe_month}.pdf")
            due = payment_due_date(bill["date"])
            styles = getSampleStyleSheet()

            center_bold = ParagraphStyle(
                "CenterBold", parent=styles["Normal"], fontSize=10, leading=12,
                alignment=TA_CENTER, fontName="Helvetica-Bold"
            )
            header_style = ParagraphStyle(
                "Header", parent=styles["Normal"], fontSize=15, leading=17,
                alignment=TA_CENTER, textColor=colors.HexColor("#0B2447"),
                fontName="Helvetica-Bold", spaceAfter=8
            )
            sub_style = ParagraphStyle(
                "Sub", parent=styles["Normal"], fontSize=9, leading=11,
                alignment=TA_CENTER, textColor=colors.HexColor("#6B7280"), spaceAfter=12
            )
            section_style = ParagraphStyle(
                "Section", parent=styles["Heading2"], fontSize=11,
                textColor=colors.HexColor("#0B2447"), spaceBefore=8,
                spaceAfter=4, fontName="Helvetica-Bold"
            )
            normal_small = ParagraphStyle(
                "Small", parent=styles["Normal"], fontSize=8, leading=10
            )

            def p(value):
                return Paragraph(html.escape(str(value)), normal_small)

            story = []
            logo_path = find_logo()
            if logo_path and os.path.isfile(logo_path):
                try:
                    logo = PDFImage(logo_path, width=35 * mm, height=35 * mm, kind="proportional")
                    logo.hAlign = "CENTER"
                    story.extend([logo, Spacer(1, 4)])
                except Exception:
                    pass

            story.append(Paragraph(html.escape(COMPANY_NAME), header_style))
            story.append(Paragraph("ELECTRICITY BILL", sub_style))

            info_data = [
                [Paragraph("<b>Consumer Name</b>", normal_small), p(bill["name"]),
                 Paragraph("<b>BP Number</b>", normal_small), p(bill["consumer"])],
                [Paragraph("<b>Mobile</b>", normal_small), p(bill["mobile"]),
                 Paragraph("<b>Meter Number</b>", normal_small), p(bill["meter"])],
                [Paragraph("<b>Address</b>", normal_small), p(bill["address"]),
                 Paragraph("<b>Bill Cycle</b>", normal_small), p(bill["month"])],
                [Paragraph("<b>Bill Date</b>", normal_small), p(bill["date"]),
                 Paragraph("<b>Due Date</b>", normal_small), p(due)],
                [Paragraph("<b>Payment Status</b>", normal_small), p(bill.get("status", "Unpaid")),
                 Paragraph("<b>UPI ID</b>", normal_small), p(UPI_ID)],
                [Paragraph("<b>Prev Reading</b>", normal_small), p(f"{bill['old']:g}"),
                 Paragraph("<b>Curr Reading</b>", normal_small), p(f"{bill['new']:g}")],
                [Paragraph("<b>Units</b>", normal_small), p(f"{bill['units']:g}"),
                 Paragraph("<b>Rate</b>", normal_small), p(f"Rs. {bill['rate']:.2f}/unit")],
            ]
            info_table = Table(info_data, colWidths=[30 * mm, 60 * mm, 30 * mm, 55 * mm])
            info_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F3F4F6")),
                ("BACKGROUND", (2, 0), (2, -1), colors.HexColor("#F3F4F6")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(Paragraph("CONSUMER DETAILS", section_style))
            story.append(info_table)

            calc_data = [
                [Paragraph("<b>Charge Description</b>", center_bold),
                 Paragraph("<b>Amount (Rs.)</b>", center_bold)],
                ["Energy Charge", f"{bill['energy']:,.2f}"],
                ["Fixed Charge", f"{bill['fixed']:,.2f}"],
                ["Electricity Duty", f"{bill['duty']:,.2f}"],
                ["Cess", f"{bill['cess']:,.2f}"],
                ["Other Charges", f"{bill['other']:,.2f}"],
                ["Arrears", f"{bill['arrears']:,.2f}"],
                ["Adjustment", f"{bill['adjustment']:,.2f}"],
                [Paragraph("<b>Gross Amount</b>", center_bold), f"{bill['gross']:,.2f}"],
                ["Less: Rebate", f"-{bill['rebate']:,.2f}"],
                [Paragraph("<b>NET PAYABLE</b>", center_bold),
                 Paragraph(f"<b>{money(bill['total'])}</b>", center_bold)],
            ]
            calc_table = Table(calc_data, colWidths=[130 * mm, 45 * mm])
            calc_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, -1), (1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, 0), (1, 0), colors.HexColor("#E5E7EB")),
                ("BACKGROUND", (0, -1), (1, -1), colors.HexColor("#D1FAE5")),
                ("PADDING", (0, 0), (-1, -1), 4),
            ]))
            story.extend([Spacer(1, 8), Paragraph("BILL CALCULATION", section_style), calc_table])
            story.extend([Spacer(1, 8), Paragraph("SCAN TO PAY", section_style)])

            qr_path = os.path.join(folder, f"QR_{safe_no}_{safe_month}.png")
            qr_img = create_upi_qr(bill["total"], bill["consumer"], bill["month"], qr_path)
            if qr_img and os.path.isfile(qr_img):
                qr = PDFImage(qr_img, width=28 * mm, height=28 * mm, kind="proportional")
                qr.hAlign = "CENTER"
                story.append(qr)
                story.append(Paragraph(f"UPI ID: {html.escape(UPI_ID)}", center_bold))
                story.append(Paragraph(
                    "Scan with any UPI app and verify the payee and amount before paying.",
                    normal_small
                ))

            story.extend([Spacer(1, 10), Paragraph("This is a computer generated bill.", sub_style)])
            doc = SimpleDocTemplate(
                path, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm,
                topMargin=15 * mm, bottomMargin=15 * mm
            )
            doc.build(story)

            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                raise IOError("PDF was not created correctly.")
            self.saved_pdf_path = path
            self.status.text = f"PDF saved: {path}"
            show_message("PDF Generated", f"Saved successfully:\n{path}")
            return path
        except Exception as e:
            self.saved_pdf_path = None
            show_message("PDF Error", f"Failed to generate PDF:\n{e}")
            return None

    def print_pdf(self, *_):
        if not self.current_bill:
            show_message("Print Bill", "Calculate the bill first.")
            return
        if not self.saved_pdf_path or not os.path.isfile(self.saved_pdf_path):
            path = self.save_pdf()
            if not path:
                return
        try:
            open_pdf_external(self.saved_pdf_path)
            self.status.text = "PDF opened. Select Print in your PDF viewer."
            show_message(
                "Print Bill",
                "Bill PDF opened. In the PDF viewer, tap the menu or printer icon and choose Print."
            )
        except Exception as e:
            show_message("Print Error", f"Could not open bill for printing:\n{e}")

    def preview_pdf(self, *_):
        if not self.saved_pdf_path or not os.path.isfile(self.saved_pdf_path):
            path = self.save_pdf()
            if not path:
                return
        try:
            open_pdf_external(self.saved_pdf_path)
        except Exception as e:
            show_message("Preview Error", f"Could not open PDF viewer:\n{e}")

    def share_whatsapp(self, *_):
        if not self.current_bill:
            show_message("Info", "Calculate bill first.")
            return
        b = self.current_bill
        msg = (
            f"*{COMPANY_NAME}*\n"
            f"Electricity Bill Summary\n"
            f"-------------------------\n"
            f"Consumer No: {b['consumer']}\n"
            f"Name: {b['name']}\n"
            f"Billing Month: {format_billing_month(b['month'])}\n"
            f"Bill Date: {b['date']}\n"
            f"Due Date: {payment_due_date(b['date'])}\n"
            f"Prev Reading: {b['old']:.2f}\n"
            f"Curr Reading: {b['new']:.2f}\n"
            f"Units Consumed: {b['units']:.2f} kWh\n"
            f"Slab Rate: Rs. {b['rate']:.2f}/unit\n"
            f"Energy Charge: {money(b['energy'])}\n"
            f"Fixed Charge: {money(b['fixed'])}\n"
            f"*Total Payable: {money(b['total'])}*\n"
            f"UPI ID: {UPI_ID}\n"
            f"-------------------------\n"
            f"Generated via PKPDCL Bill Calculator v8.1"
        ).strip()

        if not msg:
            show_message("Info", "Bill summary text is empty.")
            return

        try:
            Clipboard.copy(msg)
        except Exception:
            pass

        if platform == "android":
            try:
                android_text_intent(msg, whatsapp_only=False)
                self.status.text = "Bill text copied & share menu opened."
            except Exception as e:
                self.status.text = f"Share menu error: {e}"
                show_message(
                    "WhatsApp Text Copied",
                    "Bill summary text clipboard mein copy ho gaya hai.\n"
                    "WhatsApp khol kar directly paste kar sakte hain.\n\n"
                    f"Detail: {e}"
                )
        else:
            self.status.text = "Bill text copied to clipboard."
            show_message("WhatsApp Text", msg)


class CGBijliBillApp(App):
    def build(self):
        Window.clearcolor = BG
        db_path = os.path.join(self.user_data_dir, "pkpdcl_spot.db")
        self.db = Database(db_path)
        manager = ScreenManager()
        manager.add_widget(LoginScreen(name="login"))
        manager.add_widget(HomeScreen(name="home"))
        self.consumer_screen = ConsumerScreen(name="consumer")
        manager.add_widget(self.consumer_screen)
        self.bill_screen = BillScreen(name="bill")
        manager.add_widget(self.bill_screen)
        manager.current = "login"
        return manager

    def on_error(self, exception_type, exception_value, tb):
        details = "".join(traceback.format_exception(exception_type, exception_value, tb))[-400:]
        show_message("App Error Caught", details)
        return True

    def on_stop(self):
        if hasattr(self, "db"):
            self.db.close()


def _global_excepthook(exctype, value, tb):
    try:
        details = "".join(traceback.format_exception(exctype, value, tb))[-400:]
        show_message("Unexpected Error", details)
    except Exception:
        pass


if __name__ == "__main__":
    sys.excepthook = _global_excepthook
    CGBijliBillApp().run()
def _fpdf_save_pdf(self, *_):
    bill = self.current_bill
    if not bill:
        self.status.text = "Calculate bill first."
        return None
    try:
        from pdf_helper import create_pkpdcl_pdf

        folder = output_folder(App.get_running_app(), "bills")
        safe_no = re.sub(r"[^A-Za-z0-9_-]", "", bill["consumer"]) or "consumer"
        safe_month = re.sub(r"[^0-9-]", "", bill["month"])
        path = os.path.join(folder, f"Bill_{safe_no}_{safe_month}.pdf")
        due = payment_due_date(bill["date"])

        qr_path = os.path.join(folder, f"QR_{safe_no}_{safe_month}.png")
        qr_img = create_upi_qr(bill["total"], bill["consumer"], bill["month"], qr_path)

        pdf_data = {
            "Company": COMPANY_NAME,
            "Consumer Name": bill["name"],
            "BP Number": bill["consumer"],
            "Mobile": bill["mobile"],
            "Meter Number": bill["meter"],
            "Address": bill["address"],
            "Bill Cycle": bill["month"],
            "Bill Date": bill["date"],
            "Due Date": due,
            "Status": bill.get("status", "Unpaid"),
            "Prev Reading": f"{bill['old']:g}",
            "Curr Reading": f"{bill['new']:g}",
            "Units": f"{bill['units']:g}",
            "Rate": f"Rs. {bill['rate']:.2f}/unit",
            "Energy Charge": money(bill["energy"]),
            "Fixed Charge": money(bill["fixed"]),
            "Duty": money(bill["duty"]),
            "Cess": money(bill["cess"]),
            "Other": money(bill["other"]),
            "Arrears": money(bill["arrears"]),
            "Adjustment": money(bill["adjustment"]),
            "Gross": money(bill["gross"]),
            "Rebate": money(bill["rebate"]),
            "NET PAYABLE": money(bill["total"]),
            "UPI ID": UPI_ID,
        }

        create_pkpdcl_pdf(
            pdf_data,
            output_path=path,
            logo_path=find_logo(),
            qr_path=qr_img if (qr_img and os.path.isfile(qr_img)) else None,
        )

        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            raise IOError("PDF was not created correctly.")
        self.saved_pdf_path = path
        self.status.text = f"PDF saved: {path}"
        show_message("PDF Generated", f"Saved successfully:\n{path}")
        return path
    except Exception as e:
        self.saved_pdf_path = None
        show_message("PDF Error", f"Failed to generate PDF:\n{e}")
        return None


BillScreen.save_pdf = _fpdf_save_pdf
