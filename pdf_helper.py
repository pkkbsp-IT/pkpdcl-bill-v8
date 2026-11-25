import os
from fpdf import FPDF


def create_pkpdcl_pdf(data, output_path="pkpdcl_bill.pdf", logo_path=None, qr_path=None):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()

    if logo_path and os.path.isfile(logo_path):
        try:
            pdf.image(logo_path, x=(pdf.w - 28) / 2, y=10, w=28)
            pdf.ln(32)
        except Exception:
            pass

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.cell(0, 10, text="PKPDCL ELECTRICITY BILL", ln=True, align="C")
    pdf.ln(2)

    pdf.set_font("Helvetica", size=10)
    if isinstance(data, dict):
        for k, v in data.items():
            pdf.cell(0, 7, text=f"{k}: {v}", ln=True)
    else:
        pdf.cell(0, 7, text=str(data), ln=True)

    if qr_path and os.path.isfile(qr_path):
        try:
            pdf.ln(4)
            pdf.image(qr_path, x=(pdf.w - 32) / 2, w=32)
            pdf.ln(2)
        except Exception:
            pass

    pdf.output(output_path)
    return output_path
