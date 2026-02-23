"""DocumentProcessorUseCase - document processing pipeline.

Orchestrates the full document processing lifecycle:
file parsing -> entity extraction -> embedding -> indexing -> event dispatch.
"""

from src.application.interfaces import (
    IEmbeddingService,
    IEventDispatcher,
    IFileParser,
    ILLMService,
)
from src.domain.events import DocumentUploadedEvent
from src.domain.models.document import Document
from src.domain.models.graph_data import GraphData
from src.domain.models.prompt import PromptType
from src.domain.repositories import (
    IDocumentRepository,
    IGraphRepository,
    IPromptRepository,
    IVectorRepository,
)


class DocumentProcessorUseCase:
    """ドキュメント処理パイプライン: 受信 -> プロンプト取得 -> パース -> 保存

    Pipeline:
    1. Parse file to extract raw text (IFileParser)
    2. Create Document entity (status: UPLOADED)
    3. Start processing (status: PROCESSING)
    4. Load entity extraction prompt and render with text
    5. Send to LLM for entity extraction
    6. Mark as parsed (status: PARSED)
    7. Create embeddings and store in VectorDB
    8. Parse LLM response to GraphData and store in GraphDB
    9. Mark as indexed (status: INDEXED)
    10. Dispatch DocumentUploadedEvent
    """

    def __init__(
        self,
        document_repo: IDocumentRepository,
        prompt_repo: IPromptRepository,
        vector_repo: IVectorRepository,
        graph_repo: IGraphRepository,
        event_dispatcher: IEventDispatcher,
        llm_service: ILLMService,
        embedding_service: IEmbeddingService,
        file_parser: IFileParser,
    ) -> None:
        self._document_repo = document_repo
        self._prompt_repo = prompt_repo
        self._vector_repo = vector_repo
        self._graph_repo = graph_repo
        self._event_dispatcher = event_dispatcher
        self._llm_service = llm_service
        self._embedding_service = embedding_service
        self._file_parser = file_parser

    async def execute(self, file_path: str) -> Document:
        """Execute the full document processing pipeline.

        Args:
            file_path: Path to the file to process.

        Returns:
            The processed Document entity with its final status.
        """
        filename = file_path.split("/")[-1]
        document = Document(filename=filename, content="")

        try:
            # Step 1: Parse file to extract raw text
            raw_text = await self._file_parser.parse(file_path)
            document.content = raw_text
            await self._document_repo.save(document)

            # Step 2: Start processing
            document.start_processing()
            await self._document_repo.save(document)

            # Step 3: Load prompt and generate with LLM
            prompt_template = self._prompt_repo.load(PromptType.ENTITY_EXTRACTION)
            rendered_prompt = prompt_template.render(text=raw_text, language="ja")
            llm_response = await self._llm_service.generate(rendered_prompt)

            # Step 4: Mark as parsed
            document.mark_parsed(llm_response)
            await self._document_repo.save(document)

            # Step 5: Create embeddings and store in VectorDB
            chunks = self._split_text(raw_text)
            embeddings = await self._embedding_service.create_embeddings(chunks)
            await self._vector_repo.store_embeddings(document.id, chunks, embeddings)

            # Step 6: Parse LLM response to graph data and store in GraphDB
            graph_data = self._parse_graph_data(llm_response)
            await self._graph_repo.store_graph(document.id, graph_data)

            # Step 7: Mark as indexed
            document.mark_indexed()
            await self._document_repo.save(document)

            # Step 8: Dispatch event
            event = DocumentUploadedEvent(
                document_id=document.id,
                filename=document.filename,
            )
            await self._event_dispatcher.dispatch(event)

        except Exception as e:
            document.mark_failed(str(e))
            await self._document_repo.save(document)

        return document

    def _split_text(self, text: str, chunk_size: int = 500) -> list[str]:
        """Split text into chunks for embedding.

        Args:
            text: The raw text to split.
            chunk_size: Maximum number of characters per chunk.

        Returns:
            A list of text chunks.
        """
        if not text:
            return []
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i : i + chunk_size])
        return chunks

    def _parse_graph_data(self, llm_response: str) -> GraphData:
        """Parse LLM response into GraphData.

        For now, returns empty GraphData.
        Full JSON parsing will be implemented in the Infrastructure layer.

        Args:
            llm_response: The raw LLM response string.

        Returns:
            A GraphData value object.
        """
        return GraphData()
