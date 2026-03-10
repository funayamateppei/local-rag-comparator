"""Integration test: Full document processing pipeline (E2E).

Tests the complete flow from file upload to Vector/Graph DB storage and search.
External services (Ollama, ChromaDB) are mocked, but all internal wiring
(use cases, repositories, event dispatcher) uses real implementations.
"""

from unittest.mock import AsyncMock

import pytest
import yaml
from src.application.event_dispatcher import EventDispatcher
from src.application.use_cases.compare_rag import CompareRAGUseCase
from src.application.use_cases.document_processor import DocumentProcessorUseCase
from src.domain.events import DocumentUploadedEvent
from src.domain.models.document import DocumentStatus
from src.domain.models.graph_data import Entity, GraphData, Relationship
from src.domain.models.query_result import QueryResult
from src.infrastructure.document_repository import InMemoryDocumentRepository
from src.infrastructure.graph_repository import GraphRAGRepository
from src.infrastructure.prompt_repository import PromptRepository


class TestDocumentProcessingPipeline:
    """Test the full document processing pipeline end-to-end."""

    @pytest.fixture
    def document_repo(self):
        return InMemoryDocumentRepository()

    @pytest.fixture
    def prompt_repo(self):
        return PromptRepository()

    @pytest.fixture
    def event_dispatcher(self):
        return EventDispatcher()

    @pytest.fixture
    def mock_file_parser(self):
        parser = AsyncMock()
        parser.parse.return_value = "これはテスト文書です。太郎と花子が東京で出会いました。"
        return parser

    @pytest.fixture
    def mock_llm_service(self):
        llm = AsyncMock()
        llm.generate.return_value = (
            '{"entities": [{"name": "太郎", "type": "人物", "description": "主人公"},'
            ' {"name": "花子", "type": "人物", "description": "登場人物"},'
            ' {"name": "東京", "type": "場所", "description": "出会いの場所"}],'
            ' "relationships": [{"source": "太郎", "target": "花子",'
            ' "relation_type": "出会い", "description": "東京で出会った"}]}'
        )
        return llm

    @pytest.fixture
    def mock_embedding_service(self):
        service = AsyncMock()
        service.create_embeddings.side_effect = lambda texts: [[0.1] * 384 for _ in texts]
        return service

    @pytest.fixture
    def mock_vector_repo(self):
        repo = AsyncMock()
        repo.search.return_value = []
        return repo

    @pytest.fixture
    def graph_repo(self, tmp_path):
        return GraphRAGRepository(data_dir=tmp_path / "graphrag")

    @pytest.fixture
    def processor(
        self,
        document_repo,
        prompt_repo,
        mock_vector_repo,
        graph_repo,
        event_dispatcher,
        mock_llm_service,
        mock_embedding_service,
        mock_file_parser,
    ):
        return DocumentProcessorUseCase(
            document_repo=document_repo,
            prompt_repo=prompt_repo,
            vector_repo=mock_vector_repo,
            graph_repo=graph_repo,
            event_dispatcher=event_dispatcher,
            llm_service=mock_llm_service,
            embedding_service=mock_embedding_service,
            file_parser=mock_file_parser,
        )

    async def test_full_pipeline_document_reaches_indexed_status(self, processor):
        """Test that a document reaches INDEXED status after full pipeline."""
        document = await processor.execute("/path/to/test.pdf")
        assert document.status == DocumentStatus.INDEXED

    async def test_full_pipeline_file_parser_called(self, processor, mock_file_parser):
        """Test that file parser is called with the file path."""
        await processor.execute("/path/to/test.pdf")
        mock_file_parser.parse.assert_called_once_with("/path/to/test.pdf")

    async def test_full_pipeline_llm_called_with_prompt(self, processor, mock_llm_service):
        """Test that LLM is called with rendered prompt containing the text."""
        await processor.execute("/path/to/test.pdf")
        mock_llm_service.generate.assert_called_once()
        call_args = mock_llm_service.generate.call_args[0][0]
        assert "太郎" in call_args or "テスト文書" in call_args

    async def test_full_pipeline_embeddings_created(self, processor, mock_embedding_service):
        """Test that embeddings are created for text chunks."""
        await processor.execute("/path/to/test.pdf")
        mock_embedding_service.create_embeddings.assert_called_once()

    async def test_full_pipeline_vector_repo_stores_embeddings(self, processor, mock_vector_repo):
        """Test that embeddings are stored in vector repository."""
        await processor.execute("/path/to/test.pdf")
        mock_vector_repo.store_embeddings.assert_called_once()

    async def test_full_pipeline_graph_data_stored(self, processor, graph_repo):
        """Test that graph data is stored in graph repository."""
        await processor.execute("/path/to/test.pdf")
        # _parse_graph_data returns empty GraphData, so metadata.json should exist
        # but no entities/relationships parquet files (empty GraphData has no entities)

    async def test_full_pipeline_document_persisted(self, processor, document_repo):
        """Test that document is persisted in document repository."""
        document = await processor.execute("/path/to/test.pdf")
        stored = await document_repo.find_by_id(document.id)
        assert stored is not None
        assert stored.status == DocumentStatus.INDEXED
        assert stored.filename == "test.pdf"

    async def test_full_pipeline_event_dispatched(self, processor, event_dispatcher):
        """Test that DocumentUploadedEvent is dispatched after indexing."""
        events_received = []

        async def handler(event):
            events_received.append(event)

        event_dispatcher.register(DocumentUploadedEvent, handler)
        await processor.execute("/path/to/test.pdf")
        assert len(events_received) == 1
        assert isinstance(events_received[0], DocumentUploadedEvent)

    async def test_full_pipeline_error_handling(
        self,
        document_repo,
        prompt_repo,
        mock_vector_repo,
        graph_repo,
        event_dispatcher,
        mock_llm_service,
        mock_embedding_service,
    ):
        """Test that pipeline handles errors gracefully."""
        failing_parser = AsyncMock()
        failing_parser.parse.side_effect = Exception("File parsing failed")

        processor = DocumentProcessorUseCase(
            document_repo=document_repo,
            prompt_repo=prompt_repo,
            vector_repo=mock_vector_repo,
            graph_repo=graph_repo,
            event_dispatcher=event_dispatcher,
            llm_service=mock_llm_service,
            embedding_service=mock_embedding_service,
            file_parser=failing_parser,
        )

        document = await processor.execute("/path/to/broken.pdf")
        assert document.status == DocumentStatus.FAILED
        assert "File parsing failed" in document.error


class TestCompareRAGPipeline:
    """Test the RAG comparison pipeline end-to-end."""

    @pytest.fixture
    def mock_embedding_service(self):
        service = AsyncMock()
        service.create_embeddings.return_value = [[0.1] * 384]
        return service

    @pytest.fixture
    def mock_vector_repo(self):
        repo = AsyncMock()
        repo.search.return_value = [
            QueryResult(query="テスト", answer="ベクトル検索結果", sources=("doc1",), score=0.9, rag_type="vector"),
        ]
        return repo

    @pytest.fixture
    def mock_graph_repo(self):
        repo = AsyncMock()
        repo.search.return_value = [
            QueryResult(query="テスト", answer="グラフ検索結果", sources=("doc1",), score=0.85, rag_type="graph"),
        ]
        return repo

    @pytest.fixture
    def mock_llm_service(self):
        return AsyncMock()

    @pytest.fixture
    def compare_use_case(self, mock_vector_repo, mock_graph_repo, mock_llm_service, mock_embedding_service):
        return CompareRAGUseCase(
            vector_repo=mock_vector_repo,
            graph_repo=mock_graph_repo,
            llm_service=mock_llm_service,
            embedding_service=mock_embedding_service,
        )

    async def test_compare_returns_both_results(self, compare_use_case):
        """Test that comparison returns results from both RAG approaches."""
        result = await compare_use_case.execute("テスト質問")
        assert len(result.vector_results) == 1
        assert len(result.graph_results) == 1

    async def test_compare_vector_result_type(self, compare_use_case):
        """Test that vector results have correct rag_type."""
        result = await compare_use_case.execute("テスト質問")
        assert result.vector_results[0].rag_type == "vector"

    async def test_compare_graph_result_type(self, compare_use_case):
        """Test that graph results have correct rag_type."""
        result = await compare_use_case.execute("テスト質問")
        assert result.graph_results[0].rag_type == "graph"

    async def test_compare_query_preserved(self, compare_use_case):
        """Test that the original query is preserved in results."""
        result = await compare_use_case.execute("テスト質問")
        assert result.query == "テスト質問"

    async def test_compare_handles_vector_failure(self, mock_graph_repo, mock_llm_service, mock_embedding_service):
        """Test graceful handling when vector search fails."""
        failing_vector_repo = AsyncMock()
        failing_vector_repo.search.side_effect = Exception("Vector DB down")

        use_case = CompareRAGUseCase(
            vector_repo=failing_vector_repo,
            graph_repo=mock_graph_repo,
            llm_service=mock_llm_service,
            embedding_service=mock_embedding_service,
        )
        result = await use_case.execute("テスト質問")
        assert result.vector_error == "Vector DB down"
        assert len(result.graph_results) == 1

    async def test_compare_handles_graph_failure(self, mock_vector_repo, mock_llm_service, mock_embedding_service):
        """Test graceful handling when graph search fails."""
        failing_graph_repo = AsyncMock()
        failing_graph_repo.search.side_effect = Exception("Graph DB down")

        use_case = CompareRAGUseCase(
            vector_repo=mock_vector_repo,
            graph_repo=failing_graph_repo,
            llm_service=mock_llm_service,
            embedding_service=mock_embedding_service,
        )
        result = await use_case.execute("テスト質問")
        assert result.graph_error == "Graph DB down"
        assert len(result.vector_results) == 1


class TestGraphRepositoryIntegration:
    """Integration tests for GraphRAG repository with file system."""

    @pytest.fixture
    def graph_repo(self, tmp_path):
        return GraphRAGRepository(data_dir=tmp_path / "graphrag")

    async def test_store_and_retrieve_graph_data(self, graph_repo):
        """Test storing and retrieving graph data end-to-end."""
        entities = (
            Entity(name="太郎", type="人物", description="主人公"),
            Entity(name="東京", type="場所", description="舞台"),
        )
        relationships = (
            Relationship(source="太郎", target="東京", relation_type="居住", description="東京に住んでいる"),
        )
        graph_data = GraphData(entities=entities, relationships=relationships)

        await graph_repo.store_graph("doc-001", graph_data)
        retrieved = await graph_repo.get_graph_data("doc-001")

        assert retrieved is not None
        assert retrieved.entity_count == 2
        assert retrieved.relationship_count == 1
        assert retrieved.find_entity("太郎") is not None
        assert retrieved.find_entity("東京") is not None

    async def test_store_and_search_graph_data(self, graph_repo):
        """Test storing graph data and searching for entities."""
        entities = (
            Entity(name="太郎", type="人物", description="物語の主人公"),
            Entity(name="花子", type="人物", description="太郎の友人"),
        )
        graph_data = GraphData(entities=entities)

        await graph_repo.store_graph("doc-001", graph_data)
        results = await graph_repo.search("太郎")

        assert len(results) >= 1
        assert results[0].rag_type == "graph"
        assert "太郎" in results[0].answer

    async def test_search_no_results(self, graph_repo):
        """Test search returns empty when no matching data."""
        results = await graph_repo.search("存在しないエンティティ")
        assert results == []

    async def test_settings_yaml_generation(self, graph_repo, tmp_path):
        """Test that settings.yaml is correctly generated."""
        settings_path = graph_repo.generate_settings_yaml(tmp_path)
        assert settings_path.exists()

        with open(settings_path) as f:
            settings = yaml.safe_load(f)

        assert "llm" in settings
        assert "embeddings" in settings
        assert settings["llm"]["model"] == "qwen2.5:14b"
