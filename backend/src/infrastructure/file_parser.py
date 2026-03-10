"""PyMuPDF-based file parser implementation."""

from pathlib import Path

import fitz  # PyMuPDF

from src.application.interfaces import IFileParser


class PyMuPDFFileParser(IFileParser):
    """IFileParser implementation using PyMuPDF for PDF and plain text files."""

    SUPPORTED_EXTENSIONS = {".pdf", ".txt"}

    async def parse(self, file_path: str) -> str:
        """ファイルからテキストを抽出する"""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        extension = path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {extension}")

        if extension == ".txt":
            return path.read_text(encoding="utf-8")

        # PDF parsing with PyMuPDF
        doc = fitz.open(str(path))
        try:
            text_parts = []
            for page in doc:
                text_parts.append(page.get_text())
            return "\n".join(text_parts)
        finally:
            doc.close()
