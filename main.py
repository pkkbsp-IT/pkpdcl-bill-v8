from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle
import os
import json
import datetime

try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    HAS_FPDF = False

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
        consumers =
