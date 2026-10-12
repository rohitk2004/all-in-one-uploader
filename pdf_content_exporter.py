import io
import re
import zipfile
from fpdf import FPDF

class ContentPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 6, "StackBlitz Unique Content Document | SEO Technical Publication", align="R")
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

def safe_pdf_str(s: str) -> str:
    """Replaces non-latin1 unicode symbols with clean ascii/latin1 representations."""
    if not s:
        return ""
    replacements = {
        '\u2018': "'", '\u2019': "'", '\u201c': '"', '\u201d': '"',
        '\u2013': '-', '\u2014': '-', '\u2026': '...', '\u2122': 'TM',
        '《': '<', '》': '>', '✓': '[OK]', '⚡': '', '📊': '', '🚀': '',
        '•': '-', '–': '-', '—': '-', '“': '"', '”': '"', '‘': "'", '’': "'",
        '\xa0': ' '
    }
    for k, v in replacements.items():
        s = s.replace(k, v)
    return s.encode('latin-1', errors='replace').decode('latin-1')

def add_article_to_pdf(pdf: ContentPDF, title: str, content: str, phone: str = "", word_count: int = 0):
    """Formats and prints an individual article onto the PDF document."""
    pdf.add_page()
    
    # Title Header Banner
    pdf.set_fill_color(15, 23, 42) # Slate 900
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 13)
    pdf.multi_cell(0, 9, safe_pdf_str(title), fill=True, align="C")
    pdf.ln(2)
    
    # Metadata Subtitle Bar
    pdf.set_fill_color(241, 245, 249) # Slate 100
    pdf.set_text_color(71, 85, 105) # Slate 600
    pdf.set_font("Helvetica", "", 9)
    wc = word_count or len(content.split())
    meta_text = f"Support: {safe_pdf_str(phone)}   |   Words: {wc}   |   Format: SEO Knowledgebase Guide"
    pdf.cell(0, 7, meta_text, fill=True, align="C")
    pdf.ln(8)
    
    # Body Content
    paragraphs = content.split("\n")
    for para in paragraphs:
        p = para.strip()
        if not p:
            pdf.ln(2)
            continue
        
        is_header = (
            p.startswith("SECTION") or p.startswith("PHASE") or
            p.startswith("MODULE") or p.startswith("CHAPTER") or
            p.startswith("STAGE") or p.startswith("PART") or
            (p.isupper() and len(p.split()) < 14)
        )
        
        if is_header:
            pdf.ln(3)
            pdf.set_fill_color(226, 232, 240) # Slate 200
            pdf.set_text_color(15, 23, 42) # Slate 900
            pdf.set_font("Helvetica", "B", 10)
            pdf.multi_cell(0, 7, safe_pdf_str(p), fill=True)
            pdf.ln(2)
        else:
            pdf.set_text_color(30, 41, 59) # Slate 800
            pdf.set_font("Helvetica", "", 9.5)
            pdf.multi_cell(0, 5.5, safe_pdf_str(p))
            pdf.ln(1.5)

def create_single_article_pdf(title: str, content: str, phone: str = "", word_count: int = 0) -> bytes:
    """Generates PDF bytes for a single article."""
    pdf = ContentPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    add_article_to_pdf(pdf, title, content, phone, word_count)
    return bytes(pdf.output())

def create_combined_pdf(articles: list) -> bytes:
    """Generates a single combined PDF bytes document containing all articles."""
    pdf = ContentPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    for art in articles:
        add_article_to_pdf(
            pdf,
            title=art.get("Title", ""),
            content=art.get("Generated Content", ""),
            phone=art.get("Phone Interleaved", ""),
            word_count=art.get("Word Count", 0)
        )
    return bytes(pdf.output())

def create_articles_zip(articles: list) -> bytes:
    """Generates a zip file containing individual PDFs for all articles."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for idx, art in enumerate(articles, 1):
            title = art.get("Title", f"article_{idx}")
            clean_title = re.sub(r'[\\/*?:"<>|]', "", title)[:55].strip()
            filename = f"{idx:02d}_{clean_title}.pdf"
            pdf_bytes = create_single_article_pdf(
                title=title,
                content=art.get("Generated Content", ""),
                phone=art.get("Phone Interleaved", ""),
                word_count=art.get("Word Count", 0)
            )
            zf.writestr(filename, pdf_bytes)
    return zip_buffer.getvalue()
