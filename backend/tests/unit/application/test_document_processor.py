"""Tests for DocumentProcessorUseCase - document processing pipeline."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from src.application.use_cases.document_processor import DocumentProcessorUseCase
from src.domain.events import DocumentUploadedEvent
from src.domain.models.document import Document, DocumentStatus
from src.domain.models.graph_data import GraphData
from src.domain.models.prompt import PromptTemplate, PromptType


@pytest.fixture
def mock_dependencies():
    """Create all mocked dependencies for DocumentProcessorUseCase."""
    return {
        "document_repo": AsyncMock(),
        "prompt_repo": MagicMock(),
        "vector_repo": AsyncMock(),
        "graph_repo": AsyncMock(),
        "event_dispatcher": AsyncMock(),
        "llm_service": AsyncMock(),
        "embedding_service": AsyncMock(),
        "file_parser": AsyncMock(),
    }


@pytest.fixture
def prompt_template():
    """Create a test PromptTemplate for entity extraction."""
    return PromptTemplate(
        name="entity_extraction",
        template="Extract entities from: {{text}} in {{language}}",
        version="1.0",
        variables=["text", "language"],
    )


@pytest.fixture
def use_case(mock_dependencies):
    """Create a DocumentProcessorUseCase with mocked dependencies."""
    return DocumentProcessorUseCase(**mock_dependencies)


@pytest.fixture
def configured_mocks(mock_dependencies, prompt_template):
    """Set up mock return values for the happy path."""
    mock_dependencies["file_parser"].parse.return_value = "This is the raw text content of the document."
    mock_dependencies["prompt_repo"].load.return_value = prompt_template
    mock_dependencies[
        "llm_service"
    ].generate.return_value = '{"entities": [{"name": "Test", "type": "concept", "description": "A test entity"}]}'
    mock_dependencies["embedding_service"].create_embeddings.return_value = [[0.1, 0.2, 0.3]]
    return mock_dependencies


@pytest.fixture
def configured_use_case(configured_mocks):
    """Create a DocumentProcessorUseCase with fully configured mocks."""
    return DocumentProcessorUseCase(**configured_mocks)


class TestDocumentProcessorExecuteSuccess:
    """Tests for the happy path of the document processing pipeline."""

    @pytest.mark.asyncio
    async def test_execute_success_full_pipeline(self, configured_use_case, configured_mocks):
        """Test the full happy path: parse -> process -> embed -> index -> dispatch event."""
        result = await configured_use_case.execute("/path/to/test_doc.pdf")

        # Verify the result is a Document with INDEXED status
        assert isinstance(result, Document)
        assert result.status == DocumentStatus.INDEXED
        assert result.filename == "test_doc.pdf"

        # Verify file_parser was called
        configured_mocks["file_parser"].parse.assert_called_once_with("/path/to/test_doc.pdf")

        # Verify prompt_repo was called
        configured_mocks["prompt_repo"].load.assert_called_once_with(PromptType.ENTITY_EXTRACTION)

        # Verify llm_service was called
        configured_mocks["llm_service"].generate.assert_called_once()

        # Verify embedding_service was called
        configured_mocks["embedding_service"].create_embeddings.assert_called_once()

        # Verify repos were called
        configured_mocks["vector_repo"].store_embeddings.assert_called_once()
        configured_mocks["graph_repo"].store_graph.assert_called_once()

        # Verify document_repo.save was called multiple times (status transitions)
        assert configured_mocks["document_repo"].save.call_count >= 3

        # Verify event was dispatched
        configured_mocks["event_dispatcher"].dispatch.assert_called_once()
        dispatched_event = configured_mocks["event_dispatcher"].dispatch.call_args[0][0]
        assert isinstance(dispatched_event, DocumentUploadedEvent)

    @pytest.mark.asyncio
    async def test_execute_calls_file_parser_with_correct_path(self, configured_use_case, configured_mocks):
        """Verify file_parser.parse is called with the provided file path."""
        await configured_use_case.execute("/data/uploads/report.pdf")

        configured_mocks["file_parser"].parse.assert_called_once_with("/data/uploads/report.pdf")

    @pytest.mark.asyncio
    async def test_execute_loads_entity_extraction_prompt(self, configured_use_case, configured_mocks):
        """Verify prompt_repo.load is called with PromptType.ENTITY_EXTRACTION."""
        await configured_use_case.execute("/path/to/doc.pdf")

        configured_mocks["prompt_repo"].load.assert_called_once_with(PromptType.ENTITY_EXTRACTION)

    @pytest.mark.asyncio
    async def test_execute_renders_prompt_with_parsed_text(self, configured_use_case, configured_mocks):
        """Verify the LLM receives a rendered prompt containing the file's text content."""
        raw_text = "This is the raw text content of the document."

        await configured_use_case.execute("/path/to/doc.pdf")

        # The LLM should receive the rendered prompt that includes the raw text
        llm_call_args = configured_mocks["llm_service"].generate.call_args[0][0]
        assert raw_text in llm_call_args

    @pytest.mark.asyncio
    async def test_execute_creates_embeddings_from_text_chunks(self, configured_use_case, configured_mocks):
        """Verify embedding_service is called with text chunks derived from the raw text."""
        await configured_use_case.execute("/path/to/doc.pdf")

        # embedding_service.create_embeddings should be called with a list of strings
        call_args = configured_mocks["embedding_service"].create_embeddings.call_args[0][0]
        assert isinstance(call_args, list)
        assert len(call_args) > 0
        assert all(isinstance(chunk, str) for chunk in call_args)

    @pytest.mark.asyncio
    async def test_execute_stores_in_vector_and_graph_repos(self, configured_use_case, configured_mocks):
        """Verify both vector_repo.store_embeddings and graph_repo.store_graph are called."""
        result = await configured_use_case.execute("/path/to/doc.pdf")

        # vector_repo.store_embeddings called with document_id, chunks, embeddings
        configured_mocks["vector_repo"].store_embeddings.assert_called_once()
        vector_call_args = configured_mocks["vector_repo"].store_embeddings.call_args
        assert vector_call_args[0][0] == result.id  # document_id
        assert isinstance(vector_call_args[0][1], list)  # chunks
        assert isinstance(vector_call_args[0][2], list)  # embeddings

        # graph_repo.store_graph called with document_id and GraphData
        configured_mocks["graph_repo"].store_graph.assert_called_once()
        graph_call_args = configured_mocks["graph_repo"].store_graph.call_args
        assert graph_call_args[0][0] == result.id  # document_id
        assert isinstance(graph_call_args[0][1], GraphData)  # graph_data

    @pytest.mark.asyncio
    async def test_execute_dispatches_document_uploaded_event(self, configured_use_case, configured_mocks):
        """Verify event_dispatcher.dispatch is called with a DocumentUploadedEvent."""
        result = await configured_use_case.execute("/path/to/my_file.pdf")

        configured_mocks["event_dispatcher"].dispatch.assert_called_once()
        dispatched_event = configured_mocks["event_dispatcher"].dispatch.call_args[0][0]
        assert isinstance(dispatched_event, DocumentUploadedEvent)
        assert dispatched_event.document_id == result.id
        assert dispatched_event.filename == "my_file.pdf"


class TestDocumentProcessorStatusTransitions:
    """Tests for document status transitions during processing."""

    @pytest.mark.asyncio
    async def test_execute_document_status_transitions(self, configured_mocks, prompt_template):
        """Verify Document goes through UPLOADED -> PROCESSING -> PARSED -> INDEXED."""
        # Capture the document status at each save call using side_effect,
        # because Document is mutable and call_args_list stores references.
        captured_statuses: list[DocumentStatus] = []

        async def capture_status(document: Document) -> None:
            captured_statuses.append(document.status)

        configured_mocks["document_repo"].save.side_effect = capture_status

        use_case = DocumentProcessorUseCase(**configured_mocks)
        result = await use_case.execute("/path/to/doc.pdf")

        # Should see the progression: UPLOADED, PROCESSING, PARSED, INDEXED
        assert DocumentStatus.UPLOADED in captured_statuses
        assert DocumentStatus.PROCESSING in captured_statuses
        assert DocumentStatus.PARSED in captured_statuses
        assert DocumentStatus.INDEXED in captured_statuses

        # Verify correct ordering
        uploaded_idx = captured_statuses.index(DocumentStatus.UPLOADED)
        processing_idx = captured_statuses.index(DocumentStatus.PROCESSING)
        parsed_idx = captured_statuses.index(DocumentStatus.PARSED)
        indexed_idx = captured_statuses.index(DocumentStatus.INDEXED)
        assert uploaded_idx < processing_idx < parsed_idx < indexed_idx

        # Final result should be INDEXED
        assert result.status == DocumentStatus.INDEXED

    @pytest.mark.asyncio
    async def test_execute_saves_document_at_each_status_change(self, configured_mocks, prompt_template):
        """Verify document_repo.save is called at each status transition."""
        captured_statuses: list[DocumentStatus] = []

        async def capture_status(document: Document) -> None:
            captured_statuses.append(document.status)

        configured_mocks["document_repo"].save.side_effect = capture_status

        use_case = DocumentProcessorUseCase(**configured_mocks)
        await use_case.execute("/path/to/doc.pdf")

        # document_repo.save should be called at least 4 times:
        # 1. After initial save (UPLOADED)
        # 2. After start_processing (PROCESSING)
        # 3. After mark_parsed (PARSED)
        # 4. After mark_indexed (INDEXED)
        assert len(captured_statuses) >= 4
        assert DocumentStatus.UPLOADED in captured_statuses
        assert DocumentStatus.PROCESSING in captured_statuses
        assert DocumentStatus.PARSED in captured_statuses
        assert DocumentStatus.INDEXED in captured_statuses


class TestDocumentProcessorErrorHandling:
    """Tests for error handling in the document processing pipeline."""

    @pytest.mark.asyncio
    async def test_execute_marks_failed_on_parser_error(self, mock_dependencies):
        """When file_parser.parse raises an exception, document status should be FAILED."""
        mock_dependencies["file_parser"].parse.side_effect = Exception("File not found")
        use_case = DocumentProcessorUseCase(**mock_dependencies)

        result = await use_case.execute("/path/to/missing.pdf")

        assert result.status == DocumentStatus.FAILED
        assert "File not found" in result.error

        # document_repo.save should still be called to persist the failed state
        mock_dependencies["document_repo"].save.assert_called()
        last_save_call = mock_dependencies["document_repo"].save.call_args_list[-1]
        assert last_save_call[0][0].status == DocumentStatus.FAILED

    @pytest.mark.asyncio
    async def test_execute_marks_failed_on_llm_error(self, mock_dependencies, prompt_template):
        """When llm_service.generate raises an exception, document should be marked as FAILED."""
        mock_dependencies["file_parser"].parse.return_value = "Some raw text"
        mock_dependencies["prompt_repo"].load.return_value = prompt_template
        mock_dependencies["llm_service"].generate.side_effect = Exception("LLM service unavailable")
        use_case = DocumentProcessorUseCase(**mock_dependencies)

        result = await use_case.execute("/path/to/doc.pdf")

        assert result.status == DocumentStatus.FAILED
        assert "LLM service unavailable" in result.error

        # document_repo.save should still be called to persist the failed state
        mock_dependencies["document_repo"].save.assert_called()
        last_save_call = mock_dependencies["document_repo"].save.call_args_list[-1]
        assert last_save_call[0][0].status == DocumentStatus.FAILED
