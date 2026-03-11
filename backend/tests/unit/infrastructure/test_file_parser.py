"""Tests for PyMuPDFFileParser - concrete implementation of IFileParser."""

import pytest

fitz = pytest.importorskip("fitz", reason="PyMuPDF not installed")
from src.application.interfaces import IFileParser  # noqa: E402
from src.infrastructure.file_parser import PyMuPDFFileParser  # noqa: E402


class TestPyMuPDFFileParserInterface:
    """Tests that PyMuPDFFileParser properly implements IFileParser."""

    def test_implements_ifile_parser(self):
        """PyMuPDFFileParser should be an instance of IFileParser."""
        parser = PyMuPDFFileParser()
        assert isinstance(parser, IFileParser)


class TestPyMuPDFFileParserTxtParsing:
    """Tests for parsing plain text files."""

    @pytest.mark.asyncio
    async def test_parse_txt_file_returns_content(self, tmp_path):
        """Parsing a .txt file should return its text content."""
        txt_file = tmp_path / "sample.txt"
        txt_file.write_text("Hello, world!", encoding="utf-8")

        parser = PyMuPDFFileParser()
        result = await parser.parse(str(txt_file))

        assert result == "Hello, world!"

    @pytest.mark.asyncio
    async def test_parse_txt_file_with_multiline_content(self, tmp_path):
        """Parsing a multi-line .txt file should preserve all lines."""
        content = "Line 1\nLine 2\nLine 3"
        txt_file = tmp_path / "multiline.txt"
        txt_file.write_text(content, encoding="utf-8")

        parser = PyMuPDFFileParser()
        result = await parser.parse(str(txt_file))

        assert result == content

    @pytest.mark.asyncio
    async def test_parse_txt_file_with_utf8_content(self, tmp_path):
        """Parsing a .txt file with UTF-8 characters should work correctly."""
        content = "日本語テスト"
        txt_file = tmp_path / "japanese.txt"
        txt_file.write_text(content, encoding="utf-8")

        parser = PyMuPDFFileParser()
        result = await parser.parse(str(txt_file))

        assert result == content


class TestPyMuPDFFileParserPdfParsing:
    """Tests for parsing PDF files."""

    @pytest.mark.asyncio
    async def test_parse_pdf_file_returns_text(self, tmp_path):
        """Parsing a PDF file should extract its text content."""
        pdf_path = tmp_path / "test.pdf"
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Test content")
        doc.save(str(pdf_path))
        doc.close()

        parser = PyMuPDFFileParser()
        result = await parser.parse(str(pdf_path))

        assert "Test content" in result

    @pytest.mark.asyncio
    async def test_parse_pdf_with_multiple_pages(self, tmp_path):
        """Parsing a multi-page PDF should extract text from all pages."""
        pdf_path = tmp_path / "multipage.pdf"
        doc = fitz.open()
        page1 = doc.new_page()
        page1.insert_text((72, 72), "Page 1 content")
        page2 = doc.new_page()
        page2.insert_text((72, 72), "Page 2 content")
        doc.save(str(pdf_path))
        doc.close()

        parser = PyMuPDFFileParser()
        result = await parser.parse(str(pdf_path))

        assert "Page 1 content" in result
        assert "Page 2 content" in result


class TestPyMuPDFFileParserErrorHandling:
    """Tests for error handling."""

    @pytest.mark.asyncio
    async def test_parse_nonexistent_file_raises_file_not_found_error(self):
        """Parsing a nonexistent file should raise FileNotFoundError."""
        parser = PyMuPDFFileParser()

        with pytest.raises(FileNotFoundError, match="File not found"):
            await parser.parse("/nonexistent/path/file.pdf")

    @pytest.mark.asyncio
    async def test_parse_unsupported_csv_raises_value_error(self, tmp_path):
        """Parsing a .csv file should raise ValueError for unsupported type."""
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b,c", encoding="utf-8")

        parser = PyMuPDFFileParser()

        with pytest.raises(ValueError, match="Unsupported file type: .csv"):
            await parser.parse(str(csv_file))

    @pytest.mark.asyncio
    async def test_parse_unsupported_xlsx_raises_value_error(self, tmp_path):
        """Parsing a .xlsx file should raise ValueError for unsupported type."""
        xlsx_file = tmp_path / "data.xlsx"
        xlsx_file.write_bytes(b"fake xlsx content")

        parser = PyMuPDFFileParser()

        with pytest.raises(ValueError, match="Unsupported file type: .xlsx"):
            await parser.parse(str(xlsx_file))

    @pytest.mark.asyncio
    async def test_parse_unsupported_docx_raises_value_error(self, tmp_path):
        """Parsing a .docx file should raise ValueError for unsupported type."""
        docx_file = tmp_path / "doc.docx"
        docx_file.write_bytes(b"fake docx content")

        parser = PyMuPDFFileParser()

        with pytest.raises(ValueError, match="Unsupported file type: .docx"):
            await parser.parse(str(docx_file))
