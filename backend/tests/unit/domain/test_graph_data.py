"""Tests for GraphData, Entity, and Relationship value objects."""

import pytest

from src.domain.models.graph_data import Entity, GraphData, Relationship


class TestEntityCreation:
    """Tests for Entity value object."""

    def test_create_entity(self):
        entity = Entity(
            name="Python",
            type="ProgrammingLanguage",
            description="A high-level programming language.",
        )

        assert entity.name == "Python"
        assert entity.type == "ProgrammingLanguage"
        assert entity.description == "A high-level programming language."

    def test_entity_is_immutable(self):
        entity = Entity(name="Python", type="Language", description="desc")

        with pytest.raises(AttributeError):
            entity.name = "Java"


class TestRelationshipCreation:
    """Tests for Relationship value object."""

    def test_create_relationship(self):
        rel = Relationship(
            source="Python",
            target="FastAPI",
            relation_type="USED_BY",
            description="Python is used by FastAPI framework.",
        )

        assert rel.source == "Python"
        assert rel.target == "FastAPI"
        assert rel.relation_type == "USED_BY"
        assert rel.description == "Python is used by FastAPI framework."

    def test_relationship_is_immutable(self):
        rel = Relationship(
            source="A", target="B", relation_type="RELATES", description="desc"
        )

        with pytest.raises(AttributeError):
            rel.source = "C"


class TestGraphDataCreation:
    """Tests for GraphData value object."""

    def test_create_graph_data_with_entities_and_relationships(self):
        entities = (
            Entity(name="Python", type="Language", description="A language"),
            Entity(name="FastAPI", type="Framework", description="A framework"),
        )
        relationships = (
            Relationship(
                source="Python",
                target="FastAPI",
                relation_type="USED_BY",
                description="Python is used by FastAPI",
            ),
        )

        graph = GraphData(entities=entities, relationships=relationships)

        assert len(graph.entities) == 2
        assert len(graph.relationships) == 1

    def test_create_empty_graph_data(self):
        graph = GraphData()

        assert graph.entities == ()
        assert graph.relationships == ()

    def test_graph_data_is_immutable(self):
        graph = GraphData()

        with pytest.raises(AttributeError):
            graph.entities = ()


class TestGraphDataProperties:
    """Tests for GraphData computed properties."""

    def test_entity_count(self):
        entities = (
            Entity(name="A", type="Type", description="desc"),
            Entity(name="B", type="Type", description="desc"),
            Entity(name="C", type="Type", description="desc"),
        )
        graph = GraphData(entities=entities)

        assert graph.entity_count == 3

    def test_entity_count_empty(self):
        graph = GraphData()
        assert graph.entity_count == 0

    def test_relationship_count(self):
        relationships = (
            Relationship(source="A", target="B", relation_type="R", description="d"),
            Relationship(source="B", target="C", relation_type="R", description="d"),
        )
        graph = GraphData(relationships=relationships)

        assert graph.relationship_count == 2

    def test_relationship_count_empty(self):
        graph = GraphData()
        assert graph.relationship_count == 0


class TestGraphDataFindEntity:
    """Tests for GraphData.find_entity method."""

    def test_find_entity_returns_matching_entity(self):
        entity_python = Entity(name="Python", type="Language", description="A language")
        entity_fastapi = Entity(
            name="FastAPI", type="Framework", description="A framework"
        )
        graph = GraphData(entities=(entity_python, entity_fastapi))

        found = graph.find_entity("Python")

        assert found is not None
        assert found.name == "Python"
        assert found.type == "Language"

    def test_find_entity_returns_none_when_not_found(self):
        entity = Entity(name="Python", type="Language", description="A language")
        graph = GraphData(entities=(entity,))

        found = graph.find_entity("Java")

        assert found is None

    def test_find_entity_in_empty_graph(self):
        graph = GraphData()

        found = graph.find_entity("anything")

        assert found is None
