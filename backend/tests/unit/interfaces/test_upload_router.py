"""Tests for the upload router."""

import io
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from src.application.use_cases.document_processor import DocumentProcessorUseCase
from src.domain.models.document import Document
from src.interfaces.routers.upload import get_document_processor_use_case, router


@pytest.fixture
def mock_use_case():
    return AsyncMock(spec=DocumentProcessorUseCase)


@pytest.fixture
def app(mock_use_case):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_document_processor_use_case] = lambda: mock_use_case
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


class TestUploadRouter:
    def test_upload_success(self, client, mock_use_case):
        document = Document(filename="test.pdf", content="content")
        document.start_processing()
        document.mark_parsed("parsed content")
        document.mark_indexed()
        mock_use_case.execute.return_value = document

        file_content = b"fake pdf content"
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == document.id
        assert data["filename"] == "test.pdf"
        assert data["status"] == "indexed"
        mock_use_case.execute.assert_called_once()

    def test_upload_no_file_returns_422(self, client):
        response = client.post("/api/upload")
        assert response.status_code == 422

    def test_upload_processing_failure_returns_500(self, client, mock_use_case):
        mock_use_case.execute.side_effect = Exception("Processing failed")

        file_content = b"fake pdf content"
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data

    def test_upload_document_failed_status_returns_500(self, client, mock_use_case):
        document = Document(filename="test.pdf", content="content")
        document.mark_failed("parse error")
        mock_use_case.execute.return_value = document

        file_content = b"fake pdf content"
        response = client.post(
            "/api/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
        )

        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
