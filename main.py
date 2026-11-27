import datetime
import json
import os

from kivy.app import App
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex

try:
    from pdf_helper import create_pkpdcl_pdf
    HAS_PDF_HELPER = True
except ImportError:
    HAS_PDF_HELPER = False

try:
    import qrcode
    HAS_QR = True
except ImportError:
    HAS_QR = False

try:
    import openpyxl
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False

try:
    from jnius import autoclass
    HAS_JNIUS = True
except ImportError:
    HAS_JNIUS = False


def get_base_dir(app_instance):
    candidates = [
        "/storage/emulated/0/Download/PKPDCL",
        "/sdcard/Download/PKPDCL",
        os.path.join(app_instance.user_data_dir, "PKPDCL"),
        "PKPDCL_data",
    ]
    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            if os.access(path, os.W_OK):
                return path
        except Exception:
            continue
    return "."


def find_logo():
    candidates = []

    try:
        app = App.get_running_app()
        if app and getattr(app, "user_data_dir", None):
            candidates.append(os.path.join(app.user_data_dir, "pkpdcl_logo.png"))
            candidates.append(os.path.join(app.user_data_dir, "PKPDCL", "assets", "pkpdcl_logo.png"))
    except Exception:
        pass

    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if base_dir:
            candidates.append(os.path.join(base_dir, "pkpdcl_logo.png"))
            candidates.append(os.path.join(base_dir, "assets", "pkpdcl_logo.png"))
    except Exception:
        pass

    try:
        cwd = os.getcwd()
        if cwd:
            candidates.append(os.path.join(cwd, "pkpdcl_logo.png"))
            candidates.append(os.path.join(cwd, "assets", "pkpdcl_logo.png"))
    except Exception:
        pass

    candidates.extend([
        "/storage/emulated/0/Download/PKPDCL/pkpdcl_logo.png",
        "/storage/emulated/0/Download/PKPDCL/assets/pkpdcl_logo.png",
        "/storage/emulated/0/Download/pkpdcl_logo.png",
        "/storage/emulated/0/Pictures/PKPDCL/pkpdcl_logo.png",
        "/storage/emulated/0/Pictures/pkpdcl_logo.png",
        "/storage/emulated/0/DCIM/PKPDCL/pkpdcl_logo.png",
    ])

    checked = set()
    for path in candidates:
        if not path or path in checked:
            continue
        checked.add(path)
        try:
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                return path
        except Exception:
            continue

    return None


def build_pkpdcl_logo(target_path):
    try:
        existing = find_logo()
        if existing and os.path.exists(existing):
            return existing
    except Exception:
        pass

    try:
        if HAS_QR:
            img = qrcode.make("PKPDCL|PRAMOD KASHYAP POWER DISTRIBUTION CORPORATION LIMITED")
            img.save(target_path)
            if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                return target_path
    except Exception:
        pass

    return target_path if os.path.exists(target_path) else None


class CardBox(BoxLayout):
    def __init__(self, bg_hex="#FFFFFF", **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            self.c = Color(*get_color_from_hex(bg_hex))
            self.r = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_rect, size=self._sync_rect)

    def _sync_rect(self, *args):
        self.r.pos = self.pos
        self.r.size = self.size


class PKPDCLStore:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.bills_dir = os.path.join(base_dir, "bills")
        self.exports_dir = os.path.join(base_dir, "exports")
        self.assets_dir = os.path.join(base_dir, "assets")
        os.makedirs(self.bills_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)
        self.data_file = os.path.join(base_dir, "pkpdcl_data.json")
        default_logo_target = os.path.join(self.assets_dir, "pkpdcl_logo.png")
        self.logo_path = build_pkpdcl_logo(default_logo_target)
        self.data = self._load()

    def _default_data(self):
        return {
            "consumers": [
                {
                    "name": "Akshita Kashyap",
                    "bp_id": "1001283465",
                    "mobile": "9174042040",
                    "meter": "3023456",
                    "address": "Bilaspur CG",
                    "rate": 8.30,
                    "upi": "9009203060@ptsbi",
                },
                {
                    "name": "Arun Kashyap",
                    "bp_id": "1001286489",
                    "mobile": "930032625",
                    "meter": "3014576",
                    "address": "Ratanpur CG",
                    "rate": 8.30,
                    "upi": "9009203060@ptsbi",
                },
                {
                    "name": "Chitrarekha Kashyap",
                    "bp_id": "1001284356",
                    "mobile": "8982833685",
                    "meter": "3014562",
                    "address": "Ratanpur",
                    "rate": 8.30,
                    "upi": "9009203060@ptsbi",
                },
                {
                    "name": "Deepanjalee Kashyap",
                    "bp_id": "1001893432",
                    "mobile": "8817899800",
                    "meter": "3000331",
                    "address": "Sarkanda",
                    "rate": 8.30,
                    "upi": "9009203060@ptsbi",
                },
            ],
            "ledger": [
                {
                    "bp_id": "1001283465",
                    "cycle": "2026-11",
                    "status": "Paid",
                    "units": 1689,
                    "net_payable": 14018.70,
                    "prev_reading": 7233,
                    "curr_reading": 8922,
                    "rate": 8.30,
                    "energy": 14018.70,
                    "fixed": 0.0,
                    "duty": 0.0,
                    "cess": 0.0,
                    "other": 0.0,
                    "arrears": 0.0,
                    "rebate": 0.0,
                    "adj": 0.0,
                    "gross": 14018.70,
                    "bill_date": "27-11-2026",
                    "due_date": "07-12-2026",
                }
            ],
        }

    def _load(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                if "consumers" in loaded and "ledger" in loaded:
                    return loaded
            except Exception:
                pass
        d = self._default_data()
        self.save(d)
        return d

    def save(self, payload=None):
        target = payload if payload is not None else self.data
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(target, f, indent=2, ensure_ascii=False)

    def upsert_consumer(self, consumer, old_bp_id=None):
        consumers = self.data.setdefault("consumers", [])
        target_bp = str(old_bp_id or consumer.get("bp_id") or "").strip()
        new_bp = str(consumer.get("bp_id") or "").strip()

        clean_consumer = {
            "name": str(consumer.get("name") or "").strip(),
            "bp_id": new_bp,
            "mobile": str(consumer.get("mobile") or "").strip(),
            "meter": str(consumer.get("meter") or "").strip(),
            "address": str(consumer.get("address") or "").strip(),
            "rate": float(consumer.get("rate") or 8.30),
            "upi": str(consumer.get("upi") or "9009203060@ptsbi").strip(),
        }

        updated = False
        for idx, item in enumerate(consumers):
            item_bp = str(item.get("bp_id") or "").strip()
            if target_bp and item_bp == target_bp:
                consumers[idx] = clean_consumer
                updated = True
                break

        if not updated:
            consumers.append(clean_consumer)

        if old_bp_id and new_bp and str(old_bp_id).strip() != new_bp:
            for row in self.data.get("ledger", []):
                if str(row.get("bp_id") or "").strip() == str(old_bp_id).strip():
                    row["bp_id"] = new_bp

        self.save()
        return clean_consumer

    def generate_qr(self, bill_dict):
        if not HAS_QR:
            return None
        upi_id = str(bill_dict.get("UPI ID") or "9009203060@ptsbi").strip()
        name = str(bill_dict.get("Consumer Name") or "PKPDCL").strip()
        amt = str(bill_dict.get("Net Payable Raw") or "0.00").strip()
        bp = str(bill_dict.get("BP Number") or "").strip()
        upi_uri = f"upi://pay?pa={upi_id}&pn={name}&am={amt}&cu=INR&tn=Bill-{bp}"
        qr_file = os.path.join(self.bills_dir, f"qr_{bp or 'bill'}.png")
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=4,
        )
        qr.add_data(upi_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_file)
        return qr_file if os.path.isfile(qr_file) else None

    def generate_bill_pdf(self, bill_dict):
        if not HAS_PDF_HELPER:
            return None, "pdf_helper.py not available"
        bp = str(bill_dict.get("BP Number") or "bill").strip()
        cycle = str(bill_dict.get("Bill Cycle") or datetime.date.today().strftime("%Y-%m")).strip()
        pdf_path = os.path.join(self.bills_dir, f"PKPDCL_{bp}_{cycle}.pdf")
        qr_path = self.generate_qr(bill_dict)
        logo = find_logo() or self.logo_path
        out = create_pkpdcl_pdf(
            bill_dict,
            output_path=pdf_path,
            logo_path=logo,
            qr_path=qr_path,
        )
        return out, "PDF generated successfully"


def show_popup(title, message):
    box = CardBox(bg_hex="#FFFFFF", orientation="vertical", padding=16, spacing=10)
    box.add_widget(
        Label(
            text=str(title),
            bold=True,
            color=get_color_from_hex("#122B52"),
            size_hint_y=None,
            height=30,
        )
    )
    box.add_widget(
        Label(
            text=str(message),
            color=get_color_from_hex("#142136"),
            text_size=(Window.width * 0.75, None),
            size_hint_y=None,
            height=90,
        )
    )
    btn = Button(text="OK", size_hint_y=None, height=44, background_color=get_color_from_hex("#122B52"))
    modal = ModalView(size_hint=(0.85, 0.45), auto_dismiss=False)
    btn.bind(on_release=modal.dismiss)
    box.add_widget(btn)
    modal.add_widget(box)
    modal.open()


class HomeScreen(Screen):
    def __init__(self, store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        root = BoxLayout(orientation="vertical", padding=12, spacing=10)

        header = CardBox(bg_hex="#122B52", orientation="horizontal", padding=10, spacing=10, size_hint_y=None, height=76)
        logo_file = find_logo() or store.logo_path
        if logo_file and os.path.isfile(logo_file):
            header.add_widget(Image(source=logo_file, size_hint_x=None, width=56))
        header.add_widget(
            Label(
                text="PKPDCL BILL CALCULATOR",
                bold=True,
                color=(1, 1, 1, 1),
                halign="left",
                valign="middle",
            )
        )
        root.add_widget(header)

        self.status_lbl = Label(
            text=f"Consumers: {len(store.data.get('consumers', []))} | Dir: {store.base_dir}",
            color=get_color_from_hex("#142136"),
            size_hint_y=None,
            height=36,
        )
        root.add_widget(self.status_lbl)

        btn_grid = GridLayout(cols=2, spacing=10, size_hint_y=None, height=120)
        btn_calc = Button(text="New Bill & PDF", background_color=get_color_from_hex("#1E4E8C"))
        btn_calc.bind(on_release=lambda *_: setattr(self.manager, "current", "bill"))
        btn_test_pdf = Button(text="Test Sample PDF", background_color=get_color_from_hex("#1B6B4A"))
        btn_test_pdf.bind(on_release=self.test_sample_pdf)
        btn_grid.add_widget(btn_calc)
        btn_grid.add_widget(btn_test_pdf)
        root.add_widget(btn_grid)

        self.list_box = BoxLayout(orientation="vertical", spacing=6, size_hint_y=None)
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView()
        scroll.add_widget(self.list_box)
        root.add_widget(scroll)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.refresh_list()

    def refresh_list(self):
        self.list_box.clear_widgets()
        consumers = self.store.data.get("consumers", [])
        self.status_lbl.text = f"Consumers: {len(consumers)} | PDF Helper: {'OK' if HAS_PDF_HELPER else 'Missing'}"
        for c in consumers:
            row = CardBox(bg_hex="#F4F7FB", orientation="horizontal", padding=8, size_hint_y=None, height=52)
            row.add_widget(
                Label(
                    text=f"{c.get('name')} (BP: {c.get('bp_id')})",
                    color=get_color_from_hex("#142136"),
                    halign="left",
                )
            )
            self.list_box.add_widget(row)

    def test_sample_pdf(self, *args):
        consumers = self.store.data.get("consumers", [])
        c = consumers[0] if consumers else {
            "name": "Sample Consumer",
            "bp_id": "1001283465",
            "mobile": "9174042040",
            "meter": "3023456",
            "address": "Bilaspur CG",
            "rate": 8.30,
            "upi": "9009203060@ptsbi",
        }
        units = 100
        rate = float(c.get("rate") or 8.30)
        amount = round(units * rate, 2)
        bill_data = {
            "Consumer Name": c.get("name"),
            "BP Number": c.get("bp_id"),
            "Mobile": c.get("mobile"),
            "Meter Number": c.get("meter"),
            "Address": c.get("address"),
            "Bill Cycle": datetime.date.today().strftime("%Y-%m"),
            "Bill Date": datetime.date.today().strftime("%d-%m-%Y"),
            "Due Date": (datetime.date.today() + datetime.timedelta(days=10)).strftime("%d-%m-%Y"),
            "Status": "Unpaid",
            "UPI ID": c.get("upi", "9009203060@ptsbi"),
            "Prev Reading": "1000",
            "Curr Reading": "1100",
            "Units": str(units),
            "Rate": f"{rate:.2f}",
            "Energy Charge": f"Rs. {amount:.2f}",
            "Gross Amount": f"Rs. {amount:.2f}",
            "NET PAYABLE": f"Rs. {amount:.2f}",
            "Net Payable Raw": f"{amount:.2f}",
        }
        path, msg = self.store.generate_bill_pdf(bill_data)
        if path:
            Clipboard.copy(path)
        show_popup("PDF Result", f"{msg}\n{path or ''}")


class BillScreen(Screen):
    def __init__(self, store, **kwargs):
        super().__init__(**kwargs)
        self.store = store
        root = BoxLayout(orientation="vertical", padding=12, spacing=8)
        root.add_widget(
            Label(
                text="QUICK BILL & PDF GENERATOR",
                bold=True,
                color=get_color_from_hex("#122B52"),
                size_hint_y=None,
                height=36,
            )
        )
        self.name_in = TextInput(hint_text="Consumer Name", text="Akshita Kashyap", size_hint_y=None, height=44)
        self.bp_in = TextInput(hint_text="BP Number", text="1001283465", size_hint_y=None, height=44)
        self.units_in = TextInput(hint_text="Units", text="120", input_filter="float", size_hint_y=None, height=44)
        self.rate_in = TextInput(hint_text="Rate", text="8.30", input_filter="float", size_hint_y=None, height=44)
        root.add_widget(self.name_in)
        root.add_widget(self.bp_in)
        root.add_widget(self.units_in)
        root.add_widget(self.rate_in)

        btn_gen = Button(text="Generate PDF", size_hint_y=None, height=48, background_color=get_color_from_hex("#122B52"))
        btn_gen.bind(on_release=self.generate_pdf)
        btn_back = Button(text="Back to Home", size_hint_y=None, height=44, background_color=get_color_from_hex("#5F6E82"))
        btn_back.bind(on_release=lambda *_: setattr(self.manager, "current", "home"))
        root.add_widget(btn_gen)
        root.add_widget(btn_back)
        self.add_widget(root)

    def generate_pdf(self, *args):
        try:
            units = float(self.units_in.text or 0)
            rate = float(self.rate_in.text or 8.30)
        except ValueError:
            units, rate = 0.0, 8.30
        amt = round(units * rate, 2)
        bill_data = {
            "Consumer Name": self.name_in.text.strip() or "Consumer",
            "BP Number": self.bp_in.text.strip() or "0000000000",
            "Mobile": "-",
            "Meter Number": "-",
            "Address": "Bilaspur CG",
            "Bill Cycle": datetime.date.today().strftime("%Y-%m"),
            "Bill Date": datetime.date.today().strftime("%d-%m-%Y"),
            "Due Date": (datetime.date.today() + datetime.timedelta(days=10)).strftime("%d-%m-%Y"),
            "Status": "Unpaid",
            "UPI ID": "9009203060@ptsbi",
            "Prev Reading": "0",
            "Curr Reading": str(units),
            "Units": str(units),
            "Rate": f"{rate:.2f}",
            "Energy Charge": f"Rs. {amt:.2f}",
            "Gross Amount": f"Rs. {amt:.2f}",
            "NET PAYABLE": f"Rs. {amt:.2f}",
            "Net Payable Raw": f"{amt:.2f}",
        }
        path, msg = self.store.generate_bill_pdf(bill_data)
        show_popup("PDF Result", f"{msg}\n{path or ''}")


class PKPDCLApp(App):
    def build(self):
        Window.clearcolor = get_color_from_hex("#EEF3FA")
        base_dir = get_base_dir(self)
        self.store = PKPDCLStore(base_dir)
        sm = ScreenManager()
        sm.add_widget(HomeScreen(self.store, name="home"))
        sm.add_widget(BillScreen(self.store, name="bill"))
        return sm


if __name__ == "__main__":
    PKPDCLApp().run()
