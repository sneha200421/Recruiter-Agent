import io
import docx
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts raw text from a PDF file using pypdf."""
    text = ""
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extracts raw text from a DOCX file using python-docx."""
    docx_file = io.BytesIO(file_bytes)
    doc = docx.Document(docx_file)
    text = "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])
    return text.strip()


def extract_text_from_file(uploaded_file) -> str:
    """
    Main parser helper that routes files to the appropriate reader based on extension.
    Handles PDF, DOCX, and TXT formats safely.
    """
    filename = uploaded_file.name.lower()
    file_bytes = uploaded_file.read()

    try:
        if filename.endswith(".pdf"):
            return extract_text_from_pdf(file_bytes)
        elif filename.endswith(".docx"):
            return extract_text_from_docx(file_bytes)
        elif filename.endswith(".txt"):
            return file_bytes.decode("utf-8", errors="ignore").strip()
        else:
            raise ValueError(f"Unsupported file format: {uploaded_file.name}")
    except Exception as e:
        print(f"Error parsing file {uploaded_file.name}: {str(e)}")
        return f"[ERROR: Could not parse {uploaded_file.name}. Details: {str(e)}]"