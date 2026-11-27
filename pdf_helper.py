import os
import tempfile
from fpdf import FPDF

NAVY_RGB = (18, 43, 82)
LIGHT_BG_RGB = (238, 243, 250)
ALT_ROW_RGB = (249, 251, 254)
NET_BG_RGB = (214, 242, 224)
BORDER_RGB = (195, 206, 222)
DARK_RGB = (20, 33, 54)
MUTED_RGB = (95, 110, 130)
WHITE_RGB = (255, 255, 255)


def _pick_val(data_dict, keys, default="-"):
    for k in keys:
        if k in data_dict and data_dict[k] not in (None, ""):
            return data_dict[k]
    return default


def _resolve_logo_path(logo_path):
    candidates = []
    if logo_path:
        candidates.append(logo_path)
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.extend([
            os.path.join(base_dir, "pkpdcl_logo.png"),
            os.path.join(base_dir, "assets", "pkpdcl_logo.png"),
            os.path.join(base_dir, "images", "pkpdcl_logo.png"),
        ])
    except Exception:
        pass
    try:
        cwd = os.getcwd()
        candidates.extend([
            os.path.join(cwd, "pkpdcl_logo.png"),
            os.path.join(cwd, "assets", "pkpdcl_logo.png"),
            os.path.join(cwd, "images", "pkpdcl_logo.png"),
        ])
    except Exception:
        pass
    candidates.extend([
        "/storage/emulated/0/Download/PKPDCL/pkpdcl_logo.png",
        "/storage/emulated/0/Download/PKPDCL/assets/pkpdcl_logo.png",
        "pkpdcl_logo.png",
    ])
    for p in candidates:
        if p and os.path.isfile(p) and os.path.getsize(p) > 0:
            return os.path.abspath(p)
    return None


def _resolve_qr_path(qr_path):
    if not qr_path:
        return None
    candidates = [qr_path]
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidates.append(os.path.join(base_dir, os.path.basename(str(qr_path))))
    except Exception:
        pass
    try:
        cwd = os.getcwd()
        candidates.append(os.path.join(cwd, os.path.basename(str(qr_path))))
    except Exception:
        pass
    for p in candidates:
        if p and os.path.isfile(p) and os.path.getsize(p) > 0:
            return os.path.abspath(p)
    return None


def _prepare_image_path(img_path, tag="img", is_qr=False):
    if not img_path or not os.path.isfile(img_path) or os.path.getsize(img_path) == 0:
        return None
    try:
        from PIL import Image as PILImage

        with PILImage.open(img_path) as im:
            im.load()
            if is_qr:
                # QR ko crisp rakhne ke liye integer scale use karein
                gray = im.convert("L")
                w, h = gray.size
                if w > 0 and h > 0:
                    scale = max(1, min(280 // w, 280 // h))
                    new_w, new_h = w * scale, h * scale
                    scaled_qr = gray.resize((new_w, new_h), PILImage.Resampling.NEAREST)
                else:
                    scaled_qr = gray.resize((280, 280), PILImage.Resampling.NEAREST)
                    new_w, new_h = 280, 280

                # High-contrast black & white QR ensure karein
                bw_qr = scaled_qr.point(lambda x: 0 if x < 140 else 255, mode="1").convert("RGB")
                canvas = PILImage.new("RGB", (300, 300), (255, 255, 255))
                paste_x = (300 - new_w) // 2
                paste_y = (300 - new_h) // 2
                canvas.paste(bw_qr, (paste_x, paste_y))
                rgb = canvas
            else:
                if im.mode in ("RGBA", "LA", "P"):
                    rgba = im.convert("RGBA")
                    bg = PILImage.new("RGBA", rgba.size, (255, 255, 255, 255))
                    rgb = PILImage.alpha_composite(bg, rgba).convert("RGB")
                else:
                    rgb = im.convert("RGB")

            out_dir = tempfile.gettempdir()
            os.makedirs(out_dir, exist_ok=True)
            out_path = os.path.join(out_dir, f"_pkpdcl_{tag}.png")
            rgb.save(out_path, format="PNG", optimize=False)
            if os.path.isfile(out_path) and os.path.getsize(out_path) > 0:
                return out_path
    except Exception:
        pass
    return img_path


def _clean_text(val):
    if val is None:
        return "-"
    s = str(val).replace("\u20b9", "Rs. ")
    try:
        s.encode("latin-1")
        return s
    except UnicodeEncodeError:
        return s.encode("latin-1", errors="replace").decode("latin-1")


def _format_rebate(val):
    cleaned = _clean_text(val).replace("Rs.", "").strip()
    if cleaned.startswith("-"):
        cleaned = cleaned[1:].strip()
    if not cleaned:
        cleaned = "0.00"
    return f"-{cleaned}"


class PKPDCLBillPDF(FPDF):
    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", style="I", size=8)
        self.set_text_color(*MUTED_RGB)
        self.cell(0, 6, text="This is a computer generated bill.", align="C")


def create_pkpdcl_pdf(data, output_path="pkpdcl_bill.pdf", logo_path=None, qr_path=None):
    pdf = PKPDCLBillPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.add_page()

    page_w = pdf.w - 24
    x_left = 12
    y = 8

    actual_logo = _resolve_logo_path(logo_path)
    clean_logo = _prepare_image_path(actual_logo, "logo", is_qr=False) if actual_logo else None
    if clean_logo:
        try:
            logo_w = 24
            logo_x = x_left + (page_w - logo_w) / 2
            pdf.image(clean_logo, x=logo_x, y=y, w=logo_w)
            y += logo_w + 2
        except Exception:
            y += 4
    else:
        y += 4

    d = data if isinstance(data, dict) else {"Details": str(data)}

    company_name = _clean_text(
        _pick_val(
            d,
            ["Company", "Company Name", "Organization"],
            "PRAMOD KASHYAP POWER DISTRIBUTION CORPORATION LIMITED",
        )
    )
    pdf.set_xy(x_left, y)
    pdf.set_font("Helvetica", style="B", size=10.5)
    pdf.set_text_color(*NAVY_RGB)
    pdf.multi_cell(page_w, 5, text=company_name, align="C")
    y = pdf.get_y() + 1

    pdf.set_xy(x_left, y)
    pdf.set_font("Helvetica", style="B", size=8)
    pdf.set_text_color(*MUTED_RGB)
    pdf.cell(page_w, 4, text="ELECTRICITY BILL", align="C", ln=True)
    y = pdf.get_y() + 3

    # --- CONSUMER DETAILS (2-column grid) ---
    pdf.set_xy(x_left, y)
    pdf.set_font("Helvetica", style="B", size=8.5)
    pdf.set_text_color(*NAVY_RGB)
    pdf.cell(page_w, 5, text="CONSUMER DETAILS", ln=True)
    y = pdf.get_y() + 1

    consumer_pairs = [
        (
            "Consumer Name",
            _pick_val(d, ["Consumer Name", "Name", "Consumer"]),
            "BP Number",
            _pick_val(d, ["BP Number", "BP No", "Consumer No", "Consumer Number"]),
        ),
        (
            "Mobile",
            _pick_val(d, ["Mobile", "Mobile No", "Phone"]),
            "Meter Number",
            _pick_val(d, ["Meter Number", "Meter No"]),
        ),
        (
            "Address",
            _pick_val(d, ["Address"]),
            "Bill Cycle",
            _pick_val(d, ["Bill Cycle", "Billing Cycle", "Bill Month"]),
        ),
        (
            "Bill Date",
            _pick_val(d, ["Bill Date"]),
            "Due Date",
            _pick_val(d, ["Due Date"]),
        ),
        (
            "Payment Status",
            _pick_val(d, ["Status", "Payment Status"]),
            "UPI ID",
            _pick_val(d, ["UPI ID", "UPI"]),
        ),
        (
            "Prev Reading",
            _pick_val(d, ["Prev Reading", "Previous Reading"]),
            "Curr Reading",
            _pick_val(d, ["Curr Reading", "Current Reading"]),
        ),
        (
            "Units",
            _pick_val(d, ["Units", "Consumed Units"]),
            "Rate",
            _pick_val(d, ["Rate", "Tariff Rate"]),
        ),
    ]

    col_w = page_w / 4.0
    lbl_w = col_w * 0.88
    val_w = col_w * 1.12
    row_h = 5.4

    pdf.set_draw_color(*BORDER_RGB)
    pdf.set_line_width(0.2)

    for idx, (l1, v1, l2, v2) in enumerate(consumer_pairs):
        bg = ALT_ROW_RGB if idx % 2 == 0 else WHITE_RGB
        pdf.set_fill_color(*bg)
        pdf.set_xy(x_left, y)

        for is_val, text_val, w_cell in (
            (False, l1, lbl_w),
            (True, v1, val_w),
            (False, l2, lbl_w),
            (True, v2, val_w),
        ):
            pdf.set_font("Helvetica", style="B" if not is_val else "", size=7.5)
            pdf.set_text_color(*(MUTED_RGB if not is_val else DARK_RGB))
            pdf.cell(w_cell, row_h, text=f" {_clean_text(text_val)}", border=1, fill=True)
        y += row_h

    y += 3.5

    # --- BILL CALCULATION TABLE ---
    pdf.set_xy(x_left, y)
    pdf.set_font("Helvetica", style="B", size=8.5)
    pdf.set_text_color(*NAVY_RGB)
    pdf.cell(page_w, 5, text="BILL CALCULATION", ln=True)
    y = pdf.get_y() + 1

    desc_w = page_w * 0.72
    amt_w = page_w * 0.28
    calc_row_h = 5.2

    pdf.set_xy(x_left, y)
    pdf.set_fill_color(*LIGHT_BG_RGB)
    pdf.set_text_color(*NAVY_RGB)
    pdf.set_font("Helvetica", style="B", size=8)
    pdf.cell(desc_w, calc_row_h + 0.5, text=" Charge Description", border=1, fill=True, align="L")
    pdf.cell(amt_w, calc_row_h + 0.5, text="Amount (Rs.) ", border=1, fill=True, align="R")
    y += calc_row_h + 0.5

    calc_rows = [
        ("Energy Charge", _pick_val(d, ["Energy Charge", "Energy Charges"], "Rs. 0.00"), False, False),
        ("Fixed Charge", _pick_val(d, ["Fixed Charge", "Fixed Charges"], "Rs. 0.00"), False, False),
        ("Electricity Duty", _pick_val(d, ["Duty", "Electricity Duty"], "Rs. 0.00"), False, False),
        ("Cess", _pick_val(d, ["Cess"], "Rs. 0.00"), False, False),
        ("Other Charges", _pick_val(d, ["Other", "Other Charges"], "Rs. 0.00"), False, False),
        ("Arrears", _pick_val(d, ["Arrears"], "Rs. 0.00"), False, False),
        ("Adjustment", _pick_val(d, ["Adjustment"], "Rs. 0.00"), False, False),
        ("Gross Amount", _pick_val(d, ["Gross", "Gross Amount"], "Rs. 0.00"), True, False),
        ("Less: Rebate", _format_rebate(_pick_val(d, ["Rebate", "Less: Rebate"], "Rs. 0.00")), False, False),
        ("NET PAYABLE", _pick_val(d, ["NET PAYABLE", "Net Payable"], "Rs. 0.00"), True, True),
    ]

    for idx, (label, amt, is_bold, is_net) in enumerate(calc_rows):
        pdf.set_xy(x_left, y)
        if is_net:
            pdf.set_fill_color(*NET_BG_RGB)
            pdf.set_text_color(*NAVY_RGB)
            pdf.set_font("Helvetica", style="B", size=8.5)
        elif label == "Gross Amount":
            pdf.set_fill_color(*LIGHT_BG_RGB)
            pdf.set_text_color(*DARK_RGB)
            pdf.set_font("Helvetica", style="B", size=8)
        else:
            pdf.set_fill_color(*(ALT_ROW_RGB if idx % 2 == 0 else WHITE_RGB))
            pdf.set_text_color(*DARK_RGB)
            pdf.set_font("Helvetica", style="B" if is_bold else "", size=8)

        h_use = calc_row_h + 0.8 if is_net else calc_row_h
        align_desc = "C" if label in ("Gross Amount", "NET PAYABLE") else "L"
        prefix_desc = "" if align_desc == "C" else " "
        pdf.cell(
            desc_w,
            h_use,
            text=f"{prefix_desc}{_clean_text(label)}",
            border=1,
            fill=True,
            align=align_desc,
        )
        pdf.cell(
            amt_w,
            h_use,
            text=f"{_clean_text(amt)} ",
            border=1,
            fill=True,
            align="R",
        )
        y += h_use

    y += 3.5

    # --- SCAN TO PAY & UPI QR ---
    pdf.set_xy(x_left, y)
    pdf.set_font("Helvetica", style="B", size=8.5)
    pdf.set_text_color(*NAVY_RGB)
    pdf.cell(page_w, 4.5, text="SCAN TO PAY", ln=True)
    y = pdf.get_y() + 1.5

    actual_qr = _resolve_qr_path(qr_path)
    clean_qr = _prepare_image_path(actual_qr, "qr", is_qr=True) if actual_qr else None
    qr_size = 30
    if clean_qr:
        try:
            qr_x = x_left + (page_w - qr_size) / 2
            pdf.image(clean_qr, x=qr_x, y=y, w=qr_size, h=qr_size)
            y += qr_size + 1.5
        except Exception:
            y += 4
    else:
        y += 4

    upi_id_text = _clean_text(_pick_val(d, ["UPI ID", "UPI"], "9009203060@ptsbi"))
    pdf.set_xy(x_left, y)
    pdf.set_font("Helvetica", style="B", size=8)
    pdf.set_text_color(*DARK_RGB)
    pdf.cell(page_w, 4, text=f"UPI ID: {upi_id_text}", align="R", ln=True)
    y = pdf.get_y() + 0.5

    pdf.set_xy(x_left, y)
    pdf.set_font("Helvetica", style="", size=7.5)
    pdf.set_text_color(*MUTED_RGB)
    pdf.cell(
        page_w,
        4,
        text="Scan with any UPI app and verify the payee and amount before paying.",
        align="L",
        ln=True,
    )

    out_dir = os.path.dirname(os.path.abspath(output_path))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    pdf.output(output_path)
    return output_path
