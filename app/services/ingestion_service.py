"""Ingestion service — extracts text from PDFs, images, and links."""
import re
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
from PIL import Image
import pytesseract
from app.utils.logger import logger
MAX_PDF_CHARS = 8000
MAX_OCR_CHARS = 4000
MAX_LINK_CHARS = 6000
REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (compatible; LinkedInAIAgent/1.0)"
class IngestionService:
    def extract_pdf(self, file_path):
        logger.info(f"Extracting PDF: {file_path}")
        try:
            reader = PdfReader(file_path)
            chunks = []
            for page in reader.pages:
                text = page.extract_text() or ""
                chunks.append(text)
                if sum(len(c) for c in chunks) > MAX_PDF_CHARS:
                    break
            full_text = "\n".join(chunks).strip()
            cleaned = self._clean_text(full_text)
            return cleaned[:MAX_PDF_CHARS]
        except Exception as e:
            raise ValueError(f"Could not parse PDF: {e}")
    def extract_image(self, file_path):
        logger.info(f"OCR on image: {file_path}")
        try:
            img = Image.open(file_path)
            if img.mode == "RGBA":
                img = img.convert("RGB")
            text = pytesseract.image_to_string(img)
            cleaned = self._clean_text(text)
            return cleaned[:MAX_OCR_CHARS]
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return ""
    def extract_link(self, url):
        logger.info(f"Scraping URL: {url}")
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT,
                                headers={"User-Agent": USER_AGENT})
            resp.raise_for_status()
        except requests.RequestException as e:
            raise ValueError(f"Could not fetch URL: {e}")
        try:
            soup = BeautifulSoup(resp.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
                tag.decompose()
            main = (soup.find("article") or soup.find("main")
                    or soup.find("div", {"role": "main"}) or soup.body)
            text = main.get_text(separator="\n") if main else soup.get_text(separator="\n")
            cleaned = self._clean_text(text)
            title = soup.title.string.strip() if soup.title and soup.title.string else ""
            result = f"TITLE: {title}\n\n{cleaned}" if title else cleaned
            return result[:MAX_LINK_CHARS]
        except Exception as e:
            raise ValueError(f"Could not parse page: {e}")
    @staticmethod
    def _clean_text(text):
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = "".join(c for c in text if c.isprintable() or c in "\n\t")
        return text.strip()