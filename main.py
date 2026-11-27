import json
import os
import traceback
from datetime import datetime

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


def load_consumers(base_dir: str):
    data_file = os.path.join(base_dir, "pkpdcl_data.json")
    default_consumers = [
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
    ]
    if os.path.exists(data_file):
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                parsed = json.load(f)
            if isinstance(parsed, dict) and isinstance(parsed.get("consumers"), list) and parsed["consumers"]:
                return parsed["consumers"]
        except Exception:
            pass
    return default_consumers


def safe_pdf_text(val):
    s = str(val if val is not None else "")
    return s.encode("latin-1", "replace").decode("latin-1")


def generate_bill_pdf(base_dir: str, consumer: dict, prev_reading: float, curr_reading: float, units: float, amount: float, logo_path=None):
    if FPDF is None:
        raise RuntimeError("fpdf2 library installed nahi hai.")

    pdf_dir = os.path.join(base_dir, "Bills")
    os.makedirs(pdf_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_name = "".join(c if c.isalnum() else "_" for c in consumer.get("name", "Consumer"))
    pdf_path = os.path.join(pdf_dir, f"PKPDCL_Bill_{clean_name}_{timestamp}.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_fill_color(16, 38, 76)
    pdf.rect(0, 0, 210, 34, "F")

    if logo_path and os.path.exists(logo_path):
        try:
            pdf.image(logo_path, x=12, y=6, w=22, h=22)
        except Exception:
            pass

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_xy(40, 8)
    pdf.cell(0, 8, safe_pdf_text("PKPDCL ELECTRICITY BILL"), ln=1)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_xy(40, 18)
    pdf.cell(0, 6, safe_pdf_text("Pramod Kashyap Power Distribution Corporation Ltd."), ln=1)

    pdf.set_text_color(20, 20, 20)
    pdf.ln(14)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, safe_pdf_text(f"Generated On: {datetime.now().strftime('%d-%m-%Y %I:%M %p')}"), ln=1)
    pdf.ln(2)

    rows = [
        ("Consumer Name", consumer.get("name", "")),
        ("BP ID", consumer.get("bp_id", "")),
        ("Meter No", consumer.get("meter", "")),
        ("Mobile", consumer.get("mobile", "")),
        ("Address", consumer.get("address", "")),
        ("Previous Reading", f"{prev_reading:.2f}"),
        ("Current Reading", f"{curr_reading:.2f}"),
        ("Consumed Units", f"{units:.2f} kWh"),
        ("Rate per Unit", f"Rs. {float(consumer.get('rate', 8.3)):.2f}"),
        ("Total Payable Amount", f"Rs. {amount:.2f}"),
        ("UPI ID", consumer.get("upi", "")),
    ]

    pdf.set_font("Helvetica", "", 11)
    for label, value in rows:
        pdf.set_fill_color(242, 246, 252)
        pdf.cell(75, 9, safe_pdf_text(label), border=1, fill=True)
        if label == "Total Payable Amount":
            pdf.set_font("Helvetica", "B", 12)
        else:
            pdf.set_font("Helvetica", "", 11)
        pdf.cell(105, 9, safe_pdf_text(value), border=1, ln=1)

    pdf.ln(8)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(90, 90, 90)
    pdf.cell(0, 6, safe_pdf_text("System generated bill by PKPDCL Bill Calculator"), ln=1)

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


class PKPDCLApp(App):
    def build(self):
        Window.clearcolor = (0.07, 0.10, 0.16, 1)
        try:
            self.base_dir = get_base_dir()
            self.logo_path = ensure_logo_file(self.base_dir)
            self.consumers = load_consumers(self.base_dir)
            self.consumer_map = {c["name"]: c for c in self.consumers}
            names = list(self.consumer_map.keys())

            main_layout = BoxLayout(orientation="vertical", padding=14, spacing=10)

            header_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=74, spacing=10)
            if self.logo_path and os.path.exists(self.logo_path):
                header_box.add_widget(
                    Image(source=self.logo_path, size_hint_x=None, width=68, allow_stretch=True)
                )

            title_box = BoxLayout(orientation="vertical")
            title_box.add_widget(
                Label(
                    text="PKPDCL Bill Calculator",
                    font_size="20sp",
                    bold=True,
                    halign="left",
                    valign="middle",
                    color=(1, 0.85, 0.25, 1),
                )
            )
            title_box.add_widget(
                Label(
                    text="Bill & PDF Generator",
                    font_size="13sp",
                    halign="left",
                    valign="middle",
                    color=(0.78, 0.86, 0.98, 1),
                )
            )
            for lbl in title_box.children:
                lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            header_box.add_widget(title_box)
            main_layout.add_widget(header_box)

            form = GridLayout(cols=2, spacing=8, size_hint_y=None, height=220)

            form.add_widget(Label(text="Consumer:", color=(1, 1, 1, 1), halign="left"))
            self.spinner = Spinner(
                text=names[0] if names else "",
                values=names,
                size_hint_y=None,
                height=42,
            )
            self.spinner.bind(text=self.on_consumer_change)
            form.add_widget(self.spinner)

            form.add_widget(Label(text="Prev Reading:", color=(1, 1, 1, 1), halign="left"))
            self.prev_input = TextInput(text="100", input_filter="float", multiline=False, size_hint_y=None, height=42)
            form.add_widget(self.prev_input)

            form.add_widget(Label(text="Curr Reading:", color=(1, 1, 1, 1), halign="left"))
            self.curr_input = TextInput(text="150", input_filter="float", multiline=False, size_hint_y=None, height=42)
            form.add_widget(self.curr_input)

            form.add_widget(Label(text="Rate (Rs/Unit):", color=(1, 1, 1, 1), halign="left"))
            initial_rate = str(self.consumer_map[names[0]]["rate"]) if names else "8.3"
            self.rate_input = TextInput(text=initial_rate, input_filter="float", multiline=False, size_hint_y=None, height=42)
            form.add_widget(self.rate_input)

            main_layout.add_widget(form)

            self.summary_label = Label(
                text="Units: 50.00 | Total: Rs. 415.00",
                font_size="16sp",
                bold=True,
                color=(0.3, 1.0, 0.65, 1),
                size_hint_y=None,
                height=36,
            )
            main_layout.add_widget(self.summary_label)

            btn_row = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=None, height=48)
            calc_btn = Button(text="Calculate Bill", background_color=(0.18, 0.55, 0.95, 1))
            calc_btn.bind(on_press=self.calculate_bill)
            btn_row.add_widget(calc_btn)

            pdf_btn = Button(text="Generate PDF", background_color=(0.15, 0.72, 0.42, 1))
            pdf_btn.bind(on_press=self.create_pdf)
            btn_row.add_widget(pdf_btn)
            main_layout.add_widget(btn_row)

            self.status_label = Label(
                text=f"Storage: {self.base_dir}",
                font_size="12sp",
                color=(0.85, 0.9, 0.98, 1),
                halign="left",
                valign="top",
            )
            self.status_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            main_layout.add_widget(self.status_label)

            self.calculate_bill()
            return main_layout

        except Exception:
            tb = traceback.format_exc()
            log_path = save_crash_log(tb)
            return build_error_widget(tb, log_path)

    def on_consumer_change(self, spinner, text):
        consumer = self.consumer_map.get(text)
        if consumer:
            self.rate_input.text = str(consumer.get("rate", 8.3))
            self.calculate_bill()

    def _parse_values(self):
        prev_val = float(self.prev_input.text.strip() or 0)
        curr_val = float(self.curr_input.text.strip() or 0)
        rate_val = float(self.rate_input.text.strip() or 8.3)
        units = max(0.0, curr_val - prev_val)
        amount = units * rate_val
        return prev_val, curr_val, rate_val, units, amount

    def calculate_bill(self, instance=None):
        try:
            _, _, _, units, amount = self._parse_values()
            self.summary_label.text = f"Units: {units:.2f} | Total: Rs. {amount:.2f}"
        except Exception as e:
            self.status_label.text = f"Calculation error: {e}"

    def create_pdf(self, instance=None):
        try:
            prev_val, curr_val, rate_val, units, amount = self._parse_values()
            name = self.spinner.text
            consumer = dict(self.consumer_map.get(name, {"name": name or "Consumer"}))
            consumer["rate"] = rate_val

            self.summary_label.text = f"Units: {units:.2f} | Total: Rs. {amount:.2f}"
            pdf_path = generate_bill_pdf(
                base_dir=self.base_dir,
                consumer=consumer,
                prev_reading=prev_val,
                curr_reading=curr_val,
                units=units,
                amount=amount,
                logo_path=self.logo_path,
            )
            self.status_label.text = f"PDF Saved:\n{pdf_path}"
        except Exception:
            tb = traceback.format_exc()
            log_path = save_crash_log(tb)
            self.status_label.text = f"PDF Error (log: {log_path}):\n{tb.splitlines()[-1]}"


if __name__ == "__main__":
    PKPDCLApp().run()
