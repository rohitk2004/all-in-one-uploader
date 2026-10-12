from fpdf import FPDF
import os

def create_valid_pdf(filename: str = "sample_certificate.pdf") -> str:
    """Generates a valid binary PDF document using fpdf2."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "CAPIAA Certificate Submission Document", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 12)
    pdf.multi_cell(0, 8, "This is a valid PDF document uploaded automatically to capiaa.ca.gov/certificate form.\n\nVerified Status: 200 OK")
    
    abs_path = os.path.abspath(filename)
    pdf.output(abs_path)
    return abs_path

if __name__ == "__main__":
    path = create_valid_pdf()
    print(f"Created valid PDF: {path} ({os.path.getsize(path)} bytes)")
