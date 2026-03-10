"""GraphRAG-based graph repository implementation."""

import json
import logging
from pathlib import Path

import pandas as pd
import yaml
from src.domain.models.graph_data import Entity, GraphData, Relationship
from src.domain.models.query_result import QueryResult
from src.domain.repositories import IGraphRepository

logger = logging.getLogger(__name__)


class GraphRAGRepository(IGraphRepository):
    """IGraphRepository implementation using Microsoft GraphRAG.

    Stores graph data as Parquet files and provides search capabilities.
    Uses Ollama for LLM operations via dynamically generated settings.yaml.
    """

    def __init__(
        self,
        data_dir: str | Path = "./graphrag_data",
        ollama_base_url: str = "http://host.docker.internal:11434",
        llm_model: str = "qwen2.5:14b",
        embedding_model: str = "bge-m3",
    ) -> None:
        self._data_dir = Path(data_dir)
        self._ollama_base_url = ollama_base_url
        self._llm_model = llm_model
        self._embedding_model = embedding_model
        self._data_dir.mkdir(parents=True, exist_ok=True)

    def _get_document_dir(self, document_id: str) -> Path:
        doc_dir = self._data_dir / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir

    def generate_settings_yaml(self, output_dir: Path) -> Path:
        """Generate GraphRAG settings.yaml pointing to Ollama."""
        settings = {
            "llm": {
                "api_key": "ollama",
                "type": "openai_chat",
                "model": self._llm_model,
                "api_base": f"{self._ollama_base_url}/v1",
            },
            "embeddings": {
                "llm": {
                    "api_key": "ollama",
                    "type": "openai_embedding",
                    "model": self._embedding_model,
                    "api_base": f"{self._ollama_base_url}/v1",
                }
            },
            "input": {
                "type": "file",
                "file_type": "text",
                "base_dir": str(output_dir / "input"),
            },
            "storage": {
                "type": "file",
                "base_dir": str(output_dir / "output"),
            },
            "reporting": {
                "type": "file",
                "base_dir": str(output_dir / "logs"),
            },
        }
        settings_path = output_dir / "settings.yaml"
        with open(settings_path, "w", encoding="utf-8") as f:
            yaml.dump(settings, f, default_flow_style=False, allow_unicode=True)
        return settings_path

    async def store_graph(self, document_id: str, graph_data: GraphData) -> None:
        """Store graph data as Parquet files."""
        doc_dir = self._get_document_dir(document_id)

        # Store entities as Parquet
        if graph_data.entities:
            entities_data = [
                {"name": e.name, "type": e.type, "description": e.description} for e in graph_data.entities
            ]
            df_entities = pd.DataFrame(entities_data)
            df_entities.to_parquet(doc_dir / "entities.parquet", index=False)

        # Store relationships as Parquet
        if graph_data.relationships:
            relationships_data = [
                {
                    "source": r.source,
                    "target": r.target,
                    "relation_type": r.relation_type,
                    "description": r.description,
                }
                for r in graph_data.relationships
            ]
            df_relationships = pd.DataFrame(relationships_data)
            df_relationships.to_parquet(doc_dir / "relationships.parquet", index=False)

        # Store metadata
        metadata = {
            "document_id": document_id,
            "entity_count": graph_data.entity_count,
            "relationship_count": graph_data.relationship_count,
        }
        with open(doc_dir / "metadata.json", "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    async def search(self, query: str) -> list[QueryResult]:
        """Search across all stored graph data for relevant entities and relationships."""
        results: list[QueryResult] = []
        query_lower = query.lower()

        if not self._data_dir.exists():
            return results

        for doc_dir in self._data_dir.iterdir():
            if not doc_dir.is_dir():
                continue

            entities_path = doc_dir / "entities.parquet"
            if not entities_path.exists():
                continue

            df_entities = pd.read_parquet(entities_path)
            document_id = doc_dir.name

            # Search entities by name and description
            for _, row in df_entities.iterrows():
                name_lower = str(row["name"]).lower()
                desc_lower = str(row["description"]).lower()

                if query_lower in name_lower or query_lower in desc_lower:
                    score = 1.0 if query_lower in name_lower else 0.7
                    results.append(
                        QueryResult(
                            query=query,
                            answer=f"{row['name']} ({row['type']}): {row['description']}",
                            sources=(document_id,),
                            score=min(1.0, score),
                            rag_type="graph",
                        )
                    )

        # Sort by score descending
        results.sort(key=lambda r: r.score, reverse=True)
        return results

    async def get_graph_data(self, document_id: str) -> GraphData | None:
        """Retrieve graph data for a specific document."""
        doc_dir = self._data_dir / document_id
        metadata_path = doc_dir / "metadata.json"

        if not metadata_path.exists():
            return None

        entities: tuple[Entity, ...] = ()
        relationships: tuple[Relationship, ...] = ()

        entities_path = doc_dir / "entities.parquet"
        if entities_path.exists():
            df = pd.read_parquet(entities_path)
            entities = tuple(
                Entity(name=row["name"], type=row["type"], description=row["description"]) for _, row in df.iterrows()
            )

        relationships_path = doc_dir / "relationships.parquet"
        if relationships_path.exists():
            df = pd.read_parquet(relationships_path)
            relationships = tuple(
                Relationship(
                    source=row["source"],
                    target=row["target"],
                    relation_type=row["relation_type"],
                    description=row["description"],
                )
                for _, row in df.iterrows()
            )

        return GraphData(entities=entities, relationships=relationships)
