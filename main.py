import json
import os
import traceback
from datetime import datetime
from urllib.parse import quote

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput

# Safe optional imports
try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from PIL import Image as PILImage, ImageDraw
except ImportError:
    PILImage = None
    ImageDraw = None

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


def get_base_dir():
    candidates = [
        "/storage/emulated/0/Download/PKPDCL",
        "/sdcard/Download/PKPDCL",
        os.path.join(os.getcwd(), "pkpdcl_data"),
    ]
    for path in candidates:
        try:
            os.makedirs(path, exist_ok=True)
            test_file = os.path.join(path, ".write_test")
            with open(test_file, "w", encoding="utf-8") as f:
                f.write("ok")
            os.remove(test_file)
            return path
        except Exception:
            continue
    return os.getcwd()


def save_crash_log(tb_text: str):
    log_paths = [
        "/storage/emulated/0/Download/pkpdcl_crash.log",
        "/sdcard/Download/pkpdcl_crash.log",
        os.path.join(get_base_dir(), "pkpdcl_crash.log"),
    ]
    for p in log_paths:
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(tb_text)
            return p
        except Exception:
            pass
    return None


def ensure_logo_file(base_dir: str):
    local_logo = os.path.join(os.getcwd(), "pkpdcl_logo.png")
    if os.path.exists(local_logo):
        return local_logo

    target_logo = os.path.join(base_dir, "pkpdcl_logo.png")
    if os.path.exists(target_logo):
        return target_logo

    if PILImage and ImageDraw:
        try:
            img = PILImage.new("RGBA", (240, 240), (16, 38, 76, 255))
            draw = ImageDraw.Draw(img)
            draw.ellipse((24, 24, 216, 216), fill=(245, 179, 25, 255))
            draw.ellipse((46, 46, 194, 194), fill=(16, 38, 76, 255))
            draw.polygon(
                [(132, 62), (82, 132), (118, 132), (106, 180), (158, 108), (122, 108)],
                fill=(255, 215, 64, 255),
            )
            img.save(target_logo)
            return target_logo
        except Exception:
            pass
    return None


def load_or_init_data(base_dir: str):
    data_file = os.path.join(base_dir, "pkpdcl_data.json")
    default_data = {
        "company": "PRAMOD KASHYAP POWER DISTRIBUTION CORPORATION LIMITED",
        "consumers": [
            {
                "name": "Akshita Kashyap",
                "bp_id": "1001283465",
                "mobile": "9174042040",
                "meter": "3023456",
                "address": "Bilaspur CG",
                "rate": 8.3,
                "upi": "9009203060@ptsbi",
            },
            {
                "name": "Arun Kashyap",
                "bp_id": "1001286489",
                "mobile": "930032625",
                "meter": "3014576",
                "address": "Ratanpur CG",
                "rate": 8.3,
                "upi": "9009203060@ptsbi",
            },
            {
                "name": "Chitrarekha Kashyap",
                "bp_id": "1001284356",
                "mobile": "8982833685",
                "meter": "3014562",
                "address": "Bilaspur CG",
                "rate": 8.3,
                "upi": "9009203060@ptsbi",
            },
            {
                "name": "Deepanjalee Kashyap",
                "bp_id": "1001289102",
                "mobile": "9827145630",
                "meter": "3019821",
                "address": "Sarkanda, Bilaspur CG",
                "rate": 8.3,
                "upi": "9009203060@ptsbi",
            },
        ],
    }

    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                parsed = json.load(f)
            if isinstance(parsed, dict) and isinstance(parsed.get("consumers"), list) and parsed["consumers"]:
                return parsed
        except Exception:
            pass

    try:
        with open(data_file, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

    return default_data


def save_data_file(base_dir: str, data_obj: dict):
    data_file = os.path.join(base_dir, "pkpdcl_data.json")
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data_obj, f, indent=2, ensure_ascii=False)
    return data_file


def safe_pdf_text(val):
    s = str(val if val is not None else "")
    return s.encode("latin-1", "replace").decode("latin-1")


def generate_upi_qr(base_dir: str, consumer: dict, amount: float):
    if qrcode is None:
        return None
    upi_id = str(consumer.get("upi", "")).strip()
    if not upi_id:
        return None

    payee_name = quote(str(consumer.get("name", "PKPDCL")))
    uri = f"upi://pay?pa={upi_id}&pn={payee_name}&am={amount:.2f}&cu=INR"
    qr_dir = os.path.join(base_dir, "QR")
    os.makedirs(qr_dir, exist_ok=True)
    qr_path = os.path.join(qr_dir, "latest_bill_qr.png")

    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(qr_path)
    return qr_path


def generate_bill_pdf(base_dir: str, consumer: dict, prev_reading: float, curr_reading: float, units: float, amount: float, logo_path=None, qr_path=None):
    if FPDF is None:
        raise RuntimeError("fpdf2 library उपलब्ध नहीं है।")

    pdf_dir = os.path.join(base_dir, "Bills")
    os.makedirs(pdf_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = "".join(c if c.isalnum() else "_" for c in consumer.get("name", "Consumer"))
    pdf_path = os.path.join(pdf_dir, f"PKPDCL_Bill_{clean_name}_{timestamp}.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_fill_color(15, 35, 72)
    pdf.rect(0, 0, 210, 36, "F")

    if logo_path and os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=12, y=7, w=22, h=22)
        except Exception:
            pass

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(40, 8)
    pdf.cell(0, 8, safe_pdf_text("PKPDCL ELECTRICITY BILL"), ln=1)

    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(40, 19)
    pdf.cell(0, 6, safe_pdf_text("PRAMOD KASHYAP POWER DISTRIBUTION CORPORATION LIMITED"), ln=1)

    pdf.set_text_color(20, 20, 20)
    pdf.ln(15)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 7, safe_pdf_text(f"Bill Date & Time: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}"), ln=1)
    pdf.ln(2)

    rows = [
        ("Consumer Name", consumer.get("name", "")),
        ("BP ID", consumer.get("bp_id", "")),
        ("Meter Number", consumer.get("meter", "")),
        ("Mobile Number", consumer.get("mobile", "")),
        ("Address", consumer.get("address", "")),
        ("Previous Reading", f"{prev_reading:.2f}"),
        ("Current Reading", f"{curr_reading:.2f}"),
        ("Units Consumed", f"{units:.2f} kWh"),
        ("Rate per Unit", f"Rs. {float(consumer.get('rate', 8.3)):.2f}"),
        ("Total Payable Amount", f"Rs. {amount:.2f}"),
        ("UPI ID", consumer.get("upi", "")),
    ]

    for label, value in rows:
        pdf.set_fill_color(240, 245, 252)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(72, 9, safe_pdf_text(label), border=1, fill=True)
        if label == "Total Payable Amount":
            pdf.set_font("Helvetica", "B", 12)
        else:
            pdf.set_font("Helvetica", "", 10)
        pdf.cell(108, 9, safe_pdf_text(value), border=1, ln=1)

    if qr_path and os.path.exists(qr_path):
        try:
            pdf.ln(6)
            pdf.set_font("Helvetica", "B", 10)
            pdf.cell(0, 6, safe_pdf_text("Scan UPI QR to Pay:"), ln=1)
            pdf.image(qr_path, x=15, y=pdf.get_y() + 1, w=34, h=34)
        except Exception:
            pass

    pdf.output(pdf_path)
    return pdf_path


def build_error_widget(tb_text: str, log_path=None):
    root = BoxLayout(orientation="vertical", padding=12, spacing=8)
    root.add_widget(
        Label(
            text=f"Error Caught ({log_path or 'no log'})",
            color=(1.0, 0.35, 0.35, 1),
            bold=True,
            size_hint_y=None,
            height=36,
        )
    )
    sv = ScrollView()
    lbl = Label(
        text=tb_text,
        color=(1, 1, 1, 1),
        size_hint_y=None,
        halign="left",
        valign="top",
    )
    lbl.bind(texture_size=lambda inst, val: setattr(inst, "height", val[1] + 24))
    lbl.bind(width=lambda inst, val: setattr(inst, "text_size", (val - 24, None)))
    sv.add_widget(lbl)
    root.add_widget(sv)
    return root


class PKPDCLBillApp(App):
    def build(self):
        Window.clearcolor = (0.06, 0.09, 0.15, 1)
        try:
            self.base_dir = get_base_dir()
            self.logo_path = ensure_logo_file(self.base_dir)
            self.data_obj = load_or_init_data(self.base_dir)
            self.consumers = self.data_obj["consumers"]
            self.consumer_map = {c["name"]: c for c in self.consumers}
            names = list(self.consumer_map.keys())

            outer = ScrollView(do_scroll_x=False, do_scroll_y=True)
            main_box = BoxLayout(
                orientation="vertical",
                padding=14,
                spacing=10,
                size_hint_y=None,
            )
            main_box.bind(minimum_height=main_box.setter("height"))

            # Header card
            header = BoxLayout(orientation="horizontal", size_hint_y=None, height=78, spacing=12)
            if self.logo_path and os.path.exists(self.logo_path):
                header.add_widget(
                    Image(source=self.logo_path, size_hint_x=None, width=68, height=68, allow_stretch=True)
                )

            title_col = BoxLayout(orientation="vertical", spacing=2)
            t1 = Label(
                text="PKPDCL Bill Calculator",
                font_size="18sp",
                bold=True,
                color=(1.0, 0.84, 0.24, 1),
                halign="left",
                valign="middle",
            )
            t2 = Label(
                text="Consumer Billing, QR & PDF System",
                font_size="12sp",
                color=(0.78, 0.87, 0.98, 1),
                halign="left",
                valign="middle",
            )
            for lbl in (t1, t2):
                lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
                title_col.add_widget(lbl)

            header.add_widget(title_col)
            main_box.add_widget(header)

            # Consumer selector
            sel_box = GridLayout(cols=2, spacing=8, size_hint_y=None, height=54)
            lbl_con = Label(text="Consumer:", color=(1, 1, 1, 1), halign="left", valign="middle", size_hint_x=0.38)
            lbl_con.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
            sel_box.add_widget(lbl_con)

            self.spinner = Spinner(
                text=names[0] if names else "",
                values=names,
                size_hint_y=None,
                height=52,
            )
            self.spinner.bind(text=self.on_consumer_select)
            sel_box.add_widget(self.spinner)
            main_box.add_widget(sel_box)

            # Consumer info card
            self.info_label = Label(
                text="",
                font_size="13sp",
                color=(0.90, 0.95, 1.0, 1),
                halign="left",
                valign="top",
                size_hint_y=None,
                height=92,
            )
            self.info_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            main_box.add_widget(self.info_label)

            # Reading & rate inputs
            form = GridLayout(cols=2, spacing=10, size_hint_y=None, height=186)

            def add_field(label_text, default_val):
                lbl = Label(text=label_text, color=(1, 1, 1, 1), halign="left", valign="middle", size_hint_x=0.42)
                lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
                inp = TextInput(
                    text=str(default_val),
                    input_filter="float",
                    multiline=False,
                    font_size="16sp",
                    padding=[10, 12, 10, 10],
                    size_hint_y=None,
                    height=52,
                )
                form.add_widget(lbl)
                form.add_widget(inp)
                return inp

            self.prev_input = add_field("Prev Reading:", "100")
            self.curr_input = add_field("Curr Reading:", "150")
            init_rate = self.consumer_map[names[0]].get("rate", 8.3) if names else 8.3
            self.rate_input = add_field("Rate (Rs/Unit):", init_rate)

            main_box.add_widget(form)

            # Bill summary banner
            self.summary_label = Label(
                text="",
                font_size="16sp",
                bold=True,
                color=(0.28, 1.0, 0.62, 1),
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=44,
            )
            main_box.add_widget(self.summary_label)

            # Buttons row
            btn_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=52)
            calc_btn = Button(
                text="Calculate Bill",
                font_size="15sp",
                bold=True,
                background_color=(0.16, 0.54, 0.96, 1),
            )
            calc_btn.bind(on_press=self.calculate_bill)

            pdf_btn = Button(
                text="Generate PDF",
                font_size="15sp",
                bold=True,
                background_color=(0.14, 0.72, 0.40, 1),
            )
            pdf_btn.bind(on_press=self.create_pdf)

            btn_row.add_widget(calc_btn)
            btn_row.add_widget(pdf_btn)
            main_box.add_widget(btn_row)

            # QR preview image (if generated)
            self.qr_image = Image(
                source="",
                size_hint_y=None,
                height=0,
                allow_stretch=True,
            )
            main_box.add_widget(self.qr_image)

            # Status / output message
            self.status_label = Label(
                text=f"Folder: {self.base_dir}",
                font_size="12sp",
                color=(0.84, 0.90, 0.98, 1),
                halign="left",
                valign="top",
                size_hint_y=None,
                height=72,
            )
            self.status_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            main_box.add_widget(self.status_label)

            self.on_consumer_select(self.spinner, self.spinner.text)
            self.calculate_bill()

            outer.add_widget(main_box)
            return outer

        except Exception:
            tb = traceback.format_exc()
            log_path = save_crash_log(tb)
            return build_error_widget(tb, log_path)

    def _current_consumer(self):
        name = self.spinner.text
        base = dict(self.consumer_map.get(name, {"name": name or "Consumer", "rate": 8.3}))
        return base

    def on_consumer_select(self, spinner, text):
        c = self.consumer_map.get(text)
        if not c:
            return
        self.info_label.text = (
            f"BP ID: {c.get('bp_id', '-')}  |  Meter: {c.get('meter', '-')}\n"
            f"Mobile: {c.get('mobile', '-')}  |  UPI: {c.get('upi', '-')}\n"
            f"Address: {c.get('address', '-')}"
        )
        if hasattr(self, "rate_input"):
            self.rate_input.text = str(c.get("rate", 8.3))
            self.calculate_bill()

    def _compute(self):
        prev_v = float(self.prev_input.text.strip() or 0)
        curr_v = float(self.curr_input.text.strip() or 0)
        rate_v = float(self.rate_input.text.strip() or 8.3)
        units = max(0.0, curr_v - prev_v)
        amount = units * rate_v
        return prev_v, curr_v, rate_v, units, amount

    def calculate_bill(self, instance=None):
        try:
            _, _, _, units, amount = self._compute()
            self.summary_label.text = f"Units: {units:.2f} kWh  |  Total: Rs. {amount:.2f}"
        except Exception as e:
            self.status_label.text = f"Calculation error: {e}"

    def create_pdf(self, instance=None):
        try:
            prev_v, curr_v, rate_v, units, amount = self._compute()
            consumer = self._current_consumer()
            consumer["rate"] = rate_v

            # Persist updated rate in JSON
            for item in self.consumers:
                if item.get("name") == consumer.get("name"):
                    item["rate"] = rate_v
            save_data_file(self.base_dir, self.data_obj)

            qr_path = generate_upi_qr(self.base_dir, consumer, amount)
            if qr_path and os.path.exists(qr_path):
                self.qr_image.source = qr_path
                self.qr_image.height = 140
                self.qr_image.reload()

            pdf_path = generate_bill_pdf(
                base_dir=self.base_dir,
                consumer=consumer,
                prev_reading=prev_v,
                curr_reading=curr_v,
                units=units,
                amount=amount,
                logo_path=self.logo_path,
                qr_path=qr_path,
            )
            self.calculate_bill()
            self.status_label.text = f"PDF Generated:\n{pdf_path}"
        except Exception:
            tb = traceback.format_exc()
            log_path = save_crash_log(tb)
            self.status_label.text = f"PDF Error (log: {log_path}):\n{tb.splitlines()[-1]}"


if __name__ == "__main__":
    PKPDCLBillApp().run()
