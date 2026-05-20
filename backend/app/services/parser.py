import io
import pdfplumber

async def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_blocks = []

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_blocks.append(page_text.strip())

    full_text = "\n".join(text_blocks)
    return full_text