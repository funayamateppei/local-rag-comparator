"""GraphData value objects - represent knowledge graph structures."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Entity:
    """Immutable value object representing a knowledge graph entity (node).

    Attributes:
        name: The entity name/label.
        type: The entity type/category.
        description: A textual description of the entity.
    """

    name: str
    type: str
    description: str


@dataclass(frozen=True)
class Relationship:
    """Immutable value object representing a knowledge graph relationship (edge).

    Attributes:
        source: The name of the source entity.
        target: The name of the target entity.
        relation_type: The type/label of the relationship.
        description: A textual description of the relationship.
    """

    source: str
    target: str
    relation_type: str
    description: str


@dataclass(frozen=True)
class GraphData:
    """Immutable value object representing a knowledge graph with entities and relationships.

    Attributes:
        entities: Tuple of Entity objects in the graph.
        relationships: Tuple of Relationship objects in the graph.
    """

    entities: tuple[Entity, ...] = field(default_factory=tuple)
    relationships: tuple[Relationship, ...] = field(default_factory=tuple)

    @property
    def entity_count(self) -> int:
        """Return the number of entities in the graph."""
        return len(self.entities)

    @property
    def relationship_count(self) -> int:
        """Return the number of relationships in the graph."""
        return len(self.relationships)

    def find_entity(self, name: str) -> Entity | None:
        """Find an entity by name.

        Args:
            name: The entity name to search for.

        Returns:
            The matching Entity, or None if not found.
        """
        for entity in self.entities:
            if entity.name == name:
                return entity
        return None
