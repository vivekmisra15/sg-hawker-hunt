"""Tests for VectorStore — ChromaDB-backed semantic search."""
import tempfile
import os
import pytest
from rag.vector_store import VectorStore


@pytest.fixture
def store(tmp_path):
    """Create a VectorStore backed by a temporary directory."""
    return VectorStore(path=str(tmp_path / "chroma_test"))


SAMPLE_DOCS = [
    {
        "id": "stall-1",
        "text": "Famous chicken rice with silky poached chicken and fragrant oily rice",
        "metadata": {
            "stall_name": "Tian Tian Chicken Rice",
            "centre_name": "Maxwell Food Centre",
            "cuisine": "chicken rice",
            "region": "central",
            "tags": ["chicken rice", "poached"],
            "is_michelin": True,
            "is_halal": False,
        },
    },
    {
        "id": "stall-2",
        "text": "Rich and peppery bak kut teh with pork ribs simmered for hours",
        "metadata": {
            "stall_name": "Song Fa Bak Kut Teh",
            "centre_name": "Clementi 448 Market",
            "cuisine": "bak kut teh",
            "region": "west",
            "tags": ["bak kut teh", "peppery", "pork"],
            "is_michelin": True,
            "is_halal": False,
        },
    },
    {
        "id": "stall-3",
        "text": "Spicy coconut laksa with thick bee hoon and cockles",
        "metadata": {
            "stall_name": "328 Katong Laksa",
            "centre_name": "East Coast",
            "cuisine": "laksa",
            "region": "east",
            "tags": ["laksa", "coconut", "spicy"],
            "is_michelin": False,
            "is_halal": False,
        },
    },
]


def test_empty_collection_returns_empty_list(store):
    """Query on empty collection should return [] without error."""
    results = store.query("chicken rice", n_results=5)
    assert results == []


def test_collection_size_starts_at_zero(store):
    assert store.collection_size() == 0


def test_add_and_query_returns_results(store):
    """Adding docs then querying should return relevant results."""
    store.add_documents(SAMPLE_DOCS)
    assert store.collection_size() == 3

    results = store.query("chicken rice", n_results=2)
    assert len(results) == 2
    # Each result should have the expected structure
    for r in results:
        assert "text" in r
        assert "metadata" in r
        assert "distance" in r


def test_semantic_relevance_ordering(store):
    """Query for 'chicken rice' should rank the chicken rice stall first."""
    store.add_documents(SAMPLE_DOCS)
    results = store.query("chicken rice", n_results=3)
    assert results[0]["metadata"]["cuisine"] == "chicken rice"


def test_n_results_capped_to_collection_size(store):
    """Requesting more results than docs should return all docs without error."""
    store.add_documents(SAMPLE_DOCS)
    results = store.query("food", n_results=100)
    assert len(results) == 3


def test_add_empty_list_is_noop(store):
    """Adding an empty list should not error."""
    store.add_documents([])
    assert store.collection_size() == 0


def test_metadata_list_joined_to_string(store):
    """List metadata (tags) should be joined into a comma-separated string."""
    store.add_documents(SAMPLE_DOCS[:1])
    results = store.query("chicken", n_results=1)
    tags = results[0]["metadata"]["tags"]
    assert isinstance(tags, str)
    assert "chicken rice" in tags


def test_metadata_bool_converted_to_string(store):
    """Boolean metadata should be stored as string."""
    store.add_documents(SAMPLE_DOCS[:1])
    results = store.query("chicken", n_results=1)
    assert results[0]["metadata"]["is_michelin"] == "True"


def test_upsert_updates_existing_doc(store):
    """Adding a doc with the same id should update, not duplicate."""
    store.add_documents(SAMPLE_DOCS[:1])
    assert store.collection_size() == 1

    updated = [{
        "id": "stall-1",
        "text": "Updated description of chicken rice",
        "metadata": {"stall_name": "Updated Name", "cuisine": "chicken rice"},
    }]
    store.add_documents(updated)
    assert store.collection_size() == 1

    results = store.query("chicken", n_results=1)
    assert results[0]["metadata"]["stall_name"] == "Updated Name"
