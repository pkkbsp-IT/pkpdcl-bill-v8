from fpdf import FPDF


def create_pkpdcl_pdf(data, output_path="pkpdcl_bill.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(0, 10, text="PKPDCL Bill", ln=True)

    if isinstance(data, dict):
        for k, v in data.items():
            pdf.cell(0, 8, text=f"{k}: {v}", ln=True)
    else:
        pdf.cell(0, 8, text=str(data), ln=True)

    pdf.output(output_path)
    return output_path
